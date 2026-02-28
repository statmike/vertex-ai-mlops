import json
import logging
import os
from typing import Any

from google import genai
from google.adk import tools
from pydantic import Field, create_model

from .util_common import log_tool_error
from .util_output import get_results_dir

logger = logging.getLogger(__name__)


async def export_result(tool_context: tools.ToolContext) -> str:
    """
    Export the final graph and schema as artifacts.

    Marks the graph as complete and saves both graph.json and schema.json
    as artifacts via tool_context.save_artifact(). A schema is always exported:
    the user-provided input_schema if one was loaded, otherwise an auto-generated
    schema inferred from the graph structure.

    Args:
        tool_context: The ADK tool context containing graph and schema in state.

    Returns:
        A summary of the exported artifacts, or an error message if export fails.
    """
    try:
        graph = tool_context.state.get("graph")
        if graph is None:
            return "Error: No graph state found. Use load_image first."

        nodes = graph.get("nodes", [])
        edges = graph.get("edges", [])

        if not nodes:
            return (
                "Error: Graph has no nodes. Analyze the image and build the graph before exporting."
            )

        # Mark as complete
        graph["metadata"] = graph.get("metadata", {})
        graph["metadata"]["status"] = "complete"

        # Save graph.json artifact
        graph_json = json.dumps(graph, indent=2)
        graph_blob = genai.types.Part.from_bytes(
            data=graph_json.encode("utf-8"),
            mime_type="application/json",
        )
        await tool_context.save_artifact(filename="graph.json", artifact=graph_blob)

        # Ensure a schema exists — use input_schema, existing generated, or auto-generate
        schema = tool_context.state.get("input_schema") or tool_context.state.get("schema")
        schema_source = "input" if tool_context.state.get("input_schema") else "generated"

        if not schema:
            # Auto-generate schema from graph structure
            schema = _auto_generate_schema(graph, nodes, edges)
            schema_source = "auto-generated"
            tool_context.state["schema"] = schema

        # Always save schema.json artifact
        schema_json = json.dumps(schema, indent=2)
        schema_blob = genai.types.Part.from_bytes(
            data=schema_json.encode("utf-8"),
            mime_type="application/json",
        )
        await tool_context.save_artifact(filename="schema.json", artifact=schema_blob)

        # Save description.md artifact if description exists
        description = tool_context.state.get("diagram_description", "")
        has_description = False
        if description:
            desc_blob = genai.types.Part.from_bytes(
                data=description.encode("utf-8"),
                mime_type="text/markdown",
            )
            await tool_context.save_artifact(filename="description.md", artifact=desc_blob)
            has_description = True

        # Write files to disk alongside the source image
        results_dir = get_results_dir(tool_context)
        if results_dir:
            with open(os.path.join(results_dir, "graph.json"), "w") as f:
                f.write(graph_json)
            with open(os.path.join(results_dir, "schema.json"), "w") as f:
                f.write(schema_json)
            if has_description:
                with open(os.path.join(results_dir, "description.md"), "w") as f:
                    f.write(description)

        # Build summary
        node_types = {}
        for node in nodes:
            etype = node.get("element_type", "unknown")
            node_types[etype] = node_types.get(etype, 0) + 1

        summary_lines = [
            "Graph exported successfully!",
            "=" * 30,
            f"Diagram type: {graph.get('diagram_type', 'unknown')}",
            f"Total nodes: {len(nodes)}",
            f"Total edges: {len(edges)}",
            f"Schema: {schema_source}",
            "",
            "Node types:",
        ]
        for etype, count in sorted(node_types.items()):
            summary_lines.append(f"  {etype}: {count}")

        summary_lines.append("")
        summary_lines.append("Artifacts saved:")
        summary_lines.append("  - graph.json")
        summary_lines.append("  - schema.json")
        if has_description:
            summary_lines.append("  - description.md")

        if results_dir:
            summary_lines.append("")
            summary_lines.append(f"Files also written to: {results_dir}")

        return "\n".join(summary_lines)

    except Exception as e:
        return log_tool_error("export_result", e)


def _auto_generate_schema(graph: dict, nodes: list[dict], edges: list[dict]) -> dict:
    """Generate a JSON Schema from graph structure when none exists."""
    # Collect observed node attributes
    node_fields: dict[str, set[str]] = {}
    for node in nodes:
        for key, value in node.items():
            node_fields.setdefault(key, set()).add(type(value).__name__)

    # Collect observed edge attributes
    edge_fields: dict[str, set[str]] = {}
    for edge in edges:
        for key, value in edge.items():
            edge_fields.setdefault(key, set()).add(type(value).__name__)

    def _infer_type(type_names: set[str]) -> Any:
        if type_names == {"str"}:
            return str
        elif type_names == {"int"}:
            return int
        elif type_names == {"float"}:
            return float
        elif type_names == {"bool"}:
            return bool
        elif type_names <= {"int", "float"}:
            return float
        elif type_names == {"dict"}:
            return dict[str, Any]
        elif type_names == {"list"}:
            return list[Any]
        elif type_names == {"NoneType"}:
            return str | None
        return Any

    required_node = {"id", "label"}
    node_model_fields = {}
    for name, types in node_fields.items():
        pt = _infer_type(types)
        if name in required_node:
            node_model_fields[name] = (pt, Field(..., description=f"Node {name}"))
        else:
            node_model_fields[name] = (pt | None, Field(None, description=f"Node {name}"))

    required_edge = {"id", "source", "target"}
    edge_model_fields = {}
    for name, types in edge_fields.items():
        pt = _infer_type(types)
        if name in required_edge:
            edge_model_fields[name] = (pt, Field(..., description=f"Edge {name}"))
        else:
            edge_model_fields[name] = (pt | None, Field(None, description=f"Edge {name}"))

    NodeModel = create_model("GraphNode", **node_model_fields) if node_model_fields else None
    EdgeModel = create_model("GraphEdge", **edge_model_fields) if edge_model_fields else None

    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "DiagramGraph",
        "description": f"Auto-generated schema for a {graph.get('diagram_type', 'diagram')} graph",
        "type": "object",
        "properties": {
            "diagram_type": {"type": "string", "description": "The type of diagram"},
            "nodes": {
                "type": "array",
                "items": NodeModel.model_json_schema() if NodeModel else {"type": "object"},
                "description": "List of graph nodes",
            },
            "edges": {
                "type": "array",
                "items": EdgeModel.model_json_schema() if EdgeModel else {"type": "object"},
                "description": "List of graph edges",
            },
            "metadata": {
                "type": "object",
                "description": "Additional metadata about the graph",
            },
        },
        "required": ["diagram_type", "nodes", "edges"],
    }
