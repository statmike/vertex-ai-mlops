#!/usr/bin/env bash
#
# One-time privileged bootstrap: create the per-tier service accounts that fence
# the experiment's arms apart.
#
# WHY THIS EXISTS AS A SHELL SCRIPT, AND NOT AS PYTHON
# ----------------------------------------------------
# Everything else the sandbox provisions is project-scoped and reversible, and
# lives in `scripts/setup.py`. This is neither: it creates identities and edits
# project-level IAM. That deserves to be a deliberate, readable, separately
# authorized step that an operator runs once and can audit line by line.
#
# WHAT IT BUYS
# ------------
# Knowledge Catalog search is project-wide and content-addressed — `search_entries`
# takes a query, not a scope — so a tier-0 agent asking for "revenue" was handed
# the tier-1 governed entry and answered from it. No MCP parameter can stop that.
# IAM can, because catalog search is ACL-filtered per caller against the source
# system: no `bigquery.tables.get` on a table, no entry in the results.
#
# NO KEYS ARE CREATED. The agents reach these identities by impersonation from
# your own ADC (CODE_STANDARDS §4). See `src/identity.py`, `docs/scoping.md`.
#
# Idempotent — safe to re-run. Reverse it with `scripts/teardown_identities.sh`.
#
# Usage:  bash scripts/bootstrap_identities.sh [PROJECT_ID]

set -euo pipefail

PROJECT="${1:-$(gcloud config get-value project 2>/dev/null)}"
OPERATOR="$(gcloud config get-value account 2>/dev/null)"
PREFIX="${TIER_SA_PREFIX:-mcp-sandbox}"
# The ladder's intermediate rungs need identities too, and the fence is only a
# fence if every tier has one. Set LADDER=1 to create all five (Amendment C.2).
if [[ "${LADDER:-false}" =~ ^(1|true|yes)$ ]]; then
  TIERS=(0 1 2 3 4)
else
  TIERS=(0 1)
fi

# Which tiers may read the glossary. This is a *channel*, not "everything above
# the control": the glossary is one of the six governance surfaces the ladder
# varies, and only its top rung carries it. `tier != 0` was the same statement
# while there were two tiers, and is wrong the moment there are five — rungs 1-3
# would read the governed rule in plain text and the glossary's contribution
# would measure as zero, credited to whatever rung came first.
#
# Must equal `config.tiers_with("glossary")`. This is a cross-LANGUAGE join by
# string, so nothing at runtime notices when they disagree;
# `tests/test_ladder.py` parses this line and compares.
GLOSSARY_TIERS=(1)

# Looker's Google-managed service agent, which fronts every impersonation chain
# from a Looker connection. Empty unless a Looker instance lives in this project,
# in which case Path 2 gets the same IAM fence as the other paths (see below).
PROJECT_NUMBER="$(gcloud projects describe "${1:-$(gcloud config get-value project 2>/dev/null)}" \
  --format='value(projectNumber)' 2>/dev/null || true)"
LOOKER_AGENT=""
if [[ -n "$PROJECT_NUMBER" ]] && \
   gcloud looker instances list --project "${1:-$(gcloud config get-value project)}" \
     --region "${LOOKER_REGION:-us-central1}" --format='value(name)' 2>/dev/null | grep -q .; then
  LOOKER_AGENT="service-${PROJECT_NUMBER}@gcp-sa-looker.iam.gserviceaccount.com"
fi

if [[ -z "$PROJECT" || -z "$OPERATOR" ]]; then
  echo "Need a project and an authenticated account. Run: gcloud auth login" >&2
  exit 1
fi

echo "Project:  $PROJECT"
echo "Operator: $OPERATOR"
echo

# --- Custom roles -------------------------------------------------------------
#
# The obvious grant is roles/dataplex.catalogViewer, and it is WRONG here: it
# bundles dataplex.glossaryTerms.get/list, and the Net Revenue glossary term
# contains the governed rule in plain text. A glossary is a Dataplex resource
# with no BigQuery table behind it, so dataset ACLs do not filter it — a tier-0
# agent holding catalogViewer finds the rule by searching "revenue" and the
# control arm is contaminated again, this time past a perfect dataset fence.
# Measured, tier 0 baseline, DEV_NOTES 2026-08-29.
#
# So catalogViewer is split in two: the search half goes to both tiers, the
# glossary half only to the governed one.
SEARCH_ROLE="mcpSandboxCatalogSearch"
SEARCH_PERMS="dataplex.projects.search,dataplex.entries.get,dataplex.entries.list,\
dataplex.entryGroups.get,dataplex.entryGroups.list,dataplex.entryTypes.get,\
dataplex.entryTypes.list,dataplex.aspectTypes.get,dataplex.aspectTypes.list,\
dataplex.entryLinks.get,dataplex.locations.get,dataplex.locations.list,\
resourcemanager.projects.get"

GLOSSARY_ROLE="mcpSandboxGlossaryReader"
GLOSSARY_PERMS="dataplex.glossaries.get,dataplex.glossaries.list,\
dataplex.glossaryTerms.get,dataplex.glossaryTerms.list,\
dataplex.glossaryCategories.get,dataplex.glossaryCategories.list"

upsert_role() {
  local ID="$1" TITLE="$2" PERMS="$3"
  if gcloud iam roles describe "$ID" --project "$PROJECT" &>/dev/null; then
    gcloud iam roles update "$ID" --project "$PROJECT" \
      --permissions="$PERMS" --quiet >/dev/null
    echo "role ${ID}: updated"
  else
    gcloud iam roles create "$ID" --project "$PROJECT" \
      --title="$TITLE" --permissions="$PERMS" --stage=GA --quiet >/dev/null
    echo "role ${ID}: created"
  fi
}

upsert_role "$SEARCH_ROLE" "MCP Sandbox Catalog Search" "$SEARCH_PERMS"
upsert_role "$GLOSSARY_ROLE" "MCP Sandbox Glossary Reader" "$GLOSSARY_PERMS"
echo

# Project-level roles for every tier. Deliberately thin: run a query, issue a
# catalog search. No data access at all — that is granted per-dataset by
# `make setup`, and that grant is what separates the tiers.
PROJECT_ROLES=(
  roles/mcp.toolUser                                # call ANY googleapis.com/mcp tool at all
  roles/bigquery.jobUser                            # run query jobs, not read data
  roles/serviceusage.serviceUsageConsumer           # the x-goog-user-project quota header
  roles/geminidataanalytics.dataAgentStatelessUser  # Path 4: ask_data_insights
  "projects/${PROJECT}/roles/${SEARCH_ROLE}"        # search, results still ACL-filtered
)

for TIER in "${TIERS[@]}"; do
  SA="${PREFIX}-t${TIER}@${PROJECT}.iam.gserviceaccount.com"
  echo "=== tier ${TIER} :: ${SA} ==="

  if gcloud iam service-accounts describe "$SA" --project "$PROJECT" &>/dev/null; then
    echo "  exists"
  else
    gcloud iam service-accounts create "${PREFIX}-t${TIER}" \
      --project "$PROJECT" \
      --display-name "Data MCP Sandbox tier ${TIER}" \
      --description "Tier-${TIER} experiment identity. Dataset-scoped, keyless (impersonation only)."
    echo "  created"
  fi

  ROLES=("${PROJECT_ROLES[@]}")
  # The glossary carries the governed rule in plain text, so reading it IS the
  # treatment for that channel. Only the tiers carrying it may.
  CARRIES_GLOSSARY=""
  for GTIER in "${GLOSSARY_TIERS[@]}"; do
    if [[ "$TIER" == "$GTIER" ]]; then
      CARRIES_GLOSSARY="yes"
      break
    fi
  done

  if [[ -n "$CARRIES_GLOSSARY" ]]; then
    ROLES+=("projects/${PROJECT}/roles/${GLOSSARY_ROLE}")
  else
    # Revoke, do not merely skip. This script converges upward by adding roles,
    # which is enough while the answer only ever grows — and wrong here. A tier
    # granted the glossary under an earlier configuration keeps it forever, and
    # a rung silently reading the governed rule flattens the step that rule is
    # supposed to explain. Same reasoning as `setup.py` stripping descriptions
    # from tiers that should not carry them, rather than only applying them.
    # `remove-iam-policy-binding` errors when the binding is absent, which is
    # the normal case, so a failure here is not news.
    if gcloud projects remove-iam-policy-binding "$PROJECT" \
        --member="serviceAccount:${SA}" \
        --role="projects/${PROJECT}/roles/${GLOSSARY_ROLE}" \
        --condition=None --quiet &>/dev/null; then
      echo "  - ${GLOSSARY_ROLE} (revoked: this tier does not carry the glossary)"
    fi
  fi

  for ROLE in "${ROLES[@]}"; do
    gcloud projects add-iam-policy-binding "$PROJECT" \
      --member="serviceAccount:${SA}" --role="$ROLE" \
      --condition=None --quiet >/dev/null
    echo "  + ${ROLE}"
  done

  # Let the operator's own ADC mint tokens for this identity. This is the line
  # that keeps the whole scheme keyless.
  gcloud iam service-accounts add-iam-policy-binding "$SA" \
    --project "$PROJECT" \
    --member="user:${OPERATOR}" \
    --role=roles/iam.serviceAccountTokenCreator \
    --quiet >/dev/null
  echo "  + tokenCreator for ${OPERATOR}"

  # ...and let Looker do the same, so Path 2 is fenced by IAM like every other
  # path instead of by LookML alone. A Looker BigQuery connection authenticates
  # as the CONNECTION, not the calling user, so one connection per tier — each
  # ADC + "Impersonated Service Account" = this SA — is what makes a cross-tier
  # read a 403. Still keyless: no JSON key is uploaded to Looker.
  #
  # Scope note: this lets ANY connection on the Looker instance impersonate these
  # identities, not just ours. On a shared instance that is a real widening, and
  # it is bounded rather than nil: table data is dataset-scoped to the sandbox's
  # own tiers, but catalog *metadata* reads are project-wide, because the Dataplex
  # list permissions in mcpSandboxCatalogSearch take no dataset scope. No writes.
  # `make verify-isolation` checks both identities against a reviewed allow-list,
  # so this bound is tested rather than asserted. Enumerated in
  # docs/looker_setup.md.
  if [[ -n "$LOOKER_AGENT" ]]; then
    gcloud iam service-accounts add-iam-policy-binding "$SA" \
      --project "$PROJECT" \
      --member="serviceAccount:${LOOKER_AGENT}" \
      --role=roles/iam.serviceAccountTokenCreator \
      --quiet >/dev/null
    echo "  + tokenCreator for Looker (${LOOKER_AGENT})"
  fi
  echo
done

cat <<EOF
Done. Next:

  1. Turn the identities on:   echo 'USE_TIER_SA=true' >> .env
  2. Grant dataset access:     make setup
  3. Prove the fence holds:    make verify-isolation

IAM changes take a minute or two to propagate, and the catalog search index
lags further behind that. If step 3 fails on the first try, wait and re-run.
EOF
