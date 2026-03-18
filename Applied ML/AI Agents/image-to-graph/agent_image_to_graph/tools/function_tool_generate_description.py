import base64
import json
import logging

from google.adk import tools
from google.genai import types

from .util_common import log_tool_error
from .util_gemini import generate_content

logger = logging.getLogger(__name__)


async def generate_description(tool_context: tools.ToolContext) -> str:
    """
    Generate a comprehensive narrative description of the diagram.

    Uses the source image, extracted graph JSON, and schema as context to produce
    a detailed, human-readable description of the diagram's structure, purpose,
    data flows, and key components. The description is stored in state for
    inclusion in the visualization HTML.

    Args:
        tool_context: The ADK tool context containing image, graph, and schema in state.

    Returns:
        The generated description text, or an error message if generation fails.
    """
    try:
        source_image_b64 = tool_context.state.get("source_image")
        if not source_image_b64:
            return "Error: No source image loaded. Use load_image first."

        graph = tool_context.state.get("graph")
        if graph is None or not graph.get("nodes"):
            return "Error: Graph has no nodes. Build the graph before generating a description."

        mime_type = tool_context.state.get("source_image_mime_type", "image/png")
        image_bytes = base64.b64decode(source_image_b64)

        schema = tool_context.state.get("input_schema") or tool_context.state.get("schema")

        # Build context for the description prompt
        graph_summary = json.dumps(graph, indent=2)
        schema_summary = json.dumps(schema, indent=2) if schema else "No schema provided."

        # Build flow/metadata context
        extra_context = ""
        flows = graph.get("flows", [])
        if flows and len(flows) >= 2:
            flow_desc = ", ".join(
                f"{f['label']} ({len(f.get('node_ids', []))} nodes)" for f in flows
            )
            extra_context += (
                f"\n\nThis diagram contains {len(flows)} distinct flows: {flow_desc}. "
                "Describe each flow separately and explain any cross-flow relationships or references."
            )

        metadata = graph.get("metadata", {})
        if isinstance(metadata, dict):
            page_info = metadata.get("page_info", {})
            if page_info and isinstance(page_info, dict):
                info_parts = [f"{k}: {v}" for k, v in page_info.items() if v]
                if info_parts:
                    extra_context += f"\n\nPage metadata: {', '.join(info_parts)}."

            legend = metadata.get("legend", [])
            if legend and isinstance(legend, list):
                legend_lines = [
                    f"  - {e.get('symbol', '?')}: {e.get('meaning', '?')}"
                    for e in legend if isinstance(e, dict)
                ]
                if legend_lines:
                    extra_context += (
                        "\n\nThe diagram uses these symbols:\n" + "\n".join(legend_lines)
                        + "\nReference these symbols in your description where relevant."
                    )

        prompt = f"""You are given a diagram image along with its extracted graph representation and schema.

Write a comprehensive, detailed description of this diagram. Your description should cover:

1. **Overview**: What type of diagram is this? What system, process, or concept does it represent?
2. **Structure**: Describe the major sections, phases, or groupings visible in the diagram.
3. **Components**: Describe the key nodes/elements — what they represent, their roles, and how they relate to each other.
4. **Data Flow**: Trace the flow of data or control through the diagram from inputs to outputs. Describe the sequence of operations.
5. **Key Relationships**: Highlight important connections, dependencies, or feedback loops between components.
6. **Outputs**: What are the final outputs or results of the process shown?

Write in clear, professional prose. Use paragraph form, not bullet points. Reference specific node labels and connections from the graph. The description should be self-contained — someone reading it without seeing the diagram should understand the full structure and flow.{extra_context}

Graph JSON:
{graph_summary}

Schema:
{schema_summary}"""

        response = await generate_content(
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                types.Part.from_text(text=prompt),
            ],
            tool_context=tool_context,
            tool_name="generate_description",
        )

        description = response.text.strip()

        # Store in state for use by generate_visualization
        tool_context.state["diagram_description"] = description

        # Return a concise confirmation (full text is in state)
        preview = description[:200] + "..." if len(description) > 200 else description
        return (
            f"Description generated ({len(description)} chars) and stored in state.\n"
            f"Preview: {preview}\n"
            f"The full description will be included in the visualization HTML."
        )

    except Exception as e:
        return log_tool_error("generate_description", e)
