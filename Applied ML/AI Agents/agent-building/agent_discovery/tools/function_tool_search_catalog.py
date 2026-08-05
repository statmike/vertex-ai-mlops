"""ADK tool: discover datasets and tables in the Knowledge Catalog.

Runs a scoped semantic `search_entries` call against Knowledge Catalog (the
product formerly called Dataplex Universal Catalog; the API namespace is still
``dataplex_v1``). This lets the discovery agent answer "what data do you have
about X?" by returning the matching BigQuery tables with their descriptions —
without ever querying the data itself.
"""

from google.adk import tools
from google.cloud import dataplex_v1

from config import (
    BQ_DATASET,
    GOOGLE_CLOUD_PROJECT,
)

_SEARCH_PAGE_SIZE = 15

# Cached catalog client — reuse the gRPC connection across calls.
_catalog_client: dataplex_v1.CatalogServiceClient | None = None


def _client() -> dataplex_v1.CatalogServiceClient:
    global _catalog_client
    if _catalog_client is None:
        _catalog_client = dataplex_v1.CatalogServiceClient()
    return _catalog_client


async def search_catalog(question: str, tool_context: tools.ToolContext) -> str:
    """Find datasets and tables relevant to a question in the data catalog.

    Use this to answer questions about *what data exists* — which tables cover a
    topic, what a table contains, where to find a metric — rather than the values
    inside the data.

    Args:
        question: The user's natural-language question about available data.
        tool_context: ADK tool execution context.

    Returns:
        A markdown list of matching tables (name + description), or a message if
        none match.
    """
    # Bare query syntax: no parentheses around the free-text question. Wrapping
    # it in parentheses makes the parser silently drop the parent: predicate and
    # leak out-of-scope entries. Scope to the dataset setup.py registered in
    # *this* project's catalog (views over the public theLook tables).
    query = f"{question} system=BIGQUERY parent:{GOOGLE_CLOUD_PROJECT}.datasets/{BQ_DATASET}"
    request = dataplex_v1.SearchEntriesRequest(
        name=f"projects/{GOOGLE_CLOUD_PROJECT}/locations/global",
        query=query,
        page_size=_SEARCH_PAGE_SIZE,
        semantic_search=True,
    )

    try:
        results = list(_client().search_entries(request=request))
    except Exception as e:  # noqa: BLE001 — surface a clean message to the model
        return (
            f"Error searching the data catalog: {e}. "
            "Has scripts/setup.py been run to register the dataset in Knowledge "
            "Catalog?"
        )

    rows: list[str] = []
    tables: list[str] = []
    for result in results:
        entry = result.dataplex_entry
        source = entry.entry_source
        fqn = entry.fully_qualified_name or ""
        name = source.display_name if source else (fqn.rsplit(".", 1)[-1] if fqn else "?")
        description = (source.description if source else "") or "(no description)"
        rows.append(f"- **{name}** — {description}")
        tables.append(fqn or name)

    if not rows:
        return "No tables in the catalog matched that question."

    # Record what we surfaced so callers can chain to the analytics agent.
    tool_context.state["discovery_last_tables"] = tables
    return "Matching tables in the catalog:\n" + "\n".join(rows)
