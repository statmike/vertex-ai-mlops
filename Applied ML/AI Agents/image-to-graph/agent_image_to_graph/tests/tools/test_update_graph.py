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
    async def test_add_node_duplicate_label_bbox_skipped(self, mock_tool_context):
        """Node with same label and overlapping bbox as existing node is skipped."""
        mock_tool_context.state["graph"] = {
            "nodes": [
                {"id": "GND_1", "label": "GND", "bounding_box": [347, 335, 356, 345]}
            ],
            "edges": [],
        }
        ops = [
            {
                "op": "add_node",
                "data": {
                    "id": "GND_NET",
                    "label": "GND",
                    "bounding_box": [347, 335, 356, 345],
                },
            }
        ]
        result = await update_graph(ops, mock_tool_context)
        assert "Skipped" in result
        assert "duplicate of" in result
        assert "GND_1" in result
        assert len(mock_tool_context.state["graph"]["nodes"]) == 1

    @pytest.mark.asyncio
    async def test_add_node_same_label_different_position_allowed(self, mock_tool_context):
        """Nodes with same label but different positions are not duplicates."""
        mock_tool_context.state["graph"] = {
            "nodes": [
                {"id": "GND_1", "label": "GND", "bounding_box": [100, 100, 120, 120]}
            ],
            "edges": [],
        }
        ops = [
            {
                "op": "add_node",
                "data": {
                    "id": "GND_2",
                    "label": "GND",
                    "bounding_box": [800, 800, 820, 820],
                },
            }
        ]
        result = await update_graph(ops, mock_tool_context)
        assert "+ node 'GND_2'" in result
        assert len(mock_tool_context.state["graph"]["nodes"]) == 2

    @pytest.mark.asyncio
    async def test_add_node_different_label_same_bbox_allowed(self, mock_tool_context):
        """Nodes with different labels at same position are not duplicates."""
        mock_tool_context.state["graph"] = {
            "nodes": [
                {"id": "n1", "label": "+3V3", "bounding_box": [100, 200, 110, 210]}
            ],
            "edges": [],
        }
        ops = [
            {
                "op": "add_node",
                "data": {
                    "id": "n2",
                    "label": "+5V0",
                    "bounding_box": [100, 200, 110, 210],
                },
            }
        ]
        result = await update_graph(ops, mock_tool_context)
        assert "+ node 'n2'" in result
        assert len(mock_tool_context.state["graph"]["nodes"]) == 2

    @pytest.mark.asyncio
    async def test_add_node_no_bbox_skips_dedup_check(self, mock_tool_context):
        """Nodes without bounding_box bypass the label+bbox dedup check."""
        mock_tool_context.state["graph"] = {
            "nodes": [{"id": "n1", "label": "GND"}],
            "edges": [],
        }
        ops = [{"op": "add_node", "data": {"id": "n2", "label": "GND"}}]
        result = await update_graph(ops, mock_tool_context)
        assert "+ node 'n2'" in result
        assert len(mock_tool_context.state["graph"]["nodes"]) == 2

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

    @pytest.mark.asyncio
    async def test_add_node_with_inverted_bbox_auto_corrected(self, mock_tool_context):
        """Inverted bounding box should be auto-corrected at storage."""
        mock_tool_context.state["graph"] = {"nodes": [], "edges": []}
        ops = [
            {
                "op": "add_node",
                "data": {
                    "id": "n1",
                    "label": "Inverted",
                    "bounding_box": {"top": 500, "left": 400, "bottom": 100, "right": 200},
                },
            }
        ]
        result = await update_graph(ops, mock_tool_context)
        assert "+ node 'n1'" in result
        node = mock_tool_context.state["graph"]["nodes"][0]
        assert node["bounding_box"] == [100, 200, 500, 400]


class TestUpdateGraphBboxCorrections:
    """Test bbox_corrections state tracking."""

    @pytest.mark.asyncio
    async def test_inverted_bbox_tracked_in_state(self, mock_tool_context):
        """Adding a node with inverted bbox should populate bbox_corrections state."""
        mock_tool_context.state["graph"] = {"nodes": [], "edges": []}
        ops = [
            {
                "op": "add_node",
                "data": {
                    "id": "n1",
                    "label": "Inverted",
                    "bounding_box": {"top": 500, "left": 400, "bottom": 100, "right": 200},
                },
            }
        ]
        await update_graph(ops, mock_tool_context)
        corrections = mock_tool_context.state.get("bbox_corrections", [])
        assert len(corrections) == 1
        entry = corrections[0]
        assert entry["node_id"] == "n1"
        assert entry["op"] == "add_node"
        assert entry["raw"] == [500, 400, 100, 200]
        assert entry["corrected"] == [100, 200, 500, 400]
        assert entry["y_inverted"] is True
        assert entry["x_inverted"] is True

    @pytest.mark.asyncio
    async def test_valid_bbox_no_correction_tracked(self, mock_tool_context):
        """A valid bbox should NOT create any bbox_corrections entry."""
        mock_tool_context.state["graph"] = {"nodes": [], "edges": []}
        ops = [
            {
                "op": "add_node",
                "data": {
                    "id": "n1",
                    "label": "Valid",
                    "bounding_box": {"top": 10, "left": 20, "bottom": 100, "right": 200},
                },
            }
        ]
        await update_graph(ops, mock_tool_context)
        assert "bbox_corrections" not in mock_tool_context.state

    @pytest.mark.asyncio
    async def test_update_node_bbox_tracked(self, mock_tool_context):
        """Updating a node with inverted bbox should track correction."""
        mock_tool_context.state["graph"] = {
            "nodes": [{"id": "n1", "label": "Existing", "bounding_box": [10, 20, 100, 200]}],
            "edges": [],
        }
        ops = [
            {
                "op": "update_node",
                "data": {
                    "id": "n1",
                    "bounding_box": {"top": 300, "left": 20, "bottom": 50, "right": 200},
                },
            }
        ]
        await update_graph(ops, mock_tool_context)
        corrections = mock_tool_context.state.get("bbox_corrections", [])
        assert len(corrections) == 1
        assert corrections[0]["op"] == "update_node"
        assert corrections[0]["y_inverted"] is True


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

    @pytest.mark.asyncio
    async def test_add_edge_duplicate_pair_skipped(self, mock_tool_context):
        """Edge with same (source, target) as existing edge is skipped."""
        mock_tool_context.state["graph"] = {
            "nodes": [{"id": "n1"}, {"id": "n2"}],
            "edges": [{"id": "e1", "source": "n1", "target": "n2", "label": "first"}],
        }
        ops = [{"op": "add_edge", "data": {"id": "e2", "source": "n1", "target": "n2"}}]
        result = await update_graph(ops, mock_tool_context)
        assert "Skipped" in result
        assert "duplicate connection" in result
        assert len(mock_tool_context.state["graph"]["edges"]) == 1

    @pytest.mark.asyncio
    async def test_add_edge_reverse_direction_not_duplicate(self, mock_tool_context):
        """Edge with reversed (target, source) is NOT a duplicate — direction matters."""
        mock_tool_context.state["graph"] = {
            "nodes": [{"id": "n1"}, {"id": "n2"}],
            "edges": [{"id": "e1", "source": "n1", "target": "n2"}],
        }
        ops = [{"op": "add_edge", "data": {"id": "e2", "source": "n2", "target": "n1"}}]
        result = await update_graph(ops, mock_tool_context)
        assert "+ edge 'e2'" in result
        assert len(mock_tool_context.state["graph"]["edges"]) == 2

    @pytest.mark.asyncio
    async def test_add_edge_same_nodes_different_target_allowed(self, mock_tool_context):
        """Same source but different target is not a duplicate."""
        mock_tool_context.state["graph"] = {
            "nodes": [{"id": "n1"}, {"id": "n2"}, {"id": "n3"}],
            "edges": [{"id": "e1", "source": "n1", "target": "n2"}],
        }
        ops = [{"op": "add_edge", "data": {"id": "e2", "source": "n1", "target": "n3"}}]
        result = await update_graph(ops, mock_tool_context)
        assert "+ edge 'e2'" in result
        assert len(mock_tool_context.state["graph"]["edges"]) == 2


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


class TestUpdateGraphSetMetadata:
    """Test set_metadata operations."""

    @pytest.mark.asyncio
    async def test_set_metadata_legend(self, mock_tool_context):
        mock_tool_context.state["graph"] = {"nodes": [], "edges": []}
        legend = [
            {"symbol": "dashed line", "meaning": "optional dependency"},
            {"symbol": "red fill", "meaning": "critical path"},
        ]
        ops = [{"op": "set_metadata", "data": {"key": "legend", "value": legend}}]
        result = await update_graph(ops, mock_tool_context)
        assert "metadata['legend'] set" in result
        assert mock_tool_context.state["graph"]["metadata"]["legend"] == legend

    @pytest.mark.asyncio
    async def test_set_metadata_page_info(self, mock_tool_context):
        mock_tool_context.state["graph"] = {"nodes": [], "edges": []}
        page_info = {
            "title": "Data Pipeline v2.1",
            "author": "Jane Doe",
            "date": "2025-03-15",
            "version": "2.1",
        }
        ops = [{"op": "set_metadata", "data": {"key": "page_info", "value": page_info}}]
        result = await update_graph(ops, mock_tool_context)
        assert "metadata['page_info'] set" in result
        assert mock_tool_context.state["graph"]["metadata"]["page_info"] == page_info

    @pytest.mark.asyncio
    async def test_set_metadata_missing_key(self, mock_tool_context):
        mock_tool_context.state["graph"] = {"nodes": [], "edges": []}
        ops = [{"op": "set_metadata", "data": {"value": "something"}}]
        result = await update_graph(ops, mock_tool_context)
        assert "'key' required" in result

    @pytest.mark.asyncio
    async def test_set_metadata_preserves_existing(self, mock_tool_context):
        mock_tool_context.state["graph"] = {
            "nodes": [],
            "edges": [],
            "metadata": {"existing_key": "existing_value"},
        }
        ops = [{"op": "set_metadata", "data": {"key": "new_key", "value": "new_value"}}]
        await update_graph(ops, mock_tool_context)
        metadata = mock_tool_context.state["graph"]["metadata"]
        assert metadata["existing_key"] == "existing_value"
        assert metadata["new_key"] == "new_value"
