"""Tests for the get_table_columns tool."""

from unittest.mock import MagicMock, patch

import pytest

from agent_catalog.tools.function_tool_get_table_columns import get_table_columns


class TestGetTableColumns:
    @pytest.mark.asyncio
    @patch("agent_catalog.tools.function_tool_get_table_columns.GOOGLE_CLOUD_PROJECT", "")
    async def test_no_project_returns_error(self):
        result = await get_table_columns("test_table")
        assert "GOOGLE_CLOUD_PROJECT not set" in result

    @pytest.mark.asyncio
    @patch("agent_catalog.tools.function_tool_get_table_columns.GOOGLE_CLOUD_PROJECT", "test-proj")
    @patch("agent_context.context_cache.cache._CACHE", {})
    async def test_cache_miss_falls_through(self):
        """When cache has no match and BQ fallback also fails, return not-found."""
        with patch(
            "agent_catalog.tools.function_tool_get_table_columns._query_table_documentation",
        ) as mock_fallback:
            mock_fallback.return_value = "Table 'missing' not found in any onboarded dataset."
            result = await get_table_columns("missing")
            assert "not found" in result

    @pytest.mark.asyncio
    @patch("agent_catalog.tools.function_tool_get_table_columns.GOOGLE_CLOUD_PROJECT", "test-proj")
    async def test_cache_hit_returns_columns(self):
        """When the context cache has the table, return formatted columns."""
        cached_data = {
            "full_id": "test-proj.bronze.my_table",
            "description": "A test table",
            "columns": [
                {"name": "col1", "bq_type": "STRING", "description": "First column"},
                {"name": "col2", "bq_type": "INT64", "description": ""},
            ],
        }
        with patch(
            "agent_context.context_cache.get_table_columns_from_cache",
            return_value=cached_data,
        ):
            result = await get_table_columns("my_table")

        assert "**my_table**" in result
        assert "test-proj.bronze.my_table" in result
        assert "2 columns" in result
        assert "**col1** (STRING): First column" in result
        assert "**col2** (INT64)" in result
