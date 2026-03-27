"""Tests for the publish_lineage tool (state assembly and error handling)."""

from unittest.mock import MagicMock, patch

import pytest

from agent_implement.tools.function_tool_publish_lineage import publish_lineage


@pytest.fixture
def mock_tool_context():
    ctx = MagicMock()
    ctx.state = {}
    return ctx


@pytest.fixture
def populated_state():
    """State dict representing a successful execute_sql run."""
    return {
        "source_id": "src-123",
        "source_uri": "https://data.gov/portal",
        "tables_created": {
            "sales": {"rows": 100, "table_id": "proj.bronze.sales"},
        },
        "external_tables": {
            "sales": "proj.bronze.ext_sales",
        },
        "files_acquired": [
            {
                "url": "https://data.gov/sales.csv",
                "gcs_path": "staging/src-123/sales.csv",
                "gcs_uri": "gs://bucket/staging/src-123/sales.csv",
            },
        ],
        "proposed_tables": {
            "sales": {
                "source_path": "staging/src-123/sales.csv",
                "columns": [{"name": "id", "bq_type": "INT64"}],
            },
        },
    }


class TestPublishLineageGuards:
    @pytest.mark.asyncio
    async def test_no_tables_created(self, mock_tool_context):
        result = await publish_lineage(mock_tool_context)
        assert "Run execute_sql first" in result

    @pytest.mark.asyncio
    async def test_no_source_uri(self, mock_tool_context):
        mock_tool_context.state["tables_created"] = {"t": {"rows": 1}}
        result = await publish_lineage(mock_tool_context)
        assert "source_uri" in result

    @pytest.mark.asyncio
    @patch("agent_implement.tools.function_tool_publish_lineage.GOOGLE_CLOUD_PROJECT", "")
    async def test_no_project(self, mock_tool_context):
        mock_tool_context.state["tables_created"] = {"t": {"rows": 1}}
        mock_tool_context.state["source_uri"] = "https://example.com"
        result = await publish_lineage(mock_tool_context)
        assert "GOOGLE_CLOUD_PROJECT" in result


class TestPublishLineageAssembly:
    @pytest.mark.asyncio
    @patch("agent_implement.tools.function_tool_publish_lineage.GOOGLE_CLOUD_PROJECT", "proj")
    @patch("agent_implement.tools.function_tool_publish_lineage.gcs_bucket_name", return_value="bucket")
    @patch("agent_implement.tools.function_tool_publish_lineage.write_processing_log")
    @patch("agent_implement.tools.function_tool_publish_lineage._publish")
    async def test_assembles_file_lineage(
        self, mock_publish, mock_log, mock_bucket, mock_tool_context, populated_state
    ):
        mock_tool_context.state.update(populated_state)
        mock_publish.return_value = {
            "process": "p/proc1",
            "run": "p/proc1/runs/r1",
            "events_created": 3,
        }

        result = await publish_lineage(mock_tool_context)

        # Verify _publish was called with correct arguments
        mock_publish.assert_called_once()
        call_args = mock_publish.call_args
        assert call_args.kwargs["source_id"] == "src-123"
        assert call_args.kwargs["starting_url"] == "https://data.gov/portal"

        file_lineage = call_args.kwargs["file_lineage"]
        assert len(file_lineage) == 1
        assert file_lineage[0]["file_url"] == "https://data.gov/sales.csv"
        assert file_lineage[0]["gcs_uri"] == "gs://bucket/staging/src-123/sales.csv"
        assert file_lineage[0]["external_table"] == "proj.bronze.ext_sales"

        assert "Lineage published" in result
        assert "Events created: 3" in result

    @pytest.mark.asyncio
    @patch("agent_implement.tools.function_tool_publish_lineage.GOOGLE_CLOUD_PROJECT", "proj")
    @patch("agent_implement.tools.function_tool_publish_lineage.gcs_bucket_name", return_value="bucket")
    @patch("agent_implement.tools.function_tool_publish_lineage.write_processing_log")
    @patch("agent_implement.tools.function_tool_publish_lineage._publish")
    async def test_handles_publish_error(
        self, mock_publish, mock_log, mock_bucket, mock_tool_context, populated_state
    ):
        mock_tool_context.state.update(populated_state)
        mock_publish.return_value = {"events_created": 0, "error": "API unavailable"}

        result = await publish_lineage(mock_tool_context)
        assert "failed" in result.lower()

    @pytest.mark.asyncio
    @patch("agent_implement.tools.function_tool_publish_lineage.GOOGLE_CLOUD_PROJECT", "proj")
    @patch("agent_implement.tools.function_tool_publish_lineage.gcs_bucket_name", return_value="bucket")
    @patch("agent_implement.tools.function_tool_publish_lineage.write_processing_log")
    @patch("agent_implement.tools.function_tool_publish_lineage._publish")
    async def test_builds_gcs_uri_from_bare_path(
        self, mock_publish, mock_log, mock_bucket, mock_tool_context, populated_state
    ):
        """When source_path doesn't start with gs://, prepend bucket."""
        mock_tool_context.state.update(populated_state)
        mock_publish.return_value = {"process": "p", "run": "r", "events_created": 3}

        await publish_lineage(mock_tool_context)

        file_lineage = mock_publish.call_args.kwargs["file_lineage"]
        # source_path is "staging/src-123/sales.csv" (no gs://), so bucket is prepended
        assert file_lineage[0]["gcs_uri"] == "gs://bucket/staging/src-123/sales.csv"

    @pytest.mark.asyncio
    @patch("agent_implement.tools.function_tool_publish_lineage.GOOGLE_CLOUD_PROJECT", "proj")
    @patch("agent_implement.tools.function_tool_publish_lineage.gcs_bucket_name", return_value="bucket")
    @patch("agent_implement.tools.function_tool_publish_lineage.write_processing_log")
    @patch("agent_implement.tools.function_tool_publish_lineage._publish")
    async def test_zip_extracted_passes_archive_gcs_uri(
        self, mock_publish, mock_log, mock_bucket, mock_tool_context
    ):
        """files_acquired entry with archive_gcs_uri passes it through to file_lineage."""
        mock_tool_context.state.update({
            "source_id": "src-zip",
            "source_uri": "https://data.gov/portal",
            "tables_created": {
                "report": {"rows": 50, "table_id": "proj.bronze.report"},
            },
            "external_tables": {
                "report": "proj.bronze.ext_report",
            },
            "files_acquired": [
                {
                    "url": "https://data.gov/data.zip",
                    "gcs_path": "staging/src-zip/report.csv",
                    "gcs_uri": "gs://bucket/staging/src-zip/report.csv",
                    "archive_gcs_uri": "gs://bucket/staging/src-zip/archives/data.zip",
                },
            ],
            "proposed_tables": {
                "report": {
                    "source_path": "staging/src-zip/report.csv",
                },
            },
        })
        mock_publish.return_value = {"process": "p", "run": "r", "events_created": 5}

        await publish_lineage(mock_tool_context)

        file_lineage = mock_publish.call_args.kwargs["file_lineage"]
        assert len(file_lineage) == 1
        assert file_lineage[0]["archive_gcs_uri"] == "gs://bucket/staging/src-zip/archives/data.zip"
        assert file_lineage[0]["gcs_uri"] == "gs://bucket/staging/src-zip/report.csv"

    @pytest.mark.asyncio
    @patch("agent_implement.tools.function_tool_publish_lineage.GOOGLE_CLOUD_PROJECT", "proj")
    @patch("agent_implement.tools.function_tool_publish_lineage.gcs_bucket_name", return_value="bucket")
    @patch("agent_implement.tools.function_tool_publish_lineage.write_processing_log")
    @patch("agent_implement.tools.function_tool_publish_lineage._publish")
    async def test_xlsx_sheet_in_gcs_uri(
        self, mock_publish, mock_log, mock_bucket, mock_tool_context
    ):
        """source_path with #Sheet1 produces gcs_uri with sheet suffix."""
        mock_tool_context.state.update({
            "source_id": "src-xlsx",
            "source_uri": "https://data.gov/portal",
            "tables_created": {
                "sales": {"rows": 10, "table_id": "proj.bronze.sales"},
            },
            "external_tables": {
                "sales": "proj.bronze.ext_sales",
            },
            "files_acquired": [
                {
                    "url": "https://data.gov/report.xlsx",
                    "gcs_path": "staging/src-xlsx/report.xlsx",
                    "gcs_uri": "gs://bucket/staging/src-xlsx/report.xlsx",
                },
            ],
            "proposed_tables": {
                "sales": {
                    "source_path": "staging/src-xlsx/report.xlsx#Sheet1",
                },
            },
        })
        mock_publish.return_value = {"process": "p", "run": "r", "events_created": 4}

        await publish_lineage(mock_tool_context)

        file_lineage = mock_publish.call_args.kwargs["file_lineage"]
        assert len(file_lineage) == 1
        assert file_lineage[0]["gcs_uri"] == "gs://bucket/staging/src-xlsx/report.xlsx#Sheet1"
        assert file_lineage[0]["file_url"] == "https://data.gov/report.xlsx"

    @pytest.mark.asyncio
    @patch("agent_implement.tools.function_tool_publish_lineage.GOOGLE_CLOUD_PROJECT", "proj")
    @patch("agent_implement.tools.function_tool_publish_lineage.gcs_bucket_name", return_value="bucket")
    @patch("agent_implement.tools.function_tool_publish_lineage.write_processing_log")
    @patch("agent_implement.tools.function_tool_publish_lineage._publish")
    async def test_multiple_tables(
        self, mock_publish, mock_log, mock_bucket, mock_tool_context
    ):
        mock_tool_context.state.update({
            "source_id": "src-1",
            "source_uri": "https://example.com",
            "tables_created": {
                "alpha": {"rows": 10, "table_id": "p.d.alpha"},
                "beta": {"rows": 20, "table_id": "p.d.beta"},
            },
            "external_tables": {"alpha": "p.d.ext_alpha", "beta": "p.d.ext_beta"},
            "files_acquired": [
                {"url": "https://example.com/a.csv", "gcs_path": "staging/a.csv"},
                {"url": "https://example.com/b.json", "gcs_path": "staging/b.json"},
            ],
            "proposed_tables": {
                "alpha": {"source_path": "staging/a.csv"},
                "beta": {"source_path": "staging/b.json"},
            },
        })
        mock_publish.return_value = {"process": "p", "run": "r", "events_created": 6}

        result = await publish_lineage(mock_tool_context)

        file_lineage = mock_publish.call_args.kwargs["file_lineage"]
        assert len(file_lineage) == 2
        assert "Events created: 6" in result
