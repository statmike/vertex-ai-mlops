import os
from a2a_root_agent.callback_logging import log_query_to_model, log_model_response
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.a2a.utils.agent_to_a2a import to_a2a
from toolbox_core import ToolboxSyncClient
from a2a_root_agent.prompts import places_of_interest_prompt


load_dotenv()
model_name = os.getenv("MODEL")

toolbox = ToolboxSyncClient("http://localhost:5000")

# Tools (add the tool here when instructed)

bq_toolbox = toolbox.load_toolset('my_bq_toolset')

# Agents

places_of_interest = Agent(
    name="places_of_interest_agent",
    model=model_name,
    description="Store or Fetch the attraction picked by the user to/from BigQuery table",
    instruction=places_of_interest_prompt,
    before_model_callback=log_query_to_model,
    after_model_callback=log_model_response,
    tools=[*bq_toolbox]
    )

a2a_app4 = to_a2a(places_of_interest, port=8004)