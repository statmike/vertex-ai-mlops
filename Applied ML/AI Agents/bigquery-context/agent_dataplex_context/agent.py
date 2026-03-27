"""Approach 3: Dataplex Context — pre-loaded LLM-ready capsules.

Uses the Dataplex lookupContext API to pre-fetch rich metadata for all
configured tables at module load time.  When ``adk web`` or ``adk run``
starts, the context is already cached before the first user question.

The before_agent_callback handles the entire workflow deterministically:
read cached context → call shared reranker → return results.  No LLM
agent calls are needed — the only model invocation is the reranker's
Gemini structured output (same ``call_reranker`` used by all approaches).

Note: The lookupContext API is called via REST because it is not yet
available in the google-cloud-dataplex Python SDK (v2.16.0). This will
be updated when SDK support is added.
"""

from google.adk import agents

from config import AGENT_MODEL
from reranker import TOOLS as RERANKER_TOOLS

from . import prompts
from .tools import TOOLS as CONTEXT_TOOLS
from .tools import discover_and_rerank

root_agent = agents.Agent(
    name="agent_dataplex_context",
    model=AGENT_MODEL,
    description=(
        "Discovers relevant BigQuery tables using pre-loaded Knowledge Context "
        "capsules from the Dataplex lookupContext API, then reranks results. "
        "Fastest at query time — zero discovery API calls after initialization."
    ),
    global_instruction=prompts.global_instructions,
    instruction=prompts.agent_instructions,
    tools=CONTEXT_TOOLS + RERANKER_TOOLS,
    before_agent_callback=discover_and_rerank,
)
