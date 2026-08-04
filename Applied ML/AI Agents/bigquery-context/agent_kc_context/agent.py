"""Approach 3: Knowledge Catalog Context — pre-loaded LLM-ready capsules.

Uses the Knowledge Catalog lookupContext API to pre-fetch rich metadata for
all configured tables at module load time.  When ``adk web`` or ``adk run``
starts, the context is already cached before the first user question.

The before_agent_callback handles the entire workflow deterministically:
read cached context → call shared reranker → return results.  No LLM
agent calls are needed — the only model invocation is the reranker's
Gemini structured output (same ``call_reranker`` used by all approaches).

Knowledge Catalog is the product formerly called Dataplex Universal Catalog
(renamed April 2026). The API namespace remains ``dataplex`` (``dataplex_v1``).
The lookupContext capsule bundles schema, data-profile statistics, business
glossary terms, frequent-join hints, and sample queries when those catalog
enrichments are present.
"""

from google.adk import agents

from config import AGENT_MODEL

from . import prompts
from .tools import discover_and_rerank

root_agent = agents.Agent(
    name="agent_kc_context",
    model=AGENT_MODEL,
    description=(
        "Discovers relevant BigQuery tables using pre-loaded Knowledge Context "
        "capsules from the Knowledge Catalog lookupContext API, then reranks "
        "results. Fastest at query time — zero discovery API calls after "
        "initialization."
    ),
    global_instruction=prompts.global_instructions,
    instruction=prompts.agent_instructions,
    tools=[],
    before_agent_callback=discover_and_rerank,
)
