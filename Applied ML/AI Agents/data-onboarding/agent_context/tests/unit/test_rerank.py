"""Tests for the reranker utility and tool."""

from unittest.mock import AsyncMock, patch

import pytest

from agent_context.schemas import (
    ColumnHint,
    JoinSuggestion,
    RankedTable,
    RerankerResponse,
)
from agent_context.tools.util_rerank import format_reranker_markdown


class _FakeToolContext:
    def __init__(self):
        self.state = {}
        self.save_artifact = AsyncMock(return_value=1)


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


class TestRerankerTool:
    @pytest.mark.asyncio
    @patch("agent_context.tools.function_tool_rerank.call_reranker")
    async def test_stores_result_in_state(self, mock_reranker):
        from agent_context.tools.function_tool_rerank import rerank_tables

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

        ctx = _FakeToolContext()
        result = await rerank_tables("test question", "metadata here", ctx)

        assert "reranker_result" in ctx.state
        assert ctx.state["reranker_result"]["question"] == "test question"
        assert len(ctx.state["reranker_result"]["ranked_tables"]) == 1
        assert "proj.ds.t1" in result

    @pytest.mark.asyncio
    @patch("agent_context.tools.function_tool_rerank.call_reranker")
    async def test_handles_error_gracefully(self, mock_reranker):
        from agent_context.tools.function_tool_rerank import rerank_tables

        mock_reranker.side_effect = Exception("API error")

        ctx = _FakeToolContext()
        result = await rerank_tables("test", "metadata", ctx)

        assert "error" in result.lower()
        assert "reranker_result" not in ctx.state
