"""REST client for the Dataplex lookupContext API.

The lookupContext API is not yet available in the google-cloud-dataplex Python
SDK (as of v2.16.0). This utility calls it via REST. When the SDK adds support,
this can be replaced with a native client call.

See: https://cloud.google.com/dataplex/docs/reference/rest/v1/projects.locations/lookupContext
"""

import google.auth
import google.auth.transport.requests
import requests

from config import BQ_LOCATION, GOOGLE_CLOUD_PROJECT


def lookup_context(
    entry_names: list[str],
    format: str = "YAML",
) -> str:
    """Call the Dataplex lookupContext API for a batch of entries.

    Args:
        entry_names: Dataplex entry names (max 10 per call). Format:
            projects/{project}/locations/{location}/entryGroups/@bigquery/
            entries/bigquery.googleapis.com/projects/{project}/datasets/{dataset}/tables/{table}
        format: Response format — "YAML" or "XML".

    Returns:
        The context string from the API (LLM-ready formatted metadata).
    """
    creds, _ = google.auth.default()
    creds.refresh(google.auth.transport.requests.Request())

    url = (
        f"https://dataplex.googleapis.com/v1/projects/{GOOGLE_CLOUD_PROJECT}"
        f"/locations/{BQ_LOCATION.lower()}:lookupContext"
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
    format: str = "YAML",
) -> str:
    """Call lookupContext in batches (API limit is 10 entries per call).

    Args:
        entry_names: All Dataplex entry names to look up.
        batch_size: Max entries per API call (default 10, the API max).
        format: Response format — "YAML" or "XML".

    Returns:
        Concatenated context string from all batches.
    """
    all_context = []

    for i in range(0, len(entry_names), batch_size):
        batch = entry_names[i : i + batch_size]
        context = lookup_context(batch, format=format)
        if context:
            all_context.append(context)

    return "\n".join(all_context)
