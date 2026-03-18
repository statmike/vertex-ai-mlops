import logging

from google.adk import tools

from agent_acquire.tools.util_common import log_tool_error
from agent_orchestrator.config import (
    BQ_BRONZE_DATASET,
    GOOGLE_CLOUD_PROJECT,
)

logger = logging.getLogger(__name__)


async def apply_bq_metadata(
    tool_context: tools.ToolContext,
) -> str:
    """
    Apply table and column descriptions and labels to BigQuery tables.

    Reads proposed_tables from state and updates BQ table metadata
    including table description, column descriptions, and labels.

    Args:
        tool_context: The ADK tool context for accessing shared state.

    Returns:
        Summary of applied metadata, or an error message.
    """
    try:
        proposals = tool_context.state.get("proposed_tables", {})

        if not proposals:
            return "No proposed tables to apply metadata to."

        if not GOOGLE_CLOUD_PROJECT:
            return "Cannot apply BQ metadata: GOOGLE_CLOUD_PROJECT not set."

        from google.cloud import bigquery

        client = bigquery.Client(project=GOOGLE_CLOUD_PROJECT)
        applied = []
        errors = []

        for table_name, proposal in proposals.items():
            table_id = f"{GOOGLE_CLOUD_PROJECT}.{BQ_BRONZE_DATASET}.{table_name}"

            try:
                table = client.get_table(table_id)

                # Update table description
                table.description = proposal.get("description", "")

                # Update table labels
                source_id = tool_context.state.get("source_id", "")
                table.labels = {
                    "managed_by": "data_onboarding",
                    "source_id": source_id[:63] if source_id else "",
                }

                # Update column descriptions
                columns = proposal.get("enriched_columns", [])
                if columns:
                    new_schema = []
                    for field in table.schema:
                        col_info = next(
                            (c for c in columns if c["name"] == field.name),
                            None,
                        )
                        if col_info and col_info.get("description"):
                            new_field = field.to_api_repr()
                            new_field["description"] = col_info["description"]
                            new_schema.append(bigquery.SchemaField.from_api_repr(new_field))
                        else:
                            new_schema.append(field)
                    table.schema = new_schema

                client.update_table(table, ["description", "labels", "schema"])
                applied.append(table_name)

            except Exception as e:
                if "Not found" in str(e):
                    errors.append(f"{table_name}: Table does not exist yet (run execute_sql first)")
                else:
                    errors.append(f"{table_name}: {e}")

        result = "BQ metadata application:\n"
        result += f"  Applied: {len(applied)}\n"
        result += f"  Skipped/Errors: {len(errors)}\n"

        if applied:
            result += "\nApplied to:\n"
            for t in applied:
                result += f"  - {t}\n"

        if errors:
            result += "\nSkipped:\n"
            for e in errors:
                result += f"  - {e}\n"

        return result

    except Exception as e:
        return log_tool_error("apply_bq_metadata", e)
