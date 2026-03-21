import os

# Model and location configuration (read early, before ADK imports).
# ADK uses GOOGLE_CLOUD_LOCATION to determine the Vertex AI API endpoint,
# so AGENT_MODEL_LOCATION overrides it if set.
AGENT_MODEL_LOCATION = os.getenv("AGENT_MODEL_LOCATION", "")
if AGENT_MODEL_LOCATION:
    os.environ["GOOGLE_CLOUD_LOCATION"] = AGENT_MODEL_LOCATION

from google.adk import agents  # noqa: E402

from .config import AGENT_MODEL_INSTANCE as AGENT_MODEL  # noqa: E402

from agent_acquire.agent import root_agent as acquire_agent  # noqa: E402
from agent_design.agent import root_agent as design_agent  # noqa: E402
from agent_discover.agent import root_agent as discover_agent  # noqa: E402
from agent_implement.agent import root_agent as implement_agent  # noqa: E402
from agent_understand.agent import root_agent as understand_agent  # noqa: E402
from agent_validate.agent import root_agent as validate_agent  # noqa: E402

from . import prompts, tools  # noqa: E402

root_agent = agents.Agent(
    name="agent_orchestrator",
    model=AGENT_MODEL,
    description="Root orchestrator that coordinates data onboarding into BigQuery through a pipeline of specialized agents.",
    global_instruction=prompts.global_instructions,
    instruction=prompts.agent_instructions,
    tools=tools.TOOLS,
    sub_agents=[
        acquire_agent,
        discover_agent,
        understand_agent,
        design_agent,
        implement_agent,
        validate_agent,
    ],
)

# ============================================================
# BigQuery Agent Analytics Plugin
# Logs agent events to BigQuery for analysis and debugging.
# Auto-creates dataset and table on first run if they don't exist.
# To disable: comment out the following 3 lines
# ============================================================
from google.adk.apps import App  # noqa: E402

from .bq_plugin import bq_analytics_plugin  # noqa: E402

app = App(
    name="agent_orchestrator",
    root_agent=root_agent,
    plugins=[p for p in [bq_analytics_plugin] if p],
)
# ============================================================
