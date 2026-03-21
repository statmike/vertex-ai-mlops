import logging

from google.adk import agents
from google.cloud import bigquery

from agent_orchestrator.config import AGENT_MODEL_INSTANCE as AGENT_MODEL, GOOGLE_CLOUD_PROJECT
from agent_chat.config import META_DATASET

from . import prompts, tools

logger = logging.getLogger(__name__)


def _load_catalog() -> str:
    """Pre-load the dataset catalog and table documentation at agent start.

    Returns a text block with all datasets, tables, columns, and relationships
    so the LLM has full context without needing to call discovery tools.
    """
    if not GOOGLE_CLOUD_PROJECT:
        return ""

    try:
        client = bigquery.Client(project=GOOGLE_CLOUD_PROJECT)
        catalog_table = f"{GOOGLE_CLOUD_PROJECT}.{META_DATASET}.data_catalog"

        catalog_rows = list(client.query(f"""
            SELECT dataset_name, source_uri, domain, tables_created,
                   table_relationships
            FROM `{catalog_table}`
            ORDER BY onboarded_at DESC
        """).result())

        if not catalog_rows:
            return ""

        parts = []
        for row in catalog_rows:
            tables = row.tables_created or []
            parts.append(f"### Dataset: {row.dataset_name}")
            parts.append(f"  Source: {row.source_uri}")
            parts.append(f"  Tables: {', '.join(tables)}")

            # Load table documentation for each dataset
            doc_table = f"{GOOGLE_CLOUD_PROJECT}.{row.dataset_name}.table_documentation"
            try:
                doc_rows = list(client.query(f"""
                    SELECT table_name, column_details, related_tables, source_file
                    FROM `{doc_table}`
                    ORDER BY table_name
                """).result())

                for doc in doc_rows:
                    columns = doc.column_details or []
                    col_names = [c.get("name", "") for c in columns]
                    parts.append(f"\n  **{doc.table_name}** ({len(columns)} columns)")
                    parts.append(f"    Columns: {', '.join(col_names[:15])}")
                    if len(col_names) > 15:
                        parts.append(f"    ... (+{len(col_names) - 15} more)")
                    for col in columns[:5]:
                        desc = col.get("description", "")
                        if desc:
                            parts.append(
                                f"    - {col['name']} ({col.get('bq_type', 'STRING')}): "
                                f"{desc[:100]}"
                            )
                    rels = doc.related_tables or {}
                    if rels:
                        parts.append(f"    Related: {rels}")
                    parts.append(
                        f"    Full ref: {GOOGLE_CLOUD_PROJECT}.{row.dataset_name}.{doc.table_name}"
                    )
            except Exception as e:
                logger.debug("Could not load table docs for %s: %s", row.dataset_name, e)

            parts.append("")

        return "\n".join(parts)

    except Exception as e:
        logger.warning("Failed to pre-load catalog: %s", e)
        return ""


# Pre-load once at import time — this runs when adk web starts
_catalog_context = _load_catalog()


def _build_instruction():
    """Build the agent instruction with pre-loaded catalog data."""
    base = prompts.agent_instructions
    if _catalog_context:
        return (
            f"{base}\n\n"
            f"## Pre-loaded Data Catalog\n\n"
            f"The following datasets and tables are available. Use these exact "
            f"`project.dataset.table` references when transferring to agent_convo.\n\n"
            f"{_catalog_context}"
        )
    return base


root_agent = agents.Agent(
    name="agent_context",
    model=AGENT_MODEL,
    description="Discovers relevant BigQuery datasets and tables for a user's question by querying metadata catalogs and table documentation.",
    global_instruction=prompts.global_instructions,
    instruction=_build_instruction(),
    tools=tools.TOOLS,
    disallow_transfer_to_peers=False,
)
