"""Shared utilities for CV preprocessing tools.

Mirrors agent_image_to_graph.tools.util_common to avoid circular imports
(agent_cv_preprocess ↔ agent_image_to_graph).
"""

import logging


def strip_json_markdown_fence(text: str) -> str:
    """Extract JSON content from a response that may be wrapped in markdown fences."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = lines[1:-1] if lines[-1].strip() == "```" else lines[1:]
        text = "\n".join(lines)
    return text


def log_tool_error(tool_name: str, error: Exception, context: str = "") -> str:
    """Log full traceback and return a sanitized error message for the agent."""
    logger = logging.getLogger(f"agent_cv_preprocess.tools.{tool_name}")
    ctx = f" ({context})" if context else ""
    logger.exception(f"Error in {tool_name}{ctx}")
    return f"Error in {tool_name}: {error}"
