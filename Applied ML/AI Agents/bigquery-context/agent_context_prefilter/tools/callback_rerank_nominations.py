"""Callback: rerank nominated tables with full detailed metadata.

Runs as ``after_agent_callback`` — executes exactly once after the LLM has
finished nominating tables via the ``nominate_tables`` tool. Its distinctive step
is that the candidate set comes from the LLM's nominations rather than a search;
question extraction and reranking are shared helpers in ``discovery_common``. It
returns no Content so the LLM's own response stands as the agent output.
"""

from google.adk.agents.callback_context import CallbackContext

from context_cache import get_detailed_for_tables
from discovery_common import get_question, rerank_and_store, store_empty

METHOD = "context_prefilter"


async def rerank_nominations(callback_context: CallbackContext):
    """After-agent callback: rerank nominated tables with full detail."""
    nominated = callback_context.state.get("nominated_tables", [])
    callback_context.state["nominated_tables_context_prefilter"] = nominated

    question = get_question(callback_context)
    if not question:
        return None

    if not nominated:
        store_empty(
            callback_context, METHOD, question, "No tables were nominated by the pre-filter."
        )
        return None

    detailed = get_detailed_for_tables(nominated)
    if not detailed:
        store_empty(
            callback_context, METHOD, question, "Nominated tables had no cached detailed context."
        )
        return None

    await rerank_and_store(callback_context, question, detailed, METHOD)
    # Don't return Content — let the LLM's response stand as the agent output
