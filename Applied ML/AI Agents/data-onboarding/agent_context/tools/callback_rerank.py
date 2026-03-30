"""Deterministic before_agent_callback: run reranker before the LLM.

Runs the two-pass reranker in ``before_agent_callback`` so it executes
deterministically on every invocation — the LLM never decides whether to
call the reranker.  After storing the result in state, the callback returns
``None`` so the LLM gets a turn to handle the transfer to ``agent_convo``.
"""

import asyncio
import logging

from google.adk.agents.callback_context import CallbackContext

from agent_context.catalog import _catalog_data, _catalog_summary

from .util_rerank import call_reranker_two_pass, format_reranker_markdown

logger = logging.getLogger(__name__)


async def rerank_and_transfer(callback_context: CallbackContext):
    """Run two-pass reranker and store results in state.

    1. Extract the user question from callback_context.user_content.
    2. Call the two-pass reranker (shortlist → detail).
    3. Store the structured result AND formatted markdown in session state.
    4. Return None — the LLM runs next and transfers to agent_convo.

    The LLM's only job is to transfer to agent_convo.  The reranker result
    is already in state for agent_convo to auto-pick tables.
    """
    # Guard: skip if the reranker already ran (prevents double-invocation
    # when agent_chat re-invokes agent_context after agent_convo answers)
    if callback_context.state.get("reranker_result"):
        return None

    user_content = callback_context.user_content
    if not user_content or not user_content.parts:
        return None

    question = user_content.parts[0].text
    if not question:
        return None

    if not _catalog_data:
        return None

    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            call_reranker_two_pass,
            question,
            _catalog_summary,
            _catalog_data,
        )

        # Store structured result in state for agent_convo
        callback_context.state["reranker_result"] = result.model_dump()

        # Store formatted markdown so the LLM can see what was found
        callback_context.state["reranker_markdown"] = format_reranker_markdown(result)

        logger.info(
            "Reranker callback: found %d table(s) for: %s",
            len(result.ranked_tables),
            question[:80],
        )

    except Exception as e:
        logger.warning("Reranker callback failed: %s", e)

    # Always return None — let the LLM handle the transfer
    return None
