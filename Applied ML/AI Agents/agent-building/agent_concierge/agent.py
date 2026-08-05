"""Concierge — the root router (Gemini 3 Pro).

Demonstrates BOTH composition styles a Google developer reaches for:

- **In-process sub-agents** (agent_catalog, agent_analytics): tight coupling, low
  latency, one deployable. Wired via ADK ``sub_agents=[...]``.
- **A2A remote agent** (agent_discovery): its own service with an independent
  lifecycle, consumed as a ``RemoteA2aAgent`` pointed at the discovery agent's
  card URL. Locally that server runs via ``uvicorn`` (see the README); in
  production it deploys separately to Agent Runtime.

The router never answers specialist questions itself — it classifies and delegates.
"""

import os

from config import AGENT_MODEL, AGENT_MODEL_LOCATION

# ADK reads GOOGLE_CLOUD_LOCATION to pick the Vertex inference endpoint, so set it
# to where the router's model is served before importing ADK.
if AGENT_MODEL_LOCATION:
    os.environ["GOOGLE_CLOUD_LOCATION"] = AGENT_MODEL_LOCATION

from google.adk.agents import Agent  # noqa: E402
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent  # noqa: E402
from google.adk.apps import App  # noqa: E402

from config import discovery_a2a_base_url  # noqa: E402

from . import prompts  # noqa: E402
from .bq_plugin import bq_analytics_plugin  # noqa: E402
from .sub_agents.agent_analytics.agent import analytics_agent  # noqa: E402
from .sub_agents.agent_catalog.agent import catalog_agent  # noqa: E402
from .utils import (  # noqa: E402
    MEMORY_TOOLS,
    add_session_to_memory,
    authed_httpx_client_for,
    discovery_agent_card,
)

# Discovery is a separate deployable, reached over A2A. Locally its card is a
# well-known URL string (RemoteA2aAgent resolves it over HTTP); deployed, the
# Runtime serves no fetchable card, so discovery_agent_card() returns the
# AgentCard object read from the resource spec (see utils/a2a.py). The auth client
# keys off the *base* URL — a token-refreshing client for a Runtime endpoint, None
# for localhost (where RemoteA2aAgent builds its own plain client).
_discovery_base_url = discovery_a2a_base_url()
discovery_agent = RemoteA2aAgent(
    name="agent_discovery",
    description=(
        "Finds datasets and tables in theLook's data catalog and explains what "
        "each contains. Runs as a separate A2A service."
    ),
    agent_card=discovery_agent_card(),
    httpx_client=authed_httpx_client_for(_discovery_base_url),
    # A2A protocol v1.0: talk to the discovery service over the current protocol,
    # not the v0.3 legacy path. Requires a2a-sdk 1.x (ADK 2.x) on both ends.
    use_legacy=False,
)

root_agent = Agent(
    model=AGENT_MODEL,
    name="agent_concierge",
    description="Front-door router that delegates retail questions to specialists.",
    global_instruction=prompts.global_instructions,
    instruction=prompts.agent_instructions,
    sub_agents=[catalog_agent, analytics_agent, discovery_agent],
    # Scale pillar: recall past turns from Memory Bank, and persist each finished
    # turn back into it. Both are no-ops locally without a memory service.
    tools=MEMORY_TOOLS,
    after_agent_callback=add_session_to_memory,
)

# App bundles the root agent with the observability plugin (None-guarded, so the
# list is empty when GOOGLE_CLOUD_PROJECT is unset).
app = App(
    name="agent_concierge",
    root_agent=root_agent,
    plugins=[p for p in [bq_analytics_plugin] if p],
)
