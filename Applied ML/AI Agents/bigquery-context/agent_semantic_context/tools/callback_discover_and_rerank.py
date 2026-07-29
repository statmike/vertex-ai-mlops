"""Callback: semantic search + cached context lookup + rerank.

Runs the entire Approach 5 workflow deterministically in
``before_agent_callback`` so no LLM agent calls are needed.

Combines Knowledge Catalog semantic search (like Approach 2) to narrow to ~20
candidates with detailed cached context (like Approach 3) for those matches.
"""

import asyncio

from google.adk.agents.callback_context import CallbackContext
from google.cloud import dataplex_v1
from google.genai import types

from config import (
    GOOGLE_CLOUD_PROJECT,
    TOP_K,
    get_datasets,
    is_table_in_scope,
)
from context_cache import get_detailed_for_tables
from reranker.util_rerank import call_reranker, format_reranker_markdown
from schemas import RerankerResponse


def _search_and_get_cached(question: str) -> tuple[str, list[str], dict]:
    """Semantic search + cached context lookup.

    Returns:
        Tuple of (detailed_metadata_string, matched_table_ids, search_stats),
        where ``search_stats`` records the *raw* count the API returned vs. what
        survived our client-side scope filter. The ``parent:`` predicate is
        advisory, not enforced, so the API can fill the page budget with tables
        from unrelated datasets; this instrumentation makes that visible per run.
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
    matched_ids = []
    for result in client.search_entries(request=request):
        raw_count += 1
        entry = result.dataplex_entry
        fqn = entry.fully_qualified_name or ""
        parts = fqn.rsplit(".", 2)
        if len(parts) >= 2:
            ds_name = parts[-2]
            tbl_name = parts[-1]
            if not is_table_in_scope(ds_name, tbl_name):
                out_of_scope_dropped += 1
                continue
            full_id = f"{GOOGLE_CLOUD_PROJECT}.{ds_name}.{tbl_name}"
            matched_ids.append(full_id)

    stats = {
        "raw_search_count": raw_count,
        "out_of_scope_dropped": out_of_scope_dropped,
        "page_size": 20,
    }

    # Step 2: Cache lookup instead of lookup_entry
    detailed = get_detailed_for_tables(matched_ids)
    return detailed, matched_ids, stats


async def discover_and_rerank(callback_context: CallbackContext):
    """Semantic search + cache lookup + rerank — no LLM needed.

    1. Extract the user's question from callback context.
    2. Run Knowledge Catalog semantic search to narrow candidates.
    3. Look up detailed cached context for matched tables.
    4. Call the shared ``call_reranker`` (Gemini structured output).
    5. Store the result in state for the compare agent.
    6. Return types.Content so the agent skips the LLM entirely.
    """
    user_content = callback_context.user_content
    if not user_content or not user_content.parts:
        return None  # No question — fall back to LLM + tools

    question = user_content.parts[0].text
    if not question:
        return None

    detailed, matched_ids, search_stats = await asyncio.to_thread(
        _search_and_get_cached, question
    )

    # Store nominations in state
    callback_context.state["nominated_tables_semantic_context"] = matched_ids
    # Raw-vs-filtered search stats (see kc_search callback): lets the report
    # separate the relevance-gap regime from the scope-leak regime per run.
    callback_context.state["search_stats_semantic_context"] = search_stats

    if not detailed:
        empty = RerankerResponse(
            question=question,
            top_k=TOP_K,
            ranked_tables=[],
            notes=(
                "No in-scope tables found via semantic search, "
                "or no cached context available for matches."
            ),
        )
        callback_context.state["reranker_result_semantic_context"] = (
            empty.model_dump_json()
        )
        return types.Content(
            role="model",
            parts=[types.Part(text=(
                "**[Approach 5: Semantic Context]**\n\n"
                "No in-scope tables found via semantic search."
            ))],
        )

    top_k = callback_context.state.get("top_k", TOP_K)

    result = await asyncio.to_thread(
        call_reranker,
        question=question,
        candidate_metadata=detailed,
        discovery_method="semantic_context",
        top_k=top_k,
    )

    callback_context.state["reranker_result_semantic_context"] = (
        result.model_dump_json()
    )
    return types.Content(
        role="model",
        parts=[types.Part(text=format_reranker_markdown(
            result, "Approach 5: Semantic Context"
        ))],
    )
