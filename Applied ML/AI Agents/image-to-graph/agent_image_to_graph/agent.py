import os

# Model and location configuration (read early, before ADK imports).
# ADK uses GOOGLE_CLOUD_LOCATION to determine the Vertex AI API endpoint,
# so AGENT_MODEL_LOCATION overrides it if set.
AGENT_MODEL = os.getenv('AGENT_MODEL', 'gemini-2.5-flash')
AGENT_MODEL_LOCATION = os.getenv('AGENT_MODEL_LOCATION', '')
if AGENT_MODEL_LOCATION:
    os.environ['GOOGLE_CLOUD_LOCATION'] = AGENT_MODEL_LOCATION

from google.adk import agents
from . import prompts
from . import tools
from agent_graph_qa.agent import root_agent as qa_agent

root_agent = agents.Agent(
    name = "agent_image_to_graph",
    model = AGENT_MODEL,
    description = "An agent that converts diagram images into structured graph representations (nodes + edges + attributes).",
    global_instruction = prompts.global_instructions,
    instruction = prompts.agent_instructions,
    tools = tools.TOOLS,
    sub_agents = [qa_agent],
)

# ============================================================
# BigQuery Agent Analytics Plugin
# Logs agent events to BigQuery for analysis and debugging.
# Auto-creates dataset and table on first run if they don't exist.
# To disable: comment out the following 3 lines
# ============================================================
from .bq_plugin import bq_analytics_plugin
from google.adk.apps import App
app = App(name="agent_image_to_graph", root_agent=root_agent, plugins=[bq_analytics_plugin])
# ============================================================
