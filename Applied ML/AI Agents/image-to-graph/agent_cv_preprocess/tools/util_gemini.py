"""Gemini utility wrapper that lazily imports from agent_image_to_graph.

Avoids circular imports at module load time — the real import happens
only when generate_content() is actually called at runtime.
"""


async def generate_content(contents, model=None, tool_context=None, tool_name=None):
    """Proxy to agent_image_to_graph.tools.util_gemini.generate_content."""
    from agent_image_to_graph.tools.util_gemini import generate_content as _generate_content

    return await _generate_content(
        contents=contents,
        model=model,
        tool_context=tool_context,
        tool_name=tool_name,
    )
