import logging

from google.adk import tools

logger = logging.getLogger(__name__)


async def get_context(tool_context: tools.ToolContext) -> str:
    """
    Retrieve the full graph context from session state for answering questions.

    Returns a formatted summary of the graph structure, all nodes and edges,
    the schema, and the diagram description. This gives the LLM everything
    it needs to answer structural, traversal, and semantic questions.

    Args:
        tool_context: The ADK tool context for accessing shared state.

    Returns:
        A formatted string with the complete graph context, or an error
        message if no graph data is available.
    """
    graph = tool_context.state.get("graph")
    if not graph:
        return "No graph data in session state. Use load_results to load a results directory first."

    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])

    if not nodes:
        return "Graph is empty (no nodes). Use load_results to load a results directory first."

    lines = []

    # --- Graph summary ---
    lines.append("=" * 60)
    lines.append("GRAPH SUMMARY")
    lines.append("=" * 60)
    lines.append(f"Diagram type: {graph.get('diagram_type', 'unknown')}")
    lines.append(f"Total nodes: {len(nodes)}")
    lines.append(f"Total edges: {len(edges)}")

    # Node type breakdown
    type_counts = {}
    for node in nodes:
        etype = node.get("element_type", "unknown")
        type_counts[etype] = type_counts.get(etype, 0) + 1
    lines.append("Node types:")
    for etype, count in sorted(type_counts.items()):
        lines.append(f"  {etype}: {count}")

    # Metadata
    metadata = graph.get("metadata", {})
    if metadata:
        source = metadata.get("source_file", "unknown")
        lines.append(f"Source file: {source}")

    # --- All nodes ---
    lines.append("")
    lines.append("=" * 60)
    lines.append("ALL NODES")
    lines.append("=" * 60)
    for node in nodes:
        node_id = node.get("id", "?")
        label = node.get("label", "?")
        etype = node.get("element_type", "")
        shape = node.get("shape", "")
        # Collect additional attributes beyond the standard ones
        standard_keys = {"id", "label", "element_type", "shape", "bounding_box", "confidence"}
        extras = {k: v for k, v in node.items() if k not in standard_keys}
        extra_str = f"  attrs={extras}" if extras else ""
        lines.append(f'  [{node_id}] "{label}" (type={etype}, shape={shape}){extra_str}')

    # --- All edges ---
    lines.append("")
    lines.append("=" * 60)
    lines.append("ALL EDGES")
    lines.append("=" * 60)
    # Build a quick node-id to label map for readable edges
    id_to_label = {n.get("id", ""): n.get("label", "?") for n in nodes}
    for edge in edges:
        edge_id = edge.get("id", "?")
        source = edge.get("source", "?")
        target = edge.get("target", "?")
        label = edge.get("label", "")
        edge_type = edge.get("edge_type", "")
        source_label = id_to_label.get(source, source)
        target_label = id_to_label.get(target, target)
        label_str = f' "{label}"' if label else ""
        type_str = f" ({edge_type})" if edge_type else ""
        lines.append(f"  [{edge_id}] {source_label} --> {target_label}{label_str}{type_str}")

    # --- Schema summary ---
    schema = tool_context.state.get("schema") or tool_context.state.get("input_schema")
    if schema:
        lines.append("")
        lines.append("=" * 60)
        lines.append("SCHEMA")
        lines.append("=" * 60)
        lines.append(f"Title: {schema.get('title', 'N/A')}")
        lines.append(f"Description: {schema.get('description', 'N/A')}")

        props = schema.get("properties", {})
        node_items = props.get("nodes", {}).get("items", {})
        edge_items = props.get("edges", {}).get("items", {})

        if node_items:
            node_props = node_items.get("properties", {})
            node_required = node_items.get("required", [])
            lines.append(f"Node fields: {list(node_props.keys())}")
            lines.append(f"Node required: {node_required}")
            # Show enums if present
            for fname, fschema in node_props.items():
                if "enum" in fschema:
                    lines.append(f"  {fname} enum: {fschema['enum']}")

        if edge_items:
            edge_props = edge_items.get("properties", {})
            edge_required = edge_items.get("required", [])
            lines.append(f"Edge fields: {list(edge_props.keys())}")
            lines.append(f"Edge required: {edge_required}")
            for fname, fschema in edge_props.items():
                if "enum" in fschema:
                    lines.append(f"  {fname} enum: {fschema['enum']}")

    # --- Description ---
    description = tool_context.state.get("diagram_description", "")
    if description:
        lines.append("")
        lines.append("=" * 60)
        lines.append("DIAGRAM DESCRIPTION")
        lines.append("=" * 60)
        lines.append(description)

    return "\n".join(lines)
