"""Tests for function_tool_report_results."""

import pytest

from agent_cv_preprocess.tools.function_tool_report_results import report_results


class TestReportResults:
    """Test report_results tool."""

    @pytest.mark.asyncio
    async def test_report_skipped(self, mock_tool_context):
        result = await report_results("skipped", "Image not suitable for CV", mock_tool_context)
        assert "status: skipped" in result
        cv = mock_tool_context.state.get("cv_preprocessing")
        assert cv is not None
        assert cv["status"] == "skipped"
        assert cv["confidence"] == 0.0

    @pytest.mark.asyncio
    async def test_report_complete_with_elements(self, mock_tool_context):
        mock_tool_context.state["cv_elements"] = [
            {"id": "cv_1", "bounding_box": [100, 200, 300, 400], "shape": "rectangle", "text": "A"},
            {"id": "cv_2", "bounding_box": [500, 200, 700, 400], "shape": "circle", "text": "B"},
        ]
        mock_tool_context.state["cv_connections"] = [
            {"id": "cv_conn_1", "source_element_id": "cv_1", "target_element_id": "cv_2",
             "line_type": "arrow", "confidence": 0.9},
        ]
        mock_tool_context.state["cv_detect_params"] = {"min_contour_area": 500}

        result = await report_results("complete", "Found 2 elements and 1 connection", mock_tool_context)
        assert "status: complete" in result
        cv = mock_tool_context.state.get("cv_preprocessing")
        assert cv["status"] == "complete"
        assert len(cv["elements"]) == 2
        assert len(cv["connections"]) == 1
        assert cv["confidence"] > 0

    @pytest.mark.asyncio
    async def test_report_cleans_intermediate_state(self, mock_tool_context):
        mock_tool_context.state["cv_elements"] = []
        mock_tool_context.state["cv_connections"] = []
        mock_tool_context.state["cv_detect_stats"] = {"total": 10}
        mock_tool_context.state["cv_detect_params"] = {}
        mock_tool_context.state["cv_assessment"] = {"suitability": "high"}

        await report_results("partial", "Partial results", mock_tool_context)

        # Intermediate keys should be cleaned up
        assert "cv_elements" not in mock_tool_context.state
        assert "cv_connections" not in mock_tool_context.state
        assert "cv_detect_stats" not in mock_tool_context.state
        assert "cv_detect_params" not in mock_tool_context.state
        assert "cv_assessment" not in mock_tool_context.state
        # Final result should be present
        assert "cv_preprocessing" in mock_tool_context.state

    @pytest.mark.asyncio
    async def test_invalid_status(self, mock_tool_context):
        result = await report_results("invalid", "test", mock_tool_context)
        assert "Error: status must be" in result

    @pytest.mark.asyncio
    async def test_report_partial(self, mock_tool_context):
        mock_tool_context.state["cv_elements"] = [
            {"id": "cv_1", "bounding_box": [100, 200, 300, 400], "shape": "rectangle"},
        ]
        mock_tool_context.state["cv_connections"] = []
        await report_results("partial", "Elements found but no connections", mock_tool_context)
        cv = mock_tool_context.state["cv_preprocessing"]
        assert cv["status"] == "partial"
        assert len(cv["elements"]) == 1
        assert len(cv["connections"]) == 0
