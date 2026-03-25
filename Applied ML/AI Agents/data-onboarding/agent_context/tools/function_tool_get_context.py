"""Merged context tool — returns table_documentation + lookupContext for a dataset."""

import logging

from google.adk import tools

from agent_orchestrator.config import BQ_DATASET_LOCATION, GOOGLE_CLOUD_PROJECT

from .util_lookup_context import build_entry_name, lookup_context_batched

logger = logging.getLogger(__name__)


async def get_table_context(
    dataset_name: str,
    tool_context: tools.ToolContext,
) -> str:
    """Get merged table metadata for a dataset.

    Combines ``table_documentation`` from BigQuery with Dataplex
    ``lookupContext`` profile statistics to produce the richest possible
    context for the reranker.

    Args:
        dataset_name: The bronze dataset name (e.g., ``data_onboarding_cms_gov_bronze``).
        tool_context: The ADK tool context.

    Returns:
        Merged metadata text block with table schemas, descriptions,
        and profile statistics.
    """
    try:
        if not GOOGLE_CLOUD_PROJECT:
            return "Cannot get context: GOOGLE_CLOUD_PROJECT not set."

        from google.cloud import bigquery

        client = bigquery.Client(project=GOOGLE_CLOUD_PROJECT)

        # 1. Load table_documentation
        doc_table = f"{GOOGLE_CLOUD_PROJECT}.{dataset_name}.table_documentation"
        try:
            doc_rows = list(client.query(f"""
                SELECT table_name, documentation_md, column_details,
                       related_tables, source_file
                FROM `{doc_table}`
                ORDER BY table_name
            """).result())
        except Exception as e:
            logger.warning("Could not load table_documentation for %s: %s", dataset_name, e)
            doc_rows = []

        if not doc_rows:
            return f"No table documentation found in dataset '{dataset_name}'."

        # 2. Build Dataplex entry names for lookupContext
        entry_names = [
            build_entry_name(GOOGLE_CLOUD_PROJECT, BQ_DATASET_LOCATION, dataset_name, row.table_name)
            for row in doc_rows
        ]

        # 3. Call lookupContext (graceful fallback)
        dataplex_context = ""
        try:
            dataplex_context = lookup_context_batched(entry_names)
        except Exception as e:
            logger.warning("lookupContext failed for %s: %s", dataset_name, e)

        # 4. Build merged context
        parts = [f"## Dataset: {dataset_name}\n"]

        for row in doc_rows:
            columns = row.column_details if row.column_details else []
            relationships = row.related_tables if row.related_tables else {}
            full_ref = f"{GOOGLE_CLOUD_PROJECT}.{dataset_name}.{row.table_name}"

            parts.append(f"### Table: {row.table_name}")
            parts.append(f"  Full reference: `{full_ref}`")

            # Column details
            if columns:
                parts.append(f"  Columns ({len(columns)}):")
                for col in columns:
                    desc = col.get("description", "")
                    bq_type = col.get("bq_type", "STRING")
                    parts.append(f"    - {col.get('name', '?')} ({bq_type}): {desc[:150]}")

            # Relationships
            if relationships:
                parts.append("  Relationships:")
                for rel_type, rel_val in relationships.items():
                    parts.append(f"    {rel_type}: {rel_val}")

            parts.append("")

        # Append Dataplex context if available
        if dataplex_context:
            parts.append("## Dataplex Profile Statistics\n")
            parts.append(dataplex_context)

        merged = "\n".join(parts)

        # Store in state for other tools
        tool_context.state["merged_context"] = merged

        return merged

    except Exception as e:
        return f"Error getting table context for '{dataset_name}': {e}"
