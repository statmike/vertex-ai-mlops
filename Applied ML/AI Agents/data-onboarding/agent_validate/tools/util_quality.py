"""BQ query helpers for data quality validation."""

import logging

from agent_orchestrator.config import (
    BQ_BRONZE_DATASET,
    BQ_META_DATASET,
    GOOGLE_CLOUD_PROJECT,
)

logger = logging.getLogger(__name__)


def get_bq_client():
    """Get a BigQuery client."""
    from google.cloud import bigquery

    return bigquery.Client(project=GOOGLE_CLOUD_PROJECT)


def get_table_row_count(table_name: str, bronze_dataset: str = "") -> int | None:
    """Get row count from a BQ table. Returns None if table doesn't exist."""
    if not GOOGLE_CLOUD_PROJECT:
        return None

    try:
        client = get_bq_client()
        ds = bronze_dataset or BQ_BRONZE_DATASET
        table_id = f"{GOOGLE_CLOUD_PROJECT}.{ds}.{table_name}"
        table = client.get_table(table_id)
        return table.num_rows
    except Exception as e:
        logger.warning(f"Failed to get row count for {table_name}: {e}")
        return None


def get_column_null_rates(table_name: str, bronze_dataset: str = "") -> dict[str, float]:
    """Get null rates for each column in a BQ table.

    Returns dict of column_name → null_percentage.
    """
    if not GOOGLE_CLOUD_PROJECT:
        return {}

    try:
        client = get_bq_client()
        ds = bronze_dataset or BQ_BRONZE_DATASET
        table_id = f"{GOOGLE_CLOUD_PROJECT}.{ds}.{table_name}"
        table = client.get_table(table_id)

        if table.num_rows == 0:
            return {field.name: 0.0 for field in table.schema}

        # Build query to check all columns
        null_exprs = []
        for field in table.schema:
            null_exprs.append(
                f"ROUND(COUNTIF(`{field.name}` IS NULL) / COUNT(*) * 100, 2) AS `{field.name}`"
            )

        query = f"SELECT {', '.join(null_exprs)} FROM `{table_id}`"
        result = client.query(query).result()
        row = next(iter(result))
        return dict(row.items())

    except Exception as e:
        logger.warning(f"Failed to get null rates for {table_name}: {e}")
        return {}


def get_column_types(table_name: str, bronze_dataset: str = "") -> dict[str, str]:
    """Get actual column types from a BQ table.

    Returns dict of column_name → BQ type string.
    """
    if not GOOGLE_CLOUD_PROJECT:
        return {}

    try:
        client = get_bq_client()
        ds = bronze_dataset or BQ_BRONZE_DATASET
        table_id = f"{GOOGLE_CLOUD_PROJECT}.{ds}.{table_name}"
        table = client.get_table(table_id)
        return {field.name: field.field_type for field in table.schema}

    except Exception as e:
        logger.warning(f"Failed to get column types for {table_name}: {e}")
        return {}


def check_lineage_exists(source_id: str, table_name: str) -> bool:
    """Check if lineage records exist for a given source and table."""
    if not GOOGLE_CLOUD_PROJECT:
        return False

    try:
        from google.cloud import bigquery

        client = get_bq_client()
        table_id = f"{GOOGLE_CLOUD_PROJECT}.{BQ_META_DATASET}.table_lineage"

        query = f"""
        SELECT COUNT(*) as cnt
        FROM `{table_id}`
        WHERE source_id = @source_id AND bq_table LIKE @table_pattern
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("source_id", "STRING", source_id),
                bigquery.ScalarQueryParameter("table_pattern", "STRING", f"%{table_name}%"),
            ]
        )
        result = client.query(query, job_config=job_config).result()
        row = next(iter(result))
        return row.cnt > 0

    except Exception as e:
        logger.warning(f"Failed to check lineage for {table_name}: {e}")
        return False
