import logging
import math

from google.adk import tools

from .util_common import log_tool_error
from .util_schema import resolve_items

logger = logging.getLogger(__name__)


async def validate_graph(tool_context: tools.ToolContext) -> str:
    """
    Validate the current graph for structural correctness and schema conformance.

    Performs two levels of validation:
    1. Structural: missing required fields (id, label, source, target), duplicate IDs,
       orphaned edges, disconnected nodes.
    2. Schema: if an input_schema or generated schema exists, validates each node and
       edge against the schema's required/optional fields and types.

    Args:
        tool_context: The ADK tool context containing graph and schema in state.

    Returns:
        A validation report listing any errors, warnings, or confirming
        the graph is valid.
    """
    try:
        graph = tool_context.state.get("graph")
        if graph is None:
            return "Error: No graph state found. Use load_image first."

        nodes = graph.get("nodes", [])
        edges = graph.get("edges", [])

        errors = []
        warnings = []

        # 1. Check diagram type is set
        if not graph.get("diagram_type"):
            warnings.append("Diagram type is not set.")

        # 2. Check for empty graph
        if not nodes and not edges:
            errors.append("Graph is empty — no nodes or edges.")
            return _format_report(errors, warnings)

        # 3. Validate nodes — structural
        node_ids = set()
        for i, node in enumerate(nodes):
            node_id = node.get("id")
            if not node_id:
                errors.append(f"Node at index {i} is missing required field 'id'.")
                continue
            if not node.get("label"):
                errors.append(f"Node '{node_id}' is missing required field 'label'.")
            if node_id in node_ids:
                errors.append(f"Duplicate node id: '{node_id}'.")
            node_ids.add(node_id)

        # 4. Detect and fix bounding box coordinate swaps (x/y confusion)
        image_dimensions = tool_context.state.get("image_dimensions", {})
        swap_needed = _detect_bbox_swap(nodes, image_dimensions)
        if swap_needed:
            swap_count = 0
            for node in nodes:
                bbox = node.get("bounding_box")
                if bbox and len(bbox) == 4:
                    # Swap [x_min, y_min, x_max, y_max] → [y_min, x_min, y_max, x_max]
                    node["bounding_box"] = [bbox[1], bbox[0], bbox[3], bbox[2]]
                    swap_count += 1
            warnings.append(
                f"Bounding box coordinate swap detected and corrected on {swap_count} nodes "
                f"(image {image_dimensions.get('width', '?')}x{image_dimensions.get('height', '?')}). "
                f"Swapped x/y coordinates to match [y_min, x_min, y_max, x_max] convention."
            )
            # Track xy_swap in state for BQ analytics observability
            prev = list(tool_context.state.get("bbox_corrections", []))
            prev.append({
                "tool": "validate_graph",
                "op": "xy_swap",
                "node_count": swap_count,
                "image_width": image_dimensions.get("width"),
                "image_height": image_dimensions.get("height"),
            })
            tool_context.state["bbox_corrections"] = prev
            # Update graph state with corrected bboxes
            tool_context.state["graph"] = graph

        # 5. Validate parent_id references (grouping) and auto-fix group bounding boxes
        node_by_id = {n.get("id"): n for n in nodes if n.get("id")}
        group_node_ids = {n.get("id") for n in nodes if n.get("shape") == "group_rectangle"}
        children_of: dict[str, list[str]] = {gid: [] for gid in group_node_ids}
        for node in nodes:
            parent_id = node.get("parent_id")
            if parent_id:
                node_id = node.get("id", "?")
                if parent_id not in node_ids:
                    errors.append(
                        f"Node '{node_id}' has parent_id '{parent_id}' which does not exist."
                    )
                elif parent_id not in group_node_ids:
                    warnings.append(
                        f"Node '{node_id}' has parent_id '{parent_id}' but that node "
                        f"is not a group (shape != 'group_rectangle')."
                    )
                else:
                    children_of[parent_id].append(node_id)
        for gid in group_node_ids:
            if not children_of[gid]:
                warnings.append(
                    f"Group node '{gid}' has no children (no nodes with parent_id='{gid}')."
                )
            else:
                # Auto-compute group bounding box from children (with padding)
                child_bboxes = [
                    node_by_id[cid].get("bounding_box")
                    for cid in children_of[gid]
                    if cid in node_by_id
                    and node_by_id[cid].get("bounding_box")
                    and len(node_by_id[cid].get("bounding_box", [])) == 4
                ]
                if child_bboxes:
                    y_min = min(b[0] for b in child_bboxes)
                    x_min = min(b[1] for b in child_bboxes)
                    y_max = max(b[2] for b in child_bboxes)
                    x_max = max(b[3] for b in child_bboxes)
                    # Add padding (2% of 1000-scale = 20 units, clamped to 0-1000)
                    pad = 20
                    computed_bbox = [
                        max(0, y_min - pad),
                        max(0, x_min - pad),
                        min(1000, y_max + pad),
                        min(1000, x_max + pad),
                    ]
                    group_node = node_by_id[gid]
                    old_bbox = group_node.get("bounding_box")
                    group_node["bounding_box"] = computed_bbox
                    if old_bbox and old_bbox != computed_bbox:
                        warnings.append(
                            f"Group '{gid}' bounding_box auto-corrected from children: "
                            f"{old_bbox} -> {computed_bbox}"
                        )

        # 6. Validate edges — structural
        edge_ids = set()
        for i, edge in enumerate(edges):
            edge_id = edge.get("id")
            if not edge_id:
                errors.append(f"Edge at index {i} is missing required field 'id'.")
                continue
            if not edge.get("source"):
                errors.append(f"Edge '{edge_id}' is missing required field 'source'.")
            if not edge.get("target"):
                errors.append(f"Edge '{edge_id}' is missing required field 'target'.")
            if edge_id in edge_ids:
                errors.append(f"Duplicate edge id: '{edge_id}'.")
            edge_ids.add(edge_id)

            # Check for orphaned edges
            source = edge.get("source")
            target = edge.get("target")
            if source and source not in node_ids:
                errors.append(f"Edge '{edge_id}' references non-existent source node '{source}'.")
            if target and target not in node_ids:
                errors.append(f"Edge '{edge_id}' references non-existent target node '{target}'.")

            # Check for self-loops
            if source and target and source == target:
                warnings.append(
                    f"Edge '{edge_id}' is a self-loop (source == target == '{source}')."
                )

        # 7. Check for disconnected nodes
        connected_node_ids = set()
        for edge in edges:
            if edge.get("source"):
                connected_node_ids.add(edge["source"])
            if edge.get("target"):
                connected_node_ids.add(edge["target"])

        disconnected = node_ids - connected_node_ids
        if disconnected and edges:
            warnings.append(f"Disconnected nodes (no edges): {sorted(disconnected)}")

        # 8. Schema conformance validation
        schema = tool_context.state.get("input_schema") or tool_context.state.get("schema")
        schema_source = "input" if tool_context.state.get("input_schema") else "generated"
        if schema:
            schema_errors, schema_warnings = _validate_against_schema(
                nodes, edges, schema, schema_source
            )
            errors.extend(schema_errors)
            warnings.extend(schema_warnings)

        # 9. Confidence warnings
        for node in nodes:
            if node.get("confidence") == "low":
                warnings.append(f"Node '{node.get('id')}' has LOW confidence — review manually.")
        for edge in edges:
            if edge.get("confidence") == "low":
                warnings.append(f"Edge '{edge.get('id')}' has LOW confidence — review manually.")

        return _format_report(
            errors, warnings, len(nodes), len(edges), schema_source if schema else None
        )

    except Exception as e:
        return log_tool_error("validate_graph", e)


def _validate_against_schema(
    nodes: list[dict],
    edges: list[dict],
    schema: dict,
    schema_source: str,
) -> tuple[list[str], list[str]]:
    """Validate nodes and edges against a JSON Schema."""
    errors = []
    warnings = []

    # Validate nodes against schema (resolves $ref for Pydantic schemas)
    node_items = resolve_items(schema, "nodes")
    if node_items:
        node_required = set(node_items.get("required", []))
        node_props = node_items.get("properties", {})

        for node in nodes:
            node_id = node.get("id", "?")
            provided = set(node.keys())

            # Check required fields from schema
            missing = node_required - provided
            if missing:
                errors.append(
                    f"Node '{node_id}' missing schema-required fields: {sorted(missing)} "
                    f"(from {schema_source} schema)"
                )

            # Check for type mismatches on provided fields
            for field_name, field_value in node.items():
                if field_name in node_props and field_value is not None:
                    expected_type = node_props[field_name].get("type")
                    if expected_type and not _type_matches(field_value, expected_type):
                        warnings.append(
                            f"Node '{node_id}' field '{field_name}': "
                            f"expected type '{expected_type}', got '{type(field_value).__name__}'"
                        )

    # Validate edges against schema (resolves $ref for Pydantic schemas)
    edge_items = resolve_items(schema, "edges")
    if edge_items:
        edge_required = set(edge_items.get("required", []))
        edge_props = edge_items.get("properties", {})

        for edge in edges:
            edge_id = edge.get("id", "?")
            provided = set(edge.keys())

            # Check required fields from schema
            missing = edge_required - provided
            if missing:
                errors.append(
                    f"Edge '{edge_id}' missing schema-required fields: {sorted(missing)} "
                    f"(from {schema_source} schema)"
                )

            # Check for type mismatches on provided fields
            for field_name, field_value in edge.items():
                if field_name in edge_props and field_value is not None:
                    expected_type = edge_props[field_name].get("type")
                    if expected_type and not _type_matches(field_value, expected_type):
                        warnings.append(
                            f"Edge '{edge_id}' field '{field_name}': "
                            f"expected type '{expected_type}', got '{type(field_value).__name__}'"
                        )

    return errors, warnings


def _type_matches(value, json_type: str) -> bool:
    """Check if a Python value matches a JSON Schema type."""
    type_map = {
        "string": str,
        "integer": int,
        "number": (int, float),
        "boolean": bool,
        "array": list,
        "object": dict,
    }
    expected = type_map.get(json_type)
    if expected is None:
        return True  # Unknown type, skip check
    return isinstance(value, expected)


def _format_report(
    errors: list[str],
    warnings: list[str],
    node_count: int = 0,
    edge_count: int = 0,
    schema_source: str | None = None,
) -> str:
    """Format validation results into a readable report."""
    lines = ["Graph Validation Report", "=" * 30]

    lines.append(f"Nodes: {node_count}, Edges: {edge_count}")
    if schema_source:
        lines.append(f"Schema: {schema_source}")
    else:
        lines.append("Schema: none (structural validation only)")
    lines.append("")

    if not errors and not warnings:
        lines.append("PASSED: Graph is valid. No errors or warnings.")
        return "\n".join(lines)

    if errors:
        lines.append(f"ERRORS ({len(errors)}):")
        for err in errors:
            lines.append(f"  - {err}")
        lines.append("")

    if warnings:
        lines.append(f"WARNINGS ({len(warnings)}):")
        for warn in warnings:
            lines.append(f"  - {warn}")
        lines.append("")

    if errors:
        lines.append("FAILED: Fix the errors above before exporting.")
    else:
        lines.append("PASSED with warnings: Graph is structurally valid but has warnings.")

    return "\n".join(lines)


def _detect_bbox_swap(nodes: list[dict], image_dimensions: dict) -> bool:
    """Detect if bounding box coordinates have x/y swapped.

    Uses two complementary signals:

    1. **Element aspect ratios** (non-group nodes): For each node, compute its
       pixel-space aspect ratio under both interpretations ([y,x,y,x] vs [x,y,x,y]).
       The correct interpretation should produce ratios closer to 1.0 (square-ish).

    2. **Group extreme ratios**: Group nodes (which span many children) have very
       different x/y spans. Under the wrong interpretation they produce physically
       implausible aspect ratios (>7:1). This catches cases where individual nodes
       are nearly square in normalized space and the element signal is ambiguous.

    Swap is triggered if:
    - The element signal strongly indicates swap (>20% better), OR
    - The group signal indicates swap AND the element signal at least leans that way
      (swapped median ≤ normal median). This guard prevents false positives on
      diagrams with legitimately wide/tall groups.

    Only applies to non-square images where the swap produces a measurable difference.
    """
    img_w = image_dimensions.get("width", 0)
    img_h = image_dimensions.get("height", 0)

    if not img_w or not img_h:
        return False

    # Need at least 10% aspect ratio difference to detect swap reliably
    if 0.9 < img_w / img_h < 1.1:
        return False

    # --- Signal 1: Non-group element aspect ratios ---
    normal_devs = []
    swapped_devs = []

    for node in nodes:
        bbox = node.get("bounding_box")
        if not bbox or len(bbox) != 4 or node.get("shape") == "group_rectangle":
            continue

        a, b, c, d = bbox
        if c <= a or d <= b:
            continue

        # Normal [y_min, x_min, y_max, x_max]
        n_h = (c - a) / 1000 * img_h
        n_w = (d - b) / 1000 * img_w
        # Swapped [x_min, y_min, x_max, y_max]
        s_h = (d - b) / 1000 * img_h
        s_w = (c - a) / 1000 * img_w

        if n_w > 0 and n_h > 0:
            normal_devs.append(abs(math.log(n_h / n_w)))
        if s_w > 0 and s_h > 0:
            swapped_devs.append(abs(math.log(s_h / s_w)))

    element_swap = False
    element_leans_swap = False
    if len(normal_devs) >= 3:
        normal_devs.sort()
        swapped_devs.sort()
        mid = len(normal_devs) // 2
        normal_median = normal_devs[mid]
        swapped_median = swapped_devs[mid]
        # Strong signal: swapped is at least 20% better
        element_swap = swapped_median < normal_median * 0.8
        # Weak signal: swapped is at least marginally better (guard for group signal)
        element_leans_swap = swapped_median < normal_median

    # --- Signal 2: Group extreme aspect ratios ---
    # Groups span multiple children and have large x/y differences, making them
    # sensitive to swap even when individual elements are nearly square.
    # IMPORTANT: This signal alone can false-positive on diagrams with legitimately
    # wide horizontal groups (e.g., top-to-bottom flow in landscape images), so it
    # requires the element signal to at least lean toward swap.
    extreme_threshold = math.log(7)  # |log(h/w)| > log(7) ≈ 1.95 means >7:1 ratio
    normal_extreme = 0
    swapped_extreme = 0
    group_count = 0

    for node in nodes:
        if node.get("shape") != "group_rectangle":
            continue
        bbox = node.get("bounding_box")
        if not bbox or len(bbox) != 4:
            continue
        a, b, c, d = bbox
        if c <= a or d <= b:
            continue

        group_count += 1
        n_h = (c - a) / 1000 * img_h
        n_w = (d - b) / 1000 * img_w
        s_h = (d - b) / 1000 * img_h
        s_w = (c - a) / 1000 * img_w

        if n_w > 0 and n_h > 0 and abs(math.log(n_h / n_w)) > extreme_threshold:
            normal_extreme += 1
        if s_w > 0 and s_h > 0 and abs(math.log(s_h / s_w)) > extreme_threshold:
            swapped_extreme += 1

    group_swap = (
        group_count >= 2
        and normal_extreme > swapped_extreme
        and normal_extreme >= 2
    )

    # Element signal alone is sufficient. Group signal requires element agreement.
    return element_swap or (group_swap and element_leans_swap)
