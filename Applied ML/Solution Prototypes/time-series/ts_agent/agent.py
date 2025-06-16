from google.adk import agents
from . import prompts
from . import callbacks
from . import tools
from toolbox_core import ToolboxSyncClient

toolbox_client = ToolboxSyncClient("http://localhost:7000")

root_agent = agents.Agent(
    name = "ts_agent",
    model = "gemini-2.0-flash",
    description = 'The primary agent that processes time-series data.',
    global_instruction = prompts.global_instructions,
    instruction = prompts.root_agent_instuctions,
    #sub_agents = [],
    tools = toolbox_client.load_toolset('ts-toolset') + tools.TS_TOOLS,
    after_tool_callback = callbacks.process_toolbox_output,
)