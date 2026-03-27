"""Tests for util_context_chunks chunking logic."""

from unittest.mock import MagicMock, patch

from agent_orchestrator.util_context_chunks import (
    chunk_table_documentation,
    insert_context_chunks,
)


class TestChunkTableDocumentation:
    """Test the chunking logic."""

    def test_full_doc_creates_table_chunk(self):
        chunks = chunk_table_documentation(
            dataset_name="bronze",
            table_name="users",
            documentation_md="# Users\nUser data.",
            column_details=[],
        )
        table_chunks = [c for c in chunks if c["chunk_type"] == "table_documentation"]
        assert len(table_chunks) == 1
        assert "Table: bronze.users" in table_chunks[0]["chunk_text"]
        assert "# Users" in table_chunks[0]["chunk_text"]

    def test_each_column_creates_chunk(self):
        columns = [
            {"name": "id", "bq_type": "INT64", "description": "Primary key"},
            {"name": "name", "bq_type": "STRING", "description": "User name"},
            {"name": "email", "bq_type": "STRING", "description": "Email address"},
        ]
        chunks = chunk_table_documentation(
            dataset_name="bronze",
            table_name="users",
            documentation_md="# Users",
            column_details=columns,
        )
        col_chunks = [c for c in chunks if c["chunk_type"] == "column_description"]
        assert len(col_chunks) == 3
        assert "Column: bronze.users.id (INT64)" in col_chunks[0]["chunk_text"]
        assert "Description: Primary key" in col_chunks[0]["chunk_text"]

    def test_related_tables_creates_relationship_chunk(self):
        chunks = chunk_table_documentation(
            dataset_name="bronze",
            table_name="orders",
            documentation_md="# Orders",
            column_details=[],
            related_tables={"shared_keys": ["users"], "contains": ["order_items"]},
        )
        rel_chunks = [c for c in chunks if c["chunk_type"] == "relationship"]
        assert len(rel_chunks) == 1
        assert "shared_keys" in rel_chunks[0]["chunk_text"]
        assert "contains" in rel_chunks[0]["chunk_text"]

    def test_profile_stats_creates_chunk(self):
        chunks = chunk_table_documentation(
            dataset_name="bronze",
            table_name="users",
            documentation_md="# Users",
            column_details=[],
            profile_stats="Row count: 1000, Null ratio: 0.05",
        )
        stat_chunks = [c for c in chunks if c["chunk_type"] == "profile_stat"]
        assert len(stat_chunks) == 1
        assert "Row count: 1000" in stat_chunks[0]["chunk_text"]

    def test_empty_inputs_minimal_chunks(self):
        chunks = chunk_table_documentation(
            dataset_name="bronze",
            table_name="empty",
            documentation_md="",
            column_details=[],
        )
        # Should have exactly 1 chunk: the table_documentation chunk
        assert len(chunks) == 1
        assert chunks[0]["chunk_type"] == "table_documentation"

    def test_no_relationship_or_profile_without_data(self):
        chunks = chunk_table_documentation(
            dataset_name="bronze",
            table_name="t",
            documentation_md="Doc",
            column_details=[{"name": "a", "bq_type": "STRING", "description": "col a"}],
            related_tables=None,
            profile_stats=None,
        )
        types = {c["chunk_type"] for c in chunks}
        assert types == {"table_documentation", "table_summary", "column_description"}

    def test_table_summary_chunk_created(self):
        columns = [
            {"name": "id", "bq_type": "INT64", "description": "Primary key"},
            {"name": "name", "bq_type": "STRING", "description": "User name"},
        ]
        chunks = chunk_table_documentation(
            dataset_name="bronze",
            table_name="users",
            documentation_md="# Users",
            column_details=columns,
        )
        summary_chunks = [c for c in chunks if c["chunk_type"] == "table_summary"]
        assert len(summary_chunks) == 1
        text = summary_chunks[0]["chunk_text"]
        assert "Table summary: bronze.users" in text
        assert "2 columns" in text
        assert "id (INT64): Primary key" in text
        assert "name (STRING): User name" in text

    def test_no_table_summary_when_no_columns(self):
        chunks = chunk_table_documentation(
            dataset_name="bronze",
            table_name="empty",
            documentation_md="Doc",
            column_details=[],
        )
        summary_chunks = [c for c in chunks if c["chunk_type"] == "table_summary"]
        assert len(summary_chunks) == 0

    def test_long_doc_truncated(self):
        long_doc = "x" * 10000
        chunks = chunk_table_documentation(
            dataset_name="bronze",
            table_name="t",
            documentation_md=long_doc,
            column_details=[],
        )
        table_chunk = chunks[0]
        assert len(table_chunk["chunk_text"]) <= 8000

    def test_chunk_ids_are_unique(self):
        chunks = chunk_table_documentation(
            dataset_name="bronze",
            table_name="t",
            documentation_md="Doc",
            column_details=[
                {"name": "a", "bq_type": "STRING", "description": "A"},
                {"name": "b", "bq_type": "INT64", "description": "B"},
            ],
            related_tables={"shared_keys": ["other"]},
            profile_stats="Stats",
        )
        ids = [c["chunk_id"] for c in chunks]
        assert len(ids) == len(set(ids))

    def test_all_chunks_have_required_fields(self):
        chunks = chunk_table_documentation(
            dataset_name="bronze",
            table_name="t",
            documentation_md="Doc",
            column_details=[{"name": "a", "bq_type": "STRING", "description": "A"}],
        )
        required = {"chunk_id", "source_dataset", "source_table", "chunk_type", "chunk_text", "created_at"}
        for chunk in chunks:
            assert required.issubset(chunk.keys())


class TestInsertContextChunks:
    """Tests for insert_context_chunks."""

    @patch("agent_orchestrator.util_context_chunks.GOOGLE_CLOUD_PROJECT", "")
    def test_returns_zero_without_project(self):
        result = insert_context_chunks([{"chunk_id": "x"}])
        assert result == 0

    def test_returns_zero_for_empty_list(self):
        result = insert_context_chunks([])
        assert result == 0

    @patch("agent_orchestrator.util_context_chunks.GOOGLE_CLOUD_PROJECT", "test-project")
    @patch("agent_orchestrator.util_context_chunks.FULL_DATASET_ID", "test-project.context")
    def test_inserts_chunks_to_bq(self):
        mock_client = MagicMock()
        mock_client.insert_rows_json.return_value = []
        with patch("google.cloud.bigquery.Client", return_value=mock_client):
            chunks = [
                {"chunk_id": "1", "chunk_text": "test"},
                {"chunk_id": "2", "chunk_text": "test2"},
            ]
            result = insert_context_chunks(chunks)
            assert result == 2
            mock_client.insert_rows_json.assert_called_once()
