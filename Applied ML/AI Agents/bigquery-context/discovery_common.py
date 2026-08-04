"""Shared helpers for the discovery callbacks.

Five of the six approaches run their whole workflow inside a callback rather than
an LLM tool loop, so they repeat the same mechanical steps: pull the question out
of the callback context, (for the search-based approaches) run the scoped
Knowledge Catalog semantic search, then store + emit a ``RerankerResponse``. These
helpers hold that shared machinery so each callback carries only what makes its
approach distinct — how it sources the candidate metadata.

Knowledge Catalog is the product formerly called Dataplex Universal Catalog
(renamed April 2026). The API namespace remains ``dataplex`` (``dataplex_v1``).
"""

import asyncio
from typing import NamedTuple

from google.adk.agents.callback_context import CallbackContext
from google.cloud import dataplex_v1
from google.genai import types

from config import GOOGLE_CLOUD_PROJECT, TOP_K, get_datasets, is_table_in_scope
from reranker.util_rerank import call_reranker, format_reranker_markdown
from schemas import RerankerResponse

SEARCH_PAGE_SIZE = 20


class SearchHit(NamedTuple):
    """One in-scope Knowledge Catalog search result, in returned order."""

    table_id: str  # fully-qualified project.dataset.table
    entry_name: str  # Dataplex entry resource name (for lookup_entry)
    fqn: str  # entry.fully_qualified_name
    display_name: str
    description: str


def get_question(callback_context: CallbackContext) -> str | None:
    """Return the user's question text, or None if there is none.

    None signals the callback to decline and fall back to the LLM path.
    """
    user_content = callback_context.user_content
    if not user_content or not user_content.parts:
        return None
    return user_content.parts[0].text or None


def search_entries_scoped(question: str) -> tuple[list[SearchHit], dict]:
    """Run scoped Knowledge Catalog semantic search; return in-scope hits + stats.

    Shared by the three search-based approaches (kc_search, semantic_context,
    search_direct) so they issue the *identical* retrieval call — that parity is
    what makes the search_direct vs kc_search comparison a clean measure of the
    reranker's marginal value.

    Bare query syntax: no parentheses around the question, no explicit AND (every
    predicate is implicitly ANDed). Wrapping the free-text question in parentheses
    makes the query parser silently drop the parent: predicate, leaking
    out-of-scope tables (verified live against the catalog). Scope is a single tier
    dataset, so parent: takes exactly one value.

    Returns:
        (hits, stats). ``hits`` preserve search's own relevance order. ``stats``
        records raw vs. in-scope counts; with the corrected query the parent:
        predicate is honored server-side, so ``out_of_scope_dropped`` should be 0 —
        a non-zero value flags a scoping regression. The client-side
        ``is_table_in_scope`` filter stays as harmless defense-in-depth.
    """
    client = dataplex_v1.CatalogServiceClient()
    ds = get_datasets()[0]
    query = f"{question} system=BIGQUERY parent:datasets/{ds}"
    request = dataplex_v1.SearchEntriesRequest(
        name=f"projects/{GOOGLE_CLOUD_PROJECT}/locations/global",
        query=query,
        page_size=SEARCH_PAGE_SIZE,
        semantic_search=True,
    )

    raw_count = 0
    out_of_scope_dropped = 0
    hits: list[SearchHit] = []
    for result in client.search_entries(request=request):
        raw_count += 1
        entry = result.dataplex_entry
        source = entry.entry_source
        fqn = entry.fully_qualified_name or ""
        parts = fqn.rsplit(".", 2)
        if len(parts) < 2:
            continue
        ds_name, tbl_name = parts[-2], parts[-1]
        if not is_table_in_scope(ds_name, tbl_name):
            out_of_scope_dropped += 1
            continue
        hits.append(
            SearchHit(
                table_id=f"{GOOGLE_CLOUD_PROJECT}.{ds_name}.{tbl_name}",
                entry_name=entry.name,
                fqn=fqn,
                display_name=source.display_name if source else "",
                description=source.description if source else "",
            )
        )

    stats = {
        "raw_search_count": raw_count,
        "out_of_scope_dropped": out_of_scope_dropped,
        "page_size": SEARCH_PAGE_SIZE,
    }
    return hits, stats


async def rerank_and_store(
    callback_context: CallbackContext,
    question: str,
    candidate_metadata: str,
    method: str,
) -> RerankerResponse:
    """Call the shared reranker, store its result, and return it.

    Writes the ``reranker_result_{method}`` state key the compare agent reads.
    Approaches differ only in how they build ``candidate_metadata``.
    """
    top_k = callback_context.state.get("top_k", TOP_K)
    result = await asyncio.to_thread(
        call_reranker,
        question=question,
        candidate_metadata=candidate_metadata,
        discovery_method=method,
        top_k=top_k,
    )
    callback_context.state[f"reranker_result_{method}"] = result.model_dump_json()
    return result


def store_empty(
    callback_context: CallbackContext, method: str, question: str, notes: str
) -> RerankerResponse:
    """Store an empty RerankerResponse (no candidates) and return it."""
    result = RerankerResponse(question=question, top_k=TOP_K, ranked_tables=[], notes=notes)
    callback_context.state[f"reranker_result_{method}"] = result.model_dump_json()
    return result


def emit(label: str, result: RerankerResponse) -> types.Content:
    """Render a RerankerResponse as agent Content under ``label``."""
    return types.Content(
        role="model",
        parts=[types.Part(text=format_reranker_markdown(result, label))],
    )


def plain_content(label: str, message: str) -> types.Content:
    """Build a short ``**[label]**`` message Content (used for empty results)."""
    return types.Content(
        role="model",
        parts=[types.Part(text=f"**[{label}]**\n\n{message}")],
    )
