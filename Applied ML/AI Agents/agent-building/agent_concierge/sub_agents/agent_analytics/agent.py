"""Analytics sub-agent — BigQuery Q&A over theLook via the Conversational Analytics API.

Model: Gemini 3 Flash-Lite (fast, cheap; the CA API does the heavy lifting).
"""

from google.adk.agents import Agent

from config import ANALYTICS_MODEL

from . import prompts, tools
from .examples import example_tool

# Attach the Example Store few-shot tool when configured (None-guarded). It steers
# answers with the most similar curated examples per question; omitted when the
# store isn't provisioned, so the agent behaves identically either way.
_tools = [*tools.TOOLS, *([example_tool] if example_tool else [])]

analytics_agent = Agent(
    model=ANALYTICS_MODEL,
    name="agent_analytics",
    description=(
        "Answers quantitative questions about theLook's sales, orders, products, "
        "and customers using live BigQuery data."
    ),
    global_instruction=prompts.global_instructions,
    instruction=prompts.agent_instructions,
    tools=_tools,
)
