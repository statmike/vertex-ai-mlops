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

# The one model knob Conversational Analytics actually exposes (Amendment C.4).
# Enumerated against SDK 0.13.2, not read from documentation:
#
#   ChatRequest.ThinkingMode   THINKING_MODE_UNSPECIFIED=0, FAST=1, THINKING=2
#   ChatRequest.Model          MODEL_UNSPECIFIED=0, LATEST_GA_MODEL=1
#
# `Model` has exactly one selectable value, so going direct buys no choice of
# model — only a choice of how hard it thinks. That asymmetry against the MCP
# arms, which expose neither, is the finding C.4 measures.
#
# Empty is the published default. The field has no proto presence, so leaving it
# empty sends the identical bytes every published direct cell sent — which is
# what makes the published capture a usable control rather than a near-copy.
CA_THINKING_MODE = os.getenv("CA_THINKING_MODE", "")

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
# enrichment, and a semantic LookML model. See docs/paths.md.
#
# The ladder (Amendment C.2) adds three intermediate tiers between them. It is
# opt-in because turning it on triples the provisioned surface and would change
# what `make sweep` means: the published 1,440-cell factorial is two tiers, and a
# five-tier default would silently stop reproducing it.
LADDER = os.getenv("LADDER", "false").lower() in ("1", "true", "yes")

TIERS: tuple[int, ...] = (0, 1, 2, 3, 4) if LADDER else (0, 1)

# Every tier this project can ever provision, whether or not it is provisioning
# them today. Teardown iterates this rather than `TIERS`: a `make teardown` run
# with the ladder off must still delete the scans a ladder run created, or they
# are orphaned and keep billing under a name nothing left in the config mentions.
PROVISIONABLE_TIERS: tuple[int, ...] = (0, 1, 2, 3, 4)

# The tiers the ladder *adds*. Tiers 0 and 1 are excluded because they are the
# published ones: anything that treats them as unmeasured neighbours rather than
# as measurements is a guess wearing a measurement's clothes. `estimate.rate_for`
# is the case that bit — pricing an unmeasured tier 0 off tier 1 would have read
# 6x low, since tier 0 is the *expensive* condition (more turns spent hunting for
# context that is not there).
LADDER_RUNGS: tuple[int, ...] = (2, 3, 4)

# -----------------------------------------------------------------------------
# The governance ladder — which increment of governance actually pays.
#
# Governance is not one switch. It arrives through six channels a real team
# installs separately and in some order, and tier 1 is all of them at once, which
# is why the published result can say governance doubles accuracy but not which
# part of it did.
#
# **The tier integers are deliberately not the rung positions.**
# `traces.cell_key` embeds the tier, and 1,440 published cells are keyed on
# `tier0` / `tier1`. Renumbering so the rungs read 0..4 in order would make every
# published key unreadable to new code, and a second file in which `tier1` means
# something else would be worse still. So the new rungs are *appended* as 2, 3, 4
# and never reordered; `RUNG_ORDER` states the reading order once, here, and
# everything that renders a ladder sorts by it rather than by the integer.
#
# The cost is that the tier integer stops reading as monotone governance. That is
# a documentation problem, and the alternative was a correctness problem.
# -----------------------------------------------------------------------------
CHANNELS = ("descriptions", "profiles", "rules", "glossary", "quality", "lookml")

# Ladder position -> tier integer. Rung 0 is today's tier 0, rung 4 today's tier 1.
RUNG_ORDER: tuple[int, ...] = (0, 2, 3, 4, 1)

# Cumulative: each rung carries everything below it, because that is how
# governance is actually adopted and a non-cumulative rung would measure a
# configuration nobody runs.
RUNG_CHANNELS: dict[int, tuple[str, ...]] = {
    0: (),
    2: ("descriptions",),
    3: ("descriptions", "profiles"),
    4: ("descriptions", "profiles", "rules"),
    1: CHANNELS,
}

# What each tier actually carries. Written as the *increment* over the rung
# below, because that is the thing the ladder measures and the thing an operator
# needs to recognise when a `make setup` summary scrolls past.
TIER_LABELS = {
    0: "ungoverned control",
    2: "+ column descriptions",
    3: "+ profile scans",
    4: "+ business rules",
    1: "+ glossary, quality scans, LookML — the published governed tier",
}


def tier_label(tier: int) -> str:
    """A tier for human eyes, carrying its rung position only when there is one.

    With the ladder off there are two tiers and no ladder to be a position in, so
    printing `rung 4` at someone who never enabled it is noise about a feature
    they are not using. With it on the rung is the *only* useful ordering, since
    the integers are not monotone.
    """
    if LADDER:
        return f"rung {rung_of(tier)} (tier {tier}) · {TIER_LABELS[tier]}"
    return f"{tier} · {TIER_LABELS[tier]}"


def tiers_with(channel: str) -> tuple[int, ...]:
    """Every provisioned tier carrying a governance channel, in tier order.

    The provisioning modules ask this instead of testing `tier >= 1`, which was
    true when governance was one switch and quietly wrong the moment it became
    five. With the ladder off this returns `(1,)` for every channel — exactly the
    old behaviour — so the published tiers keep their published meaning.

    An unknown channel raises rather than returning empty. A typo that provisions
    nothing does not fail; it produces a rung that scores like the rung below it
    and reads as *"this increment of governance does not pay"*, which is a false
    finding rather than a broken run.
    """
    if channel not in CHANNELS:
        raise ValueError(f"Unknown governance channel {channel!r}; expected one of {CHANNELS}")
    return tuple(tier for tier in TIERS if channel in RUNG_CHANNELS[tier])


def rung_of(tier: int) -> int:
    """Ladder position of a tier — what to sort and plot by, never the integer."""
    return RUNG_ORDER.index(tier)


def tier_semantics() -> str:
    """The tier vocabulary this capture uses, recorded in its header.

    Two captures can both hold `tier1` and mean the same thing while one of them
    also holds a `tier3` that the other has never heard of. A file that declares
    its vocabulary can be read without inferring it from which integers happen to
    be present — and `MUST_AGREE` can then refuse to difference two files that
    number their tiers differently, which is the failure this naming scheme was
    chosen to avoid and would otherwise reintroduce at comparison time.

    The two-tier case returns `""`, not `"tiers-v1"`. Every capture taken before
    this field existed has no value for it and reads as unset, and `compare`
    collapses unset with empty — so an empty string keeps the published capture
    comparable to a two-tier sweep taken today, which is the single most likely
    comparison anyone will run. A `"tiers-v1"` string would have made the guard
    fire on the replication it exists to permit.
    """
    return "ladder-v1" if LADDER else ""


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
# fence verified 24/24 by `make verify-isolation`.
USE_TIER_SA = os.getenv("USE_TIER_SA", "false").lower() in ("1", "true", "yes")


def tier_service_account(tier: int) -> str:
    """Email of the service account that runs the agents for one tier."""
    return f"{TIER_SA_PREFIX}-t{tier}@{require_project()}.iam.gserviceaccount.com"


# Looker is not laddered, whatever `TIERS` says. LookML arrives as one lump at
# rung 4, and splitting it into rungs means semantic-model surgery on a shared
# instance this project is a guest on — out of scope by the standing rule against
# touching content that is not ours (Amendment C.2 excludes `p2_*` and
# `p4_looker_ca` for exactly this reason).
LOOKER_TIERS: tuple[int, ...] = (0, 1)


def _require_looker_tier(tier: int) -> None:
    """Refuse to name a Looker object for a tier that has none.

    Both lookups below were `T0 if tier == 0 else T1`, which answers *every*
    other integer with the tier-1 semantic model. Under the ladder that is a
    silent wrong answer, not an error: rung 2 would be pointed at the fully
    governed LookML and score like rung 4, and the ladder would report that
    profile scans deliver the whole benefit of the semantic layer.
    """
    if tier not in LOOKER_TIERS:
        raise ValueError(
            f"Tier {tier} has no Looker model. Looker runs at tiers {LOOKER_TIERS} only "
            f"— the ladder's intermediate rungs exclude the Path 2 and Looker CA arms."
        )


def looker_model(tier: int) -> str:
    """LookML model name for a tier (t0 = raw passthrough, t1 = semantic)."""
    _require_looker_tier(tier)
    return LOOKER_MODEL_T0 if tier == 0 else LOOKER_MODEL_T1


def looker_connection(tier: int) -> str:
    """Looker BigQuery connection name for a tier. Impersonates `tier_service_account`."""
    _require_looker_tier(tier)
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


def quality_scan_id(tier: int, table: str) -> str:
    """DataScan id for a table's data-quality scan at a given tier."""
    return bounded_id(f"{RESOURCE_PREFIX}-t{tier}-quality-{table}")


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
