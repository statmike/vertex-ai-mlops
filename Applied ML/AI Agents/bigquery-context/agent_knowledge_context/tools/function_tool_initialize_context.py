"""Tool to pre-load Knowledge Context capsules from Dataplex lookupContext API."""

from google.adk import tools
from google.cloud import bigquery

from config import (
    GOOGLE_CLOUD_PROJECT,
    get_datasets, get_scoped_tables,
    get_dataplex_dataset_entry_name, get_dataplex_entry_name,
)
from .util_lookup_context import lookup_context, lookup_context_batched


async def initialize_context(
    tool_context: tools.ToolContext,
) -> str:
    """Load Knowledge Context capsules for all tables in scope.

    For datasets with all tables in scope, discovers tables via the BQ API.
    For datasets with specific tables listed, uses those directly.
    Then calls the Dataplex lookupContext API to fetch LLM-ready metadata.
    Results are cached in agent state — subsequent calls return from cache.

    The capsules include schema, column descriptions, and data profile
    statistics (null ratios, distinct values, sample values) when Dataplex
    profiling has been run on the tables.

    Returns:
        The full knowledge context string for all tables in scope.
    """
    # Return from cache if already loaded
    cached = tool_context.state.get("knowledge_context")
    if cached:
        return cached

    # Build table entries based on scope: (project.dataset.table, entry_name)
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

    # Combine
    full_context = f"# Dataset Context\n{dataset_context}\n\n# Table Context\n{table_context}"

    # Cache in state
    tool_context.state["knowledge_context"] = full_context

    return full_context
