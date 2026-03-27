"""Approach 5: Semantic Context — semantic search + cached Knowledge Context.

Combines Dataplex semantic search (like Approach 2) to narrow candidates with
detailed cached Knowledge Context capsules (like Approach 3) for those matches.
Fully deterministic — the ``before_agent_callback`` handles the entire workflow:
semantic search → cache lookup → call shared reranker → return results.

Key difference from Approach 2: replaces per-table ``lookup_entry`` API calls
with a single cache lookup (zero additional API calls after the initial search).
"""

from google.adk import agents

from config import AGENT_MODEL

from . import prompts
from .tools import discover_and_rerank

root_agent = agents.Agent(
    name="agent_semantic_context",
    model=AGENT_MODEL,
    description=(
        "Discovers relevant BigQuery tables using Dataplex semantic search "
        "to narrow candidates, then enriches matches with cached Knowledge "
        "Context capsules and reranks results."
    ),
    global_instruction=prompts.global_instructions,
    instruction=prompts.agent_instructions,
    tools=[],
    before_agent_callback=discover_and_rerank,
)
