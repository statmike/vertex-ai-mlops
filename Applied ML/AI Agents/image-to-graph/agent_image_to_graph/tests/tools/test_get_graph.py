"""Tests for function_tool_get_graph."""

import pytest

from agent_image_to_graph.tools.function_tool_get_graph import get_graph


class TestGetGraph:
    """Test get_graph tool with mocked ToolContext."""

    @pytest.mark.asyncio
    async def test_no_graph_in_state(self, mock_tool_context):
        result = await get_graph(mock_tool_context)
        assert "Error" in result

    @pytest.mark.asyncio
    async def test_valid_graph(self, mock_tool_context, sample_graph):
        mock_tool_context.state["graph"] = sample_graph
        result = await get_graph(mock_tool_context)
        assert "Nodes: 2" in result
        assert "Edges: 1" in result
        assert "flowchart" in result
        assert '"n1"' in result  # JSON dump includes node ids
