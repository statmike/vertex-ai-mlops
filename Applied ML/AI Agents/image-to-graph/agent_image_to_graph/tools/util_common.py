"""Shared utilities for image-to-graph tools."""

import logging


def strip_json_markdown_fence(text: str) -> str:
    """Extract JSON content from a Gemini response that may be wrapped in markdown fences.

    Handles responses like:
        ```json
        {"key": "value"}
        ```

    Returns the text unchanged if no fences are present.
    """
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        # Remove first line (```json or ```) and last line (```)
        lines = lines[1:-1] if lines[-1].strip() == "```" else lines[1:]
        text = "\n".join(lines)
    return text


def log_tool_error(tool_name: str, error: Exception, context: str = "") -> str:
    """Log full traceback and return a sanitized error message for the agent.

    Args:
        tool_name: Name of the tool that encountered the error.
        error: The exception that was raised.
        context: Optional extra context to include in the log message.

    Returns:
        A sanitized error message suitable for returning to the agent.
    """
    logger = logging.getLogger(f"agent_image_to_graph.tools.{tool_name}")
    ctx = f" ({context})" if context else ""
    logger.exception(f"Error in {tool_name}{ctx}")
    return f"Error in {tool_name}: {error}"
