"""Tests for function_tool_assess_image."""

import pytest

from agent_cv_preprocess.tools.function_tool_assess_image import assess_image


class TestAssessImage:
    """Test assess_image tool with synthetic images."""

    @pytest.mark.asyncio
    async def test_no_image_loaded(self, mock_tool_context):
        result = await assess_image(mock_tool_context)
        assert "Error: No source image loaded" in result

    @pytest.mark.asyncio
    async def test_flowchart_suitable(self, mock_tool_context, flowchart_state):
        mock_tool_context.state = flowchart_state
        result = await assess_image(mock_tool_context)
        assert "assessment complete" in result.lower()
        assert mock_tool_context.state.get("cv_assessment") is not None
        assessment = mock_tool_context.state["cv_assessment"]
        assert assessment["suitability"] in ("high", "medium")
        assert "recommended_params" in assessment

    @pytest.mark.asyncio
    async def test_noisy_photo_low_suitability(self, mock_tool_context, noisy_photo_b64):
        mock_tool_context.state = {
            "source_image": noisy_photo_b64,
            "source_image_mime_type": "image/png",
            "image_dimensions": {"width": 400, "height": 400},
        }
        result = await assess_image(mock_tool_context)
        assert "assessment complete" in result.lower()
        assessment = mock_tool_context.state["cv_assessment"]
        # Noisy random image should score low
        assert assessment["suitability"] in ("low", "medium")

    @pytest.mark.asyncio
    async def test_assessment_stores_metrics(self, mock_tool_context, flowchart_state):
        mock_tool_context.state = flowchart_state
        await assess_image(mock_tool_context)
        assessment = mock_tool_context.state["cv_assessment"]
        metrics = assessment["metrics"]
        assert "intensity_std" in metrics
        assert "edge_density" in metrics
        assert "laplacian_var" in metrics
        assert "significant_colors" in metrics
