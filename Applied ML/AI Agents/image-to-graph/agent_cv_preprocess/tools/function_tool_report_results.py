"""Report CV preprocessing results back to the main agent via session state."""

import logging

from google.adk import tools

from .util_common import log_tool_error

logger = logging.getLogger(__name__)


async def report_results(
    status: str,
    message: str,
    tool_context: tools.ToolContext,
) -> str:
    """
    Store CV preprocessing results in session state and return control to the main agent.

    Packages the detected elements, connections, and metadata into a structured
    result stored as state["cv_preprocessing"]. The main agent's tools
    (analyze_image, crop_and_examine, trace_connections) will read this data
    to enrich their Gemini prompts with deterministic CV context.

    Args:
        status: Result status — "complete" (all steps succeeded), "partial"
            (some steps succeeded), or "skipped" (image not suitable).
        message: A human-readable summary of the CV preprocessing outcome.
        tool_context: The ADK tool context for accessing shared state.

    Returns:
        A confirmation message indicating results have been stored.
    """
    try:
        if status not in ("complete", "partial", "skipped"):
            return f"Error: status must be 'complete', 'partial', or 'skipped', got '{status}'."

        elements = tool_context.state.get("cv_elements", [])
        connections = tool_context.state.get("cv_connections", [])
        params_used = tool_context.state.get("cv_detect_params", {})

        # Compute overall confidence
        if status == "skipped":
            confidence = 0.0
        elif elements:
            # Average element confidence (from labeling step if available)
            # For now, use connection ratio as a proxy
            connected_elements = set()
            for conn in connections:
                connected_elements.add(conn.get("source_element_id"))
                connected_elements.add(conn.get("target_element_id"))
            connectivity_ratio = len(connected_elements) / len(elements) if elements else 0
            confidence = min(0.95, 0.5 + connectivity_ratio * 0.4)
        else:
            confidence = 0.0

        cv_result = {
            "status": status,
            "message": message,
            "confidence": round(confidence, 2),
            "elements": elements,
            "connections": connections,
            "parameters_used": params_used,
        }

        tool_context.state["cv_preprocessing"] = cv_result

        # Clean up intermediate state keys (State doesn't support del/pop, set to None)
        for key in ("cv_elements", "cv_connections", "cv_detect_stats", "cv_detect_params", "cv_assessment"):
            if key in tool_context.state:
                tool_context.state[key] = None

        element_count = len(elements)
        connection_count = len(connections)

        return (
            f"CV preprocessing results stored (status: {status}).\n"
            f"  Elements: {element_count}\n"
            f"  Connections: {connection_count}\n"
            f"  Confidence: {confidence:.2f}\n"
            f"  Message: {message}\n\n"
            f"Returning control to the main agent."
        )

    except Exception as e:
        return log_tool_error("report_results", e)
