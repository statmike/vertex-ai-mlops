"""Tests for the discover_datasets tool."""

import json
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest


class _FakeToolContext:
    def __init__(self):
        self.state = {}


def _make_row(dataset_name, source_uri, domain, tables, relationships=None):
    # BQ JSON columns are returned as already-parsed Python objects, not strings
    return SimpleNamespace(
        dataset_name=dataset_name,
        source_uri=source_uri,
        domain=domain,
        tables_created=tables,
        table_relationships=relationships,
        description_md="",
        onboarded_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )


@pytest.fixture
def mock_bq_client():
    with patch(
        "agent_context.tools.function_tool_discover_datasets.GOOGLE_CLOUD_PROJECT",
        "test-project",
    ), patch("google.cloud.bigquery.Client") as mock_client_cls:
        client = MagicMock()
        mock_client_cls.return_value = client
        yield client


class TestDiscoverDatasets:
    @pytest.mark.asyncio
    async def test_returns_datasets(self, mock_bq_client):
        from agent_context.tools.function_tool_discover_datasets import discover_datasets

        rows = [
            _make_row(
                "data_onboarding_cms_gov_bronze",
                "https://data.cms.gov/provider-data",
                "cms_gov",
                ["ipsf_full", "ipsf_hha"],
                {"ipsf_full": {"contains": ["ipsf_hha"]}},
            ),
        ]
        mock_bq_client.query.return_value.result.return_value = rows

        ctx = _FakeToolContext()
        result = await discover_datasets(ctx)

        assert "1 onboarded dataset(s)" in result
        assert "cms_gov" in result
        assert "ipsf_full" in result
        assert len(ctx.state["discovered_datasets"]) == 1

    @pytest.mark.asyncio
    async def test_no_datasets(self, mock_bq_client):
        from agent_context.tools.function_tool_discover_datasets import discover_datasets

        mock_bq_client.query.return_value.result.return_value = []

        ctx = _FakeToolContext()
        result = await discover_datasets(ctx)
        assert "No onboarded datasets" in result

    @pytest.mark.asyncio
    async def test_no_project(self):
        with patch(
            "agent_context.tools.function_tool_discover_datasets.GOOGLE_CLOUD_PROJECT",
            "",
        ):
            from agent_context.tools.function_tool_discover_datasets import discover_datasets

            ctx = _FakeToolContext()
            result = await discover_datasets(ctx)
            assert "GOOGLE_CLOUD_PROJECT not set" in result
