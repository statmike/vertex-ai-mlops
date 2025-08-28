import os
from a2a_root_agent.callback_logging import log_query_to_model, log_model_response
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.a2a.utils.agent_to_a2a import to_a2a
from toolbox_core import ToolboxSyncClient
from a2a_root_agent.prompts import travel_history_prompt

load_dotenv()
model_name = os.getenv("MODEL")

toolbox = ToolboxSyncClient("http://localhost:5000")

# Tools

bq_toolbox = toolbox.load_toolset('my_bq_toolset')

# Agents

travel_history = Agent(
    name="travel_history_agent",
    model=model_name,
    description="Show the list of places visited by the user in the past",
    instruction=travel_history_prompt,
    before_model_callback=log_query_to_model,
    after_model_callback=log_model_response,
    tools=[*bq_toolbox]
    )

a2a_app3 = to_a2a(travel_history, port=8003)