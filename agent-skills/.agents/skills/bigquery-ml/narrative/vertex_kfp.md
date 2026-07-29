# Vertex AI Pipelines (KFP) — BigQuery ML Pipeline

Train → evaluate → quality-gate → conditionally score, built from the **official prebuilt `google_cloud_pipeline_components.v1.bigquery` ops** (`BigqueryCreateModelJobOp`, `BigqueryEvaluateModelJobOp`, `BigqueryPredictModelJobOp`) instead of hand-rolled BigQuery client calls inside custom components. These prebuilt ops auto-track model lineage in Vertex ML Metadata and are the modern, Google-recommended way to wire BQML into a KFP pipeline — a real upgrade over this repo's own older custom-`@dsl.component` pattern (see Related content). One small custom component (`check_quality_gate`) fills the one gap the prebuilt ops don't cover: reading a metric back out and branching on it with `dsl.If`.

This notebook focuses narrowly on applying Vertex AI Pipelines to BQML. For the much deeper, general-purpose treatment of pipeline mechanics — components, parameters/artifacts, control flow, scheduling, notifications, testing, and managing pipelines/jobs — see `MLOps/Pipelines/readme.md` (`MLOps/Pipelines/`), a full notebook series this one builds on rather than repeats.

**Workflow operationalized:** `workflows/ga4_churn_prediction` (`workflows/ga4_churn_prediction/`)
**API:** Vertex AI Pipelines (`google.cloud.aiplatform`, `kfp`) · **Components:** `google_cloud_pipeline_components.v1.bigquery`

**Data:** [`bigquery-public-data.ga4_obfuscated_sample_ecommerce`](https://console.cloud.google.com/marketplace/product/bigquery-public-datasets)

**References:** `RESOURCES.md` (Full reference) | [Prebuilt BigQuery ML components](https://cloud.google.com/vertex-ai/docs/pipelines/bigqueryml-component) | [dsl.If control flow](https://www.kubeflow.org/docs/components/pipelines/user-guides/core-functions/control-flow/) | `setup` (Setup guide)

---
## Setup

Set your project and location, authenticate, and create a shared dataset.

```python
PROJECT_ID = 'statmike-mlops-349915'  # <-- Replace with your project ID
LOCATION = 'US'  # BigQuery dataset location
DATASET_ID = 'bq_ml'  # Shared dataset across all bq-ml notebooks
VERTEX_REGION = 'us-central1'  # Vertex AI Pipelines requires a specific region, not the 'US' multi-region
BUCKET = 'statmike-mlops-349915'  # GCS bucket for the pipeline_root (compiled specs + intermediate artifacts)
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
## Step 0 — Enable the Vertex AI API and confirm the pipeline runtime service account has what it needs

Vertex AI Pipelines runs each step as a managed job under the project's default Compute Engine service account (unless a different one is configured at submission time). That service account needs BigQuery execute permissions (to run `CREATE MODEL`/`ML.EVALUATE`/`ML.PREDICT`) and Cloud Storage permissions (to read/write the `pipeline_root` artifacts). Both checks below are safe to re-run — they no-op if already satisfied.

```python
import subprocess

def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)

# 1. Enable the Vertex AI API (idempotent)
result = run(['gcloud', 'services', 'enable', 'aiplatform.googleapis.com', '--project', PROJECT_ID])
if result.returncode == 0:
    print('Vertex AI API enabled (or already was)')
else:
    print('Could not enable the API automatically:')
    print(result.stderr)
    print(f"Run this yourself: gcloud services enable aiplatform.googleapis.com --project {PROJECT_ID}")

# 2. Determine the project number and the pipeline runtime service account
project_number = run(['gcloud', 'projects', 'describe', PROJECT_ID, '--format=value(projectNumber)']).stdout.strip()
runtime_service_account = f'{project_number}-compute@developer.gserviceaccount.com'
print('Pipeline runtime service account:', runtime_service_account)

# 3. Check whether that service account already has sufficient BigQuery + Storage access
policy = run(['gcloud', 'projects', 'get-iam-policy', PROJECT_ID,
              '--flatten=bindings[].members',
              f'--filter=bindings.members:serviceAccount:{runtime_service_account}',
              '--format=value(bindings.role)'])
current_roles = set(policy.stdout.split())

bq_sufficient_roles = {'roles/bigquery.admin', 'roles/bigquery.dataEditor', 'roles/editor', 'roles/owner'}
gcs_sufficient_roles = {'roles/storage.admin', 'roles/storage.objectAdmin', 'roles/editor', 'roles/owner'}

def grant(role):
    grant_result = run(['gcloud', 'projects', 'add-iam-policy-binding', PROJECT_ID,
                         f'--member=serviceAccount:{runtime_service_account}',
                         f'--role={role}', '--condition=None'])
    if grant_result.returncode == 0:
        print(f'Granted {role} to {runtime_service_account}')
    else:
        print(f'Could not grant {role} automatically (likely missing roles/resourcemanager.projectIamAdmin). Ask a project admin to run:')
        print(f'  gcloud projects add-iam-policy-binding {PROJECT_ID} \\')
        print(f'    --member="serviceAccount:{runtime_service_account}" --role="{role}"')

if current_roles & bq_sufficient_roles:
    print('BigQuery access already sufficient.')
else:
    print('No sufficient BigQuery role found — granting roles/bigquery.dataEditor and roles/bigquery.jobUser...')
    grant('roles/bigquery.dataEditor')
    grant('roles/bigquery.jobUser')

if current_roles & gcs_sufficient_roles:
    print('Cloud Storage access already sufficient.')
else:
    print('No sufficient Cloud Storage role found — granting roles/storage.objectAdmin...')
    grant('roles/storage.objectAdmin')
```

---
## Step 1 — Self-contained feature table

Identical feature engineering to every other Phase 8 pipeline. Unlike the drift-check pipelines (`sql_scripting`, `scheduled_queries`, `dataform`, `cloud_workflows`), this pipeline's `CREATE MODEL` step happens *inside* the KFP pipeline itself (via `BigqueryCreateModelJobOp`), so there's no separate "initial production model" to pre-create here — just the features.

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
```

---
## Step 2 — The one custom component this pipeline needs: `check_quality_gate`

The prebuilt ops cover `CREATE MODEL` / `ML.EVALUATE` / `ML.PREDICT`, but reading a metric back out and branching on it needs a small custom `@dsl.component` — exactly the pattern of "prebuilt ops first, custom component for the gap they don't cover." For the full range of ways to build a component (prebuilt, lightweight Python, containerized, container) and the full parameter/artifact type system, see `MLOps/Pipelines/Vertex%20AI%20Pipelines%20-%20Components.ipynb` (`Vertex AI Pipelines - Components`) and `MLOps/Pipelines/Vertex%20AI%20Pipelines%20-%20IO.ipynb` (`Vertex AI Pipelines - IO`).

**GOTCHA, verified live**: `BigqueryEvaluateModelJobOp`'s `evaluation_metrics` output is a `dsl.Artifact` whose `.metadata` is **not** a flat `{metric_name: value}` dict. It stores the raw BigQuery REST API tabular response — the same `schema`/`rows`, `f`/`v` cell shape as `jobs.getQueryResults` (and the Cloud Workflows connector's own result rows in `pipelines/cloud_workflows/`) — not a convenient mapping. A naive `evaluation_metrics.metadata.get('roc_auc')` returns `None` every time, since there's no top-level `roc_auc` key. First live run of this component: the gate silently evaluated to `False` even though the real `roc_auc` (0.728) comfortably cleared the 0.6 threshold — caught by dumping the raw `task.outputs` from a live `PipelineJob`'s `task_details`, not by trusting the artifact's shape. Fix: find `roc_auc`'s position in `metadata['schema']['fields']`, then read that position out of `metadata['rows'][0]['f']`.

```python
from kfp import dsl

@dsl.component(base_image='python:3.11')
def check_quality_gate(evaluation_metrics: dsl.Input[dsl.Artifact], threshold: float) -> bool:
    """Parse the roc_auc metric out of a BigqueryEvaluateModelJobOp artifact and compare to a threshold."""
    field_names = [f['name'] for f in evaluation_metrics.metadata['schema']['fields']]
    roc_auc_index = field_names.index('roc_auc')
    roc_auc = float(evaluation_metrics.metadata['rows'][0]['f'][roc_auc_index]['v'])
    print(f'Available metrics: {field_names}')
    print(f'roc_auc={roc_auc}, threshold={threshold}')
    passed = roc_auc >= threshold
    print('passed:', passed)
    return passed
```

---
## Step 3 — Define the pipeline

`BigqueryCreateModelJobOp` trains the model; its `model` output (a `google.BQMLModel` artifact) feeds directly into `BigqueryEvaluateModelJobOp` and `BigqueryPredictModelJobOp` — no manual model-name string-passing needed, and Vertex ML Metadata records the lineage automatically. `dsl.If` gates the scoring step on `check_quality_gate`'s output, mirroring the same "halt downstream work on a failed quality check" story already demonstrated with Dataform's `dependOnDependencyAssertions` and dbt's `dbt build`. `dsl.If` is one control-flow construct among several (ordering, `elif`/`else`, looping + parallelism, exit handlers, error handling) — see `MLOps/Pipelines/Vertex%20AI%20Pipelines%20-%20Control.ipynb` (`Vertex AI Pipelines - Control`) for the full survey.

**GOTCHA, verified live, MAJOR (now in `RESOURCES.md` (RESOURCES.md))**: `BigqueryEvaluateModelJobOp` re-runs the identical `SELECT * FROM ML.EVALUATE(MODEL ga4_churn_pipeline_model)` text every time this pipeline runs against a model that gets `CREATE OR REPLACE`'d each run — exactly the scenario that caused a silently-stale `roc_auc` in `pipelines/cloud_workflows/` and `pipelines/dataform/`. The component accepts a `job_configuration_query` override to set `useQueryCache: false`, but **passing the Python bool `False` is a no-op**: the library's own JSON-cleanup step (`recursive_remove_empty`) strips any dict value that's falsy under plain Python truthiness (`if v:`) before merging the override into the job body — so `False` never reaches the BigQuery API call, and caching silently stays on with no error. Confirmed via `INFORMATION_SCHEMA.JOBS_BY_PROJECT`: `job_configuration_query={'useQueryCache': False}` still showed `cache_hit: true`. The BigQuery REST API itself accepts the **string** `'false'` for this boolean field and genuinely disables caching — confirmed both via a direct REST call and inside a real pipeline run (`cache_hit: false`). **Fix: pass the string `'false'`, not the Python bool `False`.**

```python
from kfp import compiler
from google_cloud_pipeline_components.v1.bigquery import (
    BigqueryCreateModelJobOp,
    BigqueryEvaluateModelJobOp,
    BigqueryPredictModelJobOp,
)

@dsl.pipeline(name='ga4-churn-pipeline')
def ga4_churn_pipeline(
    project: str = PROJECT_ID,
    dataset: str = DATASET_ID,
    location: str = LOCATION,
    quality_threshold: float = 0.6,
):
    features_table = f"`{project}.{dataset}.ga4_churn_pipeline_features`"
    model_ref = f"`{project}.{dataset}.ga4_churn_pipeline_model`"

    create_model_query = f"""
    CREATE OR REPLACE MODEL {model_ref}
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
    FROM {features_table}
    WHERE first_date <= '2020-11-20'
    """

    create_model_task = BigqueryCreateModelJobOp(
        project=project,
        location=location,
        query=create_model_query,
    )

    evaluate_task = BigqueryEvaluateModelJobOp(
        project=project,
        location=location,
        model=create_model_task.outputs['model'],
        # STRING 'false', not the Python bool False -- see gotcha above.
        job_configuration_query={'useQueryCache': 'false'},
    )

    gate_task = check_quality_gate(
        evaluation_metrics=evaluate_task.outputs['evaluation_metrics'],
        threshold=quality_threshold,
    )

    with dsl.If(gate_task.output == True):
        predict_query = f"SELECT * FROM {features_table} WHERE first_date <= '2020-11-20' LIMIT 1000"
        BigqueryPredictModelJobOp(
            project=project,
            location=location,
            model=create_model_task.outputs['model'],
            table_name='',
            query_statement=predict_query,
        )

compiler.Compiler().compile(
    pipeline_func=ga4_churn_pipeline,
    package_path='ga4_churn_pipeline.json',
)
print('Compiled pipeline to ga4_churn_pipeline.json')
```

---
## Step 4 — Run the pipeline (default threshold — the gate passes)

Submits a real `PipelineJob`: trains a fresh `BOOSTED_TREE_CLASSIFIER` (~5 minutes), evaluates it, checks the quality gate, and — since `roc_auc` comfortably clears the default 0.6 threshold — scores the training population.

```python
from google.cloud import aiplatform
import time

aiplatform.init(project=PROJECT_ID, location=VERTEX_REGION)

pipeline_root = f'gs://{BUCKET}/bq_ml/vertex_kfp/pipeline_root'

job = aiplatform.PipelineJob(
    display_name='ga4-churn-pipeline-pass',
    template_path='ga4_churn_pipeline.json',
    pipeline_root=pipeline_root,
    parameter_values={'project': PROJECT_ID, 'dataset': DATASET_ID, 'location': LOCATION, 'quality_threshold': 0.6},
    enable_caching=False,
)
job.submit()
print('Submitted:', job.resource_name)

terminal_states = {'PIPELINE_STATE_SUCCEEDED', 'PIPELINE_STATE_FAILED', 'PIPELINE_STATE_CANCELLED', 'PIPELINE_STATE_PAUSED'}
while True:
    job._sync_gca_resource()
    state = job.state.name
    if state in terminal_states:
        break
    time.sleep(30)

print('Final pipeline state:', state)
for task in job.task_details:
    print(' ', task.task_name, '->', task.state.name)
```

**Real, live-verified outcome**: `bigquery-create-model-job` → `bigquery-evaluate-model-job` (`roc_auc≈0.728`, `cache_hit: false` — confirmed via `INFORMATION_SCHEMA.JOBS_BY_PROJECT`) → `check-quality-gate` returns `True` → `condition-1` **TRIGGERED** → `bigquery-predict-model-job` runs and succeeds. The scoring destination table is auto-created (since `table_name=''` with a `query_statement`) in a hidden, anonymous BigQuery dataset with BigQuery's own default temp-table expiration — nothing to clean up by hand.

> `BOOSTED_TREE_CLASSIFIER` training carries a small amount of run-to-run variation — a rerun may show a slightly different exact `roc_auc`, but the outcome (gate passes, scoring runs) is the durable finding at this threshold.

---
## Step 5 — Run the pipeline again with an unattainable threshold (the gate blocks scoring)

Same pipeline, same model, `quality_threshold=0.99` instead of `0.6` — proving `dsl.If` genuinely gates `BigqueryPredictModelJobOp`, not just reports a warning, the same "halt on a failed check" story already verified live in `pipelines/dataform/` (`dependOnDependencyAssertions`) and `pipelines/dbt/` (`dbt build`).

```python
job_strict = aiplatform.PipelineJob(
    display_name='ga4-churn-pipeline-strict-gate',
    template_path='ga4_churn_pipeline.json',
    pipeline_root=pipeline_root,
    parameter_values={'project': PROJECT_ID, 'dataset': DATASET_ID, 'location': LOCATION, 'quality_threshold': 0.99},
    enable_caching=False,
)
job_strict.submit()
print('Submitted:', job_strict.resource_name)

while True:
    job_strict._sync_gca_resource()
    state = job_strict.state.name
    if state in terminal_states:
        break
    time.sleep(30)

print('Final pipeline state:', state)
for task in job_strict.task_details:
    print(' ', task.task_name, '->', task.state.name)
```

**Verified live**: `check-quality-gate` returns `False` (the same `roc_auc≈0.728` genuinely can't clear 0.99), `condition-1` shows **`NOT_TRIGGERED`**, and `bigquery-predict-model-job` never even appears in the task list — it was never created, not just skipped-and-reported. The overall `PipelineJob` still reports `PIPELINE_STATE_SUCCEEDED`, since a not-triggered conditional branch is expected control flow, not a pipeline failure — the same "success at the pipeline level, honest reporting at the step level" pattern used throughout Phase 8 (compare `pipelines/dataform/`'s deliberately-`FAILED` workflow invocation).

---
## Related content

**This notebook's BQML/Phase 8 siblings:**
- `03%20-%20BigQuery%20ML%20%28BQML%29/03Tools%20-%20Pipelines%20Example%201.ipynb` (`03 - BigQuery ML (BQML)/03Tools - Pipelines Example 1.ipynb`) and `...Example 2.ipynb` — this repo's older, legacy pattern: a custom `@dsl.component` calling `google.cloud.bigquery.Client()` directly for every step, on the older `kfp.v2` API. Still the right fallback for BQML logic the prebuilt ops don't cover (which is exactly what `check_quality_gate` demonstrates above) — but prefer the prebuilt ops for anything they already do.
- `pipelines/dataform` (`pipelines/dataform/`) and `pipelines/dbt` (`pipelines/dbt/`) — the same "halt downstream work on a failed quality check" idea via a SQL dependency graph instead of imperative pipeline control flow.
- `pipelines/cloud_workflows` (`pipelines/cloud_workflows/`) — the same query-cache-after-retrain gotcha, hit independently in a completely different orchestrator.
- `workflows/ga4_churn_prediction` (`workflows/ga4_churn_prediction/`) — the workflow this pipeline operationalizes.

**The much deeper, general-purpose Vertex AI Pipelines series** — `MLOps/Pipelines/readme.md` (`MLOps/Pipelines/readme.md`) is the full map; this notebook only needed a slice of it. Most relevant follow-ups for what's used above:
- `MLOps/Pipelines/Vertex%20AI%20Pipelines%20-%20Start%20Here.ipynb` (`Vertex AI Pipelines - Start Here`) / `MLOps/Pipelines/Vertex%20AI%20Pipelines%20-%20Introduction.ipynb` (`- Introduction`) — if pipelines are new, start here rather than with this BQML-focused notebook.
- `MLOps/Pipelines/Vertex%20AI%20Pipelines%20-%20Components.ipynb` (`Vertex AI Pipelines - Components`) — the full range of component types (prebuilt, lightweight Python, containerized, container) beyond the one custom component and three prebuilt ops used here.
- `MLOps/Pipelines/Vertex%20AI%20Pipelines%20-%20IO.ipynb` (`Vertex AI Pipelines - IO`) — the full parameter/artifact type system and Vertex ML Metadata lineage, the same mechanism behind the `evaluation_metrics` artifact gotcha above.
- `MLOps/Pipelines/Vertex%20AI%20Pipelines%20-%20Control.ipynb` (`Vertex AI Pipelines - Control`) — every control-flow construct (ordering, `if`/`elif`/`else`, looping + parallelism, exit handlers, error handling), of which `dsl.If` is only one.
- `MLOps/Pipelines/Vertex%20AI%20Pipelines%20-%20Scheduling.ipynb` (`Vertex AI Pipelines - Scheduling`) — this notebook submits one-off runs; production use would likely schedule the retrain step instead (compare `pipelines/scheduled_queries/`'s BigQuery-native scheduling of the same idea).
- `MLOps/Pipelines/Vertex%20AI%20Pipelines%20-%20Notifications.ipynb` (`Vertex AI Pipelines - Notifications`) — alerting on pipeline completion/failure, the KFP-native counterpart to `scheduled_queries`'s `email_preferences.enable_failure_email`.
- `MLOps/Pipelines/Vertex%20AI%20Pipelines%20-%20Managing%20Pipeline%20Jobs.ipynb` (`Vertex AI Pipelines - Managing Pipeline Jobs`) — listing, filtering, cancelling, and deleting jobs across an environment, beyond this notebook's own polling of two specific runs.
