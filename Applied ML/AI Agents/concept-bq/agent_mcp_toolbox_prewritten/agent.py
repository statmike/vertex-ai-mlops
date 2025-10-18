from google.adk import agents
from . import prompts

# DEFINE TOOLS - MCP TOOLBOX Tools
import toolbox_core
toolbox_client = toolbox_core.ToolboxSyncClient("http://localhost:7000")
MCP_TOOLBOX_PREDEFINED_TOOLS = toolbox_client.load_toolset('mcp_toolbox_predefined_sql')

root_agent = agents.Agent(
    name = 'agent_mcp_toolbox_prewritten',
    model = "gemini-2.5-flash",
    description = "An agent that can use pre-written SQL queries to answer questions about hurricane wind speeds.",
    global_instruction = prompts.global_instructions,
    instruction = prompts.prewritten_query_agent_instructions,
    tools = MCP_TOOLBOX_PREDEFINED_TOOLS,
    disallow_transfer_to_parent=False,  # Allows transfers to parent (default)
    disallow_transfer_to_peers=True     # Prevents transfers to peers
)
