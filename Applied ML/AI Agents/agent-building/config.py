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
def _project_id(raw: str) -> str:
    """Return the project *ID*, resolving from a project number if needed.

    Agent Runtime injects the reserved ``GOOGLE_CLOUD_PROJECT`` env var as the
    project *number*, but resource identifiers that must textually match — BigQuery
    fully-qualified table names, and especially the Knowledge Catalog ``parent:``
    search predicate (entries are named ``bigquery:{project_id}.dataset.table``) —
    need the project *ID*. A number silently matches nothing, so the deployed
    discovery agent's catalog search returns zero rows while it works locally.

    Locally the value from .env is already the ID (contains letters), so this is a
    no-op and makes no network call. Only a purely numeric value triggers a
    Resource Manager lookup to convert it.
    """
    if not raw or not raw.isdigit():
        return raw
    try:
        from google.cloud import resourcemanager_v3

        client = resourcemanager_v3.ProjectsClient()
        return client.get_project(name=f"projects/{raw}").project_id
    except Exception:
        # If resolution fails, fall back to the raw value rather than crashing at
        # import; call sites that only need a BigQuery client still work.
        return raw


GOOGLE_CLOUD_PROJECT = _project_id(os.getenv("GOOGLE_CLOUD_PROJECT", ""))
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
# MCP (agent_mcp_client consumes tools from a remote MCP server over HTTP)
# ---------------------------------------------------------------------------
# theLook's tools are re-published as an MCP server (see mcp_server/). This is the
# URL an ADK McpToolset connects to. Locally that's the Streamable-HTTP server
# from `python -m mcp_server.server --transport http`; in production it would be a
# Cloud Run service hosting the same app. The Streamable-HTTP endpoint is /mcp.
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8009/mcp")

# Model the MCP-client agent reasons with (Gemini 3 Flash — it just orchestrates
# calls to the MCP tools). Its own inference endpoint, same split as the others.
MCP_CLIENT_MODEL = os.getenv("MCP_CLIENT_MODEL", "gemini-3-flash-preview")
MCP_CLIENT_MODEL_LOCATION = os.getenv("MCP_CLIENT_MODEL_LOCATION", "global")

# --- Web-grounding model (agent_web: Google Search grounding) ---
# Gemini 3 Flash — a built-in grounding tool does the retrieval; the model
# synthesizes and cites. Grounding needs a Gemini model on a Vertex endpoint.
WEB_MODEL = os.getenv("WEB_MODEL", "gemini-3-flash-preview")
WEB_MODEL_LOCATION = os.getenv("WEB_MODEL_LOCATION", "global")

# ---------------------------------------------------------------------------
# Skill Registry (platform-managed, semantically-searchable skill bundles)
# ---------------------------------------------------------------------------
# The Skill Registry (`client.skills`) publishes packaged skill bundles — a
# directory with a SKILL.md at its root — that agents can discover by semantic
# search. Unlike loss clustering (global-only), the registry is served only in a
# few regions; `global` returns INTERNAL. Default to us-central1.
SKILL_REGISTRY_LOCATION = os.getenv("SKILL_REGISTRY_LOCATION", "us-central1")

# Where the skill bundles to publish live. This demo reuses the sibling
# `agent-skills/` project's bundles (SKILL.md + reference/ + narrative/) rather
# than authoring throwaway ones. Default resolves to that project relative to the
# repo root; override to point at any directory of skill bundles.
_DEFAULT_SKILLS_SRC = (
    Path(__file__).resolve().parents[3] / "agent-skills" / ".agents" / "skills"
)
SKILLS_SOURCE_DIR = os.getenv("SKILLS_SOURCE_DIR", str(_DEFAULT_SKILLS_SRC))

# ---------------------------------------------------------------------------
# Model Armor (Govern pillar — prompt/response guardrails)
# ---------------------------------------------------------------------------
# Model Armor screens user prompts and model responses for prompt-injection /
# jailbreak attempts, malicious URLs, and responsible-AI harms against a template
# you provision once (scripts/setup.py). The concierge applies it via
# before/after_model callbacks (see agent_concierge/guard.py). Set
# MODEL_ARMOR_TEMPLATE to "" to disable the guard entirely (callbacks no-op).
#
# The API is regional and uses a per-region REST endpoint
# (modelarmor.<location>.rep.googleapis.com); the template lives in that same
# region. Default to the infra location so it sits with the deployed agent.
MODEL_ARMOR_LOCATION = os.getenv("MODEL_ARMOR_LOCATION", GOOGLE_CLOUD_LOCATION)
MODEL_ARMOR_TEMPLATE = os.getenv("MODEL_ARMOR_TEMPLATE", f"{RESOURCE_PREFIX}_guard")

# ---------------------------------------------------------------------------
# Example Store (Build — managed few-shot example retrieval)
# ---------------------------------------------------------------------------
# The Example Store holds curated (question -> ideal answer) examples and serves
# the few most similar ones for each incoming question, so the analytics agent
# gets dynamic few-shot steering without hard-coding examples in the prompt. The
# store is provisioned + seeded by scripts/setup.py; the analytics agent attaches
# it via ADK's VertexAiExampleStore (see agent_analytics/examples.py).
#
# Vertex assigns the store a numeric resource ID at creation (a custom id passed
# to create() is NOT honored), so nothing here can predict the full resource name
# up front. Instead setup, cleanup, and the agent all key on the deterministic
# EXAMPLE_STORE_DISPLAY_NAME: setup creates/finds the store by that display name,
# and the agent resolves the store's resource name by listing and matching it.
# Set EXAMPLE_STORE_DISPLAY_NAME blank to disable (the agent runs with no tool).
#
# EXAMPLE_STORE_NAME is an optional escape hatch: set it to the full resource name
# (projects/.../exampleStores/<numeric-id>, which setup.py prints) to skip the
# list-and-match lookup entirely — handy in deploy where a network call at import
# is undesirable. The API is regional; keep it with the infra location. The
# embedding model backs the semantic search over stored examples.
EXAMPLE_STORE_LOCATION = os.getenv("EXAMPLE_STORE_LOCATION", GOOGLE_CLOUD_LOCATION)
EXAMPLE_STORE_DISPLAY_NAME = os.getenv(
    "EXAMPLE_STORE_DISPLAY_NAME", f"{RESOURCE_PREFIX.replace('_', '-')}-examples"
)
EXAMPLE_STORE_NAME = os.getenv("EXAMPLE_STORE_NAME", "")  # full resource name override
EXAMPLE_STORE_EMBEDDING_MODEL = os.getenv(
    "EXAMPLE_STORE_EMBEDDING_MODEL", "text-embedding-005"
)

# ---------------------------------------------------------------------------
# RAG Engine / Vector Search (Build — managed retrieval for the catalog agent)
# ---------------------------------------------------------------------------
# RAG Engine is the managed alternative to the catalog agent's object-table +
# AI.GENERATE approach: scripts/setup.py creates a RAG corpus (backed by the
# managed vector database — this is the "Vector Search" storage), imports the same
# GCS retail docs, and the catalog agent attaches a semantic-retrieval tool over
# it (see agent_catalog/rag.py). It runs *alongside* the object-table tool so both
# retrieval styles are demonstrable; the agent picks whichever fits.
#
# Like the Example Store, Vertex assigns the corpus a numeric resource id, so
# setup/cleanup/agent resolve it by the deterministic RAG_CORPUS_DISPLAY_NAME
# (or an explicit RAG_CORPUS_NAME full-resource-name override). Set the display
# name blank to disable (the agent keeps only the object-table tool). The API is
# regional; keep it with the infra location.
RAG_LOCATION = os.getenv("RAG_LOCATION", GOOGLE_CLOUD_LOCATION)
RAG_CORPUS_DISPLAY_NAME = os.getenv(
    "RAG_CORPUS_DISPLAY_NAME", f"{RESOURCE_PREFIX.replace('_', '-')}-retail-docs"
)
RAG_CORPUS_NAME = os.getenv("RAG_CORPUS_NAME", "")  # full resource name override
RAG_EMBEDDING_MODEL = os.getenv("RAG_EMBEDDING_MODEL", "text-embedding-005")
RAG_SIMILARITY_TOP_K = int(os.getenv("RAG_SIMILARITY_TOP_K", "5"))

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

    Local: a ``to_a2a()`` uvicorn server on host:port. Deployed: the discovery
    agent's Agent Runtime A2A endpoint (``.../reasoningEngines/{id}/a2a``). The
    concierge uses this to build the discovery agent card — a well-known URL
    locally, and (deployed) the resource name to read the card embedded in the
    Runtime resource, since the Runtime serves no fetchable card (see
    agent_concierge/utils/a2a.py).
    """
    return (DISCOVERY_A2A_URL or f"http://{DISCOVERY_A2A_HOST}:{DISCOVERY_A2A_PORT}").rstrip("/")
