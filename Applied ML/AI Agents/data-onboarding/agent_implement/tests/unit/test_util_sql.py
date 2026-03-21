"""Tests for SQL generation and changelog formatting utilities."""

from unittest.mock import MagicMock, patch

from agent_implement.tools.util_sql import (
    _build_create_table_ddl,
    build_select_sql,
    format_changelog_entry,
    refine_partition_cluster,
)


class TestBuildSelectSql:
    def test_basic_select(self):
        columns = [
            {"name": "id", "bq_type": "INT64", "description": "Row identifier"},
            {"name": "name", "bq_type": "STRING", "description": "User name"},
        ]
        result = build_select_sql(columns, "project.dataset.ext_t")

        assert "SELECT" in result
        assert "SAFE_CAST(CAST(`id` AS STRING) AS INT64) AS id" in result
        assert "CAST(`name` AS STRING) AS name" in result
        assert "FROM\n  `project.dataset.ext_t`" in result

    def test_source_name_aliasing(self):
        columns = [
            {"name": "user_name", "source_name": "UserName", "bq_type": "STRING", "description": ""},
        ]
        result = build_select_sql(columns, "p.d.ext_t")
        assert "CAST(`UserName` AS STRING)" in result
        assert "AS user_name" in result

    def test_provenance_comments(self):
        columns = [{"name": "id", "bq_type": "INT64", "description": ""}]
        result = build_select_sql(
            columns, "p.d.ext_t",
            source_uri="gs://bucket/data.csv",
            original_url="https://example.com/data.csv",
            source_id="src-abc-123",
        )
        assert "-- Source GCS: gs://bucket/data.csv" in result
        assert "-- Original URL: https://example.com/data.csv" in result
        assert "-- Source ID: src-abc-123" in result
        assert "-- Generated:" in result

    def test_no_optional_params(self):
        columns = [{"name": "id", "bq_type": "INT64", "description": ""}]
        result = build_select_sql(columns, "p.d.ext_t")
        assert "-- Source GCS:" not in result
        assert "-- Original URL:" not in result
        assert "-- Source ID:" not in result
        assert "-- Generated:" in result

    def test_external_table_ref_in_from(self):
        columns = [{"name": "id", "bq_type": "INT64", "description": ""}]
        result = build_select_sql(
            columns, "project.dataset.ext_t",
            source_uri="gs://bucket/t.csv",
        )
        assert "FROM\n  `project.dataset.ext_t`" in result
        assert "-- Source GCS: gs://bucket/t.csv" in result


class TestBuildCreateTableDdl:
    def test_basic_ddl(self):
        ddl = _build_create_table_ddl(
            "project.dataset.my_table",
            "SELECT id, name FROM `project.dataset.ext_my_table`",
        )
        assert "CREATE OR REPLACE TABLE `project.dataset.my_table`" in ddl
        assert "SELECT id, name FROM `project.dataset.ext_my_table`" in ddl
        assert "PARTITION" not in ddl
        assert "CLUSTER" not in ddl

    def test_with_partition(self):
        ddl = _build_create_table_ddl(
            "p.d.t",
            "SELECT * FROM `p.d.ext_t`",
            partition_by={"column": "created_at", "type": "DAY"},
        )
        assert "PARTITION BY DATE(created_at)" in ddl

    def test_with_cluster(self):
        ddl = _build_create_table_ddl(
            "p.d.t",
            "SELECT * FROM `p.d.ext_t`",
            cluster_by=["region", "category"],
        )
        assert "CLUSTER BY region, category" in ddl

    def test_with_partition_and_cluster(self):
        ddl = _build_create_table_ddl(
            "p.d.t",
            "SELECT * FROM `p.d.ext_t`",
            partition_by={"column": "ts"},
            cluster_by=["region"],
        )
        assert "PARTITION BY DATE_TRUNC(DATE(ts), MONTH)" in ddl
        assert "CLUSTER BY region" in ddl
        # Partition should come before cluster
        assert ddl.index("PARTITION") < ddl.index("CLUSTER")


class TestFormatChangelogEntry:
    def test_basic_entry(self):
        result = format_changelog_entry(
            tables=["users", "orders"],
            action="created",
        )
        assert "Tables created" in result
        assert "`users`" in result
        assert "`orders`" in result

    def test_with_decisions_and_notes(self):
        result = format_changelog_entry(
            tables=["events"],
            action="updated",
            decisions=["Added timestamp partitioning"],
            notes=["Source had 5% null rate in email column"],
        )
        assert "Schema Decisions" in result
        assert "timestamp partitioning" in result
        assert "Notes" in result
        assert "null rate" in result


# ---------------------------------------------------------------------------
# refine_partition_cluster
# ---------------------------------------------------------------------------

_COLUMNS = [
    {"name": "event_date", "source_name": "EventDate", "bq_type": "DATE"},
    {"name": "region", "source_name": "Region", "bq_type": "STRING"},
    {"name": "category", "source_name": "Category", "bq_type": "STRING"},
    {"name": "id", "source_name": "Id", "bq_type": "INT64"},
]


def _mock_client(row_dicts: list[dict]):
    """Build a mock BQ client that returns rows in query order.

    Each call to ``client.query(sql).result()`` will yield the next row
    from *row_dicts* (a list of dicts, one per query).
    """
    client = MagicMock()
    iterators = []
    for d in row_dicts:
        row = MagicMock()
        for k, v in d.items():
            setattr(row, k, v)
        result_iter = MagicMock()
        result_iter.__iter__ = MagicMock(return_value=iter([row]))
        iterators.append(result_iter)

    job_mocks = [MagicMock(result=MagicMock(return_value=it)) for it in iterators]
    client.query.side_effect = [jm.result() for jm in job_mocks]
    # Fix: client.query() should return an object whose .result() returns the iterator
    client.query.side_effect = None
    jobs = []
    for it in iterators:
        job = MagicMock()
        job.result.return_value = it
        jobs.append(job)
    client.query.side_effect = jobs
    return client


class TestRefinePartitionCluster:
    def test_small_table_skips_partitioning(self):
        """Tables with fewer rows than PARTITION_MIN_ROWS skip partitioning."""
        client = _mock_client([
            {"total_rows": 500},   # count query
            # cluster cardinality query (region + event_date demoted)
            {"region_distinct": 10, "event_date_distinct": 50},
        ])
        part, clust = refine_partition_cluster(
            client=client,
            ext_table_id="p.d.ext_t",
            partition_by={"column": "event_date", "type": "MONTH"},
            cluster_by=["region"],
            columns=_COLUMNS,
        )
        assert part is None
        assert "event_date" in clust  # demoted to clustering
        assert "region" in clust

    def test_daily_within_limit(self):
        """When daily cardinality ≤ 4000, use DAY granularity."""
        client = _mock_client([
            {"total_rows": 50000},  # count query
            {"daily": 365, "monthly": 12, "yearly": 1},  # cardinality query
            {"region_distinct": 50},  # cluster cardinality
        ])
        part, clust = refine_partition_cluster(
            client=client,
            ext_table_id="p.d.ext_t",
            partition_by={"column": "event_date", "type": "MONTH"},
            cluster_by=["region"],
            columns=_COLUMNS,
        )
        assert part == {"column": "event_date", "type": "DAY"}
        assert clust == ["region"]

    def test_monthly_fallback(self):
        """When daily > 4000 but monthly ≤ 4000, use MONTH."""
        client = _mock_client([
            {"total_rows": 50000},
            {"daily": 5000, "monthly": 200, "yearly": 17},
            {"region_distinct": 50},
        ])
        part, clust = refine_partition_cluster(
            client=client,
            ext_table_id="p.d.ext_t",
            partition_by={"column": "event_date", "type": "DAY"},
            cluster_by=["region"],
            columns=_COLUMNS,
        )
        assert part == {"column": "event_date", "type": "MONTH"}

    def test_yearly_fallback(self):
        """When monthly > 4000 but yearly ≤ 4000, use YEAR."""
        client = _mock_client([
            {"total_rows": 50000},
            {"daily": 10000, "monthly": 5000, "yearly": 100},
            {"region_distinct": 50},
        ])
        part, clust = refine_partition_cluster(
            client=client,
            ext_table_id="p.d.ext_t",
            partition_by={"column": "event_date", "type": "DAY"},
            cluster_by=["region"],
            columns=_COLUMNS,
        )
        assert part == {"column": "event_date", "type": "YEAR"}

    def test_all_granularities_exceed_limit(self):
        """When even yearly > 4000, partitioning is dropped entirely."""
        client = _mock_client([
            {"total_rows": 50000},
            {"daily": 50000, "monthly": 50000, "yearly": 5000},
            # cluster query: region + event_date (demoted)
            {"region_distinct": 50, "event_date_distinct": 500},
        ])
        part, clust = refine_partition_cluster(
            client=client,
            ext_table_id="p.d.ext_t",
            partition_by={"column": "event_date", "type": "MONTH"},
            cluster_by=["region"],
            columns=_COLUMNS,
        )
        assert part is None
        assert "event_date" in clust

    def test_drops_constant_cluster_columns(self):
        """Cluster columns with cardinality = 1 are dropped."""
        client = _mock_client([
            {"total_rows": 50000},
            {"daily": 100, "monthly": 10, "yearly": 1},
            {"region_distinct": 1, "category_distinct": 50},
        ])
        part, clust = refine_partition_cluster(
            client=client,
            ext_table_id="p.d.ext_t",
            partition_by={"column": "event_date", "type": "MONTH"},
            cluster_by=["region", "category"],
            columns=_COLUMNS,
        )
        assert "region" not in clust
        assert "category" in clust

    def test_drops_nearly_unique_cluster_columns(self):
        """Cluster columns with cardinality ≥ 90% of total_rows are dropped."""
        client = _mock_client([
            {"total_rows": 1000},
            # cluster query only (no partition proposed)
            {"id_distinct": 999},
        ])
        part, clust = refine_partition_cluster(
            client=client,
            ext_table_id="p.d.ext_t",
            partition_by=None,
            cluster_by=["id"],
            columns=_COLUMNS,
        )
        assert part is None
        assert "id" not in clust

    def test_no_partition_proposed(self):
        """When no partitioning is proposed, only clustering is refined."""
        client = _mock_client([
            {"total_rows": 50000},
            {"region_distinct": 50},
        ])
        part, clust = refine_partition_cluster(
            client=client,
            ext_table_id="p.d.ext_t",
            partition_by=None,
            cluster_by=["region"],
            columns=_COLUMNS,
        )
        assert part is None
        assert clust == ["region"]

    def test_query_failure_returns_original(self):
        """On query failure, falls back to the original proposal."""
        client = MagicMock()
        client.query.side_effect = Exception("BQ error")
        part, clust = refine_partition_cluster(
            client=client,
            ext_table_id="p.d.ext_t",
            partition_by={"column": "event_date", "type": "MONTH"},
            cluster_by=["region"],
            columns=_COLUMNS,
        )
        assert part == {"column": "event_date", "type": "MONTH"}
        assert clust == ["region"]

    def test_empty_cluster_by(self):
        """When no clustering is proposed and no partitioning, both remain empty."""
        client = _mock_client([
            {"total_rows": 50000},
        ])
        part, clust = refine_partition_cluster(
            client=client,
            ext_table_id="p.d.ext_t",
            partition_by=None,
            cluster_by=[],
            columns=_COLUMNS,
        )
        assert part is None
        assert clust == []
