import json
from google.adk import tools
from .schema_utils import resolve_items


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
        graph = tool_context.state.get('graph')
        if graph is None:
            return "Error: No graph state found. Use load_image first."

        nodes = graph.get('nodes', [])
        edges = graph.get('edges', [])

        errors = []
        warnings = []

        # 1. Check diagram type is set
        if not graph.get('diagram_type'):
            warnings.append("Diagram type is not set.")

        # 2. Check for empty graph
        if not nodes and not edges:
            errors.append("Graph is empty — no nodes or edges.")
            return _format_report(errors, warnings)

        # 3. Validate nodes — structural
        node_ids = set()
        for i, node in enumerate(nodes):
            node_id = node.get('id')
            if not node_id:
                errors.append(f"Node at index {i} is missing required field 'id'.")
                continue
            if not node.get('label'):
                errors.append(f"Node '{node_id}' is missing required field 'label'.")
            if node_id in node_ids:
                errors.append(f"Duplicate node id: '{node_id}'.")
            node_ids.add(node_id)

        # 4. Validate edges — structural
        edge_ids = set()
        for i, edge in enumerate(edges):
            edge_id = edge.get('id')
            if not edge_id:
                errors.append(f"Edge at index {i} is missing required field 'id'.")
                continue
            if not edge.get('source'):
                errors.append(f"Edge '{edge_id}' is missing required field 'source'.")
            if not edge.get('target'):
                errors.append(f"Edge '{edge_id}' is missing required field 'target'.")
            if edge_id in edge_ids:
                errors.append(f"Duplicate edge id: '{edge_id}'.")
            edge_ids.add(edge_id)

            # Check for orphaned edges
            source = edge.get('source')
            target = edge.get('target')
            if source and source not in node_ids:
                errors.append(f"Edge '{edge_id}' references non-existent source node '{source}'.")
            if target and target not in node_ids:
                errors.append(f"Edge '{edge_id}' references non-existent target node '{target}'.")

            # Check for self-loops
            if source and target and source == target:
                warnings.append(f"Edge '{edge_id}' is a self-loop (source == target == '{source}').")

        # 5. Check for disconnected nodes
        connected_node_ids = set()
        for edge in edges:
            if edge.get('source'):
                connected_node_ids.add(edge['source'])
            if edge.get('target'):
                connected_node_ids.add(edge['target'])

        disconnected = node_ids - connected_node_ids
        if disconnected and edges:
            warnings.append(f"Disconnected nodes (no edges): {sorted(disconnected)}")

        # 6. Schema conformance validation
        schema = tool_context.state.get('input_schema') or tool_context.state.get('schema')
        schema_source = "input" if tool_context.state.get('input_schema') else "generated"
        if schema:
            schema_errors, schema_warnings = _validate_against_schema(
                nodes, edges, schema, schema_source
            )
            errors.extend(schema_errors)
            warnings.extend(schema_warnings)

        # 7. Confidence warnings
        for node in nodes:
            if node.get('confidence') == 'low':
                warnings.append(f"Node '{node.get('id')}' has LOW confidence — review manually.")
        for edge in edges:
            if edge.get('confidence') == 'low':
                warnings.append(f"Edge '{edge.get('id')}' has LOW confidence — review manually.")

        return _format_report(errors, warnings, len(nodes), len(edges), schema_source if schema else None)

    except Exception as e:
        return f"Error validating graph: {str(e)}"


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
    node_items = resolve_items(schema, 'nodes')
    if node_items:
        node_required = set(node_items.get('required', []))
        node_props = node_items.get('properties', {})

        for node in nodes:
            node_id = node.get('id', '?')
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
                    expected_type = node_props[field_name].get('type')
                    if expected_type and not _type_matches(field_value, expected_type):
                        warnings.append(
                            f"Node '{node_id}' field '{field_name}': "
                            f"expected type '{expected_type}', got '{type(field_value).__name__}'"
                        )

    # Validate edges against schema (resolves $ref for Pydantic schemas)
    edge_items = resolve_items(schema, 'edges')
    if edge_items:
        edge_required = set(edge_items.get('required', []))
        edge_props = edge_items.get('properties', {})

        for edge in edges:
            edge_id = edge.get('id', '?')
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
                    expected_type = edge_props[field_name].get('type')
                    if expected_type and not _type_matches(field_value, expected_type):
                        warnings.append(
                            f"Edge '{edge_id}' field '{field_name}': "
                            f"expected type '{expected_type}', got '{type(field_value).__name__}'"
                        )

    return errors, warnings


def _type_matches(value, json_type: str) -> bool:
    """Check if a Python value matches a JSON Schema type."""
    type_map = {
        'string': str,
        'integer': int,
        'number': (int, float),
        'boolean': bool,
        'array': list,
        'object': dict,
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
        return '\n'.join(lines)

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

    return '\n'.join(lines)
