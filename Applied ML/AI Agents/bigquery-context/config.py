"""Agent configuration — scope and settings for ADK agents.

Defines which BQ datasets/tables the agents search within, plus model
and reranker settings. Agents discover metadata at runtime.
Pure data module — no SDK imports.
"""

import os

# --- GCP ---
GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "")
GOOGLE_CLOUD_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")

# --- Models ---
AGENT_MODEL = os.getenv("AGENT_MODEL", "gemini-2.5-flash")
TOOL_MODEL = os.getenv("TOOL_MODEL", "gemini-2.5-flash")

# --- BigQuery ---
BQ_LOCATION = os.getenv("BQ_LOCATION", "US")

# --- Reranker ---
TOP_K = int(os.getenv("TOP_K", "5"))

# --- Resource prefix ---
RESOURCE_PREFIX = os.getenv("RESOURCE_PREFIX", "bigquery_context")

# ---------------------------------------------------------------------------
# Scope — what agents search within.
#
# Each entry is either:
#   "dataset"             — all tables in that dataset
#   "dataset.table"       — only that specific table
#
# Setup creates these datasets with views over bigquery-public-data tables.
# Agents discover the metadata at runtime via BQ API, Dataplex, etc.
# ---------------------------------------------------------------------------
SCOPE = [
    f"{RESOURCE_PREFIX}_transportation.austin_bikeshare_trips",
    f"{RESOURCE_PREFIX}_transportation.austin_bikeshare_stations",
    f"{RESOURCE_PREFIX}_transportation.nyc_taxi_trips_2022",
    f"{RESOURCE_PREFIX}_weather",
    f"{RESOURCE_PREFIX}_demographics",
    f"{RESOURCE_PREFIX}_geography",
]


# ---------------------------------------------------------------------------
# Helpers — parse SCOPE into datasets, tables, and filters
# ---------------------------------------------------------------------------

def get_datasets() -> list[str]:
    """Return unique dataset names from SCOPE (preserving order)."""
    return list(dict.fromkeys(entry.split(".")[0] for entry in SCOPE))


def get_scoped_tables(dataset: str) -> list[str] | None:
    """Return the list of specific table names for a dataset, or None if all.

    Returns None when the bare dataset name appears in SCOPE (= all tables).
    Returns a list of table names when only dataset.table entries exist.
    """
    if dataset in SCOPE:
        return None  # bare dataset = all tables
    tables = [
        entry.split(".", 1)[1]
        for entry in SCOPE
        if "." in entry and entry.split(".", 1)[0] == dataset
    ]
    return tables if tables else None


def is_table_in_scope(dataset: str, table: str) -> bool:
    """Check whether a specific table is in scope."""
    if dataset in SCOPE:
        return True  # bare dataset = all tables
    return f"{dataset}.{table}" in SCOPE


def get_dataplex_entry_name(dataset: str, table: str) -> str:
    """Build a Dataplex entry name for a BQ table in this project."""
    return (
        f"projects/{GOOGLE_CLOUD_PROJECT}/locations/{BQ_LOCATION.lower()}"
        f"/entryGroups/@bigquery/entries/bigquery.googleapis.com"
        f"/projects/{GOOGLE_CLOUD_PROJECT}/datasets/{dataset}/tables/{table}"
    )


def get_dataplex_dataset_entry_name(dataset: str) -> str:
    """Build a Dataplex entry name for a BQ dataset in this project."""
    return (
        f"projects/{GOOGLE_CLOUD_PROJECT}/locations/{BQ_LOCATION.lower()}"
        f"/entryGroups/@bigquery/entries/bigquery.googleapis.com"
        f"/projects/{GOOGLE_CLOUD_PROJECT}/datasets/{dataset}"
    )
