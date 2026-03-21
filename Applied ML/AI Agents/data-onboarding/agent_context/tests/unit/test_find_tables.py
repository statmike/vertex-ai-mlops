"""Tests for the find_tables tool."""

import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest


class _FakeToolContext:
    def __init__(self):
        self.state = {}


def _make_row(table_name, columns, related_tables=None):
    # BQ JSON columns are returned as already-parsed Python objects, not strings
    return SimpleNamespace(
        table_name=table_name,
        documentation_md=f"# {table_name}",
        column_details=columns,
        related_tables=related_tables,
        source_file="gs://bucket/file.parquet",
    )


@pytest.fixture
def mock_bq_client():
    with patch(
        "agent_context.tools.function_tool_find_tables.GOOGLE_CLOUD_PROJECT",
        "test-project",
    ), patch("google.cloud.bigquery.Client") as mock_client_cls:
        client = MagicMock()
        mock_client_cls.return_value = client
        yield client


class TestFindTables:
    @pytest.mark.asyncio
    async def test_returns_table_info(self, mock_bq_client):
        from agent_context.tools.function_tool_find_tables import find_tables

        rows = [
            _make_row(
                "ipsf_full",
                [
                    {"name": "provider_ccn", "bq_type": "STRING", "description": "Provider ID"},
                    {"name": "bed_count", "bq_type": "INT64", "description": "Number of beds"},
                ],
                {"contains": ["ipsf_hha"]},
            ),
            _make_row(
                "ipsf_hha",
                [
                    {"name": "provider_ccn", "bq_type": "STRING", "description": "Provider ID"},
                ],
                {"contained_by": "ipsf_full"},
            ),
        ]
        mock_bq_client.query.return_value.result.return_value = rows

        ctx = _FakeToolContext()
        result = await find_tables("data_onboarding_cms_gov_bronze", ctx)

        assert "2 table(s)" in result
        assert "ipsf_full" in result
        assert "contains" in result
        assert len(ctx.state["recommended_tables"]) == 2

    @pytest.mark.asyncio
    async def test_no_tables(self, mock_bq_client):
        from agent_context.tools.function_tool_find_tables import find_tables

        mock_bq_client.query.return_value.result.return_value = []

        ctx = _FakeToolContext()
        result = await find_tables("empty_dataset", ctx)
        assert "No table documentation found" in result

    @pytest.mark.asyncio
    async def test_stores_full_table_id(self, mock_bq_client):
        from agent_context.tools.function_tool_find_tables import find_tables

        rows = [
            _make_row("my_table", [{"name": "id", "bq_type": "INT64", "description": ""}]),
        ]
        mock_bq_client.query.return_value.result.return_value = rows

        ctx = _FakeToolContext()
        await find_tables("my_dataset", ctx)

        table_info = ctx.state["recommended_tables"][0]
        assert table_info["full_table_id"] == "test-project.my_dataset.my_table"
