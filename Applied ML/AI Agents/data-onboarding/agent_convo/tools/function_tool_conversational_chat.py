"""Conversational Analytics API tool for answering questions about BigQuery data.

Adapted from concept-bq/agent_convo_api/tools/conversational_chat.py.
"""

import logging

from google.adk import tools

from .util_conversational_api import call_conversational_api

logger = logging.getLogger(__name__)


def _tables_from_reranker(reranker_result: dict) -> list[dict[str, str]]:
    """Extract BigQuery table references from a reranker result dict."""
    tables = []
    for rt in reranker_result.get("ranked_tables", []):
        table_id = rt.get("table_id", "")
        parts = table_id.split(".")
        if len(parts) != 3:
            continue
        tables.append({
            "project_id": parts[0],
            "dataset_id": parts[1],
            "table_id": parts[2],
        })
    return tables


async def conversational_chat(
    question: str,
    chart: bool,
    tool_context: tools.ToolContext,
    bigquery_tables: list[dict[str, str]] | None = None,
    thinking_mode: str | None = None,
) -> str:
    """Answer a question using the Conversational Analytics API.

    This API analyzes BigQuery data sources and responds with answers,
    data tables, and visual charts.

    Args:
        question: The user's question.
        chart: Whether the user is requesting a chart or other visual.
        bigquery_tables: Optional list of dicts, each with ``project_id``,
            ``dataset_id``, and ``table_id``. When omitted, tables are
            auto-extracted from the ``reranker_result`` in session state.
        tool_context: The ADK tool context for session state.
        thinking_mode: Optional thinking mode override — ``"THINKING"``
            (deliberate, high quality) or ``"FAST"`` (quick, lower latency).
            If not provided, uses the ``CONVO_THINKING_MODE`` env var default.

    Returns:
        The API response as text, or a message about a chart artifact.

    Example::

        conversational_chat(
            question="What providers have the largest bed sizes?",
            chart=False,
        )
    """
    # Auto-pick tables from reranker result if not explicitly provided
    if bigquery_tables is None:
        reranker_result = tool_context.state.get("reranker_result")
        if reranker_result:
            bigquery_tables = _tables_from_reranker(reranker_result)
            logger.info(
                "Auto-picked %d tables from reranker_result", len(bigquery_tables)
            )

    if not bigquery_tables:
        return (
            "No tables available. Either provide bigquery_tables or ensure "
            "the reranker has run and stored results in state."
        )

    # Build enriched context from reranker if available
    reranker_result = tool_context.state.get("reranker_result")

    return await call_conversational_api(
        question=question,
        chart=chart,
        bigquery_tables=bigquery_tables,
        tool_context=tool_context,
        session_state_key="conversational_api_sessions",
        artifact_key="conversational_analytics_api_chart",
        reranker_result=reranker_result,
        system_instruction=(
            "Help users explore, analyze, and give detailed reports "
            "for the provided data sources."
        ),
        thinking_mode=thinking_mode,
    )
