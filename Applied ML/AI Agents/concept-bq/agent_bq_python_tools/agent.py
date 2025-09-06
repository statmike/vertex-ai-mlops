from google.adk import agents
from . import prompts
from . import tools

# DEFINE TOOLS - Local Python Function Tools 
PYTHON_FUNCTION_TOOLS = tools.PYTHON_FUNCTION_TOOLS

root_agent = agents.Agent(
    name = 'agent_bq_python_tools',
    model = "gemini-2.0-flash",
    description = "An agent that can use Python functions to query BigQuery for the number of hurricanes per year.",
    global_instruction = prompts.global_instructions,
    instruction = prompts.python_tools_agent_instructions,
    tools = PYTHON_FUNCTION_TOOLS,
    disallow_transfer_to_parent=False,  # Allows transfers to parent (default)
    disallow_transfer_to_peers=True     # Prevents transfers to peers
)
