"""Direct column listing for a specific table using table_documentation."""

import logging

from google.adk import tools

from agent_orchestrator.config import GOOGLE_CLOUD_PROJECT

logger = logging.getLogger(__name__)


async def get_table_columns(
    table_name: str,
    tool_context: tools.ToolContext = None,
) -> str:
    """List all columns and their descriptions for a specific table.

    Queries the ``table_documentation`` table directly to return complete
    column information.  Use this when the user asks to describe a specific
    table's columns — it returns ALL columns, unlike semantic search which
    only returns a few matches.

    Args:
        table_name: Table name (e.g., ``underlying_eod``).  Can be a short
            name or fully qualified ``project.dataset.table``.
        tool_context: The ADK tool context (unused but required by ADK).

    Returns:
        Formatted column listing, or an error message.
    """
    if not GOOGLE_CLOUD_PROJECT:
        return "Cannot query: GOOGLE_CLOUD_PROJECT not set."

    try:
        from google.cloud import bigquery

        client = bigquery.Client(project=GOOGLE_CLOUD_PROJECT)

        # Extract just the short table name if fully qualified
        short_name = table_name.split(".")[-1] if "." in table_name else table_name

        # Search across all bronze datasets' table_documentation
        sql = f"""
            SELECT
                t.table_catalog || '.' || t.table_schema || '.' || td.table_name AS full_ref,
                td.table_name,
                t.table_schema AS dataset_name,
                td.documentation_md,
                td.column_details
            FROM
                `{GOOGLE_CLOUD_PROJECT}`.`region-US`.INFORMATION_SCHEMA.TABLES t
            JOIN UNNEST([t.table_schema]) AS ds
            JOIN `{GOOGLE_CLOUD_PROJECT}`.`{{ds}}`.table_documentation td
                ON TRUE
            WHERE
                t.table_name = 'table_documentation'
                AND LOWER(td.table_name) = LOWER(@table_name)
            LIMIT 1
        """

        # Simpler approach: query the data_catalog to find datasets, then
        # query table_documentation in each
        from agent_chat.config import META_DATASET

        catalog_sql = f"""
            SELECT dataset_name
            FROM `{GOOGLE_CLOUD_PROJECT}.{META_DATASET}.data_catalog`
        """
        datasets = [
            row.dataset_name
            for row in client.query(catalog_sql).result()
        ]

        for dataset_name in datasets:
            doc_table = f"{GOOGLE_CLOUD_PROJECT}.{dataset_name}.table_documentation"
            try:
                doc_sql = f"""
                    SELECT table_name, documentation_md, column_details
                    FROM `{doc_table}`
                    WHERE LOWER(table_name) = LOWER(@table_name)
                    LIMIT 1
                """
                job_config = bigquery.QueryJobConfig(
                    query_parameters=[
                        bigquery.ScalarQueryParameter(
                            "table_name", "STRING", short_name
                        ),
                    ]
                )
                rows = list(client.query(doc_sql, job_config=job_config).result())

                if rows:
                    row = rows[0]
                    columns = row.column_details or []
                    full_ref = f"{GOOGLE_CLOUD_PROJECT}.{dataset_name}.{row.table_name}"

                    # Extract first line of documentation as description
                    doc_md = row.documentation_md or ""
                    first_line = (
                        doc_md.split("\n")[0].strip().strip("#").strip()
                        if doc_md
                        else ""
                    )

                    parts = [
                        f"**{row.table_name}** ({full_ref})",
                    ]
                    if first_line:
                        parts.append(f"_{first_line}_")
                    parts.append(f"\n{len(columns)} columns:\n")

                    for col in columns:
                        name = col.get("name", "")
                        bq_type = col.get("bq_type", "STRING")
                        desc = col.get("description", "")
                        if desc:
                            parts.append(f"- **{name}** ({bq_type}): {desc}")
                        else:
                            parts.append(f"- **{name}** ({bq_type})")

                    return "\n".join(parts)

            except Exception:
                continue

        return (
            f"Table '{short_name}' not found in any onboarded dataset. "
            f"Check the table name and try again."
        )

    except Exception as e:
        return f"Error looking up table columns: {e}"
