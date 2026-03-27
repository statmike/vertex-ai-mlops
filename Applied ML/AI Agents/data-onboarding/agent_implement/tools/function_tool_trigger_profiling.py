"""Trigger Dataplex data profile scans for bronze and meta tables."""

import logging

from google.adk import tools

from agent_orchestrator.config import (
    BQ_BRONZE_DATASET,
    BQ_META_DATASET,
    DATAPLEX_LOCATION,
    GOOGLE_CLOUD_PROJECT,
)
from agent_orchestrator.util_dataplex import create_and_run_profile_scans
from agent_orchestrator.util_metadata import write_processing_log

logger = logging.getLogger(__name__)

META_TABLE_NAMES = [
    "source_manifest",
    "processing_log",
    "table_lineage",
    "schema_decisions",
    "web_provenance",
]


async def trigger_profiling(
    tool_context: tools.ToolContext,
) -> str:
    """Trigger Dataplex data profile scans for bronze and meta tables.

    Reads ``tables_created`` and ``bq_bronze_dataset`` from state, then
    creates and starts Dataplex profile scans for both the bronze data
    tables and the shared metadata tables. Scans run asynchronously —
    this tool does NOT wait for them to complete.

    Must be called after ``execute_sql`` has completed successfully.

    Args:
        tool_context: The ADK tool context for accessing shared state.

    Returns:
        Summary of profile scans triggered, or an error message.
    """
    try:
        tables_created = tool_context.state.get("tables_created", {})
        if not tables_created:
            return "No tables created yet. Run execute_sql first."

        if not GOOGLE_CLOUD_PROJECT:
            return "Cannot trigger profiling: GOOGLE_CLOUD_PROJECT not set."

        bronze_dataset = tool_context.state.get("bq_bronze_dataset", BQ_BRONZE_DATASET)
        table_names = list(tables_created.keys())

        # Profile bronze tables
        result = create_and_run_profile_scans(
            project=GOOGLE_CLOUD_PROJECT,
            location=DATAPLEX_LOCATION,
            dataset=bronze_dataset,
            table_names=table_names,
        )

        source_id = tool_context.state.get("source_id", "")
        if source_id:
            write_processing_log(
                source_id, "implement", "trigger_profiling", "completed",
                details=result,
            )

        summary = (
            f"Bronze table profile scans triggered.\n"
            f"  Scans created: {result['scans_created']}\n"
            f"  Scans started: {result['scans_started']}\n"
            f"  Tables: {', '.join(table_names)}\n"
        )
        if result["errors"]:
            summary += f"  Errors: {'; '.join(result['errors'])}\n"

        # Profile meta tables
        try:
            meta_result = create_and_run_profile_scans(
                project=GOOGLE_CLOUD_PROJECT,
                location=DATAPLEX_LOCATION,
                dataset=BQ_META_DATASET,
                table_names=META_TABLE_NAMES,
            )
            summary += (
                f"\nMeta table profile scans triggered.\n"
                f"  Scans created: {meta_result['scans_created']}\n"
                f"  Scans started: {meta_result['scans_started']}\n"
                f"  Tables: {', '.join(META_TABLE_NAMES)}\n"
            )
            if meta_result["errors"]:
                summary += f"  Errors: {'; '.join(meta_result['errors'])}\n"
        except Exception as e:
            summary += f"\nMeta table profiling error: {e}\n"

        return summary

    except Exception as e:
        return f"Error triggering profile scans: {e}"
