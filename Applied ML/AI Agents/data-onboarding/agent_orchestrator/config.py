"""Centralized configuration for the data-onboarding agent system.

All agents import from this module. It is a leaf module — only reads
environment variables, no imports from other agent packages.
"""

import os
from urllib.parse import urlparse

# --- GCP ---
GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "")
GOOGLE_CLOUD_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
GOOGLE_CLOUD_STORAGE_BUCKET = os.getenv("GOOGLE_CLOUD_STORAGE_BUCKET", "")

# --- Models ---
AGENT_MODEL = os.getenv("AGENT_MODEL", "gemini-2.5-flash")
AGENT_MODEL_LOCATION = os.getenv("AGENT_MODEL_LOCATION", "")
TOOL_MODEL = os.getenv("TOOL_MODEL", "gemini-2.5-flash")
TOOL_MODEL_LOCATION = os.getenv("TOOL_MODEL_LOCATION", "")

# --- Naming ---
RESOURCE_PREFIX = os.getenv("RESOURCE_PREFIX", "data_onboarding")

# --- Dataplex ---
# Default to us-central1 (not GOOGLE_CLOUD_LOCATION which ADK may override to "global").
# Dataplex data scans require a regional location, not a multi-region.
DATAPLEX_LOCATION = os.getenv("DATAPLEX_LOCATION", "us-central1")

# --- BigQuery ---
BQ_DATASET_LOCATION = os.getenv("BQ_DATASET_LOCATION", "US")
BQ_BRONZE_DATASET = os.getenv("BQ_BRONZE_DATASET") or f"{RESOURCE_PREFIX}_bronze"
BQ_META_DATASET = os.getenv("BQ_META_DATASET") or f"{RESOURCE_PREFIX}_meta"
BQ_CONTEXT_DATASET = os.getenv("BQ_CONTEXT_DATASET") or f"{RESOURCE_PREFIX}_context"
BQ_CONNECTION_ID = os.getenv("BQ_CONNECTION_ID") or f"{RESOURCE_PREFIX}_embed"
BQ_ANALYTICS_DATASET = os.getenv("BQ_ANALYTICS_DATASET") or f"{RESOURCE_PREFIX}_adk"
BQ_ANALYTICS_TABLE = os.getenv("BQ_ANALYTICS_TABLE", "agent_events")

# --- Partitioning ---
PARTITION_MIN_ROWS = int(os.getenv("PARTITION_MIN_ROWS", "10000"))

# --- GCS Staging ---
GCS_STAGING_ROOT = (
    os.getenv("GCS_STAGING_ROOT")
    or f"applied-ml/ai-agents/{RESOURCE_PREFIX.replace('_', '-')}"
)

# --- Web Crawling ---
CRAWL_SAME_ORIGIN_ONLY = os.getenv("CRAWL_SAME_ORIGIN_ONLY", "true").lower() == "true"
CRAWL_MAX_DEPTH = int(os.getenv("CRAWL_MAX_DEPTH", "1"))
CRAWL_MAX_FILES = int(os.getenv("CRAWL_MAX_FILES", "100"))
ACQUIRE_FILE_EXTENSIONS = os.getenv(
    "ACQUIRE_FILE_EXTENSIONS",
    "csv,tsv,json,jsonl,xlsx,xls,parquet,avro,orc,xml,pdf,txt,md,html,zip",
).split(",")

# --- File Classification ---
DATA_FILE_EXTENSIONS = os.getenv(
    "DATA_FILE_EXTENSIONS",
    "csv,tsv,json,jsonl,xlsx,xls,parquet,avro,orc,xml",
).split(",")
CONTEXT_FILE_EXTENSIONS = os.getenv(
    "CONTEXT_FILE_EXTENSIONS",
    "pdf,txt,md,html",
).split(",")

# --- Domain-based dataset naming ---

def extract_domain_slug(url: str) -> str:
    """Extract a BQ-safe slug from a URL's domain name.

    Only processes http/https URLs. Returns empty string for other schemes.
    Strips common subdomains (www, data, api, download, ftp) to get
    the registrable domain, then converts to a BQ-safe identifier.

    Examples:
        https://data.cms.gov/...  →  cms_gov
        https://www.census.gov/...  →  census_gov
        https://example.com/data  →  example_com
        gs://bucket/path  →  (empty string)
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return ""
    hostname = parsed.hostname or ""
    if not hostname:
        return ""
    parts = hostname.lower().split(".")
    # Remove common subdomains to get the main domain
    while len(parts) > 2 and parts[0] in ("www", "data", "api", "download", "ftp"):
        parts.pop(0)
    slug = "_".join(parts)
    # Replace any non-alphanumeric chars (except underscore) for BQ safety
    slug = "".join(c if c.isalnum() or c == "_" else "_" for c in slug)
    return slug.strip("_")


def get_bronze_dataset(domain_slug: str = "") -> str:
    """Return the bronze dataset name, optionally scoped by domain.

    Args:
        domain_slug: Domain slug from extract_domain_slug(). If empty,
            returns the static default BQ_BRONZE_DATASET.

    Returns:
        Dataset name like ``data_onboarding_cms_gov_bronze``.
    """
    if domain_slug:
        return f"{RESOURCE_PREFIX}_{domain_slug}_bronze"
    return BQ_BRONZE_DATASET


def get_staging_dataset(domain_slug: str = "") -> str:
    """Return the staging dataset name for external tables.

    External tables live in a separate staging dataset to keep the
    bronze dataset clean for downstream consumers.

    Args:
        domain_slug: Domain slug from extract_domain_slug(). If empty,
            returns ``{RESOURCE_PREFIX}_staging``.

    Returns:
        Dataset name like ``data_onboarding_cms_gov_staging``.
    """
    if domain_slug:
        return f"{RESOURCE_PREFIX}_{domain_slug}_staging"
    return f"{RESOURCE_PREFIX}_staging"


# --- Model with retry ---
# Wraps the model string in a Gemini instance with retry for transient errors.
# Import is deferred to keep config a leaf module for non-ADK consumers.
def _build_agent_model():
    """Build a Gemini model instance with retry options for transient errors."""
    try:
        from google.adk.models.google_llm import Gemini
        from google.genai import types

        return Gemini(
            model=AGENT_MODEL,
            retry_options=types.HttpRetryOptions(
                initial_delay=5,
                multiplier=2,
                attempts=6,
                http_status_codes=[408, 429, 499, 500, 502, 503, 504],
            ),
        )
    except Exception:
        # Fallback to plain string if Gemini import fails (e.g. in tests)
        return AGENT_MODEL

AGENT_MODEL_INSTANCE = _build_agent_model()

# --- Reranker ---
TOP_K = int(os.getenv("TOP_K", "10"))

# --- Output ---
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "./output")


# ---------------------------------------------------------------------------
# Scope — which datasets/tables the chat agent can query.
#
# Each entry is either:
#   "dataset"             — all tables in that dataset
#   "dataset.table"       — only that specific table
#
# When empty (default), the chat agent discovers datasets dynamically
# from the data_catalog table. When set, only these datasets/tables are
# available for the reranker and context cache.
#
# Set via CHAT_SCOPE env var (comma-separated), e.g.:
#   CHAT_SCOPE="cboe_bronze,other_dataset.specific_table"
# ---------------------------------------------------------------------------
CHAT_SCOPE: list[str] = [
    s.strip()
    for s in os.getenv("CHAT_SCOPE", "").split(",")
    if s.strip()
]


def get_scope_datasets() -> list[str]:
    """Return unique dataset names from CHAT_SCOPE (preserving order)."""
    return list(dict.fromkeys(entry.split(".")[0] for entry in CHAT_SCOPE))


def get_scoped_tables(dataset: str) -> list[str] | None:
    """Return the list of specific table names for a dataset, or None if all.

    Returns None when the bare dataset name appears in CHAT_SCOPE (= all tables).
    Returns a list of table names when only dataset.table entries exist.
    """
    if dataset in CHAT_SCOPE:
        return None  # bare dataset = all tables
    tables = [
        entry.split(".", 1)[1]
        for entry in CHAT_SCOPE
        if "." in entry and entry.split(".", 1)[0] == dataset
    ]
    return tables if tables else None


def is_table_in_scope(dataset: str, table: str) -> bool:
    """Check whether a specific table is in scope."""
    if not CHAT_SCOPE:
        return True  # no scope = everything in scope
    if dataset in CHAT_SCOPE:
        return True  # bare dataset = all tables
    return f"{dataset}.{table}" in CHAT_SCOPE


def get_dataplex_entry_name(dataset: str, table: str) -> str:
    """Build a Dataplex entry name for a BQ table in this project."""
    return (
        f"projects/{GOOGLE_CLOUD_PROJECT}/locations/{BQ_DATASET_LOCATION.lower()}"
        f"/entryGroups/@bigquery/entries/bigquery.googleapis.com"
        f"/projects/{GOOGLE_CLOUD_PROJECT}/datasets/{dataset}/tables/{table}"
    )


# --- Derived ---
def gcs_bucket_name() -> str:
    """Return the bucket name without gs:// prefix."""
    bucket = GOOGLE_CLOUD_STORAGE_BUCKET
    if bucket.startswith("gs://"):
        bucket = bucket[5:]
    return bucket.rstrip("/")
