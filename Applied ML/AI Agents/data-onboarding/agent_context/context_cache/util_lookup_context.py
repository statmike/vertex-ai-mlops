"""REST client for the Dataplex lookupContext API.

The lookupContext API is not yet available in the google-cloud-dataplex Python
SDK (as of v2.16.0). This utility calls it via REST. When the SDK adds support,
this can be replaced with a native client call.
"""

import json
import logging

import google.auth
import google.auth.transport.requests
import requests

from agent_orchestrator.config import BQ_DATASET_LOCATION, GOOGLE_CLOUD_PROJECT

logger = logging.getLogger(__name__)


def lookup_context(
    entry_names: list[str],
    format: str = "JSON",
) -> str:
    """Call the Dataplex lookupContext API for a batch of entries.

    Args:
        entry_names: Dataplex entry names (max 10 per call).
        format: Response format — "JSON", "YAML", or "XML".

    Returns:
        The context string from the API (LLM-ready formatted metadata).
    """
    creds, _ = google.auth.default()
    creds.refresh(google.auth.transport.requests.Request())

    url = (
        f"https://dataplex.googleapis.com/v1/projects/{GOOGLE_CLOUD_PROJECT}"
        f"/locations/{BQ_DATASET_LOCATION.lower()}:lookupContext"
    )

    payload = {
        "resources": entry_names,
        "options": {"format": format},
    }

    resp = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {creds.token}",
            "Content-Type": "application/json",
        },
        json=payload,
    )
    resp.raise_for_status()

    data = resp.json()
    return data.get("context", "")


def lookup_context_batched(
    entry_names: list[str],
    batch_size: int = 10,
    format: str = "JSON",
) -> str:
    """Call lookupContext in batches (API limit is 10 entries per call).

    Args:
        entry_names: All Dataplex entry names to look up.
        batch_size: Max entries per API call (default 10, the API max).
        format: Response format.

    Returns:
        For JSON format: a single JSON array string with all entries merged.
        For other formats: concatenated context strings.
    """
    all_context = []

    for i in range(0, len(entry_names), batch_size):
        batch = entry_names[i : i + batch_size]
        context = lookup_context(batch, format=format)
        if context:
            all_context.append(context)

    if not all_context:
        return "[]" if format == "JSON" else ""

    if format == "JSON":
        merged = []
        for ctx in all_context:
            merged.extend(json.loads(ctx))
        return json.dumps(merged, indent=2)

    return "\n".join(all_context)
