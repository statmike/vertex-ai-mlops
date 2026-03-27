"""Callback: semantic search + cached context lookup + rerank.

Runs the entire Approach 5 workflow deterministically in
``before_agent_callback`` so no LLM agent calls are needed.

Combines Dataplex semantic search (like Approach 2) to narrow to ~20
candidates with detailed cached context (like Approach 3) for those matches.
"""

import asyncio

from google.adk.agents.callback_context import CallbackContext
from google.cloud import dataplex_v1
from google.genai import types

from config import (
    GOOGLE_CLOUD_PROJECT,
    TOP_K,
    is_table_in_scope,
)
from context_cache import get_detailed_for_tables
from reranker.util_rerank import call_reranker, format_reranker_markdown
from schemas import RerankerResponse


def _search_and_get_cached(question: str) -> tuple[str, list[str]]:
    """Semantic search + cached context lookup.

    Returns:
        Tuple of (detailed_metadata_string, matched_table_ids).
    """
    client = dataplex_v1.CatalogServiceClient()

    # Step 1: Semantic search (same as Approach 2)
    query = f"({question}) AND system=BIGQUERY"
    request = dataplex_v1.SearchEntriesRequest(
        name=f"projects/{GOOGLE_CLOUD_PROJECT}/locations/global",
        query=query,
        page_size=20,
        semantic_search=True,
    )

    matched_ids = []
    for result in client.search_entries(request=request):
        entry = result.dataplex_entry
        fqn = entry.fully_qualified_name or ""
        parts = fqn.rsplit(".", 2)
        if len(parts) >= 2:
            ds_name = parts[-2]
            tbl_name = parts[-1]
            if not is_table_in_scope(ds_name, tbl_name):
                continue
            full_id = f"{GOOGLE_CLOUD_PROJECT}.{ds_name}.{tbl_name}"
            matched_ids.append(full_id)

    # Step 2: Cache lookup instead of lookup_entry
    detailed = get_detailed_for_tables(matched_ids)
    return detailed, matched_ids


async def discover_and_rerank(callback_context: CallbackContext):
    """Semantic search + cache lookup + rerank — no LLM needed.

    1. Extract the user's question from callback context.
    2. Run Dataplex semantic search to narrow candidates.
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

    detailed, matched_ids = await asyncio.to_thread(
        _search_and_get_cached, question
    )

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
