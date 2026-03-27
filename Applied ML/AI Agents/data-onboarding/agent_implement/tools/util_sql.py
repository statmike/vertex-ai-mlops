"""SQL generation utilities for BigQuery table creation."""

import datetime
import logging

from agent_orchestrator.config import PARTITION_MIN_ROWS

logger = logging.getLogger(__name__)

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

    # SELECT columns with SAFE_CAST (tolerates bad source values).
    # Cast through STRING first to avoid hard "Invalid cast" errors
    # (e.g., TIME→TIMESTAMP is rejected even with SAFE_CAST, but
    #  STRING→TIMESTAMP returns NULL as expected).
    select_parts = []
    for col in columns:
        bq_type = col.get("bq_type", "STRING")
        source_name = col.get("source_name", col["name"])
        src_ref = f"`{source_name}`"
        if bq_type == "STRING":
            expr = f"  CAST({src_ref} AS STRING) AS {col['name']}"
        else:
            expr = f"  SAFE_CAST(CAST({src_ref} AS STRING) AS {bq_type}) AS {col['name']}"
        select_parts.append(expr)

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
    columns: list[dict] | None = None,
) -> str:
    """Build a CREATE OR REPLACE TABLE ... AS SELECT DDL string.

    Args:
        table_id: Fully-qualified BQ table id (project.dataset.table).
        select_sql: The SELECT statement to materialize.
        partition_by: Optional dict with 'column' key.
        cluster_by: Optional list of clustering column names.
        columns: Optional column definitions to validate clustering types.

    Returns:
        Complete DDL string.
    """
    parts = [f"CREATE OR REPLACE TABLE `{table_id}`"]

    if partition_by:
        col = partition_by["column"]
        granularity = partition_by.get("type", "MONTH")
        # Resolve column BQ type to pick the correct truncation function
        col_bq_type = None
        if columns:
            col_bq_type = next(
                (c.get("bq_type", "").upper() for c in columns if c["name"] == col), None
            )
        if granularity == "DAY":
            # Daily partitioning — simple syntax
            if col_bq_type == "DATE":
                parts.append(f"PARTITION BY {col}")
            else:
                parts.append(f"PARTITION BY DATE({col})")
        else:
            # Coarser granularity (MONTH, YEAR) — use truncation functions
            if col_bq_type == "DATE":
                parts.append(f"PARTITION BY DATE_TRUNC({col}, {granularity})")
            elif col_bq_type in ("TIMESTAMP", "DATETIME"):
                parts.append(f"PARTITION BY TIMESTAMP_TRUNC({col}, {granularity})")
            else:
                # Fallback: wrap in DATE() then truncate
                parts.append(f"PARTITION BY DATE_TRUNC(DATE({col}), {granularity})")
    if cluster_by:
        # BQ does not allow FLOAT64/FLOAT/NUMERIC/TIME types in CLUSTER BY
        if columns:
            float_types = {"FLOAT64", "FLOAT", "NUMERIC", "BIGNUMERIC", "TIME"}
            col_types = {c["name"]: c.get("bq_type", "STRING").upper() for c in columns}
            cluster_by = [c for c in cluster_by if col_types.get(c, "STRING") not in float_types]
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


# ---------------------------------------------------------------------------
# Partition / cluster refinement
# ---------------------------------------------------------------------------

_PARTITION_LIMIT = 4000


def refine_partition_cluster(
    client,
    ext_table_id: str,
    partition_by: dict | None,
    cluster_by: list[str],
    columns: list[dict],
) -> tuple[dict | None, list[str]]:
    """Validate and refine partition/cluster choices by querying the external table.

    Uses actual data cardinality (via APPROX_COUNT_DISTINCT) to decide the
    right partitioning granularity and drop useless clustering candidates.

    Args:
        client: A ``bigquery.Client`` instance.
        ext_table_id: Fully-qualified external table id (project.dataset.table).
        partition_by: Proposed partition dict with ``column`` and ``type`` keys,
            or *None* if no partitioning was proposed.
        cluster_by: Proposed list of clustering column names.
        columns: Enriched column definitions (must have ``source_name``,
            ``name``, and ``bq_type`` keys).

    Returns:
        Tuple of ``(refined_partition_by, refined_cluster_by)``.
        Falls back to the original proposal on any query error.
    """
    try:
        # --- row count check ------------------------------------------------
        count_sql = f"SELECT COUNT(*) AS total_rows FROM `{ext_table_id}`"
        total_rows = 0
        try:
            row = next(iter(client.query(count_sql).result()))
            total_rows = row.total_rows or 0
        except Exception:
            logger.warning("refine_partition_cluster: row count query failed, using proposal as-is")
            return partition_by, list(cluster_by)

        # --- partitioning ---------------------------------------------------
        refined_partition = partition_by
        demoted_col: str | None = None

        if partition_by:
            part_col = partition_by["column"]
            # Find the source column name for the partition column
            source_col = part_col
            for c in columns:
                if c["name"] == part_col:
                    source_col = c.get("source_name", part_col)
                    break

            if total_rows < PARTITION_MIN_ROWS:
                # Small table — skip partitioning, demote to cluster candidate
                logger.info(
                    f"refine_partition_cluster: {total_rows} rows < {PARTITION_MIN_ROWS} "
                    f"threshold, skipping partitioning on {part_col}"
                )
                refined_partition = None
                demoted_col = part_col
            else:
                # Query actual date cardinality at each granularity
                cardinality_sql = (
                    f"SELECT\n"
                    f"  APPROX_COUNT_DISTINCT(SAFE_CAST(`{source_col}` AS DATE)) AS daily,\n"
                    f"  APPROX_COUNT_DISTINCT(DATE_TRUNC(SAFE_CAST(`{source_col}` AS DATE), MONTH)) AS monthly,\n"
                    f"  APPROX_COUNT_DISTINCT(DATE_TRUNC(SAFE_CAST(`{source_col}` AS DATE), YEAR)) AS yearly\n"
                    f"FROM `{ext_table_id}`"
                )
                try:
                    row = next(iter(client.query(cardinality_sql).result()))
                    daily = row.daily or 0
                    monthly = row.monthly or 0
                    yearly = row.yearly or 0

                    if daily <= _PARTITION_LIMIT:
                        refined_partition = {"column": part_col, "type": "DAY"}
                    elif monthly <= _PARTITION_LIMIT:
                        refined_partition = {"column": part_col, "type": "MONTH"}
                    elif yearly <= _PARTITION_LIMIT:
                        refined_partition = {"column": part_col, "type": "YEAR"}
                    else:
                        # Too many partitions even at YEAR — drop partitioning
                        logger.info(
                            f"refine_partition_cluster: {part_col} has {yearly} yearly "
                            f"partitions (>{_PARTITION_LIMIT}), skipping partitioning"
                        )
                        refined_partition = None
                        demoted_col = part_col
                except Exception:
                    logger.warning(
                        "refine_partition_cluster: cardinality query failed, "
                        "keeping proposed partitioning"
                    )

        # --- clustering -----------------------------------------------------
        refined_cluster = list(cluster_by)

        # Add demoted partition column as a cluster candidate
        if demoted_col and demoted_col not in refined_cluster:
            refined_cluster.append(demoted_col)

        # Validate cluster candidates against actual cardinality
        if refined_cluster and total_rows > 0:
            # Find source names for cluster columns
            cluster_source_names: dict[str, str] = {}
            for col_name in refined_cluster:
                for c in columns:
                    if c["name"] == col_name:
                        cluster_source_names[col_name] = c.get("source_name", col_name)
                        break
                else:
                    cluster_source_names[col_name] = col_name

            distinct_parts = ", ".join(
                f"APPROX_COUNT_DISTINCT(`{cluster_source_names[col]}`) AS `{col}_distinct`"
                for col in refined_cluster
            )
            cluster_sql = (
                f"SELECT {distinct_parts}\n"
                f"FROM `{ext_table_id}`"
            )
            try:
                row = next(iter(client.query(cluster_sql).result()))
                keep = []
                for col in refined_cluster:
                    distinct = getattr(row, f"{col}_distinct", None)
                    if distinct is None:
                        keep.append(col)
                        continue
                    # Drop constant columns (cardinality = 1) and
                    # nearly-unique columns (cardinality ≥ 90% of total rows)
                    if distinct <= 1:
                        logger.info(f"refine_partition_cluster: dropping cluster col {col} (constant)")
                    elif distinct >= total_rows * 0.9:
                        logger.info(
                            f"refine_partition_cluster: dropping cluster col {col} "
                            f"(nearly unique: {distinct}/{total_rows})"
                        )
                    else:
                        keep.append(col)
                refined_cluster = keep
            except Exception:
                logger.warning(
                    "refine_partition_cluster: cluster cardinality query failed, "
                    "keeping proposed clustering"
                )

        return refined_partition, refined_cluster

    except Exception:
        logger.warning("refine_partition_cluster: unexpected error, using proposal as-is")
        return partition_by, list(cluster_by)
