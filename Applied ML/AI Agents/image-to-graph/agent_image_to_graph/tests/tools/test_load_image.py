"""Tests for function_tool_load_image."""

import pytest

from agent_image_to_graph.tools.function_tool_load_image import load_image


class TestLoadImage:
    """Test load_image tool with mocked ToolContext."""

    @pytest.mark.asyncio
    async def test_valid_image(self, mock_tool_context, temp_test_image):
        result = await load_image(temp_test_image, mock_tool_context)
        assert "Image loaded successfully" in result
        assert "100 x 100" in result
        assert "PNG" in result
        assert mock_tool_context.state["source_image"] is not None
        assert mock_tool_context.state["image_dimensions"] == {"width": 100, "height": 100}
        assert mock_tool_context.state["graph"]["nodes"] == []

    @pytest.mark.asyncio
    async def test_missing_file(self, mock_tool_context):
        result = await load_image("/nonexistent/path.png", mock_tool_context)
        assert "Error: File not found" in result

    @pytest.mark.asyncio
    async def test_oversized_file(self, mock_tool_context, temp_oversized_file):
        result = await load_image(temp_oversized_file, mock_tool_context)
        assert "too large" in result

    @pytest.mark.asyncio
    async def test_unsupported_format(self, mock_tool_context, tmp_path):
        """Create a file that PIL can open but isn't in the whitelist."""
        # Write a PPM file (not in ALLOWED_IMAGE_FORMATS)
        ppm_path = tmp_path / "test.ppm"
        # P6 PPM: minimal valid file
        ppm_path.write_bytes(b"P6\n2 2\n255\n" + b"\xff\x00\x00" * 4)
        result = await load_image(str(ppm_path), mock_tool_context)
        assert "Unsupported image format" in result
