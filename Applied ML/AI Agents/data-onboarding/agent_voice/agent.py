import os

from google.adk import agents

from . import prompts, tools

# Use a lightweight model import that doesn't trigger agent_orchestrator's
# __init__.py (which would pull in agent_implement → pandas and other heavy
# deps not available in the UI venv). The model is always overridden via
# clone() in _get_voice_runner() anyway.
_DEFAULT_MODEL = os.environ.get("AGENT_MODEL", "gemini-2.5-flash")

root_agent = agents.Agent(
    name="agent_voice",
    model=_DEFAULT_MODEL,  # Overridden with voice model at runtime
    description="Voice assistant for conversational data exploration.",
    global_instruction=prompts.global_instructions,
    instruction=prompts.agent_instructions,
    tools=tools.TOOLS,
)
