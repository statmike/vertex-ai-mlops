"""Tests for function_tool_search_catalog (agent_discovery).

The Dataplex CatalogServiceClient is patched, so these run offline — we verify
the tool renders catalog hits into markdown, records the tables it surfaced, and
surfaces errors cleanly.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from agent_discovery.tools import function_tool_search_catalog
from agent_discovery.tools.function_tool_search_catalog import search_catalog


def _hit(display_name: str, description: str, fqn: str):
    """Build a stand-in for one SearchEntriesResult."""
    source = SimpleNamespace(display_name=display_name, description=description)
    entry = SimpleNamespace(entry_source=source, fully_qualified_name=fqn)
    return SimpleNamespace(dataplex_entry=entry)


@pytest.fixture(autouse=True)
def _reset_client():
    function_tool_search_catalog._catalog_client = None
    yield
    function_tool_search_catalog._catalog_client = None


def _patch_hits(hits):
    mock_client = MagicMock()
    mock_client.search_entries.return_value = iter(hits)
    return patch.object(function_tool_search_catalog, "_client", return_value=mock_client)


class TestSearchCatalog:
    @pytest.mark.asyncio
    async def test_renders_hits_and_records_tables(self, mock_tool_context):
        hits = [
            _hit("orders", "One row per order.", "bigquery:proj.ds.orders"),
            _hit("order_items", "Line items per order.", "bigquery:proj.ds.order_items"),
        ]
        with _patch_hits(hits):
            result = await search_catalog("where are orders?", mock_tool_context)
        assert "**orders**" in result
        assert "One row per order." in result
        assert "**order_items**" in result
        assert mock_tool_context.state["discovery_last_tables"] == [
            "bigquery:proj.ds.orders",
            "bigquery:proj.ds.order_items",
        ]

    @pytest.mark.asyncio
    async def test_missing_description_falls_back(self, mock_tool_context):
        with _patch_hits([_hit("users", "", "bigquery:proj.ds.users")]):
            result = await search_catalog("customer data?", mock_tool_context)
        assert "**users**" in result
        assert "(no description)" in result

    @pytest.mark.asyncio
    async def test_no_matches(self, mock_tool_context):
        with _patch_hits([]):
            result = await search_catalog("spaceships?", mock_tool_context)
        assert "No tables in the catalog matched" in result
        assert "discovery_last_tables" not in mock_tool_context.state

    @pytest.mark.asyncio
    async def test_error_is_surfaced(self, mock_tool_context):
        mock_client = MagicMock()
        mock_client.search_entries.side_effect = RuntimeError("boom")
        with patch.object(function_tool_search_catalog, "_client", return_value=mock_client):
            result = await search_catalog("anything", mock_tool_context)
        assert "Error searching the data catalog" in result
        assert "setup.py" in result
