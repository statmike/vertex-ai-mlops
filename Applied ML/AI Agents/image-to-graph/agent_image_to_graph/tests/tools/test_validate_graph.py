"""Tests for function_tool_validate_graph."""

import pytest

from agent_image_to_graph.tools.function_tool_validate_graph import validate_graph


class TestValidateGraphStructural:
    """Structural validation tests."""

    @pytest.mark.asyncio
    async def test_valid_graph(self, mock_tool_context, sample_graph):
        mock_tool_context.state["graph"] = sample_graph
        result = await validate_graph(mock_tool_context)
        assert "PASSED" in result

    @pytest.mark.asyncio
    async def test_empty_graph(self, mock_tool_context):
        mock_tool_context.state["graph"] = {"nodes": [], "edges": []}
        result = await validate_graph(mock_tool_context)
        assert "empty" in result.lower()

    @pytest.mark.asyncio
    async def test_no_graph_state(self, mock_tool_context):
        result = await validate_graph(mock_tool_context)
        assert "Error" in result

    @pytest.mark.asyncio
    async def test_missing_node_id(self, mock_tool_context):
        mock_tool_context.state["graph"] = {
            "diagram_type": "test",
            "nodes": [{"label": "no id"}],
            "edges": [],
        }
        result = await validate_graph(mock_tool_context)
        assert "missing" in result.lower() and "id" in result.lower()

    @pytest.mark.asyncio
    async def test_duplicate_node_ids(self, mock_tool_context):
        mock_tool_context.state["graph"] = {
            "diagram_type": "test",
            "nodes": [
                {"id": "n1", "label": "A"},
                {"id": "n1", "label": "B"},
            ],
            "edges": [],
        }
        result = await validate_graph(mock_tool_context)
        assert "Duplicate" in result

    @pytest.mark.asyncio
    async def test_orphaned_edge(self, mock_tool_context):
        mock_tool_context.state["graph"] = {
            "diagram_type": "test",
            "nodes": [{"id": "n1", "label": "A"}],
            "edges": [{"id": "e1", "source": "n1", "target": "n_nonexistent"}],
        }
        result = await validate_graph(mock_tool_context)
        assert "non-existent" in result.lower()

    @pytest.mark.asyncio
    async def test_disconnected_nodes_warning(self, mock_tool_context):
        mock_tool_context.state["graph"] = {
            "diagram_type": "test",
            "nodes": [
                {"id": "n1", "label": "A"},
                {"id": "n2", "label": "B"},
                {"id": "n3", "label": "C"},
            ],
            "edges": [{"id": "e1", "source": "n1", "target": "n2"}],
        }
        result = await validate_graph(mock_tool_context)
        assert "Disconnected" in result

    @pytest.mark.asyncio
    async def test_self_loop_warning(self, mock_tool_context):
        mock_tool_context.state["graph"] = {
            "diagram_type": "test",
            "nodes": [{"id": "n1", "label": "A"}],
            "edges": [{"id": "e1", "source": "n1", "target": "n1"}],
        }
        result = await validate_graph(mock_tool_context)
        assert "self-loop" in result.lower()

    @pytest.mark.asyncio
    async def test_low_confidence_warning(self, mock_tool_context):
        mock_tool_context.state["graph"] = {
            "diagram_type": "test",
            "nodes": [{"id": "n1", "label": "A", "confidence": "low"}],
            "edges": [],
        }
        result = await validate_graph(mock_tool_context)
        assert "LOW confidence" in result


class TestValidateGraphGroups:
    """Group (parent_id) validation tests."""

    @pytest.mark.asyncio
    async def test_valid_parent_id(self, mock_tool_context):
        mock_tool_context.state["graph"] = {
            "diagram_type": "test",
            "nodes": [
                {"id": "g1", "label": "Group", "shape": "group_rectangle"},
                {
                    "id": "n1",
                    "label": "Child",
                    "parent_id": "g1",
                    "bounding_box": [100, 100, 200, 200],
                },
            ],
            "edges": [],
        }
        result = await validate_graph(mock_tool_context)
        # Should pass (no error about invalid parent_id)
        assert "PASSED" in result

    @pytest.mark.asyncio
    async def test_invalid_parent_id(self, mock_tool_context):
        mock_tool_context.state["graph"] = {
            "diagram_type": "test",
            "nodes": [
                {"id": "n1", "label": "Child", "parent_id": "nonexistent"},
            ],
            "edges": [],
        }
        result = await validate_graph(mock_tool_context)
        assert "does not exist" in result

    @pytest.mark.asyncio
    async def test_group_no_children_warning(self, mock_tool_context):
        mock_tool_context.state["graph"] = {
            "diagram_type": "test",
            "nodes": [
                {"id": "g1", "label": "Empty Group", "shape": "group_rectangle"},
            ],
            "edges": [],
        }
        result = await validate_graph(mock_tool_context)
        assert "no children" in result.lower()

    @pytest.mark.asyncio
    async def test_group_bbox_auto_computed(self, mock_tool_context):
        """Group bbox should be auto-computed from children."""
        mock_tool_context.state["graph"] = {
            "diagram_type": "test",
            "nodes": [
                {
                    "id": "g1",
                    "label": "Group",
                    "shape": "group_rectangle",
                    "bounding_box": [0, 0, 500, 500],
                },
                {"id": "n1", "label": "A", "parent_id": "g1", "bounding_box": [100, 100, 200, 200]},
                {"id": "n2", "label": "B", "parent_id": "g1", "bounding_box": [300, 300, 400, 400]},
            ],
            "edges": [],
        }
        await validate_graph(mock_tool_context)
        # Group bbox should be recomputed from children + padding
        group = mock_tool_context.state["graph"]["nodes"][0]
        assert group["bounding_box"] == [80, 80, 420, 420]


class TestValidateGraphSchema:
    """Schema conformance validation."""

    @pytest.mark.asyncio
    async def test_schema_conformance_check(self, mock_tool_context, sample_schema):
        mock_tool_context.state["graph"] = {
            "diagram_type": "test",
            "nodes": [{"id": "n1"}],  # missing label (required)
            "edges": [],
        }
        mock_tool_context.state["input_schema"] = sample_schema
        result = await validate_graph(mock_tool_context)
        assert "label" in result
