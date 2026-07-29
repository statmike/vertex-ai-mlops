"""Delete all BQ datasets and Knowledge Catalog resources created by setup.py.

Run when done with the demo:
    uv run python scripts/cleanup.py

Knowledge Catalog is the product formerly called Dataplex Universal Catalog
(renamed April 2026). The API/SDK/IAM namespace remains ``dataplex``.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# Reuse the manifest + id helpers from setup so the two never drift.
import sys  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from setup import (  # noqa: E402
    CORPUS,
    GLOSSARY_ID,
    GLOSSARY_TERMS,
    TIERS,
    definition_link_id,
    profile_scan_id,
    tier_dataset,
)

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "")
BQ_LOCATION = os.getenv("BQ_LOCATION", "US")
DATAPLEX_LOCATION = os.getenv("DATAPLEX_LOCATION", "us-central1")
RESOURCE_PREFIX = os.getenv("RESOURCE_PREFIX", "bigquery_context")

# Glossary, terms, and entry links are co-located with the BQ entries in
# CATALOG_LOCATION (BQ_LOCATION); profile scans live in DATAPLEX_LOCATION.
# Keep this in lockstep with scripts/setup.py.
CATALOG_LOCATION = BQ_LOCATION.lower()

DATASETS = [tier_dataset(t) for t in TIERS]


def delete_entry_links():
    """Delete term↔column definition links (tiers >= 2)."""
    from google.api_core.exceptions import NotFound
    from google.cloud import dataplex_v1

    client = dataplex_v1.CatalogServiceClient()
    loc = CATALOG_LOCATION
    link_parent = f"projects/{PROJECT_ID}/locations/{loc}/entryGroups/@bigquery"

    for tier in TIERS:
        if tier < 2:
            continue
        for term_id, term_def in GLOSSARY_TERMS.items():
            for table, columns in term_def.get("columns", {}).items():
                for column in columns:
                    link_id = definition_link_id(tier, term_id, table, column)
                    link_name = f"{link_parent}/entryLinks/{link_id}"
                    try:
                        client.delete_entry_link(name=link_name)
                        print(f"  Deleted link: {link_id}")
                    except NotFound:
                        print(f"  Not found:    {link_id}")
                    except Exception as e:
                        print(f"  Error:        {link_id} - {e}")


def delete_glossary():
    """Delete the business glossary (cascades to its terms). LRO."""
    from google.api_core.exceptions import NotFound
    from google.cloud import dataplex_v1

    client = dataplex_v1.BusinessGlossaryServiceClient()
    glossary_name = (
        f"projects/{PROJECT_ID}/locations/{CATALOG_LOCATION}"
        f"/glossaries/{GLOSSARY_ID}"
    )
    try:
        op = client.delete_glossary(name=glossary_name)
        op.result()
        print(f"  Deleted glossary: {GLOSSARY_ID}")
    except NotFound:
        print(f"  Not found:        {GLOSSARY_ID}")
    except Exception as e:
        print(f"  Error:            {GLOSSARY_ID} - {e}")


def delete_profile_scans():
    """Delete all Knowledge Catalog data profile scans (tiers >= 1)."""
    from google.api_core.exceptions import NotFound
    from google.cloud.dataplex_v1 import (
        DataScanServiceClient,
        DeleteDataScanRequest,
    )

    client = DataScanServiceClient()
    parent = f"projects/{PROJECT_ID}/locations/{DATAPLEX_LOCATION}"

    for tier in TIERS:
        if tier < 1:
            continue
        for view_def in CORPUS:
            scan_id = profile_scan_id(tier, view_def["name"])
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
    """Delete all tier datasets (cascades to views inside them)."""
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

    print("Deleting term definition links:")
    delete_entry_links()

    print("\nDeleting business glossary:")
    delete_glossary()

    print("\nDeleting profile scans:")
    delete_profile_scans()

    print("\nDeleting BQ datasets and views:")
    delete_datasets()

    print("\nCleanup complete!")


if __name__ == "__main__":
    main()
