"""Callback: semantic search + cached context lookup + rerank.

Runs the entire Approach 5 workflow deterministically in
``before_agent_callback`` so no LLM agent calls are needed. Its distinctive step
is sourcing rich metadata from the shared cache (like Approach 3) for the tables
that semantic search narrowed to (like Approach 2); the scoped search, question
extraction, reranking, and emit are shared helpers in ``discovery_common``.
"""

import asyncio

from google.adk.agents.callback_context import CallbackContext

from context_cache import get_detailed_for_tables
from discovery_common import (
    emit,
    get_question,
    plain_content,
    rerank_and_store,
    search_entries_scoped,
    store_empty,
)

LABEL = "Approach 5: Semantic Context"
METHOD = "semantic_context"


def _search_and_get_cached(question: str) -> tuple[str, list[str], dict]:
    """Semantic search to narrow candidates, then cached context for the matches.

    Returns (detailed_metadata_string, matched_table_ids, search_stats).
    """
    hits, stats = search_entries_scoped(question)
    matched_ids = [hit.table_id for hit in hits]
    detailed = get_detailed_for_tables(matched_ids)
    return detailed, matched_ids, stats


async def discover_and_rerank(callback_context: CallbackContext):
    """Semantic search + cache lookup + rerank — no LLM needed."""
    question = get_question(callback_context)
    if not question:
        return None  # No question — fall back to LLM + tools

    detailed, matched_ids, search_stats = await asyncio.to_thread(_search_and_get_cached, question)

    callback_context.state["nominated_tables_semantic_context"] = matched_ids
    callback_context.state["search_stats_semantic_context"] = search_stats

    if not detailed:
        store_empty(
            callback_context,
            METHOD,
            question,
            "No in-scope tables found via semantic search, or no cached context for matches.",
        )
        return plain_content(LABEL, "No in-scope tables found via semantic search.")

    result = await rerank_and_store(callback_context, question, detailed, METHOD)
    return emit(LABEL, result)
