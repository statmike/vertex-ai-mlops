"""Tests for function_tool_load_results (agent_graph_qa)."""

import json

import pytest

from agent_graph_qa.tools.function_tool_load_results import load_results


class TestLoadResults:
    """Test load_results tool with mocked ToolContext."""

    @pytest.mark.asyncio
    async def test_valid_directory(self, mock_tool_context, tmp_path, sample_graph, sample_schema):
        """Valid directory with graph.json and schema.json."""
        (tmp_path / "graph.json").write_text(json.dumps(sample_graph))
        (tmp_path / "schema.json").write_text(json.dumps(sample_schema))
        result = await load_results(str(tmp_path), mock_tool_context)
        assert "Loaded graph" in result
        assert "2 nodes" in result
        assert mock_tool_context.state["graph"] is not None

    @pytest.mark.asyncio
    async def test_with_description(self, mock_tool_context, tmp_path, sample_graph, sample_schema):
        """Directory with optional description.md."""
        (tmp_path / "graph.json").write_text(json.dumps(sample_graph))
        (tmp_path / "schema.json").write_text(json.dumps(sample_schema))
        (tmp_path / "description.md").write_text("A test description.")
        result = await load_results(str(tmp_path), mock_tool_context)
        assert "Description: yes" in result
        assert mock_tool_context.state["diagram_description"] == "A test description."

    @pytest.mark.asyncio
    async def test_missing_directory(self, mock_tool_context):
        result = await load_results("/nonexistent/dir", mock_tool_context)
        assert "Error: Directory not found" in result

    @pytest.mark.asyncio
    async def test_missing_graph_json(self, mock_tool_context, tmp_path, sample_schema):
        (tmp_path / "schema.json").write_text(json.dumps(sample_schema))
        result = await load_results(str(tmp_path), mock_tool_context)
        assert "graph.json not found" in result

    @pytest.mark.asyncio
    async def test_existing_graph_skips_load(self, mock_tool_context, tmp_path):
        """If graph already in state (sub-agent mode), skip loading."""
        mock_tool_context.state["graph"] = {"nodes": [{"id": "n1"}], "edges": []}
        result = await load_results(str(tmp_path), mock_tool_context)
        assert "already available" in result
