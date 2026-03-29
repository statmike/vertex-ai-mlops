"""Shared context cache — pre-fetched table metadata with brief and detailed views.

Populated once at module import time (when ``adk web`` or ``adk run`` loads any
agent that imports this module).  Both views are derived from the Dataplex
lookupContext API (JSON format):

- **brief**: schema columns with name, type, and description only (dataProfile stripped)
- **detailed**: full JSON including dataProfile (nullRatio, distinctValues, sampleValues)

Keyed by ``project.dataset.table``.
"""

import json
import logging
from dataclasses import dataclass

from google.cloud import bigquery

from config import (
    GOOGLE_CLOUD_PROJECT,
    get_dataplex_entry_name,
    get_datasets,
    get_scoped_tables,
)

from .util_lookup_context import lookup_context_batched

logger = logging.getLogger(__name__)


@dataclass
class TableContext:
    """Brief and detailed metadata for a single BigQuery table."""

    full_id: str  # "project.dataset.table"
    brief: str  # JSON without dataProfile sections
    detailed: str  # Full JSON with dataProfile sections


# ---------------------------------------------------------------------------
# Module-level cache
# ---------------------------------------------------------------------------
_CACHE: dict[str, TableContext] = {}


def _entry_name_to_full_id(entry_name: str) -> str | None:
    """Extract 'project.dataset.table' from a lookupContext entry name.

    Entry names look like:
        projects/{project}/datasets/{dataset}/tables/{table}
    """
    parts = entry_name.split("/")
    # Expected: ['projects', proj, 'datasets', ds, 'tables', tbl]
    try:
        proj_idx = parts.index("projects")
        ds_idx = parts.index("datasets")
        tbl_idx = parts.index("tables")
        return f"{parts[proj_idx + 1]}.{parts[ds_idx + 1]}.{parts[tbl_idx + 1]}"
    except (ValueError, IndexError):
        return None


def _build_brief(entry: dict) -> dict:
    """Build a compact brief dict by stripping dataProfile from schema columns.

    Keeps: table_id, name, description, schema (column name, type, description).
    Strips: dataProfile, system, type (entry type path).
    """
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


def populate_cache() -> None:
    """Populate the module-level cache with brief and detailed metadata.

    For each in-scope table:
      - ``lookup_context_batched(entry_names)`` → JSON with full metadata
      - Brief derived by stripping ``dataProfile`` from each schema column
      - Detailed stored as-is (full JSON)
    """
    bq_client = bigquery.Client(project=GOOGLE_CLOUD_PROJECT)
    datasets = get_datasets()

    # Collect table entries grouped by dataset for batched lookupContext calls
    tables_by_dataset: dict[str, list[tuple[str, str]]] = {}  # ds → [(table_name, full_id)]
    for dataset in datasets:
        tables_by_dataset[dataset] = []
        tables = get_scoped_tables(dataset)
        if tables is None:
            # All tables — discover via BQ API
            for t in bq_client.list_tables(f"{GOOGLE_CLOUD_PROJECT}.{dataset}"):
                full_id = f"{GOOGLE_CLOUD_PROJECT}.{dataset}.{t.table_id}"
                tables_by_dataset[dataset].append((t.table_id, full_id))
        else:
            for table_name in tables:
                full_id = f"{GOOGLE_CLOUD_PROJECT}.{dataset}.{table_name}"
                tables_by_dataset[dataset].append((table_name, full_id))

    # Fetch table-level context in batches per dataset
    for dataset, table_list in tables_by_dataset.items():
        if not table_list:
            continue

        entry_names = [
            get_dataplex_entry_name(dataset, tbl_name) for tbl_name, _ in table_list
        ]

        # Batched lookupContext — up to 10 per API call, merged into one JSON array
        context_json = lookup_context_batched(entry_names)
        if not context_json or context_json == "[]":
            continue

        try:
            entries = json.loads(context_json)
        except json.JSONDecodeError:
            logger.warning("Failed to parse lookupContext JSON for dataset %s", dataset)
            continue

        # Match returned entries to full_ids via the name field
        for entry in entries:
            entry_name = entry.get("name", "")
            full_id = _entry_name_to_full_id(entry_name)

            if not full_id or full_id not in {fid for _, fid in table_list}:
                logger.warning("Could not match lookupContext entry: %s", entry_name)
                continue

            # Add table_id in project.dataset.table format so the reranker
            # uses consistent IDs (the raw name field uses Dataplex path format)
            entry["table_id"] = full_id

            brief_dict = _build_brief(entry)
            _CACHE[full_id] = TableContext(
                full_id=full_id,
                brief=json.dumps(brief_dict, indent=2),
                detailed=json.dumps(entry, indent=2),
            )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get_all_briefs() -> str:
    """Return all brief summaries as a JSON array.

    Used by Approach 4 (Context Pre-Filter) to show the LLM all tables
    in the system prompt for nomination.
    """
    briefs = [json.loads(tc.brief) for tc in _CACHE.values()]
    return json.dumps(briefs, indent=2)


def get_detailed_for_tables(table_ids: list[str]) -> str:
    """Return detailed JSON for specific tables as a JSON array.

    Used by Approach 4 (after nomination) and Approach 5 (after search).

    Args:
        table_ids: List of fully qualified table IDs (project.dataset.table).

    Returns:
        JSON array of full lookupContext entries for the requested tables.
    """
    entries = []
    for tid in table_ids:
        tc = _CACHE.get(tid)
        if tc and tc.detailed:
            entries.append(json.loads(tc.detailed))
    return json.dumps(entries, indent=2)


def get_all_detailed() -> str:
    """Return all table detailed JSON as an array.

    Used by Approach 3 (Dataplex Context) — sends everything to the reranker.
    """
    entries = [json.loads(tc.detailed) for tc in _CACHE.values() if tc.detailed]
    return json.dumps(entries, indent=2)


def get_table_ids() -> list[str]:
    """Return a list of all cached fully qualified table IDs.

    Useful for validation and prompt building.
    """
    return list(_CACHE.keys())


def is_cached(full_id: str) -> bool:
    """Check whether a table is in the cache."""
    return full_id in _CACHE


# ---------------------------------------------------------------------------
# Auto-populate at module import time
# ---------------------------------------------------------------------------
try:
    logger.info("Populating shared context cache at startup ...")
    populate_cache()
    logger.info("Shared context cache populated: %d table(s).", len(_CACHE))
except Exception:
    logger.warning(
        "Shared context cache population failed; cache will be empty.",
        exc_info=True,
    )
