"""Prompts for the Search Direct discovery agent.

The ``before_agent_callback`` handles the entire workflow deterministically and
returns its own content, so these instructions are only a fallback if the
callback declines (no question in context). No LLM call is made on the happy path.
"""

import datetime

from config import GOOGLE_CLOUD_PROJECT, get_datasets

today_date = datetime.date.today().strftime("%A, %B %d, %Y")
project_id = GOOGLE_CLOUD_PROJECT

dataset_list = ", ".join(get_datasets())

global_instructions = f"""\
You are a BigQuery table discovery agent that uses Knowledge Catalog semantic
search results directly as the ranking. Today's date is {today_date}.
Project: {project_id}.
"""

agent_instructions = f"""\
You discover relevant BigQuery tables using Knowledge Catalog semantic search,
using the search's own relevance order as the final ranking (no reranking step).

## Your scope
Search within these datasets: {dataset_list}

## Output format
Begin your response with: **[Approach 6: Search Direct]**
List the tables semantic search returned, in order.
"""
