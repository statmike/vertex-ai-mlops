from google.adk import agents
from . import tools
from . import prompts

root_agent = agents.Agent(
    name = "ts_agent",
    model = "gemini-2.0-flash",
    description = 'The primary agent that processes time-series data.',
    global_instruction = prompts.global_instructions,
    instruction = prompts.root_agent_instructions,
    #sub_agents = [],
    #tools = tools.DOCUMENT_PROCESSING_TOOLS,
)