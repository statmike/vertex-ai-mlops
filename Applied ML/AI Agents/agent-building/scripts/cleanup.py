"""Tear down everything scripts/setup.py provisioned.

    uv run python scripts/cleanup.py

Idempotent: missing resources are skipped. Names are reconstructed from the same
config + helpers setup.py used, so this removes exactly what was created:

  - Agent Runtime service-agent IAM bindings (catalog search)
  - Dataplex profile scans (one per view)
  - BigQuery dataset {BQ_DATASET} (views + object table, deleted with contents)
  - BigQuery AI connection {BQ_DATASET}_ai
  - GCS docs bucket (and its contents)
  - BigQuery analytics dataset {BQ_ANALYTICS_DATASET} (observability logs)

It does NOT disable APIs or touch the public theLook data (we only read it).
"""

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import (  # noqa: E402
    BQ_ANALYTICS_DATASET,
    BQ_DATASET,
    BQ_LOCATION,
    DATAPLEX_LOCATION,
    GOOGLE_CLOUD_PROJECT,
    THELOOK_TABLES,
)
from scripts.resources import (  # noqa: E402
    agent_runtime_service_agent,
    ai_connection_id,
    docs_bucket_name,
    profile_scan_id,
)

# Kept in sync with setup.RUNTIME_SA_ROLES — the roles to revoke on teardown.
RUNTIME_SA_ROLES = [
    "roles/dataplex.catalogViewer",
]


def _run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True)


def revoke_runtime_iam() -> None:
    """Remove the IAM bindings setup.py granted the Agent Runtime service agent."""
    number = _run(
        ["gcloud", "projects", "describe", GOOGLE_CLOUD_PROJECT, "--format=value(projectNumber)"]
    ).stdout.strip()
    if not number:
        print("Agent Runtime IAM: could not resolve project number; skipping.")
        return
    sa = agent_runtime_service_agent(number)
    print("Revoking Agent Runtime IAM:")
    for role in RUNTIME_SA_ROLES:
        result = _run(
            [
                "gcloud", "projects", "remove-iam-policy-binding", GOOGLE_CLOUD_PROJECT,
                f"--member=serviceAccount:{sa}", f"--role={role}", "--quiet",
            ]
        )
        if result.returncode == 0:
            print(f"    Revoked: {role}")
        else:
            print(f"    Not removed (may not exist): {role}")


def delete_profile_scans() -> None:
    from google.api_core.exceptions import NotFound
    from google.cloud.dataplex_v1 import DataScanServiceClient, DeleteDataScanRequest

    client = DataScanServiceClient()
    parent = f"projects/{GOOGLE_CLOUD_PROJECT}/locations/{DATAPLEX_LOCATION}"
    print("Deleting profile scans:")
    for table in THELOOK_TABLES:
        scan_id = profile_scan_id(table)
        name = f"{parent}/dataScans/{scan_id}"
        try:
            client.delete_data_scan(request=DeleteDataScanRequest(name=name)).result()
            print(f"    Deleted: {scan_id}")
        except NotFound:
            print(f"    Not found: {scan_id}")
        except Exception as e:  # noqa: BLE001
            print(f"    FAILED (non-fatal): {scan_id} - {e}")


def delete_datasets() -> None:
    """Delete the working dataset and the analytics dataset (with contents)."""
    from google.cloud import bigquery

    client = bigquery.Client(project=GOOGLE_CLOUD_PROJECT)
    print("Deleting BigQuery datasets:")
    for dataset in (BQ_DATASET, BQ_ANALYTICS_DATASET):
        ref = f"{GOOGLE_CLOUD_PROJECT}.{dataset}"
        client.delete_dataset(ref, delete_contents=True, not_found_ok=True)
        print(f"    Deleted: {ref}")


def delete_ai_connection() -> None:
    conn_id = ai_connection_id()
    result = _run(
        [
            "bq", "rm", "--connection", "--force",
            "--project_id", GOOGLE_CLOUD_PROJECT,
            "--location", BQ_LOCATION.lower(), conn_id,
        ]
    )
    if result.returncode == 0:
        print(f"Deleted AI connection: {conn_id}")
    else:
        print(f"AI connection not removed (may not exist): {conn_id}")


def delete_docs_bucket() -> None:
    from google.cloud import storage

    client = storage.Client(project=GOOGLE_CLOUD_PROJECT)
    bucket_name = docs_bucket_name()
    bucket = client.bucket(bucket_name)
    if bucket.exists():
        bucket.delete(force=True)
        print(f"Deleted bucket: gs://{bucket_name}")
    else:
        print(f"Bucket not found: gs://{bucket_name}")


def main() -> None:
    if not GOOGLE_CLOUD_PROJECT:
        sys.exit("GOOGLE_CLOUD_PROJECT is not set.")

    print(f"Removing agent-building resources from {GOOGLE_CLOUD_PROJECT}\n")
    revoke_runtime_iam()
    print()
    delete_profile_scans()
    print()
    delete_ai_connection()
    print()
    delete_docs_bucket()
    print()
    delete_datasets()
    print("\nCleanup complete.")


if __name__ == "__main__":
    main()
