"""Detect connections (lines, arrows) between elements using OpenCV."""

import base64
import logging
import math

import cv2
import numpy as np
from google.adk import tools

from .util_common import log_tool_error

logger = logging.getLogger(__name__)


def _point_near_bbox(px: int, py: int, bbox: list[int], img_w: int, img_h: int, margin: int = 20) -> bool:
    """Check if a pixel point (px, py) is near a normalized bounding box.

    Args:
        px, py: Pixel coordinates.
        bbox: Normalized [y_min, x_min, y_max, x_max] in 0-1000 scale.
        img_w, img_h: Image dimensions in pixels.
        margin: Pixel margin for proximity check.
    """
    # Convert bbox to pixel coords
    by_min = bbox[0] / 1000 * img_h
    bx_min = bbox[1] / 1000 * img_w
    by_max = bbox[2] / 1000 * img_h
    bx_max = bbox[3] / 1000 * img_w

    return (bx_min - margin <= px <= bx_max + margin and by_min - margin <= py <= by_max + margin)


def _line_overlaps_bbox(x1: int, y1: int, x2: int, y2: int, bbox: list[int], img_w: int, img_h: int) -> bool:
    """Check if a line segment substantially overlaps with a bounding box interior.

    Returns True if both endpoints are inside the bbox (the line is part of the shape, not a connection).
    """
    by_min = bbox[0] / 1000 * img_h
    bx_min = bbox[1] / 1000 * img_w
    by_max = bbox[2] / 1000 * img_h
    bx_max = bbox[3] / 1000 * img_w

    p1_inside = bx_min <= x1 <= bx_max and by_min <= y1 <= by_max
    p2_inside = bx_min <= x2 <= bx_max and by_min <= y2 <= by_max

    return p1_inside and p2_inside


def _detect_arrow_direction(gray: np.ndarray, x1: int, y1: int, x2: int, y2: int, search_radius: int = 25) -> str | None:
    """Detect arrowhead at line endpoints by looking for triangular contours.

    Returns "forward" if arrowhead near (x2, y2), "backward" if near (x1, y1), None if no arrow.
    """
    h, w = gray.shape

    for endpoint, direction in [((x2, y2), "forward"), ((x1, y1), "backward")]:
        ex, ey = endpoint
        # Extract a small region around the endpoint
        ry_min = max(0, ey - search_radius)
        ry_max = min(h, ey + search_radius)
        rx_min = max(0, ex - search_radius)
        rx_max = min(w, ex + search_radius)

        if ry_max - ry_min < 5 or rx_max - rx_min < 5:
            continue

        roi = gray[ry_min:ry_max, rx_min:rx_max]
        _, roi_bin = cv2.threshold(roi, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        roi_contours, _ = cv2.findContours(roi_bin, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for cnt in roi_contours:
            area = cv2.contourArea(cnt)
            if area < 20 or area > search_radius * search_radius * 2:
                continue
            peri = cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, 0.04 * peri, True)
            if len(approx) == 3:
                return direction

    return None


async def detect_connections(tool_context: tools.ToolContext) -> str:
    """
    Detect connections (lines, arrows) between previously detected elements.

    Uses Canny edge detection and probabilistic Hough line transform to find
    lines in the image, then matches line endpoints to element bounding boxes
    to identify connections.

    Args:
        tool_context: The ADK tool context containing the source image and
            detected elements (from detect_elements) in state.

    Returns:
        A summary of detected connections with confidence levels,
        or an error message if detection fails.
    """
    try:
        source_image_b64 = tool_context.state.get("source_image")
        if not source_image_b64:
            return "Error: No source image loaded. Use load_image first."

        elements = tool_context.state.get("cv_elements", [])
        if not elements:
            return "Error: No elements detected. Run detect_elements first."

        image_bytes = base64.b64decode(source_image_b64)
        img_array = np.frombuffer(image_bytes, dtype=np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        if img is None:
            return "Error: Could not decode image for connection detection."

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        img_h, img_w = gray.shape

        # 1. Edge detection
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)

        # 2. Probabilistic Hough line transform
        min_line_length = max(20, min(img_w, img_h) // 20)
        max_line_gap = max(10, min(img_w, img_h) // 40)
        lines = cv2.HoughLinesP(
            edges, 1, np.pi / 180, threshold=50,
            minLineLength=min_line_length, maxLineGap=max_line_gap,
        )

        if lines is None:
            tool_context.state["cv_connections"] = []
            return "No lines detected in the image. No connections found."

        # 3. Filter lines that are entirely inside an element bbox (shape edges, not connections)
        candidate_lines = []
        for line in lines:
            x1, y1, x2, y2 = line[0]
            inside_element = False
            for el in elements:
                if _line_overlaps_bbox(x1, y1, x2, y2, el["bounding_box"], img_w, img_h):
                    inside_element = True
                    break
            if not inside_element:
                candidate_lines.append((int(x1), int(y1), int(x2), int(y2)))

        # 4. Match line endpoints to elements
        connections = []
        seen_pairs = set()

        # Adaptive margin based on image size
        margin = max(15, min(img_w, img_h) // 30)

        for x1, y1, x2, y2 in candidate_lines:
            source_id = None
            target_id = None

            for el in elements:
                bbox = el["bounding_box"]
                if _point_near_bbox(x1, y1, bbox, img_w, img_h, margin):
                    source_id = el["id"]
                if _point_near_bbox(x2, y2, bbox, img_w, img_h, margin):
                    target_id = el["id"]

            if source_id and target_id and source_id != target_id:
                pair = (source_id, target_id)
                reverse_pair = (target_id, source_id)

                if pair in seen_pairs or reverse_pair in seen_pairs:
                    continue

                # Detect arrow direction
                arrow_dir = _detect_arrow_direction(gray, x1, y1, x2, y2)
                if arrow_dir == "backward":
                    source_id, target_id = target_id, source_id
                    pair = (source_id, target_id)

                line_type = "arrow" if arrow_dir else "solid"

                # Compute line length for confidence
                length = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
                confidence = 0.9 if length > min_line_length * 2 else 0.7

                seen_pairs.add(pair)
                connections.append({
                    "id": f"cv_conn_{len(connections) + 1}",
                    "source_element_id": source_id,
                    "target_element_id": target_id,
                    "line_type": line_type,
                    "endpoints": [[x1, y1], [x2, y2]],
                    "confidence": confidence,
                })

        # Store in state
        tool_context.state["cv_connections"] = connections

        if not connections:
            return (
                f"Detected {len(lines)} lines but none connected two different elements.\n"
                "This may mean elements are not connected by straight lines, "
                "or detection parameters need adjustment."
            )

        # Build summary
        conn_lines = []
        for conn in connections:
            conn_lines.append(
                f"  - {conn['id']}: {conn['source_element_id']} -> {conn['target_element_id']} "
                f"({conn['line_type']}) confidence={conn['confidence']:.1f}"
            )

        return (
            f"Connection detection complete.\n"
            f"  Total lines detected: {len(lines)}\n"
            f"  Candidate lines (not inside shapes): {len(candidate_lines)}\n"
            f"  Connections matched: {len(connections)}\n\n"
            f"Connections:\n" + "\n".join(conn_lines) + "\n\n"
            "Proceed with label_elements to add OCR and semantic labels."
        )

    except Exception as e:
        return log_tool_error("detect_connections", e)
