"""agent_catalog — answers policy/help questions from unstructured documents.

Model: Gemini 3 Flash (fast, grounded document QA). Runs as an in-process
sub-agent of the concierge — tight coupling, low latency, one deployable.
"""

from google.adk.agents import Agent

from config import CATALOG_MODEL

from . import prompts, tools

catalog_agent = Agent(
    model=CATALOG_MODEL,
    name="agent_catalog",
    description=(
        "Answers questions about store policies and help content — returns, "
        "shipping, sizing, product care, warranties — from written documents."
    ),
    global_instruction=prompts.global_instructions,
    instruction=prompts.agent_instructions,
    tools=tools.TOOLS,
)
