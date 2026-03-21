from google.adk import agents

from agent_orchestrator.config import AGENT_MODEL_INSTANCE as AGENT_MODEL

from . import prompts, tools

root_agent = agents.Agent(
    name="agent_understand",
    model=AGENT_MODEL,
    description="Reads and analyzes file contents, infers schemas, and cross-references data files with context documents to build understanding.",
    global_instruction=prompts.global_instructions,
    instruction=prompts.agent_instructions,
    tools=tools.TOOLS,
)
