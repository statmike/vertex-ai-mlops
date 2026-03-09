import logging

from google.adk import tools

from agent_acquire.tools.util_common import log_tool_error
from agent_orchestrator.config import CONTEXT_FILE_EXTENSIONS, DATA_FILE_EXTENSIONS

logger = logging.getLogger(__name__)


async def classify_files(
    tool_context: tools.ToolContext,
) -> str:
    """
    Classify inventoried files as 'data' or 'context' based on extension and location.

    Reads `file_inventory` from state and classifies each file.
    Files in the context/ subdirectory are always classified as context.
    Other files are classified by their extension.

    Args:
        tool_context: The ADK tool context for accessing shared state.

    Returns:
        A summary of classified files, or an error message.
    """
    try:
        inventory = tool_context.state.get("file_inventory", [])
        if not inventory:
            return "No files to classify. Run inventory_files first."

        classified = []
        for f in inventory:
            ext = f.get("extension", "")
            subdir = f.get("subdir", "")

            if subdir == "context":
                classification = "context"
            elif ext in DATA_FILE_EXTENSIONS:
                classification = "data"
            elif ext in CONTEXT_FILE_EXTENSIONS:
                classification = "context"
            else:
                classification = "unknown"

            classified.append({
                **f,
                "classification": classification,
            })

        tool_context.state["files_classified"] = classified

        data_count = sum(1 for f in classified if f["classification"] == "data")
        context_count = sum(1 for f in classified if f["classification"] == "context")
        unknown_count = sum(1 for f in classified if f["classification"] == "unknown")

        summary = (
            f"Classification complete.\n"
            f"  Data files: {data_count}\n"
            f"  Context files: {context_count}\n"
            f"  Unknown: {unknown_count}\n"
        )

        if data_count:
            summary += "\nData files:\n"
            for f in classified:
                if f["classification"] == "data":
                    summary += f"  - {f['filename']} (.{f['extension']})\n"

        if context_count:
            summary += "\nContext files:\n"
            for f in classified:
                if f["classification"] == "context":
                    summary += f"  - {f['filename']} (.{f['extension']})\n"

        return summary

    except Exception as e:
        return log_tool_error("classify_files", e)
