"""Centralized configuration constants for the image-to-graph agent.

File size limits, image format whitelist, and model settings are all
configured here. Defaults can be overridden via environment variables.
"""

import os

# --- File size limits ---
MAX_IMAGE_SIZE_BYTES = int(os.getenv("MAX_IMAGE_SIZE_BYTES", 50 * 1024 * 1024))  # 50 MB
MAX_SCHEMA_SIZE_BYTES = int(os.getenv("MAX_SCHEMA_SIZE_BYTES", 10 * 1024 * 1024))  # 10 MB

# --- Image safety ---
PIL_MAX_IMAGE_PIXELS = int(os.getenv("PIL_MAX_IMAGE_PIXELS", 200_000_000))  # 200 MP

# --- Allowed image formats (PIL format names) ---
ALLOWED_IMAGE_FORMATS = {"JPEG", "PNG", "GIF", "BMP", "TIFF", "WEBP"}

# --- PDF rendering ---
PDF_RENDER_DPI = int(os.getenv("PDF_RENDER_DPI", 300))

# --- Model configuration (used by gemini_utils.py) ---
TOOL_MODEL = os.getenv("TOOL_MODEL", "gemini-2.5-flash")
TOOL_MODEL_LOCATION = os.getenv("TOOL_MODEL_LOCATION", "")

# --- Diagram-type-specific thresholds ---
# Keyed by diagram type category. "default" is used for unrecognised types.
DIAGRAM_TYPE_CONFIG: dict[str, dict] = {
    "schematic": {
        "oversized_bbox_threshold": 0.05,  # 5% of image area
    },
    "default": {
        "oversized_bbox_threshold": 0.10,  # 10% of image area
    },
}
