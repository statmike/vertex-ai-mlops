import logging
from typing import Any

from google.adk import tools
from pydantic import Field, create_model

from .util_common import log_tool_error

logger = logging.getLogger(__name__)


async def generate_schema(tool_context: tools.ToolContext) -> str:
    """
    Generate a JSON Schema from the current graph structure.

    Analyzes the nodes and edges in the current graph to infer Pydantic models
    based on observed attributes. Outputs a JSON Schema that can be used for
    validation. Stores the schema in tool_context.state['schema'].

    Args:
        tool_context: The ADK tool context containing the graph in state.

    Returns:
        A JSON Schema string describing the graph structure,
        or an error message if generation fails.
    """
    try:
        # If an input schema was provided, use it instead of generating
        input_schema = tool_context.state.get("input_schema")
        if input_schema:
            return (
                f"An input schema is already loaded (title: '{input_schema.get('title', 'N/A')}').\n"
                f"The graph is being built to conform to this schema.\n"
                f"Use validate_graph to check conformance.\n\n"
                f"To generate a new schema from the current graph instead, "
                f"clear the input schema first by calling load_image again."
            )

        graph = tool_context.state.get("graph")
        if graph is None:
            return "Error: No graph state found. Use load_image first."

        nodes = graph.get("nodes", [])
        edges = graph.get("edges", [])

        if not nodes and not edges:
            return "Error: Graph is empty. Add nodes and edges before generating a schema."

        # Collect all observed node attributes and their types
        node_fields: dict[str, set[str]] = {}
        for node in nodes:
            for key, value in node.items():
                if key not in node_fields:
                    node_fields[key] = set()
                node_fields[key].add(type(value).__name__)

        # Collect all observed edge attributes and their types
        edge_fields: dict[str, set[str]] = {}
        for edge in edges:
            for key, value in edge.items():
                if key not in edge_fields:
                    edge_fields[key] = set()
                edge_fields[key].add(type(value).__name__)

        def _infer_python_type(type_names: set[str]) -> Any:
            """Map observed Python type names to annotation types."""
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
            else:
                return Any

        # Build node field definitions for Pydantic
        required_node_fields = {"id", "label"}
        node_model_fields = {}
        for field_name, type_names in node_fields.items():
            python_type = _infer_python_type(type_names)
            if field_name in required_node_fields:
                node_model_fields[field_name] = (
                    python_type,
                    Field(..., description=f"Node {field_name}"),
                )
            else:
                node_model_fields[field_name] = (
                    python_type | None,
                    Field(None, description=f"Node {field_name}"),
                )

        # Build edge field definitions for Pydantic
        required_edge_fields = {"id", "source", "target"}
        edge_model_fields = {}
        for field_name, type_names in edge_fields.items():
            python_type = _infer_python_type(type_names)
            if field_name in required_edge_fields:
                edge_model_fields[field_name] = (
                    python_type,
                    Field(..., description=f"Edge {field_name}"),
                )
            else:
                edge_model_fields[field_name] = (
                    python_type | None,
                    Field(None, description=f"Edge {field_name}"),
                )

        # Create dynamic Pydantic models
        NodeModel = create_model("GraphNode", **node_model_fields)
        EdgeModel = create_model("GraphEdge", **edge_model_fields)

        # Build the full graph schema
        graph_schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "title": "DiagramGraph",
            "description": f"Schema for a {graph.get('diagram_type', 'diagram')} graph",
            "type": "object",
            "properties": {
                "diagram_type": {"type": "string", "description": "The type of diagram"},
                "nodes": {
                    "type": "array",
                    "items": NodeModel.model_json_schema(),
                    "description": "List of graph nodes",
                },
                "edges": {
                    "type": "array",
                    "items": EdgeModel.model_json_schema(),
                    "description": "List of graph edges",
                },
                "flows": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string", "description": "Flow identifier"},
                            "label": {"type": "string", "description": "Human-readable flow name"},
                            "node_ids": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Node IDs belonging to this flow",
                            },
                        },
                        "required": ["id", "label", "node_ids"],
                    },
                    "description": "Distinct flows (connected components) detected in the diagram",
                },
                "metadata": {
                    "type": "object",
                    "description": "Additional metadata about the graph",
                    "properties": {
                        "page_info": {
                            "type": "object",
                            "description": "Page-level metadata (title, author, date, version)",
                            "properties": {
                                "title": {"type": "string"},
                                "author": {"type": "string"},
                                "date": {"type": "string"},
                                "version": {"type": "string"},
                            },
                        },
                        "legend": {
                            "type": "array",
                            "description": "Legend entries mapping symbols to meanings",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "symbol": {"type": "string"},
                                    "meaning": {"type": "string"},
                                },
                            },
                        },
                    },
                },
            },
            "required": ["diagram_type", "nodes", "edges"],
        }

        # Store in state
        tool_context.state["schema"] = graph_schema

        return (
            f"Schema generated successfully.\n"
            f"  Node attributes: {list(node_fields.keys())}\n"
            f"  Node required: {list(required_node_fields)}\n"
            f"  Edge attributes: {list(edge_fields.keys())}\n"
            f"  Edge required: {list(required_edge_fields)}\n"
            f"Schema stored in state. Use validate_graph to check conformance, "
            f"or export_result to save as schema.json artifact."
        )

    except Exception as e:
        return log_tool_error("generate_schema", e)
