# Scheduled Queries — BigQuery ML Pipeline

Takes `pipelines/sql_scripting` (`pipelines/sql_scripting/`)'s exact drift-check → conditional-retrain → `SELECT ERROR()` script — **unchanged** — and schedules it via the BigQuery Data Transfer API, the same mechanism behind BigQuery Studio's "Scheduled queries" UI. No new BQML logic here: this notebook's real content is the scheduling/triggering/alerting layer wrapped around a script that doesn't know or care how it gets invoked.

Modernizes `MLOps/Model Monitoring/bqml-model-monitoring-tutorial.ipynb`'s "From Job To Scheduled Query" section.

**Workflow operationalized:** `workflows/ga4_churn_prediction` (`workflows/ga4_churn_prediction/`)
**Builds on:** `pipelines/sql_scripting` (`pipelines/sql_scripting/`) (the script being scheduled) · **API:** `google.cloud.bigquery_datatransfer` (`TransferConfig`, `ScheduleOptions`, `EmailPreferences`, `StartManualTransferRunsRequest`)

**Data:** [`bigquery-public-data.ga4_obfuscated_sample_ecommerce`](https://console.cloud.google.com/marketplace/product/bigquery-public-datasets)

**References:** `RESOURCES.md` (Full reference) | [Scheduling queries docs](https://cloud.google.com/bigquery/docs/scheduling-queries) | `setup` (Setup guide)

---
## Setup

Set your project and location, authenticate, and create a shared dataset. No connection needed.

```python
PROJECT_ID = 'statmike-mlops-349915'  # <-- Replace with your project ID
LOCATION = 'US'  # BigQuery dataset location
DATASET_ID = 'bq_ml'  # Shared dataset across all bq-ml notebooks
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
## Step 1 — Self-contained feature table + an initial "production" model

Identical setup to `pipelines/sql_scripting` (`pipelines/sql_scripting/`): its own copies of the GA4 churn feature table and initial model, since each pipeline notebook is self-contained (the workflow notebook's own cleanup drops its artifacts).

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
## Step 2 — The script being scheduled

The exact `pipeline_script` from `pipelines/sql_scripting/` — not modified in any way. A scheduled query is just this same text handed to a different execution mechanism.

**Design note:** the legacy `bqml-model-monitoring-tutorial.ipynb` this pipeline modernizes writes its script around the `@run_date` pseudo-parameter, so a recurring schedule can compute rolling date windows (e.g. "last week vs. the week before") against a live, continuously-growing serving table. This script instead uses fixed literal dates (`cutoff_date = DATE '2020-11-20'`) against a frozen historical GA4 export — every scheduled run would check the identical fixed window. That's an honest, disclosed difference driven by the dataset, not a gap in the scheduling mechanism itself: the same `@run_date` pattern would apply directly to a live production table.

```python
pipeline_script = r"""
DECLARE cutoff_date DATE DEFAULT DATE '2020-11-20';
DECLARE drift_anomalies ARRAY<STRUCT<input STRING, metric STRING, value FLOAT64>>;
DECLARE drift_report STRING;

SET drift_anomalies = (
  SELECT ARRAY_AGG(STRUCT(input, metric, ROUND(value, 4) AS value))
  FROM ML.VALIDATE_DATA_DRIFT(
    (SELECT n_events, n_active_days, n_page_view, n_view_item, n_add_to_cart, n_begin_checkout, n_sessions, did_purchase, device_category, country, traffic_medium, total_engagement_time_msec
     FROM `{project}.{dataset}.ga4_churn_pipeline_features`
     WHERE first_date <= cutoff_date),
    (SELECT n_events, n_active_days, n_page_view, n_view_item, n_add_to_cart, n_begin_checkout, n_sessions, did_purchase, device_category, country, traffic_medium, total_engagement_time_msec
     FROM `{project}.{dataset}.ga4_churn_pipeline_features`
     WHERE first_date > cutoff_date),
    STRUCT(0.1 AS numerical_default_threshold, 0.1 AS categorical_default_threshold)
  )
  WHERE is_anomaly = TRUE
);

IF ARRAY_LENGTH(drift_anomalies) > 0 THEN
  SET drift_report = (
    SELECT STRING_AGG(CONCAT('\n\t', da.input, ' (', da.metric, '): ', CAST(da.value AS STRING)) ORDER BY da.value DESC)
    FROM UNNEST(drift_anomalies) AS da
  );

  BEGIN
    DECLARE prior_roc_auc FLOAT64;
    DECLARE retrained_roc_auc FLOAT64;

    SET prior_roc_auc = (SELECT roc_auc FROM ML.EVALUATE(MODEL `{project}.{dataset}.ga4_churn_pipeline_model`));

    CREATE OR REPLACE MODEL `{project}.{dataset}.ga4_churn_pipeline_model`
    OPTIONS(
      model_type = 'BOOSTED_TREE_CLASSIFIER',
      input_label_cols = ['churned'],
      auto_class_weights = TRUE,
      data_split_method = 'AUTO_SPLIT',
      enable_global_explain = TRUE
    ) AS
    SELECT n_events, n_active_days, n_page_view, n_view_item, n_add_to_cart, n_begin_checkout, n_sessions, did_purchase, device_category, country, traffic_medium, total_engagement_time_msec, churned
    FROM `{project}.{dataset}.ga4_churn_pipeline_features`;

    SET retrained_roc_auc = (SELECT roc_auc FROM ML.EVALUATE(MODEL `{project}.{dataset}.ga4_churn_pipeline_model`));

    SELECT ERROR(
      CONCAT(
        "\n\nGA4 Churn Pipeline Monitoring Report (cutoff ", CAST(cutoff_date AS STRING), "):",
        "\n\tDrift detected in:", drift_report,
        "\n\nModel retrained on full cohort.",
        "\n\troc_auc before retrain (early-cohort-only model): ", CAST(prior_roc_auc AS STRING),
        "\n\troc_auc after retrain (full cohort): ", CAST(retrained_roc_auc AS STRING),
        "\n"
      )
    );
  END;
ELSE
  SELECT 'No drift detected -- no retrain triggered.' AS status;
END IF;
""".format(project=PROJECT_ID, dataset=DATASET_ID)
print('Pipeline script ready (same text as pipelines/sql_scripting/)')
```

---
## Step 3 — Create the scheduled query

`google.cloud.bigquery_datatransfer.DataTransferServiceClient` is the Python client for the same BigQuery Data Transfer Service that powers BigQuery Studio's "Scheduled queries" UI. `data_source_id='scheduled_query'` tells the Data Transfer Service that `params['query']` is arbitrary SQL to run on a schedule — the identical mechanism as any other transfer, just pointed at BigQuery itself instead of an external source.

**Verified live gotcha**: creating a transfer config directly through this API (rather than the Console's interactive flow) requires an explicit runtime identity — omitting `service_account_name` fails with `Failed to find a valid credential. The field 'version_info' or 'service_account_name' must be specified.` The Console handles this transparently via an OAuth consent step; the API needs a service account named explicitly.

**Verified live gotcha #2**: the schedule's own first automatic run and a manually-triggered demo run can race each other if both land close in time — both would try to `CREATE OR REPLACE` the same model concurrently, and BigQuery genuinely rejects that (`Model can not be updated by multiple create model query jobs at the same time`). Pushing `schedule_options.start_time` a couple of days out keeps this notebook's manual demo run isolated; a real production schedule wouldn't need this, since you wouldn't normally trigger a manual run at the exact moment the recurring schedule is also about to fire.

```python
from google.cloud import bigquery_datatransfer
from datetime import datetime, timezone, timedelta
import time

transfer_client = bigquery_datatransfer.DataTransferServiceClient()
parent = transfer_client.common_location_path(PROJECT_ID, 'us')

# Run the schedule as the project's default Compute Engine service account
import subprocess
project_number = subprocess.check_output(
    ['gcloud', 'projects', 'describe', PROJECT_ID, '--format=value(projectNumber)']
).decode().strip()
service_account_name = f'{project_number}-compute@developer.gserviceaccount.com'
print('Using service account:', service_account_name)

request = bigquery_datatransfer.CreateTransferConfigRequest(
    parent=parent,
    transfer_config=bigquery_datatransfer.TransferConfig(
        display_name='GA4 Churn Pipeline Monitoring (bq-ml demo)',
        data_source_id='scheduled_query',
        params={'query': pipeline_script},
        schedule='every 24 hours',
        schedule_options=bigquery_datatransfer.ScheduleOptions(
            start_time=datetime.now(timezone.utc) + timedelta(days=2)
        ),
        email_preferences=bigquery_datatransfer.EmailPreferences(
            enable_failure_email=True
        ),
    ),
    service_account_name=service_account_name,
)
scheduled_query = transfer_client.create_transfer_config(request=request)
print('Created:', scheduled_query.name)
print('Next automatic run:', scheduled_query.next_run_time)
```

---
## Step 4 — Trigger a manual run now (a real backfill, not waiting 24 hours)

`start_manual_transfer_runs` is exactly what a "Schedule backfill" click in the Console does — request that the transfer run immediately (or for a specific past date) rather than waiting for its next scheduled time.

```python
backfill_job = transfer_client.start_manual_transfer_runs(
    request=bigquery_datatransfer.StartManualTransferRunsRequest(
        parent=scheduled_query.name,
        requested_run_time=datetime.now(timezone.utc),
    )
)
run_name = backfill_job.runs[0].name
print('Run:', run_name)

while True:
    run = transfer_client.get_transfer_run(name=run_name)
    state = run.state.name
    if state in ['FAILED', 'SUCCEEDED', 'CANCELLED']:
        break
    time.sleep(15)

print('Final state:', state)
print()
print('Error status (the alert payload email_preferences would forward):')
print(run.error_status.message if run.error_status else '(none)')
```

**`FAILED` is the correct, expected terminal state here** — not a real failure. This scheduled run used the exact same `SELECT ERROR()` idiom as `pipelines/sql_scripting/` to pass its report through as the job's (and therefore the transfer run's) error message. `email_preferences.enable_failure_email=True` means this exact message is what would land in an inbox as a real failure-alert email. A state of `SUCCEEDED` would mean the script's `ELSE` branch fired instead — no drift, no report, nothing to alert on. Same real, positive retrain outcome as `pipelines/sql_scripting/`: `roc_auc` improves from **0.737 to 0.766** by folding the newer, holiday-inclusive cohort back into training.

> `BOOSTED_TREE_CLASSIFIER` training carries a small amount of run-to-run variation — a rerun may show slightly different exact figures, but the direction (drift detected, retrain improves `roc_auc`) is the durable finding.

---
## Related content

- `pipelines/sql_scripting` (`pipelines/sql_scripting/`) — the script this pipeline schedules, and where its drift-check/retrain design is explained in full.
- `functions/data_quality` (`functions/data_quality/`) — `ML.VALIDATE_DATA_DRIFT`'s full mechanics.
- `MLOps/Model%20Monitoring` (`MLOps/Model Monitoring/bqml-model-monitoring-tutorial.ipynb`) — the legacy tutorial this pipeline modernizes, including the `@run_date`-based rolling-window pattern for live serving tables.
- `workflows/ga4_churn_prediction` (`workflows/ga4_churn_prediction/`) — the workflow this pipeline operationalizes.
