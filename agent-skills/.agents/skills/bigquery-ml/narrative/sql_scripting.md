# SQL Scripting — BigQuery ML Pipeline

The simplest possible BQML pipeline: **no external orchestrator at all.** A single multi-statement BigQuery script (`DECLARE`/`SET`/`IF`/`BEGIN...END`, submitted as one query job) checks for data drift, conditionally retrains, and reports via a deliberate `SELECT ERROR()` — the report string becomes the job's error message, which any caller can catch and forward to an alerting system. This exact script is what `pipelines/scheduled_queries` (`pipelines/scheduled_queries/`) schedules next.

Modernizes `MLOps/Model Monitoring/model_monitoring_job.sql`'s `DECLARE`/`IF`/`BEGIN...END` + `SELECT ERROR()` alerting pattern.

**Workflow operationalized:** `workflows/ga4_churn_prediction` (`workflows/ga4_churn_prediction/`)
**Functions used:** `ML.VALIDATE_DATA_DRIFT`, `ML.EVALUATE` · **Scripting:** `DECLARE`, `SET`, `IF...THEN...END IF`, `BEGIN...END`, `SELECT ERROR()`

`ML.VALIDATE_DATA_DRIFT`'s own mechanics (categorical vs. numerical metrics, `thresholds` overrides) are already covered in `functions/data_quality` (`functions/data_quality/`) and not repeated here — **this notebook's real content is composing drift detection + conditional retraining + alerting into one deployable script.**

**Data:** [`bigquery-public-data.ga4_obfuscated_sample_ecommerce`](https://console.cloud.google.com/marketplace/product/bigquery-public-datasets)

**References:** `RESOURCES.md` (Full reference) | [Scripting docs](https://cloud.google.com/bigquery/docs/reference/standard-sql/scripting) | `setup` (Setup guide)

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

Same cohort/feature/label design as `workflows/ga4_churn_prediction/`, with `first_date` retained so this pipeline can simulate "new users showing up after the model went into production" using the dataset's own real chronology — entirely self-contained, since the workflow notebook's own cleanup drops its tables.

The initial model trains on users whose first activity falls on or before `2020-11-20` — simulating a model that went into production trained on the first ~3 weeks of user acquisition. **Black Friday 2020 was `2020-11-27`**, so this cutoff falls just *before* the holiday shopping surge — a realistic "model trained on pre-holiday behavior" scenario.

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

query = f"""
SELECT
  CASE WHEN first_date <= '2020-11-20' THEN 'TRAIN_INITIAL' ELSE 'NEW_ARRIVALS' END AS slice,
  COUNT(*) AS n_users,
  ROUND(AVG(CAST(churned AS INT64)), 3) AS churn_rate
FROM `{PROJECT_ID}.{DATASET_ID}.ga4_churn_pipeline_features`
GROUP BY slice
"""
client.query(query).to_dataframe()
```

A real 4.2-point churn-rate gap between the two slices (91.4% vs. 95.6%) even before any drift test runs — a first hint that these are two meaningfully different populations, not just more of the same.

```python
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
## Step 2 — The pipeline script: drift check → conditional retrain → report

Submitted as **one multi-statement script** (a single BigQuery job). Compares the model's original training population (`TRAIN_INITIAL`) against everyone who has arrived since (`NEW_ARRIVALS`) on the model's own input features — label excluded, since a real serving-time drift check wouldn't have it either (this static historical dataset happens to have every label already observed, but the check is written as if it didn't).

`ML.VALIDATE_DATA_DRIFT`'s 3-argument form is used here (base query, compare query, options) rather than passing a `MODEL` as a 4th argument — verified live that a plain `CREATE MODEL`-trained `BOOSTED_TREE_CLASSIFIER` doesn't qualify as the "Model Registry MODEL" that 4th argument requires; the 3-argument form (already established in `functions/data_quality/`) works universally.

If drift is detected, the script retrains on the full cohort, re-evaluates, and reports via `SELECT ERROR()` — a deliberate BigQuery scripting idiom (also used in the legacy `model_monitoring_job.sql`): the report string becomes the query job's error message, which the calling code catches and treats as the alert payload rather than a real failure.

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

# SELECT ERROR() raises the report as the job's error message -- catch it as
# the alert payload rather than letting it propagate as an unhandled failure.
try:
    client.query(pipeline_script).result()
    print('Pipeline ran clean: no drift detected, no retrain triggered.')
except Exception as e:
    print('PIPELINE ALERT:')
    print(str(e))
```

**Real, honest result**: drift detected in 5 of 12 features (`total_engagement_time_msec` strongest at 0.49, then `n_begin_checkout`, `n_add_to_cart`, `n_events`, `n_page_view` — all Jensen-Shannon divergence above the 0.1 threshold). This is genuinely explainable, not a data-quality artifact: the `NEW_ARRIVALS` window spans Black Friday/Cyber Monday (`2020-11-27`/`2020-11-30`), a real seasonal shift in shopping behavior. The retrain that followed is a real, positive outcome — `roc_auc` improved from **0.734 to 0.767** by folding the larger, more recent, holiday-inclusive cohort back into training rather than continuing to serve on pre-holiday-only data.

> `BOOSTED_TREE_CLASSIFIER` training carries a small amount of run-to-run variation — a rerun may show slightly different exact figures (drift values and `roc_auc` alike), but the direction (drift detected, retrain improves `roc_auc`) is the durable finding.

On a quiet run (no drift), the script's `ELSE` branch returns a plain status row and skips retraining entirely — no alert, no wasted retraining cost. That's the same design choice the legacy `model_monitoring_job.sql` this pipeline modernizes makes.

---
## Step 3 — What comes next: scheduling this script

This notebook ran the script once, interactively, from Python. The script itself doesn't know or care how it's invoked — that's the point of packaging the whole check→retrain→alert cycle into one self-contained multi-statement query. `pipelines/scheduled_queries` (`pipelines/scheduled_queries/`) takes this exact script and runs it on a recurring schedule via the BigQuery Data Transfer API, with the same `SELECT ERROR()` payload wired to email alerting on failure.

---
## Related content

- `functions/data_quality` (`functions/data_quality/`) — `ML.VALIDATE_DATA_DRIFT`'s full mechanics (categorical vs. numerical metrics, per-column `thresholds` overrides).
- `MLOps/Model%20Monitoring` (`MLOps/Model Monitoring/model_monitoring_job.sql`) — the legacy script this pipeline modernizes.
- `workflows/ga4_churn_prediction` (`workflows/ga4_churn_prediction/`) — the workflow this pipeline operationalizes.
