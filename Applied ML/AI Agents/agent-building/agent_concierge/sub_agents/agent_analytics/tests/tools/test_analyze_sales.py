"""Tests for function_tool_analyze_sales (agent_analytics).

The Conversational Analytics core is patched, so we verify the thin wrapper's
job: it builds the in-scope theLook table references from config and forwards
them (with the question and a system instruction) to the core.
"""

from unittest.mock import AsyncMock, patch

import pytest

from agent_concierge.sub_agents.agent_analytics.tools import function_tool_analyze_sales
from agent_concierge.sub_agents.agent_analytics.tools.function_tool_analyze_sales import (
    analyze_sales,
)
from config import THELOOK_DATASET, THELOOK_PROJECT, THELOOK_TABLES


class TestAnalyzeSales:
    @pytest.mark.asyncio
    async def test_forwards_question_and_scoped_tables(self, mock_tool_context):
        mock_core = AsyncMock(return_value="Revenue was $1.2M.")
        with patch.object(function_tool_analyze_sales, "call_conversational_api", mock_core):
            result = await analyze_sales("What was total revenue?", mock_tool_context)

        assert result == "Revenue was $1.2M."
        kwargs = mock_core.await_args.kwargs
        assert kwargs["question"] == "What was total revenue?"
        assert kwargs["tool_context"] is mock_tool_context
        assert kwargs["system_instruction"]  # a non-empty persona was passed

        tables = kwargs["bigquery_tables"]
        assert len(tables) == len(THELOOK_TABLES)
        assert all(t["project_id"] == THELOOK_PROJECT for t in tables)
        assert all(t["dataset_id"] == THELOOK_DATASET for t in tables)
        assert {t["table_id"] for t in tables} == set(THELOOK_TABLES)
