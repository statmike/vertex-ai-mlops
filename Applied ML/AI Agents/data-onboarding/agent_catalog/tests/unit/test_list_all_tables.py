"""Tests for the list_all_tables tool."""

import json
from unittest.mock import patch

import pytest

from agent_catalog.tools.function_tool_list_all_tables import list_all_tables


class TestListAllTables:
    @pytest.mark.asyncio
    @patch("agent_catalog.tools.function_tool_list_all_tables.GOOGLE_CLOUD_PROJECT", "")
    async def test_no_project_returns_error(self):
        result = await list_all_tables()
        assert "GOOGLE_CLOUD_PROJECT not set" in result

    @pytest.mark.asyncio
    @patch("agent_catalog.tools.function_tool_list_all_tables.GOOGLE_CLOUD_PROJECT", "test-proj")
    async def test_returns_cached_tables(self):
        from agent_context.context_cache.cache import TableContext, _CACHE

        original = _CACHE.copy()
        try:
            _CACHE.clear()
            _CACHE["test-proj.bronze.orders"] = TableContext(
                full_id="test-proj.bronze.orders",
                brief="{}",
                detailed="{}",
                columns=[
                    {"name": "order_id", "bq_type": "INT64", "description": "PK"},
                    {"name": "amount", "bq_type": "FLOAT64", "description": "Order amount"},
                ],
                description="Customer orders",
            )
            _CACHE["test-proj.bronze.exchange_ids"] = TableContext(
                full_id="test-proj.bronze.exchange_ids",
                brief="{}",
                detailed="{}",
                columns=[
                    {"name": "id", "bq_type": "INT64", "description": "Exchange ID"},
                    {"name": "name", "bq_type": "STRING", "description": "Exchange name"},
                ],
                description="Exchange identifier lookup table",
            )

            result = await list_all_tables()

            assert "2 table(s) onboarded" in result
            assert "orders" in result
            assert "exchange_ids" in result
            assert "Customer orders" in result
            assert "order_id" in result
            assert "2 columns" in result
        finally:
            _CACHE.clear()
            _CACHE.update(original)

    @pytest.mark.asyncio
    @patch("agent_catalog.tools.function_tool_list_all_tables.GOOGLE_CLOUD_PROJECT", "test-proj")
    async def test_empty_cache_falls_back(self):
        from agent_context.context_cache.cache import _CACHE

        original = _CACHE.copy()
        try:
            _CACHE.clear()

            with patch(
                "agent_catalog.tools.function_tool_list_all_tables._fallback_from_bq",
                return_value="No onboarded datasets found.",
            ):
                result = await list_all_tables()
                assert "No onboarded datasets" in result
        finally:
            _CACHE.clear()
            _CACHE.update(original)
