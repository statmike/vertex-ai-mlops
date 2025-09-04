from google.adk import agents
from . import prompts
from . import callbacks

############################### IMPORT TOOLS ###############################

# Function Tools
from . import tools
PYTHON_FUNCTION_TOOLS = tools.PYTHON_FUNCTION_TOOLS

# MCP Tools:
import toolbox_core
toolbox_client = toolbox_core.ToolboxSyncClient("http://localhost:7000")
MCP_TOOLBOX_PREDEFINED_TOOLS = toolbox_client.load_toolset('mcp_toolbox_predefined_sql')
MCP_TOOLBOX_DYNAMIC_TOOLS = toolbox_client.load_toolset('mcp_toolbox_dynamic_sql')

# Built-in Tools

# dont need auth for this local testing method which uses the authed user session
#import google.auth
#application_default_credentials, _ = google.auth.default()
#credentials_config = bq_tools.BigQueryCredentialsConfig(credentials = application_default_credentials),

from google.adk.tools import bigquery as bq_tools 
bq_toolset = bq_tools.BigQueryToolset(
    #credentials_config = credentials_config,
    bigquery_tool_config = bq_tools.config.BigQueryToolConfig(write_mode = bq_tools.config.WriteMode.BLOCKED)
)
BUILTIN_BQ_TOOLS = [bq_toolset]

############################################################################

builtin_query_agent = agents.Agent(
    name = 'builtin_query_agent',
    model = "gemini-2.0-flash",
    description = 'An agent that can use bigquery to try to answer any user question.',
    global_instruction = prompts.global_instructions,
    instruction = prompts.builtin_query_agent_instructions,
    tools = BUILTIN_BQ_TOOLS,
)

mcp_toolbox_dynamic_agent = agents.Agent(
    name = 'mcp_toolbox_dynamic_agent',
    model = "gemini-2.0-flash",
    description = "An agent that can query table metadata and write SQL queries based on user questions about hurricanes.",
    global_instruction = prompts.global_instructions,
    instruction = prompts.mcp_query_agent_instructions,
    tools = MCP_TOOLBOX_DYNAMIC_TOOLS,
    before_tool_callback = callbacks.sql_dry_run_callback
)

root_agent = agents.Agent(
    name = "concept_bq",
    model = "gemini-2.0-flash",
    description = 'The primary agent that processes users questions.',
    global_instruction = prompts.global_instructions,
    instruction = prompts.root_agent_instuctions,
    sub_agents = [
        mcp_toolbox_dynamic_agent,
        builtin_query_agent
    ],
    tools =  MCP_TOOLBOX_PREDEFINED_TOOLS + PYTHON_FUNCTION_TOOLS,
    #after_tool_callback = callbacks.process_toolbox_output,
)