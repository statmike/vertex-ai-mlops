"""Generate per-table documentation and a dataset catalog in BigQuery.

Creates:
  - ``table_documentation`` in the **bronze** dataset: one row per data table
    with rich markdown docs (table-level docs belong near the data).
  - ``data_catalog`` in the **meta** dataset: one row describing the dataset
    source and contents, so all bronze datasets are discoverable from one place.

Documentation is generated programmatically from enriched column details and
context insights gathered during earlier phases — no LLM calls required.
"""

import datetime
import json
import logging

from google.adk import tools

from agent_acquire.tools.util_common import log_tool_error
from agent_orchestrator.config import (
    BQ_BRONZE_DATASET,
    BQ_DATASET_LOCATION,
    BQ_META_DATASET,
    GOOGLE_CLOUD_PROJECT,
)

logger = logging.getLogger(__name__)

# DDL templates — filled at runtime with the actual dataset reference.

TABLE_DOCUMENTATION_DDL = """
CREATE TABLE IF NOT EXISTS `{dataset_ref}.table_documentation`
(
  table_name STRING NOT NULL OPTIONS(description="Name of the documented BQ table."),
  documentation_md STRING NOT NULL OPTIONS(description="Rich markdown documentation — data dictionary, business rules, relationships."),
  source_documents JSON OPTIONS(description="Array of context doc URLs/paths that informed this table's design."),
  source_file STRING OPTIONS(description="GCS path of the data file this table was built from."),
  column_details JSON OPTIONS(description="Per-column deep context beyond the 1024-char BQ description limit."),
  related_tables JSON OPTIONS(description="Inter-table relationships: contains, contained_by, snapshot_of, has_snapshot, shared_keys."),
  created_at TIMESTAMP NOT NULL OPTIONS(description="When the documentation was generated.")
)
CLUSTER BY table_name;
"""

DATA_CATALOG_DDL = """
CREATE TABLE IF NOT EXISTS `{dataset_ref}.data_catalog`
(
  dataset_name STRING NOT NULL OPTIONS(description="Name of the bronze dataset."),
  source_uri STRING NOT NULL OPTIONS(description="Original URL or GCS path that was onboarded."),
  domain STRING OPTIONS(description="Domain slug extracted from URL (e.g. cms_gov)."),
  source_id STRING OPTIONS(description="Deterministic UUID for this source."),
  tables_created JSON OPTIONS(description="Array of table names created in this dataset."),
  context_documents JSON OPTIONS(description="Array of context doc URLs/paths used."),
  table_relationships JSON OPTIONS(description="Relationship graph for all tables in this dataset: containment, snapshots, shared keys."),
  description_md STRING OPTIONS(description="Markdown overview of the source and what was onboarded."),
  onboarded_at TIMESTAMP NOT NULL OPTIONS(description="When this source was onboarded.")
)
CLUSTER BY dataset_name;
"""


def _build_table_doc(
    table_name: str,
    table_description: str,
    columns: list[dict],
    source_file: str,
    source_uri: str,
    context_summary: str,
    related_tables: dict | None = None,
    column_recovery: dict | None = None,
) -> str:
    """Build a markdown documentation string for a single table."""
    lines = [
        f"# {table_name}",
        "",
        "## Overview",
        "",
        table_description or f"Data table `{table_name}`.",
        "",
        "## Source",
        "",
    ]

    if source_uri:
        lines.append(f"- **Original URL**: {source_uri}")
    if source_file:
        lines.append(f"- **Source file(s)**: {source_file}")
    lines.append("")

    # Column dictionary — include Source column if any column has attribution
    has_attribution = any(col.get("attributed_to") for col in columns)
    lines.append("## Column Dictionary")
    lines.append("")
    if has_attribution:
        lines.append("| Name | Type | Description | Source |")
        lines.append("|------|------|-------------|--------|")
    else:
        lines.append("| Name | Type | Description | Notes |")
        lines.append("|------|------|-------------|-------|")
    for col in columns:
        name = col.get("name", "")
        bq_type = col.get("bq_type", col.get("dtype", "STRING"))
        desc = (col.get("description") or "").replace("|", "\\|")
        if has_attribution:
            attr = col.get("attributed_to", [])
            source = ", ".join(attr) if attr else ""
            source = source.replace("|", "\\|")
            lines.append(f"| {name} | {bq_type} | {desc} | {source} |")
        else:
            notes = (col.get("notes") or "").replace("|", "\\|")
            lines.append(f"| {name} | {bq_type} | {desc} | {notes} |")
    lines.append("")

    # Schema Provenance — list unique source documents from column attribution
    if has_attribution:
        all_sources = set()
        for col in columns:
            for attr in col.get("attributed_to", []):
                all_sources.add(attr)
        if all_sources:
            lines.append("## Schema Provenance")
            lines.append("")
            lines.append("Column names and types were informed by the following source documents:")
            lines.append("")
            for src in sorted(all_sources):
                lines.append(f"- {src}")
            lines.append("")

    # Related tables
    if related_tables:
        lines.append("## Related Tables")
        lines.append("")
        for rel_type, rel_val in related_tables.items():
            if isinstance(rel_val, list):
                lines.append(f"- **{rel_type}**: {', '.join(rel_val)}")
            else:
                lines.append(f"- **{rel_type}**: {rel_val}")
        lines.append("")

    # Data quality notes from column recovery
    if column_recovery:
        coerced = column_recovery.get("coerced_to_string", [])
        omitted = column_recovery.get("omitted", [])
        if coerced or omitted:
            lines.append("## Data Quality Notes")
            lines.append("")
            if coerced:
                lines.append("**Columns coerced to STRING** (mixed types in source data):")
                lines.append("")
                for c in coerced:
                    lines.append(f"- `{c}`")
                lines.append("")
            if omitted:
                lines.append("**Columns omitted** (could not be serialized from source):")
                lines.append("")
                for c in omitted:
                    lines.append(f"- `{c}`")
                lines.append("")

    # Context
    if context_summary:
        lines.append("## Context from Source Documentation")
        lines.append("")
        lines.append(context_summary)
        lines.append("")

    return "\n".join(lines)


def _build_catalog_doc(
    source_uri: str,
    domain_slug: str,
    table_summaries: list[str],
    context_docs: list[str],
) -> str:
    """Build a markdown catalog entry for the dataset."""
    lines = [
        f"# Dataset: {domain_slug or 'unknown'}",
        "",
        f"Data onboarded from {source_uri or '(unknown source)'}.",
        "",
        "## Tables",
        "",
    ]
    for s in table_summaries:
        lines.append(s)
    lines.append("")

    if context_docs:
        lines.append("## Context Documents")
        lines.append("")
        for doc in context_docs[:10]:
            lines.append(f"- {doc}")
        lines.append("")

    return "\n".join(lines)


async def generate_documentation(
    tool_context: tools.ToolContext,
) -> str:
    """Generate table documentation and dataset catalog in the bronze dataset.

    Reads proposals, context insights, and enriched columns from state,
    generates structured markdown documentation for each table
    programmatically, and writes ``table_documentation`` and
    ``data_catalog`` tables.

    Args:
        tool_context: The ADK tool context for accessing shared state.

    Returns:
        Summary of generated documentation, or an error message.
    """
    try:
        proposals = tool_context.state.get("proposed_tables", {})
        if not proposals:
            return "No proposed tables to document."

        if not GOOGLE_CLOUD_PROJECT:
            return "Cannot generate documentation: GOOGLE_CLOUD_PROJECT not set."

        bronze_dataset = tool_context.state.get("bq_bronze_dataset", BQ_BRONZE_DATASET)
        source_uri = tool_context.state.get("source_uri", "")
        source_id = tool_context.state.get("source_id", "")
        domain_slug = tool_context.state.get("domain_slug", "")
        context_insights = tool_context.state.get("context_insights", {})

        from google.cloud import bigquery

        client = bigquery.Client(project=GOOGLE_CLOUD_PROJECT)

        # Ensure bronze dataset exists (for table_documentation)
        dataset_ref = f"{GOOGLE_CLOUD_PROJECT}.{bronze_dataset}"
        ds = bigquery.Dataset(dataset_ref)
        ds.location = BQ_DATASET_LOCATION
        client.create_dataset(ds, exists_ok=True)

        # Ensure meta dataset exists (for data_catalog)
        meta_dataset_ref = f"{GOOGLE_CLOUD_PROJECT}.{BQ_META_DATASET}"
        meta_ds = bigquery.Dataset(meta_dataset_ref)
        meta_ds.location = BQ_DATASET_LOCATION
        client.create_dataset(meta_ds, exists_ok=True)

        # Create table_documentation in bronze, data_catalog in meta
        client.query(TABLE_DOCUMENTATION_DDL.format(dataset_ref=dataset_ref)).result()
        client.query(DATA_CATALOG_DDL.format(dataset_ref=meta_dataset_ref)).result()

        # Build context summary from insights
        file_insights = {}
        if isinstance(context_insights, dict):
            file_insights = context_insights.get("files", {})

        # Collect context document paths — classification lives in files_classified
        files_classified = tool_context.state.get("files_classified", [])
        context_docs = [
            f.get("url", f.get("gcs_path", ""))
            for f in files_classified
            if f.get("classification") == "context"
        ]

        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        doc_rows = []
        table_summaries = []

        for table_name, proposal in proposals.items():
            columns = proposal.get("enriched_columns", proposal.get("columns", []))
            source_file = proposal.get("source_file", "")
            table_description = proposal.get("description", "")

            # Build column details for storage
            column_details = []
            for col in columns:
                name = col.get("name", "")
                bq_type = col.get("bq_type", col.get("dtype", "STRING"))
                desc = col.get("description", "")
                column_details.append({
                    "name": name,
                    "bq_type": bq_type,
                    "description": desc,
                    "source_name": col.get("source_name", name),
                    "category": col.get("category", ""),
                    "attributed_to": col.get("attributed_to", []),
                })

            # Build context summary for this table's source file
            context_summary = ""
            if file_insights:
                for fname, info in file_insights.items():
                    if isinstance(info, dict):
                        context_summary += f"\n### {fname}\n{info.get('description', '')}\n"

            # For grouped tables, join all source paths; fall back to single path
            source_paths = proposal.get("source_paths", [])
            if not source_paths:
                sp = proposal.get("source_path", source_file)
                source_paths = [sp] if sp else [source_file]
            source_file_value = ", ".join(source_paths) if source_paths else source_file

            # Get related tables from proposal
            related_tables = proposal.get("related_tables", {})

            # Generate documentation programmatically (no LLM call)
            documentation_md = _build_table_doc(
                table_name=table_name,
                table_description=table_description,
                columns=columns,
                source_file=source_file_value,
                source_uri=source_uri,
                context_summary=context_summary,
                related_tables=related_tables if related_tables else None,
                column_recovery=proposal.get("column_recovery"),
            )

            # Aggregate attributed_to from columns to get per-table context docs
            table_context_docs = set()
            for col in columns:
                for attr in col.get("attributed_to", []):
                    table_context_docs.add(attr)
            # Fall back to all context docs if no column-level attribution
            source_docs = sorted(table_context_docs) if table_context_docs else context_docs

            doc_rows.append({
                "table_name": table_name,
                "documentation_md": documentation_md,
                "source_documents": json.dumps(source_docs),
                "source_file": source_file_value,
                "column_details": json.dumps(column_details),
                "related_tables": json.dumps(related_tables) if related_tables else None,
                "created_at": now,
            })

            table_summaries.append(
                f"- **{table_name}**: {table_description} "
                f"({len(columns)} columns, {proposal.get('row_count', 'unknown')} rows)"
            )

        # Insert table_documentation rows
        doc_table_id = f"{dataset_ref}.table_documentation"
        if doc_rows:
            errors = client.insert_rows_json(doc_table_id, doc_rows)
            if errors:
                logger.warning(f"table_documentation insert errors: {errors}")

        # Generate catalog entry programmatically (no LLM call)
        table_names = list(proposals.keys())
        catalog_md = _build_catalog_doc(
            source_uri=source_uri,
            domain_slug=domain_slug,
            table_summaries=table_summaries,
            context_docs=context_docs,
        )

        # Build table_relationships summary for the entire dataset
        all_relationships = {}
        for tname, prop in proposals.items():
            rels = prop.get("related_tables", {})
            if rels:
                all_relationships[tname] = rels

        catalog_row = {
            "dataset_name": bronze_dataset,
            "source_uri": source_uri,
            "domain": domain_slug,
            "source_id": source_id,
            "tables_created": json.dumps(table_names),
            "context_documents": json.dumps(context_docs),
            "table_relationships": json.dumps(all_relationships) if all_relationships else None,
            "description_md": catalog_md,
            "onboarded_at": now,
        }

        catalog_table_id = f"{meta_dataset_ref}.data_catalog"
        errors = client.insert_rows_json(catalog_table_id, [catalog_row])
        if errors:
            logger.warning(f"data_catalog insert errors: {errors}")

        return (
            f"Documentation generated for {len(doc_rows)} table(s).\n"
            f"  table_documentation: {doc_table_id}\n"
            f"  data_catalog: {catalog_table_id}\n"
            f"\nTables documented:\n"
            + "\n".join(f"  - {r['table_name']}" for r in doc_rows)
        )

    except Exception as e:
        return log_tool_error("generate_documentation", e)
