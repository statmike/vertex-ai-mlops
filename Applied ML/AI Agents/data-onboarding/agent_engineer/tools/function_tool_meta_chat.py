"""Conversational Analytics API tool for querying pipeline metadata tables.

Uses the shared ``call_conversational_api`` utility with hardcoded meta
tables and a separate session key (``meta_api_sessions``).
"""

import logging

from google.adk import tools

from agent_convo.tools.util_conversational_api import call_conversational_api
from agent_orchestrator.config import BQ_META_DATASET, CHAT_SCOPE, GOOGLE_CLOUD_PROJECT

logger = logging.getLogger(__name__)

META_TABLE_NAMES = [
    "source_manifest",
    "processing_log",
    "table_lineage",
    "schema_decisions",
    "web_provenance",
    "data_catalog",
]


def _build_meta_table_refs() -> list[dict[str, str]]:
    """Build BigQuery table references for all meta tables."""
    return [
        {
            "project_id": GOOGLE_CLOUD_PROJECT,
            "dataset_id": BQ_META_DATASET,
            "table_id": table_name,
        }
        for table_name in META_TABLE_NAMES
    ]


async def meta_chat(
    question: str,
    chart: bool,
    tool_context: tools.ToolContext,
    thinking_mode: str | None = None,
) -> str:
    """Answer a question about pipeline metadata using the Conversational Analytics API.

    Queries the shared metadata tables (processing log, lineage, schema
    decisions, source manifest, web provenance, data catalog) to answer
    questions about the data onboarding pipeline.

    Args:
        question: The user's question about pipeline metadata.
        chart: Whether the user is requesting a chart or visual.
        tool_context: The ADK tool context for session state.
        thinking_mode: Optional thinking mode override — ``"THINKING"``
            (deliberate, high quality) or ``"FAST"`` (quick, lower latency).
            If not provided, uses the ``CONVO_THINKING_MODE`` env var default.

    Returns:
        The API response as text, or a message about a chart artifact.
    """
    # Build scope filter for the system instruction
    scope_instruction = ""
    if CHAT_SCOPE:
        scope_datasets = ", ".join(f"'{ds}'" for ds in CHAT_SCOPE)
        scope_instruction = (
            f"\n\nIMPORTANT — Data Scope:\n"
            f"Only return results for the following dataset(s): {scope_datasets}.\n"
            f"- **data_catalog**: filter on `dataset_name` IN ({scope_datasets}).\n"
            f"- **All other tables** (table_lineage, processing_log, "
            f"schema_decisions, source_manifest, web_provenance): filter on "
            f"`source_id`. Find the matching source_id by joining to "
            f"data_catalog ON source_id, or by looking up which source_id "
            f"corresponds to the scoped dataset_name.\n"
            f"Always apply this scope filter. Never return results from "
            f"other data sources."
        )

    return await call_conversational_api(
        question=question,
        chart=chart,
        bigquery_tables=_build_meta_table_refs(),
        tool_context=tool_context,
        session_state_key="meta_api_sessions",
        artifact_key="meta_chat_chart",
        system_instruction=(
            "Help users explore pipeline metadata, processing history, "
            "data lineage, schema decisions, and source provenance.\n\n"
            "Key table guidance:\n"
            "- **data_catalog**: has `tables_created` (integer count of tables created per "
            "onboarded source), `dataset_name`, `source_uri`, `domain`, `onboarded_at`. "
            "Use this table for questions about how many tables exist, what was onboarded, "
            "or dataset summaries. Do NOT use INFORMATION_SCHEMA — use data_catalog instead.\n"
            "- **table_lineage**: maps each table to its source files and transformations.\n"
            "- **processing_log**: timestamped log of onboarding steps and outcomes.\n"
            "- **schema_decisions**: records why columns/types were chosen.\n"
            "- **source_manifest**: inventory of downloaded files with sizes and formats.\n"
            "- **web_provenance**: crawl graph of discovered URLs and pages."
            + scope_instruction
        ),
        thinking_mode=thinking_mode,
    )
