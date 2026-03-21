"""Tests for the sample_data tool."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest


class _FakeToolContext:
    def __init__(self):
        self.state = {}


@pytest.fixture
def mock_bq_client():
    with patch(
        "agent_context.tools.function_tool_sample_data.GOOGLE_CLOUD_PROJECT",
        "test-project",
    ), patch("google.cloud.bigquery.Client") as mock_client_cls:
        client = MagicMock()
        mock_client_cls.return_value = client
        yield client


class TestSampleData:
    @pytest.mark.asyncio
    async def test_select_query(self, mock_bq_client):
        from agent_context.tools.function_tool_sample_data import sample_data

        # Mock query result with schema and rows
        field1 = SimpleNamespace(name="provider_type")
        field2 = SimpleNamespace(name="count")
        result_mock = MagicMock()
        result_mock.schema = [field1, field2]
        result_mock.__iter__ = lambda self: iter([
            {"provider_type": "Hospital", "count": 42},
            {"provider_type": "SNF", "count": 18},
        ])
        mock_bq_client.query.return_value.result.return_value = result_mock

        ctx = _FakeToolContext()
        result = await sample_data(
            "SELECT provider_type, COUNT(*) as count FROM `p.d.t` GROUP BY 1",
            ctx,
        )

        assert "provider_type" in result
        assert "Hospital" in result

    @pytest.mark.asyncio
    async def test_rejects_dml(self):
        with patch(
            "agent_context.tools.function_tool_sample_data.GOOGLE_CLOUD_PROJECT",
            "test-project",
        ):
            from agent_context.tools.function_tool_sample_data import sample_data

            ctx = _FakeToolContext()
            result = await sample_data("DELETE FROM `p.d.table` WHERE true", ctx)
            assert "Rejected" in result
            assert "SELECT" in result

    @pytest.mark.asyncio
    async def test_rejects_ddl(self):
        with patch(
            "agent_context.tools.function_tool_sample_data.GOOGLE_CLOUD_PROJECT",
            "test-project",
        ):
            from agent_context.tools.function_tool_sample_data import sample_data

            ctx = _FakeToolContext()
            result = await sample_data("DROP TABLE `p.d.table`", ctx)
            assert "Rejected" in result

    @pytest.mark.asyncio
    async def test_empty_result(self, mock_bq_client):
        from agent_context.tools.function_tool_sample_data import sample_data

        mock_bq_client.query.return_value.result.return_value = MagicMock(
            __iter__=lambda self: iter([])
        )
        # Make list() return empty
        result_mock = mock_bq_client.query.return_value.result.return_value
        result_mock.__iter__ = lambda self: iter([])

        ctx = _FakeToolContext()
        result = await sample_data("SELECT * FROM `p.d.t` WHERE false", ctx)
        assert "no rows" in result.lower()

    @pytest.mark.asyncio
    async def test_bytes_billed_cap(self, mock_bq_client):
        from agent_context.tools.function_tool_sample_data import sample_data

        result_mock = MagicMock()
        result_mock.__iter__ = lambda self: iter([])
        mock_bq_client.query.return_value.result.return_value = result_mock

        ctx = _FakeToolContext()
        await sample_data("SELECT 1", ctx)

        # Verify the job config was passed with maximum_bytes_billed
        call_args = mock_bq_client.query.call_args
        job_config = call_args.kwargs.get("job_config") or call_args[1].get("job_config")
        assert job_config.maximum_bytes_billed == 50_000_000
