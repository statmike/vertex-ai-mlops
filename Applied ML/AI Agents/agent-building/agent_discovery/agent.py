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

import os

from google.adk.a2a.utils.agent_to_a2a import to_a2a
from google.adk.agents import Agent
from google.adk.models.anthropic_llm import Claude

from config import (
    DISCOVERY_A2A_PORT,
    DISCOVERY_MODEL,
    DISCOVERY_MODEL_LOCATION,
)

from . import prompts, tools

# The ADK Claude wrapper builds its AnthropicVertex client from these env vars at
# request time, so pin the location to where Claude is served before use.
os.environ["GOOGLE_CLOUD_LOCATION"] = DISCOVERY_MODEL_LOCATION

root_agent = Agent(
    model=Claude(model=DISCOVERY_MODEL),
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
