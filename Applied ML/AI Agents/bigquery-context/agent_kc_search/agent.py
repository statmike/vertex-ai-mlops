"""Approach 2: Knowledge Catalog Search — semantic discovery via natural language.

The before_agent_callback handles the entire workflow deterministically:
semantic search → lookup entries → call shared reranker → return results.
No LLM agent calls are needed — the only model invocation is the reranker's
Gemini structured output (same ``call_reranker`` used by all approaches).

Knowledge Catalog is the product formerly called Dataplex Universal Catalog
(renamed April 2026). The API namespace remains ``dataplex`` (``dataplex_v1``).
"""

from google.adk import agents

from config import AGENT_MODEL

from . import prompts
from .tools import discover_and_rerank

root_agent = agents.Agent(
    name="agent_kc_search",
    model=AGENT_MODEL,
    description=(
        "Discovers relevant BigQuery tables using Knowledge Catalog semantic "
        "search, retrieves detailed entry metadata, then reranks results."
    ),
    global_instruction=prompts.global_instructions,
    instruction=prompts.agent_instructions,
    tools=[],
    before_agent_callback=discover_and_rerank,
)
