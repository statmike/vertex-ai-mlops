from google.adk import agents

from agent_orchestrator.config import AGENT_MODEL

from . import prompts, tools

root_agent = agents.Agent(
    name="agent_design",
    model=AGENT_MODEL,
    description="Proposes BigQuery table structures with column types, descriptions, partitioning, and clustering based on analyzed schemas and context.",
    global_instruction=prompts.global_instructions,
    instruction=prompts.agent_instructions,
    tools=tools.TOOLS,
)
