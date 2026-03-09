import logging

from google.adk import tools

from agent_acquire.tools.util_common import log_tool_error
from agent_orchestrator.config import BQ_BRONZE_DATASET, GOOGLE_CLOUD_PROJECT

from .util_bq_types import sanitize_column_name

logger = logging.getLogger(__name__)


async def propose_tables(
    tool_context: tools.ToolContext,
) -> str:
    """
    Propose BigQuery table structures based on analyzed schemas and context insights.

    Reads schemas and context insights from state, then proposes table names,
    descriptions, and overall structure for each data file.

    Args:
        tool_context: The ADK tool context for accessing shared state.

    Returns:
        A summary of proposed tables, or an error message.
    """
    try:
        schemas = tool_context.state.get("schemas_analyzed", {})
        insights = tool_context.state.get("context_insights", {})

        if not schemas:
            return "No schemas to design tables from. Run the understand phase first."

        proposals = {}
        file_insights = insights.get("files", {}) if isinstance(insights, dict) else {}

        for path, schema in schemas.items():
            filename = schema.get("filename", path.split("/")[-1])
            base_name = filename.rsplit(".", 1)[0] if "." in filename else filename
            table_name = sanitize_column_name(base_name)

            # Get insight-based description if available
            file_info = file_insights.get(filename, {})
            table_description = file_info.get("description", f"Data from {filename}")

            full_table_id = f"{GOOGLE_CLOUD_PROJECT}.{BQ_BRONZE_DATASET}.{table_name}"

            proposal = {
                "table_name": table_name,
                "full_table_id": full_table_id,
                "description": table_description,
                "source_file": filename,
                "source_path": path,
                "row_count": schema.get("rows", 0),
                "columns": [],
            }

            # Build column list from schema
            if "columns" in schema:
                for col in schema["columns"]:
                    proposal["columns"].append({
                        "source_name": col["name"],
                        "name": sanitize_column_name(col["name"]),
                        "dtype": col["dtype"],
                    })
            elif "column_analysis" in schema:
                for col_name, info in schema["column_analysis"].items():
                    proposal["columns"].append({
                        "source_name": col_name,
                        "name": sanitize_column_name(col_name),
                        "dtype": info["dtype"],
                        "category": info.get("category", ""),
                    })

            proposals[table_name] = proposal

        tool_context.state["proposed_tables"] = proposals

        # Format summary
        result = f"Proposed {len(proposals)} table(s):\n\n"
        for _name, prop in proposals.items():
            result += (
                f"### {prop['full_table_id']}\n"
                f"  Description: {prop['description']}\n"
                f"  Source: {prop['source_file']}\n"
                f"  Rows: {prop['row_count']}\n"
                f"  Columns: {len(prop['columns'])}\n\n"
            )

        return result

    except Exception as e:
        return log_tool_error("propose_tables", e)
