"""RAG Engine retrieval tool for the catalog agent (Build — managed retrieval).

[RAG Engine](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/rag-engine/rag-overview)
is Vertex's managed retrieval-augmented-generation service: you import documents
into a **corpus** backed by a managed vector database (the "Vector Search"
storage), and it handles chunking, embedding, indexing, and semantic retrieval.

This is the managed counterpart to the catalog agent's object-table +
``AI.GENERATE`` tool (``search_docs``): both retrieve from the *same* seeded
retail docs, so the project demonstrates both a hand-built BigQuery retrieval
path and the platform's managed one side by side. The agent keeps both tools and
picks whichever fits.

ADK does the retrieval: ``VertexAiRagRetrieval`` (a ``BaseTool``) queries the
corpus with the user's question and returns the top passages. Resolving the
corpus mirrors the Example Store (see agent_analytics/examples.py): Vertex assigns
a numeric resource id, so we resolve by explicit ``RAG_CORPUS_NAME`` if set, else
by listing and matching ``RAG_CORPUS_DISPLAY_NAME``. Fully guarded: when the
corpus can't be resolved the tool is ``None`` and the catalog agent runs with only
its object-table tool.
"""

from __future__ import annotations

import logging

from config import (
    GOOGLE_CLOUD_PROJECT,
    RAG_CORPUS_DISPLAY_NAME,
    RAG_CORPUS_NAME,
    RAG_LOCATION,
    RAG_SIMILARITY_TOP_K,
)

logger = logging.getLogger(__name__)

_CONFIGURED = bool(
    GOOGLE_CLOUD_PROJECT and (RAG_CORPUS_NAME or RAG_CORPUS_DISPLAY_NAME)
)


def _resolve_corpus_resource_name() -> str | None:
    """Return the corpus's full resource name, or None if it can't be resolved.

    Prefers the explicit ``RAG_CORPUS_NAME`` override (no network call); otherwise
    lists the region's corpora and matches on display name. Any failure (SDK
    missing, no credentials, corpus absent) resolves to None so the agent degrades
    gracefully to its object-table tool rather than failing to import.
    """
    if RAG_CORPUS_NAME:
        return RAG_CORPUS_NAME
    try:
        import vertexai
        from vertexai.preview import rag

        vertexai.init(project=GOOGLE_CLOUD_PROJECT, location=RAG_LOCATION)
        for corpus in rag.list_corpora():
            if getattr(corpus, "display_name", None) == RAG_CORPUS_DISPLAY_NAME:
                return corpus.name
    except Exception as e:  # noqa: BLE001 — resolution is best-effort
        logger.info("Could not resolve RAG corpus by display name: %s", e)
        return None
    logger.info(
        "No RAG corpus with display name %r found in %s.",
        RAG_CORPUS_DISPLAY_NAME,
        RAG_LOCATION,
    )
    return None


def _build_rag_tool(corpus_name: str):
    """Build the VertexAiRagRetrieval tool bound to the corpus.

    Imported lazily so this module is import-safe (and testable) without the ADK
    RAG extras installed or credentials present.
    """
    from google.adk.tools.retrieval import VertexAiRagRetrieval

    return VertexAiRagRetrieval(
        name="retrieve_retail_docs",
        description=(
            "Semantically search theLook's policy and help documents (returns, "
            "shipping, sizing, product care, warranties, membership) with managed "
            "RAG, and return the most relevant passages."
        ),
        rag_corpora=[corpus_name],
        similarity_top_k=RAG_SIMILARITY_TOP_K,
    )


# Exported to agent.py. None when the corpus can't be resolved, so the catalog
# agent's tools list omits it and it behaves as a build with only search_docs.
_resolved_name = _resolve_corpus_resource_name() if _CONFIGURED else None
rag_tool = _build_rag_tool(_resolved_name) if _resolved_name else None

if rag_tool is None:
    logger.info(
        "RAG retrieval disabled (set GOOGLE_CLOUD_PROJECT + a provisioned corpus; "
        "run scripts/setup.py, or set RAG_CORPUS_NAME to the resource name)."
    )
