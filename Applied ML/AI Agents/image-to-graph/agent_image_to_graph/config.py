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

# --- Model configuration (used by gemini_utils.py) ---
TOOL_MODEL = os.getenv("TOOL_MODEL", "gemini-2.5-flash")
TOOL_MODEL_LOCATION = os.getenv("TOOL_MODEL_LOCATION", "")
