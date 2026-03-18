import logging
import math

from google.adk import tools

from ..config import DIAGRAM_TYPE_CONFIG
from .util_bbox import (
    detect_schematic_mode,
    fix_oversized_bboxes,
    fix_schematic_bboxes,
    match_cv_to_graph_elements,
)
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
        source_image = tool_context.state.get("source_image")
        source_image_bytes = None
        if source_image:
            try:
                import base64
                source_image_bytes = base64.b64decode(source_image)
            except Exception:
                pass
        swap_needed = _detect_bbox_swap(
            nodes, image_dimensions, source_image_bytes,
        )
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

        # 4b. Check for degenerate bounding boxes (zero width or height)
        for node in nodes:
            bbox = node.get("bounding_box")
            node_id = node.get("id", "?")
            if bbox and len(bbox) == 4:
                y_min_b, x_min_b, y_max_b, x_max_b = bbox
                if y_min_b == y_max_b:
                    warnings.append(
                        f"Node '{node_id}' has zero-height bounding_box {bbox} "
                        f"(top == bottom == {y_min_b})."
                    )
                if x_min_b == x_max_b:
                    warnings.append(
                        f"Node '{node_id}' has zero-width bounding_box {bbox} "
                        f"(left == right == {x_min_b})."
                    )

        # 4c. Refine bounding boxes using CV preprocessing data (if available)
        cv_data = tool_context.state.get("cv_preprocessing")
        nudge_count = _refine_bboxes_from_cv(nodes, cv_data, warnings)
        if nudge_count:
            tool_context.state["graph"] = graph
            prev = list(tool_context.state.get("bbox_corrections", []))
            prev.append({
                "tool": "validate_graph",
                "op": "cv_refinement",
                "nudge_count": nudge_count,
            })
            tool_context.state["bbox_corrections"] = prev

        # 4d. Schematic-specific bbox normalization (if detected)
        is_schematic_diagram = detect_schematic_mode(graph, nodes)
        if is_schematic_diagram:
            corrections = fix_schematic_bboxes(nodes)
            if corrections:
                tool_context.state["graph"] = graph
                warnings.append(
                    f"Schematic mode: {len(corrections)} degenerate "
                    f"bounding boxes normalized to component-sized regions."
                )
                prev = list(tool_context.state.get("bbox_corrections", []))
                prev.append({
                    "tool": "validate_graph",
                    "op": "schematic_bbox_normalization",
                    "correction_count": len(corrections),
                })
                tool_context.state["bbox_corrections"] = prev

        # 4e. General oversized bbox guard (all diagram types)
        type_key = "schematic" if is_schematic_diagram else "default"
        type_cfg = DIAGRAM_TYPE_CONFIG.get(type_key, DIAGRAM_TYPE_CONFIG["default"])
        oversized_threshold = type_cfg["oversized_bbox_threshold"]
        oversized_corrections = fix_oversized_bboxes(nodes, area_threshold=oversized_threshold)
        if oversized_corrections:
            tool_context.state["graph"] = graph
            pct = int(oversized_threshold * 100)
            warnings.append(
                f"Oversized bbox guard: {len(oversized_corrections)} node bounding "
                f"boxes exceeding {pct}% of image area shrunk to component size."
            )
            prev = list(tool_context.state.get("bbox_corrections", []))
            prev.append({
                "tool": "validate_graph",
                "op": "oversized_bbox_guard",
                "correction_count": len(oversized_corrections),
            })
            tool_context.state["bbox_corrections"] = prev

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

        # 5b. Check child bboxes are inside their parent group bbox
        for gid, child_ids in children_of.items():
            group_node = node_by_id.get(gid)
            if not group_node:
                continue
            gbbox = group_node.get("bounding_box")
            if not gbbox or len(gbbox) != 4:
                continue
            gy_min, gx_min, gy_max, gx_max = gbbox
            for cid in child_ids:
                child_node = node_by_id.get(cid)
                if not child_node:
                    continue
                cbbox = child_node.get("bounding_box")
                if not cbbox or len(cbbox) != 4:
                    continue
                cy_min, cx_min, cy_max, cx_max = cbbox
                # Child entirely outside parent on any axis
                if cy_max <= gy_min or cy_min >= gy_max or cx_max <= gx_min or cx_min >= gx_max:
                    warnings.append(
                        f"Node '{cid}' bbox {cbbox} is entirely outside its parent "
                        f"group '{gid}' bbox {gbbox}."
                    )

        # 5c. Check for near-zero area bboxes (width or height < 3 in normalized 0-1000)
        for node in nodes:
            bbox = node.get("bounding_box")
            node_id = node.get("id", "?")
            if bbox and len(bbox) == 4 and node.get("shape") != "group_rectangle":
                y_min_b, x_min_b, y_max_b, x_max_b = bbox
                width = x_max_b - x_min_b
                height = y_max_b - y_min_b
                if 0 < width < 3 or 0 < height < 3:
                    warnings.append(
                        f"Node '{node_id}' has near-zero area bounding_box {bbox} "
                        f"(width={width}, height={height})."
                    )

        # 5d. Detect significantly overlapping non-group bboxes
        non_group_with_bbox = [
            n for n in nodes
            if n.get("shape") != "group_rectangle"
            and n.get("bounding_box") and len(n.get("bounding_box", [])) == 4
        ]
        for i, na in enumerate(non_group_with_bbox):
            ba = na["bounding_box"]
            area_a = (ba[2] - ba[0]) * (ba[3] - ba[1])
            if area_a <= 0:
                continue
            for nb in non_group_with_bbox[i + 1:]:
                bb = nb["bounding_box"]
                area_b = (bb[2] - bb[0]) * (bb[3] - bb[1])
                if area_b <= 0:
                    continue
                # Intersection
                iy = max(0, min(ba[2], bb[2]) - max(ba[0], bb[0]))
                ix = max(0, min(ba[3], bb[3]) - max(ba[1], bb[1]))
                inter = iy * ix
                if inter <= 0:
                    continue
                containment = inter / min(area_a, area_b)
                if containment > 0.7:
                    pct = int(containment * 100)
                    warnings.append(
                        f"Nodes '{na.get('id', '?')}' and '{nb.get('id', '?')}' bboxes "
                        f"significantly overlap ({pct}% containment)."
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

        # 7. Detect flows (connected components) and check disconnected nodes
        flows = _compute_flows(nodes, edges)
        if len(flows) >= 2:
            # Multi-flow diagram: store flows and assign flow_id to nodes
            graph["flows"] = flows
            flow_lookup = {}
            for flow in flows:
                for nid in flow["node_ids"]:
                    flow_lookup[nid] = flow["id"]
            for node in nodes:
                nid = node.get("id")
                if nid and nid in flow_lookup:
                    node["flow_id"] = flow_lookup[nid]
            warnings.append(f"Diagram contains {len(flows)} distinct flows.")
            tool_context.state["graph"] = graph

            # Auto-detect label-based cross-references between flows
            label_to_flows: dict[str, list[str]] = {}
            for node in nodes:
                label = node.get("label", "")
                nid = node.get("id", "")
                fid = node.get("flow_id", "")
                if label and fid:
                    label_to_flows.setdefault(label, []).append(fid)
            for label, fids in label_to_flows.items():
                unique_flows = sorted(set(fids))
                if len(unique_flows) >= 2:
                    warnings.append(
                        f"Cross-reference candidate: label \"{label}\" appears in "
                        f"flows {unique_flows}. Consider adding 'reference' edges."
                    )
        else:
            # Single flow: standard disconnected node check
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


def _detect_bbox_swap(
    nodes: list[dict],
    image_dimensions: dict,
    source_image_bytes: bytes | None = None,
) -> bool:
    """Detect if bounding box coordinates have x/y swapped.

    Uses three complementary signals:

    1. **Element aspect ratios** (non-group nodes): For each node, compute its
       pixel-space aspect ratio under both interpretations ([y,x,y,x] vs [x,y,x,y]).
       The correct interpretation should produce ratios closer to 1.0 (square-ish).

    2. **Group extreme ratios**: Group nodes (which span many children) have very
       different x/y spans. Under the wrong interpretation they produce physically
       implausible aspect ratios (>7:1). This catches cases where individual nodes
       are nearly square in normalized space and the element signal is ambiguous.

    3. **Content verification** (requires source_image_bytes): Samples bbox center
       pixels under both interpretations and checks which one hits actual diagram
       content (non-white pixels). This is ground truth — it catches swaps that
       the heuristic signals miss, such as schematics with small near-square
       components on non-square images.

    Swap is triggered if:
    - The element signal strongly indicates swap (>20% better), OR
    - The group signal indicates swap AND the element signal does not strongly
      oppose (normal median must not be more than 40% better than swapped median).
    - The content signal strongly indicates swap (>70% of samples favor swap)
      AND the element signal does not strongly oppose swap.

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
    element_strongly_opposes_swap = False
    if len(normal_devs) >= 3:
        normal_devs.sort()
        swapped_devs.sort()
        mid = len(normal_devs) // 2
        normal_median = normal_devs[mid]
        swapped_median = swapped_devs[mid]
        # Strong signal: swapped is at least 20% better
        element_swap = swapped_median < normal_median * 0.8
        # Elements strongly oppose swap: normal is >40% better than swapped.
        # This blocks the group signal to prevent false positives on diagrams
        # with legitimately wide/tall groups.
        element_strongly_opposes_swap = (
            swapped_median > 0 and (normal_median / swapped_median) < 0.6
        )

    # --- Signal 2: Group extreme aspect ratios ---
    # Groups span multiple children and have large x/y differences, making them
    # sensitive to swap even when individual elements are nearly square.
    # IMPORTANT: This signal alone can false-positive on diagrams with legitimately
    # wide horizontal groups (e.g., top-to-bottom flow in landscape images), so it
    # requires the element signal to NOT strongly oppose swap.
    extreme_threshold = math.log(5)  # |log(h/w)| > log(5) ≈ 1.61 means >5:1 ratio
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

    # --- Signal 3: Content verification (ground truth) ---
    # Sample bbox centers under both interpretations and check which one
    # hits actual diagram content. This catches swaps that the heuristic
    # signals miss (e.g., schematics with small near-square components).
    content_swap = False
    if source_image_bytes and not element_swap:
        content_swap = _content_based_swap_check(
            nodes, img_w, img_h, source_image_bytes,
        )

    # Element signal alone is sufficient.
    # Group signal requires elements to NOT strongly oppose swap.
    # Content signal requires elements to NOT strongly oppose swap.
    return (
        element_swap
        or (group_swap and not element_strongly_opposes_swap)
        or (content_swap and not element_strongly_opposes_swap)
    )


def _content_based_swap_check(
    nodes: list[dict],
    img_w: int,
    img_h: int,
    source_image_bytes: bytes,
    sample_size: int = 12,
    threshold: float = 0.70,
) -> bool:
    """Check whether swapping bbox coordinates puts them on actual content.

    Samples up to *sample_size* non-group bbox centers and compares the mean
    pixel darkness at each center under normal vs swapped interpretations.
    Returns True if the swapped interpretation consistently hits darker
    (non-white) pixels, indicating the bboxes are currently x/y swapped.

    A pixel region is considered "content" if its mean grayscale value is
    below 240 (white = 255).  The function compares per-sample winners:
    if ≥ *threshold* of samples favor the swapped interpretation, returns True.
    """
    try:
        import io

        from PIL import Image
    except ImportError:
        return False

    try:
        img = Image.open(io.BytesIO(source_image_bytes)).convert("L")
    except Exception:
        return False

    actual_w, actual_h = img.size
    if actual_w == 0 or actual_h == 0:
        return False

    # Collect non-group bbox centers (normalized 0-1000)
    centers = []
    for node in nodes:
        bbox = node.get("bounding_box")
        if not bbox or len(bbox) != 4 or node.get("shape") == "group_rectangle":
            continue
        a, b, c, d = bbox
        if c <= a or d <= b:
            continue
        centers.append(((a + c) / 2, (b + d) / 2))

    if len(centers) < 4:
        return False

    # Sample evenly across the list to get spatial diversity
    step = max(1, len(centers) // sample_size)
    sampled = centers[::step][:sample_size]

    normal_hits = 0
    swapped_hits = 0
    patch_radius = 3  # sample a 7x7 patch around center

    for cy_norm, cx_norm in sampled:
        # Normal interpretation: [y_min, x_min, y_max, x_max]
        n_py = int(cy_norm / 1000 * actual_h)
        n_px = int(cx_norm / 1000 * actual_w)
        # Swapped interpretation: stored as [x_min, y_min, x_max, y_max]
        s_py = int(cx_norm / 1000 * actual_h)
        s_px = int(cy_norm / 1000 * actual_w)

        n_dark = _sample_darkness(img, n_px, n_py, patch_radius, actual_w, actual_h)
        s_dark = _sample_darkness(img, s_px, s_py, patch_radius, actual_w, actual_h)

        if n_dark > s_dark:
            normal_hits += 1
        elif s_dark > n_dark:
            swapped_hits += 1

    total = normal_hits + swapped_hits
    if total < 3:
        return False

    return swapped_hits / total >= threshold


def _sample_darkness(
    img: "Image.Image",  # noqa: F821
    cx: int,
    cy: int,
    radius: int,
    img_w: int,
    img_h: int,
) -> float:
    """Return mean darkness (255 - grayscale) of a small patch around (cx, cy)."""
    x0 = max(0, cx - radius)
    y0 = max(0, cy - radius)
    x1 = min(img_w, cx + radius + 1)
    y1 = min(img_h, cy + radius + 1)
    if x1 <= x0 or y1 <= y0:
        return 0.0
    patch = img.crop((x0, y0, x1, y1))
    pixel_bytes = patch.tobytes()
    if not pixel_bytes:
        return 0.0
    # Darkness = 255 - brightness. White (255) → 0 darkness. Black (0) → 255.
    return sum(255 - p for p in pixel_bytes) / len(pixel_bytes)


def _refine_bboxes_from_cv(
    nodes: list[dict],
    cv_data: dict | None,
    warnings: list[str],
) -> int:
    """Match CV elements to graph nodes and nudge/flag bounding boxes.

    Returns the number of bboxes nudged.
    """
    if not cv_data or cv_data.get("status") not in ("complete", "partial"):
        return 0

    cv_elements = cv_data.get("elements", [])
    if not cv_elements:
        return 0

    matches = match_cv_to_graph_elements(cv_elements, nodes)

    nudge_count = 0
    node_by_id = {n["id"]: n for n in nodes if n.get("id")}

    for match in matches:
        node = node_by_id.get(match["node_id"])
        if not node:
            continue

        if match["action"] == "nudge":
            node["bounding_box"] = match["cv_bbox"]
            nudge_count += 1
        elif match["action"] == "flag":
            warnings.append(
                f"Node '{match['node_id']}' bbox may be misplaced "
                f"(best CV match score={match['combined_score']:.2f}, "
                f"IoU={match['iou_score']:.2f})."
            )

    if nudge_count:
        warnings.append(
            f"CV refinement: {nudge_count} node bounding boxes nudged to "
            f"pixel-precise positions from OpenCV detection."
        )

    return nudge_count


def _compute_flows(
    nodes: list[dict], edges: list[dict], min_component_size: int = 3,
) -> list[dict]:
    """Partition nodes into flows (connected components) using union-find.

    Small components (fewer than *min_component_size* nodes) are merged into the
    largest component instead of being treated as separate flows.  This prevents
    spurious multi-flow detection when a few edges happen to be missed.
    """
    node_ids = [n["id"] for n in nodes if n.get("id")]
    if not node_ids:
        return []

    parent = {nid: nid for nid in node_ids}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: str, b: str) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    for edge in edges:
        src, tgt = edge.get("source"), edge.get("target")
        if src in parent and tgt in parent:
            union(src, tgt)

    # Also union nodes with same parent_id (groups)
    for node in nodes:
        pid = node.get("parent_id")
        nid = node.get("id")
        if pid and pid in parent and nid and nid in parent:
            union(nid, pid)

    # Build component map
    components: dict[str, list[str]] = {}
    for nid in node_ids:
        root = find(nid)
        components.setdefault(root, []).append(nid)

    if not components:
        return []

    # Merge small components into the largest component
    largest_root = max(components, key=lambda r: len(components[r]))
    merged: dict[str, list[str]] = {}
    for root, members in components.items():
        if len(members) < min_component_size and root != largest_root:
            # Absorb into largest component
            merged.setdefault(largest_root, list(components[largest_root]))
            merged[largest_root].extend(members)
        else:
            merged.setdefault(root, list(members))

    # Sort by first appearance and assign flow IDs
    flows = []
    for i, (_root, members) in enumerate(
        sorted(merged.items(), key=lambda x: node_ids.index(x[0])), 1
    ):
        # De-duplicate (largest component may appear in initial + merged)
        seen = set()
        unique_members = []
        for m in members:
            if m not in seen:
                seen.add(m)
                unique_members.append(m)
        flows.append({
            "id": f"flow_{i}",
            "label": f"Flow {i}",
            "node_ids": sorted(unique_members),
        })
    return flows
