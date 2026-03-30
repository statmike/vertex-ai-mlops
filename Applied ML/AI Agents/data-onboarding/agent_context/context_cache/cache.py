"""Shared context cache — pre-fetched table metadata with brief and detailed views.

Populated once at module import time. Uses the Dataplex lookupContext API
for rich metadata (including dataProfile stats). Falls back to the existing
BQ ``table_documentation`` approach when lookupContext is unavailable.

Keyed by ``project.dataset.table``.
"""

import json
import logging
from dataclasses import dataclass, field

from google.cloud import bigquery

from agent_orchestrator.config import (
    BQ_DATASET_LOCATION,
    BQ_META_DATASET,
    CHAT_SCOPE,
    GOOGLE_CLOUD_PROJECT,
    get_dataplex_entry_name,
    get_scoped_tables,
    is_table_in_scope,
)

logger = logging.getLogger(__name__)


@dataclass
class TableContext:
    """Brief and detailed metadata for a single BigQuery table."""

    full_id: str  # "project.dataset.table"
    brief: str  # JSON without dataProfile sections
    detailed: str  # Full JSON with dataProfile sections
    columns: list[dict] = field(default_factory=list)  # [{name, bq_type, description}]
    description: str = ""


# ---------------------------------------------------------------------------
# Module-level cache
# ---------------------------------------------------------------------------
_CACHE: dict[str, TableContext] = {}


def _entry_name_to_full_id(entry_name: str) -> str | None:
    """Extract 'project.dataset.table' from a lookupContext entry name."""
    parts = entry_name.split("/")
    try:
        proj_idx = parts.index("projects")
        ds_idx = parts.index("datasets")
        tbl_idx = parts.index("tables")
        return f"{parts[proj_idx + 1]}.{parts[ds_idx + 1]}.{parts[tbl_idx + 1]}"
    except (ValueError, IndexError):
        return None


def _build_brief(entry: dict) -> dict:
    """Build a compact brief dict by stripping dataProfile from schema columns."""
    brief = {
        "name": entry.get("name", ""),
        "description": entry.get("description", ""),
        "schema": [
            {k: v for k, v in col.items() if k != "dataProfile"}
            for col in entry.get("schema", [])
        ],
    }
    if "table_id" in entry:
        brief["table_id"] = entry["table_id"]
    return brief


def _extract_columns(entry: dict) -> list[dict]:
    """Extract column info from a lookupContext entry for get_table_columns."""
    columns = []
    for col in entry.get("schema", []):
        columns.append({
            "name": col.get("column", col.get("name", "")),
            "bq_type": col.get("dataType", col.get("type", "STRING")),
            "description": col.get("description", ""),
        })
    return columns


def _get_datasets_from_catalog(bq_client: bigquery.Client) -> list[str]:
    """Discover datasets from the data_catalog meta table."""
    catalog_table = f"{GOOGLE_CLOUD_PROJECT}.{BQ_META_DATASET}.data_catalog"
    try:
        rows = list(bq_client.query(f"""
            SELECT dataset_name
            FROM `{catalog_table}`
            ORDER BY onboarded_at DESC
        """).result())
        return [row.dataset_name for row in rows]
    except Exception as e:
        logger.warning("Could not read data_catalog: %s", e)
        return []


def _populate_from_lookup_context(
    bq_client: bigquery.Client,
    datasets: list[str],
) -> bool:
    """Try to populate cache using Dataplex lookupContext API.

    Returns True if at least one table was cached, False otherwise.
    """
    from .util_lookup_context import lookup_context_batched

    for dataset in datasets:
        scoped_tables = get_scoped_tables(dataset) if CHAT_SCOPE else None
        if scoped_tables is None:
            # All tables — discover via BQ API
            try:
                table_list = [
                    (t.table_id, f"{GOOGLE_CLOUD_PROJECT}.{dataset}.{t.table_id}")
                    for t in bq_client.list_tables(f"{GOOGLE_CLOUD_PROJECT}.{dataset}")
                    if is_table_in_scope(dataset, t.table_id)
                ]
            except Exception as e:
                logger.debug("Could not list tables in %s: %s", dataset, e)
                continue
        else:
            table_list = [
                (tbl, f"{GOOGLE_CLOUD_PROJECT}.{dataset}.{tbl}")
                for tbl in scoped_tables
            ]

        if not table_list:
            continue

        entry_names = [
            get_dataplex_entry_name(dataset, tbl_name)
            for tbl_name, _ in table_list
        ]

        context_json = lookup_context_batched(entry_names)
        if not context_json or context_json == "[]":
            continue

        try:
            entries = json.loads(context_json)
        except json.JSONDecodeError:
            logger.warning("Failed to parse lookupContext JSON for dataset %s", dataset)
            continue

        valid_ids = {fid for _, fid in table_list}
        for entry in entries:
            entry_name = entry.get("name", "")
            full_id = _entry_name_to_full_id(entry_name)

            if not full_id or full_id not in valid_ids:
                logger.debug("Could not match lookupContext entry: %s", entry_name)
                continue

            entry["table_id"] = full_id
            brief_dict = _build_brief(entry)
            columns = _extract_columns(entry)
            desc = entry.get("description", "")

            _CACHE[full_id] = TableContext(
                full_id=full_id,
                brief=json.dumps(brief_dict, indent=2),
                detailed=json.dumps(entry, indent=2),
                columns=columns,
                description=desc,
            )

    return len(_CACHE) > 0


def _populate_from_table_documentation(
    bq_client: bigquery.Client,
    datasets: list[str],
) -> None:
    """Fallback: populate cache from BQ table_documentation tables."""
    for dataset in datasets:
        doc_table = f"{GOOGLE_CLOUD_PROJECT}.{dataset}.table_documentation"
        try:
            doc_rows = list(bq_client.query(f"""
                SELECT table_name, documentation_md, column_details,
                       related_tables, source_file
                FROM `{doc_table}`
                ORDER BY table_name
            """).result())
        except Exception as e:
            logger.debug("Could not load table docs for %s: %s", dataset, e)
            continue

        for doc in doc_rows:
            if not is_table_in_scope(dataset, doc.table_name):
                continue

            full_id = f"{GOOGLE_CLOUD_PROJECT}.{dataset}.{doc.table_name}"
            raw_columns = doc.column_details or []
            columns = [
                {
                    "name": c.get("name", ""),
                    "bq_type": c.get("bq_type", "STRING"),
                    "description": c.get("description", ""),
                }
                for c in raw_columns
            ]
            relationships = doc.related_tables or {}

            doc_md = doc.documentation_md or ""
            first_line = doc_md.split("\n")[0].strip().strip("#").strip() if doc_md else ""

            # Build brief and detailed as JSON for consistency
            brief_dict = {
                "table_id": full_id,
                "name": doc.table_name,
                "description": first_line,
                "schema": [
                    {"column": c["name"], "dataType": c["bq_type"], "description": c["description"]}
                    for c in columns
                ],
            }
            detailed_dict = {
                **brief_dict,
                "relationships": relationships,
                "documentation_md": doc_md,
            }

            _CACHE[full_id] = TableContext(
                full_id=full_id,
                brief=json.dumps(brief_dict, indent=2),
                detailed=json.dumps(detailed_dict, indent=2),
                columns=columns,
                description=first_line,
            )


def populate_cache() -> None:
    """Populate the module-level cache.

    Strategy:
    1. Determine datasets from CHAT_SCOPE config, or discover from data_catalog.
    2. Try Dataplex lookupContext API (rich metadata with dataProfile).
    3. Fall back to BQ table_documentation if lookupContext fails.
    """
    if not GOOGLE_CLOUD_PROJECT:
        return

    bq_client = bigquery.Client(project=GOOGLE_CLOUD_PROJECT)

    # Determine which datasets to cache
    if CHAT_SCOPE:
        from agent_orchestrator.config import get_scope_datasets
        datasets = get_scope_datasets()
    else:
        datasets = _get_datasets_from_catalog(bq_client)

    if not datasets:
        logger.info("No datasets found for context cache.")
        return

    # Try lookupContext first (richer metadata)
    try:
        if _populate_from_lookup_context(bq_client, datasets):
            logger.info(
                "Context cache populated via lookupContext: %d table(s).", len(_CACHE)
            )
            return
    except Exception as e:
        logger.info("lookupContext unavailable (%s), falling back to table_documentation.", e)

    # Fallback to table_documentation
    _populate_from_table_documentation(bq_client, datasets)
    logger.info(
        "Context cache populated via table_documentation: %d table(s).", len(_CACHE)
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get_all_briefs() -> str:
    """Return all brief summaries as a JSON array."""
    briefs = [json.loads(tc.brief) for tc in _CACHE.values()]
    return json.dumps(briefs, indent=2)


def get_brief_summary() -> str:
    """Return a compact text summary suitable for the shortlist reranker pass.

    One block per table: name, description, column list.
    """
    parts = []
    for tc in _CACHE.values():
        brief = json.loads(tc.brief)
        table_id = brief.get("table_id", tc.full_id)
        desc = brief.get("description", "")
        col_names = [
            col.get("column", col.get("name", ""))
            for col in brief.get("schema", [])
        ]

        parts.append(f"\n  **{table_id.split('.')[-1]}** ({len(col_names)} columns)")
        if desc:
            parts.append(f"    {desc}")
        if col_names:
            parts.append(f"    Columns: {', '.join(col_names)}")
        parts.append(f"    Full ref: {table_id}")

    return "\n".join(parts)


def get_detailed_for_tables(table_ids: list[str]) -> str:
    """Return detailed JSON for specific tables as a JSON array."""
    entries = []
    for tid in table_ids:
        tc = _CACHE.get(tid)
        if tc and tc.detailed:
            entries.append(json.loads(tc.detailed))
    return json.dumps(entries, indent=2)


def get_all_detailed() -> str:
    """Return all table detailed JSON as an array."""
    entries = [json.loads(tc.detailed) for tc in _CACHE.values() if tc.detailed]
    return json.dumps(entries, indent=2)


def get_table_ids() -> list[str]:
    """Return a list of all cached fully qualified table IDs."""
    return list(_CACHE.keys())


def get_table_columns_from_cache(table_name: str) -> dict | None:
    """Look up a table's column info from the cache.

    Args:
        table_name: Short name (e.g., "underlying_eod") or fully qualified
            ("project.dataset.table").

    Returns:
        Dict with keys ``full_id``, ``description``, ``columns`` if found,
        else None.
    """
    short_name = table_name.split(".")[-1] if "." in table_name else table_name
    for tc in _CACHE.values():
        if tc.full_id.endswith(f".{short_name}") or tc.full_id == table_name:
            return {
                "full_id": tc.full_id,
                "description": tc.description,
                "columns": tc.columns,
            }
    return None


def is_cached(full_id: str) -> bool:
    """Check whether a table is in the cache."""
    return full_id in _CACHE
