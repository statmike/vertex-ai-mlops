"""Approach 4: Context Pre-Filter — LLM reviews briefs, nominates candidates.

The LLM sees brief summaries of all in-scope tables and calls
``nominate_tables`` to select candidates.  An ``after_agent_callback``
fetches detailed cached context for the nominated tables and sends them
to the shared reranker.  This combines LLM reasoning (for candidate
selection) with deterministic reranking (for final scoring).
"""

from google.adk import agents

from config import AGENT_MODEL

from . import prompts
from .tools import TOOLS as PREFILTER_TOOLS
from .tools import rerank_nominations

root_agent = agents.Agent(
    name="agent_context_prefilter",
    model=AGENT_MODEL,
    description=(
        "Discovers relevant BigQuery tables by having the LLM review brief "
        "metadata summaries of all in-scope tables, nominate candidates, then "
        "rerank the nominees using detailed cached context."
    ),
    global_instruction=prompts.global_instructions,
    instruction=prompts.agent_instructions,
    tools=PREFILTER_TOOLS,
    after_agent_callback=rerank_nominations,
)
