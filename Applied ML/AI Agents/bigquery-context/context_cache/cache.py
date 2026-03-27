"""Shared context cache — pre-fetched table metadata with brief and detailed views.

Populated once at module import time (when ``adk web`` or ``adk run`` loads any
agent that imports this module).  Provides brief summaries (for LLM pre-filtering)
and detailed YAML capsules (for reranking) keyed by ``project.dataset.table``.
"""

import logging
from dataclasses import dataclass

from google.cloud import bigquery

from config import (
    GOOGLE_CLOUD_PROJECT,
    get_dataplex_dataset_entry_name,
    get_dataplex_entry_name,
    get_datasets,
    get_scoped_tables,
)

from .util_lookup_context import lookup_context, lookup_context_batched

logger = logging.getLogger(__name__)


@dataclass
class TableContext:
    """Brief and detailed metadata for a single BigQuery table."""

    full_id: str  # "project.dataset.table"
    brief: str  # Compact: description + column names/types + row count
    detailed: str  # Full YAML capsule from lookupContext


# ---------------------------------------------------------------------------
# Module-level cache
# ---------------------------------------------------------------------------
_CACHE: dict[str, TableContext] = {}
_DATASET_CONTEXT: str = ""


def _build_brief(table: bigquery.Table) -> str:
    """Build a compact brief summary from a BQ Table object.

    Format:
        **project.dataset.table_name**
        Description of the table from catalog
        Columns: col_a (STRING), col_b (INT64), col_c (TIMESTAMP), ...
        Rows: ~1,200,000
    """
    full_id = f"{table.project}.{table.dataset_id}.{table.table_id}"
    parts = [f"**{full_id}**"]

    if table.description:
        parts.append(table.description)

    if table.schema:
        col_strs = [f"{f.name} ({f.field_type})" for f in table.schema]
        parts.append(f"Columns: {', '.join(col_strs)}")

    if table.num_rows is not None:
        parts.append(f"Rows: ~{table.num_rows:,}")

    return "\n".join(parts)


def populate_cache() -> None:
    """Populate the module-level cache with brief and detailed metadata.

    For each in-scope table:
      - ``bq_client.get_table(full_id)`` → build **brief**
      - ``lookup_context([entry_name])`` → store as **detailed** (full YAML)

    For each dataset:
      - ``lookup_context_batched(dataset_entry_names)`` → ``_DATASET_CONTEXT``
    """
    global _DATASET_CONTEXT  # noqa: PLW0603

    bq_client = bigquery.Client(project=GOOGLE_CLOUD_PROJECT)
    datasets = get_datasets()

    # Collect table entries: (full_id, dataset, table_name)
    table_entries: list[tuple[str, str, str]] = []
    for dataset in datasets:
        tables = get_scoped_tables(dataset)
        if tables is None:
            # All tables — discover via BQ API
            for t in bq_client.list_tables(f"{GOOGLE_CLOUD_PROJECT}.{dataset}"):
                full_id = f"{GOOGLE_CLOUD_PROJECT}.{dataset}.{t.table_id}"
                table_entries.append((full_id, dataset, t.table_id))
        else:
            for table_name in tables:
                full_id = f"{GOOGLE_CLOUD_PROJECT}.{dataset}.{table_name}"
                table_entries.append((full_id, dataset, table_name))

    # Fetch dataset-level context
    dataset_entry_names = [get_dataplex_dataset_entry_name(ds) for ds in datasets]
    _DATASET_CONTEXT = lookup_context_batched(dataset_entry_names)

    # Fetch per-table brief (BQ API) and detailed (lookupContext)
    for full_id, dataset, table_name in table_entries:
        try:
            # Brief from BQ get_table
            bq_table = bq_client.get_table(full_id)
            brief = _build_brief(bq_table)

            # Detailed from lookupContext
            entry_name = get_dataplex_entry_name(dataset, table_name)
            detailed_yaml = lookup_context([entry_name])
            detailed = f"## {full_id}\n{detailed_yaml}" if detailed_yaml else ""

            _CACHE[full_id] = TableContext(
                full_id=full_id,
                brief=brief,
                detailed=detailed,
            )
        except Exception:
            logger.warning("Failed to cache table %s", full_id, exc_info=True)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get_all_briefs() -> str:
    """Return all brief summaries concatenated (one per table).

    Used by Approach 4 (Context Pre-Filter) to show the LLM all tables.
    """
    return "\n\n".join(tc.brief for tc in _CACHE.values())


def get_detailed_for_tables(table_ids: list[str]) -> str:
    """Return detailed YAML for specific tables, concatenated.

    Used by Approach 4 (after rerank) and Approach 5.

    Args:
        table_ids: List of fully qualified table IDs (project.dataset.table).

    Returns:
        Concatenated detailed YAML for the requested tables.
    """
    parts = []
    for tid in table_ids:
        tc = _CACHE.get(tid)
        if tc and tc.detailed:
            parts.append(tc.detailed)
    return "\n\n".join(parts)


def get_all_detailed() -> str:
    """Return dataset context + all table detailed YAML, concatenated.

    Used by Approach 3 (Dataplex Context) — replaces the old
    ``_PREFETCHED_CONTEXT`` module-level variable.
    """
    table_context = "\n\n".join(tc.detailed for tc in _CACHE.values() if tc.detailed)
    return f"# Dataset Context\n{_DATASET_CONTEXT}\n\n# Table Context\n{table_context}"


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
