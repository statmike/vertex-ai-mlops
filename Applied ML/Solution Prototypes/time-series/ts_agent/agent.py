from google.adk import agents
from . import tools
from . import prompts
from toolbox_core import ToolboxSyncClient


with ToolboxSyncClient("http://localhost:7000") as toolbox_client:
    agent_toolset = toolbox_client.load_toolset('ts-toolset')
    root_agent = agents.Agent(
        name = "ts_agent",
        model = "gemini-2.0-flash",
        description = 'The primary agent that processes time-series data.',
        global_instruction = prompts.global_instructions,
        instruction = prompts.root_agent_instuctions,
        #sub_agents = [],
        #tools = tools.DOCUMENT_PROCESSING_TOOLS,
        tools = agent_toolset,
    )