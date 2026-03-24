"""Dataplex Catalog entry lookup tool for detailed metadata."""

import json

from google.adk import tools
from google.cloud import dataplex_v1
from google.protobuf import json_format

from config import GOOGLE_CLOUD_PROJECT, BQ_LOCATION


async def lookup_entry(
    entry_name: str,
    tool_context: tools.ToolContext,
) -> str:
    """Look up detailed metadata for a Dataplex catalog entry.

    Returns full schema, descriptions, storage info, and any aspects
    (including data profile results if profiling has been run).

    Args:
        entry_name: The Dataplex entry name from search results, e.g.,
            "projects/.../entryGroups/@bigquery/entries/...".

    Returns:
        JSON string with the full entry metadata including schema and aspects.
    """
    client = dataplex_v1.CatalogServiceClient()

    request = dataplex_v1.LookupEntryRequest(
        name=f"projects/{GOOGLE_CLOUD_PROJECT}/locations/{BQ_LOCATION.lower()}",
        entry=entry_name,
        view=dataplex_v1.EntryView.FULL,
    )

    entry = client.lookup_entry(request=request)
    entry_dict = json_format.MessageToDict(entry._pb)

    # Extract the most useful parts for the reranker
    summary = {
        "name": entry_dict.get("name", ""),
        "fully_qualified_name": entry_dict.get("fullyQualifiedName", ""),
        "entry_type": entry_dict.get("entryType", ""),
    }

    # Entry source (description, system)
    source = entry_dict.get("entrySource", {})
    if source:
        summary["display_name"] = source.get("displayName", "")
        summary["description"] = source.get("description", "")
        summary["system"] = source.get("system", "")

    # Schema aspect
    aspects = entry_dict.get("aspects", {})
    for key, aspect in aspects.items():
        if "schema" in key:
            summary["schema"] = aspect.get("data", {})
        if "storage" in key:
            summary["storage"] = aspect.get("data", {})

    return json.dumps(summary, indent=2)
