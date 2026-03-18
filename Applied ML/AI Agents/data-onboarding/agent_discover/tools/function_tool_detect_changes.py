import logging

from google.adk import tools

from agent_acquire.tools.util_common import log_tool_error
from agent_orchestrator.util_metadata import write_processing_log

from .util_manifest import compute_changes, get_prior_manifest

logger = logging.getLogger(__name__)


async def detect_changes(
    tool_context: tools.ToolContext,
) -> str:
    """
    Detect changes between current files and the prior source manifest in BigQuery.

    Compares file hashes of current staged files against the last recorded manifest.
    Identifies new, modified, unchanged, and removed files.

    Args:
        tool_context: The ADK tool context for accessing shared state.

    Returns:
        A change summary, or an error message.
    """
    try:
        source_id = tool_context.state.get("source_id", "")
        files_acquired = tool_context.state.get("files_acquired", [])

        if not source_id:
            return "Error: source_id not set in state."

        # Get prior manifest from BQ
        prior = get_prior_manifest(source_id)

        # Compute changes
        changes = compute_changes(files_acquired, prior)

        tool_context.state["change_summary"] = changes

        # Write processing log
        write_processing_log(
            source_id, "discover", "detect_changes", "completed",
            details={
                "new": len(changes["new"]),
                "modified": len(changes["modified"]),
                "unchanged": len(changes["unchanged"]),
                "removed": len(changes["removed"]),
            },
        )

        is_first_run = not prior

        summary = "Change detection complete.\n"
        if is_first_run:
            summary += "  This is the first run for this source — all files are new.\n"

        summary += (
            f"  New files: {len(changes['new'])}\n"
            f"  Modified files: {len(changes['modified'])}\n"
            f"  Unchanged files: {len(changes['unchanged'])}\n"
            f"  Removed files: {len(changes['removed'])}\n"
        )

        if changes["new"]:
            summary += "\nNew:\n" + "\n".join(f"  + {p}" for p in changes["new"][:10])
        if changes["modified"]:
            summary += "\nModified:\n" + "\n".join(f"  ~ {p}" for p in changes["modified"][:10])
        if changes["removed"]:
            summary += "\nRemoved:\n" + "\n".join(f"  - {p}" for p in changes["removed"][:10])

        return summary

    except Exception as e:
        return log_tool_error("detect_changes", e)
