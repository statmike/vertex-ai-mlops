from google.adk import agents

from agent_orchestrator.config import AGENT_MODEL_INSTANCE as AGENT_MODEL

from . import prompts, tools

root_agent = agents.Agent(
    name="agent_context",
    model=AGENT_MODEL,
    description="Discovers relevant BigQuery datasets and tables for a user's question by querying metadata catalogs and table documentation.",
    global_instruction=prompts.global_instructions,
    instruction=prompts.agent_instructions,
    tools=tools.TOOLS,
)
