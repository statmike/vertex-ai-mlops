"""Diagram-type detection and ID normalization utilities.

Centralizes the "is this a schematic?" check and schematic-specific
ID cleaning so the pattern is not duplicated across multiple tools.
"""

import re

# Pattern matching grid-cell suffixes appended by the agent (e.g., _r1_c2, _r0_c3)
_GRID_SUFFIX_RE = re.compile(r"(_r\d+_c\d+)+$")


def is_schematic(graph_or_type: dict | str) -> bool:
    """Return True if the diagram type indicates a schematic or circuit.

    Args:
        graph_or_type: Either a graph dict (with a "diagram_type" key)
                       or a raw diagram_type string.
    """
    if isinstance(graph_or_type, dict):
        dtype = (graph_or_type.get("diagram_type") or "").lower()
    else:
        dtype = (graph_or_type or "").lower()
    return "schematic" in dtype or "circuit" in dtype


def normalize_node_id(node_id: str, graph: dict) -> str:
    """Strip grid-cell suffixes from schematic node IDs.

    For schematics, the agent may append _r1_c2-style suffixes when
    the same component appears in multiple grid cells. This strips
    those suffixes so duplicate detection works on the base ID.

    For non-schematic diagrams, returns the ID unchanged.

    Args:
        node_id: The raw node ID (e.g., "C92_r1_c2").
        graph: The graph dict (used to check diagram_type).

    Returns:
        The cleaned node ID (e.g., "C92").
    """
    if not is_schematic(graph):
        return node_id
    return _GRID_SUFFIX_RE.sub("", node_id)


def generate_schematic_grid(
    cols: int = 4, rows: int = 3, overlap: float = 0.05
) -> list[dict]:
    """Generate systematic grid regions for schematic examination.

    Creates cols x rows cells in normalized 0-1000 space with `overlap` fraction
    padding on each side to catch components at cell boundaries.

    Args:
        cols: Number of columns in the grid.
        rows: Number of rows in the grid.
        overlap: Fraction of cell size to pad on each side (0.05 = 5%).

    Returns:
        List of region dicts with element_type "grid_cell".
    """
    cell_w = 1000 / cols
    cell_h = 1000 / rows
    pad_x = cell_w * overlap
    pad_y = cell_h * overlap

    regions = []
    for r in range(rows):
        for c in range(cols):
            left = max(0, int(c * cell_w - pad_x))
            top = max(0, int(r * cell_h - pad_y))
            right = min(1000, int((c + 1) * cell_w + pad_x))
            bottom = min(1000, int((r + 1) * cell_h + pad_y))
            cell_id = f"grid_{r}_{c}"
            regions.append(
                {
                    "region_id": cell_id,
                    "label": f"Grid cell row {r}, col {c}",
                    "description": f"Systematic grid cell ({r},{c}) for schematic examination",
                    "bounding_box": [top, left, bottom, right],
                    "element_type": "grid_cell",
                }
            )
    return regions
