"""Reranker tool — two-pass approach using compact shortlist then detailed ranking."""

import asyncio
import logging

from google.adk import tools

from agent_context.catalog import _catalog_data, _catalog_summary

from .util_rerank import call_reranker_two_pass, format_reranker_markdown

logger = logging.getLogger(__name__)


async def rerank_tables(
    question: str,
    tool_context: tools.ToolContext,
) -> str:
    """Rank tables by relevance using a two-pass approach.

    Pass 1: Screens all tables using compact summaries.
    Pass 2: Ranks shortlisted tables using full metadata.

    The catalog data is pre-loaded at startup — no external calls needed.

    Args:
        question: The user's original question.
        tool_context: The ADK tool context for session state.

    Returns:
        Formatted markdown with ranked tables and guidance.
    """
    try:
        if not _catalog_data:
            return "No catalog data available. The catalog may not have loaded at startup."

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            call_reranker_two_pass,
            question,
            _catalog_summary,
            _catalog_data,
        )

        # Store structured result in state for agent_convo
        tool_context.state["reranker_result"] = result.model_dump()

        return format_reranker_markdown(result)

    except Exception as e:
        logger.warning("Reranker failed: %s", e)
        return f"Reranker error: {e}. Falling back to all candidate tables."
