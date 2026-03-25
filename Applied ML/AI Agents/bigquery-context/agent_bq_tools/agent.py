"""Approach 1: BQ Metadata Tools — exhaustive enumeration of table metadata.

Uses the ADK BigQueryToolset filtered to discovery-only tools
(list_dataset_ids, list_table_ids, get_dataset_info, get_table_info)
plus the shared reranker tool.
"""

import os

from google.adk import agents
from google.adk.tools import bigquery as bq_tools

from config import AGENT_MODEL, GOOGLE_CLOUD_PROJECT
from reranker import TOOLS as RERANKER_TOOLS
from . import prompts
from .callback_filter_scope import filter_scope

# ADK BigQuery tools — filtered to discovery only (no execute_sql, no forecast)
bq_toolset = bq_tools.BigQueryToolset(
    bigquery_tool_config=bq_tools.config.BigQueryToolConfig(
        write_mode=bq_tools.config.WriteMode.BLOCKED,
        compute_project_id=GOOGLE_CLOUD_PROJECT,
    ),
    tool_filter=[
        "list_dataset_ids",
        "list_table_ids",
        "get_dataset_info",
        "get_table_info",
    ],
)

root_agent = agents.Agent(
    name="agent_bq_tools",
    model=AGENT_MODEL,
    description=(
        "Discovers relevant BigQuery tables by enumerating dataset and table "
        "metadata using the ADK BigQuery built-in tools, then reranks results."
    ),
    global_instruction=prompts.global_instructions,
    instruction=prompts.agent_instructions,
    tools=[bq_toolset] + RERANKER_TOOLS,
    after_tool_callback=filter_scope,
)
