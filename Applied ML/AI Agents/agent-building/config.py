"""Shared configuration loaded from environment variables.

All settings are read from the .env file at the project root. Every variable
has a sensible default so the project works out of the box (local, no deploy).

Two location concepts are kept separate — this matters:
    GOOGLE_CLOUD_LOCATION   → where infrastructure runs (Agent Runtime region)
    AGENT_MODEL_LOCATION    → which API endpoint ADK agents call for inference
    TOOL_MODEL_LOCATION     → which API endpoint tools call directly (google-genai)

Preview models (e.g. gemini-3-pro-preview) often live only on the `global`
endpoint, while Agent Runtime deploys to a region like `us-central1`. Keeping
these separate lets the same code run locally and deployed without 404s.
"""

import os
from pathlib import Path

import dotenv

# Load .env from the project root (this file's directory).
dotenv.load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")

# --- Google Cloud ---
GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "")
GOOGLE_CLOUD_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")

# --- Router / reasoning model (agent_concierge) ---
# Gemini 3 Pro: the strongest reasoning model, used for routing decisions.
AGENT_MODEL = os.getenv("AGENT_MODEL", "gemini-3-pro-preview")
AGENT_MODEL_LOCATION = os.getenv("AGENT_MODEL_LOCATION", "global")

# --- Catalog model (agent_catalog: unstructured search) ---
# Gemini 3 Flash: fast, capable, good for grounded document lookup.
CATALOG_MODEL = os.getenv("CATALOG_MODEL", "gemini-3-flash-preview")
CATALOG_MODEL_LOCATION = os.getenv("CATALOG_MODEL_LOCATION", "global")

# --- Analytics model (agent_analytics: BigQuery Q&A) ---
# Gemini 3 Flash Lite: cheapest/fastest — the heavy lifting is done by the
# Conversational Analytics API, so the agent itself just orchestrates.
ANALYTICS_MODEL = os.getenv("ANALYTICS_MODEL", "gemini-3-flash-lite-preview")
ANALYTICS_MODEL_LOCATION = os.getenv("ANALYTICS_MODEL_LOCATION", "global")

# --- Discovery model (agent_discovery: catalog search over A2A) ---
# Claude on Vertex (Model Garden) — demonstrates model variety. The ADK Claude
# wrapper builds an AnthropicVertex client from GOOGLE_CLOUD_PROJECT +
# GOOGLE_CLOUD_LOCATION, so the discovery process sets its location from this
# value (see agent_discovery/agent.py). `global` gives the best availability.
DISCOVERY_MODEL = os.getenv("DISCOVERY_MODEL", "claude-opus-5")
DISCOVERY_MODEL_LOCATION = os.getenv("DISCOVERY_MODEL_LOCATION", "global")

# ---------------------------------------------------------------------------
# Data sources (theLook retail demo)
# ---------------------------------------------------------------------------

# Public structured data — queried live, never copied. This is the "company
# already has data" stand-in: agents only read it.
THELOOK_PROJECT = os.getenv("THELOOK_PROJECT", "bigquery-public-data")
THELOOK_DATASET = os.getenv("THELOOK_DATASET", "thelook_ecommerce")

# Tables the analytics agent is allowed to reference (inline, read-only).
THELOOK_TABLES = [
    "products",
    "orders",
    "order_items",
    "users",
    "distribution_centers",
    "inventory_items",
]

# ---------------------------------------------------------------------------
# Resources this demo provisions (scripts/setup.py). A real company would
# already have these — everything derives from one prefix for easy cleanup.
# ---------------------------------------------------------------------------
RESOURCE_PREFIX = os.getenv("RESOURCE_PREFIX", "agent_building")

BQ_LOCATION = os.getenv("BQ_LOCATION", "US")
DATAPLEX_LOCATION = os.getenv("DATAPLEX_LOCATION", "us-central1")  # must be regional

# Unstructured demo corpus (return policy, sizing/care guides, FAQs) lives in
# GCS and is exposed to BigQuery through an object table for the catalog agent.
GCS_BUCKET = os.getenv("GCS_BUCKET", "")  # defaults to "<project>-agent-building" in setup
DOCS_PREFIX = os.getenv("DOCS_PREFIX", "retail-docs")

BQ_DATASET = os.getenv("BQ_DATASET") or f"{RESOURCE_PREFIX}_retail"
BQ_OBJECT_TABLE = os.getenv("BQ_OBJECT_TABLE", "retail_docs")

# ---------------------------------------------------------------------------
# A2A (agent_discovery is consumed remotely, not as an in-process sub-agent)
# ---------------------------------------------------------------------------
# Local: `to_a2a()` served by uvicorn. Deployed: the discovery agent's Runtime
# resource. The concierge reads this to build a RemoteA2aAgent.
DISCOVERY_A2A_HOST = os.getenv("DISCOVERY_A2A_HOST", "localhost")
DISCOVERY_A2A_PORT = int(os.getenv("DISCOVERY_A2A_PORT", "8001"))
DISCOVERY_A2A_URL = os.getenv("DISCOVERY_A2A_URL", "")  # overrides host:port when set

# ---------------------------------------------------------------------------
# Observability (BigQuery Agent Analytics plugin — see agent_concierge/bq_plugin.py)
# ---------------------------------------------------------------------------
BQ_ANALYTICS_DATASET = os.getenv("BQ_ANALYTICS_DATASET") or f"{RESOURCE_PREFIX}_analytics"
BQ_ANALYTICS_TABLE = os.getenv("BQ_ANALYTICS_TABLE", "agent_events")

# ---------------------------------------------------------------------------
# Deployment (deploy/ pushes agents to Agent Runtime — Phase 2)
# ---------------------------------------------------------------------------
# Cloud Storage bucket Agent Runtime stages the build in. Leave blank to let the
# SDK use the project's default staging bucket.
STAGING_BUCKET = os.getenv("STAGING_BUCKET", "")


def discovery_a2a_base_url() -> str:
    """Base URL where the discovery agent's A2A server is reachable.

    The concierge appends ADK's AGENT_CARD_WELL_KNOWN_PATH to this to locate
    the agent card — we import that constant rather than hardcode the suffix,
    since ADK owns the well-known path.
    """
    return (DISCOVERY_A2A_URL or f"http://{DISCOVERY_A2A_HOST}:{DISCOVERY_A2A_PORT}").rstrip("/")
