"""Tests for SQL generation and changelog formatting utilities."""

from agent_implement.tools.util_sql import (
    _build_create_table_ddl,
    build_select_sql,
    format_changelog_entry,
)


class TestBuildSelectSql:
    def test_basic_select(self):
        columns = [
            {"name": "id", "bq_type": "INT64", "description": "Row identifier"},
            {"name": "name", "bq_type": "STRING", "description": "User name"},
        ]
        result = build_select_sql(columns, "project.dataset.ext_t")

        assert "SELECT" in result
        assert "CAST(`id` AS INT64) AS id" in result
        assert "CAST(`name` AS STRING) AS name" in result
        assert "FROM\n  `project.dataset.ext_t`" in result

    def test_source_name_aliasing(self):
        columns = [
            {"name": "user_name", "source_name": "UserName", "bq_type": "STRING", "description": ""},
        ]
        result = build_select_sql(columns, "p.d.ext_t")
        assert "CAST(`UserName` AS STRING) AS user_name" in result

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
        assert "PARTITION BY DATE(ts)" in ddl
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
