"""Discovery agent — Knowledge Catalog search, powered by Claude on Vertex.

This agent is deliberately **independent**: it is not an in-process sub-agent of
the concierge. It is its own deployable and is consumed over the A2A protocol.
That demonstrates the production pattern where a capability owned by another team
scales and ships on its own lifecycle.

Model variety: this one runs on Claude (Opus) served from Vertex AI Model Garden,
alongside the Gemini 3 agents elsewhere in the project.

Serving:
    Local  — `to_a2a()` builds an ASGI app served by uvicorn (see project README).
    Deployed — packaged for Agent Runtime in deploy/ (Phase 2).
"""

from google.adk.a2a.utils.agent_to_a2a import to_a2a
from google.adk.agents import Agent
from google.adk.models.anthropic_llm import Claude

from config import (
    DISCOVERY_A2A_PORT,
    DISCOVERY_MODEL,
    DISCOVERY_MODEL_LOCATION,
    GOOGLE_CLOUD_PROJECT,
)

from . import prompts, tools

# The ADK Claude wrapper reads GOOGLE_CLOUD_LOCATION at *request* time to pick the
# Model Garden region — but when deployed, the A2aAgent Runtime template rewrites
# that env var to the infra region (us-central1) during set_up(), where Claude
# may not be servable. Passing the model as a fully-qualified resource path pins
# the region inside the model string, which the wrapper parses in preference to
# the env var (see anthropic_llm._anthropic_client), so it's correct both locally
# and deployed regardless of what GOOGLE_CLOUD_LOCATION holds at request time.
_DISCOVERY_MODEL_PATH = (
    f"projects/{GOOGLE_CLOUD_PROJECT}/locations/{DISCOVERY_MODEL_LOCATION}"
    f"/publishers/anthropic/models/{DISCOVERY_MODEL}"
    if GOOGLE_CLOUD_PROJECT
    else DISCOVERY_MODEL
)

root_agent = Agent(
    model=Claude(model=_DISCOVERY_MODEL_PATH),
    name="agent_discovery",
    description=(
        "Finds datasets and tables in theLook's data catalog and explains what "
        "each contains. Answers 'what data do you have about X?'."
    ),
    global_instruction=prompts.global_instructions,
    instruction=prompts.agent_instructions,
    tools=tools.TOOLS,
)

# A2A application: `uvicorn agent_discovery.agent:a2a_app --port <DISCOVERY_A2A_PORT>`.
a2a_app = to_a2a(root_agent, port=DISCOVERY_A2A_PORT)
