import base64
import io
import logging
import os

from google.adk import tools
from PIL import Image

from ..config import ALLOWED_IMAGE_FORMATS, MAX_IMAGE_SIZE_BYTES, PIL_MAX_IMAGE_PIXELS
from .util_common import log_tool_error

logger = logging.getLogger(__name__)


async def load_image(file_path: str, tool_context: tools.ToolContext) -> str:
    """
    Load an image from a file path and store it in state for subsequent analysis.

    Reads the image file, validates it with Pillow, and stores the raw bytes
    and dimensions in tool_context.state for use by other tools (analyze, crop, etc.).
    Also initializes an empty graph structure in state.

    Args:
        file_path: The absolute or relative path to the image file to load.
        tool_context: The ADK tool context for accessing shared state.

    Returns:
        A message confirming the image was loaded with its dimensions,
        or an error message if loading fails.
    """
    try:
        expanded_path = os.path.expanduser(file_path)

        if not os.path.exists(expanded_path):
            return f"Error: File not found at '{file_path}'."

        # Check file size before reading
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

        # Set pixel limit before opening
        Image.MAX_IMAGE_PIXELS = PIL_MAX_IMAGE_PIXELS

        # Validate with Pillow and get dimensions
        img = Image.open(io.BytesIO(image_bytes))
        width, height = img.size
        image_format = img.format or "UNKNOWN"

        # Check format whitelist
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
        tool_context.state["graph"] = {
            "diagram_type": None,
            "nodes": [],
            "edges": [],
            "metadata": {
                "source_file": file_path,
                "image_width": width,
                "image_height": height,
            },
        }
        tool_context.state["cropped_regions"] = {}
        tool_context.state["schema"] = None

        return (
            f"Image loaded successfully.\n"
            f"  File: {file_path}\n"
            f"  Format: {image_format}\n"
            f"  Dimensions: {width} x {height} pixels\n"
            f"  MIME type: {mime_type}\n"
            f"Graph state initialized (empty). Ready for analysis."
        )

    except Exception as e:
        return log_tool_error("load_image", e)
