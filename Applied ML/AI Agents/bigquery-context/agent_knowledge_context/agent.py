"""Approach 3: Knowledge Context API — pre-loaded LLM-ready capsules.

Uses the Dataplex lookupContext API to pre-fetch rich metadata for all
configured tables at initialization. At query time, skips discovery
entirely and goes straight to the reranker with cached capsules.

Note: The lookupContext API is called via REST because it is not yet
available in the google-cloud-dataplex Python SDK (v2.16.0). This will
be updated when SDK support is added.
"""

from google.adk import agents

from config import AGENT_MODEL
from reranker import TOOLS as RERANKER_TOOLS
from . import prompts
from .tools import TOOLS as CONTEXT_TOOLS

root_agent = agents.Agent(
    name="agent_knowledge_context",
    model=AGENT_MODEL,
    description=(
        "Discovers relevant BigQuery tables using pre-loaded Knowledge Context "
        "capsules from the Dataplex lookupContext API, then reranks results. "
        "Fastest at query time — zero discovery API calls after initialization."
    ),
    global_instruction=prompts.global_instructions,
    instruction=prompts.agent_instructions,
    tools=CONTEXT_TOOLS + RERANKER_TOOLS,
)
