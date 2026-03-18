"""Shared fixtures for CV preprocessing tests."""

import base64
from unittest.mock import MagicMock

import cv2
import numpy as np
import pytest


@pytest.fixture
def mock_tool_context():
    """A MagicMock that behaves like tools.ToolContext with a dict state."""
    ctx = MagicMock()
    ctx.state = {}
    return ctx


@pytest.fixture
def flowchart_image_b64():
    """Create a synthetic flowchart image with rectangles, diamonds, and arrows.

    Returns base64-encoded PNG bytes suitable for storing in state["source_image"].
    """
    img = np.ones((600, 400, 3), dtype=np.uint8) * 255  # White background

    # Rectangle 1 (top) — "Start" box
    cv2.rectangle(img, (150, 30), (250, 80), (0, 0, 0), 2)
    cv2.putText(img, "Start", (165, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)

    # Rectangle 2 (middle) — "Process" box
    cv2.rectangle(img, (130, 180), (270, 240), (0, 0, 0), 2)
    cv2.putText(img, "Process", (148, 218), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)

    # Rectangle 3 (bottom) — "End" box
    cv2.rectangle(img, (150, 380), (250, 430), (0, 0, 0), 2)
    cv2.putText(img, "End", (175, 415), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)

    # Diamond (decision) — between Process and End
    diamond_pts = np.array([[200, 280], [250, 320], [200, 360], [150, 320]], dtype=np.int32)
    cv2.polylines(img, [diamond_pts], True, (0, 0, 0), 2)
    cv2.putText(img, "?", (193, 325), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)

    # Arrow: Start -> Process
    cv2.arrowedLine(img, (200, 80), (200, 180), (0, 0, 0), 2, tipLength=0.15)

    # Arrow: Process -> Diamond
    cv2.arrowedLine(img, (200, 240), (200, 280), (0, 0, 0), 2, tipLength=0.15)

    # Arrow: Diamond -> End
    cv2.arrowedLine(img, (200, 360), (200, 380), (0, 0, 0), 2, tipLength=0.15)

    # Encode as PNG
    _, png_bytes = cv2.imencode(".png", img)
    return base64.b64encode(png_bytes.tobytes()).decode("utf-8")


@pytest.fixture
def noisy_photo_b64():
    """Create a noisy photographic-style image (not suitable for CV).

    Returns base64-encoded PNG bytes.
    """
    rng = np.random.default_rng(42)
    img = rng.integers(0, 256, (400, 400, 3), dtype=np.uint8)
    _, png_bytes = cv2.imencode(".png", img)
    return base64.b64encode(png_bytes.tobytes()).decode("utf-8")


@pytest.fixture
def flowchart_state(flowchart_image_b64):
    """Pre-populated state dict with flowchart image loaded."""
    return {
        "source_image": flowchart_image_b64,
        "source_image_mime_type": "image/png",
        "image_dimensions": {"width": 400, "height": 600},
        "image_format": "PNG",
    }
