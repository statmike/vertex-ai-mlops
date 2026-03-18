import logging

from google.adk import tools

from agent_acquire.tools.util_common import log_tool_error
from agent_orchestrator.config import (
    GOOGLE_CLOUD_PROJECT,
    gcs_bucket_name,
)
from agent_orchestrator.util_lineage import publish_lineage as _publish
from agent_orchestrator.util_metadata import write_processing_log

logger = logging.getLogger(__name__)


async def publish_lineage(
    tool_context: tools.ToolContext,
) -> str:
    """Publish end-to-end data lineage to Dataplex Data Lineage API.

    Reads the crawl graph, file mappings, external table IDs, and created
    table IDs from agent state to build and publish a complete lineage
    chain from the original source URL through to BigQuery external tables.
    BigQuery automatically captures the final hop from external table to
    materialized table.

    Must be called after ``execute_sql`` has completed successfully.

    Args:
        tool_context: The ADK tool context for accessing shared state.

    Returns:
        Summary of published lineage events, or an error message.
    """
    try:
        source_id = tool_context.state.get("source_id", "")
        source_uri = tool_context.state.get("source_uri", "")
        tables_created = tool_context.state.get("tables_created", {})
        external_tables = tool_context.state.get("external_tables", {})
        files_acquired = tool_context.state.get("files_acquired", [])
        proposed_tables = tool_context.state.get("proposed_tables", {})

        if not tables_created:
            return "No tables created yet. Run execute_sql first."
        if not source_uri:
            return "No source_uri in state. Cannot determine starting URL."
        if not GOOGLE_CLOUD_PROJECT:
            return "Cannot publish lineage: GOOGLE_CLOUD_PROJECT not set."

        # Build lookup: gcs_path → file acquisition info
        path_to_file: dict[str, dict] = {}
        for f in files_acquired:
            gcs_path = f.get("gcs_path", "")
            if gcs_path:
                path_to_file[gcs_path] = f

        # Assemble lineage entries for each created table
        file_lineage = []
        bucket = gcs_bucket_name()

        for table_name in tables_created:
            proposal = proposed_tables.get(table_name, {})
            source_path = proposal.get("source_path", "")
            file_info = path_to_file.get(source_path, {})
            ext_table_id = external_tables.get(table_name, "")

            # Build GCS URI
            if source_path.startswith("gs://"):
                gcs_uri = source_path
            else:
                gcs_uri = f"gs://{bucket}/{source_path}"

            file_lineage.append({
                "file_url": file_info.get("url", ""),
                "gcs_uri": gcs_uri,
                "external_table": ext_table_id,
            })

        result = _publish(
            source_id=source_id,
            starting_url=source_uri,
            file_lineage=file_lineage,
        )

        # Log to processing log
        if source_id:
            status = "completed" if result.get("events_created", 0) > 0 else "failed"
            write_processing_log(
                source_id, "implement", "publish_lineage", status,
                details=result,
            )

        if "error" in result:
            return f"Lineage publishing failed: {result['error']}"

        return (
            f"Lineage published to Dataplex.\n"
            f"  Process: {result.get('process', '')}\n"
            f"  Run: {result.get('run', '')}\n"
            f"  Events created: {result.get('events_created', 0)}\n"
            f"\nLineage chain per file:\n"
            f"  1. Starting URL → File download URL\n"
            f"  2. File URL → GCS staging object\n"
            f"  3. GCS object → External BQ table\n"
            f"  4. External table → Materialized table (auto-captured by BQ)\n"
        )

    except Exception as e:
        return log_tool_error("publish_lineage", e)
