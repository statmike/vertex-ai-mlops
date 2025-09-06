from google.adk import agents
from . import prompts
from . import callbacks

# DEFINE TOOLS - MCP TOOLBOX Tools
import toolbox_core
toolbox_client = toolbox_core.ToolboxSyncClient("http://localhost:7000")
MCP_TOOLBOX_DYNAMIC_TOOLS = toolbox_client.load_toolset('mcp_toolbox_dynamic_sql')

root_agent = agents.Agent(
    name = 'agent_mcp_toolbox_dynamic',
    model = "gemini-2.0-flash",
    description = "An agent that can query table metadata and write SQL queries based on user questions about hurricanes.",
    global_instruction = prompts.global_instructions,
    instruction = prompts.mcp_query_agent_instructions,
    tools = MCP_TOOLBOX_DYNAMIC_TOOLS,
    before_tool_callback = callbacks.sql_dry_run_callback,
    disallow_transfer_to_parent=False,  # Allows transfers to parent (default)
    disallow_transfer_to_peers=True     # Prevents transfers to peers
)