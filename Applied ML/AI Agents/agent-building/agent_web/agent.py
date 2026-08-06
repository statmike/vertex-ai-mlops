"""agent_web — answers current-events questions with Google Search grounding.

Where the other agents read theLook's *internal* documents and data, this one
reaches the *public web* through ADK's built-in ``google_search`` tool: the model
issues search queries, the platform grounds the response in the results, and the
answer comes back with citations. It rounds out the tool story — hand-written
function tools (catalog/analytics/discovery), MCP-supplied tools
(``agent_mcp_client``), and now a built-in **grounding** tool.

Built-in grounding tools have a wiring constraint worth knowing: a grounding tool
can't be freely mixed with ordinary function tools in the same agent, so this
agent carries *only* ``google_search``. To offer web grounding alongside the
other specialists, add this agent as an in-process ``sub_agent`` of the concierge
(each agent keeps its own tool set) rather than adding the tool to an existing
agent.

Run locally:  ``uv run adk web agent_web``
"""

import os

from config import WEB_MODEL, WEB_MODEL_LOCATION

# Pick the inference endpoint before importing ADK (same pattern as the concierge).
if WEB_MODEL_LOCATION:
    os.environ["GOOGLE_CLOUD_LOCATION"] = WEB_MODEL_LOCATION

from google.adk.agents import Agent  # noqa: E402
from google.adk.tools import google_search  # noqa: E402

from . import prompts  # noqa: E402

root_agent = Agent(
    model=WEB_MODEL,
    name="agent_web",
    description=(
        "Answers questions needing current, external information from the public "
        "web (trends, competitor/market info, live status) with Google Search "
        "grounding and citations."
    ),
    global_instruction=prompts.global_instructions,
    instruction=prompts.agent_instructions,
    # Only the built-in grounding tool — see the module docstring on why it isn't
    # mixed with function tools.
    tools=[google_search],
)
