import os
from google.adk import agents
from . import prompts
from . import tools

# DEFINE TOOLS - Built-in Tools
from google.adk.tools import bigquery as bq_tools
bq_toolset = bq_tools.BigQueryToolset(
    bigquery_tool_config=bq_tools.config.BigQueryToolConfig(
        write_mode=bq_tools.config.WriteMode.BLOCKED,
        compute_project_id=os.getenv('GOOGLE_CLOUD_PROJECT')
    ),
    tool_filter = [
        'list_dataset_ids',
        'list_table_ids',
        'get_dataset_info',
        'get_table_info',
    ]
)
BUILTIN_BQ_TOOLS = [bq_toolset]

# DEFINE TOOLS - Local Python Function Tools
PYTHON_FUNCTION_TOOLS = tools.PYTHON_FUNCTION_TOOLS

root_agent = agents.Agent(
    name='agent_convo_api',
    model="gemini-2.5-flash",
    description='An agent that can answer questions about BigQuery data using the Conversational Analytics API.',
    global_instruction=prompts.global_instructions,
    instruction=prompts.agent_instructions,
    tools=BUILTIN_BQ_TOOLS + PYTHON_FUNCTION_TOOLS,
    disallow_transfer_to_parent=False,
    disallow_transfer_to_peers=True
)
