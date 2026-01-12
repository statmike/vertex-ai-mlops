from google.adk import agents
from . import prompts

# IMPORT SUB-AGENTS
from agent_bq_builtin.agent import root_agent as agent_bq_builtin
from agent_mcp_toolbox_dynamic.agent import root_agent as agent_mcp_toolbox_dynamic
from agent_mcp_toolbox_prewritten.agent import root_agent as agent_mcp_toolbox_prewritten
from agent_bq_python_tools.agent import root_agent as agent_bq_python_tools
from agent_convo_api.agent import root_agent as agent_convo_api

root_agent = agents.Agent(
    name = "agent_concept_bq",
    model = "gemini-2.5-flash",
    description = 'The primary agent that processes users questions.',
    global_instruction = prompts.global_instructions,
    instruction = prompts.root_agent_instuctions,
    sub_agents = [
        agent_mcp_toolbox_dynamic,
        agent_bq_builtin,
        agent_mcp_toolbox_prewritten,
        agent_bq_python_tools,
        agent_convo_api
    ],
    #tools =  [],
    #disallow_transfer_to_parent=False,  # Allows transfers to parent (default)
    #disallow_transfer_to_peers=True     # Prevents transfers to peers
)

# ============================================================
# BigQuery Agent Analytics Plugin
# Logs agent events to BigQuery for analysis and debugging.
# To disable: comment out the following 3 lines
# ============================================================
from bq_plugin import bq_analytics_plugin
from google.adk.apps import App
app = App(name="agent_concept_bq", root_agent=root_agent, plugins=[bq_analytics_plugin])
# ============================================================