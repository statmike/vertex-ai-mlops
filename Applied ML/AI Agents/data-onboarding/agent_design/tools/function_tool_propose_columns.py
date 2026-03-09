import logging

from google.adk import tools

from agent_acquire.tools.util_common import log_tool_error

from .util_bq_types import (
    pandas_dtype_to_bq,
    suggest_clustering,
    suggest_partitioning,
)

logger = logging.getLogger(__name__)


async def propose_columns(
    table_name: str,
    tool_context: tools.ToolContext,
) -> str:
    """
    Define detailed column specifications for a proposed table.

    Takes a table name from proposed_tables and enriches each column with
    BigQuery type, description, and nullable flag. Also suggests
    partitioning and clustering.

    Args:
        table_name: The table name from proposed_tables to define columns for.
        tool_context: The ADK tool context for accessing shared state.

    Returns:
        Detailed column specifications, or an error message.
    """
    try:
        proposals = tool_context.state.get("proposed_tables", {})
        insights = tool_context.state.get("context_insights", {})

        if table_name not in proposals:
            available = list(proposals.keys())
            return f"Table '{table_name}' not found. Available: {available}"

        proposal = proposals[table_name]
        file_insights = {}
        if isinstance(insights, dict) and "files" in insights:
            for _fname, finfo in insights["files"].items():
                if "columns" in finfo:
                    file_insights.update(finfo["columns"])

        enriched_columns = []
        for col in proposal["columns"]:
            source_name = col.get("source_name", col["name"])
            dtype = col.get("dtype", "object")
            category = col.get("category", "")

            # Get BQ type
            bq_type = pandas_dtype_to_bq(dtype, category)

            # Get description from context insights
            col_insight = file_insights.get(source_name, {})
            if col_insight.get("suggested_bq_type"):
                bq_type = col_insight["suggested_bq_type"]

            description = col_insight.get("description", "")

            enriched_columns.append({
                "name": col["name"],
                "source_name": source_name,
                "bq_type": bq_type,
                "description": description,
                "mode": "NULLABLE",
                "notes": col_insight.get("notes", ""),
            })

        # Suggest partitioning and clustering
        partition_suggestion = suggest_partitioning(proposal["columns"])
        cluster_suggestion = suggest_clustering(proposal["columns"])

        # Update proposal in state
        proposal["enriched_columns"] = enriched_columns
        proposal["partition_by"] = partition_suggestion
        proposal["cluster_by"] = cluster_suggestion
        proposals[table_name] = proposal
        tool_context.state["proposed_tables"] = proposals

        # Format result
        result = f"Column specifications for {table_name}:\n\n"
        for col in enriched_columns:
            result += (
                f"  {col['name']} {col['bq_type']} ({col['mode']})\n"
                f"    source: {col['source_name']}\n"
            )
            if col["description"]:
                result += f"    description: {col['description']}\n"
            if col["notes"]:
                result += f"    notes: {col['notes']}\n"

        if partition_suggestion:
            result += f"\nPartitioning: BY {partition_suggestion['type']}({partition_suggestion['column']})\n"
        else:
            result += "\nPartitioning: None suggested\n"

        if cluster_suggestion:
            result += f"Clustering: BY {', '.join(cluster_suggestion)}\n"
        else:
            result += "Clustering: None suggested\n"

        return result

    except Exception as e:
        return log_tool_error("propose_columns", e)
