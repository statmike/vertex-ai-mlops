import base64
import io
import json
from google.adk import tools
from google.genai import types
from PIL import Image
from .gemini_utils import generate_content


async def crop_and_examine(
    region_id: str,
    bounding_box: list[int],
    tool_context: tools.ToolContext,
) -> str:
    """
    Crop a region from the source image and examine it in one step.

    Crops using bounding box coordinates (normalized 0-1000 scale), then sends
    the cropped image to Gemini for detailed analysis of labels, symbols, shapes,
    connection points, and attributes.

    Args:
        region_id: A unique identifier for this region (e.g., "region_1").
        bounding_box: Normalized bounding box as [y_min, x_min, y_max, x_max]
                      where coordinates are on a 0-1000 scale.
        tool_context: The ADK tool context containing the source image in state.

    Returns:
        A concise summary of elements and connections found in the region,
        or an error message if cropping or examination fails.
    """
    response_text = ''
    try:
        source_image_b64 = tool_context.state.get('source_image')
        if not source_image_b64:
            return "Error: No source image loaded. Use load_image first."

        dimensions = tool_context.state.get('image_dimensions', {})
        img_width = dimensions.get('width', 0)
        img_height = dimensions.get('height', 0)

        if not img_width or not img_height:
            return "Error: Image dimensions not found in state."

        if len(bounding_box) != 4:
            return "Error: bounding_box must be [y_min, x_min, y_max, x_max] (4 values)."

        y_min_norm, x_min_norm, y_max_norm, x_max_norm = bounding_box

        # Convert normalized (0-1000) to pixel coordinates
        x_min = int(x_min_norm / 1000 * img_width)
        y_min = int(y_min_norm / 1000 * img_height)
        x_max = int(x_max_norm / 1000 * img_width)
        y_max = int(y_max_norm / 1000 * img_height)

        # Apply padding (5% of region size, clamped to image bounds)
        pad_x = max(int((x_max - x_min) * 0.05), 5)
        pad_y = max(int((y_max - y_min) * 0.05), 5)
        x_min = max(0, x_min - pad_x)
        y_min = max(0, y_min - pad_y)
        x_max = min(img_width, x_max + pad_x)
        y_max = min(img_height, y_max + pad_y)

        # Crop the image
        image_bytes = base64.b64decode(source_image_b64)
        img = Image.open(io.BytesIO(image_bytes))
        cropped = img.crop((x_min, y_min, x_max, y_max))

        # Convert cropped image to bytes
        buffer = io.BytesIO()
        mime_type = tool_context.state.get('source_image_mime_type', 'image/png')
        crop_format = tool_context.state.get('image_format', 'PNG')
        if crop_format == 'JPEG':
            cropped.save(buffer, format='JPEG', quality=95)
        else:
            cropped.save(buffer, format='PNG')
        cropped_bytes = buffer.getvalue()

        # Get diagram type for context
        graph = tool_context.state.get('graph', {})
        diagram_type = graph.get('diagram_type', 'unknown')

        # Send cropped image to Gemini for examination (with 429 retry)
        examine_prompt = f"""Examine this cropped region from a {diagram_type} diagram in detail.
Return a JSON object with this exact structure:
{{
    "elements": [
        {{
            "element_id": "unique_id_for_this_element",
            "label": "The text label or name visible on this element",
            "element_type": "The type of element (e.g., process, decision, terminal, resistor, room, server, class, state)",
            "shape": "The visual shape (rectangle, diamond, circle, oval, hexagon, custom)",
            "attributes": {{
                "key": "value pairs for any additional properties visible"
            }},
            "connection_points": ["top", "bottom", "left", "right"],
            "text_content": "Any text visible inside or near this element",
            "confidence": "high|medium|low"
        }}
    ],
    "connections_visible": [
        {{
            "description": "Description of any connection/arrow/line visible in this region",
            "from_direction": "Where the connection comes from (e.g., left edge, top)",
            "to_direction": "Where the connection goes (e.g., right edge, bottom)",
            "label": "Any label on the connection, or null"
        }}
    ],
    "complexity": "low|medium|high",
    "confidence": "high|medium|low",
    "suggested_sub_regions": [
        {{
            "label": "description of dense area needing closer examination",
            "bounding_box": [y_min, x_min, y_max, x_max]
        }}
    ],
    "notes": "Any additional observations about this region"
}}

IMPORTANT:
- Extract ALL text labels, even small ones.
- Note the shape and visual style of each element.
- Identify connection points where lines/arrows enter or leave elements.
- For domain-specific elements (electrical symbols, UML notation, etc.), identify them precisely.
- Include any visible attributes, values, or annotations.
- Set "confidence" to "high", "medium", or "low" for each element based on how clearly you can read it.
- Set the top-level "complexity" to "high" if the region has many overlapping elements, small text, or is hard to parse; "medium" for moderate density; "low" for simple regions.
- Set the top-level "confidence" to your overall confidence in the examination results.
- Only populate "suggested_sub_regions" when complexity is "high". Use bounding_box coordinates normalized 0-1000 RELATIVE TO THIS CROP (not the full image). These are sub-areas that need closer examination.

Return ONLY the JSON object, no other text."""

        response = await generate_content(
            contents=[
                types.Part.from_bytes(data=cropped_bytes, mime_type=mime_type),
                types.Part.from_text(text=examine_prompt),
            ],
        )

        # Parse the response
        response_text = response.text.strip()
        if response_text.startswith('```'):
            lines = response_text.split('\n')
            lines = lines[1:-1] if lines[-1].strip() == '```' else lines[1:]
            response_text = '\n'.join(lines)

        examination = json.loads(response_text)

        elements = examination.get('elements', [])
        connections = examination.get('connections_visible', [])
        complexity = examination.get('complexity', 'low')
        overall_confidence = examination.get('confidence', 'high')
        suggested_sub_regions = examination.get('suggested_sub_regions', [])

        # Build concise summary
        crop_width = x_max - x_min
        crop_height = y_max - y_min

        element_lines = []
        for el in elements:
            eid = el.get('element_id', '?')
            elabel = el.get('label', 'unlabeled')
            etype = el.get('element_type', '?')
            eshape = el.get('shape', '?')
            el_conf = el.get('confidence', 'high')
            attrs = el.get('attributes', {})
            attr_str = f" attrs={attrs}" if attrs else ""
            element_lines.append(f"  - {eid}: \"{elabel}\" ({etype}, {eshape}) confidence={el_conf}{attr_str}")

        conn_lines = []
        for conn in connections:
            desc = conn.get('description', '?')
            clabel = conn.get('label', '')
            label_str = f" label=\"{clabel}\"" if clabel else ""
            conn_lines.append(f"  - {desc}{label_str}")

        notes = examination.get('notes', '')

        result = (
            f"Region '{region_id}' cropped ({crop_width}x{crop_height}px) and examined.\n"
            f"  Elements: {len(elements)}, Connections: {len(connections)}\n"
            f"  Complexity: {complexity}, Confidence: {overall_confidence}\n"
        )
        if element_lines:
            result += "Elements:\n" + '\n'.join(element_lines) + "\n"
        if conn_lines:
            result += "Connections:\n" + '\n'.join(conn_lines) + "\n"
        if notes:
            result += f"Notes: {notes}\n"

        # Convert suggested sub-region bounding boxes from crop-relative to full-image coordinates
        if suggested_sub_regions:
            converted_subs = []
            for sub in suggested_sub_regions:
                sub_label = sub.get('label', 'sub-region')
                sub_bbox = sub.get('bounding_box', [])
                if len(sub_bbox) == 4:
                    # sub_bbox is normalized 0-1000 relative to the crop
                    sy_min, sx_min, sy_max, sx_max = sub_bbox
                    # Convert to pixel coords within the crop, then to full-image normalized 0-1000
                    full_y_min = int((y_min + sy_min / 1000 * crop_height) / img_height * 1000)
                    full_x_min = int((x_min + sx_min / 1000 * crop_width) / img_width * 1000)
                    full_y_max = int((y_min + sy_max / 1000 * crop_height) / img_height * 1000)
                    full_x_max = int((x_min + sx_max / 1000 * crop_width) / img_width * 1000)
                    converted_subs.append(
                        f"  - \"{sub_label}\": [{full_y_min}, {full_x_min}, {full_y_max}, {full_x_max}]"
                    )
            if converted_subs:
                result += "Suggested sub-regions for re-examination (full-image coords):\n"
                result += '\n'.join(converted_subs) + "\n"

        return result

    except json.JSONDecodeError as e:
        raw = response_text[:500] if response_text else '(no response)'
        return f"Error parsing examination response as JSON: {str(e)}\nRaw response: {raw}"
    except Exception as e:
        return f"Error in crop_and_examine for '{region_id}': {str(e)}"
