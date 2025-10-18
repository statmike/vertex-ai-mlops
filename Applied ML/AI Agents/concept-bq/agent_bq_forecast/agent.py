import os
from google.adk import agents
from . import prompts
from . import callbacks
from . import tools

# DEFINE TOOLS - Built-in Tools
from google.adk.tools import bigquery as bq_tools
bq_toolset = bq_tools.BigQueryToolset(
    #credentials_config = credentials_config,
    bigquery_tool_config=bq_tools.config.BigQueryToolConfig(
        write_mode=bq_tools.config.WriteMode.BLOCKED,
        compute_project_id=os.getenv('GOOGLE_CLOUD_PROJECT')
    ),
    tool_filter = [
        'list_dataset_ids',
        'list_table_ids',
        'get_dataset_info',
        'get_table_info',
        'forecast',
        'execute_sql'
    ]
)
BUILTIN_BQ_TOOLS = [bq_toolset]


root_agent = agents.Agent(
    name = 'agent_bq_forecast',
    model = "gemini-2.5-flash",
    description = 'An agent that can use bigquery with tools to answer questions with time series data including forecasting.',
    global_instruction = prompts.global_instructions,
    instruction = prompts.builtin_query_agent_instructions,
    tools = BUILTIN_BQ_TOOLS + [tools.function_tool_forecast_plot],
    before_tool_callback = callbacks.before_forecast_callback,
    after_tool_callback = callbacks.after_forecast_callback,
    disallow_transfer_to_parent=False,  # Allows transfers to parent (default)
    disallow_transfer_to_peers=True     # Prevents transfers to peers
)