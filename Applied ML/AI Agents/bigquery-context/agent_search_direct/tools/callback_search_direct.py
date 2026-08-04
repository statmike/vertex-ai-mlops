"""Callback: Knowledge Catalog semantic search as discovery AND rank.

Approach 6 — Search Direct. Runs the *same* scoped ``search_entries`` call as
Approach 2 (``kc_search``) via the shared ``search_entries_scoped`` helper, but
treats semantic search's own returned order as the final answer: it builds the
shared ``RerankerResponse`` directly from that order and does **not** call the LLM
reranker.

The point of the pairing is a clean, controlled comparison: identical retrieval,
with vs. without the LLM rerank stage. Any difference in recall / extra tables /
rank quality between Approach 6 and Approach 2 is the reranker's marginal effect.

Knowledge Catalog is the product formerly called Dataplex Universal Catalog
(renamed April 2026). The API namespace remains ``dataplex`` (``dataplex_v1``).
"""

import asyncio

from google.adk.agents.callback_context import CallbackContext

from config import TOP_K
from discovery_common import emit, get_question, search_entries_scoped
from schemas import RankedTable, RerankerResponse

LABEL = "Approach 6: Search Direct"


def _response_from_search_order(question: str, ordered_ids: list[str]) -> RerankerResponse:
    """Build a RerankerResponse straight from semantic search's own ranking.

    No LLM is involved: rank = search position, confidence is a smooth descending
    proxy for that position (search returns no score of its own). The full
    returned set is kept as-is — search already pruned it, so there is no top_k
    truncation.
    """
    n = len(ordered_ids)
    ranked = []
    for i, table_id in enumerate(ordered_ids):
        # Descending proxy confidence in (0.5, 1.0]; preserves search order
        # without implying a real score the API never returned.
        confidence = 1.0 - (0.5 * i / n) if n else 0.0
        ranked.append(
            RankedTable(
                table_id=table_id,
                rank=i + 1,
                confidence=round(confidence, 3),
                reasoning="Ranked by Knowledge Catalog semantic search relevance order (no LLM rerank).",
                discovery_method="search_direct",
            )
        )
    return RerankerResponse(
        question=question,
        top_k=TOP_K,
        ranked_tables=ranked,
        notes=(
            "Search-direct: semantic search's own returned order is the final "
            "ranking; no reranker was applied."
        ),
    )


async def search_direct(callback_context: CallbackContext):
    """Search + rank-by-search-order in a single callback — no LLM at all."""
    question = get_question(callback_context)
    if not question:
        return None  # No question — fall back to LLM

    hits, search_stats = await asyncio.to_thread(search_entries_scoped, question)
    ordered_ids = [hit.table_id for hit in hits]

    callback_context.state["nominated_tables_search_direct"] = ordered_ids
    callback_context.state["search_stats_search_direct"] = search_stats

    result = _response_from_search_order(question, ordered_ids)
    callback_context.state["reranker_result_search_direct"] = result.model_dump_json()
    return emit(LABEL, result)
