"""Reranker tool — uses Gemini structured output to rank tables by relevance."""

import asyncio
import logging

from google.adk import tools

from .util_rerank import call_reranker, format_reranker_markdown

logger = logging.getLogger(__name__)


async def rerank_tables(
    question: str,
    candidate_metadata: str,
    tool_context: tools.ToolContext,
) -> str:
    """Rank candidate BigQuery tables by relevance to a user's question.

    Uses Gemini with structured output to evaluate candidate tables and
    return them ranked by relevance with key columns, SQL hints, and
    join suggestions.

    Args:
        question: The user's original question.
        candidate_metadata: Merged table metadata (schemas, descriptions,
            profile statistics) as a text block.
        tool_context: The ADK tool context for session state.

    Returns:
        Formatted markdown with ranked tables and guidance.
    """
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            call_reranker,
            question,
            candidate_metadata,
        )

        # Store structured result in state for agent_convo
        tool_context.state["reranker_result"] = result.model_dump()

        return format_reranker_markdown(result)

    except Exception as e:
        logger.warning("Reranker failed: %s", e)
        return f"Reranker error: {e}. Falling back to all candidate tables."
