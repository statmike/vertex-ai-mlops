"""Tests for util_metadata table definitions and write functions."""

from unittest.mock import MagicMock, patch

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


class TestWriteSourceManifest:
    """Tests for write_source_manifest."""

    @patch("agent_orchestrator.util_metadata.GOOGLE_CLOUD_PROJECT", "")
    def test_returns_zero_without_project(self):
        from agent_orchestrator.util_metadata import write_source_manifest

        result = write_source_manifest([{"source_id": "s1", "file_path": "/f"}])
        assert result == 0

    @patch("agent_orchestrator.util_metadata.GOOGLE_CLOUD_PROJECT", "test-project")
    @patch("agent_orchestrator.util_metadata.FULL_DATASET_ID", "test-project.meta")
    def test_writes_rows_to_bq(self):
        from agent_orchestrator.util_metadata import write_source_manifest

        mock_client = MagicMock()
        mock_client.insert_rows_json.return_value = []

        with patch("google.cloud.bigquery.Client", return_value=mock_client):
            result = write_source_manifest([
                {
                    "source_id": "src-1",
                    "file_path": "gs://bucket/file.csv",
                    "file_hash": "abc123",
                    "file_size_bytes": 1024,
                    "file_type": "csv",
                    "classification": "data",
                    "original_url": "https://example.com/file.csv",
                },
            ])

        assert result == 1
        mock_client.insert_rows_json.assert_called_once()
        call_args = mock_client.insert_rows_json.call_args
        assert call_args[0][0] == "test-project.meta.source_manifest"
        rows = call_args[0][1]
        assert len(rows) == 1
        assert rows[0]["source_id"] == "src-1"
        assert rows[0]["file_type"] == "csv"

    @patch("agent_orchestrator.util_metadata.GOOGLE_CLOUD_PROJECT", "test-project")
    @patch("agent_orchestrator.util_metadata.FULL_DATASET_ID", "test-project.meta")
    def test_returns_zero_on_empty_list(self):
        from agent_orchestrator.util_metadata import write_source_manifest

        result = write_source_manifest([])
        assert result == 0


class TestWriteProcessingLog:
    """Tests for write_processing_log."""

    @patch("agent_orchestrator.util_metadata.GOOGLE_CLOUD_PROJECT", "")
    def test_returns_empty_without_project(self):
        from agent_orchestrator.util_metadata import write_processing_log

        result = write_processing_log("s1", "acquire", "crawl", "completed")
        assert result == ""

    @patch("agent_orchestrator.util_metadata.GOOGLE_CLOUD_PROJECT", "test-project")
    @patch("agent_orchestrator.util_metadata.FULL_DATASET_ID", "test-project.meta")
    def test_writes_log_entry(self):
        from agent_orchestrator.util_metadata import write_processing_log

        mock_client = MagicMock()
        mock_client.insert_rows_json.return_value = []

        with patch("google.cloud.bigquery.Client", return_value=mock_client):
            result = write_processing_log(
                "src-1", "acquire", "crawl_url", "completed"
            )

        assert result != ""  # returns a UUID log_id
        mock_client.insert_rows_json.assert_called_once()
        rows = mock_client.insert_rows_json.call_args[0][1]
        assert rows[0]["phase"] == "acquire"
        assert rows[0]["action"] == "crawl_url"
        assert rows[0]["status"] == "completed"

    @patch("agent_orchestrator.util_metadata.GOOGLE_CLOUD_PROJECT", "test-project")
    @patch("agent_orchestrator.util_metadata.FULL_DATASET_ID", "test-project.meta")
    def test_serializes_details_as_json(self):
        import json

        from agent_orchestrator.util_metadata import write_processing_log

        mock_client = MagicMock()
        mock_client.insert_rows_json.return_value = []

        with patch("google.cloud.bigquery.Client", return_value=mock_client):
            write_processing_log(
                "src-1", "discover", "detect_changes", "completed",
                details={"new": 3, "modified": 1},
            )

        rows = mock_client.insert_rows_json.call_args[0][1]
        parsed = json.loads(rows[0]["details"])
        assert parsed["new"] == 3
        assert parsed["modified"] == 1

    @patch("agent_orchestrator.util_metadata.GOOGLE_CLOUD_PROJECT", "test-project")
    @patch("agent_orchestrator.util_metadata.FULL_DATASET_ID", "test-project.meta")
    def test_generates_uuid_id(self):
        import uuid

        from agent_orchestrator.util_metadata import write_processing_log

        mock_client = MagicMock()
        mock_client.insert_rows_json.return_value = []

        with patch("google.cloud.bigquery.Client", return_value=mock_client):
            log_id = write_processing_log("s1", "acquire", "crawl", "completed")

        # Verify it's a valid UUID
        uuid.UUID(log_id)  # raises ValueError if not valid


class TestWriteTableLineage:
    """Tests for write_table_lineage."""

    @patch("agent_orchestrator.util_metadata.GOOGLE_CLOUD_PROJECT", "")
    def test_returns_zero_without_project(self):
        from agent_orchestrator.util_metadata import write_table_lineage

        result = write_table_lineage([{"source_id": "s1", "bq_table": "t1"}])
        assert result == 0

    @patch("agent_orchestrator.util_metadata.GOOGLE_CLOUD_PROJECT", "test-project")
    @patch("agent_orchestrator.util_metadata.FULL_DATASET_ID", "test-project.meta")
    def test_writes_lineage_rows(self):
        from agent_orchestrator.util_metadata import write_table_lineage

        mock_client = MagicMock()
        mock_client.insert_rows_json.return_value = []

        with patch("google.cloud.bigquery.Client", return_value=mock_client):
            result = write_table_lineage([
                {
                    "source_id": "src-1",
                    "bq_table": "project.dataset.users",
                    "source_file": "gs://bucket/users.csv",
                    "column_mappings": {"UserName": "user_name"},
                },
            ])

        assert result == 1
        rows = mock_client.insert_rows_json.call_args[0][1]
        assert rows[0]["bq_table"] == "project.dataset.users"

    @patch("agent_orchestrator.util_metadata.GOOGLE_CLOUD_PROJECT", "test-project")
    @patch("agent_orchestrator.util_metadata.FULL_DATASET_ID", "test-project.meta")
    def test_serializes_column_mappings_as_json(self):
        import json

        from agent_orchestrator.util_metadata import write_table_lineage

        mock_client = MagicMock()
        mock_client.insert_rows_json.return_value = []

        with patch("google.cloud.bigquery.Client", return_value=mock_client):
            write_table_lineage([
                {
                    "source_id": "src-1",
                    "bq_table": "t",
                    "source_file": "gs://b/f.csv",
                    "column_mappings": {"A": "a", "B": "b"},
                },
            ])

        rows = mock_client.insert_rows_json.call_args[0][1]
        parsed = json.loads(rows[0]["column_mappings"])
        assert parsed == {"A": "a", "B": "b"}


class TestWriteWebProvenance:
    """Tests for write_web_provenance."""

    @patch("agent_orchestrator.util_metadata.GOOGLE_CLOUD_PROJECT", "")
    def test_returns_zero_without_project(self):
        from agent_orchestrator.util_metadata import write_web_provenance

        result = write_web_provenance([{"source_id": "s1", "url": "https://x.com"}])
        assert result == 0

    @patch("agent_orchestrator.util_metadata.GOOGLE_CLOUD_PROJECT", "test-project")
    @patch("agent_orchestrator.util_metadata.FULL_DATASET_ID", "test-project.meta")
    def test_writes_provenance_rows(self):
        from agent_orchestrator.util_metadata import write_web_provenance

        mock_client = MagicMock()
        mock_client.insert_rows_json.return_value = []

        with patch("google.cloud.bigquery.Client", return_value=mock_client):
            result = write_web_provenance([
                {
                    "source_id": "src-1",
                    "url": "https://example.com/page",
                    "parent_url": None,
                    "page_title": "Example",
                    "status_code": 200,
                },
                {
                    "source_id": "src-1",
                    "url": "https://example.com/data.csv",
                    "parent_url": "https://example.com/page",
                },
            ])

        assert result == 2
        call_args = mock_client.insert_rows_json.call_args
        assert call_args[0][0] == "test-project.meta.web_provenance"
        rows = call_args[0][1]
        assert len(rows) == 2
        # Each row should have a unique provenance_id
        assert rows[0]["provenance_id"] != rows[1]["provenance_id"]
