from google.adk import agents
from . import prompts
#from . import callbacks
from . import tools
import toolbox_core

toolbox_client = toolbox_core.ToolboxSyncClient("http://localhost:7000")



root_agent = agents.Agent(
    name = "concept_bq",
    model = "gemini-2.0-flash",
    description = 'The primary agent that processes users questions.',
    global_instruction = prompts.global_instructions,
    instruction = prompts.root_agent_instuctions,
    #sub_agents = [],
    tools = toolbox_client.load_toolset('bq-concept') + tools.BQ_QUERY_TOOLS,
    #after_tool_callback = callbacks.process_toolbox_output,
)

