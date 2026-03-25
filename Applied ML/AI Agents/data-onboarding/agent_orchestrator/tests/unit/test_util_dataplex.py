"""Tests for the Dataplex data profiling utility."""

from unittest.mock import MagicMock, patch

from agent_orchestrator.util_dataplex import create_and_run_profile_scans


class TestCreateAndRunProfileScans:
    @patch("google.cloud.dataplex_v1.DataScanServiceClient")
    @patch("agent_orchestrator.util_dataplex.time.sleep")
    def test_creates_and_starts_scans(self, mock_sleep, mock_client_cls):
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        # create_data_scan returns an operation that .result() succeeds
        mock_op = MagicMock()
        mock_client.create_data_scan.return_value = mock_op

        # run_data_scan succeeds
        mock_client.run_data_scan.return_value = MagicMock()

        result = create_and_run_profile_scans(
            project="test-project",
            location="us-central1",
            dataset="bronze_ds",
            table_names=["table_a", "table_b"],
        )

        assert result["scans_created"] == 2
        assert result["scans_started"] == 2
        assert result["errors"] == []
        assert mock_client.create_data_scan.call_count == 2
        assert mock_client.run_data_scan.call_count == 2

    @patch("google.cloud.dataplex_v1.DataScanServiceClient")
    def test_idempotent_already_exists(self, mock_client_cls):
        from google.api_core.exceptions import AlreadyExists

        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        # create_data_scan raises AlreadyExists
        mock_client.create_data_scan.side_effect = AlreadyExists("exists")
        mock_client.run_data_scan.return_value = MagicMock()

        result = create_and_run_profile_scans(
            project="test-project",
            location="us-central1",
            dataset="bronze_ds",
            table_names=["table_a"],
        )

        # Not counted as created, but still started
        assert result["scans_created"] == 0
        assert result["scans_started"] == 1
        assert result["errors"] == []

    @patch("google.cloud.dataplex_v1.DataScanServiceClient")
    def test_run_error_recorded(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        mock_op = MagicMock()
        mock_client.create_data_scan.return_value = mock_op
        mock_client.run_data_scan.side_effect = Exception("quota exceeded")

        result = create_and_run_profile_scans(
            project="test-project",
            location="us-central1",
            dataset="bronze_ds",
            table_names=["table_a"],
        )

        assert result["scans_created"] == 1
        assert result["scans_started"] == 0
        assert len(result["errors"]) == 1
        assert "quota exceeded" in result["errors"][0]

    def test_empty_table_list(self):
        result = create_and_run_profile_scans(
            project="test-project",
            location="us-central1",
            dataset="bronze_ds",
            table_names=[],
        )

        assert result["scans_created"] == 0
        assert result["scans_started"] == 0
        assert result["errors"] == []

    @patch("google.cloud.dataplex_v1.DataScanServiceClient")
    def test_scan_id_format(self, mock_client_cls):
        """Scan IDs should use hyphens (not underscores) for Dataplex compatibility."""
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.create_data_scan.return_value = MagicMock()
        mock_client.run_data_scan.return_value = MagicMock()

        create_and_run_profile_scans(
            project="test-project",
            location="us-central1",
            dataset="data_onboarding_cms_gov_bronze",
            table_names=["provider_info"],
        )

        # Check the create request for proper scan_id format
        create_call = mock_client.create_data_scan.call_args
        request = create_call.kwargs.get("request")
        assert request is not None
        # The scan_id should use hyphens
        assert request.data_scan_id == "data-onboarding-cms-gov-bronze-profile-provider-info"
