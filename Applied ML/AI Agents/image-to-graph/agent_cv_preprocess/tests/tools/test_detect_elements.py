"""Tests for function_tool_detect_elements."""

import pytest

from agent_cv_preprocess.tools.function_tool_detect_elements import (
    _classify_shape,
    detect_elements,
)


class TestClassifyShape:
    """Test shape classification helper."""

    def test_triangle(self):
        assert _classify_shape(3) == "triangle"

    def test_rectangle(self):
        assert _classify_shape(4) == "rectangle"

    def test_pentagon(self):
        assert _classify_shape(5) == "pentagon"

    def test_hexagon(self):
        assert _classify_shape(6) == "hexagon"

    def test_circle(self):
        assert _classify_shape(8) == "circle"
        assert _classify_shape(12) == "circle"

    def test_unknown(self):
        assert _classify_shape(2) == "unknown"


class TestDetectElements:
    """Test detect_elements tool with synthetic images."""

    @pytest.mark.asyncio
    async def test_no_image_loaded(self, mock_tool_context):
        result = await detect_elements(tool_context=mock_tool_context)
        assert "Error: No source image loaded" in result

    @pytest.mark.asyncio
    async def test_flowchart_detects_elements(self, mock_tool_context, flowchart_state):
        mock_tool_context.state = flowchart_state
        result = await detect_elements(tool_context=mock_tool_context)
        assert "detection complete" in result.lower()
        elements = mock_tool_context.state.get("cv_elements", [])
        assert len(elements) >= 3  # Should find at least the 3 rectangles + diamond
        # Verify element structure
        for el in elements:
            assert "id" in el
            assert "bounding_box" in el
            assert "shape" in el
            assert "area" in el
            assert len(el["bounding_box"]) == 4

    @pytest.mark.asyncio
    async def test_stores_stats(self, mock_tool_context, flowchart_state):
        mock_tool_context.state = flowchart_state
        await detect_elements(tool_context=mock_tool_context)
        stats = mock_tool_context.state.get("cv_detect_stats")
        assert stats is not None
        assert "total_contours" in stats
        assert "filtered" in stats
        assert "elements_kept" in stats
        assert "shapes_found" in stats

    @pytest.mark.asyncio
    async def test_custom_params(self, mock_tool_context, flowchart_state):
        mock_tool_context.state = flowchart_state
        result = await detect_elements(
            binary_threshold="adaptive",
            min_contour_area=100,
            approx_epsilon=0.03,
            morphology_kernel=5,
            tool_context=mock_tool_context,
        )
        assert "detection complete" in result.lower()
        params = mock_tool_context.state.get("cv_detect_params")
        assert params["min_contour_area"] == 100
        assert params["approx_epsilon"] == 0.03
        assert params["morphology_kernel"] == 5

    @pytest.mark.asyncio
    async def test_high_min_area_filters_more(self, mock_tool_context, flowchart_state):
        mock_tool_context.state = flowchart_state.copy()
        await detect_elements(min_contour_area=100, tool_context=mock_tool_context)
        elements_low = len(mock_tool_context.state.get("cv_elements", []))

        mock_tool_context.state = flowchart_state.copy()
        await detect_elements(min_contour_area=5000, tool_context=mock_tool_context)
        elements_high = len(mock_tool_context.state.get("cv_elements", []))

        assert elements_low >= elements_high

    @pytest.mark.asyncio
    async def test_bounding_boxes_normalized(self, mock_tool_context, flowchart_state):
        mock_tool_context.state = flowchart_state
        await detect_elements(tool_context=mock_tool_context)
        elements = mock_tool_context.state.get("cv_elements", [])
        for el in elements:
            bbox = el["bounding_box"]
            for v in bbox:
                assert 0 <= v <= 1000, f"Bbox value {v} out of 0-1000 range"
            # y_min < y_max, x_min < x_max
            assert bbox[0] <= bbox[2], f"y_min ({bbox[0]}) > y_max ({bbox[2]})"
            assert bbox[1] <= bbox[3], f"x_min ({bbox[1]}) > x_max ({bbox[3]})"
