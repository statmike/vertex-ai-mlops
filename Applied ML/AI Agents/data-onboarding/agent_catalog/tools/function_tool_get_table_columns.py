"""Direct column listing for a specific table.

Checks the shared context cache first (instant). Falls back to a BQ
query against ``table_documentation`` if the table isn't cached.
"""

import logging

from google.adk import tools

from agent_orchestrator.config import CHAT_SCOPE, GOOGLE_CLOUD_PROJECT

logger = logging.getLogger(__name__)


async def get_table_columns(
    table_name: str,
    tool_context: tools.ToolContext = None,
) -> str:
    """List all columns and their descriptions for a specific table.

    Checks the shared context cache first for an instant response. Falls
    back to a BQ query against ``table_documentation`` if the table isn't
    cached.

    Args:
        table_name: Table name (e.g., ``underlying_eod``).  Can be a short
            name or fully qualified ``project.dataset.table``.
        tool_context: The ADK tool context (unused but required by ADK).

    Returns:
        Formatted column listing, or an error message.
    """
    if not GOOGLE_CLOUD_PROJECT:
        return "Cannot query: GOOGLE_CLOUD_PROJECT not set."

    # Try the context cache first (instant, no BQ calls)
    try:
        from agent_context.context_cache import get_table_columns_from_cache

        cached = get_table_columns_from_cache(table_name)
        if cached:
            return _format_columns(
                table_name=cached["full_id"].split(".")[-1],
                full_ref=cached["full_id"],
                description=cached["description"],
                columns=cached["columns"],
            )
    except ImportError:
        pass  # context cache not available, fall through to BQ

    # Fallback: query table_documentation directly
    return await _query_table_documentation(table_name)


def _format_columns(
    table_name: str,
    full_ref: str,
    description: str,
    columns: list[dict],
) -> str:
    """Format column info as readable markdown."""
    parts = [f"**{table_name}** ({full_ref})"]
    if description:
        parts.append(f"_{description}_")
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


async def _query_table_documentation(table_name: str) -> str:
    """Fallback: query BQ table_documentation tables directly."""
    try:
        from google.cloud import bigquery

        from agent_orchestrator.config import BQ_META_DATASET, get_scope_datasets

        client = bigquery.Client(project=GOOGLE_CLOUD_PROJECT)
        short_name = table_name.split(".")[-1] if "." in table_name else table_name

        # Use scoped datasets when CHAT_SCOPE is set, otherwise discover all
        if CHAT_SCOPE:
            datasets = get_scope_datasets()
        else:
            catalog_sql = f"""
                SELECT dataset_name
                FROM `{GOOGLE_CLOUD_PROJECT}.{BQ_META_DATASET}.data_catalog`
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
                    doc_md = row.documentation_md or ""
                    first_line = (
                        doc_md.split("\n")[0].strip().strip("#").strip()
                        if doc_md
                        else ""
                    )
                    return _format_columns(
                        table_name=row.table_name,
                        full_ref=full_ref,
                        description=first_line,
                        columns=[
                            {
                                "name": c.get("name", ""),
                                "bq_type": c.get("bq_type", "STRING"),
                                "description": c.get("description", ""),
                            }
                            for c in columns
                        ],
                    )

            except Exception:
                continue

        return (
            f"Table '{short_name}' not found in any onboarded dataset. "
            f"Check the table name and try again."
        )

    except Exception as e:
        return f"Error looking up table columns: {e}"
