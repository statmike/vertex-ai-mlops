"""Helpers for consuming the Discovery agent over A2A.

The concierge talks to Discovery as a remote agent, and where its agent card
lives depends on how Discovery is running:

- **Local** — Discovery is a ``to_a2a()`` uvicorn server. ADK serves the card at
  the A2A well-known path (``/.well-known/agent-card.json``), imported from the
  a2a SDK so we never drift if the constant changes.
- **Deployed** — Discovery is an ``A2aAgent`` on Agent Runtime. The Runtime does
  not expose a public well-known card; it serves an *authenticated* card at
  ``{a2a_url}/v1/card`` (reached with a bearer token — see auth.py). This is a
  Runtime-managed convention, not the a2a-sdk well-known path.

We detect the deployed case by the ``*-aiplatform.googleapis.com`` host, matching
the same signal auth.py uses to decide whether to attach credentials.
"""

from a2a.utils.constants import AGENT_CARD_WELL_KNOWN_PATH

from config import discovery_a2a_base_url

# Google Cloud endpoints — the deployed Runtime lives here and serves an
# authenticated card rather than a public well-known one.
_GOOGLE_APIS_HOST = "googleapis.com"

# Path (relative to the deployed A2A base URL) of the Runtime's authenticated
# agent card. Kept as a named constant so it lives in one place if it changes.
_RUNTIME_CARD_PATH = "/v1/card"


def discovery_agent_card_url() -> str:
    """Full URL of the discovery agent's A2A card, correct for local vs deployed.

    Local uvicorn serves the a2a well-known card; the deployed Agent Runtime
    serves an authenticated card at ``{a2a_url}/v1/card``.
    """
    base = discovery_a2a_base_url()
    if _GOOGLE_APIS_HOST in base:
        return f"{base}{_RUNTIME_CARD_PATH}"
    return f"{base}/{AGENT_CARD_WELL_KNOWN_PATH.lstrip('/')}"
