from google.adk import agents

from agent_orchestrator.config import AGENT_MODEL_INSTANCE as AGENT_MODEL

from . import prompts, tools

root_agent = agents.Agent(
    name="agent_engineer",
    model=AGENT_MODEL,
    description=(
        "Answers questions about the data onboarding pipeline: processing logs, "
        "lineage, schema decisions, source manifests, and web provenance."
    ),
    global_instruction=prompts.global_instructions,
    instruction=prompts.agent_instructions,
    tools=tools.TOOLS,
    disallow_transfer_to_parent=False,
    disallow_transfer_to_peers=True,
)
