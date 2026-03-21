"""Tests for the initialize_source orchestrator tool."""

from unittest.mock import MagicMock, patch

import pytest

from agent_orchestrator.tools.function_tool_initialize_source import initialize_source


@pytest.fixture
def mock_tool_context():
    ctx = MagicMock()
    ctx.state = {}
    return ctx


class TestInitializeSource:
    @pytest.mark.asyncio
    async def test_url_source(self, mock_tool_context):
        result = await initialize_source("https://example.com/data", mock_tool_context)

        assert mock_tool_context.state["source_type"] == "url"
        assert mock_tool_context.state["source_uri"] == "https://example.com/data"
        assert mock_tool_context.state["source_id"]  # non-empty
        assert mock_tool_context.state["gcs_staging_path"]  # non-empty
        assert "Source initialized" in result

    @pytest.mark.asyncio
    async def test_gcs_source(self, mock_tool_context):
        result = await initialize_source("gs://bucket/path", mock_tool_context)

        assert mock_tool_context.state["source_type"] == "gcs"
        assert mock_tool_context.state["source_uri"] == "gs://bucket/path"
        assert "Source initialized" in result

    @pytest.mark.asyncio
    async def test_invalid_source(self, mock_tool_context):
        result = await initialize_source("ftp://nope", mock_tool_context)

        assert "Unrecognized source format" in result
        assert "source_id" not in mock_tool_context.state

    @pytest.mark.asyncio
    async def test_strips_whitespace(self, mock_tool_context):
        await initialize_source("  https://example.com  ", mock_tool_context)

        assert mock_tool_context.state["source_uri"] == "https://example.com"

    @pytest.mark.asyncio
    async def test_deterministic_source_id(self, mock_tool_context):
        await initialize_source("https://example.com/data", mock_tool_context)
        id1 = mock_tool_context.state["source_id"]

        mock_tool_context.state = {}
        await initialize_source("https://example.com/data", mock_tool_context)
        id2 = mock_tool_context.state["source_id"]

        assert id1 == id2

    @pytest.mark.asyncio
    async def test_staging_path_includes_source_id(self, mock_tool_context):
        await initialize_source("https://example.com/data", mock_tool_context)

        source_id = mock_tool_context.state["source_id"]
        staging_path = mock_tool_context.state["gcs_staging_path"]
        assert source_id in staging_path

    @pytest.mark.asyncio
    async def test_http_source(self, mock_tool_context):
        result = await initialize_source("http://example.com/data", mock_tool_context)

        assert mock_tool_context.state["source_type"] == "url"

    @pytest.mark.asyncio
    async def test_url_sets_domain_slug(self, mock_tool_context):
        await initialize_source("https://data.cms.gov/provider-data", mock_tool_context)

        assert mock_tool_context.state["domain_slug"] == "cms_gov"
        assert "cms_gov" in mock_tool_context.state["bq_bronze_dataset"]
        assert mock_tool_context.state["bq_bronze_dataset"].endswith("_bronze")

    @pytest.mark.asyncio
    async def test_gcs_no_domain_slug(self, mock_tool_context):
        await initialize_source("gs://bucket/path", mock_tool_context)

        assert mock_tool_context.state["domain_slug"] == ""
        # Falls back to default BQ_BRONZE_DATASET
        assert mock_tool_context.state["bq_bronze_dataset"].endswith("_bronze")

    @pytest.mark.asyncio
    async def test_same_domain_same_dataset(self, mock_tool_context):
        await initialize_source("https://data.cms.gov/page1", mock_tool_context)
        ds1 = mock_tool_context.state["bq_bronze_dataset"]

        mock_tool_context.state = {}
        await initialize_source("https://data.cms.gov/page2", mock_tool_context)
        ds2 = mock_tool_context.state["bq_bronze_dataset"]

        assert ds1 == ds2

    @pytest.mark.asyncio
    async def test_url_sets_staging_dataset(self, mock_tool_context):
        await initialize_source("https://data.cms.gov/provider-data", mock_tool_context)

        assert "cms_gov" in mock_tool_context.state["bq_staging_dataset"]
        assert mock_tool_context.state["bq_staging_dataset"].endswith("_staging")

    @pytest.mark.asyncio
    async def test_gcs_sets_staging_dataset(self, mock_tool_context):
        await initialize_source("gs://bucket/path", mock_tool_context)

        assert mock_tool_context.state["bq_staging_dataset"].endswith("_staging")
