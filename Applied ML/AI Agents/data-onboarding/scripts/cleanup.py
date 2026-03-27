"""Cleanup script for data-onboarding cloud and local resources.

Removes BQ datasets, GCS staging blobs, Dataplex lineage events,
Dataplex data profile scans, local output directory, and Agent Engine
deployments. Uses agent_orchestrator.config for naming consistency.

Usage:
    python scripts/cleanup.py              # interactive confirmation
    python scripts/cleanup.py --yes        # skip confirmation
    python scripts/cleanup.py --dry-run    # preview without deleting
    python scripts/cleanup.py --skip-bq    # skip BigQuery cleanup
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

import dotenv

# Load .env from project root (one level up from scripts/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
dotenv.load_dotenv(dotenv_path=PROJECT_ROOT / ".env")

sys.path.insert(0, str(PROJECT_ROOT))

from agent_orchestrator.config import (  # noqa: E402
    BQ_ANALYTICS_DATASET,
    BQ_BRONZE_DATASET,
    BQ_CONNECTION_ID,
    BQ_CONTEXT_DATASET,
    BQ_META_DATASET,
    BQ_DATASET_LOCATION,
    DATAPLEX_LOCATION,
    OUTPUT_DIR,
    GCS_STAGING_ROOT,
    GOOGLE_CLOUD_PROJECT,
    GOOGLE_CLOUD_STORAGE_BUCKET,
    RESOURCE_PREFIX,
    gcs_bucket_name,
)

DEPLOYMENT_FILE = PROJECT_ROOT / "deploy" / "deployment.json"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Clean up data-onboarding cloud and local resources.",
    )
    parser.add_argument("--yes", "-y", action="store_true", help="Skip confirmation prompt")
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview what would be deleted without deleting"
    )
    parser.add_argument("--skip-bq", action="store_true", help="Skip BigQuery dataset cleanup")
    parser.add_argument("--skip-gcs", action="store_true", help="Skip GCS staging cleanup")
    parser.add_argument("--skip-local", action="store_true", help="Skip local output cleanup")
    parser.add_argument(
        "--skip-agent-engine", action="store_true", help="Skip Agent Engine deployment cleanup"
    )
    parser.add_argument(
        "--skip-lineage", action="store_true", help="Skip Dataplex lineage cleanup"
    )
    parser.add_argument(
        "--skip-profiling", action="store_true", help="Skip Dataplex data profile scan cleanup"
    )
    return parser.parse_args()


def _discover_managed_datasets() -> list[str]:
    """Discover all domain-scoped datasets matching the RESOURCE_PREFIX pattern.

    Returns dataset names like data_onboarding_bronze, data_onboarding_cms_gov_bronze,
    data_onboarding_cms_gov_staging, etc.
    """
    if not GOOGLE_CLOUD_PROJECT:
        return [BQ_BRONZE_DATASET]

    try:
        from google.cloud import bigquery

        client = bigquery.Client(project=GOOGLE_CLOUD_PROJECT)
        prefix = f"{RESOURCE_PREFIX}_"
        datasets = []
        for ds in client.list_datasets():
            name = ds.dataset_id
            # Match: {RESOURCE_PREFIX}_*_bronze or {RESOURCE_PREFIX}_*_staging
            if name.startswith(prefix) and (
                name.endswith("_bronze") or name.endswith("_staging")
            ):
                datasets.append(name)
        return datasets if datasets else [BQ_BRONZE_DATASET]
    except Exception:
        return [BQ_BRONZE_DATASET]


def _print_plan(args: argparse.Namespace) -> list[str]:
    """Print and return a summary of what will be deleted."""
    actions: list[str] = []

    if not args.skip_bq:
        managed_datasets = _discover_managed_datasets()
        all_datasets = managed_datasets + [BQ_META_DATASET, BQ_CONTEXT_DATASET, BQ_ANALYTICS_DATASET]
        # Deduplicate while preserving order
        seen = set()
        for ds in all_datasets:
            if ds not in seen:
                seen.add(ds)
                ref = f"{GOOGLE_CLOUD_PROJECT}.{ds}" if GOOGLE_CLOUD_PROJECT else ds
                actions.append(f"BQ dataset: {ref} (location={BQ_DATASET_LOCATION})")
        actions.append(f"BQ connection: {BQ_CONNECTION_ID} (location={BQ_DATASET_LOCATION})")

    if not args.skip_gcs:
        bucket = gcs_bucket_name()
        if bucket:
            actions.append(f"GCS blobs:  gs://{bucket}/{GCS_STAGING_ROOT}/")
        else:
            actions.append("GCS blobs:  (skipped — no bucket configured)")

    if not args.skip_local:
        output_path = (PROJECT_ROOT / OUTPUT_DIR).resolve()
        actions.append(f"Local dir:  {output_path}")

    if not args.skip_lineage:
        lineage_loc = BQ_DATASET_LOCATION.lower()
        actions.append(
            f"Lineage:    Data Onboarding processes (location={lineage_loc})"
        )

    if not args.skip_profiling:
        actions.append(
            f"Profiling:  {RESOURCE_PREFIX}-* data scans (location={DATAPLEX_LOCATION})"
        )

    if not args.skip_agent_engine:
        if DEPLOYMENT_FILE.exists():
            try:
                meta = json.loads(DEPLOYMENT_FILE.read_text())
                rid = meta.get("resource_id", "")
                if rid:
                    actions.append(f"Agent Engine: {rid}")
                else:
                    actions.append("Agent Engine: (no resource_id in deployment.json)")
            except (json.JSONDecodeError, OSError):
                actions.append("Agent Engine: (could not read deployment.json)")
        else:
            actions.append("Agent Engine: (no deployment.json found)")

    print("\nResources to delete:")
    for a in actions:
        print(f"  - {a}")
    print()
    return actions


def _delete_bq_datasets(dry_run: bool) -> None:
    if not GOOGLE_CLOUD_PROJECT:
        print("  GOOGLE_CLOUD_PROJECT not set, skipping BQ cleanup.")
        return

    from google.cloud import bigquery

    client = bigquery.Client(project=GOOGLE_CLOUD_PROJECT)
    managed_datasets = _discover_managed_datasets()
    all_datasets = managed_datasets + [BQ_META_DATASET, BQ_CONTEXT_DATASET, BQ_ANALYTICS_DATASET]
    seen = set()
    for ds_name in all_datasets:
        if ds_name in seen:
            continue
        seen.add(ds_name)
        ds_ref = f"{GOOGLE_CLOUD_PROJECT}.{ds_name}"
        if dry_run:
            print(f"  [dry-run] Would delete BQ dataset: {ds_ref}")
            continue
        try:
            client.delete_dataset(ds_ref, delete_contents=True, not_found_ok=True)
            print(f"  Deleted BQ dataset: {ds_ref}")
        except Exception as e:
            print(f"  Error deleting BQ dataset {ds_ref}: {e}")

    # Delete BQ connection
    conn_ref = (
        f"projects/{GOOGLE_CLOUD_PROJECT}/locations/{BQ_DATASET_LOCATION}"
        f"/connections/{BQ_CONNECTION_ID}"
    )
    if dry_run:
        print(f"  [dry-run] Would delete BQ connection: {conn_ref}")
    else:
        try:
            from google.cloud import bigquery_connection_v1

            conn_client = bigquery_connection_v1.ConnectionServiceClient()
            conn_client.delete_connection(name=conn_ref)
            print(f"  Deleted BQ connection: {conn_ref}")
        except Exception as e:
            if "not found" in str(e).lower() or "404" in str(e):
                print(f"  BQ connection not found (already deleted): {BQ_CONNECTION_ID}")
            else:
                print(f"  Error deleting BQ connection: {e}")


def _delete_gcs_staging(dry_run: bool) -> None:
    bucket_name = gcs_bucket_name()
    if not bucket_name:
        print("  No GCS bucket configured, skipping.")
        return

    from google.cloud import storage

    client = storage.Client(project=GOOGLE_CLOUD_PROJECT)
    bucket = client.bucket(bucket_name)
    prefix = GCS_STAGING_ROOT.rstrip("/") + "/"
    blobs = list(bucket.list_blobs(prefix=prefix))

    if not blobs:
        print(f"  No blobs found under gs://{bucket_name}/{prefix}")
        return

    if dry_run:
        print(f"  [dry-run] Would delete {len(blobs)} blob(s) under gs://{bucket_name}/{prefix}")
        return

    bucket.delete_blobs(blobs)
    print(f"  Deleted {len(blobs)} blob(s) under gs://{bucket_name}/{prefix}")


def _delete_local_output(dry_run: bool) -> None:
    output_path = (PROJECT_ROOT / OUTPUT_DIR).resolve()
    if not output_path.exists():
        print(f"  Local output dir does not exist: {output_path}")
        return

    if dry_run:
        print(f"  [dry-run] Would remove directory: {output_path}")
        return

    shutil.rmtree(output_path)
    print(f"  Removed directory: {output_path}")


def _delete_lineage(dry_run: bool) -> None:
    """Delete Data Onboarding lineage processes (cascades to runs and events)."""
    if not GOOGLE_CLOUD_PROJECT:
        print("  GOOGLE_CLOUD_PROJECT not set, skipping lineage cleanup.")
        return

    try:
        from google.cloud.datacatalog_lineage_v1 import (
            DeleteProcessRequest,
            LineageClient,
            ListProcessesRequest,
        )
    except ImportError:
        print("  google-cloud-datacatalog-lineage not installed, skipping.")
        return

    client = LineageClient()
    location = BQ_DATASET_LOCATION.lower()
    parent = f"projects/{GOOGLE_CLOUD_PROJECT}/locations/{location}"

    deleted = 0
    try:
        request = ListProcessesRequest(parent=parent)
        for process in client.list_processes(request=request):
            display = process.display_name or ""
            attrs = process.attributes or {}
            system = attrs.get("system")
            system_val = getattr(system, "string_value", "") if system else ""
            if display == "Data Onboarding Pipeline" or system_val == "data-onboarding-agent":
                if dry_run:
                    print(f"  [dry-run] Would delete lineage process: {process.name}")
                else:
                    try:
                        client.delete_process(
                            request=DeleteProcessRequest(
                                name=process.name, allow_missing=True,
                            )
                        )
                        deleted += 1
                    except Exception as e:
                        print(f"  Error deleting process {process.name}: {e}")
    except Exception as e:
        print(f"  Error listing lineage processes: {e}")
        return

    if dry_run:
        return
    if deleted:
        print(f"  Deleted {deleted} lineage process(es) (with all runs and events)")
    else:
        print("  No data-onboarding lineage processes found.")


def _delete_profile_scans(dry_run: bool) -> None:
    """Delete Dataplex data profile scans created by the onboarding pipeline."""
    if not GOOGLE_CLOUD_PROJECT:
        print("  GOOGLE_CLOUD_PROJECT not set, skipping profiling cleanup.")
        return

    try:
        from google.cloud.dataplex_v1 import (
            DataScanServiceClient,
            DeleteDataScanRequest,
            ListDataScansRequest,
        )
    except ImportError:
        print("  google-cloud-dataplex not installed, skipping.")
        return

    client = DataScanServiceClient()
    parent = f"projects/{GOOGLE_CLOUD_PROJECT}/locations/{DATAPLEX_LOCATION}"
    prefix = RESOURCE_PREFIX.replace("_", "-")

    deleted = 0
    try:
        request = ListDataScansRequest(parent=parent)
        for scan in client.list_data_scans(request=request):
            scan_id = scan.name.rsplit("/", 1)[-1]
            if scan_id.startswith(prefix):
                if dry_run:
                    print(f"  [dry-run] Would delete scan: {scan_id}")
                else:
                    try:
                        client.delete_data_scan(
                            request=DeleteDataScanRequest(name=scan.name)
                        )
                        deleted += 1
                    except Exception as e:
                        print(f"  Error deleting scan {scan_id}: {e}")
    except Exception as e:
        print(f"  Error listing data scans: {e}")
        return

    if dry_run:
        return
    if deleted:
        print(f"  Deleted {deleted} data profile scan(s)")
    else:
        print(f"  No {prefix}-* data scans found.")


def _delete_agent_engine(dry_run: bool) -> None:
    if not DEPLOYMENT_FILE.exists():
        print("  No deployment.json found, skipping.")
        return

    try:
        meta = json.loads(DEPLOYMENT_FILE.read_text())
    except (json.JSONDecodeError, OSError) as e:
        print(f"  Could not read deployment.json: {e}")
        return

    resource_id = meta.get("resource_id", "")
    if not resource_id:
        print("  No resource_id in deployment.json, skipping.")
        return

    if dry_run:
        print(f"  [dry-run] Would delete Agent Engine: {resource_id}")
        return

    try:
        import vertexai
        from vertexai import agent_engines

        vertexai.init(
            project=GOOGLE_CLOUD_PROJECT,
            location=meta.get("location", "us-central1"),
        )
        agent_engines.delete(resource_name=resource_id, force=True)
        print(f"  Deleted Agent Engine: {resource_id}")

        # Clear deployment.json
        DEPLOYMENT_FILE.write_text("{}\n")
        print("  Cleared deployment.json")
    except Exception as e:
        print(f"  Error deleting Agent Engine: {e}")


def main() -> None:
    args = _parse_args()
    actions = _print_plan(args)

    if not actions:
        print("Nothing to clean up.")
        return

    if args.dry_run:
        print("Dry-run mode — no resources will be deleted.\n")

    if not args.dry_run and not args.yes:
        confirm = input("Proceed with deletion? [y/N] ").strip().lower()
        if confirm not in ("y", "yes"):
            print("Aborted.")
            sys.exit(0)

    if not args.skip_bq:
        print("\nBigQuery datasets:")
        _delete_bq_datasets(args.dry_run)

    if not args.skip_gcs:
        print("\nGCS staging:")
        _delete_gcs_staging(args.dry_run)

    if not args.skip_local:
        print("\nLocal output:")
        _delete_local_output(args.dry_run)

    if not args.skip_lineage:
        print("\nDataplex lineage:")
        _delete_lineage(args.dry_run)

    if not args.skip_profiling:
        print("\nDataplex profiling:")
        _delete_profile_scans(args.dry_run)

    if not args.skip_agent_engine:
        print("\nAgent Engine:")
        _delete_agent_engine(args.dry_run)

    print("\nDone.")


if __name__ == "__main__":
    main()
