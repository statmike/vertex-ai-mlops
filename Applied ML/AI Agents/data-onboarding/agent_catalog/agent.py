from google.adk import agents

from agent_orchestrator.config import AGENT_MODEL_INSTANCE as AGENT_MODEL

from . import prompts, tools

root_agent = agents.Agent(
    name="agent_catalog",
    model=AGENT_MODEL,
    description=(
        "Answers questions about data meaning, column definitions, table "
        "documentation, and relationships. Uses semantic search over indexed "
        "documentation."
    ),
    global_instruction=prompts.global_instructions,
    instruction=prompts.agent_instructions,
    tools=tools.TOOLS,
    disallow_transfer_to_parent=False,
    disallow_transfer_to_peers=True,
)
