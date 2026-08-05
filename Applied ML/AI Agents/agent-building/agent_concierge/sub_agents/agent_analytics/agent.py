"""Analytics sub-agent — BigQuery Q&A over theLook via the Conversational Analytics API.

Model: Gemini 3 Flash-Lite (fast, cheap; the CA API does the heavy lifting).
"""

from google.adk.agents import Agent

from config import ANALYTICS_MODEL

from . import prompts, tools

analytics_agent = Agent(
    model=ANALYTICS_MODEL,
    name="agent_analytics",
    description=(
        "Answers quantitative questions about theLook's sales, orders, products, "
        "and customers using live BigQuery data."
    ),
    global_instruction=prompts.global_instructions,
    instruction=prompts.agent_instructions,
    tools=tools.TOOLS,
)
