"""Tear down every billable resource `scripts/setup.py` created.

    uv run python scripts/cleanup.py [--yes]

Deletes, in dependency order: glossary definition links, glossary terms and the
glossary itself, Dataplex profile scans, and finally the tier datasets (with
their contents). Prompts unless `--yes`.

Does **not** touch Looker — the LookML models are hand-authored in a Git-backed
project and are not this script's to delete.
"""

import argparse
import sys

import _bootstrap  # noqa: F401 - import for the sys.path side effect
from google.api_core.exceptions import NotFound
from google.cloud import bigquery

import catalog_setup
import config


def delete_datasets(client: bigquery.Client) -> None:
    for tier in config.TIERS:
        dataset = config.dataset_ref(tier)
        try:
            client.delete_dataset(dataset, delete_contents=True, not_found_ok=True)
            print(f"    Dataset deleted: {config.tier_dataset(tier)}")
        except NotFound:
            pass


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--yes", action="store_true", help="Skip the confirmation prompt")
    args = parser.parse_args()

    project = config.require_project()
    targets = ", ".join(config.tier_dataset(t) for t in config.TIERS)
    print(f"This will DELETE from {project}:")
    print(f"  BigQuery datasets: {targets} (and all their tables)")
    print(f"  Dataplex profile + quality scans in {config.DATAPLEX_LOCATION}")
    print(f"  Glossary '{catalog_setup.GLOSSARY_ID}' in {config.CATALOG_LOCATION}, + terms/links")

    if not args.yes and input("\nProceed? [y/N] ").strip().lower() != "y":
        print("Aborted.")
        return 1

    print("\n[1/3] Glossary:")
    catalog_setup.delete_glossary()
    print("\n[2/3] Profile + quality scans:")
    catalog_setup.delete_profile_scans()
    catalog_setup.delete_quality_scans()
    print("\n[3/3] BigQuery datasets:")
    delete_datasets(bigquery.Client(project=project))

    print("\nDone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
