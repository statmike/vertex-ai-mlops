#!/usr/bin/env bash
#
# Enable the Google Cloud APIs this sandbox calls.
#
# WHY THIS EXISTS
# ---------------
# The project this was built in had every API on already, so nothing here was
# ever discovered the hard way — which is exactly the problem for anyone else.
# A missing API surfaces deep inside an MCP client as a 403 with a service name
# in it, an hour into a sweep. This list is derived from what the code actually
# calls, not from a snapshot of our project.
#
# Enabling an API costs nothing. Every one of these bills only on use, and the
# things that do cost money (BigQuery storage, Dataplex scans, Gemini calls) are
# created by `scripts/setup.py` and the sweep, not by this.
#
# Idempotent — `services enable` on an enabled service is a no-op.
#
# Usage:  bash scripts/enable_apis.sh [PROJECT_ID]

set -euo pipefail

PROJECT="${1:-$(gcloud config get-value project 2>/dev/null)}"

if [[ -z "$PROJECT" ]]; then
  echo "Need a project. Pass one, or run: gcloud config set project YOUR_PROJECT" >&2
  exit 1
fi

# Required for every path, including a Looker-free run.
SERVICES=(
  bigquery.googleapis.com                # corpus, queries, INFORMATION_SCHEMA, managed BQ MCP
  dataplex.googleapis.com                # Knowledge Catalog, profile scans, managed Dataplex MCP
  aiplatform.googleapis.com              # the Gemini calls every agent and the judge make
  geminidataanalytics.googleapis.com     # Conversational Analytics, i.e. all of Path 4
  iam.googleapis.com                     # creating the per-tier service accounts
  iamcredentials.googleapis.com          # impersonating them, keylessly — the tier fence itself
  cloudresourcemanager.googleapis.com    # project-level IAM bindings, project number lookup
  serviceusage.googleapis.com            # the x-goog-user-project quota header
)

# Only for Path 2 and p4_looker_ca, and only when the Looker instance is Looker
# (Google Cloud core) in this same project. `serviceconsumermanagement` is here
# because its absence breaks the Looker connection's impersonation chain with an
# error that names neither Looker nor impersonation — see docs/looker_runbook.md.
LOOKER_SERVICES=(
  looker.googleapis.com
  serviceconsumermanagement.googleapis.com
)

if [[ "${SKIP_LOOKER:-}" == "1" ]]; then
  echo "SKIP_LOOKER=1: enabling ${#SERVICES[@]} core APIs in $PROJECT"
else
  SERVICES+=("${LOOKER_SERVICES[@]}")
  echo "Enabling ${#SERVICES[@]} APIs in $PROJECT (SKIP_LOOKER=1 to drop the Looker ones)"
fi

for service in "${SERVICES[@]}"; do
  printf '  %-40s' "$service"
  if gcloud services enable "$service" --project "$PROJECT" 2>/dev/null; then
    echo "ok"
  else
    # Non-fatal on purpose. An org policy may pin a service on or off, and a
    # sandbox that refuses to provision because one optional API could not be
    # toggled is worse than one that says so and carries on.
    echo "COULD NOT ENABLE - check org policy or your permissions"
  fi
done

echo
echo "Done. Next: bash scripts/bootstrap_identities.sh $PROJECT"
