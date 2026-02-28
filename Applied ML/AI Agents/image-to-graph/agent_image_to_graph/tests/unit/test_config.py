"""Tests for config constants and validation."""

from agent_image_to_graph.config import (
    ALLOWED_IMAGE_FORMATS,
    MAX_IMAGE_SIZE_BYTES,
    MAX_SCHEMA_SIZE_BYTES,
    PIL_MAX_IMAGE_PIXELS,
    TOOL_MODEL,
)


class TestConfigDefaults:
    """Verify config constants have sensible defaults."""

    def test_max_image_size(self):
        assert MAX_IMAGE_SIZE_BYTES == 50 * 1024 * 1024

    def test_max_schema_size(self):
        assert MAX_SCHEMA_SIZE_BYTES == 10 * 1024 * 1024

    def test_pil_max_pixels(self):
        assert PIL_MAX_IMAGE_PIXELS == 200_000_000

    def test_allowed_formats(self):
        assert "PNG" in ALLOWED_IMAGE_FORMATS
        assert "JPEG" in ALLOWED_IMAGE_FORMATS
        assert "GIF" in ALLOWED_IMAGE_FORMATS
        assert "BMP" in ALLOWED_IMAGE_FORMATS
        assert "TIFF" in ALLOWED_IMAGE_FORMATS
        assert "WEBP" in ALLOWED_IMAGE_FORMATS

    def test_tool_model_has_default(self):
        assert isinstance(TOOL_MODEL, str)
        assert len(TOOL_MODEL) > 0
