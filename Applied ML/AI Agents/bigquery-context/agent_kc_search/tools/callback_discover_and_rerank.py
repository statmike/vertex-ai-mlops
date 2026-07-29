"""Callback: search Knowledge Catalog + lookup entries + rerank.

Runs the entire Approach 2 workflow deterministically in
``before_agent_callback`` so no LLM agent calls are needed.

Knowledge Catalog is the product formerly called Dataplex Universal Catalog
(renamed April 2026). The API namespace remains ``dataplex`` (``dataplex_v1``).
"""

import asyncio
import json

from google.adk.agents.callback_context import CallbackContext
from google.cloud import dataplex_v1
from google.genai import types
from google.protobuf import json_format

from config import (
    BQ_LOCATION,
    GOOGLE_CLOUD_PROJECT,
    TOP_K,
    get_datasets,
    is_table_in_scope,
)
from reranker.util_rerank import call_reranker, format_reranker_markdown
from schemas import RerankerResponse


def _search_and_lookup(question: str) -> tuple[str, list[str], dict]:
    """Run Knowledge Catalog semantic search + entry lookup, return metadata and IDs.

    Combines the logic of search_catalog and lookup_entry into a single
    synchronous function suitable for ``asyncio.to_thread``.

    Returns:
        Tuple of (metadata_string, nominated_table_ids, search_stats), where
        ``search_stats`` records the *raw* count the API returned vs. what
        survived our client-side scope filter. The ``parent:`` predicate is
        advisory, not enforced, so the API can fill the page budget with tables
        from unrelated datasets; this instrumentation makes that visible per run
        instead of only inferring it from the post-filter nominated count.
    """
    client = dataplex_v1.CatalogServiceClient()

    # Step 1: Semantic search — scope to our datasets via parent: filter
    dataset_filter = "|".join(f"datasets/{ds}" for ds in get_datasets())
    query = f"({question}) AND system=BIGQUERY AND parent:({dataset_filter})"
    request = dataplex_v1.SearchEntriesRequest(
        name=f"projects/{GOOGLE_CLOUD_PROJECT}/locations/global",
        query=query,
        page_size=20,
        semantic_search=True,
    )

    raw_count = 0
    out_of_scope_dropped = 0
    search_results = []
    for result in client.search_entries(request=request):
        raw_count += 1
        entry = result.dataplex_entry
        source = entry.entry_source
        fqn = entry.fully_qualified_name or ""
        parts = fqn.rsplit(".", 2)
        if len(parts) >= 2:
            ds_name = parts[-2]
            tbl_name = parts[-1]
            if not is_table_in_scope(ds_name, tbl_name):
                out_of_scope_dropped += 1
                continue
        search_results.append({
            "entry_name": entry.name,
            "fqn": fqn,
            "display_name": source.display_name if source else "",
            "description": source.description if source else "",
        })

    stats = {
        "raw_search_count": raw_count,
        "out_of_scope_dropped": out_of_scope_dropped,
        "page_size": 20,
    }

    if not search_results:
        return "", [], stats

    # Step 2: Lookup each entry for full metadata
    nominated_ids = []
    metadata_parts = []
    for sr in search_results:
        fqn = sr["fqn"]
        fqn_parts = fqn.rsplit(".", 2)
        if len(fqn_parts) >= 3:
            table_header = (
                f"{GOOGLE_CLOUD_PROJECT}.{fqn_parts[-2]}.{fqn_parts[-1]}"
            )
        else:
            table_header = fqn

        try:
            lookup_req = dataplex_v1.LookupEntryRequest(
                name=(
                    f"projects/{GOOGLE_CLOUD_PROJECT}"
                    f"/locations/{BQ_LOCATION.lower()}"
                ),
                entry=sr["entry_name"],
                view=dataplex_v1.EntryView.FULL,
            )
            entry = client.lookup_entry(request=lookup_req)
            entry_dict = json_format.MessageToDict(entry._pb)

            summary = {
                "display_name": sr["display_name"],
                "description": sr["description"],
            }
            aspects = entry_dict.get("aspects", {})
            for key, aspect in aspects.items():
                if "schema" in key:
                    summary["schema"] = aspect.get("data", {})
                if "storage" in key:
                    summary["storage"] = aspect.get("data", {})

            nominated_ids.append(table_header)
            metadata_parts.append(
                f"## {table_header}\n{json.dumps(summary, indent=2)}"
            )
        except Exception:
            continue

    return "\n\n".join(metadata_parts), nominated_ids, stats


async def discover_and_rerank(callback_context: CallbackContext):
    """Search + lookup + rerank in a single callback — no LLM needed.

    1. Extract the user's question from callback context.
    2. Run Knowledge Catalog semantic search + entry lookup.
    3. Call the shared ``call_reranker`` (Gemini structured output).
    4. Store the result in state for the compare agent.
    5. Return types.Content so the agent skips the LLM entirely.
    """
    user_content = callback_context.user_content
    if not user_content or not user_content.parts:
        return None  # No question — fall back to LLM + tools

    question = user_content.parts[0].text
    if not question:
        return None

    metadata, nominated_ids, search_stats = await asyncio.to_thread(
        _search_and_lookup, question
    )

    # Store nominations in state
    callback_context.state["nominated_tables_kc_search"] = nominated_ids
    # Raw-vs-filtered search stats: the harness records these so the report can
    # separate "the API returned few candidates" (relevance gap) from "the API
    # filled the page with out-of-scope tables our filter dropped" (scope leak).
    callback_context.state["search_stats_kc_search"] = search_stats

    if not metadata:
        empty = RerankerResponse(
            question=question,
            top_k=TOP_K,
            ranked_tables=[],
            notes="No in-scope tables found via Knowledge Catalog search.",
        )
        callback_context.state["reranker_result_kc_search"] = (
            empty.model_dump_json()
        )
        return types.Content(
            role="model",
            parts=[types.Part(text=(
                "**[Approach 2: Knowledge Catalog Search]**\n\n"
                "No in-scope tables found via catalog search."
            ))],
        )

    top_k = callback_context.state.get("top_k", TOP_K)

    result = await asyncio.to_thread(
        call_reranker,
        question=question,
        candidate_metadata=metadata,
        discovery_method="kc_search",
        top_k=top_k,
    )

    callback_context.state["reranker_result_kc_search"] = (
        result.model_dump_json()
    )
    return types.Content(
        role="model",
        parts=[types.Part(text=format_reranker_markdown(
            result, "Approach 2: Knowledge Catalog Search"
        ))],
    )
