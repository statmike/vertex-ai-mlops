from google.adk import agents

from agent_orchestrator.config import AGENT_MODEL

from . import prompts, tools

root_agent = agents.Agent(
    name="agent_acquire",
    model=AGENT_MODEL,
    description="Acquires data from URLs or GCS paths — crawls web pages, downloads files, and extracts page content as context documents.",
    global_instruction=prompts.global_instructions,
    instruction=prompts.agent_instructions,
    tools=tools.TOOLS,
)
