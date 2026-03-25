"""Dataplex data profiling utility.

Creates and runs Dataplex data profile scans for BigQuery tables.
Profile results are published to the Dataplex catalog, making them
available via the lookupContext API for downstream discovery agents.
"""

import logging
import time

logger = logging.getLogger(__name__)


def create_and_run_profile_scans(
    project: str,
    location: str,
    dataset: str,
    table_names: list[str],
) -> dict:
    """Create and start Dataplex data profile scans for BigQuery tables.

    Creates one DataScan per table with 10% sampling and catalog publishing
    enabled. Scans are started but NOT waited on (fire-and-forget).
    Idempotent — AlreadyExists is handled gracefully.

    Args:
        project: GCP project ID.
        location: Dataplex location (e.g., ``us-central1``).
        dataset: BigQuery dataset ID containing the tables.
        table_names: List of table names to profile.

    Returns:
        Dict with ``scans_created``, ``scans_started``, and ``errors`` keys.
    """
    from google.api_core.exceptions import AlreadyExists
    from google.cloud.dataplex_v1 import (
        CreateDataScanRequest,
        DataProfileSpec,
        DataScan,
        DataScanServiceClient,
        DataSource,
        RunDataScanRequest,
        Trigger,
    )

    client = DataScanServiceClient()
    parent = f"projects/{project}/locations/{location}"
    prefix = dataset.replace("_", "-")

    scans_created = 0
    scans_started = 0
    errors = []

    for i, table_name in enumerate(table_names):
        scan_id = f"{prefix}-profile-{table_name.replace('_', '-')}"
        scan_name = f"{parent}/dataScans/{scan_id}"
        resource = (
            f"//bigquery.googleapis.com/projects/{project}"
            f"/datasets/{dataset}/tables/{table_name}"
        )

        # Pause between iterations to stay under Dataplex 30 req/min quota
        if i > 0:
            time.sleep(5)

        # Create scan
        scan = DataScan(
            data=DataSource(resource=resource),
            data_profile_spec=DataProfileSpec(
                sampling_percent=10.0,
                catalog_publishing_enabled=True,
            ),
            execution_spec=DataScan.ExecutionSpec(
                trigger=Trigger(on_demand=Trigger.OnDemand()),
            ),
            description=f"Profile scan for {dataset}.{table_name}",
        )

        try:
            operation = client.create_data_scan(
                request=CreateDataScanRequest(
                    parent=parent, data_scan=scan, data_scan_id=scan_id,
                )
            )
            operation.result()
            scans_created += 1
            logger.info("Scan created: %s", scan_id)
        except AlreadyExists:
            logger.info("Scan exists: %s", scan_id)

        # Run scan (fire-and-forget)
        try:
            client.run_data_scan(
                request=RunDataScanRequest(name=scan_name)
            )
            scans_started += 1
            logger.info("Scan started: %s", scan_id)
        except Exception as e:
            msg = f"{scan_id}: {e}"
            logger.warning("Scan run failed: %s", msg)
            errors.append(msg)

    return {
        "scans_created": scans_created,
        "scans_started": scans_started,
        "errors": errors,
    }
