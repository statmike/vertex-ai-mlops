import os
from google.adk import agents
from . import prompts

# DEFINE TOOLS - Built-in Tools
from google.adk.tools import bigquery as bq_tools 
bq_toolset = bq_tools.BigQueryToolset(
    #credentials_config = credentials_config,
    bigquery_tool_config = bq_tools.config.BigQueryToolConfig(
        write_mode = bq_tools.config.WriteMode.BLOCKED, # BLOCKED=no writes, PROTECTED=only writes to temporary tables allowed, ALLOWED=write to permamnent tables also
        compute_project_id=os.getenv('GOOGLE_CLOUD_PROJECT') # set the compute project
    )
)
BUILTIN_BQ_TOOLS = [bq_toolset]

root_agent = agents.Agent(
    name = 'agent_bq_builtin',
    model = "gemini-2.5-flash",
    description = 'An agent that can use bigquery to try to answer any user question.',
    global_instruction = prompts.global_instructions,
    instruction = prompts.builtin_query_agent_instructions,
    tools = BUILTIN_BQ_TOOLS,
    disallow_transfer_to_parent=False,  # Allows transfers to parent (default)
    disallow_transfer_to_peers=True     # Prevents transfers to peers
)

# ============================================================
# BigQuery Agent Analytics Plugin
# Logs agent events to BigQuery for analysis and debugging.
# To disable: comment out the following 3 lines
# ============================================================
from bq_plugin import bq_analytics_plugin
from google.adk.apps import App
app = App(name="agent_bq_builtin", root_agent=root_agent, plugins=[bq_analytics_plugin])
# ============================================================