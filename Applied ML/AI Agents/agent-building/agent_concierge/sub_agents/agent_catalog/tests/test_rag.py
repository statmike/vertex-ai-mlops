"""Tests for the catalog agent's RAG Engine retrieval wiring.

The corpus is a managed cloud resource, so these tests never touch it: the
vertexai RAG SDK and the ADK tool import are patched. We verify the pure parts —
the resource-name override wins with no network call, display-name matching finds
the corpus, unresolved config yields ``None``, and the tool is built with the
resolved corpus name.
"""

from unittest.mock import MagicMock, patch

from agent_concierge.sub_agents.agent_catalog import rag


def test_resolve_prefers_explicit_resource_name():
    """RAG_CORPUS_NAME is returned verbatim with no listing/network call."""
    name = "projects/p/locations/us-central1/ragCorpora/123"
    with (
        patch.object(rag, "RAG_CORPUS_NAME", name),
        patch.dict("sys.modules", {"vertexai": MagicMock()}),
    ):
        assert rag._resolve_corpus_resource_name() == name


def test_resolve_matches_by_display_name():
    match = MagicMock()
    match.display_name = "agent-building-retail-docs"
    match.name = "projects/p/locations/us-central1/ragCorpora/999"
    other = MagicMock()
    other.display_name = "something-else"
    other.name = "projects/p/locations/us-central1/ragCorpora/000"

    fake_vertexai = MagicMock()
    fake_rag = MagicMock()
    fake_rag.list_corpora.return_value = [other, match]
    preview_mod = MagicMock()
    preview_mod.rag = fake_rag
    fake_vertexai.preview = preview_mod

    with (
        patch.object(rag, "RAG_CORPUS_NAME", ""),
        patch.object(rag, "RAG_CORPUS_DISPLAY_NAME", "agent-building-retail-docs"),
        patch.dict(
            "sys.modules",
            {"vertexai": fake_vertexai, "vertexai.preview": preview_mod},
        ),
    ):
        assert rag._resolve_corpus_resource_name() == match.name


def test_resolve_returns_none_when_no_display_name_matches():
    other = MagicMock()
    other.display_name = "nope"

    fake_vertexai = MagicMock()
    fake_rag = MagicMock()
    fake_rag.list_corpora.return_value = [other]
    preview_mod = MagicMock()
    preview_mod.rag = fake_rag
    fake_vertexai.preview = preview_mod

    with (
        patch.object(rag, "RAG_CORPUS_NAME", ""),
        patch.object(rag, "RAG_CORPUS_DISPLAY_NAME", "agent-building-retail-docs"),
        patch.dict(
            "sys.modules",
            {"vertexai": fake_vertexai, "vertexai.preview": preview_mod},
        ),
    ):
        assert rag._resolve_corpus_resource_name() is None


def test_resolve_returns_none_on_error():
    """A failure resolving (no creds, SDK missing) degrades to None, not a raise."""
    fake_vertexai = MagicMock()
    fake_vertexai.init.side_effect = RuntimeError("no credentials")
    with (
        patch.object(rag, "RAG_CORPUS_NAME", ""),
        patch.object(rag, "RAG_CORPUS_DISPLAY_NAME", "agent-building-retail-docs"),
        patch.dict("sys.modules", {"vertexai": fake_vertexai}),
    ):
        assert rag._resolve_corpus_resource_name() is None


def test_build_rag_tool_binds_corpus():
    fake_tool = MagicMock(name="VertexAiRagRetrieval")
    fake_tool_cls = MagicMock(return_value=fake_tool)
    retrieval_mod = MagicMock()
    retrieval_mod.VertexAiRagRetrieval = fake_tool_cls

    corpus = "projects/p/locations/us-central1/ragCorpora/123"
    with patch.dict(
        "sys.modules", {"google.adk.tools.retrieval": retrieval_mod}
    ):
        tool = rag._build_rag_tool(corpus)

    assert tool is fake_tool
    _, kwargs = fake_tool_cls.call_args
    assert kwargs["rag_corpora"] == [corpus]
    assert kwargs["similarity_top_k"] == rag.RAG_SIMILARITY_TOP_K
    assert kwargs["name"] == "retrieve_retail_docs"
