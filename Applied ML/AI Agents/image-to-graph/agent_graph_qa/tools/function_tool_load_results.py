import json
import logging
import os

from google.adk import tools

from agent_image_to_graph.config import MAX_SCHEMA_SIZE_BYTES

logger = logging.getLogger(__name__)

# Use 2x the schema limit for graph.json since graphs can be larger
MAX_GRAPH_SIZE_BYTES = MAX_SCHEMA_SIZE_BYTES * 2


async def load_results(directory_path: str, tool_context: tools.ToolContext) -> str:
    """
    Load previously exported graph results from a directory on disk.

    Reads graph.json, schema.json, and optionally description.md from the
    specified directory and stores them in session state so the Q&A agent
    can answer questions about the diagram.

    Args:
        directory_path: Path to a results directory containing graph.json
            and schema.json (e.g. "examples/bq-arima-flowchart/results-with-schema").
        tool_context: The ADK tool context for accessing shared state.

    Returns:
        A summary of what was loaded, or an error message.
    """
    # If state already has a populated graph (sub-agent mode), skip loading
    existing_graph = tool_context.state.get("graph")
    if existing_graph and existing_graph.get("nodes"):
        nodes = existing_graph.get("nodes", [])
        edges = existing_graph.get("edges", [])
        return (
            f"Graph data already available ({len(nodes)} nodes, {len(edges)} edges). "
            "Use get_context to review."
        )

    try:
        expanded = os.path.expanduser(directory_path)

        if not os.path.isdir(expanded):
            return f"Error: Directory not found at '{directory_path}'."

        # --- graph.json (required) ---
        graph_path = os.path.join(expanded, "graph.json")
        if not os.path.isfile(graph_path):
            return f"Error: graph.json not found in '{directory_path}'."

        graph_size = os.path.getsize(graph_path)
        if graph_size > MAX_GRAPH_SIZE_BYTES:
            size_mb = graph_size / (1024 * 1024)
            limit_mb = MAX_GRAPH_SIZE_BYTES / (1024 * 1024)
            return (
                f"Error: graph.json is too large ({size_mb:.1f} MB). "
                f"Maximum allowed size is {limit_mb:.0f} MB."
            )

        with open(graph_path) as f:
            graph = json.load(f)
        tool_context.state["graph"] = graph

        nodes = graph.get("nodes", [])
        edges = graph.get("edges", [])

        # --- schema.json (required) ---
        schema_path = os.path.join(expanded, "schema.json")
        if not os.path.isfile(schema_path):
            return f"Error: schema.json not found in '{directory_path}'."

        schema_size = os.path.getsize(schema_path)
        if schema_size > MAX_SCHEMA_SIZE_BYTES:
            size_mb = schema_size / (1024 * 1024)
            limit_mb = MAX_SCHEMA_SIZE_BYTES / (1024 * 1024)
            return (
                f"Error: schema.json is too large ({size_mb:.1f} MB). "
                f"Maximum allowed size is {limit_mb:.0f} MB."
            )

        with open(schema_path) as f:
            schema = json.load(f)
        tool_context.state["schema"] = schema

        # Detect if this was a schema-guided run
        abs_path = os.path.abspath(expanded)
        if "results-with-schema" in abs_path:
            tool_context.state["input_schema"] = schema

        # --- description.md (optional) ---
        has_description = False
        desc_path = os.path.join(expanded, "description.md")
        if os.path.isfile(desc_path):
            with open(desc_path) as f:
                description = f.read()
            tool_context.state["diagram_description"] = description
            has_description = True

        # Build summary
        schema_type = "provided" if tool_context.state.get("input_schema") else "auto-generated"
        desc_status = "yes" if has_description else "no"
        return (
            f"Loaded graph with {len(nodes)} nodes, {len(edges)} edges. "
            f"Schema: {schema_type}. Description: {desc_status}."
        )

    except json.JSONDecodeError as e:
        return f"Error: Invalid JSON in results files: {e}"
    except Exception as e:
        logger.exception("Error loading results")
        return f"Error loading results: {e}"
