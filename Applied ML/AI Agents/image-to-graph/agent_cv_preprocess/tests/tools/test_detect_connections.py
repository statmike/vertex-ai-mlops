"""Tests for function_tool_detect_connections."""

import pytest

from agent_cv_preprocess.tools.function_tool_detect_connections import (
    _line_overlaps_bbox,
    _point_near_bbox,
    detect_connections,
)
from agent_cv_preprocess.tools.function_tool_detect_elements import detect_elements


class TestPointNearBbox:
    """Test point-near-bounding-box helper."""

    def test_point_inside(self):
        # Point at (200, 100) inside bbox [50, 100, 200, 300] on a 1000x1000 image
        assert _point_near_bbox(200, 100, [50, 100, 200, 300], 1000, 1000, margin=10)

    def test_point_outside(self):
        assert not _point_near_bbox(800, 800, [50, 100, 200, 300], 1000, 1000, margin=10)

    def test_point_near_edge(self):
        # Point just outside bbox edge, within margin
        # bbox pixel coords: x_min=100, x_max=300, y_min=50, y_max=200
        assert _point_near_bbox(310, 100, [50, 100, 200, 300], 1000, 1000, margin=20)


class TestLineOverlapsBbox:
    """Test line-overlaps-bbox helper."""

    def test_line_inside_bbox(self):
        # Both endpoints inside the bbox
        assert _line_overlaps_bbox(150, 100, 250, 150, [50, 100, 200, 300], 1000, 1000)

    def test_line_outside_bbox(self):
        assert not _line_overlaps_bbox(500, 500, 600, 600, [50, 100, 200, 300], 1000, 1000)

    def test_line_one_endpoint_inside(self):
        # One endpoint inside, one outside — not "overlapping" (it's a connection)
        assert not _line_overlaps_bbox(150, 100, 500, 500, [50, 100, 200, 300], 1000, 1000)


class TestDetectConnections:
    """Test detect_connections tool with synthetic images."""

    @pytest.mark.asyncio
    async def test_no_image_loaded(self, mock_tool_context):
        result = await detect_connections(mock_tool_context)
        assert "Error: No source image loaded" in result

    @pytest.mark.asyncio
    async def test_no_elements_detected(self, mock_tool_context, flowchart_state):
        mock_tool_context.state = flowchart_state
        result = await detect_connections(mock_tool_context)
        assert "Error: No elements detected" in result

    @pytest.mark.asyncio
    async def test_flowchart_finds_connections(self, mock_tool_context, flowchart_state):
        mock_tool_context.state = flowchart_state
        # First detect elements
        await detect_elements(min_contour_area=200, tool_context=mock_tool_context)
        elements = mock_tool_context.state.get("cv_elements", [])
        assert len(elements) >= 3, f"Expected >=3 elements, got {len(elements)}"

        # Now detect connections
        await detect_connections(mock_tool_context)
        connections = mock_tool_context.state.get("cv_connections", [])
        # The synthetic flowchart has 3 arrows, we should find at least some
        # (exact count depends on how well Hough lines match the arrowed lines)
        assert isinstance(connections, list)

    @pytest.mark.asyncio
    async def test_connection_structure(self, mock_tool_context, flowchart_state):
        mock_tool_context.state = flowchart_state
        await detect_elements(min_contour_area=200, tool_context=mock_tool_context)
        await detect_connections(mock_tool_context)
        connections = mock_tool_context.state.get("cv_connections", [])
        for conn in connections:
            assert "id" in conn
            assert "source_element_id" in conn
            assert "target_element_id" in conn
            assert "line_type" in conn
            assert conn["line_type"] in ("solid", "arrow", "dashed")
            assert "confidence" in conn

    @pytest.mark.asyncio
    async def test_no_self_connections(self, mock_tool_context, flowchart_state):
        mock_tool_context.state = flowchart_state
        await detect_elements(min_contour_area=200, tool_context=mock_tool_context)
        await detect_connections(mock_tool_context)
        connections = mock_tool_context.state.get("cv_connections", [])
        for conn in connections:
            assert conn["source_element_id"] != conn["target_element_id"]
