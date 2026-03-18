"""Detect visual elements (shapes, contours) in the source image using OpenCV."""

import base64
import logging

import cv2
import numpy as np
from google.adk import tools

from .util_common import log_tool_error

logger = logging.getLogger(__name__)


def _classify_shape(approx_vertices: int) -> str:
    """Classify a contour shape based on its polygon approximation vertex count."""
    if approx_vertices == 3:
        return "triangle"
    elif approx_vertices == 4:
        return "rectangle"
    elif approx_vertices == 5:
        return "pentagon"
    elif approx_vertices == 6:
        return "hexagon"
    elif approx_vertices > 6:
        return "circle"
    return "unknown"


async def detect_elements(
    binary_threshold: str = "adaptive",
    min_contour_area: int = 500,
    approx_epsilon: float = 0.02,
    morphology_kernel: int = 3,
    tool_context: tools.ToolContext = None,
) -> str:
    """
    Detect visual elements in the source image using OpenCV contour detection.

    Applies adaptive thresholding, morphological closing, contour detection,
    and shape classification to find distinct visual elements (rectangles,
    circles, triangles, etc.) in the diagram.

    Args:
        binary_threshold: Thresholding method — "adaptive" (default) or an
            integer value (0-255) for simple thresholding.
        min_contour_area: Minimum contour area in pixels to keep (filters noise).
        approx_epsilon: Polygon approximation epsilon as fraction of perimeter.
        morphology_kernel: Kernel size for morphological closing (fills small gaps).
        tool_context: The ADK tool context containing the source image in state.

    Returns:
        A summary of detected elements with stats and parameters used,
        or an error message if detection fails.
    """
    try:
        source_image_b64 = tool_context.state.get("source_image")
        if not source_image_b64:
            return "Error: No source image loaded. Use load_image first."

        image_bytes = base64.b64decode(source_image_b64)
        img_array = np.frombuffer(image_bytes, dtype=np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        if img is None:
            return "Error: Could not decode image for element detection."

        dimensions = tool_context.state.get("image_dimensions", {})
        img_height = dimensions.get("height", img.shape[0])
        img_width = dimensions.get("width", img.shape[1])

        # 1. Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # 2. Thresholding
        if binary_threshold == "adaptive":
            binary = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2
            )
        else:
            thresh_val = int(binary_threshold)
            _, binary = cv2.threshold(gray, thresh_val, 255, cv2.THRESH_BINARY_INV)

        # 3. Morphological close (fill small gaps in shapes)
        kernel = np.ones((morphology_kernel, morphology_kernel), np.uint8)
        closed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=2)

        # 4. Find contours
        contours, hierarchy = cv2.findContours(closed, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        total_contours = len(contours)

        # 5. Filter and classify
        elements = []
        filtered_count = 0

        for contour in contours:
            area = cv2.contourArea(contour)
            if area < min_contour_area:
                filtered_count += 1
                continue

            # Bounding box
            x, y, w, h = cv2.boundingRect(contour)

            # Filter by aspect ratio (extremely elongated contours are likely lines, not shapes)
            aspect_ratio = max(w, h) / max(min(w, h), 1)
            if aspect_ratio > 15:
                filtered_count += 1
                continue

            # Filter contours that span nearly the entire image (likely the image border)
            if w > img_width * 0.95 and h > img_height * 0.95:
                filtered_count += 1
                continue

            # Polygon approximation
            perimeter = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, approx_epsilon * perimeter, True)
            vertex_count = len(approx)

            shape = _classify_shape(vertex_count)

            # Normalize bounding box to 0-1000 scale [y_min, x_min, y_max, x_max]
            y_min = int(y / img_height * 1000)
            x_min = int(x / img_width * 1000)
            y_max = int((y + h) / img_height * 1000)
            x_max = int((x + w) / img_width * 1000)

            elements.append({
                "id": f"cv_{len(elements) + 1}",
                "bounding_box": [y_min, x_min, y_max, x_max],
                "shape": shape,
                "area": int(area),
                "vertices": vertex_count,
            })

        # Count shape types
        shape_counts = {}
        for el in elements:
            s = el["shape"]
            shape_counts[s] = shape_counts.get(s, 0) + 1

        params_used = {
            "binary_threshold": binary_threshold,
            "min_contour_area": min_contour_area,
            "approx_epsilon": approx_epsilon,
            "morphology_kernel": morphology_kernel,
        }

        stats = {
            "total_contours": total_contours,
            "filtered": filtered_count,
            "elements_kept": len(elements),
            "shapes_found": shape_counts,
        }

        # Store in state for other tools
        tool_context.state["cv_elements"] = elements
        tool_context.state["cv_detect_stats"] = stats
        tool_context.state["cv_detect_params"] = params_used

        # Build summary
        shape_summary = ", ".join(f"{count} {shape}(s)" for shape, count in shape_counts.items())

        result = (
            f"Element detection complete.\n"
            f"  Total contours found: {total_contours}\n"
            f"  Filtered out: {filtered_count}\n"
            f"  Elements kept: {len(elements)}\n"
            f"  Shapes: {shape_summary or 'none'}\n"
            f"  Params used: {params_used}\n\n"
        )

        # Guidance for self-refinement
        if len(elements) > 200:
            result += (
                "Too many elements detected — likely noise. Consider increasing "
                "min_contour_area or morphology_kernel and calling detect_elements again."
            )
        elif len(elements) < 3 and total_contours > 10:
            result += (
                "Very few elements kept despite many contours. Consider decreasing "
                "min_contour_area or adjusting binary_threshold and calling detect_elements again."
            )
        elif len(elements) == 0:
            result += (
                "No elements detected. The image may not be suitable for CV preprocessing. "
                "Consider calling report_results with status \"partial\" or \"skipped\"."
            )
        else:
            result += "Detection looks reasonable. Proceed with detect_connections."

        return result

    except Exception as e:
        return log_tool_error("detect_elements", e)
