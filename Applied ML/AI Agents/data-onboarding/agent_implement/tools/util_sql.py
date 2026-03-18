"""SQL generation utilities for BigQuery table creation."""

import datetime

# Maps file extension → (BQ external-table format, format-specific options).
GCS_FORMAT_MAP: dict[str, tuple[str, dict]] = {
    "csv": ("CSV", {"skip_leading_rows": 1}),
    "tsv": ("CSV", {"skip_leading_rows": 1, "field_delimiter": "\t"}),
    "json": ("NEWLINE_DELIMITED_JSON", {}),
    "jsonl": ("NEWLINE_DELIMITED_JSON", {}),
    "parquet": ("PARQUET", {}),
    "avro": ("AVRO", {}),
    "orc": ("ORC", {}),
}


def build_select_sql(
    columns: list[dict],
    from_ref: str,
    source_uri: str = "",
    original_url: str = "",
    source_id: str = "",
) -> str:
    """Build a SELECT statement from column definitions.

    Args:
        columns: List of column dicts with 'name', 'bq_type', optionally 'source_name'.
        from_ref: Fully-qualified BQ external table reference for the FROM clause.
        source_uri: GCS URI of the source file (for provenance comment).
        original_url: Original URL the source file was downloaded from.
        source_id: Unique source identifier for provenance tracking.

    Returns:
        SQL SELECT statement with provenance comments.
    """
    # Provenance comments
    comments = []
    if source_uri:
        comments.append(f"-- Source GCS: {source_uri}")
    if original_url:
        comments.append(f"-- Original URL: {original_url}")
    if source_id:
        comments.append(f"-- Source ID: {source_id}")
    comments.append(f"-- Generated: {datetime.date.today().isoformat()}")

    # SELECT columns with CAST
    select_parts = []
    for col in columns:
        bq_type = col.get("bq_type", "STRING")
        source_name = col.get("source_name", col["name"])
        if source_name != col["name"]:
            select_parts.append(f"  CAST(`{source_name}` AS {bq_type}) AS {col['name']}")
        else:
            select_parts.append(f"  CAST(`{col['name']}` AS {bq_type}) AS {col['name']}")

    sql = (
        "\n".join(comments) + "\n\n"
        "SELECT\n"
        + ",\n".join(select_parts)
        + f"\nFROM\n  `{from_ref}`"
    )

    return sql


def _build_create_table_ddl(
    table_id: str,
    select_sql: str,
    partition_by: dict | None = None,
    cluster_by: list[str] | None = None,
) -> str:
    """Build a CREATE OR REPLACE TABLE ... AS SELECT DDL string.

    Args:
        table_id: Fully-qualified BQ table id (project.dataset.table).
        select_sql: The SELECT statement to materialize.
        partition_by: Optional dict with 'column' key.
        cluster_by: Optional list of clustering column names.

    Returns:
        Complete DDL string.
    """
    parts = [f"CREATE OR REPLACE TABLE `{table_id}`"]

    if partition_by:
        col = partition_by["column"]
        parts.append(f"PARTITION BY DATE({col})")
    if cluster_by:
        parts.append(f"CLUSTER BY {', '.join(cluster_by)}")

    parts.append("AS")
    parts.append(select_sql)

    return "\n".join(parts)


def format_changelog_entry(
    tables: list[str],
    action: str = "created",
    decisions: list[str] | None = None,
    notes: list[str] | None = None,
) -> str:
    """Format a changelog entry in structured markdown.

    Args:
        tables: List of table names affected.
        action: What was done (created, updated, etc.).
        decisions: Schema decision summaries.
        notes: Data quality or other notes.

    Returns:
        Formatted markdown entry.
    """
    today = datetime.date.today().isoformat()
    entry = f"\n## {today} — Tables {action}\n\n"

    entry += "### Tables\n"
    for t in tables:
        entry += f"- `{t}`\n"

    if decisions:
        entry += "\n### Schema Decisions\n"
        for d in decisions:
            entry += f"- {d}\n"

    if notes:
        entry += "\n### Notes\n"
        for n in notes:
            entry += f"- {n}\n"

    return entry
