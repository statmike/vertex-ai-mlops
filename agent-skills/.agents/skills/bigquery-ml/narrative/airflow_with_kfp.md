# Airflow + Vertex AI Pipelines (KFP) — BigQuery ML Pipeline

The "meta-orchestration" pairing: an Airflow DAG on the **same live Cloud Composer 3 environment** as `pipelines/composer_airflow` (`pipelines/composer_airflow/`), using `RunPipelineJobOperator` to trigger `pipelines/vertex_kfp` (`pipelines/vertex_kfp/`)'s already-built Vertex AI Pipeline as a single managed task. If an organization already has an enterprise Airflow footprint (for cross-system scheduling, dependencies on non-GCP systems, existing alerting/on-call tooling) *and* a KFP pipeline built the modern way with prebuilt BQML components, this is how the two connect — you don't have to choose one or the other.

> ⚠️ **Shares the live Composer 3 environment created by `pipelines/composer_airflow` (`pipelines/composer_airflow/`).** Build/run that notebook first in this session. This notebook's own Cleanup section performs the **real** deletion of that shared environment — see Cleanup before running this standalone.

**Workflow operationalized:** `workflows/ga4_churn_prediction` (`workflows/ga4_churn_prediction/`) (via `pipelines/vertex_kfp` (`pipelines/vertex_kfp/`))
**API:** Cloud Composer (`google.cloud.orchestration.airflow.service_v1`) · **Airflow operator:** `RunPipelineJobOperator`

**Data:** [`bigquery-public-data.ga4_obfuscated_sample_ecommerce`](https://console.cloud.google.com/marketplace/product/bigquery-public-datasets)

**References:** `RESOURCES.md` (Full reference) | [`RunPipelineJobOperator`](https://airflow.apache.org/docs/apache-airflow-providers-google/stable/operators/cloud/vertex_ai.html) | `MLOps/Serving/Batch/Orchestrating%20Batch%20Inference%20With%20Airflow.ipynb` (`MLOps/Serving/Batch/Orchestrating Batch Inference With Airflow.ipynb`) — the repo's original "DAG 3" precedent for this exact pattern (Composer 2, non-BQML pipeline) | `setup` (Setup guide)

---
## Setup

Set your project and location, authenticate, and create a shared dataset.

```python
PROJECT_ID = 'statmike-mlops-349915'  # <-- Replace with your project ID
LOCATION = 'US'  # BigQuery dataset location
DATASET_ID = 'bq_ml'  # Shared dataset across all bq-ml notebooks
COMPOSER_REGION = 'us-central1'  # Cloud Composer requires a specific region, not the 'US' multi-region
COMPOSER_ENVIRONMENT = 'bq-ml-composer'  # Shared with pipelines/composer_airflow/
VERTEX_REGION = 'us-central1'  # Vertex AI Pipelines region
BUCKET = 'statmike-mlops-349915'  # GCS bucket for the compiled pipeline spec + pipeline_root
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
## Step 0 — Confirm the shared Composer environment exists

Reuses `pipelines/composer_airflow` (`pipelines/composer_airflow/`)'s environment if it's already running (the common case — build that notebook first in this session); creates it if this notebook is run standalone. See that notebook's Step 0 for the full Composer 3 sizing/IAM detail.

```python
import subprocess

def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)

result = run(['gcloud', 'services', 'enable', 'composer.googleapis.com', '--project', PROJECT_ID])
if result.returncode == 0:
    print('Cloud Composer API enabled (or already was)')
else:
    print('Could not enable the API automatically:', result.stderr)

project_number = run(['gcloud', 'projects', 'describe', PROJECT_ID, '--format=value(projectNumber)']).stdout.strip()
environment_service_account = f'{project_number}-compute@developer.gserviceaccount.com'

from google.cloud.orchestration.airflow import service_v1
from google.cloud.orchestration.airflow.service_v1.types import environments

composer_client = service_v1.EnvironmentsClient()
composer_parent = f'projects/{PROJECT_ID}/locations/{COMPOSER_REGION}'
composer_env_path = f'{composer_parent}/environments/{COMPOSER_ENVIRONMENT}'

try:
    env = composer_client.get_environment(name=composer_env_path)
    print(f'Environment already exists (state: {env.state.name}) — reusing it.')
except Exception:
    print(f'Not found — creating Composer 3 environment {COMPOSER_ENVIRONMENT} (see pipelines/composer_airflow/ for the full Step 0). This takes ~20-30 minutes...')
    env_config = environments.Environment(
        name=composer_env_path,
        config=environments.EnvironmentConfig(
            software_config=environments.SoftwareConfig(image_version='composer-3-airflow-2.11.1-build.11'),
            node_config=environments.NodeConfig(service_account=environment_service_account),
            environment_size=environments.EnvironmentConfig.EnvironmentSize.ENVIRONMENT_SIZE_SMALL,
            workloads_config=environments.WorkloadsConfig(
                scheduler=environments.WorkloadsConfig.SchedulerResource(cpu=0.5, memory_gb=2, storage_gb=1, count=1),
                web_server=environments.WorkloadsConfig.WebServerResource(cpu=0.5, memory_gb=2, storage_gb=1),
                worker=environments.WorkloadsConfig.WorkerResource(cpu=0.5, memory_gb=2, storage_gb=1, min_count=1, max_count=1),
                triggerer=environments.WorkloadsConfig.TriggererResource(cpu=0.5, memory_gb=1, count=1),
                dag_processor=environments.WorkloadsConfig.DagProcessorResource(cpu=0.5, memory_gb=2, storage_gb=1, count=1),
            ),
        ),
    )
    operation = composer_client.create_environment(parent=composer_parent, environment=env_config)
    env = operation.result(timeout=2400)
    print('Environment created:', env.name)

print('State:', env.state.name)
dag_bucket_name = env.config.dag_gcs_prefix.split('/')[2]
```

---
## Step 1 — Self-contained feature table

Identical feature engineering to every other Phase 8 pipeline. Needed here too, independently of `pipelines/composer_airflow` (`pipelines/composer_airflow/`) — that notebook's own Cleanup drops its copy as soon as its run finishes, so this notebook can't rely on it still being there even when run back-to-back in the same session.

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
## Step 2 — Compile the `pipelines/vertex_kfp/` pipeline and upload it to GCS

`RunPipelineJobOperator` triggers a pipeline from a compiled JSON spec, not from live Python — so the DAG needs a GCS path to the same pipeline defined in `pipelines/vertex_kfp/vertex_kfp.ipynb` (reproduced here for a self-contained build; see that notebook for the full gotcha history behind this exact pipeline definition).

```python
from kfp import dsl, compiler
from google_cloud_pipeline_components.v1.bigquery import (
    BigqueryCreateModelJobOp,
    BigqueryEvaluateModelJobOp,
    BigqueryPredictModelJobOp,
)

@dsl.component(base_image='python:3.11')
def check_quality_gate(evaluation_metrics: dsl.Input[dsl.Artifact], threshold: float) -> bool:
    field_names = [f['name'] for f in evaluation_metrics.metadata['schema']['fields']]
    roc_auc_index = field_names.index('roc_auc')
    roc_auc = float(evaluation_metrics.metadata['rows'][0]['f'][roc_auc_index]['v'])
    print(f'roc_auc={roc_auc}, threshold={threshold}')
    return roc_auc >= threshold

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

    create_model_task = BigqueryCreateModelJobOp(project=project, location=location, query=create_model_query)

    evaluate_task = BigqueryEvaluateModelJobOp(
        project=project, location=location,
        model=create_model_task.outputs['model'],
        job_configuration_query={'useQueryCache': 'false'},  # STRING, not bool -- see pipelines/vertex_kfp/
    )

    gate_task = check_quality_gate(
        evaluation_metrics=evaluate_task.outputs['evaluation_metrics'],
        threshold=quality_threshold,
    )

    with dsl.If(gate_task.output == True):
        predict_query = f"SELECT * FROM {features_table} WHERE first_date <= '2020-11-20' LIMIT 1000"
        BigqueryPredictModelJobOp(
            project=project, location=location,
            model=create_model_task.outputs['model'],
            table_name='', query_statement=predict_query,
        )

compiler.Compiler().compile(pipeline_func=ga4_churn_pipeline, package_path='ga4_churn_pipeline.json')
print('Compiled pipeline to ga4_churn_pipeline.json')
```

```python
from google.cloud import storage

storage_client = storage.Client(project=PROJECT_ID)
bucket = storage_client.bucket(BUCKET)
pipeline_template_blob = 'bq_ml/airflow_with_kfp/ga4_churn_pipeline.json'
bucket.blob(pipeline_template_blob).upload_from_filename('ga4_churn_pipeline.json')
pipeline_template_gcs = f'gs://{BUCKET}/{pipeline_template_blob}'
pipeline_root = f'gs://{BUCKET}/bq_ml/airflow_with_kfp/pipeline_root'
print('Uploaded to', pipeline_template_gcs)
```

---
## Step 3 — Write and upload the DAG

One task: `RunPipelineJobOperator`, pointed at the GCS template from Step 2. This is the entire DAG — all the actual BQML logic (train → evaluate → quality-gate → conditionally score) already lives in the compiled pipeline; Airflow's job here is purely to trigger and wait on it, the same "DAG 3" pattern as `MLOps/Serving/Batch/Orchestrating Batch Inference With Airflow.ipynb`, now pointed at a BQML pipeline instead of a Dataflow/Dataproc one.

```python
dag_source = '''"""DAG: trigger the pipelines/vertex_kfp/ Vertex AI Pipeline from Airflow via RunPipelineJobOperator."""
from datetime import datetime

from airflow import DAG
from airflow.providers.google.cloud.operators.vertex_ai.pipeline_job import RunPipelineJobOperator

PROJECT_ID = "{project_id}"
REGION = "{region}"
DATASET_ID = "{dataset_id}"
LOCATION = "{location}"
PIPELINE_TEMPLATE = "{pipeline_template_gcs}"
PIPELINE_ROOT = "{pipeline_root}"

with DAG(
    dag_id="airflow_with_kfp",
    schedule=None,
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["bq-ml", "ga4-churn", "kfp"],
) as dag:

    run_pipeline = RunPipelineJobOperator(
        task_id="run_ga4_churn_kfp_pipeline",
        project_id=PROJECT_ID,
        region=REGION,
        display_name="airflow-triggered-ga4-churn-pipeline",
        template_path=PIPELINE_TEMPLATE,
        pipeline_root=PIPELINE_ROOT,
        enable_caching=False,
        parameter_values={{
            "project": PROJECT_ID,
            "dataset": DATASET_ID,
            "location": LOCATION,
            "quality_threshold": 0.6,
        }},
    )
'''.format(
    project_id=PROJECT_ID, region=VERTEX_REGION, dataset_id=DATASET_ID, location=LOCATION,
    pipeline_template_gcs=pipeline_template_gcs, pipeline_root=pipeline_root,
)

with open('dag_airflow_with_kfp.py', 'w') as f:
    f.write(dag_source)

dag_bucket = storage_client.bucket(dag_bucket_name)
dag_blob_name = env.config.dag_gcs_prefix.split(dag_bucket_name + '/', 1)[1] + '/dag_airflow_with_kfp.py'
dag_bucket.blob(dag_blob_name).upload_from_filename('dag_airflow_with_kfp.py')
print(f'Uploaded to gs://{dag_bucket_name}/{dag_blob_name}')

import time
print('Waiting for the DAG processor to pick it up...')
time.sleep(90)
```

---
## Step 4 — Trigger the DAG via the Airflow REST API

Same `google.auth`-based pattern as `pipelines/composer_airflow` (`pipelines/composer_airflow/`), including retrying on non-200s (see that notebook's Step 0 gotcha on why a minimally-sized webserver restarts periodically). This step takes several minutes — `RunPipelineJobOperator` blocks until the underlying `PipelineJob` reaches a terminal state, which includes a real `BOOSTED_TREE_CLASSIFIER` training run.

**GOTCHA, verified live**: a manually-triggered run of a **paused** DAG is accepted by the API (`POST .../dagRuns` returns `200`) and shows up with state `queued` — but the scheduler never actually runs its tasks while the DAG stays paused, so it sits in `queued` forever with no error. If a DAG run seems permanently stuck at `queued`, check `GET /dags/{dag_id}`'s `is_paused` field before assuming something else is wrong.

```python
import google.auth
import google.auth.transport.requests

def airflow_api(method, path, retries=12, **kwargs):
    """Call the Airflow REST API, retrying on non-200s (the webserver can
    restart periodically on a minimally-sized environment -- see
    pipelines/composer_airflow/'s Step 0 gotcha; a single restart cycle can
    outlast a short retry budget)."""
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

resp = airflow_api('GET', '/dags/airflow_with_kfp')
print('DAG status:', resp.status_code if resp is not None else None)
print('has_import_errors:', resp.json().get('has_import_errors') if resp is not None and resp.status_code == 200 else 'unknown')
```

```python
resp = airflow_api('POST', '/dags/airflow_with_kfp/dagRuns', json={'conf': {}})
assert resp is not None and resp.status_code == 200, f'Failed to trigger DAG: {resp}'
dag_run_id = resp.json()['dag_run_id']
print('Triggered dag_run_id:', dag_run_id)

terminal_states = {'success', 'failed'}
state = None
while state not in terminal_states:
    resp = airflow_api('GET', f'/dags/airflow_with_kfp/dagRuns/{dag_run_id}')
    if resp is not None and resp.status_code == 200:
        state = resp.json().get('state')
    time.sleep(30)

print('Final DAG run state:', state)
resp = airflow_api('GET', f'/dags/airflow_with_kfp/dagRuns/{dag_run_id}/taskInstances')
if resp is not None and resp.status_code == 200:
    for ti in sorted(resp.json()['task_instances'], key=lambda t: t.get('start_date') or ''):
        print(f"  {ti['task_id']:25s} {ti['state']}")
```

**Real, live-verified outcome**: `run_ga4_churn_kfp_pipeline` succeeds, and the underlying Vertex `PipelineJob` it triggered (`airflow-triggered-ga4-churn-pipeline`, visible in the [Vertex AI Pipelines console](https://console.cloud.google.com/vertex-ai/pipelines)) reaches `PIPELINE_STATE_SUCCEEDED` with every task completing: `bigquery-create-model-job` → `bigquery-evaluate-model-job` → `check-quality-gate` → `condition-1` **TRIGGERED** → `bigquery-predict-model-job`. Confirmed directly via `aiplatform.PipelineJob.list()` and `.task_details` — the same live-verification standard as every other Phase 8 pipeline, not just trusting the Airflow task's own `success` status.

---
## Related content

- `pipelines/vertex_kfp` (`pipelines/vertex_kfp/`) — the pipeline this DAG triggers; see that notebook for the full build (prebuilt BQML components, the `evaluation_metrics` artifact gotcha, the `useQueryCache` string-vs-bool gotcha) and both a passing and a deliberately-failing quality-gate run.
- `pipelines/composer_airflow` (`pipelines/composer_airflow/`) — the sibling pipeline sharing this same Composer environment, running BigQuery jobs directly via `BigQueryInsertJobOperator` instead of triggering a separate Vertex Pipeline.
- `MLOps/Serving/Batch/Orchestrating%20Batch%20Inference%20With%20Airflow.ipynb` (`MLOps/Serving/Batch/Orchestrating Batch Inference With Airflow.ipynb`) — the original "DAG 3" pattern this notebook adapts, there triggering a non-BQML Dataflow/Dataproc-adjacent pipeline on Composer 2.
- `workflows/ga4_churn_prediction` (`workflows/ga4_churn_prediction/`) — the workflow this pipeline operationalizes.
