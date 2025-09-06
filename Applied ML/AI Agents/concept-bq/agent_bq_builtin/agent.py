from google.adk import agents
from . import prompts

# DEFINE TOOLS - Built-in Tools
from google.adk.tools import bigquery as bq_tools 
bq_toolset = bq_tools.BigQueryToolset(
    #credentials_config = credentials_config,
    bigquery_tool_config = bq_tools.config.BigQueryToolConfig(write_mode = bq_tools.config.WriteMode.BLOCKED)
)
BUILTIN_BQ_TOOLS = [bq_toolset]

root_agent = agents.Agent(
    name = 'agent_bq_builtin',
    model = "gemini-2.0-flash",
    description = 'An agent that can use bigquery to try to answer any user question.',
    global_instruction = prompts.global_instructions,
    instruction = prompts.builtin_query_agent_instructions,
    tools = BUILTIN_BQ_TOOLS,
    disallow_transfer_to_parent=False,  # Allows transfers to parent (default)
    disallow_transfer_to_peers=True     # Prevents transfers to peers
)