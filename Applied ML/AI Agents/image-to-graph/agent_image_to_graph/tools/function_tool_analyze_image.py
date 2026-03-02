import base64
import json
import logging

from google.adk import tools
from google.genai import types

from .util_bbox import normalize_bbox
from .util_common import log_tool_error, strip_json_markdown_fence
from .util_gemini import generate_content

logger = logging.getLogger(__name__)


async def analyze_image(tool_context: tools.ToolContext) -> str:
    """
    Analyze the full source image to identify diagram type, regions, and bounding boxes.

    Sends the stored source image to Gemini for structured analysis. Returns the
    diagram type, a description, and a list of detected regions with normalized
    bounding box coordinates (0-1000 scale).

    Args:
        tool_context: The ADK tool context containing the source image in state.

    Returns:
        A JSON string with diagram analysis results including detected regions
        and bounding boxes, or an error message if analysis fails.
    """
    response_text = ""
    try:
        source_image_b64 = tool_context.state.get("source_image")
        if not source_image_b64:
            return "Error: No source image loaded. Use load_image first."

        mime_type = tool_context.state.get("source_image_mime_type", "image/png")
        image_bytes = base64.b64decode(source_image_b64)

        analysis_prompt = """Analyze this diagram image comprehensively. Return a JSON object with this exact structure:
{
    "diagram_type": "flowchart|schematic|building_plan|network_diagram|uml|org_chart|state_diagram|other",
    "description": "Brief description of what this diagram represents",
    "regions": [
        {
            "region_id": "region_1",
            "label": "Human-readable label for this region",
            "description": "What this region contains",
            "bounding_box": {"top": y_min, "left": x_min, "bottom": y_max, "right": x_max},
            "element_type": "node|group|label|connector|annotation"
        }
    ]
}

IMPORTANT:
- Bounding box coordinates use a normalized 0-1000 scale where the image top-left corner is {"top": 0, "left": 0} and the bottom-right corner is {"bottom": 1000, "right": 1000}.
  "top" = distance from the top edge (0 = very top, 1000 = very bottom).
  "left" = distance from the left edge (0 = far left, 1000 = far right).
  Example: an element at the top-left corner → {"top": 0, "left": 0, "bottom": 200, "right": 150}
  Example: an element at the bottom-right → {"top": 800, "left": 850, "bottom": 1000, "right": 1000}
- Identify ALL distinct visual elements: shapes, boxes, circles, text labels, connectors, arrows, symbols.
- Group related elements into regions (e.g., a box with its label is one region).
- Use descriptive region_ids like "region_1", "region_2", etc.
- For element_type, use "node" for main diagram elements (boxes, circles, symbols), "connector" for lines/arrows, "group" for grouped elements, "label" for standalone text, and "annotation" for notes/comments.

Return ONLY the JSON object, no other text."""

        response = await generate_content(
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                types.Part.from_text(text=analysis_prompt),
            ],
            tool_context=tool_context,
            tool_name="analyze_image",
        )

        # Parse the response
        response_text = strip_json_markdown_fence(response.text)

        analysis = json.loads(response_text)

        # Store diagram type in graph state
        graph = tool_context.state.get("graph", {})
        graph["diagram_type"] = analysis.get("diagram_type")
        tool_context.state["graph"] = graph

        # Store analysis results
        tool_context.state["analysis_result"] = analysis

        regions = analysis.get("regions", [])
        region_count = len(regions)

        # Normalize bounding boxes from dict to list format
        for r in regions:
            bbox = r.get("bounding_box")
            if bbox is not None:
                normalized = normalize_bbox(bbox)
                if normalized:
                    r["bounding_box"] = normalized

        # Update stored analysis with normalized boxes
        analysis["regions"] = regions
        tool_context.state["analysis_result"] = analysis

        # Build a concise region summary (avoid dumping full JSON into conversation)
        region_lines = []
        for r in regions:
            rid = r.get("region_id", "?")
            rlabel = r.get("label", "unlabeled")
            rtype = r.get("element_type", "?")
            bbox = r.get("bounding_box", [])
            region_lines.append(f"  - {rid}: {rlabel} ({rtype}) bbox={bbox}")

        return (
            f"Image analysis complete.\n"
            f"  Diagram type: {analysis.get('diagram_type', 'unknown')}\n"
            f"  Description: {analysis.get('description', 'N/A')}\n"
            f"  Regions detected: {region_count}\n\n"
            f"Regions:\n" + "\n".join(region_lines)
        )

    except json.JSONDecodeError as e:
        raw = response_text[:500] if response_text else "(no response)"
        return f"Error parsing analysis response as JSON: {str(e)}\nRaw response: {raw}"
    except Exception as e:
        return log_tool_error("analyze_image", e)
