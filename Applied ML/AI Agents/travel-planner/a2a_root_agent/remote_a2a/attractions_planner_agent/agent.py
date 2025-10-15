import os
from a2a_root_agent.callback_logging import log_query_to_model, log_model_response
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.a2a.utils.agent_to_a2a import to_a2a
from typing import List
from google.adk.tools.tool_context import ToolContext
from a2a_root_agent.prompts import attractions_planner_prompt


load_dotenv()
model_name = os.getenv("MODEL")


# Tools (add the tool here when instructed)


# def save_attractions_to_state(
#     tool_context: ToolContext,
#     attractions: List[str]
# ) -> dict[str, str]:
#     """Saves the list of attractions to state["attractions"].

#     Args:
#         attractions [str]: a list of strings to add to the list of attractions

#     Returns:
#         None
#     """
#     existing_attractions = tool_context.state.get("attractions", [])
#     tool_context.state["attractions"] = existing_attractions + attractions
#     return {"status": "success"}


# Agents

attractions_planner = Agent(
    name="attractions_planner",
    model=model_name,
    description="Build a list of attractions to visit in a country.",
    instruction=attractions_planner_prompt,
    before_model_callback=log_query_to_model,
    after_model_callback=log_model_response,
    )

a2a_app2 = to_a2a(attractions_planner, port=8002)