import base64
import json
import logging

from google.adk import tools
from google.genai import types

from .util_common import log_tool_error, strip_json_markdown_fence
from .util_gemini import generate_content

logger = logging.getLogger(__name__)


async def trace_connections(tool_context: tools.ToolContext) -> str:
    """
    Detect edges across the full image using all discovered node positions.

    Sends the full source image along with a context listing of all nodes
    (ids, labels, bounding box positions) to Gemini for a dedicated
    edge-finding pass. This catches cross-region connections that
    region-level examination may miss.

    Does NOT auto-add edges to the graph — returns them for the agent
    to review and add via update_graph.

    Args:
        tool_context: The ADK tool context containing source image and graph in state.

    Returns:
        A summary of discovered edges with confidence levels, or an error message.
    """
    response_text = ""
    try:
        source_image_b64 = tool_context.state.get("source_image")
        if not source_image_b64:
            return "Error: No source image loaded. Use load_image first."

        graph = tool_context.state.get("graph")
        if graph is None:
            return "Error: No graph state found. Use load_image first."

        nodes = graph.get("nodes", [])
        if not nodes:
            return "Error: No nodes in graph. Examine regions and add nodes before tracing connections."

        mime_type = tool_context.state.get("source_image_mime_type", "image/png")
        diagram_type = graph.get("diagram_type", "unknown")

        # Build node context string
        node_context_lines = []
        for node in nodes:
            node_id = node.get("id", "?")
            label = node.get("label", "?")
            bbox = node.get("bounding_box", [])
            bbox_str = f" at [{', '.join(str(v) for v in bbox)}]" if bbox else ""
            etype = node.get("element_type", "")
            etype_str = f" ({etype})" if etype else ""
            parent_id = node.get("parent_id", "")
            parent_str = f" [parent: {parent_id}]" if parent_id else ""
            node_context_lines.append(f'  - {node_id}: "{label}"{etype_str}{bbox_str}{parent_str}')

        node_context = "\n".join(node_context_lines)

        image_bytes = base64.b64decode(source_image_b64)

        prompt = f"""You are analyzing a {diagram_type} diagram. The following nodes have been identified:

{node_context}

Bounding box coordinates are [y_min, x_min, y_max, x_max] on a 0-1000 normalized scale.

Examine the FULL image carefully and identify ALL visible connections (arrows, lines, wires, flows) between these nodes.

Return a JSON object with this exact structure:
{{
    "edges": [
        {{
            "id": "e1",
            "source": "source_node_id",
            "target": "target_node_id",
            "label": "visible text printed ON the connection line/arrow, or null if no text is visible",
            "edge_type": "flow|feedback|dependency|association|...",
            "confidence": "high|medium|low"
        }}
    ]
}}

IMPORTANT:
- Look for ALL arrows, lines, wires, and connections between nodes.
- Include connections that cross between different regions of the diagram.
- Pay attention to arrow direction — source is where the arrow starts, target is where it points.
- For dashed or dotted lines, set edge_type to "feedback" or "dependency" as appropriate.
- For solid arrows, use "flow".
- "label" is ONLY for text that is visibly printed ON or next to the connection line/arrow
  (e.g., "Point Forecast", "Yes", "No"). Do NOT use the edge_type as the label.
  If there is no visible text on the connection, set label to null.
- Set confidence to "high" if the connection is clearly visible, "medium" if partially obscured, "low" if uncertain.
- Use the exact node IDs from the list above for source and target.
- Generate unique edge IDs (e.g., "e1", "e2", ...).

Return ONLY the JSON object, no other text."""

        response = await generate_content(
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                types.Part.from_text(text=prompt),
            ],
        )

        response_text = strip_json_markdown_fence(response.text)

        result_data = json.loads(response_text)
        edges = result_data.get("edges", [])

        if not edges:
            return "No connections found between nodes."

        # Build summary
        edge_lines = []
        for edge in edges:
            eid = edge.get("id", "?")
            source = edge.get("source", "?")
            target = edge.get("target", "?")
            label = edge.get("label", "")
            etype = edge.get("edge_type", "flow")
            conf = edge.get("confidence", "high")
            label_str = f' "{label}"' if label else ""
            edge_lines.append(
                f"  - {eid}: {source} -> {target}{label_str} ({etype}) confidence={conf}"
            )

        result = (
            f"Traced {len(edges)} connections across full image.\n"
            f"Edges:\n" + "\n".join(edge_lines) + "\n"
            "\nAdd these edges to the graph via update_graph. Review and adjust as needed."
        )

        return result

    except json.JSONDecodeError as e:
        raw = response_text[:500] if response_text else "(no response)"
        return f"Error parsing trace_connections response as JSON: {str(e)}\nRaw response: {raw}"
    except Exception as e:
        return log_tool_error("trace_connections", e)
