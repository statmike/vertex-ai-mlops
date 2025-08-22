import os
from callback_logging import log_query_to_model, log_model_response
from dotenv import load_dotenv
from google.adk import Agent
from google.adk.a2a.utils.agent_to_a2a import to_a2a
from toolbox_core import ToolboxSyncClient
from prompts import travel_brainstormer_prompt

load_dotenv()
model_name = os.getenv("MODEL")

toolbox = ToolboxSyncClient("http://localhost:5000")

bq_toolbox = toolbox.load_toolset('my_bq_toolset')

# Agents

travel_brainstormer = Agent(
    name="travel_brainstormer",
    model=model_name,
    description="Help a user decide what country to visit.",
    instruction=travel_brainstormer_prompt,
    before_model_callback=log_query_to_model,
    after_model_callback=log_model_response,tools=[*bq_toolbox]
)

a2a_app1 = to_a2a(travel_brainstormer, port=8001)