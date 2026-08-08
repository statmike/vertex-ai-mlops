"""Deterministic resource-id helpers shared by setup.py and cleanup.py.

Keeping the id logic in one place means the two scripts always reconstruct the
*same* names, so cleanup can find exactly what setup created — no drift. Every
name derives from config values (RESOURCE_PREFIX, the project, the dataset).
"""

import re

from config import BQ_DATASET, GCS_BUCKET, GOOGLE_CLOUD_PROJECT, RESOURCE_PREFIX


def _bounded_id(base: str, limit: int = 63) -> str:
    """Lowercase, sanitize to [a-z0-9-], and length-bound an id deterministically."""
    sanitized = re.sub(r"[^a-z0-9]+", "-", base.lower()).strip("-")
    return sanitized[:limit].strip("-")


def docs_bucket_name() -> str:
    """GCS bucket holding the synthetic retail docs (GCS_BUCKET overrides)."""
    if GCS_BUCKET:
        return GCS_BUCKET
    return _bounded_id(f"{GOOGLE_CLOUD_PROJECT}-{RESOURCE_PREFIX}-docs")


def ai_connection_id() -> str:
    """BigQuery Cloud Resource connection used by the AI.* functions."""
    return f"{BQ_DATASET}_ai"


def profile_scan_id(table: str) -> str:
    """Dataplex data-profile scan id for a view."""
    prefix = RESOURCE_PREFIX.replace("_", "-")
    return _bounded_id(f"{prefix}-profile-{table}")


def model_armor_template_path(project: str, location: str, template: str) -> str:
    """Full resource name of the Model Armor guardrail template.

    Built by hand (not via the client's ``template_path`` helper) so setup and
    cleanup can reconstruct the same name without importing the Model Armor SDK.
    """
    return f"projects/{project}/locations/{location}/templates/{template}"


# NOTE: the Example Store has no deterministic-id helper here on purpose. Vertex
# assigns a numeric resource id at creation (a custom id is ignored), so the name
# can't be reconstructed from config the way the others can. setup, cleanup, and
# the agent instead resolve the store by its deterministic display name
# (EXAMPLE_STORE_DISPLAY_NAME) — see scripts/setup.py:create_example_store.


def agent_runtime_service_agent(project_number: str) -> str:
    """Email of the Agent Runtime (reasoning engine) service agent.

    Deployed agents run as this Google-managed SA — not as the developer — so any
    role the local run gets from your own credentials must be granted here too.
    The name derives from the project *number*, so setup (grant) and cleanup
    (revoke) reconstruct the same address with no drift.
    """
    return f"service-{project_number}@gcp-sa-aiplatform-re.iam.gserviceaccount.com"
