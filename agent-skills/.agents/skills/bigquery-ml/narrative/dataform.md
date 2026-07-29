# Dataform — BigQuery ML Pipeline

Version-controlled SQL pipeline: `CREATE MODEL` as an `operations`-type `.sqlx` file, `ML.EVALUATE` as an **assertion** that halts a dependent downstream action when it fails. One of Google's own three officially-documented BQML pipeline paths (alongside plain SQL scripting and Vertex AI Pipelines) — and the engine behind BigQuery Studio's newer native "Pipelines" UI feature.

**Workflow operationalized:** `workflows/ga4_churn_prediction` (`workflows/ga4_churn_prediction/`)
**API:** `google.cloud.dataform_v1` (`Repository`, `Workspace`, `CompilationResult`, `WorkflowInvocation`)

**Data:** [`bigquery-public-data.ga4_obfuscated_sample_ecommerce`](https://console.cloud.google.com/marketplace/product/bigquery-public-datasets)

**References:** `RESOURCES.md` (Full reference) | [Dataform overview](https://cloud.google.com/dataform/docs/overview) | [Assertions](https://cloud.google.com/dataform/docs/assertions) | `setup` (Setup guide)

---
## Setup

Set your project and location, authenticate, and create a shared dataset. No BigQuery connection needed (Dataform needs its own one-time API/IAM setup — Step 0 below).

```python
PROJECT_ID = 'statmike-mlops-349915'  # <-- Replace with your project ID
LOCATION = 'US'  # BigQuery dataset location
DATASET_ID = 'bq_ml'  # Shared dataset across all bq-ml notebooks
DATAFORM_LOCATION = 'us-central1'  # Dataform requires a specific region, not the 'US' multi-region
```

### Environment

> **Already set up the project environment?** The cell below is a no-op — packages are already in your kernel. See the `setup` (Setup Reference) for details.
>
> **Running standalone** (Colab, Colab Enterprise, Vertex AI Workbench)? The cell below installs required packages into your current kernel.

```python
from google.cloud import bigquery
import pandas as pd

client = bigquery.Client(project=PROJECT_ID)
pd.set_option('display.max_colwidth', None)

# Create the shared dataset (idempotent)
dataset_ref = bigquery.DatasetReference(PROJECT_ID, DATASET_ID)
dataset = bigquery.Dataset(dataset_ref)
dataset.location = LOCATION
client.create_dataset(dataset, exists_ok=True)
print(f'Dataset {PROJECT_ID}.{DATASET_ID} ready')

# Register %%bigquery cell magic (auto-loaded in Colab, needed elsewhere)
%load_ext bigquery_magics
```

---
## Step 0 — Enable the Dataform API and grant the IAM permission it needs

Dataform is a separate GCP API from BigQuery and needs its own one-time enablement, plus one IAM grant that isn't obvious from the docs. Both checks below are safe to re-run — they no-op if already satisfied.

**Verified live, not documented in the tutorials researched**: a workflow invocation needs an explicit runtime `service_account`, and — separately — that service account's own IAM policy must grant `roles/iam.serviceAccountTokenCreator` to Dataform's per-project service agent (`service-PROJECT_NUMBER@gcp-sa-dataform.iam.gserviceaccount.com`). Without it, every action in the pipeline fails immediately with a permission-denied error before any BigQuery work starts. This cell checks for and grants that binding automatically; it requires `roles/iam.serviceAccountAdmin` (or equivalent) on the runtime service account — if your credentials lack that, the cell prints the exact `gcloud` command for a project admin to run instead.

```python
import subprocess

def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)

# 1. Enable the Dataform API (idempotent)
result = run(['gcloud', 'services', 'enable', 'dataform.googleapis.com', '--project', PROJECT_ID])
if result.returncode == 0:
    print('Dataform API enabled (or already was)')
else:
    print('Could not enable Dataform API automatically:')
    print(result.stderr)
    print(f"Run this yourself: gcloud services enable dataform.googleapis.com --project {PROJECT_ID}")

# 2. Determine the project number and the runtime service account
project_number = run(['gcloud', 'projects', 'describe', PROJECT_ID, '--format=value(projectNumber)']).stdout.strip()
runtime_service_account = f'{project_number}-compute@developer.gserviceaccount.com'
dataform_service_agent = f'serviceAccount:service-{project_number}@gcp-sa-dataform.iam.gserviceaccount.com'
print('Runtime service account:', runtime_service_account)
print('Dataform service agent:', dataform_service_agent)

# 3. Check whether the Dataform service agent already has Token Creator on
# the runtime service account
policy = run(['gcloud', 'iam', 'service-accounts', 'get-iam-policy', runtime_service_account,
              '--project', PROJECT_ID, '--format=json'])
has_binding = dataform_service_agent in policy.stdout and 'serviceAccountTokenCreator' in policy.stdout

if has_binding:
    print('IAM binding already in place: Dataform can impersonate the runtime service account.')
else:
    print('Granting roles/iam.serviceAccountTokenCreator to the Dataform service agent...')
    grant = run(['gcloud', 'iam', 'service-accounts', 'add-iam-policy-binding', runtime_service_account,
                 f'--member={dataform_service_agent}',
                 '--role=roles/iam.serviceAccountTokenCreator',
                 '--project', PROJECT_ID])
    if grant.returncode == 0:
        print('Granted. IAM changes can take ~1-2 minutes to propagate — the workflow invocation')
        print('step below retries automatically if it hits that window.')
    else:
        print('Could not grant automatically (likely missing roles/iam.serviceAccountAdmin). Ask a project admin to run:')
        print(f'  gcloud iam service-accounts add-iam-policy-binding {runtime_service_account} \\')
        print(f'    --member="{dataform_service_agent}" \\')
        print(f'    --role="roles/iam.serviceAccountTokenCreator" --project {PROJECT_ID}')
```

---
## Step 1 — Create a Dataform repository and workspace

A **repository** is Dataform's top-level container (like a Git repo). A **workspace** is a working directory within it, used here without ever committing to Dataform's own git history — fine for this self-contained demo, since everything gets deleted in cleanup anyway.

**Verified live gotcha**: a workspace cannot be named the same as the repository's default branch (`main`) — `FAILED_PRECONDITION: Workspace name must not be the same as the remote default branch name`. Any other name works.

```python
from google.cloud import dataform_v1

dataform_client = dataform_v1.DataformClient()
dataform_parent = dataform_client.common_location_path(PROJECT_ID, DATAFORM_LOCATION)

repository = dataform_client.create_repository(
    parent=dataform_parent,
    repository_id='bq-ml-ga4-churn-pipeline',
    repository=dataform_v1.Repository(),
)
print('Repository:', repository.name)

workspace = dataform_client.create_workspace(
    parent=repository.name,
    workspace_id='dev',  # not "main" -- see gotcha above
    workspace=dataform_v1.Workspace(),
)
print('Workspace:', workspace.name)
```

---
## Step 2 — Write the project config and `.sqlx` action files

`workflow_settings.yaml` is the modern project config (verified live: the legacy `dataform.json` alone fails with `Can't find package.json` — `workflow_settings.yaml` needs no separate `package.json`).

Five actions, in dependency order:
1. **`ga4_churn_pipeline_features`** (`type: "table"`) — same cohort/feature/label engineering as `workflows/ga4_churn_prediction/`. Dataform wraps the `SELECT` body in `CREATE OR REPLACE TABLE ${self()} AS (...)` automatically.
2. **`ga4_churn_pipeline_model`** (`type: "operations", hasOutput: true`) — `CREATE OR REPLACE MODEL ${self()} ... FROM ${ref("ga4_churn_pipeline_features")}`. `hasOutput: true` + `${self()}` declares this operation's output (the model) as referenceable by other actions; `${ref(...)}` is what builds the real dependency graph.
3. **`ga4_churn_pipeline_quality_reasonable`** (`type: "assertion"`) — `SELECT * FROM ML.EVALUATE(MODEL ${ref("ga4_churn_pipeline_model")}) WHERE roc_auc < 0.6`. Dataform assertions are just `SELECT` queries — returning *any* rows means the assertion failed. A 0.6 bar should pass comfortably.
4. **`ga4_churn_pipeline_quality_strict`** (`type: "assertion"`) — the same query with an unrealistic `WHERE roc_auc < 0.99` bar, deliberately designed to fail live (no model here gets near 0.99) so this notebook demonstrates a genuine assertion failure, not a hypothetical one.
5. **`ga4_churn_pipeline_scoring`** (`type: "table", dependOnDependencyAssertions: true`) — batch `ML.PREDICT` output. `dependOnDependencyAssertions: true` makes this action *also* depend on every assertion of its direct dependencies (both quality checks above) — this is what actually halts a downstream action on a failed quality gate, not just leaving a bad evaluation number sitting unread in a table somewhere.

```python
workflow_settings = f"""defaultProject: {PROJECT_ID}
defaultDataset: {DATASET_ID}
defaultLocation: {LOCATION}
defaultAssertionDataset: {DATASET_ID}_assertions
dataformCoreVersion: 3.0.0
"""

features_sqlx = """config { type: "table" }

WITH events AS (
  SELECT
    user_pseudo_id,
    PARSE_DATE('%Y%m%d', event_date) AS event_date,
    event_name,
    device.category AS device_category,
    geo.country AS country,
    traffic_source.medium AS traffic_medium,
    (SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'engagement_time_msec') AS engagement_time_msec
  FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
),
first_visit AS (
  SELECT user_pseudo_id, MIN(event_date) AS first_date
  FROM events
  GROUP BY user_pseudo_id
  HAVING first_date BETWEEN '2020-11-01' AND '2020-12-24'
),
feature_window AS (
  SELECT e.*, f.first_date
  FROM events e
  JOIN first_visit f USING (user_pseudo_id)
  WHERE e.event_date BETWEEN f.first_date AND DATE_ADD(f.first_date, INTERVAL 6 DAY)
),
label_window AS (
  SELECT DISTINCT e.user_pseudo_id
  FROM events e
  JOIN first_visit f USING (user_pseudo_id)
  WHERE e.event_date BETWEEN DATE_ADD(f.first_date, INTERVAL 7 DAY) AND DATE_ADD(f.first_date, INTERVAL 36 DAY)
)
SELECT
  fw.user_pseudo_id,
  ANY_VALUE(fw.first_date) AS first_date,
  ANY_VALUE(fw.device_category) AS device_category,
  ANY_VALUE(fw.country) AS country,
  ANY_VALUE(fw.traffic_medium) AS traffic_medium,
  COUNT(*) AS n_events,
  COUNT(DISTINCT fw.event_date) AS n_active_days,
  COUNTIF(fw.event_name = 'page_view') AS n_page_view,
  COUNTIF(fw.event_name = 'view_item') AS n_view_item,
  COUNTIF(fw.event_name = 'add_to_cart') AS n_add_to_cart,
  COUNTIF(fw.event_name = 'begin_checkout') AS n_begin_checkout,
  COUNTIF(fw.event_name = 'session_start') AS n_sessions,
  COUNTIF(fw.event_name = 'purchase') > 0 AS did_purchase,
  IFNULL(SUM(fw.engagement_time_msec), 0) AS total_engagement_time_msec,
  lw.user_pseudo_id IS NULL AS churned
FROM feature_window fw
LEFT JOIN label_window lw USING (user_pseudo_id)
GROUP BY fw.user_pseudo_id, lw.user_pseudo_id
"""

model_sqlx = """config { type: "operations", hasOutput: true }

CREATE OR REPLACE MODEL ${self()}
OPTIONS(
  model_type = 'BOOSTED_TREE_CLASSIFIER',
  input_label_cols = ['churned'],
  auto_class_weights = TRUE,
  data_split_method = 'AUTO_SPLIT',
  enable_global_explain = TRUE
) AS
SELECT n_events, n_active_days, n_page_view, n_view_item, n_add_to_cart,
       n_begin_checkout, n_sessions, did_purchase, device_category, country,
       traffic_medium, total_engagement_time_msec, churned
FROM ${ref("ga4_churn_pipeline_features")}
WHERE first_date <= '2020-11-20'
"""

quality_reasonable_sqlx = """config { type: "assertion" }

SELECT * FROM ML.EVALUATE(MODEL ${ref("ga4_churn_pipeline_model")})
WHERE roc_auc < 0.6
"""

quality_strict_sqlx = """config { type: "assertion" }

SELECT * FROM ML.EVALUATE(MODEL ${ref("ga4_churn_pipeline_model")})
WHERE roc_auc < 0.99
"""

scoring_sqlx = """config { type: "table", dependOnDependencyAssertions: true }

SELECT
  user_pseudo_id,
  predicted_churned,
  predicted_churned_probs
FROM ML.PREDICT(
  MODEL ${ref("ga4_churn_pipeline_model")},
  (SELECT * FROM ${ref("ga4_churn_pipeline_features")} WHERE first_date <= '2020-11-20' LIMIT 1000)
)
"""

dataform_files = {
    'workflow_settings.yaml': workflow_settings,
    'definitions/ga4_churn_pipeline_features.sqlx': features_sqlx,
    'definitions/ga4_churn_pipeline_model.sqlx': model_sqlx,
    'definitions/ga4_churn_pipeline_quality_reasonable.sqlx': quality_reasonable_sqlx,
    'definitions/ga4_churn_pipeline_quality_strict.sqlx': quality_strict_sqlx,
    'definitions/ga4_churn_pipeline_scoring.sqlx': scoring_sqlx,
}

for path, contents in dataform_files.items():
    dataform_client.write_file(
        request=dataform_v1.WriteFileRequest(
            workspace=workspace.name,
            path=path,
            contents=contents.encode('utf-8'),
        )
    )
print(f'Wrote {len(dataform_files)} files to the workspace')
```

---
## Step 3 — Compile

Compiling resolves every `${ref()}`/`${self()}` into real, fully-qualified BigQuery identifiers and builds the dependency graph — without running anything yet.

```python
compilation_result = dataform_client.create_compilation_result(
    parent=repository.name,
    compilation_result=dataform_v1.CompilationResult(workspace=workspace.name),
)
print('Compilation result:', compilation_result.name)
print('Compilation errors:', len(compilation_result.compilation_errors))
for err in compilation_result.compilation_errors:
    print(' -', err.path, ':', err.message)

actions = dataform_client.query_compilation_result_actions(
    request=dataform_v1.QueryCompilationResultActionsRequest(name=compilation_result.name)
)
print()
print('Resolved actions:')
for a in actions:
    kind = 'relation' if a.relation else ('operations' if a.operations else ('assertion' if a.assertion else '?'))
    print(f'  {a.target.name:45s} {kind}')
```

---
## Step 4 — Run the pipeline (a real workflow invocation)

This is the actual BQML work: create the table, train the model (~5 min), run both assertions, and attempt the scoring table. A retry with a short wait is built in for the IAM propagation window from Step 0.

**Expect the final state below to print `FAILED` — that's by design, not an error.** One of the two assertions defined in Step 2 (`quality_strict`) uses a deliberately unrealistic bar so this pipeline can demonstrate a real assertion failure and a real blocked downstream action, not just describe what *would* happen. The explanation and full per-action breakdown follow immediately after.

```python
import time
from google.api_core.exceptions import PermissionDenied

def start_invocation():
    return dataform_client.create_workflow_invocation(
        parent=repository.name,
        workflow_invocation=dataform_v1.WorkflowInvocation(
            compilation_result=compilation_result.name,
            invocation_config=dataform_v1.InvocationConfig(
                service_account=runtime_service_account,
            ),
        ),
    )

for attempt in range(3):
    try:
        invocation = start_invocation()
        break
    except PermissionDenied:
        print(f'Permission not yet propagated (attempt {attempt + 1}/3) — waiting 60s...')
        time.sleep(60)
else:
    invocation = start_invocation()

print('Invocation:', invocation.name)

while True:
    invocation = dataform_client.get_workflow_invocation(name=invocation.name)
    state = invocation.state.name
    if state in ('SUCCEEDED', 'FAILED', 'CANCELLED'):
        break
    time.sleep(15)

print('Final invocation state:', state)
```

**`FAILED` here is a deliberately engineered outcome, not a problem to fix.** This pipeline includes two quality-check assertions on purpose: `quality_reasonable` (`roc_auc` must be ≥ 0.6 — a realistic bar, and it passes) and `quality_strict` (`roc_auc` must be ≥ 0.99 — an unrealistic bar no model on this data could ever clear, included *specifically* to force a real assertion failure). Dataform marks the overall invocation `FAILED` whenever any single action in it fails, even when — as here — 4 of the 5 actions succeeded exactly as intended. In a real pipeline you would only include the realistic bar, and the whole run would show `SUCCEEDED`. What actually matters is the per-action breakdown next, and specifically that the one designed-to-fail assertion genuinely blocked the scoring table below it from ever running.

```python
action_results = dataform_client.query_workflow_invocation_actions(
    request=dataform_v1.QueryWorkflowInvocationActionsRequest(name=invocation.name)
)
for a in action_results:
    reason = f' — {a.failure_reason}' if a.failure_reason else ''
    print(f'{a.target.name:45s} {a.state.name}{reason}')
```

```python
query = f"SELECT roc_auc FROM ML.EVALUATE(MODEL `{PROJECT_ID}.{DATASET_ID}.ga4_churn_pipeline_model`)"
# useQueryCache=False: this exact query text has run against this exact model
# name in multiple earlier pipeline notebooks/test iterations, and BigQuery's
# query cache does not reliably invalidate when a MODEL is replaced via
# CREATE OR REPLACE MODEL (see pipelines/cloud_workflows/ and RESOURCES.md) --
# without this, the value below could silently be a stale result from a
# different model version, not the one this notebook just trained.
job_config = bigquery.QueryJobConfig(use_query_cache=False)
client.query(query, job_config=job_config).to_dataframe()
```

**This is the real, working "halt downstream work on a failed quality gate" behavior, not a hypothetical:**
- `ga4_churn_pipeline_features` → `SUCCEEDED`
- `ga4_churn_pipeline_model` → `SUCCEEDED` (`roc_auc` shown above — comfortably clears the 0.6 bar, nowhere near the deliberately-unrealistic 0.99 bar)
- `ga4_churn_pipeline_quality_reasonable` → `SUCCEEDED` (0.6 bar passes)
- `ga4_churn_pipeline_quality_strict` → `FAILED` (0.99 bar genuinely fails — `Assertion failed, expected zero rows`)
- `ga4_churn_pipeline_scoring` → `SKIPPED` — because `dependOnDependencyAssertions: true` made it depend on *both* quality assertions, and one failed. The scoring table is never created; querying for it returns "Not found."

Without `dependOnDependencyAssertions`, `scoring` would have run anyway — a failed `ML.EVALUATE` check sitting in a table nobody reads is very different from a pipeline that actually stops.

> **The `roc_auc` display query above sets `use_query_cache=False` for the same reason documented in `pipelines/cloud_workflows` (`pipelines/cloud_workflows/`) and `RESOURCES.md` (RESOURCES.md): this exact query text has run against this exact model name across several pipeline notebooks, and BigQuery's query cache does not reliably invalidate when the model is replaced via `CREATE OR REPLACE MODEL`.** An earlier version of this cell (without that setting) displayed a stale value from a previous test run — caught by comparing it against a direct `INFORMATION_SCHEMA.JOBS` check showing `cache_hit: true`, then confirming a fresh, uncached run of the identical query returned a genuinely different number. The pass/fail *assertion* results above were never affected — Dataform compiles each assertion into a multi-statement script (`CREATE VIEW` + `ASSERT`), and that class of query reliably re-evaluates fresh every time (the same immunity `pipelines/sql_scripting/`'s script has) — only this notebook's own added display query, a plain standalone `SELECT`, was exposed.

---
## Related content

- `pipelines/sql_scripting` (`pipelines/sql_scripting/`) — the plain-SQL alternative to this same drift/quality-gate idea, no version control or dependency graph.
- BigQuery Studio's newer native **"Pipelines" UI** (2026) is built on Dataform under the hood — this API-driven approach is the same engine, just without the console's drag-and-drop task sequencing.
- `workflows/ga4_churn_prediction` (`workflows/ga4_churn_prediction/`) — the workflow this pipeline operationalizes.
