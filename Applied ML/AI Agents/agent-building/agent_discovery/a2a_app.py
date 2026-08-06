"""Native-A2A deployable for the discovery agent (Agent Runtime, object mode).

Discovery is the independently-deployable half of the system: it ships on its own
lifecycle and the concierge reaches it over A2A. Unlike an ``AdkApp`` (which Agent
Runtime serves as a plain reasoning engine and does *not* expose an A2A card),
this uses the ``A2aAgent`` template so the deployed Runtime speaks the **A2A
protocol natively** — it serves the agent card and the message/task RPCs at
``{resource}/a2a`` and advertises the authenticated card at ``{a2a_url}/v1/card``.

That native path is the reason this project runs on ADK 2.x + a2a-sdk 1.x:
``A2aAgent`` requires A2A protocol **v1.0** types (``TransportProtocol``,
``PROTOCOL_VERSION_CURRENT``), which only exist in a2a-sdk 1.x — and google-adk
pins ``a2a-sdk<0.4`` on every 1.x release, lifting the cap only at 2.5.0.

**Why this lives in ``agent_discovery/`` and not ``deploy/``:** object-mode
deployment cloudpickles the ``A2aAgent`` *by reference* — the pickle records the
module path of ``agent_executor_builder`` and the card, and the remote container
re-imports them. Only ``agent_discovery`` (plus ``config.py``) is shipped as an
extra package, so these builders must live here to resolve remotely. ``deploy/``
just re-exports ``app``.

How it is wired:
  * ``AgentCardBuilder`` turns the ADK ``root_agent`` into a v1.0 agent card
    (name, description, skills). ADK stamps the primary interface as ``JSONRPC``;
    the ``A2aAgent`` template and the Runtime REST routes require ``HTTP+JSON``,
    so we retarget the primary interface's binding before handing the card over.
  * ``A2aAgentExecutor`` (fed a fresh ADK ``Runner`` per invocation) is the
    executor that actually runs the agent when a message arrives.
  * ``A2aAgent`` composes the card + executor into an object deployable by
    ``agent_engines.create`` — it exposes the ``a2a_extension`` operation set the
    Runtime mounts to serve A2A.

The card's advertised URL is a placeholder here; ``A2aAgent.set_up()`` rewrites
it to the live ``reasoningEngines/{id}/a2a`` URL at deploy time.
"""

import asyncio
import concurrent.futures

from a2a.utils.constants import PROTOCOL_VERSION_CURRENT, TransportProtocol
from google.adk.a2a.executor.a2a_agent_executor import A2aAgentExecutor
from google.adk.a2a.utils.agent_card_builder import AgentCardBuilder
from google.adk.artifacts.in_memory_artifact_service import InMemoryArtifactService
from google.adk.auth.credential_service.in_memory_credential_service import (
    InMemoryCredentialService,
)
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from vertexai.agent_engines.templates.a2a import A2aAgent

from agent_discovery.agent import root_agent
from agent_discovery.skills import apply_skills

# Placeholder RPC URL — A2aAgent.set_up() overwrites this with the real
# reasoningEngines/{id}/a2a URL once the Runtime resource exists.
_PLACEHOLDER_RPC_URL = "https://placeholder.invalid/a2a"


def _run_sync(coro):
    """Run an async coroutine to completion from a sync context, loop-safe.

    This module is imported both locally (no running loop — ``asyncio.run`` is
    fine) and, in object-mode deploy, by the Runtime's cloudpickle loader *inside*
    a running event loop (``asyncio.run`` would raise "cannot be called from a
    running event loop"). When a loop is already running, run the coroutine on a
    worker thread with its own loop instead.
    """
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(asyncio.run, coro).result()


def build_agent_card():
    """Build a v1.0 A2A agent card from the ADK root agent.

    ADK's builder stamps the primary interface as JSONRPC, but both the A2aAgent
    template and Agent Runtime's REST routes require HTTP+JSON on the primary
    interface, so we retarget it here. We also replace the auto-derived skills
    with the explicit, richly-described ones (see agent_discovery/skills.py) so
    the deployed card advertises the same capabilities a consumer sees locally.
    """
    builder = AgentCardBuilder(agent=root_agent, rpc_url=_PLACEHOLDER_RPC_URL)
    card = _run_sync(builder.build())
    primary = card.supported_interfaces[0]
    primary.protocol_binding = TransportProtocol.HTTP_JSON
    primary.protocol_version = PROTOCOL_VERSION_CURRENT
    return apply_skills(card)


def create_runner() -> Runner:
    """A fresh ADK Runner for the discovery agent (in-memory services)."""
    return Runner(
        app_name=root_agent.name or "agent_discovery",
        agent=root_agent,
        artifact_service=InMemoryArtifactService(),
        session_service=InMemorySessionService(),
        memory_service=InMemoryMemoryService(),
        credential_service=InMemoryCredentialService(),
    )


def build_executor() -> A2aAgentExecutor:
    """Executor that runs the ADK agent for each incoming A2A message."""
    return A2aAgentExecutor(runner=create_runner, use_legacy=False)


app = A2aAgent(agent_card=build_agent_card(), agent_executor_builder=build_executor)
