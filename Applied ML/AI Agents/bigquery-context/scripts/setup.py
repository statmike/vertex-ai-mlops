"""Create BQ datasets, views, and Dataplex data profile scans.

Run once before using the agents:
    uv run python scripts/setup.py

Idempotent — safe to run multiple times. Skips resources that already exist.
"""

import os
import time
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "")
BQ_LOCATION = os.getenv("BQ_LOCATION", "US")
DATAPLEX_LOCATION = os.getenv("DATAPLEX_LOCATION", "us-central1")
RESOURCE_PREFIX = os.getenv("RESOURCE_PREFIX", "bigquery_context")

# ---------------------------------------------------------------------------
# Resources to create — themed BQ datasets with views over public tables.
#
# Each view is free (zero storage cost) and places the table in your
# project's Dataplex catalog so all three discovery approaches work equally.
# ---------------------------------------------------------------------------
RESOURCES = [
    {
        "dataset": f"{RESOURCE_PREFIX}_transportation",
        "description": (
            "Transportation data including bike share trips and stations "
            "from Austin, Texas and NYC taxi trip records."
        ),
        "views": [
            {
                "name": "austin_bikeshare_trips",
                "source": "bigquery-public-data.austin_bikeshare.bikeshare_trips",
                "description": (
                    "Bike share trip records from Austin, Texas. Each row is a single "
                    "bike trip with start/end times, stations, duration, and subscriber type."
                ),
            },
            {
                "name": "austin_bikeshare_stations",
                "source": "bigquery-public-data.austin_bikeshare.bikeshare_stations",
                "description": (
                    "Bike share station locations in Austin, Texas. Each row is a station "
                    "with name, status, latitude/longitude, and number of docks."
                ),
            },
            {
                "name": "nyc_taxi_trips_2022",
                "source": "bigquery-public-data.new_york_taxi_trips.tlc_yellow_trips_2022",
                "description": (
                    "NYC yellow taxi trip records for 2022. Includes pickup/dropoff times "
                    "and locations, fare amounts, tip amounts, and payment types."
                ),
            },
        ],
    },
    {
        "dataset": f"{RESOURCE_PREFIX}_weather",
        "description": (
            "Weather and climate data including historical hurricane tracks "
            "and global weather station records."
        ),
        "views": [
            {
                "name": "hurricanes",
                "source": "bigquery-public-data.noaa_hurricanes.hurricanes",
                "description": (
                    "International Best Track Archive for Climate Stewardship (IBTrACS). "
                    "Historical hurricane and tropical cyclone tracks with wind speed, "
                    "pressure, position, and storm classification from multiple agencies."
                ),
            },
            {
                "name": "weather_stations",
                "source": "bigquery-public-data.ghcn_d.ghcnd_stations",
                "description": (
                    "Global Historical Climatology Network weather station inventory. "
                    "Station locations with latitude, longitude, elevation, and name."
                ),
            },
        ],
    },
    {
        "dataset": f"{RESOURCE_PREFIX}_demographics",
        "description": (
            "Demographic data including US census population by ZIP code "
            "and baby name popularity by state from Social Security records."
        ),
        "views": [
            {
                "name": "population_by_zip_2010",
                "source": "bigquery-public-data.census_bureau_usa.population_by_zip_2010",
                "description": (
                    "US Census 2010 population counts by ZIP code. Includes total "
                    "population, minimum and maximum age, and gender breakdowns."
                ),
            },
            {
                "name": "usa_names_1910_current",
                "source": "bigquery-public-data.usa_names.usa_1910_current",
                "description": (
                    "US baby name popularity from Social Security applications. "
                    "Each row is a name-state-year-gender combination with occurrence count."
                ),
            },
        ],
    },
    {
        "dataset": f"{RESOURCE_PREFIX}_geography",
        "description": (
            "Geographic boundary and crime data for US locations "
            "including county boundaries and Austin crime reports."
        ),
        "views": [
            {
                "name": "us_counties",
                "source": "bigquery-public-data.geo_us_boundaries.counties",
                "description": (
                    "US county boundaries with FIPS codes, names, state associations, "
                    "land/water area, and geographic coordinates."
                ),
            },
            {
                "name": "austin_crime",
                "source": "bigquery-public-data.austin_crime.crime",
                "description": (
                    "Austin, Texas crime reports. Each row is a reported crime incident "
                    "with type, description, location, timestamp, and clearance status."
                ),
            },
        ],
    },
]


def create_datasets_and_views():
    """Create themed BQ datasets with views pointing to public tables."""
    from google.cloud import bigquery

    client = bigquery.Client(project=PROJECT_ID)

    for scope in RESOURCES:
        dataset_id = scope["dataset"]
        dataset_ref = f"{PROJECT_ID}.{dataset_id}"

        # Create dataset
        dataset = bigquery.Dataset(dataset_ref)
        dataset.location = BQ_LOCATION
        dataset.description = scope["description"]
        client.create_dataset(dataset, exists_ok=True)
        print(f"  Dataset: {dataset_ref}")

        # Create views
        for view_def in scope["views"]:
            view_ref = f"{dataset_ref}.{view_def['name']}"
            view = bigquery.Table(view_ref)
            view.view_query = f"SELECT * FROM `{view_def['source']}`"
            view.description = view_def["description"]

            try:
                client.delete_table(view_ref, not_found_ok=True)
                client.create_table(view)
                print(f"    View: {view_def['name']} -> {view_def['source']}")

                # Copy column descriptions from source table to view
                try:
                    source_table = client.get_table(view_def["source"])
                    created_view = client.get_table(view_ref)
                    created_view.schema = source_table.schema
                    client.update_table(created_view, ["schema"])
                except Exception:
                    pass  # column descriptions are nice-to-have
            except Exception as e:
                print(f"    View {view_def['name']}: FAILED - {e}")


def create_and_run_profile_scans():
    """Create Dataplex data profile scans for each view and run them."""
    from google.api_core.exceptions import AlreadyExists
    from google.cloud.dataplex_v1 import (
        CreateDataScanRequest,
        DataProfileSpec,
        DataScan,
        DataScanServiceClient,
        DataSource,
        GetDataScanJobRequest,
        RunDataScanRequest,
        Trigger,
    )

    client = DataScanServiceClient()
    parent = f"projects/{PROJECT_ID}/locations/{DATAPLEX_LOCATION}"
    prefix = RESOURCE_PREFIX.replace("_", "-")
    jobs = []

    # Collect views that have corresponding BQ views (skip failed ones)
    from google.cloud import bigquery

    bq_client = bigquery.Client(project=PROJECT_ID)
    views_to_scan = []
    for scope in RESOURCES:
        for view_def in scope["views"]:
            view_ref = f"{PROJECT_ID}.{scope['dataset']}.{view_def['name']}"
            try:
                bq_client.get_table(view_ref)
                views_to_scan.append((scope, view_def))
            except Exception:
                print(f"    Skipping scan (view not found): {view_def['name']}")

    for i, (scope, view_def) in enumerate(views_to_scan):
        scan_id = f"{prefix}-profile-{view_def['name'].replace('_', '-')}"
        scan_name = f"{parent}/dataScans/{scan_id}"
        resource = (
            f"//bigquery.googleapis.com/projects/{PROJECT_ID}"
            f"/datasets/{scope['dataset']}/tables/{view_def['name']}"
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
            description=f"Profile scan for {scope['dataset']}.{view_def['name']}",
        )

        try:
            operation = client.create_data_scan(
                request=CreateDataScanRequest(
                    parent=parent, data_scan=scan, data_scan_id=scan_id,
                )
            )
            operation.result()
            print(f"    Scan created: {scan_id}")
        except AlreadyExists:
            print(f"    Scan exists:  {scan_id}")

        # Run scan
        try:
            response = client.run_data_scan(
                request=RunDataScanRequest(name=scan_name)
            )
            jobs.append((scan_id, response.job.name))
            print(f"    Scan started: {scan_id}")
        except Exception as e:
            print(f"    Scan run failed: {scan_id} - {e}")

    # Wait for all scans to complete
    if jobs:
        print("\n  Waiting for profile scans to complete...")
        for scan_id, job_name in jobs:
            for _ in range(30):  # up to 5 minutes per scan
                time.sleep(10)
                job = client.get_data_scan_job(
                    request=GetDataScanJobRequest(name=job_name)
                )
                if job.state in (3, 4, 5):  # CANCELLED, SUCCEEDED, FAILED
                    status = "OK" if job.state == 4 else f"state={job.state}"
                    print(f"    {scan_id}: {status}")
                    break
            else:
                print(f"    {scan_id}: TIMEOUT")


def main():
    print(f"Setting up bigquery-context resources in {PROJECT_ID}...\n")

    print("Creating datasets and views:")
    create_datasets_and_views()

    print("\nCreating and running Dataplex profile scans:")
    create_and_run_profile_scans()

    print("\nSetup complete!")


if __name__ == "__main__":
    main()
