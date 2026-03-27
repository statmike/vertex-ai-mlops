"""Callback: read cached Knowledge Context + rerank.

Runs the entire Approach 3 workflow deterministically in
``before_agent_callback`` so no LLM agent calls are needed.
"""

import asyncio

from google.adk.agents.callback_context import CallbackContext
from google.genai import types

from config import TOP_K
from context_cache import get_all_detailed, get_table_ids
from reranker.util_rerank import call_reranker, format_reranker_markdown
from schemas import RerankerResponse


async def discover_and_rerank(callback_context: CallbackContext):
    """Pre-fetch context + rerank in a single callback — no LLM needed.

    1. Read context from the shared cache.
    2. Call the shared ``call_reranker`` (Gemini structured output).
    3. Store the result in state for the compare agent.
    4. Return types.Content so the agent skips the LLM entirely.
    """
    user_content = callback_context.user_content
    if not user_content or not user_content.parts:
        return None  # No question — fall back to LLM + tools

    question = user_content.parts[0].text
    if not question:
        return None

    context = get_all_detailed()
    nominated_ids = get_table_ids()

    # Store nominations in state (all cached tables for this approach)
    callback_context.state["nominated_tables_dataplex_context"] = nominated_ids

    if not context:
        empty = RerankerResponse(
            question=question,
            top_k=TOP_K,
            ranked_tables=[],
            notes="No knowledge context available.",
        )
        callback_context.state["reranker_result_dataplex_context"] = (
            empty.model_dump_json()
        )
        return types.Content(
            role="model",
            parts=[types.Part(text=(
                "**[Approach 3: Dataplex Context]**\n\n"
                "No knowledge context available for tables in scope."
            ))],
        )

    top_k = callback_context.state.get("top_k", TOP_K)

    result = await asyncio.to_thread(
        call_reranker,
        question=question,
        candidate_metadata=context,
        discovery_method="dataplex_context",
        top_k=top_k,
    )

    callback_context.state["reranker_result_dataplex_context"] = (
        result.model_dump_json()
    )
    return types.Content(
        role="model",
        parts=[types.Part(text=format_reranker_markdown(
            result, "Approach 3: Dataplex Context"
        ))],
    )
