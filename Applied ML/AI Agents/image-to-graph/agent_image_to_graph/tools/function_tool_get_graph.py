import json
import logging

from google.adk import tools

from .util_common import log_tool_error

logger = logging.getLogger(__name__)


async def get_graph(tool_context: tools.ToolContext) -> str:
    """
    Return the current graph state as JSON.

    Retrieves the accumulated graph from tool_context.state and returns it
    formatted as JSON. Useful for the agent to review progress and decide
    what analysis steps remain.

    Args:
        tool_context: The ADK tool context containing the graph in state.

    Returns:
        A JSON string of the current graph state with summary statistics,
        or an error message if no graph exists.
    """
    try:
        graph = tool_context.state.get("graph")
        if graph is None:
            return "Error: No graph state found. Use load_image first to initialize."

        node_count = len(graph.get("nodes", []))
        edge_count = len(graph.get("edges", []))
        diagram_type = graph.get("diagram_type", "not set")

        summary = (
            f"Current graph state:\n"
            f"  Diagram type: {diagram_type}\n"
            f"  Nodes: {node_count}\n"
            f"  Edges: {edge_count}\n\n"
            f"Full graph:\n{json.dumps(graph, indent=2)}"
        )

        return summary

    except Exception as e:
        return log_tool_error("get_graph", e)
