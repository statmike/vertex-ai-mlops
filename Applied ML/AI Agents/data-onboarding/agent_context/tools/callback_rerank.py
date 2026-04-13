"""Deterministic before_agent_callback: run reranker before the LLM.

Runs the two-pass reranker in ``before_agent_callback`` so it executes
deterministically on every invocation — the LLM never decides whether to
call the reranker.  After storing the result in state, the callback returns
``None`` so the LLM gets a turn to handle the transfer to ``agent_convo``.
"""

import asyncio
import logging

from google.adk.agents.callback_context import CallbackContext

from agent_context.catalog import _catalog_data, _catalog_summary

from .util_rerank import call_reranker_two_pass, format_reranker_markdown

logger = logging.getLogger(__name__)


async def rerank_and_transfer(callback_context: CallbackContext):
    """Run two-pass reranker and store results in state.

    1. Extract the user question from callback_context.user_content.
    2. Check if prior reranker results can be reused (follow-up detection).
    3. If new topic, run the two-pass reranker (shortlist → detail).
    4. Store the structured result AND formatted markdown in session state.
    5. Return None — the LLM runs next and transfers to agent_convo.

    The LLM's only job is to transfer to agent_convo.  The reranker result
    is already in state for agent_convo to auto-pick tables.
    """
    user_content = callback_context.user_content
    if not user_content or not user_content.parts:
        return None
    question = user_content.parts[0].text
    if not question:
        return None

    # Guard: reuse prior results if this looks like a follow-up
    prior = callback_context.state.get("reranker_result")
    if prior:
        prior_question = prior.get("question", "")
        if _is_likely_followup(question, prior_question):
            logger.info(
                "Reranker callback: reusing prior result (follow-up). "
                "Prior: %.60s → Current: %.60s",
                prior_question, question,
            )
            return None
        # New topic — clear stale results so we re-run
        logger.info(
            "Reranker callback: new topic detected, re-running. "
            "Prior: %.60s → Current: %.60s",
            prior_question, question,
        )

    if not _catalog_data:
        return None

    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            call_reranker_two_pass,
            question,
            _catalog_summary,
            _catalog_data,
        )

        # Store structured result in state for agent_convo
        callback_context.state["reranker_result"] = result.model_dump()

        # Store formatted markdown so the LLM can see what was found
        callback_context.state["reranker_markdown"] = format_reranker_markdown(result)

        logger.info(
            "Reranker callback: found %d table(s) for: %s",
            len(result.ranked_tables),
            question[:80],
        )

    except Exception as e:
        logger.warning("Reranker callback failed: %s", e)

    # Always return None — let the LLM handle the transfer
    return None


def _is_likely_followup(current: str, previous: str) -> bool:
    """Heuristic check: is the current question a follow-up to the previous?

    Uses lightweight signals to avoid an LLM call. Errs on the side of
    returning True (reusing results) since the Conversational Analytics API
    handles follow-ups gracefully even with the same table set.
    """
    if not previous:
        return False

    c = current.strip().lower()

    # Short questions are almost always follow-ups
    if len(c.split()) <= 4:
        return True

    # Explicit follow-up signals
    followup_starts = [
        "now ", "also ", "and ", "what about ", "how about ",
        "can you ", "show me ", "filter ", "sort ", "group ",
        "break ", "chart ", "compare ", "exclude ", "include ",
        "instead ", "same ", "that ", "those ", "this ", "these ",
    ]
    if any(c.startswith(s) for s in followup_starts):
        return True

    # Pronoun references to prior data
    pronoun_signals = [
        " that ", " those ", " this ", " these ", " it ",
        " them ", " the same ", " again ",
    ]
    if any(s in f" {c} " for s in pronoun_signals):
        return True

    # If both questions share key nouns, likely same topic
    prev_words = set(previous.strip().lower().split())
    curr_words = set(c.split())
    # Remove common stop words
    stops = {
        "the", "a", "an", "is", "are", "was", "were", "what", "how",
        "show", "me", "can", "you", "do", "does", "in", "for", "of",
        "to", "by", "and", "or", "with", "from", "on", "at", "my",
        "i", "we", "they", "it", "be", "have", "has", "had", "will",
        "would", "could", "should", "may", "might", "about", "up",
    }
    prev_content = prev_words - stops
    curr_content = curr_words - stops
    if prev_content and curr_content:
        overlap = prev_content & curr_content
        # If more than 30% of content words overlap, likely same topic
        if len(overlap) / min(len(prev_content), len(curr_content)) > 0.3:
            return True

    return False
