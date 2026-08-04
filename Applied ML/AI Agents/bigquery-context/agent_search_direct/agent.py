"""Approach 6: Search Direct — semantic search as discovery AND rank.

The before_agent_callback handles the entire workflow deterministically:
semantic search → build the ranked result from search's own order → return.
No LLM is invoked at all (not even a reranker) — semantic search's returned
order is the final ranking. This is the controlled counterpart to Approach 2
(kc_search), which runs the identical search then adds an LLM rerank; the
difference between the two isolates the reranker's marginal value.

Knowledge Catalog is the product formerly called Dataplex Universal Catalog
(renamed April 2026). The API namespace remains ``dataplex`` (``dataplex_v1``).
"""

from google.adk import agents

from config import AGENT_MODEL

from . import prompts
from .tools import search_direct

root_agent = agents.Agent(
    name="agent_search_direct",
    model=AGENT_MODEL,
    description=(
        "Discovers relevant BigQuery tables using Knowledge Catalog semantic "
        "search and uses the search's own relevance order as the final ranking, "
        "with no reranking step."
    ),
    global_instruction=prompts.global_instructions,
    instruction=prompts.agent_instructions,
    before_agent_callback=search_direct,
)
