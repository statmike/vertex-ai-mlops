import logging

from google.adk import tools

from agent_acquire.tools.util_common import generate_source_id
from agent_orchestrator.config import (
    BQ_BRONZE_DATASET,
    GCS_STAGING_ROOT,
    extract_domain_slug,
    get_bronze_dataset,
    get_staging_dataset,
)

logger = logging.getLogger(__name__)


async def initialize_source(
    source_uri: str,
    tool_context: tools.ToolContext,
) -> str:
    """Initialize session state for a new data onboarding source.

    Determines the source type (URL or GCS), generates a deterministic
    source ID, extracts the domain slug for URL sources, computes
    domain-specific dataset names, and sets all required state variables
    before the pipeline can begin.

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

    # Compute domain-based dataset names for URL sources
    domain_slug = ""
    if source_type == "url":
        domain_slug = extract_domain_slug(source_uri)
    bronze_dataset = get_bronze_dataset(domain_slug) if domain_slug else BQ_BRONZE_DATASET
    staging_dataset = get_staging_dataset(domain_slug)

    tool_context.state["source_id"] = source_id
    tool_context.state["source_type"] = source_type
    tool_context.state["source_uri"] = source_uri
    tool_context.state["gcs_staging_path"] = gcs_staging_path
    tool_context.state["domain_slug"] = domain_slug
    tool_context.state["bq_bronze_dataset"] = bronze_dataset
    tool_context.state["bq_staging_dataset"] = staging_dataset

    return (
        f"Source initialized. Proceed to the Acquire phase.\n"
        f"  URI: {source_uri}\n"
        f"  Type: {source_type}\n"
        f"  Source ID: {source_id}\n"
        f"  GCS staging: {gcs_staging_path}\n"
        f"  Domain: {domain_slug or '(none)'}\n"
        f"  Bronze dataset: {bronze_dataset} (auto-created by implement tools)\n"
        f"  Staging dataset: {staging_dataset} (auto-created by implement tools)\n"
    )
