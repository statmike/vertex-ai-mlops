import logging

from google.adk import tools

from agent_acquire.tools.util_common import log_tool_error
from agent_orchestrator.config import (
    BQ_BRONZE_DATASET,
    BQ_DATASET_LOCATION,
    GOOGLE_CLOUD_PROJECT,
)
from agent_orchestrator.util_metadata import write_processing_log, write_table_lineage

from .util_sql import _build_create_table_ddl, build_select_sql, refine_partition_cluster

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

        # Read domain-scoped bronze dataset from state (set by initialize_source)
        bronze_dataset = tool_context.state.get("bq_bronze_dataset", BQ_BRONZE_DATASET)

        # Ensure bronze dataset exists
        dataset_ref = f"{GOOGLE_CLOUD_PROJECT}.{bronze_dataset}"
        ds = bigquery.Dataset(dataset_ref)
        ds.location = BQ_DATASET_LOCATION
        client.create_dataset(ds, exists_ok=True)

        tables_created = {}
        executed = []
        errors = []
        source_id = tool_context.state.get("source_id", "")

        # Build file URL lookup from files_acquired
        files_acquired = tool_context.state.get("files_acquired", [])
        path_to_url: dict[str, str] = {}
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
            # Support grouped tables with source_paths (list) or legacy source_path (string)
            source_paths = proposal.get("source_paths", [])
            if not source_paths:
                sp = proposal.get("source_path", "")
                source_paths = [sp] if sp else []
            source_path = source_paths[0] if source_paths else ""
            original_url = path_to_url.get(source_path, "")

            try:
                # Refine partition/cluster based on actual data cardinality
                proposed_partition = proposal.get("partition_by")
                proposed_cluster = proposal.get("cluster_by", [])
                refined_partition, refined_cluster = refine_partition_cluster(
                    client=client,
                    ext_table_id=ext_table_id,
                    partition_by=proposed_partition,
                    cluster_by=proposed_cluster,
                    columns=columns,
                )

                # Build SELECT from column definitions
                select_sql = build_select_sql(
                    columns=columns,
                    from_ref=ext_table_id,
                    source_uri=source_path,
                    original_url=original_url,
                    source_id=source_id,
                )

                # Build and execute DDL
                target_table_id = f"{GOOGLE_CLOUD_PROJECT}.{bronze_dataset}.{table_name}"
                ddl = _build_create_table_ddl(
                    table_id=target_table_id,
                    select_sql=select_sql,
                    partition_by=refined_partition,
                    cluster_by=refined_cluster,
                    columns=columns,
                )

                query_job = client.query(ddl)
                query_job.result()

                # Apply column descriptions to the table schema
                table_obj = client.get_table(target_table_id)
                desc_map = {col["name"]: col.get("description", "") for col in columns}
                new_schema = []
                for field in table_obj.schema:
                    desc = desc_map.get(field.name, "")
                    if desc:
                        new_schema.append(bigquery.SchemaField(
                            name=field.name,
                            field_type=field.field_type,
                            mode=field.mode,
                            description=desc,
                            fields=field.fields,
                        ))
                    else:
                        new_schema.append(field)
                table_obj.schema = new_schema
                client.update_table(table_obj, ["schema"])

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
                # Create a lineage row for each source file in the group
                for sp in source_paths:
                    lineage_rows.append({
                        "source_id": source_id,
                        "bq_table": target_table_id,
                        "external_table": ext_table_id,
                        "source_file": sp,
                        "column_mappings": column_mappings,
                    })
            except Exception as e:
                logger.warning(f"Failed to create table {table_name}: {e}")
                errors.append(f"{table_name}: {e}")

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
