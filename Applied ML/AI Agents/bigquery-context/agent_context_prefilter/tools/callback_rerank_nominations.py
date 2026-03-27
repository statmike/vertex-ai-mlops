"""Callback: rerank nominated tables with full detailed metadata.

Runs as ``after_agent_callback`` — executes exactly once after the LLM
has finished nominating tables via the ``nominate_tables`` tool.
"""

import asyncio

from google.adk.agents.callback_context import CallbackContext

from config import TOP_K
from context_cache import get_detailed_for_tables
from reranker.util_rerank import call_reranker
from schemas import RerankerResponse


async def rerank_nominations(callback_context: CallbackContext):
    """After-agent callback: rerank nominated tables with full detail.

    1. Read nominated table IDs from state.
    2. Fetch detailed cached context for those tables.
    3. Call the shared ``call_reranker`` (Gemini structured output).
    4. Store the result in state for the compare agent.
    5. Don't return Content — let the LLM's response stand as the agent output.
    """
    nominated = callback_context.state.get("nominated_tables", [])

    # Store nominations with the standard key for the compare agent
    callback_context.state["nominated_tables_context_prefilter"] = nominated

    user_content = callback_context.user_content
    if not user_content or not user_content.parts:
        return None
    question = user_content.parts[0].text
    if not question:
        return None

    if not nominated:
        empty = RerankerResponse(
            question=question,
            top_k=TOP_K,
            ranked_tables=[],
            notes="No tables were nominated by the pre-filter.",
        )
        callback_context.state["reranker_result_context_prefilter"] = (
            empty.model_dump_json()
        )
        return None

    detailed = get_detailed_for_tables(nominated)

    if not detailed:
        empty = RerankerResponse(
            question=question,
            top_k=TOP_K,
            ranked_tables=[],
            notes="Nominated tables had no cached detailed context.",
        )
        callback_context.state["reranker_result_context_prefilter"] = (
            empty.model_dump_json()
        )
        return None

    top_k = callback_context.state.get("top_k", TOP_K)

    result = await asyncio.to_thread(
        call_reranker,
        question=question,
        candidate_metadata=detailed,
        discovery_method="context_prefilter",
        top_k=top_k,
    )

    callback_context.state["reranker_result_context_prefilter"] = (
        result.model_dump_json()
    )
    # Don't return Content — let the LLM's response stand as the agent output
