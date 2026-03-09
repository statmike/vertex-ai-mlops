import logging
import posixpath

from google.adk import tools

from agent_acquire.tools.util_common import log_tool_error
from agent_acquire.tools.util_gcs import list_blobs

logger = logging.getLogger(__name__)


async def inventory_files(
    tool_context: tools.ToolContext,
) -> str:
    """
    List all files in the GCS staging area with metadata.

    Reads `gcs_staging_path` from state and lists all blobs under it,
    collecting file name, size, type, and last modified time.

    Args:
        tool_context: The ADK tool context for accessing shared state.

    Returns:
        A summary of inventoried files, or an error message.
    """
    try:
        staging_path = tool_context.state.get("gcs_staging_path", "")
        if not staging_path:
            return "Error: gcs_staging_path not set in state."

        blobs = list_blobs(staging_path)

        inventory = []
        for blob in blobs:
            name = blob["name"]
            filename = posixpath.basename(name)
            ext = posixpath.splitext(filename)[1].lstrip(".").lower()

            # Determine subdirectory (files/ or context/)
            relative = name[len(staging_path):].lstrip("/")
            subdir = relative.split("/")[0] if "/" in relative else ""

            inventory.append({
                "gcs_path": name,
                "filename": filename,
                "extension": ext,
                "size_bytes": blob["size"],
                "updated": blob["updated"],
                "content_type": blob["content_type"],
                "subdir": subdir,
            })

        tool_context.state["file_inventory"] = inventory

        summary = (
            f"Inventory complete.\n"
            f"  Total files: {len(inventory)}\n"
            f"  In files/: {sum(1 for f in inventory if f['subdir'] == 'files')}\n"
            f"  In context/: {sum(1 for f in inventory if f['subdir'] == 'context')}\n"
            f"  Total size: {sum(f['size_bytes'] or 0 for f in inventory) / 1024:.1f} KB\n"
        )

        # List by type
        ext_counts: dict[str, int] = {}
        for f in inventory:
            ext = f["extension"] or "(none)"
            ext_counts[ext] = ext_counts.get(ext, 0) + 1

        summary += "\nBy extension:\n"
        for ext, count in sorted(ext_counts.items()):
            summary += f"  .{ext}: {count}\n"

        return summary

    except Exception as e:
        return log_tool_error("inventory_files", e)
