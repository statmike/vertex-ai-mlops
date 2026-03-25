"""Approach 3: Knowledge Context API — pre-loaded LLM-ready capsules.

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

import asyncio

from google.adk import agents
from google.adk.agents.callback_context import CallbackContext
from google.genai import types

from config import AGENT_MODEL, TOP_K
from reranker.util_rerank import call_reranker
from schemas import RerankerResponse
from . import prompts
from .tools import TOOLS as CONTEXT_TOOLS
from reranker import TOOLS as RERANKER_TOOLS
from .tools.function_tool_initialize_context import (
    _PREFETCHED_CONTEXT,
    fetch_knowledge_context,
)


async def _discover_and_rerank(callback_context: CallbackContext):
    """Pre-fetch context + rerank in a single callback — no LLM needed.

    1. Read the module-level cached context (or fetch on demand).
    2. Call the shared ``call_reranker`` (Gemini structured output).
    3. Store the result in state for the compare agent.
    4. Return types.Content so the agent skips the LLM entirely.
    """
    user_content = callback_context.user_content
    if not user_content or not user_content.parts:
        return None  # No question — fall back to LLM + tools

    question = user_content.parts[0].text
    if not question:
        return None

    # Get pre-fetched context (module-level cache) or fetch on demand
    context = _PREFETCHED_CONTEXT
    if context is None:
        context = await asyncio.to_thread(fetch_knowledge_context)

    if not context:
        empty = RerankerResponse(
            question=question,
            top_k=TOP_K,
            ranked_tables=[],
            notes="No knowledge context available.",
        )
        callback_context.state["reranker_result_knowledge_context"] = (
            empty.model_dump_json()
        )
        return types.Content(
            role="model",
            parts=[types.Part(text=(
                "**[Approach 3: Knowledge Context API]**\n\n"
                "No knowledge context available for tables in scope."
            ))],
        )

    top_k = callback_context.state.get("top_k", TOP_K)

    result = await asyncio.to_thread(
        call_reranker,
        question=question,
        candidate_metadata=context,
        discovery_method="knowledge_context",
        top_k=top_k,
    )

    callback_context.state["reranker_result_knowledge_context"] = (
        result.model_dump_json()
    )
    return types.Content(
        role="model",
        parts=[types.Part(text=(
            "**[Approach 3: Knowledge Context API]**\n\n"
            f"{result.model_dump_json(indent=2)}"
        ))],
    )


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
    before_agent_callback=_discover_and_rerank,
)
