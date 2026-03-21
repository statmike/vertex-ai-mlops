import os

# Model and location configuration (read early, before ADK imports).
AGENT_MODEL_LOCATION = os.getenv("AGENT_MODEL_LOCATION", "")
if AGENT_MODEL_LOCATION:
    os.environ["GOOGLE_CLOUD_LOCATION"] = AGENT_MODEL_LOCATION

from google.adk import agents  # noqa: E402

from agent_orchestrator.config import AGENT_MODEL_INSTANCE as AGENT_MODEL  # noqa: E402

from agent_context.agent import root_agent as context_agent  # noqa: E402
from agent_convo.agent import root_agent as convo_agent  # noqa: E402

from . import prompts  # noqa: E402

root_agent = agents.Agent(
    name="agent_chat",
    model=AGENT_MODEL,
    description="Chat orchestrator for conversational analytics over onboarded BigQuery data.",
    global_instruction=prompts.global_instructions,
    instruction=prompts.agent_instructions,
    sub_agents=[context_agent, convo_agent],
)

# ============================================================
# BigQuery Agent Analytics Plugin
# Logs agent events to BigQuery for analysis and debugging.
# To disable: comment out the following lines
# ============================================================
from google.adk.apps import App  # noqa: E402

from agent_orchestrator.bq_plugin import bq_analytics_plugin  # noqa: E402

app = App(
    name="agent_chat",
    root_agent=root_agent,
    plugins=[p for p in [bq_analytics_plugin] if p],
)
# ============================================================
