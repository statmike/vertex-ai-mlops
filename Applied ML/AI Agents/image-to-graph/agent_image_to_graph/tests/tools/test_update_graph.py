"""Tests for function_tool_update_graph."""

import pytest

from agent_image_to_graph.tools.function_tool_update_graph import update_graph


class TestUpdateGraphAddNode:
    """Test add_node operations."""

    @pytest.mark.asyncio
    async def test_add_valid_node(self, mock_tool_context):
        mock_tool_context.state["graph"] = {"nodes": [], "edges": []}
        ops = [{"op": "add_node", "data": {"id": "n1", "label": "Start"}}]
        result = await update_graph(ops, mock_tool_context)
        assert "+ node 'n1'" in result
        assert len(mock_tool_context.state["graph"]["nodes"]) == 1

    @pytest.mark.asyncio
    async def test_add_node_missing_id(self, mock_tool_context):
        mock_tool_context.state["graph"] = {"nodes": [], "edges": []}
        ops = [{"op": "add_node", "data": {"label": "No ID"}}]
        result = await update_graph(ops, mock_tool_context)
        assert "Error" in result and "'id' required" in result

    @pytest.mark.asyncio
    async def test_add_duplicate_node(self, mock_tool_context):
        mock_tool_context.state["graph"] = {
            "nodes": [{"id": "n1", "label": "Existing"}],
            "edges": [],
        }
        ops = [{"op": "add_node", "data": {"id": "n1", "label": "Duplicate"}}]
        result = await update_graph(ops, mock_tool_context)
        assert "Skipped" in result

    @pytest.mark.asyncio
    async def test_add_node_with_bbox_normalization(self, mock_tool_context):
        mock_tool_context.state["graph"] = {"nodes": [], "edges": []}
        ops = [
            {
                "op": "add_node",
                "data": {
                    "id": "n1",
                    "label": "Box",
                    "bounding_box": {"top": 10, "left": 20, "bottom": 100, "right": 200},
                },
            }
        ]
        result = await update_graph(ops, mock_tool_context)
        assert "+ node 'n1'" in result
        node = mock_tool_context.state["graph"]["nodes"][0]
        assert node["bounding_box"] == [10, 20, 100, 200]


class TestUpdateGraphAddEdge:
    """Test add_edge operations."""

    @pytest.mark.asyncio
    async def test_add_valid_edge(self, mock_tool_context):
        mock_tool_context.state["graph"] = {
            "nodes": [{"id": "n1"}, {"id": "n2"}],
            "edges": [],
        }
        ops = [{"op": "add_edge", "data": {"id": "e1", "source": "n1", "target": "n2"}}]
        result = await update_graph(ops, mock_tool_context)
        assert "+ edge 'e1'" in result

    @pytest.mark.asyncio
    async def test_add_edge_missing_source_target(self, mock_tool_context):
        mock_tool_context.state["graph"] = {"nodes": [], "edges": []}
        ops = [{"op": "add_edge", "data": {"id": "e1"}}]
        result = await update_graph(ops, mock_tool_context)
        assert "'source' and 'target' required" in result


class TestUpdateGraphBatch:
    """Test batch operations."""

    @pytest.mark.asyncio
    async def test_batch_operations(self, mock_tool_context):
        mock_tool_context.state["graph"] = {"nodes": [], "edges": []}
        ops = [
            {"op": "add_node", "data": {"id": "n1", "label": "A"}},
            {"op": "add_node", "data": {"id": "n2", "label": "B"}},
            {"op": "add_edge", "data": {"id": "e1", "source": "n1", "target": "n2"}},
        ]
        result = await update_graph(ops, mock_tool_context)
        assert "3 ops" in result
        assert len(mock_tool_context.state["graph"]["nodes"]) == 2
        assert len(mock_tool_context.state["graph"]["edges"]) == 1

    @pytest.mark.asyncio
    async def test_no_graph_state(self, mock_tool_context):
        ops = [{"op": "add_node", "data": {"id": "n1", "label": "A"}}]
        result = await update_graph(ops, mock_tool_context)
        assert "Error" in result

    @pytest.mark.asyncio
    async def test_unknown_op(self, mock_tool_context):
        mock_tool_context.state["graph"] = {"nodes": [], "edges": []}
        ops = [{"op": "delete_node", "data": {"id": "n1"}}]
        result = await update_graph(ops, mock_tool_context)
        assert "unknown op" in result.lower()
