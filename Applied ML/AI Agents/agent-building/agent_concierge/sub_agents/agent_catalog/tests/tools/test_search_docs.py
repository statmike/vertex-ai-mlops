"""Tests for function_tool_search_docs (agent_catalog).

The BigQuery client is patched so these run offline — we exercise the tool's
result handling (relevance filtering, source capture, error surface), not BQ.
"""

from unittest.mock import MagicMock, patch

import pytest

from agent_concierge.sub_agents.agent_catalog.tools import function_tool_search_docs
from agent_concierge.sub_agents.agent_catalog.tools.function_tool_search_docs import (
    search_docs,
)


def _row(uri: str, answer: str) -> dict:
    return {"uri": uri, "answer": answer}


@pytest.fixture(autouse=True)
def _reset_client():
    """Ensure each test builds its own patched client."""
    function_tool_search_docs._bq_client = None
    yield
    function_tool_search_docs._bq_client = None


def _patch_rows(rows):
    """Patch the module's BigQuery client to return the given result rows."""
    mock_client = MagicMock()
    mock_client.query.return_value.result.return_value = rows
    return patch.object(function_tool_search_docs, "_client", return_value=mock_client)


class TestSearchDocs:
    @pytest.mark.asyncio
    async def test_returns_relevant_docs_and_records_sources(self, mock_tool_context):
        rows = [
            _row("gs://b/retail-docs/return_policy.txt", "Returns within 30 days."),
            _row("gs://b/retail-docs/care_guide.txt", "NONE"),
        ]
        with _patch_rows(rows):
            result = await search_docs("What is the return window?", mock_tool_context)
        assert "return_policy.txt" in result
        assert "Returns within 30 days." in result
        assert "care_guide.txt" not in result  # filtered by the NONE marker
        assert mock_tool_context.state["catalog_last_sources"] == ["return_policy.txt"]

    @pytest.mark.asyncio
    async def test_no_relevant_docs(self, mock_tool_context):
        with _patch_rows([_row("gs://b/retail-docs/care_guide.txt", "NONE")]):
            result = await search_docs("Do you sell cars?", mock_tool_context)
        assert "No policy or help documents matched" in result
        assert "catalog_last_sources" not in mock_tool_context.state

    @pytest.mark.asyncio
    async def test_query_error_is_surfaced(self, mock_tool_context):
        mock_client = MagicMock()
        mock_client.query.side_effect = RuntimeError("boom")
        with patch.object(function_tool_search_docs, "_client", return_value=mock_client):
            result = await search_docs("anything", mock_tool_context)
        assert "Error searching documents" in result
        assert "setup.py" in result

    @pytest.mark.asyncio
    async def test_connection_id_is_a_literal_not_a_parameter(self, mock_tool_context):
        # AI.GENERATE requires connection_id as a string literal; BigQuery rejects
        # it as a query parameter (400). Guard against regressing to @connection.
        mock_client = MagicMock()
        mock_client.query.return_value.result.return_value = []
        with patch.object(function_tool_search_docs, "_client", return_value=mock_client):
            await search_docs("anything", mock_tool_context)
        query = mock_client.query.call_args.args[0]
        job_config = mock_client.query.call_args.kwargs["job_config"]
        assert "@connection" not in query
        assert "connection_id => '" in query  # inlined as a literal
        param_names = {p.name for p in job_config.query_parameters}
        assert param_names == {"question"}  # only the user's question is bound
