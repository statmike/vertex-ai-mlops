"""Delete all BQ datasets and Dataplex scans created by setup.py.

Run when done with the demo:
    uv run python scripts/cleanup.py
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "")
DATAPLEX_LOCATION = os.getenv("DATAPLEX_LOCATION", "us-central1")
RESOURCE_PREFIX = os.getenv("RESOURCE_PREFIX", "bigquery_context")

# ---------------------------------------------------------------------------
# Datasets to delete (must match setup.py)
# ---------------------------------------------------------------------------
DATASETS = [
    f"{RESOURCE_PREFIX}_transportation",
    f"{RESOURCE_PREFIX}_weather",
    f"{RESOURCE_PREFIX}_demographics",
    f"{RESOURCE_PREFIX}_geography",
]

# View names per dataset (must match setup.py) — used to derive scan IDs
VIEWS_BY_DATASET = {
    f"{RESOURCE_PREFIX}_transportation": [
        "austin_bikeshare_trips",
        "austin_bikeshare_stations",
        "nyc_taxi_trips_2022",
    ],
    f"{RESOURCE_PREFIX}_weather": [
        "hurricanes",
        "weather_stations",
    ],
    f"{RESOURCE_PREFIX}_demographics": [
        "population_by_zip_2010",
        "usa_names_1910_current",
    ],
    f"{RESOURCE_PREFIX}_geography": [
        "us_counties",
        "austin_crime",
    ],
}


def delete_profile_scans():
    """Delete all Dataplex data profile scans."""
    from google.api_core.exceptions import NotFound
    from google.cloud.dataplex_v1 import (
        DataScanServiceClient,
        DeleteDataScanRequest,
    )

    client = DataScanServiceClient()
    parent = f"projects/{PROJECT_ID}/locations/{DATAPLEX_LOCATION}"
    prefix = RESOURCE_PREFIX.replace("_", "-")

    for view_names in VIEWS_BY_DATASET.values():
        for view_name in view_names:
            scan_id = f"{prefix}-profile-{view_name.replace('_', '-')}"
            scan_name = f"{parent}/dataScans/{scan_id}"

            try:
                client.delete_data_scan(
                    request=DeleteDataScanRequest(name=scan_name)
                )
                print(f"  Deleted scan: {scan_id}")
            except NotFound:
                print(f"  Not found:    {scan_id}")
            except Exception as e:
                print(f"  Error:        {scan_id} - {e}")


def delete_datasets():
    """Delete all BQ datasets (cascades to views inside them)."""
    from google.cloud import bigquery

    client = bigquery.Client(project=PROJECT_ID)

    for dataset_id in DATASETS:
        dataset_ref = f"{PROJECT_ID}.{dataset_id}"
        try:
            client.delete_dataset(dataset_ref, delete_contents=True, not_found_ok=True)
            print(f"  Deleted dataset: {dataset_id}")
        except Exception as e:
            print(f"  Error: {dataset_id} - {e}")


def main():
    print(f"Cleaning up bigquery-context resources in {PROJECT_ID}...\n")

    print("Deleting Dataplex profile scans:")
    delete_profile_scans()

    print("\nDeleting BQ datasets and views:")
    delete_datasets()

    print("\nCleanup complete!")


if __name__ == "__main__":
    main()
