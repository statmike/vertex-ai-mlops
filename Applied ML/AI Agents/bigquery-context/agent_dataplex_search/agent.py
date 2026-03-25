"""Approach 2: Dataplex Search — semantic discovery via natural language.

The before_agent_callback handles the entire workflow deterministically:
semantic search → lookup entries → call shared reranker → return results.
No LLM agent calls are needed — the only model invocation is the reranker's
Gemini structured output (same ``call_reranker`` used by all approaches).
"""

from google.adk import agents

from config import AGENT_MODEL
from reranker import TOOLS as RERANKER_TOOLS
from . import prompts
from .tools import TOOLS as CATALOG_TOOLS, discover_and_rerank


root_agent = agents.Agent(
    name="agent_dataplex_search",
    model=AGENT_MODEL,
    description=(
        "Discovers relevant BigQuery tables using Dataplex Catalog semantic "
        "search, retrieves detailed entry metadata, then reranks results."
    ),
    global_instruction=prompts.global_instructions,
    instruction=prompts.agent_instructions,
    tools=CATALOG_TOOLS + RERANKER_TOOLS,
    before_agent_callback=discover_and_rerank,
)
