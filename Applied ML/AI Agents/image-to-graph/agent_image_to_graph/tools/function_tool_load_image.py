import base64
import io
import logging
import os
import urllib.error
import urllib.parse
import urllib.request

from google.adk import tools
from PIL import Image

from ..config import (
    ALLOWED_IMAGE_FORMATS,
    MAX_IMAGE_SIZE_BYTES,
    PDF_RENDER_DPI,
    PIL_MAX_IMAGE_PIXELS,
)
from .util_common import log_tool_error

logger = logging.getLogger(__name__)


def _fetch_from_url(url: str) -> tuple[bytes, str]:
    """Download bytes from an HTTP(S) URL.

    Returns (raw_bytes, filename). Raises on network errors or oversized responses.
    """
    req = urllib.request.Request(url, headers={"User-Agent": "image-to-graph-agent/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        content_length = resp.headers.get("Content-Length")
        if content_length and int(content_length) > MAX_IMAGE_SIZE_BYTES:
            size_mb = int(content_length) / (1024 * 1024)
            limit_mb = MAX_IMAGE_SIZE_BYTES / (1024 * 1024)
            raise ValueError(
                f"Remote file is too large ({size_mb:.1f} MB). "
                f"Maximum allowed size is {limit_mb:.0f} MB."
            )
        data = resp.read()
    if len(data) > MAX_IMAGE_SIZE_BYTES:
        size_mb = len(data) / (1024 * 1024)
        limit_mb = MAX_IMAGE_SIZE_BYTES / (1024 * 1024)
        raise ValueError(
            f"Downloaded file is too large ({size_mb:.1f} MB). "
            f"Maximum allowed size is {limit_mb:.0f} MB."
        )
    # Extract filename from URL path
    filename = os.path.basename(urllib.parse.urlparse(url).path) or "download"
    return data, filename


def _fetch_from_gcs(gs_path: str) -> tuple[bytes, str]:
    """Download bytes from a GCS path (gs://bucket/path).

    Returns (raw_bytes, filename). Raises on errors.
    """
    from google.cloud import storage

    if not gs_path.startswith("gs://"):
        raise ValueError(f"Invalid GCS path: {gs_path}")
    path_no_prefix = gs_path[5:]
    bucket_name, _, blob_name = path_no_prefix.partition("/")
    if not blob_name:
        raise ValueError(f"GCS path must include a blob name: {gs_path}")

    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)

    # Check size before downloading
    blob.reload()
    if blob.size and blob.size > MAX_IMAGE_SIZE_BYTES:
        size_mb = blob.size / (1024 * 1024)
        limit_mb = MAX_IMAGE_SIZE_BYTES / (1024 * 1024)
        raise ValueError(
            f"GCS file is too large ({size_mb:.1f} MB). "
            f"Maximum allowed size is {limit_mb:.0f} MB."
        )

    data = blob.download_as_bytes()
    filename = os.path.basename(blob_name)
    return data, filename


def _render_pdf_page(pdf_bytes: bytes, page: int, dpi: int) -> bytes:
    """Render a single page of a PDF to PNG bytes.

    Args:
        pdf_bytes: Raw PDF file content.
        page: 1-indexed page number.
        dpi: Resolution for rendering.

    Returns:
        PNG image bytes.
    """
    try:
        import pymupdf
    except ImportError:
        import fitz as pymupdf

    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    try:
        num_pages = len(doc)
        if page < 1 or page > num_pages:
            raise ValueError(
                f"Page {page} is out of range. PDF has {num_pages} page(s)."
            )
        pdf_page = doc[page - 1]
        zoom = dpi / 72
        mat = pymupdf.Matrix(zoom, zoom)
        pix = pdf_page.get_pixmap(matrix=mat)
        return pix.tobytes("png")
    finally:
        doc.close()


async def load_image(
    file_path: str,
    page: int = 1,
    tool_context: tools.ToolContext = None,
) -> str:
    """
    Load an image from a local path, URL, or GCS path and store it in state.

    Reads the image, validates it with Pillow, and stores the raw bytes
    and dimensions in tool_context.state for use by other tools (analyze, crop, etc.).
    Also initializes an empty graph structure in state.

    For PDF files, renders the specified page at high resolution to PNG.

    Args:
        file_path: Local path, URL (https://...), or GCS path (gs://...) to an image or PDF.
        page: 1-indexed page number for PDF files (default: 1). Ignored for images.
        tool_context: The ADK tool context for accessing shared state.

    Returns:
        A message confirming the image was loaded with its dimensions,
        or an error message if loading fails.
    """
    try:
        # --- Step 1: Fetch raw bytes based on source type ---
        is_pdf = False
        source_page = None

        if file_path.startswith(("http://", "https://")):
            try:
                image_bytes, filename = _fetch_from_url(file_path)
            except urllib.error.URLError as e:
                return f"Error: Could not download URL '{file_path}': {e.reason}"
            except ValueError as e:
                return f"Error: {e}"
        elif file_path.startswith("gs://"):
            try:
                image_bytes, filename = _fetch_from_gcs(file_path)
            except ValueError as e:
                return f"Error: {e}"
        else:
            # Local file path
            expanded_path = os.path.expanduser(file_path)
            if not os.path.exists(expanded_path):
                return f"Error: File not found at '{file_path}'."
            file_size = os.path.getsize(expanded_path)
            if file_size > MAX_IMAGE_SIZE_BYTES:
                size_mb = file_size / (1024 * 1024)
                limit_mb = MAX_IMAGE_SIZE_BYTES / (1024 * 1024)
                return (
                    f"Error: Image file is too large ({size_mb:.1f} MB). "
                    f"Maximum allowed size is {limit_mb:.0f} MB."
                )
            with open(expanded_path, "rb") as f:
                image_bytes = f.read()
            filename = os.path.basename(expanded_path)

        # --- Step 2: If PDF, render to PNG ---
        if filename.lower().endswith(".pdf"):
            is_pdf = True
            try:
                image_bytes = _render_pdf_page(image_bytes, page, PDF_RENDER_DPI)
                source_page = page
            except ValueError as e:
                return f"Error: {e}"

        # --- Step 3: Validate with Pillow ---
        Image.MAX_IMAGE_PIXELS = PIL_MAX_IMAGE_PIXELS

        img = Image.open(io.BytesIO(image_bytes))
        width, height = img.size
        image_format = img.format or "UNKNOWN"

        # PDF-rendered images are always PNG
        if is_pdf:
            image_format = "PNG"

        if image_format not in ALLOWED_IMAGE_FORMATS:
            return (
                f"Error: Unsupported image format '{image_format}'. "
                f"Allowed formats: {', '.join(sorted(ALLOWED_IMAGE_FORMATS))}."
            )

        # Determine MIME type
        mime_map = {
            "JPEG": "image/jpeg",
            "PNG": "image/png",
            "GIF": "image/gif",
            "BMP": "image/bmp",
            "TIFF": "image/tiff",
            "WEBP": "image/webp",
        }
        mime_type = mime_map.get(image_format, "image/png")

        # Store in state
        tool_context.state["source_image"] = base64.b64encode(image_bytes).decode("utf-8")
        tool_context.state["source_image_mime_type"] = mime_type
        tool_context.state["image_dimensions"] = {"width": width, "height": height}
        tool_context.state["image_format"] = image_format

        # Initialize empty graph state
        metadata = {
            "source_file": file_path,
            "image_width": width,
            "image_height": height,
        }
        if source_page is not None:
            metadata["source_page"] = source_page

        tool_context.state["graph"] = {
            "diagram_type": None,
            "nodes": [],
            "edges": [],
            "metadata": metadata,
        }
        tool_context.state["cropped_regions"] = {}
        tool_context.state["schema"] = None

        # Build result message
        lines = [
            "Image loaded successfully.",
            f"  File: {file_path}",
        ]
        if source_page is not None:
            lines.append(f"  PDF page: {source_page} (rendered at {PDF_RENDER_DPI} DPI)")
        lines.extend([
            f"  Format: {image_format}",
            f"  Dimensions: {width} x {height} pixels",
            f"  MIME type: {mime_type}",
            "Graph state initialized (empty). Ready for analysis.",
        ])
        return "\n".join(lines)

    except Exception as e:
        return log_tool_error("load_image", e)
