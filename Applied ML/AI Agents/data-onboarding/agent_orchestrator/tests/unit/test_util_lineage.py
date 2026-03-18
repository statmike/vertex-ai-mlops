"""Tests for Dataplex lineage FQN builders and publish_lineage orchestration."""

from unittest.mock import MagicMock, patch

from agent_orchestrator.util_lineage import (
    build_fqn_bigquery,
    build_fqn_bigquery_full,
    build_fqn_gcs,
    build_fqn_url,
    publish_lineage,
)


# ---------------------------------------------------------------------------
# FQN builders
# ---------------------------------------------------------------------------


class TestBuildFqnBigquery:
    def test_basic(self):
        assert (
            build_fqn_bigquery("my-proj", "my_ds", "my_tbl")
            == "bigquery:my-proj.my_ds.my_tbl"
        )

    def test_full(self):
        assert build_fqn_bigquery_full("p.d.t") == "bigquery:p.d.t"


class TestBuildFqnGcs:
    def test_with_gs_prefix(self):
        assert build_fqn_gcs("gs://bucket/path/file.csv") == "gcs:gs://bucket/path/file.csv"

    def test_without_gs_prefix(self):
        assert build_fqn_gcs("bucket/path/file.csv") == "gcs:gs://bucket/path/file.csv"


class TestBuildFqnUrl:
    def test_http(self):
        assert build_fqn_url("https://example.com/data.csv") == "custom:https://example.com/data.csv"

    def test_arbitrary_string(self):
        assert build_fqn_url("my-custom-source") == "custom:my-custom-source"


# ---------------------------------------------------------------------------
# publish_lineage
# ---------------------------------------------------------------------------


class TestPublishLineage:
    @patch("agent_orchestrator.util_lineage.GOOGLE_CLOUD_PROJECT", "")
    def test_skips_when_no_project(self):
        result = publish_lineage("src-1", "https://example.com", [])
        assert result["events_created"] == 0
        assert "error" in result

    def test_creates_process_run_events(self):
        """Verify full happy-path: process, run, and 3 events per file."""
        result = self._run_with_mocks(
            file_lineage=[
                {
                    "file_url": "https://example.com/data.csv",
                    "gcs_uri": "gs://bucket/staging/data.csv",
                    "external_table": "test-project.bronze.ext_data",
                },
            ],
        )
        assert result["events_created"] == 3
        assert "process" in result
        assert "run" in result

    @patch("agent_orchestrator.util_lineage.GOOGLE_CLOUD_PROJECT", "test-project")
    @patch("agent_orchestrator.util_lineage._lineage_location", return_value="us")
    def test_skips_event1_when_urls_match(self, _mock_loc):
        """When starting_url == file_url, Event 1 is skipped (direct file link)."""
        result = self._run_with_mocks(
            starting_url="https://example.com/data.csv",
            file_lineage=[
                {
                    "file_url": "https://example.com/data.csv",
                    "gcs_uri": "gs://bucket/staging/data.csv",
                    "external_table": "test-project.bronze.ext_data",
                },
            ],
        )
        # Only events 2 and 3 (URL→GCS, GCS→ext_table)
        assert result["events_created"] == 2

    @patch("agent_orchestrator.util_lineage.GOOGLE_CLOUD_PROJECT", "test-project")
    @patch("agent_orchestrator.util_lineage._lineage_location", return_value="us")
    def test_multiple_files(self, _mock_loc):
        """Each file produces its own set of lineage events."""
        result = self._run_with_mocks(
            file_lineage=[
                {
                    "file_url": "https://example.com/a.csv",
                    "gcs_uri": "gs://bucket/staging/a.csv",
                    "external_table": "p.d.ext_a",
                },
                {
                    "file_url": "https://example.com/b.json",
                    "gcs_uri": "gs://bucket/staging/b.json",
                    "external_table": "p.d.ext_b",
                },
            ],
        )
        assert result["events_created"] == 6  # 3 events per file × 2 files

    @patch("agent_orchestrator.util_lineage.GOOGLE_CLOUD_PROJECT", "test-project")
    @patch("agent_orchestrator.util_lineage._lineage_location", return_value="us")
    def test_missing_file_url_skips_events_1_and_2(self, _mock_loc):
        """If file_url is empty, events 1 and 2 are skipped; only event 3 fires."""
        result = self._run_with_mocks(
            file_lineage=[
                {
                    "file_url": "",
                    "gcs_uri": "gs://bucket/staging/data.csv",
                    "external_table": "p.d.ext_data",
                },
            ],
        )
        assert result["events_created"] == 1  # Only GCS → ext_table

    def test_handles_api_error(self):
        """API errors are caught and returned in the result dict."""
        result = self._run_with_mocks(file_lineage=[], raise_error=True)
        assert "error" in result
        assert result["events_created"] == 0

    # ------------------------------------------------------------------
    # Helper
    # ------------------------------------------------------------------

    @staticmethod
    def _run_with_mocks(
        starting_url: str = "https://example.com",
        file_lineage: list[dict] | None = None,
        raise_error: bool = False,
    ) -> dict:
        """Run publish_lineage with all Dataplex API calls mocked."""
        if file_lineage is None:
            file_lineage = []

        mock_client = MagicMock()
        mock_client.create_process.return_value = MagicMock(
            name="projects/p/locations/us/processes/proc1"
        )
        mock_client.create_run.return_value = MagicMock(
            name="projects/p/locations/us/processes/proc1/runs/run1"
        )
        mock_client.create_lineage_event.return_value = MagicMock(name="evt")

        if raise_error:
            mock_client.create_process.side_effect = Exception("API error")

        # Mock all the lazy imports inside publish_lineage
        mock_lineage_mod = MagicMock()
        mock_lineage_mod.LineageClient.return_value = mock_client
        mock_lineage_mod.Process.return_value = MagicMock()
        mock_lineage_mod.Run.return_value = MagicMock()
        mock_lineage_mod.Run.State.COMPLETED = 2
        mock_lineage_mod.CreateProcessRequest.return_value = MagicMock()
        mock_lineage_mod.CreateRunRequest.return_value = MagicMock()
        mock_lineage_mod.CreateLineageEventRequest.return_value = MagicMock()
        mock_lineage_mod.EntityReference.side_effect = lambda **kw: MagicMock(**kw)
        mock_lineage_mod.EventLink.side_effect = lambda **kw: MagicMock(**kw)
        mock_lineage_mod.LineageEvent.return_value = MagicMock()
        mock_lineage_mod.AttributeValue.side_effect = lambda **kw: MagicMock(**kw)

        mock_timestamp = MagicMock()
        mock_timestamp.Timestamp.return_value = MagicMock()

        with (
            patch.dict("sys.modules", {
                "google.cloud.datacatalog_lineage_v1": mock_lineage_mod,
                "google.cloud.datacatalog_lineage_v1.types": mock_lineage_mod,
                "google.protobuf.timestamp_pb2": mock_timestamp,
            }),
        ):
            return publish_lineage("src-1", starting_url, file_lineage)
