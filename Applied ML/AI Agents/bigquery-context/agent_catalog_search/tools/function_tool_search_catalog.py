"""Dataplex Catalog semantic search tool."""

import json

from google.adk import tools
from google.cloud import dataplex_v1

from config import GOOGLE_CLOUD_PROJECT, is_table_in_scope


async def search_catalog(
    prompt: str,
    tool_context: tools.ToolContext,
) -> str:
    """Search for BigQuery tables using natural language via Dataplex Catalog.

    Uses semantic search to find tables whose names, descriptions, and metadata
    relate to the search prompt. Results are scoped to configured datasets and
    filtered to only include tables that are in scope.

    Args:
        prompt: Natural language search query describing the data you need.

    Returns:
        JSON string with matching entries including names, descriptions, and types.
    """
    client = dataplex_v1.CatalogServiceClient()

    # Semantic search: use natural language query with system filter only.
    # The linked_resource filter is not effective with semantic_search=True
    # (Dataplex interprets the entire query semantically), so we post-filter
    # results using is_table_in_scope instead.
    query = f"({prompt}) AND system=BIGQUERY"

    request = dataplex_v1.SearchEntriesRequest(
        name=f"projects/{GOOGLE_CLOUD_PROJECT}/locations/global",
        query=query,
        page_size=20,
        semantic_search=True,
    )

    results = []
    for result in client.search_entries(request=request):
        entry = result.dataplex_entry
        source = entry.entry_source

        # Extract dataset and table from the entry name to check scope
        # Entry name format: .../datasets/{dataset}/tables/{table}
        fqn = entry.fully_qualified_name or ""
        parts = fqn.rsplit(".", 2)  # e.g. [..., dataset, table]
        if len(parts) >= 2:
            ds_name = parts[-2]
            tbl_name = parts[-1]
            if not is_table_in_scope(ds_name, tbl_name):
                continue

        results.append({
            "entry_name": entry.name,
            "fully_qualified_name": fqn,
            "display_name": source.display_name if source else "",
            "description": source.description if source else "",
            "entry_type": entry.entry_type,
        })

    return json.dumps({"status": "SUCCESS", "result_count": len(results), "results": results}, indent=2)
