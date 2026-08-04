"""Callback: search Knowledge Catalog + lookup entries + rerank.

Runs the entire Approach 2 workflow deterministically in
``before_agent_callback`` so no LLM agent calls are needed. This approach's
distinctive step is a per-entry ``lookup_entry`` for full schema/aspect metadata;
the scoped search, question extraction, reranking, and emit are shared helpers in
``discovery_common``.

Knowledge Catalog is the product formerly called Dataplex Universal Catalog
(renamed April 2026). The API namespace remains ``dataplex`` (``dataplex_v1``).
"""

import asyncio
import json

from google.adk.agents.callback_context import CallbackContext
from google.cloud import dataplex_v1
from google.protobuf import json_format

from config import BQ_LOCATION, GOOGLE_CLOUD_PROJECT
from discovery_common import (
    emit,
    get_question,
    plain_content,
    rerank_and_store,
    search_entries_scoped,
    store_empty,
)

LABEL = "Approach 2: Knowledge Catalog Search"
METHOD = "kc_search"


def _search_and_lookup(question: str) -> tuple[str, list[str], dict]:
    """Scoped semantic search, then per-entry lookup_entry for full metadata.

    Returns (metadata_string, nominated_table_ids, search_stats).
    """
    hits, stats = search_entries_scoped(question)
    if not hits:
        return "", [], stats

    client = dataplex_v1.CatalogServiceClient()
    nominated_ids: list[str] = []
    metadata_parts: list[str] = []
    for hit in hits:
        try:
            lookup_req = dataplex_v1.LookupEntryRequest(
                name=f"projects/{GOOGLE_CLOUD_PROJECT}/locations/{BQ_LOCATION.lower()}",
                entry=hit.entry_name,
                view=dataplex_v1.EntryView.FULL,
            )
            entry = client.lookup_entry(request=lookup_req)
            entry_dict = json_format.MessageToDict(entry._pb)

            summary: dict = {
                "display_name": hit.display_name,
                "description": hit.description,
            }
            for key, aspect in entry_dict.get("aspects", {}).items():
                if "schema" in key:
                    summary["schema"] = aspect.get("data", {})
                if "storage" in key:
                    summary["storage"] = aspect.get("data", {})

            nominated_ids.append(hit.table_id)
            metadata_parts.append(f"## {hit.table_id}\n{json.dumps(summary, indent=2)}")
        except Exception:
            continue

    return "\n\n".join(metadata_parts), nominated_ids, stats


async def discover_and_rerank(callback_context: CallbackContext):
    """Search + lookup + rerank in a single callback — no LLM needed."""
    question = get_question(callback_context)
    if not question:
        return None  # No question — fall back to LLM + tools

    metadata, nominated_ids, search_stats = await asyncio.to_thread(_search_and_lookup, question)

    callback_context.state["nominated_tables_kc_search"] = nominated_ids
    callback_context.state["search_stats_kc_search"] = search_stats

    if not metadata:
        store_empty(
            callback_context,
            METHOD,
            question,
            "No in-scope tables found via Knowledge Catalog search.",
        )
        return plain_content(LABEL, "No in-scope tables found via catalog search.")

    result = await rerank_and_store(callback_context, question, metadata, METHOD)
    return emit(LABEL, result)
