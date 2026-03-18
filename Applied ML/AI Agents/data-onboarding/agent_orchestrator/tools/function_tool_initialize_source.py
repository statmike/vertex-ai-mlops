import logging

from google.adk import tools

from agent_acquire.tools.util_common import generate_source_id
from agent_orchestrator.config import GCS_STAGING_ROOT

logger = logging.getLogger(__name__)


async def initialize_source(
    source_uri: str,
    tool_context: tools.ToolContext,
) -> str:
    """Initialize session state for a new data onboarding source.

    Determines the source type (URL or GCS), generates a deterministic
    source ID, and sets all required state variables before the pipeline
    can begin.

    Args:
        source_uri: The URL or GCS path provided by the user.
        tool_context: The ADK tool context for accessing shared state.

    Returns:
        Summary of initialized state, including source_id and staging path.
    """
    source_uri = source_uri.strip()

    if source_uri.startswith(("http://", "https://")):
        source_type = "url"
    elif source_uri.startswith("gs://"):
        source_type = "gcs"
    else:
        return (
            f"Unrecognized source format: '{source_uri}'. "
            "Please provide a URL (http/https) or GCS path (gs://)."
        )

    source_id = generate_source_id(source_uri)
    gcs_staging_path = f"{GCS_STAGING_ROOT}/{source_id}"

    tool_context.state["source_id"] = source_id
    tool_context.state["source_type"] = source_type
    tool_context.state["source_uri"] = source_uri
    tool_context.state["gcs_staging_path"] = gcs_staging_path

    return (
        f"Source initialized.\n"
        f"  URI: {source_uri}\n"
        f"  Type: {source_type}\n"
        f"  Source ID: {source_id}\n"
        f"  GCS staging: {gcs_staging_path}\n"
    )
