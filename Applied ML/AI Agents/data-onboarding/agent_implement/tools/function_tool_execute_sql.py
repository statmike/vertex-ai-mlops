import logging

from google.adk import tools

from agent_acquire.tools.util_common import log_tool_error
from agent_orchestrator.config import (
    BQ_BRONZE_DATASET,
    GOOGLE_CLOUD_PROJECT,
)
from agent_orchestrator.util_metadata import write_processing_log, write_table_lineage

from .util_sql import _build_create_table_ddl, build_select_sql

logger = logging.getLogger(__name__)


async def execute_sql(
    tool_context: tools.ToolContext,
) -> str:
    """Execute SQL to materialize BigQuery tables from external tables.

    For each proposed table that has a corresponding external table, builds a
    SELECT statement directly from the proposal columns and runs
    ``CREATE OR REPLACE TABLE ... AS SELECT`` to produce the final table.

    Args:
        tool_context: The ADK tool context for accessing shared state.

    Returns:
        Summary of executed tables, or an error message.
    """
    try:
        proposals = tool_context.state.get("proposed_tables", {})
        external_tables = tool_context.state.get("external_tables", {})

        if not proposals:
            return "No proposed tables. Run the design phase first."
        if not external_tables:
            return "No external tables. Run create_external_tables first."
        if not GOOGLE_CLOUD_PROJECT:
            return "Cannot execute SQL: GOOGLE_CLOUD_PROJECT not set."

        from google.cloud import bigquery

        client = bigquery.Client(project=GOOGLE_CLOUD_PROJECT)

        tables_created = {}
        executed = []
        errors = []
        source_id = tool_context.state.get("source_id", "")

        # Build file URL lookup from files_acquired
        files_acquired = tool_context.state.get("files_acquired", [])
        path_to_url = {}
        for f in files_acquired:
            gcs_path = f.get("gcs_path", "")
            if gcs_path:
                path_to_url[gcs_path] = f.get("url", "")

        lineage_rows = []

        for table_name, proposal in proposals.items():
            ext_table_id = external_tables.get(table_name)
            if not ext_table_id:
                errors.append(f"{table_name}: no external table")
                continue

            columns = proposal.get("enriched_columns", proposal.get("columns", []))
            source_path = proposal.get("source_path", "")
            original_url = path_to_url.get(source_path, "")

            # Build SELECT from column definitions
            select_sql = build_select_sql(
                columns=columns,
                from_ref=ext_table_id,
                source_uri=source_path,
                original_url=original_url,
                source_id=source_id,
            )

            # Build and execute DDL
            target_table_id = f"{GOOGLE_CLOUD_PROJECT}.{BQ_BRONZE_DATASET}.{table_name}"
            ddl = _build_create_table_ddl(
                table_id=target_table_id,
                select_sql=select_sql,
                partition_by=proposal.get("partition_by"),
                cluster_by=proposal.get("cluster_by"),
            )

            query_job = client.query(ddl)
            query_job.result()

            # Get row count
            table_obj = client.get_table(target_table_id)
            row_count = table_obj.num_rows

            tables_created[table_name] = {
                "rows": row_count,
                "table_id": target_table_id,
            }
            executed.append(f"{table_name}: {row_count} rows")

            # Build column mappings for lineage
            column_mappings = {
                col.get("source_name", col["name"]): col["name"]
                for col in columns
            }
            lineage_rows.append({
                "source_id": source_id,
                "bq_table": target_table_id,
                "external_table": ext_table_id,
                "source_file": source_path,
                "column_mappings": column_mappings,
            })

        tool_context.state["tables_created"] = tables_created

        # Write table lineage and processing log
        if source_id and lineage_rows:
            write_table_lineage(lineage_rows)

        if source_id:
            write_processing_log(
                source_id, "implement", "execute_sql", "completed",
                details={
                    "tables": len(executed),
                    "errors": len(errors),
                    "rows": {k: v["rows"] for k, v in tables_created.items()},
                },
            )

        result = f"SQL execution: {len(executed)} tables created, {len(errors)} errors\n"
        if executed:
            result += "\nCreated:\n"
            for e in executed:
                result += f"  - {e}\n"
        if errors:
            result += "\nErrors:\n"
            for e in errors:
                result += f"  - {e}\n"

        return result

    except Exception as e:
        return log_tool_error("execute_sql", e)
