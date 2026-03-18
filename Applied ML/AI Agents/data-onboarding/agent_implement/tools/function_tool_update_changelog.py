import logging
import os

from google.adk import tools

from agent_acquire.tools.util_common import log_tool_error
from agent_orchestrator.config import OUTPUT_DIR

from .util_sql import format_changelog_entry

logger = logging.getLogger(__name__)


async def update_changelog(
    tool_context: tools.ToolContext,
) -> str:
    """
    Append a structured entry to the onboarding changelog.

    Records what tables were created/updated, schema decisions made,
    and any data quality notes.

    Args:
        tool_context: The ADK tool context for accessing shared state.

    Returns:
        Confirmation of changelog update, or an error message.
    """
    try:
        proposals = tool_context.state.get("proposed_tables", {})
        source_id = tool_context.state.get("source_id", "")
        source_uri = tool_context.state.get("source_uri", "")

        if not proposals:
            return "No proposals to log."

        table_names = list(proposals.keys())
        decisions = []
        for name, prop in proposals.items():
            desc = prop.get("description", "")
            cols = len(prop.get("enriched_columns", prop.get("columns", [])))
            decisions.append(f"{name}: {cols} columns — {desc}")

        notes = [
            f"Source: {source_uri}",
            f"Source ID: {source_id}",
        ]

        entry = format_changelog_entry(
            tables=table_names,
            action="created",
            decisions=decisions,
            notes=notes,
        )

        # Append to changelog file
        changelog_path = os.path.join(os.path.abspath(OUTPUT_DIR), "CHANGELOG.md")
        os.makedirs(os.path.dirname(changelog_path), exist_ok=True)

        if os.path.exists(changelog_path):
            with open(changelog_path) as f:
                existing = f.read()
        else:
            existing = "# Data Onboarding Changelog\n"

        with open(changelog_path, "w") as f:
            f.write(existing + entry)

        return (
            f"Changelog updated.\n"
            f"  File: {changelog_path}\n"
            f"  Tables logged: {len(table_names)}\n"
            f"  Entry:\n{entry}"
        )

    except Exception as e:
        return log_tool_error("update_changelog", e)
