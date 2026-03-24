"""Approach 2: Dataplex Catalog Search — semantic discovery via natural language.

Uses Dataplex search_entries with semantic_search=True to find relevant
tables by natural language matching, then lookup_entry for full metadata,
plus the shared reranker tool.
"""

from google.adk import agents

from config import AGENT_MODEL
from reranker import TOOLS as RERANKER_TOOLS
from . import prompts
from .tools import TOOLS as CATALOG_TOOLS

root_agent = agents.Agent(
    name="agent_catalog_search",
    model=AGENT_MODEL,
    description=(
        "Discovers relevant BigQuery tables using Dataplex Catalog semantic "
        "search, retrieves detailed entry metadata, then reranks results."
    ),
    global_instruction=prompts.global_instructions,
    instruction=prompts.agent_instructions,
    tools=CATALOG_TOOLS + RERANKER_TOOLS,
)
