"""Sandbox configuration — project, locations, tiers, and model ids.

Pure data module: reads environment, exposes constants and small helpers. No
SDK imports, so it is safe to import from anywhere (including tests) without
touching credentials.

Authentication is ADC only (CODE_STANDARDS §4). Nothing here reads a service
account key, and nothing ever should.
"""

import hashlib
import os
import re

from dotenv import load_dotenv

# Load .env from the project root if present. Real credentials never live here —
# .env is gitignored and holds only ids, locations, and the Looker host.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

# --- GCP ---------------------------------------------------------------------
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "")

# BigQuery datasets are created in a multi-region; Dataplex DataScans require a
# single region. These are deliberately different knobs — see DEV_NOTES.
BQ_LOCATION = os.getenv("BQ_LOCATION", "US")
DATAPLEX_LOCATION = os.getenv("DATAPLEX_LOCATION", "us-central1")

# Catalog entries for BigQuery tables are pinned to the BQ location, and every
# entry a glossary link references must sit in the link's own region. So the
# glossary, its terms, and the links all live here — not in DATAPLEX_LOCATION.
CATALOG_LOCATION = BQ_LOCATION.lower()

# --- Models ------------------------------------------------------------------
# One model id for both the client agent and the judge, held constant across all
# configurations so the sweep measures architecture rather than model.
AGENT_MODEL = os.getenv("AGENT_MODEL", "gemini-3.7-flash")
JUDGE_MODEL = os.getenv("JUDGE_MODEL", "gemini-3.7-flash")
MODEL_LOCATION = os.getenv("MODEL_LOCATION", "global")

# `google-genai` reads its backend and region from the environment. Derive them
# from the single knobs above rather than asking the operator to keep duplicate
# entries in .env in sync.
#
# These OVERWRITE rather than default. A `GOOGLE_CLOUD_LOCATION` exported for
# some unrelated tool would otherwise silently relocate every model call in the
# sweep — which is how the smoke run ended up on `us-central1` instead of
# `global`. Reproducibility beats deference to ambient state, so MODEL_LOCATION
# wins; change the region by changing MODEL_LOCATION.
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "TRUE"
os.environ["GOOGLE_CLOUD_LOCATION"] = MODEL_LOCATION

# --- Looker ------------------------------------------------------------------
# Instance-hosted MCP endpoint is LOOKER_BASE_URL + "/mcp" (NOT a googleapis.com
# host). Credentials come from the environment via looker-sdk's own convention.
LOOKER_BASE_URL = os.getenv("LOOKER_BASE_URL", "")

# The value shipped in .env.example. Treated as "unset" so a half-filled .env
# fails with a readable message instead of a DNS error deep inside an MCP client.
LOOKER_PLACEHOLDER_HOST = "your-instance.cloud.looker.com"
LOOKER_MODEL_T0 = os.getenv("LOOKER_MODEL_T0", "data_mcp_sandbox_t0")
LOOKER_MODEL_T1 = os.getenv("LOOKER_MODEL_T1", "data_mcp_sandbox_t1")
LOOKER_EXPLORE = os.getenv("LOOKER_EXPLORE", "transactions")

# ONE CONNECTION PER TIER, and that is the whole point. A Looker connection
# authenticates as itself, not as the calling user, so a single shared connection
# would make Path 2 the only arm whose tier boundary is not an IAM boundary.
# Each of these is ADC + `impersonated_service_account` = tier_sa(tier), which
# puts Path 2 behind the same 403 as every other path while staying keyless.
# See docs/looker_setup.md.
LOOKER_CONNECTION_T0 = os.getenv("LOOKER_CONNECTION_T0", "data_mcp_sandbox_t0")
LOOKER_CONNECTION_T1 = os.getenv("LOOKER_CONNECTION_T1", "data_mcp_sandbox_t1")

# Looker API3 credentials file. Unlike BigQuery, the Looker API has no ADC
# equivalent, so this pair is a genuine secret. Project-local and gitignored, by
# deliberate choice: no cross-project credential links. Relative paths resolve
# against the project root. See src/looker_client.py and looker.ini.template.
LOOKER_INI = os.getenv("LOOKER_INI", "looker.ini")

# --- Resource naming ---------------------------------------------------------
RESOURCE_PREFIX = os.getenv("RESOURCE_PREFIX", "data_mcp_sandbox")

# --- Governance tiers (the independent variable) -----------------------------
# The identical corpus is replicated into one dataset per tier, differing ONLY in
# governance. T0 is the ungoverned control; T1 carries descriptions, catalog
# enrichment, and a semantic LookML model. See DESIGN.md §6.3.
TIERS: tuple[int, ...] = (0, 1)

TIER_LABELS = {
    0: "0 · ungoverned control",
    1: "1 · governed",
}


def tier_dataset(tier: int) -> str:
    """Dataset id holding the corpus at a given governance tier."""
    return f"{RESOURCE_PREFIX}_t{tier}"


# -----------------------------------------------------------------------------
# Per-tier identities — how tier isolation is actually enforced.
#
# The Knowledge Catalog is project-wide and content-addressed: `search_entries`
# takes a query, not a scope, so a tier-0 agent asking for "revenue" was handed
# the *tier-1 governed entry* and answered from it. Nothing in the MCP surface
# can stop that — managed servers expose no scoping parameter, and Toolbox's
# `allowedDatasets` guards only its bigquery source. Measured: DEV_NOTES
# 2026-08-29, docs/scoping.md.
#
# IAM can, because SearchEntries is ACL-filtered per caller against the source
# system: without `bigquery.tables.get` on a table, its entry does not come back
# at all. So each arm runs as its own service account holding dataViewer on
# exactly one tier dataset, and the boundary is enforced by the platform rather
# than by the system prompt.
#
# Keyless throughout — tokens are impersonated from the operator's own ADC
# (CODE_STANDARDS §4). See `identity.py`.
# -----------------------------------------------------------------------------
TIER_SA_PREFIX = os.getenv("TIER_SA_PREFIX", "mcp-sandbox")

# Off by default: the identities need a one-time privileged bootstrap
# (`scripts/bootstrap_identities.sh`) that not every operator can run. Turning it
# off does NOT leave isolation to the prompt — it leaves the sandbox with no tier
# fence at all, so a cross-tier read will succeed. Run the bootstrap, or treat the
# results as uncontrolled. `make verify-isolation` is what tells the two apart.
#
# An earlier design provisioned one tier at a time in two "epochs" as a fallback
# for operators who cannot bootstrap. It was retired unbuilt once the identity
# fence verified 24/24 — see DEV_NOTES.md 2026-08-31.
USE_TIER_SA = os.getenv("USE_TIER_SA", "false").lower() in ("1", "true", "yes")


def tier_service_account(tier: int) -> str:
    """Email of the service account that runs the agents for one tier."""
    return f"{TIER_SA_PREFIX}-t{tier}@{require_project()}.iam.gserviceaccount.com"


def looker_model(tier: int) -> str:
    """LookML model name for a tier (t0 = raw passthrough, t1 = semantic)."""
    return LOOKER_MODEL_T0 if tier == 0 else LOOKER_MODEL_T1


def looker_connection(tier: int) -> str:
    """Looker BigQuery connection name for a tier. Impersonates `tier_service_account`."""
    return LOOKER_CONNECTION_T0 if tier == 0 else LOOKER_CONNECTION_T1


def looker_configured() -> bool:
    """True when LOOKER_BASE_URL points at a real instance, not the placeholder."""
    return bool(LOOKER_BASE_URL) and LOOKER_PLACEHOLDER_HOST not in LOOKER_BASE_URL


# -----------------------------------------------------------------------------
# Scope — which single tier dataset is visible to agents right now.
#
# CRITICAL: every tier dataset holds identically-named tables, and scoring
# matches on short table name. A run must resolve to EXACTLY ONE tier dataset or
# candidates collide across tiers and the scores are silently wrong. This is why
# SCOPE is a single dataset, never a list spanning tiers.
# -----------------------------------------------------------------------------
ACTIVE_TIER = int(os.getenv("ACTIVE_TIER", "1"))
SCOPE = tier_dataset(ACTIVE_TIER)


def set_active_tier(tier: int) -> None:
    """Repoint SCOPE at a different tier dataset (used by the battery harness).

    Mutates module globals so anything reading ``config.SCOPE`` observes the new
    tier. Callers holding cached metadata must refresh after calling this.
    """
    global ACTIVE_TIER, SCOPE  # noqa: PLW0603
    if tier not in TIERS:
        raise ValueError(f"Unknown tier {tier}; expected one of {TIERS}")
    ACTIVE_TIER = tier
    SCOPE = tier_dataset(tier)


def dataset_ref(tier: int) -> str:
    """Fully qualified `project.dataset` for a tier."""
    return f"{PROJECT_ID}.{tier_dataset(tier)}"


def table_ref(tier: int, table: str) -> str:
    """Fully qualified `project.dataset.table` for a tier."""
    return f"{dataset_ref(tier)}.{table}"


def dataplex_entry_name(tier: int, table: str) -> str:
    """Knowledge Catalog entry name for a BigQuery table in this project.

    BigQuery entries are fixed in the BQ location, which is why this uses
    BQ_LOCATION and not DATAPLEX_LOCATION.
    """
    return (
        f"projects/{PROJECT_ID}/locations/{BQ_LOCATION.lower()}"
        f"/entryGroups/@bigquery/entries/bigquery.googleapis.com"
        f"/projects/{PROJECT_ID}/datasets/{tier_dataset(tier)}/tables/{table}"
    )


def bounded_id(base: str) -> str:
    """Return a Dataplex-valid id: lowercased, sanitized, and length-bounded.

    Dataplex DataScan and entry-link ids allow only lowercase letters, digits,
    and hyphens. Table and column names here carry underscores, so normalize
    before bounding length. Deterministic, so `cleanup.py` rebuilds identical ids.
    """
    sanitized = re.sub(r"[^a-z0-9]+", "-", base.lower()).strip("-")
    if len(sanitized) <= 63:
        return sanitized
    digest = hashlib.sha1(base.encode()).hexdigest()[:8]  # noqa: S324 - id shortening, not crypto
    return f"{sanitized[:54].strip('-')}-{digest}"


def profile_scan_id(tier: int, table: str) -> str:
    """DataScan id for a table's profile scan at a given tier."""
    return bounded_id(f"{RESOURCE_PREFIX}-t{tier}-profile-{table}")


def definition_link_id(tier: int, term_id: str, table: str, column: str) -> str:
    """Entry-link id for a term-to-column definition link at a given tier.

    Tier is embedded because links across tier datasets share the `@bigquery`
    entry group and would otherwise collide on identical table/column names.
    """
    return bounded_id(f"def-t{tier}-{term_id}-{table}-{column}")


def require_project() -> str:
    """Return PROJECT_ID, failing loudly when it is unset."""
    if not PROJECT_ID:
        raise RuntimeError(
            "GOOGLE_CLOUD_PROJECT is not set. Copy .env.example to .env and fill it in, "
            "or run: gcloud config set project YOUR_PROJECT_ID"
        )
    return PROJECT_ID
