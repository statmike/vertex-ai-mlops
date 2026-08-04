"""Prompts for the Knowledge Catalog Context discovery agent.

The ``before_agent_callback`` runs the entire workflow deterministically —
pre-loaded Knowledge Context capsules plus the shared reranker — and returns its
own content, so these instructions are only a fallback if the callback declines
(no question in context). No LLM tool loop runs on the happy path.
"""

import datetime

from config import GOOGLE_CLOUD_PROJECT

today_date = datetime.date.today().strftime("%A, %B %d, %Y")
project_id = GOOGLE_CLOUD_PROJECT

global_instructions = f"""\
You are a BigQuery table discovery agent that uses pre-loaded Knowledge Context
capsules to find relevant tables. Today's date is {today_date}. Project: {project_id}.
"""

agent_instructions = """\
You discover relevant BigQuery tables using pre-loaded Knowledge Context capsules
from the Knowledge Catalog lookupContext API, then the shared reranker.

This approach runs entirely in a callback — no LLM reasoning is needed.
If you see this prompt, the callback did not return Content; respond with
the results from state if available.
"""
