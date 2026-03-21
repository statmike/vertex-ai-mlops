"""Read table_documentation from a bronze dataset to find tables matching a user question."""

import logging

from google.adk import tools

from agent_orchestrator.config import GOOGLE_CLOUD_PROJECT

logger = logging.getLogger(__name__)


async def find_tables(
    dataset_name: str,
    tool_context: tools.ToolContext,
) -> str:
    """Get detailed table documentation from a bronze dataset.

    Queries ``table_documentation`` in the specified dataset to retrieve
    table descriptions, column details, related tables, and shared join keys.

    Args:
        dataset_name: The bronze dataset name to query (e.g., ``data_onboarding_cms_gov_bronze``).
        tool_context: The ADK tool context.

    Returns:
        Structured information about all tables in the dataset.
    """
    try:
        if not GOOGLE_CLOUD_PROJECT:
            return "Cannot find tables: GOOGLE_CLOUD_PROJECT not set."

        from google.cloud import bigquery

        client = bigquery.Client(project=GOOGLE_CLOUD_PROJECT)

        doc_table = f"{GOOGLE_CLOUD_PROJECT}.{dataset_name}.table_documentation"

        query = f"""
        SELECT
            table_name,
            documentation_md,
            column_details,
            related_tables,
            source_file
        FROM `{doc_table}`
        ORDER BY table_name
        """

        rows = list(client.query(query).result())

        if not rows:
            return f"No table documentation found in dataset '{dataset_name}'."

        result = f"Found {len(rows)} table(s) in `{dataset_name}`:\n\n"
        tables_info = []

        for row in rows:
            # BQ JSON columns are returned as already-parsed Python objects
            columns = row.column_details if row.column_details else []
            relationships = row.related_tables if row.related_tables else {}

            result += f"### {row.table_name}\n"

            # Show column summary
            col_names = [c.get("name", "") for c in columns]
            result += f"  Columns ({len(columns)}): {', '.join(col_names[:10])}"
            if len(col_names) > 10:
                result += f" ... (+{len(col_names) - 10} more)"
            result += "\n"

            # Show column types and descriptions for key columns
            for col in columns[:5]:
                desc = col.get("description", "")
                if desc:
                    result += f"    - {col['name']} ({col.get('bq_type', 'STRING')}): {desc[:100]}\n"

            # Show relationships
            if relationships:
                result += "  Relationships:\n"
                for rel_type, rel_val in relationships.items():
                    result += f"    {rel_type}: {rel_val}\n"

            result += f"  Source: {row.source_file or 'unknown'}\n\n"

            tables_info.append({
                "table_name": row.table_name,
                "full_table_id": f"{GOOGLE_CLOUD_PROJECT}.{dataset_name}.{row.table_name}",
                "columns": columns,
                "related_tables": relationships,
            })

        # Store in state for the convo agent
        tool_context.state["recommended_tables"] = tables_info

        return result

    except Exception as e:
        return f"Error finding tables in '{dataset_name}': {e}"
