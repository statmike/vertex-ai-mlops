from google.adk import agents

from agent_orchestrator.config import AGENT_MODEL

from . import prompts, tools

root_agent = agents.Agent(
    name="agent_validate",
    model=AGENT_MODEL,
    description="Runs quality checks on onboarded data — validates row counts, data types, null rates, and verifies full lineage from source to BQ table.",
    global_instruction=prompts.global_instructions,
    instruction=prompts.agent_instructions,
    tools=tools.TOOLS,
)
