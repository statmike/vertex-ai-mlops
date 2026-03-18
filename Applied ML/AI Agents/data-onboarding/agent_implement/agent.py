from google.adk import agents

from agent_orchestrator.config import AGENT_MODEL

from . import prompts, tools

root_agent = agents.Agent(
    name="agent_implement",
    model=AGENT_MODEL,
    description="Creates BigQuery tables from GCS source files, applies metadata (descriptions, labels), and maintains the onboarding changelog.",
    global_instruction=prompts.global_instructions,
    instruction=prompts.agent_instructions,
    tools=tools.TOOLS,
)
