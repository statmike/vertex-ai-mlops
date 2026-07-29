# Cloud Workflows — BigQuery ML Pipeline

The same drift-check → conditional-retrain → report logic as `pipelines/sql_scripting` (`pipelines/sql_scripting/`), re-expressed as **external declarative orchestration**: a YAML Workflow definition that submits one BigQuery job per step via the BigQuery connector, polls each to completion, and branches on the result. Control flow lives in Cloud Workflows now, not in BigQuery's own scripting language — a lightweight, serverless, near-free alternative to Airflow for simple linear/branching pipelines.

**Workflow operationalized:** `workflows/ga4_churn_prediction` (`workflows/ga4_churn_prediction/`)
**API:** Cloud Workflows (`google.cloud.workflows`, `google.cloud.workflows.executions`) · **Connector:** `googleapis.bigquery.v2.jobs.*`

**Data:** [`bigquery-public-data.ga4_obfuscated_sample_ecommerce`](https://console.cloud.google.com/marketplace/product/bigquery-public-datasets)

**References:** `RESOURCES.md` (Full reference) | [Cloud Workflows overview](https://cloud.google.com/workflows/docs/overview) | [BigQuery connector](https://cloud.google.com/workflows/docs/reference/googleapis/bigquery/Overview) | `setup` (Setup guide)

---
## Setup

Set your project and location, authenticate, and create a shared dataset. No BigQuery connection needed.

```python
PROJECT_ID = 'statmike-mlops-349915'  # <-- Replace with your project ID
LOCATION = 'US'  # BigQuery dataset location
DATASET_ID = 'bq_ml'  # Shared dataset across all bq-ml notebooks
WORKFLOWS_LOCATION = 'us-central1'  # Cloud Workflows requires a specific region, not the 'US' multi-region
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
## Step 0 — Enable the Cloud Workflows API

The Workflows service account (the project's default Compute Engine service account, unless overridden at deploy time) already has the BigQuery permissions it needs from earlier setup in this project — no new IAM grant required here, just the API itself.

```python
import subprocess

def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)

result = run(['gcloud', 'services', 'enable', 'workflows.googleapis.com', '--project', PROJECT_ID])
if result.returncode == 0:
    print('Cloud Workflows API enabled (or already was)')
else:
    print('Could not enable the API automatically:')
    print(result.stderr)
    print(f"Run this yourself: gcloud services enable workflows.googleapis.com --project {PROJECT_ID}")
```

---
## Step 1 — Self-contained feature table + an initial "production" model

Identical setup to every other Phase 8 pipeline: its own copies of the GA4 churn feature table and initial model (trained on users whose first activity is on/before `2020-11-20`, pre-Black-Friday).

```python
query = """
CREATE OR REPLACE TABLE `{project}.{dataset}.ga4_churn_pipeline_features` AS
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
""".format(project=PROJECT_ID, dataset=DATASET_ID)
client.query(query).result()
print('Feature table ready')

query = """
CREATE OR REPLACE MODEL `{project}.{dataset}.ga4_churn_pipeline_model`
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
FROM `{project}.{dataset}.ga4_churn_pipeline_features`
WHERE first_date <= '2020-11-20'
""".format(project=PROJECT_ID, dataset=DATASET_ID)
client.query(query).result()
print('Model ga4_churn_pipeline_model created (trained on TRAIN_INITIAL only)')
```

---
## Step 2 — Write the Workflow YAML

Two design constraints shaped this YAML, both hit live before they were known:

1. **Workflows expressions cap at 400 characters.** A single `${"..." + var + "..."}` expression longer than that fails to deploy (`maximum length for an expression is 400 characters`). Both the drift-check query (two feature-column subqueries) and the `CREATE MODEL` statement exceed this inline — fixed by building query text across several small `assign` steps instead of one large expression.
2. **BigQuery's query result cache can silently serve a stale result after `CREATE OR REPLACE MODEL`** (see the callout after Step 4 — a major, previously-undocumented finding from building this exact pipeline). Every job this workflow submits sets `useQueryCache: false` for that reason.

The workflow has three routines: **`main`** (the pipeline logic), **`run_bq_query`** (submit a job, wait, fetch rows), and **`run_bq_job`** (submit a job via `jobs.insert`, poll `jobs.get` every 5 seconds until `state == "DONE"` — the standard pattern for BigQuery jobs that might run long, like model training, from Workflows).

```python
workflow_yaml = """
main:
  params: [args]
  steps:
    - init:
        assign:
          - project_id: ${args.project_id}
          - dataset_id: ${args.dataset_id}
          - cutoff_date: "2020-11-20"
          - features_table: ${"`" + project_id + "." + dataset_id + ".ga4_churn_pipeline_features`"}
          - model_ref: ${"`" + project_id + "." + dataset_id + ".ga4_churn_pipeline_model`"}
    - build_drift_query:
        assign:
          - cols: "n_events, n_active_days, n_page_view, n_view_item, n_add_to_cart, n_begin_checkout, n_sessions, did_purchase, device_category, country, traffic_medium, total_engagement_time_msec"
          - base_query: ${"(SELECT " + cols + " FROM " + features_table + " WHERE first_date <= '" + cutoff_date + "')"}
          - compare_query: ${"(SELECT " + cols + " FROM " + features_table + " WHERE first_date > '" + cutoff_date + "')"}
          - options_struct: "STRUCT(0.1 AS numerical_default_threshold, 0.1 AS categorical_default_threshold)"
          - drift_query_p1: ${"SELECT input, metric, ROUND(value, 4) AS value FROM ML.VALIDATE_DATA_DRIFT(" + base_query}
          - drift_query_p2: ${drift_query_p1 + ", " + compare_query}
          - drift_query: ${drift_query_p2 + ", " + options_struct + ") WHERE is_anomaly = TRUE ORDER BY value DESC"}
    - check_drift:
        call: run_bq_query
        args:
          project_id: ${project_id}
          query: ${drift_query}
        result: drift_rows
    - branch_on_drift:
        switch:
          - condition: ${len(drift_rows) > 0}
            steps:
              - get_prior_metric:
                  call: run_bq_query
                  args:
                    project_id: ${project_id}
                    query: ${"SELECT roc_auc FROM ML.EVALUATE(MODEL " + model_ref + ")"}
                  result: prior_metric_rows
              - build_retrain_query:
                  assign:
                    - retrain_options: "OPTIONS(model_type = 'BOOSTED_TREE_CLASSIFIER', input_label_cols = ['churned'], auto_class_weights = TRUE, data_split_method = 'AUTO_SPLIT', enable_global_explain = TRUE)"
                    - retrain_query_p1: ${"CREATE OR REPLACE MODEL " + model_ref + " " + retrain_options + " AS SELECT " + cols}
                    - retrain_query: ${retrain_query_p1 + ", churned FROM " + features_table}
              - retrain_model:
                  call: run_bq_job
                  args:
                    project_id: ${project_id}
                    query: ${retrain_query}
              - get_new_metric:
                  call: run_bq_query
                  args:
                    project_id: ${project_id}
                    query: ${"SELECT roc_auc FROM ML.EVALUATE(MODEL " + model_ref + ")"}
                  result: new_metric_rows
              - build_drift_report:
                  return:
                    status: "DRIFT_DETECTED_MODEL_RETRAINED"
                    drifted_features: ${drift_rows}
                    roc_auc_before_retrain: ${prior_metric_rows[0].f[0].v}
                    roc_auc_after_retrain: ${new_metric_rows[0].f[0].v}
        next: no_drift_report
    - no_drift_report:
        return:
          status: "NO_DRIFT_DETECTED_NO_RETRAIN"

run_bq_query:
  params: [project_id, query]
  steps:
    - submit_job:
        call: run_bq_job
        args:
          project_id: ${project_id}
          query: ${query}
        result: job_ref
    - fetch_results:
        call: googleapis.bigquery.v2.jobs.getQueryResults
        args:
          projectId: ${project_id}
          jobId: ${job_ref.jobId}
          location: ${job_ref.location}
        result: query_results
    - return_rows:
        return: ${default(map.get(query_results, "rows"), [])}

run_bq_job:
  params: [project_id, query]
  steps:
    - insert_job:
        call: googleapis.bigquery.v2.jobs.insert
        args:
          projectId: ${project_id}
          body:
            configuration:
              query:
                query: ${query}
                useLegacySql: false
                useQueryCache: false
        result: insert_result
    - init_poll:
        assign:
          - job_id: ${insert_result.jobReference.jobId}
          - job_location: ${insert_result.jobReference.location}
          - job_state: ${insert_result.status.state}
    - poll_loop:
        switch:
          - condition: ${job_state != "DONE"}
            steps:
              - wait:
                  call: sys.sleep
                  args:
                    seconds: 5
              - check_status:
                  call: googleapis.bigquery.v2.jobs.get
                  args:
                    projectId: ${project_id}
                    jobId: ${job_id}
                    location: ${job_location}
                  result: job_status
              - update_state:
                  assign:
                    - job_state: ${job_status.status.state}
              - loop_again:
                  next: poll_loop
    - return_job_ref:
        return:
          jobId: ${job_id}
          location: ${job_location}
"""
print(f'Workflow YAML ready ({len(workflow_yaml)} characters)')
```

---
## Step 3 — Deploy the workflow

A retry with a short wait is built in for the case where `workflows.googleapis.com` was *just* enabled in Step 0 — freshly-enabled APIs can take a short time to propagate, the same class of timing issue already seen with IAM grants in `pipelines/scheduled_queries/` and `pipelines/dataform/`.

```python
from google.cloud import workflows_v1
import time

workflows_client = workflows_v1.WorkflowsClient()
workflow_parent = workflows_client.common_location_path(PROJECT_ID, WORKFLOWS_LOCATION)
workflow_id = 'bq-ml-ga4-churn-pipeline'

def deploy_workflow():
    operation = workflows_client.create_workflow(
        request=workflows_v1.CreateWorkflowRequest(
            parent=workflow_parent,
            workflow=workflows_v1.Workflow(source_contents=workflow_yaml),
            workflow_id=workflow_id,
        )
    )
    return operation.result()

for attempt in range(3):
    try:
        workflow = deploy_workflow()
        break
    except Exception as e:
        if attempt == 2:
            raise
        print(f'Deploy failed (attempt {attempt + 1}/3), likely API propagation — waiting 30s: {e}')
        time.sleep(30)

print('Deployed workflow:', workflow.name)
```

---
## Step 4 — Execute the workflow

This triggers the actual BQML work: the drift check, then (since drift is real here — see `pipelines/sql_scripting/` for why) the retrain, polling each BigQuery job to completion from within the workflow itself.

```python
from google.cloud.workflows import executions_v1
import json

executions_client = executions_v1.ExecutionsClient()

execution = executions_client.create_execution(
    request=executions_v1.CreateExecutionRequest(
        parent=workflow.name,
        execution=executions_v1.Execution(
            argument=json.dumps({'project_id': PROJECT_ID, 'dataset_id': DATASET_ID})
        ),
    )
)
print('Execution:', execution.name)

while True:
    execution = executions_client.get_execution(name=execution.name)
    state = execution.state.name
    if state in ('SUCCEEDED', 'FAILED', 'CANCELLED'):
        break
    time.sleep(15)

print('Final execution state:', state)
result = json.loads(execution.result)
print(json.dumps(result, indent=2))
```

**Real, positive outcome, matching `pipelines/sql_scripting/`**: drift detected in 5 of 12 features (the same Black-Friday-driven population shift), triggering a retrain that improves `roc_auc`.

> ⚠️ **A major, previously-undocumented BQML gotcha was found building this pipeline, now in `RESOURCES.md` (RESOURCES.md).** The *first* live version of this workflow (before `useQueryCache: false` was added to `run_bq_job`) reported **identical** `roc_auc_before_retrain` and `roc_auc_after_retrain` values — not a coincidence. BigQuery's query result cache silently served a **stale** `ML.EVALUATE` result from *before* the retrain, even though `CREATE OR REPLACE MODEL` had genuinely changed the model in between. Confirmed directly with `bq query --nouse_cache`: the cached value was wrong. This is specific to issuing **separate top-level query jobs** before/after a retrain — exactly what any external orchestrator (Cloud Workflows, a monitoring script, a dashboard) does — and was *not* observed inside `pipelines/sql_scripting/`'s single multi-statement script, where the equivalent before/after checks reliably differed every time. **Fix: set `useQueryCache: false`** on any query that reads a model's state around a retrain step, in any pipeline built this way.

> `BOOSTED_TREE_CLASSIFIER` training carries a small amount of run-to-run variation — a rerun may show slightly different exact figures, but the direction (drift detected, retrain improves `roc_auc`) is the durable finding.

---
## Related content

- `pipelines/sql_scripting` (`pipelines/sql_scripting/`) — the same logic as one in-BigQuery multi-statement script, no external orchestrator.
- `pipelines/scheduled_queries` (`pipelines/scheduled_queries/`) — schedules that script via the BigQuery Data Transfer API.
- `pipelines/dataform` (`pipelines/dataform/`) — the same idea via a dependency graph instead of imperative step-by-step control flow.
- `workflows/ga4_churn_prediction` (`workflows/ga4_churn_prediction/`) — the workflow this pipeline operationalizes.
