"""Label detected elements with OCR text and semantic labels via Gemini."""

import base64
import json
import logging

from google.adk import tools
from google.genai import types

from .util_common import log_tool_error, strip_json_markdown_fence
from .util_gemini import generate_content

logger = logging.getLogger(__name__)


async def label_elements(tool_context: tools.ToolContext) -> str:
    """
    Add OCR text and semantic labels to detected elements using Gemini.

    Sends the original image along with the list of detected element bounding
    boxes to Gemini, which extracts visible text (OCR) and provides a semantic
    label for each element.

    Args:
        tool_context: The ADK tool context containing the source image and
            detected elements (from detect_elements) in state.

    Returns:
        A summary of labeled elements, or an error message if labeling fails.
    """
    response_text = ""
    try:
        source_image_b64 = tool_context.state.get("source_image")
        if not source_image_b64:
            return "Error: No source image loaded. Use load_image first."

        elements = tool_context.state.get("cv_elements", [])
        if not elements:
            return "Error: No elements detected. Run detect_elements first."

        mime_type = tool_context.state.get("source_image_mime_type", "image/png")
        image_bytes = base64.b64decode(source_image_b64)

        # Build element descriptions for the prompt
        element_descriptions = []
        for el in elements:
            bbox = el["bounding_box"]
            element_descriptions.append(
                f"  - id: {el['id']}, bounding_box: [y_min={bbox[0]}, x_min={bbox[1]}, "
                f"y_max={bbox[2]}, x_max={bbox[3]}] (0-1000 scale), shape: {el['shape']}"
            )

        elements_text = "\n".join(element_descriptions)

        prompt = f"""The following visual elements were detected in this diagram image using contour detection.
Each element has a bounding box in normalized 0-1000 coordinates where (0,0) is top-left.

Detected elements:
{elements_text}

For EACH element, examine the corresponding region of the image and provide:
1. "text": The exact text visible inside or directly on the element (OCR). Use null if no text is visible.
2. "semantic_label": A brief description of what the element represents in the context of the diagram
   (e.g., "start terminal", "decision node", "process step", "data store", "input/output").

Return a JSON object with this structure:
{{
    "labels": [
        {{
            "id": "cv_1",
            "text": "START",
            "semantic_label": "terminal node"
        }},
        {{
            "id": "cv_2",
            "text": null,
            "semantic_label": "connector junction"
        }}
    ]
}}

Return ONLY the JSON object, no other text."""

        response = await generate_content(
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                types.Part.from_text(text=prompt),
            ],
            tool_context=tool_context,
            tool_name="label_elements",
        )

        response_text = strip_json_markdown_fence(response.text)
        result_data = json.loads(response_text)

        labels = result_data.get("labels", [])

        # Merge labels back into elements
        label_map = {lab["id"]: lab for lab in labels}
        labeled_count = 0
        for el in elements:
            lab = label_map.get(el["id"])
            if lab:
                el["text"] = lab.get("text")
                el["semantic_label"] = lab.get("semantic_label", "")
                labeled_count += 1
            else:
                el["text"] = None
                el["semantic_label"] = ""

        # Update state
        tool_context.state["cv_elements"] = elements

        # Build summary
        label_lines = []
        for el in elements:
            text = el.get("text") or "(no text)"
            sem = el.get("semantic_label", "")
            label_lines.append(f'  - {el["id"]}: text="{text}", label="{sem}"')

        return (
            f"Labeling complete. {labeled_count}/{len(elements)} elements labeled.\n\n"
            f"Labels:\n" + "\n".join(label_lines) + "\n\n"
            "Proceed with report_results to finalize CV preprocessing."
        )

    except json.JSONDecodeError as e:
        raw = response_text[:500] if response_text else "(no response)"
        return f"Error parsing label response as JSON: {str(e)}\nRaw response: {raw}"
    except Exception as e:
        return log_tool_error("label_elements", e)
