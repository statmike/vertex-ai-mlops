"""List all onboarded tables with their descriptions and column counts.

Uses the context cache for an instant response. Useful for broad questions
like "What reference tables exist?" or "Give me an overview of all tables."
"""

import logging

from google.adk import tools

from agent_orchestrator.config import GOOGLE_CLOUD_PROJECT

logger = logging.getLogger(__name__)


async def list_all_tables(
    tool_context: tools.ToolContext = None,
) -> str:
    """List all onboarded tables with their names, descriptions, and column counts.

    Returns a complete inventory of every table in the system. Use this when
    the user asks broad questions about what tables exist, what kinds of
    tables are available, or wants an overview of the full dataset.

    Returns:
        Formatted table listing with names, descriptions, and column counts.
    """
    if not GOOGLE_CLOUD_PROJECT:
        return "Cannot query: GOOGLE_CLOUD_PROJECT not set."

    try:
        from agent_context.context_cache.cache import _CACHE

        if not _CACHE:
            return _fallback_from_bq()

        parts = [f"**{len(_CACHE)} table(s) onboarded:**\n"]
        for tc in _CACHE.values():
            short_name = tc.full_id.split(".")[-1]
            dataset = tc.full_id.split(".")[1] if "." in tc.full_id else ""
            col_count = len(tc.columns)
            desc = tc.description or "(no description)"

            parts.append(f"- **{short_name}** (`{tc.full_id}`)")
            parts.append(f"  Dataset: {dataset} | {col_count} columns")
            parts.append(f"  {desc}")

            # Include column names for role-inference
            if tc.columns:
                col_names = [c.get("name", "") for c in tc.columns]
                parts.append(f"  Columns: {', '.join(col_names)}")
            parts.append("")

        return "\n".join(parts)

    except ImportError:
        return _fallback_from_bq()


def _fallback_from_bq() -> str:
    """Fallback: query data_catalog directly."""
    try:
        from google.cloud import bigquery

        from agent_orchestrator.config import BQ_META_DATASET

        client = bigquery.Client(project=GOOGLE_CLOUD_PROJECT)
        sql = f"""
            SELECT dataset_name, source_uri, tables_created
            FROM `{GOOGLE_CLOUD_PROJECT}.{BQ_META_DATASET}.data_catalog`
            ORDER BY onboarded_at DESC
        """
        rows = list(client.query(sql).result())
        if not rows:
            return "No onboarded datasets found."

        parts = [f"**{len(rows)} dataset(s) onboarded:**\n"]
        for row in rows:
            parts.append(f"- **{row.dataset_name}**: {row.tables_created} tables")
            parts.append(f"  Source: {row.source_uri}")
        return "\n".join(parts)

    except Exception as e:
        return f"Error listing tables: {e}"
