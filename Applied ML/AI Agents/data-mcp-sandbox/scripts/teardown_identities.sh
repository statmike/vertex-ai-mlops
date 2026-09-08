#!/usr/bin/env bash
#
# Reverse `bootstrap_identities.sh`.
#
# Kept separate from `scripts/cleanup.py` for the same reason the bootstrap is
# separate from `setup.py`: this touches project-level IAM, and deleting an
# identity is not the same kind of act as dropping a dataset. Run it
# deliberately.
#
# Bindings are removed *before* the account, so the project policy is not left
# holding `deleted:serviceAccount:...` tombstones.
#
# Usage:  bash scripts/teardown_identities.sh [PROJECT_ID]

set -euo pipefail

PROJECT="${1:-$(gcloud config get-value project 2>/dev/null)}"
PREFIX="${TIER_SA_PREFIX:-mcp-sandbox}"
# Every tier this project can ever create, not just the ones the current config
# would create. Teardown that skips the ladder rungs leaves service accounts
# behind holding dataViewer on datasets nobody is looking at any more.
TIERS=(0 1 2 3 4)

SEARCH_ROLE="mcpSandboxCatalogSearch"
GLOSSARY_ROLE="mcpSandboxGlossaryReader"

PROJECT_ROLES=(
  roles/mcp.toolUser
  roles/bigquery.jobUser
  roles/serviceusage.serviceUsageConsumer
  roles/geminidataanalytics.dataAgentStatelessUser
  "projects/${PROJECT}/roles/${SEARCH_ROLE}"
  "projects/${PROJECT}/roles/${GLOSSARY_ROLE}"
)

for TIER in "${TIERS[@]}"; do
  SA="${PREFIX}-t${TIER}@${PROJECT}.iam.gserviceaccount.com"
  if ! gcloud iam service-accounts describe "$SA" --project "$PROJECT" &>/dev/null; then
    echo "tier ${TIER}: ${SA} not present, skipping"
    continue
  fi
  echo "=== tier ${TIER} :: ${SA} ==="
  for ROLE in "${PROJECT_ROLES[@]}"; do
    gcloud projects remove-iam-policy-binding "$PROJECT" \
      --member="serviceAccount:${SA}" --role="$ROLE" \
      --condition=None --quiet >/dev/null 2>&1 || true
    echo "  - ${ROLE}"
  done
  gcloud iam service-accounts delete "$SA" --project "$PROJECT" --quiet
  echo "  deleted"
done

# Custom roles go last: they cannot be dropped while a binding still names them,
# and `delete` soft-deletes for 7 days, so a re-run of the bootstrap inside that
# window undeletes rather than recreates.
for ROLE in "$SEARCH_ROLE" "$GLOSSARY_ROLE"; do
  if gcloud iam roles describe "$ROLE" --project "$PROJECT" &>/dev/null; then
    gcloud iam roles delete "$ROLE" --project "$PROJECT" --quiet >/dev/null
    echo "role ${ROLE}: deleted (recoverable for 7 days)"
  fi
done

echo
echo "Dataset ACL entries pointing at these accounts are dropped by 'make teardown',"
echo "or become inert tombstones if the datasets outlive the identities."
