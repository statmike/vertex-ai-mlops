"""Tools agent — answers questions using lookup, calculation, and explanation tools.

This sub-agent demonstrates two tool patterns:
- lookup/calculate: pure programmatic tools (no LLM calls)
- explain: calls Gemini directly via google-genai for richer answers
"""

from google.adk.agents import Agent

from config import TOOL_MODEL  # sub-agents with tools use the tool model

from .tools import calculate, explain, lookup

tools_agent = Agent(
    model=TOOL_MODEL,
    name="agent_tools",
    description="Answers factual questions, performs calculations, and explains topics in depth.",
    instruction="""You are a helpful assistant with three tools:

    1. **lookup** — Search a knowledge base of solar system facts. Use this for quick
       facts about planets, moons, distances, or other space topics.

    2. **calculate** — Evaluate math expressions. Use this when the user asks you
       to compute something (add, multiply, convert units, etc.).

    3. **explain** — Get a detailed explanation of a topic using Gemini. Use this
       when the user asks "why" or "how" questions, or wants more depth than the
       knowledge base provides (e.g., "why is Mars red?", "how do Saturn's rings form?").

    Choose the right tool for the question:
    - Simple facts → lookup
    - Math → calculate
    - Deep explanations → explain

    Keep responses concise.""",
    tools=[lookup, calculate, explain],
)
