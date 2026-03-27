"""Tests for the reranker utility and callback."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from google.genai import types

from agent_context.schemas import (
    ColumnHint,
    JoinSuggestion,
    RankedTable,
    RerankerResponse,
    ShortlistEntry,
    ShortlistResponse,
)
from agent_context.tools.util_rerank import (
    _build_detail_metadata,
    format_reranker_markdown,
)


class _FakeEventActions:
    def __init__(self):
        self.state_delta = {}
        self.transfer_to_agent = None


class _FakeCallbackContext:
    """Minimal stand-in for CallbackContext."""

    def __init__(self, question_text=""):
        self.state = {}
        self._event_actions = _FakeEventActions()
        if question_text:
            self.user_content = types.Content(
                role="user",
                parts=[types.Part(text=question_text)],
            )
        else:
            self.user_content = None


class TestShortlistSchema:
    def test_round_trip(self):
        response = ShortlistResponse(
            question="What exchanges are available?",
            shortlisted=[
                ShortlistEntry(
                    table_id="proj.ds.exchange_ids",
                    confidence=0.9,
                    reason="Contains exchange ID mappings",
                ),
                ShortlistEntry(
                    table_id="proj.ds.market_data",
                    confidence=0.6,
                    reason="Has exchange column",
                ),
            ],
        )

        dumped = response.model_dump()
        restored = ShortlistResponse.model_validate(dumped)

        assert restored.question == "What exchanges are available?"
        assert len(restored.shortlisted) == 2
        assert restored.shortlisted[0].confidence == 0.9

    def test_empty_shortlist(self):
        response = ShortlistResponse(
            question="Irrelevant question",
            shortlisted=[],
        )
        assert len(response.shortlisted) == 0


class TestRerankerResponse:
    def test_schema_round_trip(self):
        response = RerankerResponse(
            question="What is the highest VIX close?",
            top_k=5,
            ranked_tables=[
                RankedTable(
                    table_id="proj.ds.vix_daily",
                    rank=1,
                    confidence=0.95,
                    reasoning="Contains daily VIX closing values",
                    key_columns=[
                        ColumnHint(
                            name="vix_close",
                            data_type="FLOAT64",
                            description="VIX closing value",
                            useful_for_aggregation=True,
                        ),
                    ],
                    sql_hints="Use MAX(vix_close) for highest value",
                    join_suggestions=[
                        JoinSuggestion(
                            target_table="proj.ds.market_dates",
                            join_keys=["trade_date"],
                            relationship="many-to-one",
                        ),
                    ],
                    row_count=5000,
                ),
            ],
            notes="VIX data available from 2004 onwards",
        )

        # Round-trip through JSON
        dumped = response.model_dump()
        restored = RerankerResponse.model_validate(dumped)

        assert restored.question == "What is the highest VIX close?"
        assert len(restored.ranked_tables) == 1
        assert restored.ranked_tables[0].confidence == 0.95
        assert restored.ranked_tables[0].key_columns[0].useful_for_aggregation is True
        assert restored.ranked_tables[0].join_suggestions[0].target_table == "proj.ds.market_dates"

    def test_empty_ranked_tables(self):
        response = RerankerResponse(
            question="Irrelevant question",
            top_k=5,
            ranked_tables=[],
            notes="No relevant tables found",
        )
        assert len(response.ranked_tables) == 0
        assert response.notes == "No relevant tables found"


class TestBuildDetailMetadata:
    def test_builds_from_catalog_data(self):
        catalog_data = {
            "proj.ds.table1": {
                "full_ref": "proj.ds.table1",
                "dataset": "ds",
                "table_name": "table1",
                "columns": [
                    {"name": "col1", "bq_type": "STRING", "description": "A column"},
                    {"name": "col2", "bq_type": "INT64", "description": ""},
                ],
                "relationships": {"foreign_key": "proj.ds.table2.id"},
                "description": "Test table one",
            },
        }

        result = _build_detail_metadata(["proj.ds.table1"], catalog_data)

        assert "table1" in result
        assert "proj.ds.table1" in result
        assert "col1" in result
        assert "STRING" in result
        assert "A column" in result
        assert "foreign_key" in result

    def test_missing_table_skipped(self):
        result = _build_detail_metadata(["proj.ds.missing"], {})
        assert result.strip() == ""


class TestFormatRerankerMarkdown:
    def test_formats_ranked_tables(self):
        result = RerankerResponse(
            question="test",
            top_k=5,
            ranked_tables=[
                RankedTable(
                    table_id="proj.ds.table1",
                    rank=1,
                    confidence=0.9,
                    reasoning="Very relevant",
                    key_columns=[
                        ColumnHint(
                            name="col1",
                            data_type="STRING",
                            useful_for_filtering=True,
                        ),
                    ],
                    sql_hints="Filter on col1",
                ),
            ],
        )

        md = format_reranker_markdown(result)

        assert "proj.ds.table1" in md
        assert "0.90" in md
        assert "Very relevant" in md
        assert "col1" in md
        assert "filter" in md.lower()
        assert "Filter on col1" in md

    def test_empty_results(self):
        result = RerankerResponse(
            question="test",
            top_k=5,
            ranked_tables=[],
            notes="Nothing found",
        )

        md = format_reranker_markdown(result)
        assert "Nothing found" in md

    def test_join_suggestions_formatted(self):
        result = RerankerResponse(
            question="test",
            top_k=5,
            ranked_tables=[
                RankedTable(
                    table_id="proj.ds.table1",
                    rank=1,
                    confidence=0.8,
                    reasoning="Relevant",
                    join_suggestions=[
                        JoinSuggestion(
                            target_table="proj.ds.table2",
                            join_keys=["id"],
                            relationship="one-to-many",
                        ),
                    ],
                ),
            ],
        )

        md = format_reranker_markdown(result)
        assert "proj.ds.table2" in md
        assert "one-to-many" in md


class TestRerankerCallback:
    @pytest.mark.asyncio
    @patch("agent_context.tools.callback_rerank._catalog_data", {
        "proj.ds.t1": {
            "full_ref": "proj.ds.t1",
            "dataset": "ds",
            "table_name": "t1",
            "columns": [],
            "relationships": {},
            "description": "Test table",
        },
    })
    @patch("agent_context.tools.callback_rerank._catalog_summary", "summary text")
    @patch("agent_context.tools.callback_rerank.call_reranker_two_pass")
    async def test_stores_result_in_state(self, mock_reranker):
        from agent_context.tools.callback_rerank import rerank_and_transfer

        mock_reranker.return_value = RerankerResponse(
            question="test question",
            top_k=5,
            ranked_tables=[
                RankedTable(
                    table_id="proj.ds.t1",
                    rank=1,
                    confidence=0.9,
                    reasoning="Good match",
                ),
            ],
        )

        ctx = _FakeCallbackContext("test question")
        content = await rerank_and_transfer(ctx)

        # Should return None (let the LLM handle transfer)
        assert content is None

        # Should store result in state
        assert "reranker_result" in ctx.state
        assert ctx.state["reranker_result"]["question"] == "test question"
        assert len(ctx.state["reranker_result"]["ranked_tables"]) == 1

        # Should store markdown in state
        assert "reranker_markdown" in ctx.state
        assert "proj.ds.t1" in ctx.state["reranker_markdown"]

    @pytest.mark.asyncio
    @patch("agent_context.tools.callback_rerank._catalog_data", {
        "proj.ds.t1": {"full_ref": "proj.ds.t1"},
    })
    @patch("agent_context.tools.callback_rerank._catalog_summary", "summary")
    @patch("agent_context.tools.callback_rerank.call_reranker_two_pass")
    async def test_returns_none_on_error(self, mock_reranker):
        from agent_context.tools.callback_rerank import rerank_and_transfer

        mock_reranker.side_effect = Exception("API error")

        ctx = _FakeCallbackContext("test")
        content = await rerank_and_transfer(ctx)

        # Should return None — falls back to LLM
        assert content is None
        assert "reranker_result" not in ctx.state

    @pytest.mark.asyncio
    @patch("agent_context.tools.callback_rerank._catalog_data", {})
    @patch("agent_context.tools.callback_rerank._catalog_summary", "")
    async def test_returns_none_when_no_catalog(self):
        from agent_context.tools.callback_rerank import rerank_and_transfer

        ctx = _FakeCallbackContext("test")
        content = await rerank_and_transfer(ctx)

        # Should return None — no catalog, fall back to LLM
        assert content is None

    @pytest.mark.asyncio
    async def test_returns_none_when_no_user_content(self):
        from agent_context.tools.callback_rerank import rerank_and_transfer

        ctx = _FakeCallbackContext()  # No question
        content = await rerank_and_transfer(ctx)

        assert content is None
