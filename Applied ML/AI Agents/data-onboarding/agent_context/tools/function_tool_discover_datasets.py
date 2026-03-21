"""Query the shared data_catalog in the meta dataset to list all onboarded datasets."""

import logging

from google.adk import tools

from agent_chat.config import META_DATASET
from agent_orchestrator.config import GOOGLE_CLOUD_PROJECT

logger = logging.getLogger(__name__)


async def discover_datasets(
    tool_context: tools.ToolContext,
) -> str:
    """List all onboarded bronze datasets by querying the data_catalog in the meta dataset.

    Returns a summary of available datasets including their names, source URLs,
    tables created, descriptions, and table relationships.

    Args:
        tool_context: The ADK tool context.

    Returns:
        A formatted summary of all onboarded datasets, or an error message.
    """
    try:
        if not GOOGLE_CLOUD_PROJECT:
            return "Cannot discover datasets: GOOGLE_CLOUD_PROJECT not set."

        from google.cloud import bigquery

        client = bigquery.Client(project=GOOGLE_CLOUD_PROJECT)

        catalog_table = f"{GOOGLE_CLOUD_PROJECT}.{META_DATASET}.data_catalog"

        query = f"""
        SELECT
            dataset_name,
            source_uri,
            domain,
            tables_created,
            table_relationships,
            description_md,
            onboarded_at
        FROM `{catalog_table}`
        ORDER BY onboarded_at DESC
        """

        rows = list(client.query(query).result())

        if not rows:
            return "No onboarded datasets found in the data catalog."

        result = f"Found {len(rows)} onboarded dataset(s):\n\n"
        for row in rows:
            # BQ JSON columns are returned as already-parsed Python objects
            tables = row.tables_created if row.tables_created else []
            relationships = row.table_relationships if row.table_relationships else {}

            result += f"### {row.dataset_name}\n"
            result += f"  Source: {row.source_uri}\n"
            result += f"  Domain: {row.domain or 'unknown'}\n"
            result += f"  Tables: {', '.join(tables)}\n"
            result += f"  Onboarded: {row.onboarded_at}\n"

            if relationships:
                result += "  Relationships:\n"
                for tname, rels in relationships.items():
                    for rel_type, rel_val in rels.items():
                        result += f"    {tname}.{rel_type} = {rel_val}\n"

            result += "\n"

        # Store in state for other tools
        tool_context.state["discovered_datasets"] = [
            {
                "dataset_name": row.dataset_name,
                "source_uri": row.source_uri,
                "domain": row.domain,
                "tables": row.tables_created if row.tables_created else [],
                "relationships": row.table_relationships if row.table_relationships else {},
            }
            for row in rows
        ]

        return result

    except Exception as e:
        return f"Error discovering datasets: {e}"
