"""Tests for function_tool_search_context."""

from unittest.mock import MagicMock, patch

import pytest

from agent_catalog.tools.function_tool_search_context import search_context


class TestSearchContext:
    """Tests for the search_context tool."""

    @pytest.mark.asyncio
    @patch("agent_catalog.tools.function_tool_search_context.GOOGLE_CLOUD_PROJECT", "")
    async def test_no_project_returns_error(self, mock_tool_context):
        result = await search_context("test query", tool_context=mock_tool_context)
        assert "GOOGLE_CLOUD_PROJECT not set" in result

    @pytest.mark.asyncio
    @patch("agent_catalog.tools.function_tool_search_context.GOOGLE_CLOUD_PROJECT", "test-proj")
    @patch("agent_catalog.tools.function_tool_search_context.BQ_CONTEXT_DATASET", "test_context")
    async def test_formatted_results_returned(self, mock_tool_context):
        mock_row = MagicMock()
        mock_row.chunk_id = "chunk-1"
        mock_row.source_dataset = "bronze"
        mock_row.source_table = "users"
        mock_row.chunk_type = "column_description"
        mock_row.chunk_text = "Column: bronze.users.name (STRING)\nDescription: User name"
        mock_row.distance = 0.1234

        mock_query_result = MagicMock()
        mock_query_result.result.return_value = [mock_row]

        mock_client = MagicMock()
        mock_client.query.return_value = mock_query_result

        with patch("google.cloud.bigquery.Client", return_value=mock_client):
            result = await search_context(
                "What is the name column?", tool_context=mock_tool_context
            )

        assert "Found 1 relevant chunk(s)" in result
        assert "column_description" in result
        assert "bronze.users" in result
        assert "0.1234" in result

    @pytest.mark.asyncio
    @patch("agent_catalog.tools.function_tool_search_context.GOOGLE_CLOUD_PROJECT", "test-proj")
    @patch("agent_catalog.tools.function_tool_search_context.BQ_CONTEXT_DATASET", "test_context")
    async def test_no_results_message(self, mock_tool_context):
        mock_query_result = MagicMock()
        mock_query_result.result.return_value = []

        mock_client = MagicMock()
        mock_client.query.return_value = mock_query_result

        with patch("google.cloud.bigquery.Client", return_value=mock_client):
            result = await search_context(
                "nonexistent thing", tool_context=mock_tool_context
            )

        assert "No matching documentation found" in result

    @pytest.mark.asyncio
    @patch("agent_catalog.tools.function_tool_search_context.GOOGLE_CLOUD_PROJECT", "test-proj")
    @patch("agent_catalog.tools.function_tool_search_context.BQ_CONTEXT_DATASET", "test_context")
    async def test_error_handling(self, mock_tool_context):
        mock_client = MagicMock()
        mock_client.query.side_effect = Exception("BQ error")

        with patch("google.cloud.bigquery.Client", return_value=mock_client):
            result = await search_context(
                "test query", tool_context=mock_tool_context
            )

        assert "Error searching context" in result
        assert "BQ error" in result

    @pytest.mark.asyncio
    @patch("agent_catalog.tools.function_tool_search_context.GOOGLE_CLOUD_PROJECT", "test-proj")
    @patch("agent_catalog.tools.function_tool_search_context.BQ_CONTEXT_DATASET", "test_context")
    async def test_parameterized_query(self, mock_tool_context):
        """Verify the query uses parameterized inputs."""
        mock_query_result = MagicMock()
        mock_query_result.result.return_value = []

        mock_client = MagicMock()
        mock_client.query.return_value = mock_query_result

        with patch("google.cloud.bigquery.Client", return_value=mock_client):
            await search_context(
                "test query", top_k=5, tool_context=mock_tool_context
            )

        # Verify query was called with a job config containing parameters
        call_args = mock_client.query.call_args
        job_config = call_args.kwargs.get("job_config") or call_args[1].get("job_config")
        assert job_config is not None
        params = job_config.query_parameters
        assert len(params) == 2
        param_names = {p.name for p in params}
        assert param_names == {"query", "top_k"}
