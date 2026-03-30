"""Root agent — routes user messages to the right sub-agent.

This is the entry point for the multi-agent system. It delegates to:
- agent_greeter: for greetings and introductions
- agent_tools: for factual questions and calculations

ADK handles agent transfers automatically — the root agent decides which
sub-agent should handle the request, and the framework manages the handoff.
"""

import os

from google.adk.agents import Agent

from config import AGENT_MODEL, AGENT_MODEL_LOCATION  # router uses the agent model

# ADK uses GOOGLE_CLOUD_LOCATION for the Gemini API endpoint. Override it
# with AGENT_MODEL_LOCATION so preview models on 'global' work correctly,
# even when GOOGLE_CLOUD_LOCATION is set to a region like 'us-central1'
# for Agent Engine deployment.
if AGENT_MODEL_LOCATION:
    os.environ["GOOGLE_CLOUD_LOCATION"] = AGENT_MODEL_LOCATION

from agent_greeter.agent import greeter_agent
from agent_tools.agent import tools_agent


root_agent = Agent(
    model=AGENT_MODEL,
    name="agent_router",
    description="Routes user messages to the appropriate specialist agent.",
    instruction="""You are a router that delegates to specialist agents.

    **Routing rules:**
    - Greetings, hellos, "what can you do?" → transfer to **agent_greeter**
    - Questions about planets, space, the solar system → transfer to **agent_tools**
    - Math or calculation requests → transfer to **agent_tools**

    Always transfer — never answer directly. Pick the best agent and hand off.""",
    sub_agents=[greeter_agent, tools_agent],
)
