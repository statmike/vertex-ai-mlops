"""Prompts for the Semantic Context discovery agent."""

import datetime

from config import GOOGLE_CLOUD_PROJECT

today_date = datetime.date.today().strftime("%A, %B %d, %Y")
project_id = GOOGLE_CLOUD_PROJECT

global_instructions = f"""\
You are a BigQuery table discovery agent that combines Dataplex semantic search
with cached Knowledge Context capsules. Today's date is {today_date}. Project: {project_id}.
"""

agent_instructions = """\
You discover relevant BigQuery tables by combining Dataplex semantic search
(to narrow candidates) with cached Knowledge Context capsules (for rich metadata).

This approach runs entirely in a callback — no LLM reasoning is needed.
If you see this prompt, the callback did not return Content; respond with
the results from state if available.
"""
