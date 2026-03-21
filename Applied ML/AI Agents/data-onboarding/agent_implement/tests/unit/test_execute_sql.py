"""Tests for execute_sql helpers (_build_create_table_ddl)."""

from agent_implement.tools.util_sql import _build_create_table_ddl


class TestBuildCreateTableDdl:
    def test_basic(self):
        ddl = _build_create_table_ddl("p.d.t", "SELECT 1 AS id")
        assert ddl == (
            "CREATE OR REPLACE TABLE `p.d.t`\n"
            "AS\n"
            "SELECT 1 AS id"
        )

    def test_with_partition(self):
        ddl = _build_create_table_ddl(
            "p.d.t", "SELECT * FROM `s`",
            partition_by={"column": "ts", "type": "DAY"},
        )
        lines = ddl.split("\n")
        assert lines[0] == "CREATE OR REPLACE TABLE `p.d.t`"
        assert lines[1] == "PARTITION BY DATE(ts)"
        assert lines[2] == "AS"

    def test_with_cluster(self):
        ddl = _build_create_table_ddl(
            "p.d.t", "SELECT * FROM `s`",
            cluster_by=["a", "b"],
        )
        assert "CLUSTER BY a, b" in ddl

    def test_with_partition_and_cluster(self):
        ddl = _build_create_table_ddl(
            "p.d.t", "SELECT * FROM `s`",
            partition_by={"column": "dt"},
            cluster_by=["region"],
        )
        assert "PARTITION BY DATE_TRUNC(DATE(dt), MONTH)" in ddl
        assert "CLUSTER BY region" in ddl
        # Partition should come before cluster
        assert ddl.index("PARTITION") < ddl.index("CLUSTER")
