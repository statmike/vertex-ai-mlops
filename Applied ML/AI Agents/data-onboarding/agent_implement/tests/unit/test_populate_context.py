"""Tests for function_tool_populate_context."""

from unittest.mock import MagicMock, patch

import pytest

from agent_implement.tools.function_tool_populate_context import populate_context_chunks


@pytest.fixture
def mock_tool_context():
    ctx = MagicMock()
    ctx.state = {}
    return ctx


class TestPopulateContextChunks:
    """Tests for the populate_context_chunks tool."""

    @pytest.mark.asyncio
    async def test_no_docs_returns_early(self, mock_tool_context):
        result = await populate_context_chunks(mock_tool_context)
        assert "No generated documentation" in result

    @pytest.mark.asyncio
    @patch("agent_implement.tools.function_tool_populate_context.GOOGLE_CLOUD_PROJECT", "")
    async def test_no_project_returns_error(self, mock_tool_context):
        mock_tool_context.state["generated_docs"] = {"t1": {"documentation_md": "doc"}}
        result = await populate_context_chunks(mock_tool_context)
        assert "GOOGLE_CLOUD_PROJECT not set" in result

    @pytest.mark.asyncio
    @patch("agent_implement.tools.function_tool_populate_context.GOOGLE_CLOUD_PROJECT", "test-proj")
    @patch("agent_implement.tools.function_tool_populate_context.ensure_context_dataset")
    @patch("agent_implement.tools.function_tool_populate_context.insert_context_chunks", return_value=5)
    @patch("agent_implement.tools.function_tool_populate_context.chunk_table_documentation")
    @patch("agent_implement.tools.function_tool_populate_context.write_processing_log")
    async def test_chunks_created_from_docs(
        self, mock_log, mock_chunk, mock_insert, mock_ensure, mock_tool_context
    ):
        mock_chunk.return_value = [
            {"chunk_id": "1", "chunk_text": "t1"},
            {"chunk_id": "2", "chunk_text": "t2"},
        ]
        mock_tool_context.state["generated_docs"] = {
            "table_a": {
                "documentation_md": "# Table A",
                "column_details": [{"name": "col1", "bq_type": "STRING", "description": "A col"}],
                "related_tables": None,
            },
        }
        mock_tool_context.state["source_id"] = "src-123"
        mock_tool_context.state["bq_bronze_dataset"] = "test_bronze"

        result = await populate_context_chunks(mock_tool_context)

        mock_ensure.assert_called_once()
        mock_chunk.assert_called_once_with(
            dataset_name="test_bronze",
            table_name="table_a",
            documentation_md="# Table A",
            column_details=[{"name": "col1", "bq_type": "STRING", "description": "A col"}],
            related_tables=None,
        )
        mock_insert.assert_called_once()
        assert "Tables chunked: 1" in result
        assert "Chunks inserted: 5" in result
        mock_log.assert_called_once()

    @pytest.mark.asyncio
    @patch("agent_implement.tools.function_tool_populate_context.GOOGLE_CLOUD_PROJECT", "test-proj")
    @patch("agent_implement.tools.function_tool_populate_context.ensure_context_dataset")
    @patch("agent_implement.tools.function_tool_populate_context.insert_context_chunks", return_value=0)
    @patch("agent_implement.tools.function_tool_populate_context.chunk_table_documentation", return_value=[])
    async def test_multiple_tables_chunked(
        self, mock_chunk, mock_insert, mock_ensure, mock_tool_context
    ):
        mock_tool_context.state["generated_docs"] = {
            "t1": {"documentation_md": "doc1", "column_details": [], "related_tables": None},
            "t2": {"documentation_md": "doc2", "column_details": [], "related_tables": None},
        }
        result = await populate_context_chunks(mock_tool_context)
        assert mock_chunk.call_count == 2
        assert "Tables chunked: 2" in result
