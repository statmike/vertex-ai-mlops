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
AGENT_MODEL_LOCATION = os.getenv("AGENT_MODEL_LOCATION", "")
TOOL_MODEL = os.getenv("TOOL_MODEL", "gemini-2.5-flash")
TOOL_MODEL_LOCATION = os.getenv("TOOL_MODEL_LOCATION", "")

# ADK uses GOOGLE_CLOUD_LOCATION for model endpoints. Override it when a
# separate AGENT_MODEL_LOCATION is configured (e.g., "global").
if AGENT_MODEL_LOCATION:
    os.environ["GOOGLE_CLOUD_LOCATION"] = AGENT_MODEL_LOCATION

# --- BigQuery ---
BQ_LOCATION = os.getenv("BQ_LOCATION", "US")

# --- Reranker ---
TOP_K = int(os.getenv("TOP_K", "5"))

# --- Resource prefix ---
RESOURCE_PREFIX = os.getenv("RESOURCE_PREFIX", "bigquery_context")

# --- Enrichment tier ---
# setup.py replicates the identical corpus into one dataset per tier
# ({prefix}_tier0.._tier3), differing only in Knowledge Catalog enrichment.
# ACTIVE_TIER selects which single tier dataset is in scope for a run. The
# benchmark sets this per run; the notebook / adk-web story defaults to the
# fully enriched tier 3.
#
# CRITICAL: every tier dataset holds identically-named tables, and downstream
# scoring matches on short table name. Scope must resolve to EXACTLY ONE tier
# dataset, or candidates collide across tiers. This is why SCOPE is a single
# dataset, not a list spanning tiers.
ACTIVE_TIER = int(os.getenv("ACTIVE_TIER", "3"))


def tier_dataset(tier: int) -> str:
    """Dataset id holding the corpus at a given enrichment tier."""
    return f"{RESOURCE_PREFIX}_tier{tier}"


# ---------------------------------------------------------------------------
# Scope — what agents search within.
#
# Each entry is either:
#   "dataset"             — all tables in that dataset
#   "dataset.table"       — only that specific table
#
# Scoped to the single ACTIVE_TIER dataset so all five discovery approaches see
# one consistent copy of the corpus. Agents discover the metadata at runtime via
# BQ API, Knowledge Catalog, etc.
# ---------------------------------------------------------------------------
SCOPE = [tier_dataset(ACTIVE_TIER)]


def set_active_tier(tier: int) -> None:
    """Repoint SCOPE at a different tier dataset (used by the benchmark harness).

    Mutates the module globals so downstream helpers (``get_datasets`` etc.) and
    any code reading ``config.SCOPE`` observe the new tier. Callers that also
    cache metadata (e.g. ``context_cache``) must repopulate after this.
    """
    global ACTIVE_TIER, SCOPE
    ACTIVE_TIER = tier
    SCOPE = [tier_dataset(tier)]


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
