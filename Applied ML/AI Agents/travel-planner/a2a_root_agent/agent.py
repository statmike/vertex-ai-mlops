import os
from dotenv import load_dotenv
from google.adk import Agent
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from a2a.utils.constants import AGENT_CARD_WELL_KNOWN_PATH
from google.genai import types
from typing import List
from google.adk.tools.tool_context import ToolContext
from .prompts import root_agent_prompt

load_dotenv()
model_name = os.getenv("MODEL")

# Tools

def save_attractions_to_state(
    tool_context: ToolContext,
    attractions: List[str]
) -> dict[str, str]:
    """Saves the list of attractions to state["attractions"].

    Args:
        attractions [str]: a list of strings to add to the list of attractions

    Returns:
        None
    """
    existing_attractions = tool_context.state.get("attractions", [])
    tool_context.state["attractions"] = existing_attractions + attractions
    return {"status": "success"}


## Define Remote Agents

attractions_planner_remote_agent = RemoteA2aAgent(
    name="attractions_planner_agent",
    description="Agent that handles questions related to attractions planning.",
    agent_card=(
        f"http://localhost:8002/{AGENT_CARD_WELL_KNOWN_PATH}"
    ),
)

travel_brainstormer_remote_agent = RemoteA2aAgent(
    name="travel_brainstormer_agent",
    description="Agent that handles questions related to travel brainstorming.",
    agent_card=(
        f"http://localhost:8001/{AGENT_CARD_WELL_KNOWN_PATH}"
    ),
)

travel_history_remote_agent = RemoteA2aAgent(
    name="travel_history_agent",
    description="Agent that handles questions related to travel travel history.",
    agent_card=(
        f"http://localhost:8003/{AGENT_CARD_WELL_KNOWN_PATH}"
    ),
)

places_of_interest_remote_agent = RemoteA2aAgent(
    name="places_of_interest_agent",
    description="Agent gathers the attraction picked by the user and stores it in BigQuery table.",
    agent_card=(
        f"http://localhost:8004/{AGENT_CARD_WELL_KNOWN_PATH}"
    ),
)

## Root Agent

root_agent = Agent(
    name="steering",
    model=model_name,
    description="Start a user on a travel adventure.",
    instruction=root_agent_prompt,
    generate_content_config=types.GenerateContentConfig(
        temperature=0,
    ),
    sub_agents=[travel_brainstormer_remote_agent, attractions_planner_remote_agent, travel_history_remote_agent,places_of_interest_remote_agent]
)