"""Bounding box format normalization utilities.

The internal format is always [y_min, x_min, y_max, x_max] (0-1000 normalized).

Gemini-facing prompts use the named dict format {"top", "left", "bottom", "right"}
(CSS convention) to eliminate coordinate-order ambiguity. This module converts
between the two formats at storage boundaries.

Auto-corrections applied after format conversion:
  - Inverted coordinates (e.g., top > bottom) are swapped per axis pair.
  - Values are clamped to the valid 0-1000 range.
"""


def normalize_bbox(bbox) -> list[int] | None:
    """Convert a bounding box from any supported format to [y_min, x_min, y_max, x_max].

    Supported input formats:
      - dict: {"top": N, "left": N, "bottom": N, "right": N}
      - list/tuple: [y_min, x_min, y_max, x_max] (passed through as-is)

    Auto-corrects inverted coordinates (min > max) and clamps to 0-1000.

    Returns None if the input is invalid or missing required keys.
    """
    result: list[int] | None = None
    if isinstance(bbox, dict):
        try:
            result = [
                int(bbox["top"]),
                int(bbox["left"]),
                int(bbox["bottom"]),
                int(bbox["right"]),
            ]
        except (KeyError, TypeError, ValueError):
            return None
    elif isinstance(bbox, (list, tuple)) and len(bbox) == 4:
        try:
            result = [int(v) for v in bbox]
        except (TypeError, ValueError):
            return None
    else:
        return None

    # Auto-correct inverted coordinates (e.g., top > bottom)
    if result[0] > result[2]:
        result[0], result[2] = result[2], result[0]
    if result[1] > result[3]:
        result[1], result[3] = result[3], result[1]

    # Clamp to valid 0-1000 range
    result = [max(0, min(1000, v)) for v in result]

    return result


def compute_iou(bbox_a: list[int], bbox_b: list[int]) -> float:
    """Intersection over Union between two [y_min, x_min, y_max, x_max] bboxes.

    Returns 0.0 if either bbox has zero area.
    """
    ya1, xa1, ya2, xa2 = bbox_a
    yb1, xb1, yb2, xb2 = bbox_b

    area_a = (ya2 - ya1) * (xa2 - xa1)
    area_b = (yb2 - yb1) * (xb2 - xb1)
    if area_a <= 0 or area_b <= 0:
        return 0.0

    inter_y1 = max(ya1, yb1)
    inter_x1 = max(xa1, xb1)
    inter_y2 = min(ya2, yb2)
    inter_x2 = min(xa2, xb2)

    inter_w = max(0, inter_x2 - inter_x1)
    inter_h = max(0, inter_y2 - inter_y1)
    inter_area = inter_w * inter_h

    union_area = area_a + area_b - inter_area
    if union_area <= 0:
        return 0.0

    return inter_area / union_area


def compute_label_similarity(label_a: str, label_b: str) -> float:
    """Normalized similarity between two labels (case-insensitive).

    Uses SequenceMatcher ratio from difflib. Returns 0.0-1.0.
    Returns 0.0 if both labels are empty.
    """
    from difflib import SequenceMatcher

    a = label_a.strip().lower()
    b = label_b.strip().lower()
    if not a and not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


def compute_centroid_proximity(bbox_a: list[int], bbox_b: list[int]) -> float:
    """Proximity score (0.0-1.0) based on centroid distance between two bboxes.

    Uses the 0-1000 normalized coordinate space. A distance of 0 returns 1.0;
    the score decays with distance using a Gaussian-like falloff (sigma=150).
    Maximum possible distance on the 1000-scale is ~1414 (diagonal).
    """
    import math

    cy_a = (bbox_a[0] + bbox_a[2]) / 2
    cx_a = (bbox_a[1] + bbox_a[3]) / 2
    cy_b = (bbox_b[0] + bbox_b[2]) / 2
    cx_b = (bbox_b[1] + bbox_b[3]) / 2

    dist = math.sqrt((cy_a - cy_b) ** 2 + (cx_a - cx_b) ** 2)

    # Gaussian falloff: sigma=150 means ~0.5 at distance 177, ~0.1 at distance 340
    sigma = 150
    return math.exp(-(dist ** 2) / (2 * sigma ** 2))


def match_cv_to_graph_elements(
    cv_elements: list[dict],
    graph_nodes: list[dict],
) -> list[dict]:
    """Match CV elements to graph nodes using label + spatial scoring.

    CV elements use "text" for OCR content (not "label"), so this function
    reads the "text" field from CV elements for label comparison.

    Scoring: 0.45 * label_similarity + 0.25 * iou + 0.30 * centroid_proximity

    Uses greedy best-match (highest combined score first, 1:1 matching).
    Skips group nodes (shape == "group_rectangle") since CV doesn't detect groups.

    Returns list of match dicts:
        {"node_id", "cv_index", "label_score", "iou_score", "centroid_score",
         "combined_score", "node_bbox", "cv_bbox", "action": "nudge"|"flag"|"skip"}

    Thresholds:
        - nudge: combined_score >= 0.50 AND iou >= 0.15
                 AND area_ratio between 0.3 and 3.0 (guards against partial/merged contours)
        - flag:  combined_score < 0.30 OR iou < 0.05
        - skip:  everything in between, or nudge-eligible but failed area ratio guard
    """
    # Filter out group nodes
    eligible_nodes = [
        n for n in graph_nodes
        if n.get("id") and n.get("shape") != "group_rectangle"
    ]

    # Compute all pairwise scores
    candidates = []
    for ci, cv_el in enumerate(cv_elements):
        cv_bbox = cv_el.get("bounding_box")
        # CV elements use "text" for OCR content, fall back to "label" for tests
        cv_label = cv_el.get("text") or cv_el.get("label", "")
        if not cv_bbox or len(cv_bbox) != 4:
            continue

        for node in eligible_nodes:
            node_bbox = node.get("bounding_box")
            node_label = node.get("label", "")
            if not node_bbox or len(node_bbox) != 4:
                continue

            iou = compute_iou(node_bbox, cv_bbox)
            label_sim = compute_label_similarity(node_label, cv_label)
            centroid = compute_centroid_proximity(node_bbox, cv_bbox)
            combined = 0.45 * label_sim + 0.25 * iou + 0.30 * centroid

            candidates.append({
                "node_id": node["id"],
                "cv_index": ci,
                "label_score": label_sim,
                "iou_score": iou,
                "centroid_score": centroid,
                "combined_score": combined,
                "node_bbox": list(node_bbox),
                "cv_bbox": list(cv_bbox),
            })

    # Greedy best-match: sort by combined score descending, assign 1:1
    candidates.sort(key=lambda c: c["combined_score"], reverse=True)
    matched_nodes: set[str] = set()
    matched_cvs: set[int] = set()
    matches = []

    for c in candidates:
        if c["node_id"] in matched_nodes or c["cv_index"] in matched_cvs:
            continue
        matched_nodes.add(c["node_id"])
        matched_cvs.add(c["cv_index"])

        # Area ratio guard: prevent nudging to partial contours or merged outlines
        node_area = max(1, (c["node_bbox"][2] - c["node_bbox"][0])
                        * (c["node_bbox"][3] - c["node_bbox"][1]))
        cv_area = max(1, (c["cv_bbox"][2] - c["cv_bbox"][0])
                      * (c["cv_bbox"][3] - c["cv_bbox"][1]))
        c["area_ratio"] = cv_area / node_area

        # Classify action
        if c["combined_score"] >= 0.50 and c["iou_score"] >= 0.15:
            if c["area_ratio"] < 0.3 or c["area_ratio"] > 3.0:
                c["action"] = "skip"  # size mismatch — partial or merged contour
            else:
                c["action"] = "nudge"
        elif c["combined_score"] < 0.30 or c["iou_score"] < 0.05:
            c["action"] = "flag"
        else:
            c["action"] = "skip"

        matches.append(c)

    return matches


def detect_schematic_mode(graph: dict, nodes: list[dict]) -> bool:
    """Detect if the diagram is a schematic based on type and bbox patterns.

    Two independent signals (any sufficient):
    1. diagram_type contains "schematic" or "circuit"
    2. >30% of bboxes have extreme aspect ratio (>8:1)

    Note: oversized area prevalence is NOT used as a signal here because the
    general fix_oversized_bboxes() guard handles oversized bboxes for all
    diagram types.
    """
    # Signal 1: diagram_type keyword
    from .util_diagram_type import is_schematic

    if is_schematic(graph):
        return True

    # Signal 2: extreme aspect ratio prevalence
    extreme_ratio = 0
    total = 0
    for node in nodes:
        if node.get("shape") == "group_rectangle":
            continue
        bbox = node.get("bounding_box")
        if not bbox or len(bbox) != 4:
            continue
        y_min, x_min, y_max, x_max = bbox
        h = y_max - y_min
        w = x_max - x_min
        if h <= 0 or w <= 0:
            continue
        total += 1
        ratio = max(h, w) / min(h, w)
        if ratio > 8:
            extreme_ratio += 1

    if total < 3:
        return False
    return extreme_ratio / total > 0.30


def fix_schematic_bboxes(nodes: list[dict]) -> list[dict]:
    """Normalize extreme aspect-ratio schematic bboxes to component-sized regions.

    Catches wire-trace bboxes (aspect ratio >8:1) from Gemini following
    connection paths instead of component footprints.

    Target side = max(30, int(sqrt(width * height)))  [geometric mean]
    Uses centroid preservation and 0-1000 clamping.

    Note: oversized-area bboxes are handled by the general fix_oversized_bboxes()
    guard, which runs for ALL diagram types.

    Returns list of correction dicts for tracking:
        [{"node_id", "old_bbox", "new_bbox", "aspect_ratio"}, ...]
    """
    import math

    ASPECT_THRESHOLD = 8.0

    corrections = []
    for node in nodes:
        if node.get("shape") == "group_rectangle":
            continue
        bbox = node.get("bounding_box")
        if not bbox or len(bbox) != 4:
            continue
        y_min, x_min, y_max, x_max = bbox
        h = y_max - y_min
        w = x_max - x_min
        if h <= 0 or w <= 0:
            continue

        ratio = max(h, w) / min(h, w)
        if ratio <= ASPECT_THRESHOLD:
            continue

        # Centroid
        cy = (y_min + y_max) / 2
        cx = (x_min + x_max) / 2

        # Geometric mean preserves approximate area
        side = max(30, int(math.sqrt(w * h)))
        half = side / 2

        # New bbox centered on centroid, clamped to 0-1000
        new_bbox = [
            max(0, int(cy - half)),
            max(0, int(cx - half)),
            min(1000, int(cy + half)),
            min(1000, int(cx + half)),
        ]

        old_bbox = list(bbox)
        node["bounding_box"] = new_bbox
        corrections.append({
            "node_id": node.get("id", "?"),
            "old_bbox": old_bbox,
            "new_bbox": new_bbox,
            "aspect_ratio": round(ratio, 1),
        })

    return corrections


def fix_oversized_bboxes(nodes: list[dict], area_threshold: float = 0.10) -> list[dict]:
    """Shrink non-group nodes with problematic bounding boxes.

    This is a diagram-type-agnostic safety net. A non-group node is fixed when
    ANY of these conditions is true:
      1. Area exceeds area_threshold (default 10%) of the 1000x1000 image.
      2. Aspect ratio exceeds 8:1 (extreme elongation).
      3. Max dimension exceeds min(350, 4 * reference_side) — catches nodes
         spanning >35% of the image on a single axis even when area/ratio pass.

    Fixed nodes are shrunk to the median size of normal components, centered
    on their centroid.

    Returns list of correction dicts: [{"node_id", "old_bbox", "new_bbox"}, ...]
    """
    import math

    IMAGE_AREA = 1_000_000
    RATIO_THRESHOLD = 8.0

    # First pass: collect areas of normal nodes
    normal_areas = []
    for node in nodes:
        if node.get("shape") == "group_rectangle":
            continue
        bbox = node.get("bounding_box")
        if not bbox or len(bbox) != 4:
            continue
        y_min, x_min, y_max, x_max = bbox
        h = y_max - y_min
        w = x_max - x_min
        if h <= 0 or w <= 0:
            continue
        area = h * w
        ratio = max(h, w) / min(h, w)
        if area <= area_threshold * IMAGE_AREA and ratio <= RATIO_THRESHOLD:
            normal_areas.append(area)

    # Compute reference side from median of normal components
    if normal_areas:
        normal_areas.sort()
        median_area = normal_areas[len(normal_areas) // 2]
        reference_side = max(30, int(math.sqrt(median_area)))
    else:
        reference_side = 50

    threshold_area = area_threshold * IMAGE_AREA
    max_dim_limit = min(350, 4 * reference_side)

    # Second pass: shrink problematic nodes
    corrections = []
    for node in nodes:
        if node.get("shape") == "group_rectangle":
            continue
        bbox = node.get("bounding_box")
        if not bbox or len(bbox) != 4:
            continue
        y_min, x_min, y_max, x_max = bbox
        h = y_max - y_min
        w = x_max - x_min
        if h <= 0 or w <= 0:
            continue

        area = h * w
        ratio = max(h, w) / min(h, w) if min(h, w) > 0 else float("inf")

        if area <= threshold_area and ratio <= RATIO_THRESHOLD and max(h, w) <= max_dim_limit:
            continue

        # Centroid
        cy = (y_min + y_max) / 2
        cx = (x_min + x_max) / 2
        half = reference_side / 2

        # New bbox centered on centroid, clamped to 0-1000
        new_bbox = [
            max(0, int(cy - half)),
            max(0, int(cx - half)),
            min(1000, int(cy + half)),
            min(1000, int(cx + half)),
        ]

        old_bbox = list(bbox)
        node["bounding_box"] = new_bbox
        corrections.append({
            "node_id": node.get("id", "?"),
            "old_bbox": old_bbox,
            "new_bbox": new_bbox,
        })

    return corrections


def detect_bbox_corrections(raw_ints: list[int], corrected: list[int]) -> dict | None:
    """Compare raw int values with corrected result. Returns correction dict or None.

    Args:
        raw_ints: The original integer values before normalization [y_min, x_min, y_max, x_max].
        corrected: The normalized result from normalize_bbox().

    Returns:
        A dict with y_inverted, x_inverted, clamped flags, or None if no correction was needed.
    """
    if raw_ints == corrected:
        return None

    y_inverted = raw_ints[0] > raw_ints[2]
    x_inverted = raw_ints[1] > raw_ints[3]
    clamped = any(v < 0 or v > 1000 for v in raw_ints)

    return {
        "y_inverted": y_inverted,
        "x_inverted": x_inverted,
        "clamped": clamped,
    }
