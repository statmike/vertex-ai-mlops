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
