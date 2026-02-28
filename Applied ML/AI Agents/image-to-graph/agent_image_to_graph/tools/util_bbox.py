"""Bounding box format normalization utilities.

The internal format is always [y_min, x_min, y_max, x_max] (0-1000 normalized).

Gemini-facing prompts use the named dict format {"top", "left", "bottom", "right"}
(CSS convention) to eliminate coordinate-order ambiguity. This module converts
between the two formats at storage boundaries.
"""


def normalize_bbox(bbox) -> list[int] | None:
    """Convert a bounding box from any supported format to [y_min, x_min, y_max, x_max].

    Supported input formats:
      - dict: {"top": N, "left": N, "bottom": N, "right": N}
      - list/tuple: [y_min, x_min, y_max, x_max] (passed through as-is)

    Returns None if the input is invalid or missing required keys.
    """
    if isinstance(bbox, dict):
        try:
            return [
                int(bbox["top"]),
                int(bbox["left"]),
                int(bbox["bottom"]),
                int(bbox["right"]),
            ]
        except (KeyError, TypeError, ValueError):
            return None
    if isinstance(bbox, (list, tuple)) and len(bbox) == 4:
        try:
            return [int(v) for v in bbox]
        except (TypeError, ValueError):
            return None
    return None
