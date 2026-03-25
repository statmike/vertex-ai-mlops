"""Tool to pre-load Knowledge Context capsules from Dataplex lookupContext API.

The context is fetched once at module import time (i.e., when ``adk web``
or ``adk run`` loads the agent).  Every subsequent ``initialize_context``
tool call returns instantly from the module-level cache.
"""

import logging

from google.adk import tools
from google.cloud import bigquery

from config import (
    GOOGLE_CLOUD_PROJECT,
    get_datasets, get_scoped_tables,
    get_dataplex_dataset_entry_name, get_dataplex_entry_name,
)
from .util_lookup_context import lookup_context, lookup_context_batched

logger = logging.getLogger(__name__)


def fetch_knowledge_context() -> str:
    """Fetch Knowledge Context capsules for all tables in scope.

    Standalone function with no ADK dependencies.

    Returns:
        The full knowledge context string for all tables in scope.
    """
    bq_client = bigquery.Client(project=GOOGLE_CLOUD_PROJECT)
    table_entries = []
    datasets = get_datasets()

    for dataset in datasets:
        tables = get_scoped_tables(dataset)
        if tables is None:
            # All tables — discover via BQ API
            for t in bq_client.list_tables(f"{GOOGLE_CLOUD_PROJECT}.{dataset}"):
                full_id = f"{GOOGLE_CLOUD_PROJECT}.{dataset}.{t.table_id}"
                table_entries.append((full_id, get_dataplex_entry_name(dataset, t.table_id)))
        else:
            # Specific tables — use directly (no API call)
            for table_name in tables:
                full_id = f"{GOOGLE_CLOUD_PROJECT}.{dataset}.{table_name}"
                table_entries.append((full_id, get_dataplex_entry_name(dataset, table_name)))

    # Fetch dataset-level context (descriptions)
    dataset_entry_names = [get_dataplex_dataset_entry_name(ds) for ds in datasets]
    dataset_context = lookup_context_batched(dataset_entry_names)

    # Fetch table-level context with project.dataset.table headers
    table_context_parts = []
    for full_id, entry_name in table_entries:
        ctx = lookup_context([entry_name])
        if ctx:
            table_context_parts.append(f"## {full_id}\n{ctx}")
    table_context = "\n\n".join(table_context_parts)

    return f"# Dataset Context\n{dataset_context}\n\n# Table Context\n{table_context}"


# ---------------------------------------------------------------------------
# Module-level pre-fetch: runs once when the agent is loaded by ADK.
# If the fetch fails (auth, network, etc.) we log the error and fall back
# to on-demand fetching when the tool is called.
# ---------------------------------------------------------------------------
_PREFETCHED_CONTEXT: str | None = None

try:
    logger.info("Pre-fetching Knowledge Context capsules at startup …")
    _PREFETCHED_CONTEXT = fetch_knowledge_context()
    logger.info("Knowledge Context pre-fetch complete.")
except Exception:
    logger.warning(
        "Knowledge Context pre-fetch failed; will fetch on demand.",
        exc_info=True,
    )


async def initialize_context(
    tool_context: tools.ToolContext,
) -> str:
    """Return pre-loaded Knowledge Context capsules for all tables in scope.

    The context is fetched once at module load time (when ``adk web`` or
    ``adk run`` starts).  This tool returns the cached result instantly.
    If the pre-fetch failed, it falls back to fetching on demand.

    Returns:
        The full knowledge context string for all tables in scope.
    """
    if _PREFETCHED_CONTEXT is not None:
        return _PREFETCHED_CONTEXT

    # Fallback: pre-fetch failed, fetch now
    full_context = fetch_knowledge_context()
    return full_context
