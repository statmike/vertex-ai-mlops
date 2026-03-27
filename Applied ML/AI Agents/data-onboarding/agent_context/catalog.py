"""Module-level catalog data — populated once at startup.

Separated from agent.py to avoid circular imports with the tools package.
"""

import logging

from google.cloud import bigquery

from agent_chat.config import META_DATASET
from agent_orchestrator.config import GOOGLE_CLOUD_PROJECT

logger = logging.getLogger(__name__)

# Module-level catalog data — populated once at startup by _load_catalog()
_catalog_data: dict[str, dict] = {}  # full_ref → full metadata
_catalog_summary: str = ""           # compact text for the agent instruction


def _load_catalog() -> None:
    """Pre-load the dataset catalog and table documentation into structured data.

    Queries ``data_catalog`` and each dataset's ``table_documentation`` once
    at startup.  Produces two outputs stored in module globals:

    * ``_catalog_data`` — structured dict keyed by fully-qualified table ref.
      Each entry has: ``full_ref``, ``dataset``, ``columns`` (list of
      ``{name, bq_type, description}``), ``relationships``, ``description``.
    * ``_catalog_summary`` — compact text for the agent instruction containing
      only table names, column counts, 1-line descriptions, and column name
      lists (no full descriptions, no Dataplex stats).
    """
    global _catalog_data, _catalog_summary

    if not GOOGLE_CLOUD_PROJECT:
        return

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
            return

        summary_parts = []
        for row in catalog_rows:
            dataset_name = row.dataset_name
            summary_parts.append(f"### Dataset: {dataset_name}")
            summary_parts.append(f"  Source: {row.source_uri}")

            # Load table documentation for each dataset
            doc_table = f"{GOOGLE_CLOUD_PROJECT}.{dataset_name}.table_documentation"
            try:
                doc_rows = list(client.query(f"""
                    SELECT table_name, documentation_md, column_details,
                           related_tables, source_file
                    FROM `{doc_table}`
                    ORDER BY table_name
                """).result())

                for doc in doc_rows:
                    columns = doc.column_details or []
                    relationships = doc.related_tables or {}
                    full_ref = f"{GOOGLE_CLOUD_PROJECT}.{dataset_name}.{doc.table_name}"

                    # Extract first line of documentation_md as the description
                    doc_md = doc.documentation_md or ""
                    first_line = doc_md.split("\n")[0].strip().strip("#").strip() if doc_md else ""

                    # Store full metadata in _catalog_data
                    _catalog_data[full_ref] = {
                        "full_ref": full_ref,
                        "dataset": dataset_name,
                        "table_name": doc.table_name,
                        "columns": [
                            {
                                "name": c.get("name", ""),
                                "bq_type": c.get("bq_type", "STRING"),
                                "description": c.get("description", ""),
                            }
                            for c in columns
                        ],
                        "relationships": relationships,
                        "description": first_line,
                    }

                    # Build compact summary line
                    col_names = [c.get("name", "") for c in columns]
                    summary_parts.append(
                        f"\n  **{doc.table_name}** ({len(columns)} columns)"
                    )
                    if first_line:
                        summary_parts.append(f"    {first_line}")
                    summary_parts.append(
                        f"    Columns: {', '.join(col_names)}"
                    )
                    summary_parts.append(f"    Full ref: {full_ref}")

            except Exception as e:
                logger.debug("Could not load table docs for %s: %s", dataset_name, e)

            summary_parts.append("")

        _catalog_summary = "\n".join(summary_parts)

    except Exception as e:
        logger.warning("Failed to pre-load catalog: %s", e)


# Pre-load once at import time — this runs when adk web starts
_load_catalog()
