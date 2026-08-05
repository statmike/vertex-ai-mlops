"""Helpers for consuming the Discovery agent over A2A.

The concierge talks to Discovery as a remote agent. How it obtains Discovery's
agent card depends on how Discovery is running — and the two cases are genuinely
different, not just different URLs:

- **Local** — Discovery is a ``to_a2a()`` uvicorn server. ADK serves the card
  over HTTP at the A2A well-known path (``/.well-known/agent-card.json``). We hand
  ``RemoteA2aAgent`` that URL as a *string* and it resolves the card itself.
- **Deployed** — Discovery is an ``A2aAgent`` on Agent Runtime. The Runtime does
  **not** serve a fetchable card at any path; the card is embedded in the
  reasoningEngine resource's spec (``class_methods[].a2a_agent_card``) at deploy
  time, carrying a placeholder URL that ``A2aAgent.set_up()`` only rewrites in the
  serving process. So we read the card from the resource, retarget its primary
  interface to the live ``/a2a`` endpoint, and hand ``RemoteA2aAgent`` the
  resolved ``AgentCard`` *object*.

We detect the deployed case by the ``*-aiplatform.googleapis.com`` host, matching
the same signal auth.py uses to decide whether to attach credentials.

**Where the deployed card comes from.** Reading it from the resource needs the
``aiplatform.reasoningEngines.get`` control-plane permission — which the
concierge's own Runtime service agent does not have, and which would be a fragile
network call on every cold start anyway. Since the card is *static per
deployment*, ``deploy.py`` resolves it once at deploy time (with admin creds) and
bakes the retargeted card JSON into the concierge's ``DISCOVERY_A2A_CARD`` env
var. The deployed concierge just parses that env var — no control-plane call. The
resource read (:func:`_fetch_deployed_agent_card`) remains the fallback for
admin-credentialed contexts: local ``adk web`` against a deployed discovery, and
``deploy.py discovery --test``.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from a2a.utils.constants import AGENT_CARD_WELL_KNOWN_PATH

from config import GOOGLE_CLOUD_PROJECT, discovery_a2a_base_url

if TYPE_CHECKING:
    from a2a.types import AgentCard

# Google Cloud endpoints — the deployed Runtime lives here. Its card is embedded
# in the deployed resource, not served at a URL (unlike the local well-known card).
_GOOGLE_APIS_HOST = "googleapis.com"

# Env var carrying the already-resolved (retargeted) deployed discovery card JSON,
# baked in by deploy.py so the deployed concierge needs no control-plane read.
DISCOVERY_A2A_CARD_ENV = "DISCOVERY_A2A_CARD"


def _resource_name_from_a2a_url(a2a_url: str) -> str:
    """Reasoning-engine resource name from a deployed A2A base URL.

    ``https://{loc}-aiplatform.googleapis.com/v1beta1/projects/{p}/locations/{l}/
    reasoningEngines/{id}/a2a`` -> ``projects/{p}/locations/{l}/reasoningEngines/{id}``.
    """
    path = a2a_url.split("/aiplatform.googleapis.com/", 1)[-1]
    parts = path.split("/")
    if "projects" not in parts or "reasoningEngines" not in parts:
        raise ValueError(f"Not a reasoningEngines A2A URL: {a2a_url}")
    start = parts.index("projects")
    end = parts.index("reasoningEngines") + 2  # include the id segment
    return "/".join(parts[start:end])


def _location_from_resource_name(resource_name: str) -> str:
    parts = resource_name.split("/")
    return parts[parts.index("locations") + 1] if "locations" in parts else "us-central1"


def _fetch_deployed_agent_card(a2a_base_url: str) -> AgentCard:
    """Read the deployed discovery card from its Runtime resource and retarget it.

    The embedded card carries a placeholder URL (set_up() only rewrites it inside
    the serving process), so we point its primary interface at the live endpoint
    the concierge will actually call.
    """
    import vertexai
    from a2a.types import AgentCard
    from google.protobuf import json_format

    resource_name = _resource_name_from_a2a_url(a2a_base_url)
    location = _location_from_resource_name(resource_name)
    client = vertexai.Client(project=GOOGLE_CLOUD_PROJECT, location=location)
    agent = client.agent_engines.get(name=resource_name)

    card_json = agent.api_resource.spec.class_methods[0]["a2a_agent_card"]
    card = json_format.Parse(card_json, AgentCard())
    card.supported_interfaces[0].url = a2a_base_url
    return card


def deployed_agent_card_json(a2a_base_url: str) -> str:
    """Resolve the deployed discovery card and return it as retargeted JSON.

    Called by ``deploy.py`` (with admin creds) to bake a ready-to-parse card into
    the concierge's ``DISCOVERY_A2A_CARD`` env var, so the deployed concierge
    never makes a control-plane call. The JSON already carries the live endpoint
    URL, so :func:`_card_from_json` can hand it straight to ``RemoteA2aAgent``.
    """
    from google.protobuf import json_format

    return json_format.MessageToJson(_fetch_deployed_agent_card(a2a_base_url))


def _card_from_json(card_json: str) -> AgentCard:
    """Parse a baked-in card JSON string into an ``AgentCard`` object."""
    from a2a.types import AgentCard
    from google.protobuf import json_format

    return json_format.Parse(card_json, AgentCard())


def discovery_agent_card() -> str | AgentCard:
    """Value to pass to ``RemoteA2aAgent(agent_card=...)`` for the discovery agent.

    Three cases, in priority order:

    - **Deployed concierge** — ``DISCOVERY_A2A_CARD`` is set (baked in by
      deploy.py); parse it. This needs no control-plane call, which the
      concierge's Runtime service agent could not make anyway.
    - **Deployed discovery, admin creds** (local ``adk web`` / ``deploy --test``)
      — no baked card, but the base URL is a Runtime endpoint; read the card from
      the resource and retarget it.
    - **Local discovery** — the well-known card URL (a string ``RemoteA2aAgent``
      resolves over HTTP).
    """
    baked = os.getenv(DISCOVERY_A2A_CARD_ENV, "").strip()
    if baked:
        return _card_from_json(baked)
    base = discovery_a2a_base_url()
    if _GOOGLE_APIS_HOST in base:
        return _fetch_deployed_agent_card(base)
    return f"{base}/{AGENT_CARD_WELL_KNOWN_PATH.lstrip('/')}"
