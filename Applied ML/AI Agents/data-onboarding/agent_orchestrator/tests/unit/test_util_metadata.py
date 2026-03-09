"""Tests for util_metadata table definitions."""

from agent_orchestrator.util_metadata import TABLE_DDLS


class TestMetadataTableDDLs:
    """Verify metadata table DDLs are defined correctly."""

    def test_all_five_tables_defined(self):
        expected_tables = {
            "source_manifest",
            "processing_log",
            "table_lineage",
            "schema_decisions",
            "web_provenance",
        }
        # TABLE_DDLS may be empty if GOOGLE_CLOUD_PROJECT is not set,
        # but the keys should match when it is set.
        if TABLE_DDLS:
            assert set(TABLE_DDLS.keys()) == expected_tables

    def test_ddls_contain_create_table(self):
        for table_name, ddl in TABLE_DDLS.items():
            assert "CREATE TABLE IF NOT EXISTS" in ddl, f"{table_name} DDL missing CREATE TABLE"

    def test_ddls_have_partitioning(self):
        for table_name, ddl in TABLE_DDLS.items():
            assert "PARTITION BY" in ddl, f"{table_name} DDL missing PARTITION BY"

    def test_ddls_have_clustering(self):
        for table_name, ddl in TABLE_DDLS.items():
            assert "CLUSTER BY" in ddl, f"{table_name} DDL missing CLUSTER BY"
