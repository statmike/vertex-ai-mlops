import json
from google.adk import tools


async def update_graph(
    operations: list[dict],
    tool_context: tools.ToolContext,
) -> str:
    """
    Update the graph state with one or more operations in a single call.

    Each operation is a dict with an "op" field and a "data" field.
    Supported ops: add_node, update_node, add_edge, update_edge, set_diagram_type.

    Use this to batch multiple additions in one call. For example, after examining
    a region, add all discovered nodes at once instead of one at a time.

    Args:
        operations: A list of operation dicts, each with:
                    {"op": "add_node", "data": {"id": str, "label": str, ...}}
                    {"op": "update_node", "data": {"id": str, ...fields to update}}
                    {"op": "add_edge", "data": {"id": str, "source": str, "target": str, ...}}
                    {"op": "update_edge", "data": {"id": str, ...fields to update}}
                    {"op": "set_diagram_type", "data": {"diagram_type": str}}
        tool_context: The ADK tool context containing the graph in state.

    Returns:
        A summary of all operations performed, with any errors or warnings.
    """
    try:
        graph = tool_context.state.get('graph')
        if graph is None:
            return "Error: No graph state found. Use load_image first to initialize."

        results = []
        schema_hints_given = False

        for i, op_dict in enumerate(operations):
            op = op_dict.get('op', '')
            data = op_dict.get('data', {})

            if op == 'set_diagram_type':
                diagram_type = data.get('diagram_type')
                if not diagram_type:
                    results.append(f"[{i}] Error: 'diagram_type' required.")
                    continue
                graph['diagram_type'] = diagram_type
                results.append(f"[{i}] Diagram type: '{diagram_type}'")

            elif op == 'add_node':
                node_id = data.get('id')
                label = data.get('label')
                if not node_id:
                    results.append(f"[{i}] Error: 'id' required for add_node.")
                    continue
                if not label:
                    results.append(f"[{i}] Error: 'label' required for add_node.")
                    continue

                existing_ids = {n['id'] for n in graph.get('nodes', [])}
                if node_id in existing_ids:
                    results.append(f"[{i}] Skipped: node '{node_id}' already exists.")
                    continue

                graph.setdefault('nodes', []).append(dict(data))
                results.append(f"[{i}] + node '{node_id}' (\"{label}\")")

                # Schema hint (only once per call to stay concise)
                if not schema_hints_given:
                    hint = _schema_field_hint(tool_context, 'nodes', data)
                    if hint:
                        results.append(f"    {hint}")
                        schema_hints_given = True

            elif op == 'update_node':
                node_id = data.get('id')
                if not node_id:
                    results.append(f"[{i}] Error: 'id' required for update_node.")
                    continue
                found = False
                for node in graph.get('nodes', []):
                    if node['id'] == node_id:
                        for key, value in data.items():
                            node[key] = value
                        found = True
                        break
                if found:
                    results.append(f"[{i}] ~ node '{node_id}' updated")
                else:
                    results.append(f"[{i}] Error: node '{node_id}' not found.")

            elif op == 'add_edge':
                edge_id = data.get('id')
                source = data.get('source')
                target = data.get('target')
                if not edge_id:
                    results.append(f"[{i}] Error: 'id' required for add_edge.")
                    continue
                if not source or not target:
                    results.append(f"[{i}] Error: 'source' and 'target' required for add_edge.")
                    continue

                existing_ids = {e['id'] for e in graph.get('edges', [])}
                if edge_id in existing_ids:
                    results.append(f"[{i}] Skipped: edge '{edge_id}' already exists.")
                    continue

                node_ids = {n['id'] for n in graph.get('nodes', [])}
                warn = ""
                if source not in node_ids:
                    warn += f" (source '{source}' not found)"
                if target not in node_ids:
                    warn += f" (target '{target}' not found)"

                graph.setdefault('edges', []).append(dict(data))
                results.append(f"[{i}] + edge '{edge_id}' ({source} -> {target}){warn}")

                if not schema_hints_given:
                    hint = _schema_field_hint(tool_context, 'edges', data)
                    if hint:
                        results.append(f"    {hint}")
                        schema_hints_given = True

            elif op == 'update_edge':
                edge_id = data.get('id')
                if not edge_id:
                    results.append(f"[{i}] Error: 'id' required for update_edge.")
                    continue
                found = False
                for edge in graph.get('edges', []):
                    if edge['id'] == edge_id:
                        for key, value in data.items():
                            edge[key] = value
                        found = True
                        break
                if found:
                    results.append(f"[{i}] ~ edge '{edge_id}' updated")
                else:
                    results.append(f"[{i}] Error: edge '{edge_id}' not found.")

            else:
                results.append(
                    f"[{i}] Error: unknown op '{op}'. "
                    f"Valid: add_node, update_node, add_edge, update_edge, set_diagram_type."
                )

        tool_context.state['graph'] = graph

        node_count = len(graph.get('nodes', []))
        edge_count = len(graph.get('edges', []))
        summary = f"Batch update: {len(operations)} ops. Graph: {node_count} nodes, {edge_count} edges.\n"
        summary += '\n'.join(results)
        return summary

    except Exception as e:
        return f"Error updating graph: {str(e)}"


def _schema_field_hint(tool_context: tools.ToolContext, element_type: str, data: dict) -> str:
    """Check input_schema for required/expected fields missing from data."""
    from .schema_utils import resolve_items

    input_schema = tool_context.state.get('input_schema')
    if not input_schema:
        return ""

    items_schema = resolve_items(input_schema, element_type)
    if not items_schema:
        return ""

    schema_required = set(items_schema.get('required', []))
    schema_props = set(items_schema.get('properties', {}).keys())
    provided = set(data.keys())

    missing_required = schema_required - provided
    missing_optional = (schema_props - schema_required) - provided

    parts = []
    if missing_required:
        parts.append(f"Schema hint — missing REQUIRED fields: {sorted(missing_required)}")
    if missing_optional:
        parts.append(f"Schema hint — available optional fields: {sorted(missing_optional)}")

    return '\n'.join(parts)
