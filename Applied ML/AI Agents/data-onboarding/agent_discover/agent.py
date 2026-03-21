from google.adk import agents

from agent_orchestrator.config import AGENT_MODEL_INSTANCE as AGENT_MODEL

from . import prompts, tools

root_agent = agents.Agent(
    name="agent_discover",
    model=AGENT_MODEL,
    description="Inventories staged files, classifies them as data or context, and detects changes from prior onboarding runs.",
    global_instruction=prompts.global_instructions,
    instruction=prompts.agent_instructions,
    tools=tools.TOOLS,
)
