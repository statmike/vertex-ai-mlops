"""Centralized configuration for the data-onboarding agent system.

All agents import from this module. It is a leaf module — only reads
environment variables, no imports from other agent packages.
"""

import os

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

# --- BigQuery ---
BQ_DATASET_LOCATION = os.getenv("BQ_DATASET_LOCATION", "US")
BQ_BRONZE_DATASET = os.getenv("BQ_BRONZE_DATASET") or f"{RESOURCE_PREFIX}_bronze"
BQ_BRONZE_META_DATASET = os.getenv("BQ_BRONZE_META_DATASET") or f"{RESOURCE_PREFIX}_bronze_meta"
BQ_ANALYTICS_DATASET = os.getenv("BQ_ANALYTICS_DATASET") or f"applied_ml_{RESOURCE_PREFIX}"
BQ_ANALYTICS_TABLE = os.getenv("BQ_ANALYTICS_TABLE", "agent_events")

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
    "csv,tsv,json,jsonl,xlsx,xls,parquet,avro,orc,xml,pdf,txt,md,html",
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

# --- Dataform ---
DATAFORM_OUTPUT_DIR = os.getenv("DATAFORM_OUTPUT_DIR", "./output/dataform")

# --- Derived ---
def gcs_bucket_name() -> str:
    """Return the bucket name without gs:// prefix."""
    bucket = GOOGLE_CLOUD_STORAGE_BUCKET
    if bucket.startswith("gs://"):
        bucket = bucket[5:]
    return bucket.rstrip("/")
