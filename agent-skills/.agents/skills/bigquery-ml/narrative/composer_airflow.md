# Cloud Composer / Airflow — BigQuery ML Pipeline

The same drift-check → conditional-retrain → report logic as `pipelines/sql_scripting` (`pipelines/sql_scripting/`), `pipelines/scheduled_queries` (`pipelines/scheduled_queries/`), and `pipelines/cloud_workflows` (`pipelines/cloud_workflows/`), re-expressed as a real **Apache Airflow DAG on a live Cloud Composer 3 environment** — `BigQueryInsertJobOperator` for every BigQuery job, `BranchPythonOperator` + XCom for the conditional retrain, and a join task with a non-default `trigger_rule` so the DAG completes cleanly regardless of which branch ran. This is the fourth re-expression of the identical narrative, now on the industry-standard open-source orchestrator behind most enterprise MLOps stacks.

> ⚠️ **Real, non-trivial cost and ~20-30 minute provisioning time.** This notebook creates an actual Cloud Composer 3 environment, billed in DCU-hours (~$0.06/DCU-hour in `us-central1`; a minimally-sized environment like this one runs roughly $0.30-0.55/hour). Shares one environment with `pipelines/airflow_with_kfp` (`pipelines/airflow_with_kfp/`) (build/run that one right after this, in the same session, before tearing down) — see Cleanup for exactly which notebook deletes it.

**Workflow operationalized:** `workflows/ga4_churn_prediction` (`workflows/ga4_churn_prediction/`)
**API:** Cloud Composer (`google.cloud.orchestration.airflow.service_v1`) · **Airflow providers:** `apache-airflow-providers-google` (runs *inside* the Composer environment, not in this notebook's own kernel)

**Data:** [`bigquery-public-data.ga4_obfuscated_sample_ecommerce`](https://console.cloud.google.com/marketplace/product/bigquery-public-datasets)

**References:** `RESOURCES.md` (Full reference) | [Cloud Composer 3 overview](https://docs.cloud.google.com/composer/docs/composer-3/composer-overview) | [`BigQueryInsertJobOperator`](https://airflow.apache.org/docs/apache-airflow-providers-google/stable/operators/cloud/bigquery.html) | `MLOps/Serving/Batch/Orchestrating%20Batch%20Inference%20With%20Airflow.ipynb` (`MLOps/Serving/Batch/Orchestrating Batch Inference With Airflow.ipynb`) — this repo's deeper, general-purpose Composer/Airflow treatment (Composer 2, Dataproc/Dataflow/KFP DAGs) this notebook only slices for BQML | `setup` (Setup guide)

---
## Setup

Set your project and location, authenticate, and create a shared dataset.

```python
PROJECT_ID = 'statmike-mlops-349915'  # <-- Replace with your project ID
LOCATION = 'US'  # BigQuery dataset location
DATASET_ID = 'bq_ml'  # Shared dataset across all bq-ml notebooks
COMPOSER_REGION = 'us-central1'  # Cloud Composer requires a specific region, not the 'US' multi-region
COMPOSER_ENVIRONMENT = 'bq-ml-composer'  # Shared across this notebook and airflow_with_kfp/
```

### Environment

> **Already set up the project environment?** The cell below is a no-op — packages are already in your kernel. See the `setup` (Setup Reference) for details.
>
> **Running standalone** (Colab, Colab Enterprise, Vertex AI Workbench)? The cell below installs required packages into your current kernel.
>
> Note: this only installs the client library used to *manage* the Composer environment (`google-cloud-orchestration-airflow`). The DAG file itself runs *inside* Composer's own managed Airflow runtime, which already has `apache-airflow` and `apache-airflow-providers-google` pre-installed — this notebook's kernel never imports `airflow` directly.

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
## Step 0 — Enable the Composer API, confirm IAM, and create the environment (idempotent)

The environment's own service account (the project's default Compute Engine service account, unless overridden) needs `roles/composer.worker` to operate. This project's service account already has broader roles that cover it; the check below grants it explicitly if a fresh project doesn't. Creating the environment for real takes **~20-30 minutes** — this cell checks for an existing environment first (in case `airflow_with_kfp/` already created it in this session) and only creates one if missing.

```python
import subprocess

def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)

# 1. Enable the Cloud Composer API (idempotent)
result = run(['gcloud', 'services', 'enable', 'composer.googleapis.com', '--project', PROJECT_ID])
if result.returncode == 0:
    print('Cloud Composer API enabled (or already was)')
else:
    print('Could not enable the API automatically:')
    print(result.stderr)
    print(f"Run this yourself: gcloud services enable composer.googleapis.com --project {PROJECT_ID}")

# 2. Determine the project number and the environment's own service account
project_number = run(['gcloud', 'projects', 'describe', PROJECT_ID, '--format=value(projectNumber)']).stdout.strip()
environment_service_account = f'{project_number}-compute@developer.gserviceaccount.com'
print('Environment service account:', environment_service_account)

# 3. Check whether that service account already has sufficient Composer access
policy = run(['gcloud', 'projects', 'get-iam-policy', PROJECT_ID,
              '--flatten=bindings[].members',
              f'--filter=bindings.members:serviceAccount:{environment_service_account}',
              '--format=value(bindings.role)'])
current_roles = set(policy.stdout.split())
composer_sufficient_roles = {'roles/composer.worker', 'roles/composer.admin', 'roles/editor', 'roles/owner'}

if current_roles & composer_sufficient_roles:
    print('Composer access already sufficient.')
else:
    print('No sufficient Composer role found — granting roles/composer.worker...')
    grant_result = run(['gcloud', 'projects', 'add-iam-policy-binding', PROJECT_ID,
                         f'--member=serviceAccount:{environment_service_account}',
                         '--role=roles/composer.worker', '--condition=None'])
    if grant_result.returncode == 0:
        print(f'Granted roles/composer.worker to {environment_service_account}')
    else:
        print('Could not grant automatically (likely missing roles/resourcemanager.projectIamAdmin). Ask a project admin to run:')
        print(f'  gcloud projects add-iam-policy-binding {PROJECT_ID} \\')
        print(f'    --member="serviceAccount:{environment_service_account}" --role="roles/composer.worker"')
```

```python
from google.cloud.orchestration.airflow import service_v1
from google.cloud.orchestration.airflow.service_v1.types import environments

composer_client = service_v1.EnvironmentsClient()
composer_parent = f'projects/{PROJECT_ID}/locations/{COMPOSER_REGION}'
composer_env_path = f'{composer_parent}/environments/{COMPOSER_ENVIRONMENT}'

try:
    env = composer_client.get_environment(name=composer_env_path)
    print(f'Environment already exists (state: {env.state.name}) — reusing it.')
except Exception:
    print(f'Creating Composer 3 environment {COMPOSER_ENVIRONMENT} — this takes ~20-30 minutes...')
    env_config = environments.Environment(
        name=composer_env_path,
        config=environments.EnvironmentConfig(
            software_config=environments.SoftwareConfig(
                image_version='composer-3-airflow-2.11.1-build.11',  # Composer 3's current default image
            ),
            node_config=environments.NodeConfig(
                service_account=environment_service_account,
            ),
            environment_size=environments.EnvironmentConfig.EnvironmentSize.ENVIRONMENT_SIZE_SMALL,
            # Composer 3 exposes explicit per-component sizing (workloads_config) --
            # this is the actual lever for keeping a demo environment cheap. Every
            # component below is set to the smallest accepted values.
            workloads_config=environments.WorkloadsConfig(
                scheduler=environments.WorkloadsConfig.SchedulerResource(
                    cpu=0.5, memory_gb=2, storage_gb=1, count=1),
                web_server=environments.WorkloadsConfig.WebServerResource(
                    cpu=0.5, memory_gb=2, storage_gb=1),
                worker=environments.WorkloadsConfig.WorkerResource(
                    cpu=0.5, memory_gb=2, storage_gb=1, min_count=1, max_count=1),
                triggerer=environments.WorkloadsConfig.TriggererResource(
                    cpu=0.5, memory_gb=1, count=1),
                dag_processor=environments.WorkloadsConfig.DagProcessorResource(
                    cpu=0.5, memory_gb=2, storage_gb=1, count=1),
            ),
        ),
    )
    operation = composer_client.create_environment(parent=composer_parent, environment=env_config)
    operation.result(timeout=2400)
    # The Environment returned directly by the create operation doesn't
    # always have `state` populated yet (seen live: STATE_UNSPECIFIED even
    # though creation genuinely succeeded) -- re-fetch for an accurate value.
    env = composer_client.get_environment(name=composer_env_path)
    print('Environment created:', env.name)

print('State:', env.state.name)
print('DAG GCS prefix:', env.config.dag_gcs_prefix)
print('Airflow URI:', env.config.airflow_uri)
dag_bucket_name = env.config.dag_gcs_prefix.split('/')[2]
```

**GOTCHA, verified live**: right after the environment reports `RUNNING`, the Airflow webserver itself is often still starting up behind it — API calls in the next steps may see `502` for a few extra minutes even though the `Environment` resource is already `RUNNING`. The DAG *processor* and *scheduler* are typically ready sooner (confirmed live via Cloud Logging: DAGs were parsed with 0 errors while the webserver was still printing `Starting the process, got command: webserver`).

**A second, related GOTCHA, also verified live**: with `web_server` sized to the floor (`cpu=0.5, memory_gb=2`, no replica), the webserver process itself restarted several times over a ~25 minute session (roughly every 10-15 minutes, confirmed via Cloud Logging timestamps of repeated `Starting gunicorn` events) — each restart causes a brief window of non-200s from the Airflow REST API, even though the DAG *scheduler* and already-running task instances are completely unaffected (a DAG run in progress during a webserver restart keeps running correctly; only polling its status via the API is briefly interrupted). **A first attempt at retry logic (6 retries × 15s ≈ 90s) genuinely wasn't enough** — a real run hit a restart window that outlasted it, and the *calling* code crashed on `resp.json()` when the retry loop gave up and returned a non-200 response with an empty body. `airflow_api()` below uses a longer budget (12 retries × 20s ≈ 4 minutes) and every caller checks `resp is not None and resp.status_code == 200` before parsing JSON, rather than assuming a returned response is necessarily a good one. A production environment would size `web_server` well above this floor; this notebook keeps it minimal on purpose to demonstrate the actual cost lever, with retry logic absorbing the resulting instability.

Also verified live: the documented `gcloud composer environments run ... dags list` CLI path took over 10 minutes to return anything useful in this session (it spins up its own temporary execution context) — the direct Airflow REST API calls used below (once the webserver is actually up) are far faster and more scriptable, and are what the rest of this notebook uses throughout.

---
## Step 1 — Self-contained feature table

Identical feature engineering to every other Phase 8 pipeline.

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
## Step 2 — Write the DAG

Six tasks: `check_drift` runs the `ML.VALIDATE_DATA_DRIFT` query via `BigQueryInsertJobOperator`; `branch_on_drift` (a `BranchPythonOperator`) fetches that job's rows via `BigQueryHook` + XCom and picks the next task; on the drift path, `get_prior_metric` → `retrain_model` → `get_new_metric` → `report_drift_retrain` all run as `BigQueryInsertJobOperator`/`PythonOperator` tasks; on the no-drift path, `no_drift` is a no-op `EmptyOperator`. A final `pipeline_complete` task uses `trigger_rule=NONE_FAILED_MIN_ONE_SUCCESS` to join cleanly after a branch, regardless of which side ran.

`BigQueryInsertJobOperator.execute()` returns the job's `job_id` as its XCom value (not the row data) — reading actual query results back into Airflow (for branching, or for the final report) uses `BigQueryHook().get_job(job_id=...).result()` inside a `PythonOperator`, the standard combination of "operator submits the work, hook reads results back for control flow."

**GOTCHA, verified live (same family as `pipelines/cloud_workflows/`/`pipelines/dataform/`'s query-cache finding, confirmed NOT to apply here)**: `get_prior_metric`/`get_new_metric` re-run the identical `ML.EVALUATE` text against a repeatedly-retrained model — the same at-risk shape. Here, `configuration={'query': {..., 'useQueryCache': False}}` uses a real Python `bool`, and it works correctly (confirmed via `INFORMATION_SCHEMA.JOBS_BY_PROJECT`: `cache_hit: false` on both jobs) — `BigQueryInsertJobOperator` submits jobs through the standard `google-cloud-bigquery` client's own `QueryJob.from_api_repr()`, not the custom JSON-cleanup logic that silently dropped the equivalent Python bool in `pipelines/vertex_kfp/`'s KFP components. **Don't assume every Google API wrapper has that bug — verify per library, as done here.**

```python
dag_source = '''"""DAG: GA4 churn pipeline drift-check -> conditional retrain -> report, via BigQueryInsertJobOperator."""
from datetime import datetime

from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import BranchPythonOperator, PythonOperator
from airflow.providers.google.cloud.hooks.bigquery import BigQueryHook
from airflow.providers.google.cloud.operators.bigquery import BigQueryInsertJobOperator
from airflow.utils.trigger_rule import TriggerRule

PROJECT_ID = "{project_id}"
DATASET_ID = "{dataset_id}"
LOCATION = "{location}"
CUTOFF_DATE = "2020-11-20"

FEATURES_TABLE = f"`{{PROJECT_ID}}.{{DATASET_ID}}.ga4_churn_pipeline_features`"
MODEL_REF = f"`{{PROJECT_ID}}.{{DATASET_ID}}.ga4_churn_pipeline_model`"
FEATURE_COLS = (
    "n_events, n_active_days, n_page_view, n_view_item, n_add_to_cart, "
    "n_begin_checkout, n_sessions, did_purchase, device_category, country, "
    "traffic_medium, total_engagement_time_msec"
)

DRIFT_QUERY = f"""
SELECT input, metric, ROUND(value, 4) AS value
FROM ML.VALIDATE_DATA_DRIFT(
  (SELECT {{FEATURE_COLS}} FROM {{FEATURES_TABLE}} WHERE first_date <= \'{{CUTOFF_DATE}}\'),
  (SELECT {{FEATURE_COLS}} FROM {{FEATURES_TABLE}} WHERE first_date > \'{{CUTOFF_DATE}}\'),
  STRUCT(0.1 AS numerical_default_threshold, 0.1 AS categorical_default_threshold)
)
WHERE is_anomaly = TRUE
ORDER BY value DESC
"""

EVALUATE_QUERY = f"SELECT roc_auc FROM ML.EVALUATE(MODEL {{MODEL_REF}})"

RETRAIN_QUERY = f"""
CREATE OR REPLACE MODEL {{MODEL_REF}}
OPTIONS(
  model_type = \'BOOSTED_TREE_CLASSIFIER\',
  input_label_cols = [\'churned\'],
  auto_class_weights = TRUE,
  data_split_method = \'AUTO_SPLIT\',
  enable_global_explain = TRUE
) AS
SELECT {{FEATURE_COLS}}, churned FROM {{FEATURES_TABLE}}
"""


def _fetch_rows(job_id):
    hook = BigQueryHook(use_legacy_sql=False)
    job = hook.get_job(job_id=job_id, location=LOCATION)
    return [dict(row.items()) for row in job.result()]


def _branch_on_drift(**context):
    ti = context["ti"]
    job_id = ti.xcom_pull(task_ids="check_drift")
    rows = _fetch_rows(job_id)
    ti.xcom_push(key="drift_rows", value=rows)
    return "get_prior_metric" if rows else "no_drift"


def _report(**context):
    ti = context["ti"]
    drift_rows = ti.xcom_pull(task_ids="branch_on_drift", key="drift_rows")
    prior_job_id = ti.xcom_pull(task_ids="get_prior_metric")
    new_job_id = ti.xcom_pull(task_ids="get_new_metric")
    prior_roc_auc = _fetch_rows(prior_job_id)[0]["roc_auc"]
    new_roc_auc = _fetch_rows(new_job_id)[0]["roc_auc"]
    print("GA4 Churn Pipeline Monitoring Report")
    print("Drift detected in:", drift_rows)
    print("roc_auc before retrain:", prior_roc_auc)
    print("roc_auc after retrain:", new_roc_auc)


with DAG(
    dag_id="ga4_churn_pipeline",
    schedule=None,
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["bq-ml", "ga4-churn"],
) as dag:

    check_drift = BigQueryInsertJobOperator(
        task_id="check_drift",
        configuration={{"query": {{"query": DRIFT_QUERY, "useLegacySql": False}}}},
        location=LOCATION,
    )

    branch_on_drift = BranchPythonOperator(
        task_id="branch_on_drift",
        python_callable=_branch_on_drift,
    )

    get_prior_metric = BigQueryInsertJobOperator(
        task_id="get_prior_metric",
        configuration={{"query": {{"query": EVALUATE_QUERY, "useLegacySql": False, "useQueryCache": False}}}},
        location=LOCATION,
    )

    retrain_model = BigQueryInsertJobOperator(
        task_id="retrain_model",
        configuration={{"query": {{"query": RETRAIN_QUERY, "useLegacySql": False}}}},
        location=LOCATION,
    )

    get_new_metric = BigQueryInsertJobOperator(
        task_id="get_new_metric",
        configuration={{"query": {{"query": EVALUATE_QUERY, "useLegacySql": False, "useQueryCache": False}}}},
        location=LOCATION,
    )

    report_drift_retrain = PythonOperator(
        task_id="report_drift_retrain",
        python_callable=_report,
    )

    no_drift = EmptyOperator(task_id="no_drift")

    pipeline_complete = EmptyOperator(
        task_id="pipeline_complete",
        trigger_rule=TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS,
    )

    check_drift >> branch_on_drift
    branch_on_drift >> get_prior_metric >> retrain_model >> get_new_metric >> report_drift_retrain >> pipeline_complete
    branch_on_drift >> no_drift >> pipeline_complete
'''.format(project_id=PROJECT_ID, dataset_id=DATASET_ID, location=LOCATION)

with open('dag_ga4_churn_pipeline.py', 'w') as f:
    f.write(dag_source)
print('DAG written to dag_ga4_churn_pipeline.py')
```

---
## Step 3 — Upload the DAG

Composer's DAG processor picks up new files from `dag_gcs_prefix` on a short polling interval — allow a minute or two before it's parsed and available via the Airflow API.

```python
from google.cloud import storage
import time

storage_client = storage.Client(project=PROJECT_ID)
dag_bucket = storage_client.bucket(dag_bucket_name)
dag_blob_name = env.config.dag_gcs_prefix.split(dag_bucket_name + '/', 1)[1] + '/dag_ga4_churn_pipeline.py'
dag_bucket.blob(dag_blob_name).upload_from_filename('dag_ga4_churn_pipeline.py')
print(f'Uploaded to gs://{dag_bucket_name}/{dag_blob_name}')

print('Waiting for the DAG processor to pick it up...')
time.sleep(90)
```

---
## Step 4 — Trigger the DAG via the Airflow REST API

Authenticates with this notebook's own Application Default Credentials against Composer's IAP-fronted Airflow webserver — the same `google.auth`-based pattern documented for [accessing the Airflow REST API](https://cloud.google.com/composer/docs/access-airflow-api). If this returns `502`, the webserver is still warming up (see the gotcha in Step 0) — wait a minute and retry.

```python
import google.auth
import google.auth.transport.requests

def airflow_api(method, path, retries=12, **kwargs):
    """Call the Airflow REST API, retrying on non-200s (the webserver can
    restart periodically on a minimally-sized environment -- see the gotcha
    above; a single restart cycle can outlast a short retry budget)."""
    creds, _ = google.auth.default(scopes=['https://www.googleapis.com/auth/cloud-platform'])
    session = google.auth.transport.requests.AuthorizedSession(creds)
    url = f'{env.config.airflow_uri}/api/v1{path}'
    resp = None
    for attempt in range(retries):
        try:
            resp = session.request(method, url, timeout=30, **kwargs)
            if resp.status_code == 200:
                return resp
        except Exception:
            resp = None
        time.sleep(20)
    return resp  # caller must check status_code -- may be a non-200 response or None

# Confirm the DAG parsed with no import errors before triggering
resp = airflow_api('GET', '/dags/ga4_churn_pipeline')
print('DAG status:', resp.status_code if resp is not None else None)
print('has_import_errors:', resp.json().get('has_import_errors') if resp is not None and resp.status_code == 200 else 'unknown')
```

```python
resp = airflow_api('POST', '/dags/ga4_churn_pipeline/dagRuns', json={'conf': {}})
assert resp is not None and resp.status_code == 200, f'Failed to trigger DAG: {resp}'
dag_run_id = resp.json()['dag_run_id']
print('Triggered dag_run_id:', dag_run_id)

terminal_states = {'success', 'failed'}
state = None
while state not in terminal_states:
    resp = airflow_api('GET', f'/dags/ga4_churn_pipeline/dagRuns/{dag_run_id}')
    if resp is not None and resp.status_code == 200:
        state = resp.json().get('state')
    time.sleep(15)

print('Final DAG run state:', state)
resp = airflow_api('GET', f'/dags/ga4_churn_pipeline/dagRuns/{dag_run_id}/taskInstances')
if resp is not None and resp.status_code == 200:
    for ti in sorted(resp.json()['task_instances'], key=lambda t: t.get('start_date') or ''):
        print(f"  {ti['task_id']:25s} {ti['state']}")
```

**Real, live-verified outcome**: `check_drift` → `branch_on_drift` correctly routes to the retrain path (5 of 12 features drifted, the same Black-Friday-driven population shift found in every other Phase 8 pipeline) → `get_prior_metric` → `retrain_model` → `get_new_metric` → `report_drift_retrain`, while `no_drift` shows **`skipped`** — genuine proof that `BranchPythonOperator` diverts execution rather than just returning a value nobody acts on. `pipeline_complete` succeeds even though one of its two upstream branches was skipped, confirming `trigger_rule=NONE_FAILED_MIN_ONE_SUCCESS` works as intended.

`roc_auc` before/after retrain (read from `report_drift_retrain`'s task logs): **0.7515 → 0.7697** — a real, positive retrain outcome, consistent with every other Phase 8 pipeline sharing this same data and chronology.

> `BOOSTED_TREE_CLASSIFIER` training carries a small amount of run-to-run variation — a rerun may show slightly different exact figures, but the direction (drift detected, retrain improves `roc_auc`) is the durable finding.

---
## Related content

- `pipelines/sql_scripting` (`pipelines/sql_scripting/`), `pipelines/scheduled_queries` (`pipelines/scheduled_queries/`), `pipelines/cloud_workflows` (`pipelines/cloud_workflows/`) — the same drift-check/retrain logic via BigQuery scripting, BigQuery-native scheduling, and Cloud Workflows YAML, respectively. Four genuinely different orchestration mechanisms doing the identical job.
- `pipelines/dataform` (`pipelines/dataform/`) and `pipelines/dbt` (`pipelines/dbt/`) — the same idea via a dependency graph instead of imperative step-by-step control flow.
- `pipelines/airflow_with_kfp` (`pipelines/airflow_with_kfp/`) — builds on this same live Composer environment to trigger `pipelines/vertex_kfp/`'s Vertex AI Pipeline from an Airflow DAG instead of running BigQuery jobs directly.
- `MLOps/Serving/Batch/Orchestrating%20Batch%20Inference%20With%20Airflow.ipynb` (`MLOps/Serving/Batch/Orchestrating Batch Inference With Airflow.ipynb`) — the repo's deeper, general-purpose Composer/Airflow treatment (Composer 2, Dataproc/Dataflow/KFP DAGs for non-BQML batch inference) this notebook only slices for BQML.
- `workflows/ga4_churn_prediction` (`workflows/ga4_churn_prediction/`) — the workflow this pipeline operationalizes.
