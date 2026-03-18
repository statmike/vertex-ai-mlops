"""Tests for flow detection in validate_graph."""

import pytest

from agent_image_to_graph.tools.function_tool_validate_graph import (
    _compute_flows,
    validate_graph,
)


class TestComputeFlows:
    """Unit tests for _compute_flows helper."""

    def test_single_flow_all_connected(self):
        nodes = [
            {"id": "n1", "label": "A"},
            {"id": "n2", "label": "B"},
            {"id": "n3", "label": "C"},
        ]
        edges = [
            {"source": "n1", "target": "n2"},
            {"source": "n2", "target": "n3"},
        ]
        flows = _compute_flows(nodes, edges)
        assert len(flows) == 1
        assert sorted(flows[0]["node_ids"]) == ["n1", "n2", "n3"]

    def test_two_disconnected_flows(self):
        """Two components with ≥3 nodes each should produce 2 flows."""
        nodes = [
            {"id": "n1", "label": "A"},
            {"id": "n2", "label": "B"},
            {"id": "n3", "label": "C"},
            {"id": "n4", "label": "D"},
            {"id": "n5", "label": "E"},
            {"id": "n6", "label": "F"},
        ]
        edges = [
            {"source": "n1", "target": "n2"},
            {"source": "n2", "target": "n3"},
            {"source": "n4", "target": "n5"},
            {"source": "n5", "target": "n6"},
        ]
        flows = _compute_flows(nodes, edges)
        assert len(flows) == 2
        flow_ids = {f["id"] for f in flows}
        assert flow_ids == {"flow_1", "flow_2"}

    def test_small_component_merged_into_largest(self):
        """Components with < min_component_size nodes get merged into largest."""
        nodes = [
            {"id": "n1", "label": "A"},
            {"id": "n2", "label": "B"},
            {"id": "n3", "label": "C"},
            {"id": "n4", "label": "D"},  # disconnected singleton
        ]
        edges = [
            {"source": "n1", "target": "n2"},
            {"source": "n2", "target": "n3"},
        ]
        flows = _compute_flows(nodes, edges)
        # n4 is a singleton (< 3), so it gets merged → single flow
        assert len(flows) == 1
        assert sorted(flows[0]["node_ids"]) == ["n1", "n2", "n3", "n4"]

    def test_groups_unified_in_flow(self):
        nodes = [
            {"id": "g1", "label": "Group", "shape": "group_rectangle"},
            {"id": "n1", "label": "A", "parent_id": "g1"},
            {"id": "n2", "label": "B"},
        ]
        edges = []
        flows = _compute_flows(nodes, edges)
        # g1 and n1 should be in same flow due to parent_id
        for flow in flows:
            if "n1" in flow["node_ids"]:
                assert "g1" in flow["node_ids"]
                break
        else:
            pytest.fail("n1 not found in any flow")

    def test_empty_nodes(self):
        flows = _compute_flows([], [])
        assert flows == []

    def test_single_node_no_edges(self):
        nodes = [{"id": "n1", "label": "Alone"}]
        flows = _compute_flows(nodes, [])
        assert len(flows) == 1
        assert flows[0]["node_ids"] == ["n1"]


class TestValidateGraphFlows:
    """Integration tests for flow detection in validate_graph."""

    @pytest.mark.asyncio
    async def test_single_flow_no_flows_array(self, mock_tool_context):
        """All connected nodes should NOT produce a flows array."""
        mock_tool_context.state["graph"] = {
            "diagram_type": "test",
            "nodes": [
                {"id": "n1", "label": "A"},
                {"id": "n2", "label": "B"},
            ],
            "edges": [{"id": "e1", "source": "n1", "target": "n2"}],
        }
        await validate_graph(mock_tool_context)
        assert "flows" not in mock_tool_context.state["graph"]

    @pytest.mark.asyncio
    async def test_two_flows_detected(self, mock_tool_context):
        """Two disconnected components (≥3 nodes each) should produce flows array."""
        mock_tool_context.state["graph"] = {
            "diagram_type": "test",
            "nodes": [
                {"id": "n1", "label": "A"},
                {"id": "n2", "label": "B"},
                {"id": "n3", "label": "C"},
                {"id": "n4", "label": "D"},
                {"id": "n5", "label": "E"},
                {"id": "n6", "label": "F"},
            ],
            "edges": [
                {"id": "e1", "source": "n1", "target": "n2"},
                {"id": "e2", "source": "n2", "target": "n3"},
                {"id": "e3", "source": "n4", "target": "n5"},
                {"id": "e4", "source": "n5", "target": "n6"},
            ],
        }
        result = await validate_graph(mock_tool_context)
        graph = mock_tool_context.state["graph"]
        assert "flows" in graph
        assert len(graph["flows"]) == 2
        assert "2 distinct flows" in result

    @pytest.mark.asyncio
    async def test_flow_ids_assigned_to_nodes(self, mock_tool_context):
        """Each node should get a flow_id when multi-flow is detected."""
        mock_tool_context.state["graph"] = {
            "diagram_type": "test",
            "nodes": [
                {"id": "n1", "label": "A"},
                {"id": "n2", "label": "B"},
                {"id": "n3", "label": "C"},
                {"id": "n4", "label": "D"},
                {"id": "n5", "label": "E"},
                {"id": "n6", "label": "F"},
            ],
            "edges": [
                {"id": "e1", "source": "n1", "target": "n2"},
                {"id": "e2", "source": "n2", "target": "n3"},
                {"id": "e3", "source": "n4", "target": "n5"},
                {"id": "e4", "source": "n5", "target": "n6"},
            ],
        }
        await validate_graph(mock_tool_context)
        nodes = mock_tool_context.state["graph"]["nodes"]
        flow_ids = {n.get("flow_id") for n in nodes}
        assert len(flow_ids) == 2

    @pytest.mark.asyncio
    async def test_small_components_merged_no_multiflow(self, mock_tool_context):
        """Small disconnected components (<3 nodes) should NOT trigger multi-flow."""
        mock_tool_context.state["graph"] = {
            "diagram_type": "test",
            "nodes": [
                {"id": "n1", "label": "A"},
                {"id": "n2", "label": "B"},
                {"id": "n3", "label": "C"},
                {"id": "n4", "label": "D"},  # disconnected singleton
            ],
            "edges": [
                {"id": "e1", "source": "n1", "target": "n2"},
                {"id": "e2", "source": "n2", "target": "n3"},
            ],
        }
        result = await validate_graph(mock_tool_context)
        assert "distinct flows" not in result
        # Should fall through to disconnected node check
        assert "Disconnected" in result

    @pytest.mark.asyncio
    async def test_cross_reference_detection(self, mock_tool_context):
        """Same label in different flows should suggest cross-reference."""
        mock_tool_context.state["graph"] = {
            "diagram_type": "test",
            "nodes": [
                {"id": "n1", "label": "Process A"},
                {"id": "n2", "label": "Step 1"},
                {"id": "n3", "label": "Output"},
                {"id": "n4", "label": "Process A"},
                {"id": "n5", "label": "Step 2"},
                {"id": "n6", "label": "Result"},
            ],
            "edges": [
                {"id": "e1", "source": "n1", "target": "n2"},
                {"id": "e2", "source": "n2", "target": "n3"},
                {"id": "e3", "source": "n4", "target": "n5"},
                {"id": "e4", "source": "n5", "target": "n6"},
            ],
        }
        result = await validate_graph(mock_tool_context)
        assert "Cross-reference candidate" in result
        assert "Process A" in result

    @pytest.mark.asyncio
    async def test_groups_same_flow(self, mock_tool_context):
        """Nodes with parent_id should be in the same flow as their parent."""
        mock_tool_context.state["graph"] = {
            "diagram_type": "test",
            "nodes": [
                {"id": "g1", "label": "Group", "shape": "group_rectangle"},
                {"id": "n1", "label": "Child A", "parent_id": "g1",
                 "bounding_box": [100, 100, 200, 200]},
                {"id": "n2", "label": "Child B", "parent_id": "g1",
                 "bounding_box": [200, 100, 300, 200]},
                {"id": "n3", "label": "Child C", "parent_id": "g1",
                 "bounding_box": [300, 100, 400, 200]},
                {"id": "n4", "label": "Other A"},
                {"id": "n5", "label": "Other B"},
                {"id": "n6", "label": "Other C"},
            ],
            "edges": [
                {"id": "e1", "source": "n4", "target": "n5"},
                {"id": "e2", "source": "n5", "target": "n6"},
            ],
        }
        await validate_graph(mock_tool_context)
        graph = mock_tool_context.state["graph"]
        nodes_by_id = {n["id"]: n for n in graph["nodes"]}
        # g1 and all its children should share the same flow_id
        assert nodes_by_id["g1"].get("flow_id") == nodes_by_id["n1"].get("flow_id")
        assert nodes_by_id["g1"].get("flow_id") == nodes_by_id["n2"].get("flow_id")
        # Other group should be in a different flow
        assert nodes_by_id["n4"].get("flow_id") != nodes_by_id["g1"].get("flow_id")
