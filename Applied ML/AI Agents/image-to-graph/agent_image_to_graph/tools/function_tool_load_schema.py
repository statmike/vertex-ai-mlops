import json
import os
from google.adk import tools
from .schema_utils import resolve_items


async def load_schema(file_path: str, tool_context: tools.ToolContext) -> str:
    """
    Load a JSON Schema from a file to use as the target schema for graph construction.

    When a schema is loaded, the agent will build the graph to conform to it —
    ensuring nodes and edges include the fields and types the schema requires.
    The schema is stored in tool_context.state['input_schema'] and will be used
    by validate_graph and export_result.

    Supports both hand-written schemas and Pydantic-generated schemas (with $defs/$ref).

    Args:
        file_path: The absolute or relative path to a JSON Schema file.
        tool_context: The ADK tool context for accessing shared state.

    Returns:
        A summary of the loaded schema including required node/edge fields,
        or an error message if loading fails.
    """
    try:
        expanded_path = os.path.expanduser(file_path)

        if not os.path.exists(expanded_path):
            return f"Error: File not found at '{file_path}'."

        with open(expanded_path, 'r') as f:
            schema = json.load(f)

        # Basic validation — check it looks like a JSON Schema
        if not isinstance(schema, dict):
            return "Error: Schema file must contain a JSON object."

        # Store as the input schema
        tool_context.state['input_schema'] = schema
        # Also set as the active schema (used by validate and export)
        tool_context.state['schema'] = schema

        # Extract useful info for the agent (resolving $ref if needed)
        summary_lines = [
            f"Schema loaded from: {file_path}",
            f"  Title: {schema.get('title', 'N/A')}",
            f"  Description: {schema.get('description', 'N/A')}",
        ]

        # Parse node schema (resolves $ref for Pydantic schemas)
        node_items = resolve_items(schema, 'nodes')
        if node_items:
            node_props = node_items.get('properties', {})
            node_required = node_items.get('required', [])
            summary_lines.append(f"\n  Node fields: {list(node_props.keys())}")
            summary_lines.append(f"  Node required: {node_required}")

        # Parse edge schema (resolves $ref for Pydantic schemas)
        edge_items = resolve_items(schema, 'edges')
        if edge_items:
            edge_props = edge_items.get('properties', {})
            edge_required = edge_items.get('required', [])
            summary_lines.append(f"\n  Edge fields: {list(edge_props.keys())}")
            summary_lines.append(f"  Edge required: {edge_required}")

        summary_lines.append(
            "\nThe graph will be built to conform to this schema. "
            "Use validate_graph to check conformance at any time."
        )

        return '\n'.join(summary_lines)

    except json.JSONDecodeError as e:
        return f"Error: Invalid JSON in schema file: {str(e)}"
    except Exception as e:
        return f"Error loading schema: {str(e)}"
