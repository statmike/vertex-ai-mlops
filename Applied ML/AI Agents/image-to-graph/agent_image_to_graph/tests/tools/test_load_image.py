"""Tests for function_tool_load_image."""

import io
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

from agent_image_to_graph.tools.function_tool_load_image import load_image


def _make_png_bytes(width=100, height=100, color="red"):
    """Create minimal PNG bytes for testing."""
    img = Image.new("RGB", (width, height), color=color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _make_pdf_bytes(num_pages=1):
    """Create a minimal PDF with the given number of pages using PyMuPDF."""
    import pymupdf

    doc = pymupdf.open()
    for i in range(num_pages):
        page = doc.new_page(width=612, height=792)
        text_point = pymupdf.Point(72, 72)
        page.insert_text(text_point, f"Page {i + 1}")
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


class TestLoadImage:
    """Test load_image tool with mocked ToolContext."""

    @pytest.mark.asyncio
    async def test_valid_image(self, mock_tool_context, temp_test_image):
        result = await load_image(temp_test_image, tool_context=mock_tool_context)
        assert "Image loaded successfully" in result
        assert "100 x 100" in result
        assert "PNG" in result
        assert mock_tool_context.state["source_image"] is not None
        assert mock_tool_context.state["image_dimensions"] == {"width": 100, "height": 100}
        assert mock_tool_context.state["graph"]["nodes"] == []

    @pytest.mark.asyncio
    async def test_missing_file(self, mock_tool_context):
        result = await load_image("/nonexistent/path.png", tool_context=mock_tool_context)
        assert "Error: File not found" in result

    @pytest.mark.asyncio
    async def test_oversized_file(self, mock_tool_context, temp_oversized_file):
        result = await load_image(temp_oversized_file, tool_context=mock_tool_context)
        assert "too large" in result

    @pytest.mark.asyncio
    async def test_unsupported_format(self, mock_tool_context, tmp_path):
        """Create a file that PIL can open but isn't in the whitelist."""
        # Write a PPM file (not in ALLOWED_IMAGE_FORMATS)
        ppm_path = tmp_path / "test.ppm"
        # P6 PPM: minimal valid file
        ppm_path.write_bytes(b"P6\n2 2\n255\n" + b"\xff\x00\x00" * 4)
        result = await load_image(str(ppm_path), tool_context=mock_tool_context)
        assert "Unsupported image format" in result


class TestLoadImageURL:
    """Test URL-based loading."""

    @pytest.mark.asyncio
    async def test_url_loading(self, mock_tool_context):
        png_bytes = _make_png_bytes(200, 150)
        mock_resp = MagicMock()
        mock_resp.read.return_value = png_bytes
        mock_resp.headers = {"Content-Length": str(len(png_bytes))}
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_resp):
            result = await load_image(
                "https://example.com/diagram.png", tool_context=mock_tool_context
            )

        assert "Image loaded successfully" in result
        assert "200 x 150" in result
        assert mock_tool_context.state["source_image"] is not None
        assert mock_tool_context.state["graph"]["metadata"]["source_file"] == (
            "https://example.com/diagram.png"
        )

    @pytest.mark.asyncio
    async def test_url_too_large(self, mock_tool_context):
        mock_resp = MagicMock()
        mock_resp.headers = {"Content-Length": str(100 * 1024 * 1024)}  # 100 MB
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_resp):
            result = await load_image(
                "https://example.com/huge.png", tool_context=mock_tool_context
            )

        assert "too large" in result

    @pytest.mark.asyncio
    async def test_invalid_url(self, mock_tool_context):
        import urllib.error

        with patch(
            "urllib.request.urlopen",
            side_effect=urllib.error.URLError("Connection refused"),
        ):
            result = await load_image(
                "https://badhost.example.com/img.png", tool_context=mock_tool_context
            )

        assert "Error" in result
        assert "Could not download" in result


class TestLoadImageGCS:
    """Test GCS-based loading."""

    @pytest.mark.asyncio
    async def test_gcs_loading(self, mock_tool_context):
        png_bytes = _make_png_bytes(300, 250)

        mock_blob = MagicMock()
        mock_blob.size = len(png_bytes)
        mock_blob.download_as_bytes.return_value = png_bytes

        mock_bucket = MagicMock()
        mock_bucket.blob.return_value = mock_blob

        mock_client = MagicMock()
        mock_client.bucket.return_value = mock_bucket

        with patch("google.cloud.storage.Client", return_value=mock_client):
            result = await load_image(
                "gs://my-bucket/path/to/diagram.png", tool_context=mock_tool_context
            )

        assert "Image loaded successfully" in result
        assert "300 x 250" in result
        mock_client.bucket.assert_called_once_with("my-bucket")
        mock_bucket.blob.assert_called_once_with("path/to/diagram.png")


class TestLoadImagePDF:
    """Test PDF loading and rendering."""

    @pytest.mark.asyncio
    async def test_pdf_local(self, mock_tool_context, tmp_path):
        pdf_bytes = _make_pdf_bytes(1)
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(pdf_bytes)

        result = await load_image(str(pdf_path), tool_context=mock_tool_context)

        assert "Image loaded successfully" in result
        assert "PDF page: 1" in result
        assert "PNG" in result
        assert mock_tool_context.state["image_format"] == "PNG"
        assert mock_tool_context.state["graph"]["metadata"]["source_page"] == 1

    @pytest.mark.asyncio
    async def test_pdf_page_parameter(self, mock_tool_context, tmp_path):
        pdf_bytes = _make_pdf_bytes(3)
        pdf_path = tmp_path / "multi.pdf"
        pdf_path.write_bytes(pdf_bytes)

        result = await load_image(str(pdf_path), page=2, tool_context=mock_tool_context)

        assert "Image loaded successfully" in result
        assert "PDF page: 2" in result
        assert mock_tool_context.state["graph"]["metadata"]["source_page"] == 2

    @pytest.mark.asyncio
    async def test_pdf_invalid_page(self, mock_tool_context, tmp_path):
        pdf_bytes = _make_pdf_bytes(1)
        pdf_path = tmp_path / "single.pdf"
        pdf_path.write_bytes(pdf_bytes)

        result = await load_image(str(pdf_path), page=99, tool_context=mock_tool_context)

        assert "out of range" in result
        assert "1 page(s)" in result

    @pytest.mark.asyncio
    async def test_pdf_from_url(self, mock_tool_context):
        pdf_bytes = _make_pdf_bytes(1)
        mock_resp = MagicMock()
        mock_resp.read.return_value = pdf_bytes
        mock_resp.headers = {"Content-Length": str(len(pdf_bytes))}
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_resp):
            result = await load_image(
                "https://example.com/report.pdf", tool_context=mock_tool_context
            )

        assert "Image loaded successfully" in result
        assert "PDF page: 1" in result
        assert mock_tool_context.state["image_format"] == "PNG"
