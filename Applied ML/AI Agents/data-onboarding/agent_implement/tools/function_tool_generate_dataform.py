import logging
import os

from google.adk import tools

from agent_acquire.tools.util_common import log_tool_error
from agent_orchestrator.config import (
    BQ_BRONZE_DATASET,
    DATAFORM_OUTPUT_DIR,
    GOOGLE_CLOUD_PROJECT,
)

from .util_dataform import create_dataform_project, generate_sqlx

logger = logging.getLogger(__name__)


async def generate_dataform(
    tool_context: tools.ToolContext,
) -> str:
    """
    Generate Dataform SQLX files for all approved table designs.

    Creates the Dataform project structure and generates a SQLX file
    for each table in proposed_tables.

    Args:
        tool_context: The ADK tool context for accessing shared state.

    Returns:
        Summary of generated files, or an error message.
    """
    try:
        proposals = tool_context.state.get("proposed_tables", {})
        approved = tool_context.state.get("design_approved", False)

        if not proposals:
            return "No proposed tables. Run the design phase first."

        if not approved:
            return "Design has not been approved. Get human approval first."

        # Create project structure
        output_dir = os.path.abspath(DATAFORM_OUTPUT_DIR)
        config_path = create_dataform_project(output_dir, GOOGLE_CLOUD_PROJECT, BQ_BRONZE_DATASET)

        generated_files = [config_path]

        for table_name, proposal in proposals.items():
            columns = proposal.get("enriched_columns", proposal.get("columns", []))
            source_path = proposal.get("source_path", "")

            sqlx_content = generate_sqlx(
                table_name=table_name,
                columns=columns,
                source_uri=source_path,
                description=proposal.get("description", ""),
                partition_by=proposal.get("partition_by"),
                cluster_by=proposal.get("cluster_by"),
            )

            sqlx_path = os.path.join(output_dir, "definitions", f"{table_name}.sqlx")
            with open(sqlx_path, "w") as f:
                f.write(sqlx_content)

            generated_files.append(sqlx_path)

        tool_context.state["dataform_project_path"] = output_dir
        tool_context.state["generated_files"] = generated_files

        result = (
            f"Dataform project generated.\n"
            f"  Output directory: {output_dir}\n"
            f"  Files created: {len(generated_files)}\n\n"
        )
        for f in generated_files:
            result += f"  - {os.path.relpath(f, output_dir)}\n"

        return result

    except Exception as e:
        return log_tool_error("generate_dataform", e)
