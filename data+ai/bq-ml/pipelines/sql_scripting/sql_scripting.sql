-- SQL Scripting — BigQuery ML Pipeline
-- =============================================================
-- The simplest possible BQML pipeline: no external orchestrator at all.
-- A single multi-statement BigQuery script (DECLARE/SET/IF/BEGIN...END,
-- submitted as ONE query job) checks for data drift, conditionally retrains,
-- and reports via a deliberate SELECT ERROR() -- the report string becomes
-- the job's error message, which any caller (Python client, scheduled query,
-- Cloud Workflow, Airflow) can catch and forward to an alerting system. This
-- exact script is what pipelines/scheduled_queries/ schedules next.
--
-- Modernizes: MLOps/Model Monitoring/model_monitoring_job.sql (same
-- DECLARE/IF/BEGIN...END + SELECT ERROR() alerting pattern, ML.VALIDATE_DATA_DRIFT
-- signature simplified to the 3-argument form already established in
-- functions/data_quality/ -- no live BQML model qualifies as a Model
-- Registry MODEL for VALIDATE_DATA_DRIFT's optional 4th argument here).
--
-- Workflow operationalized: ../../workflows/ga4_churn_prediction/
-- Data: bigquery-public-data.ga4_obfuscated_sample_ecommerce
--
-- Full reference: ../../RESOURCES.md
-- Official docs:
--   ML.VALIDATE_DATA_DRIFT: https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-validate-data-drift
--   Scripting (DECLARE/IF/BEGIN...END): https://cloud.google.com/bigquery/docs/reference/standard-sql/scripting


-- =============================================================================
-- Setup: self-contained feature table + an initial "production" model
-- =============================================================================
-- Same cohort/feature/label design as workflows/ga4_churn_prediction/, with
-- first_date retained so this pipeline can simulate "new arrivals showing up
-- after the model went into production" using the dataset's own real
-- chronology, entirely self-contained (the workflow notebook's own cleanup
-- drops its tables, so this pipeline never depends on it having been run).
CREATE OR REPLACE TABLE `PROJECT_ID.DATASET.ga4_churn_pipeline_features` AS
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
GROUP BY fw.user_pseudo_id, lw.user_pseudo_id;
-- Verified: 162,339 users; TRAIN_INITIAL (first_date <= 2020-11-20) = 51,857
-- users, 91.4% churned; NEW_ARRIVALS (first_date > 2020-11-20) = 110,482
-- users, 95.6% churned -- a real 4.2-point churn-rate gap between the two
-- slices before any drift test even runs.

CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.ga4_churn_pipeline_model`
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
FROM `PROJECT_ID.DATASET.ga4_churn_pipeline_features`
WHERE first_date <= '2020-11-20';
-- Simulates: this model already went into production trained on the first
-- ~3 weeks of user acquisition (Black Friday 2020 was 2020-11-27, so this
-- cutoff falls just BEFORE the holiday shopping surge -- a realistic
-- "model trained on pre-holiday behavior" scenario).


-- =============================================================================
-- The pipeline script: drift check -> conditional retrain -> report
-- =============================================================================
-- Submitted as ONE multi-statement script (a single BigQuery job). Compares
-- the model's original training population (TRAIN_INITIAL) against everyone
-- who has arrived since (NEW_ARRIVALS) on the model's own input features
-- (label excluded -- a real serving-time drift check wouldn't have it
-- either, though this static historical dataset happens to have every
-- label already observed).
DECLARE cutoff_date DATE DEFAULT DATE '2020-11-20';
DECLARE drift_anomalies ARRAY<STRUCT<input STRING, metric STRING, value FLOAT64>>;
DECLARE drift_report STRING;

SET drift_anomalies = (
  SELECT ARRAY_AGG(STRUCT(input, metric, ROUND(value, 4) AS value))
  FROM ML.VALIDATE_DATA_DRIFT(
    (SELECT n_events, n_active_days, n_page_view, n_view_item, n_add_to_cart, n_begin_checkout, n_sessions, did_purchase, device_category, country, traffic_medium, total_engagement_time_msec
     FROM `PROJECT_ID.DATASET.ga4_churn_pipeline_features`
     WHERE first_date <= cutoff_date),
    (SELECT n_events, n_active_days, n_page_view, n_view_item, n_add_to_cart, n_begin_checkout, n_sessions, did_purchase, device_category, country, traffic_medium, total_engagement_time_msec
     FROM `PROJECT_ID.DATASET.ga4_churn_pipeline_features`
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

    SET prior_roc_auc = (SELECT roc_auc FROM ML.EVALUATE(MODEL `PROJECT_ID.DATASET.ga4_churn_pipeline_model`));

    -- Retrain: same recipe, now on the full cohort (TRAIN_INITIAL + NEW_ARRIVALS)
    CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.ga4_churn_pipeline_model`
    OPTIONS(
      model_type = 'BOOSTED_TREE_CLASSIFIER',
      input_label_cols = ['churned'],
      auto_class_weights = TRUE,
      data_split_method = 'AUTO_SPLIT',
      enable_global_explain = TRUE
    ) AS
    SELECT n_events, n_active_days, n_page_view, n_view_item, n_add_to_cart, n_begin_checkout, n_sessions, did_purchase, device_category, country, traffic_medium, total_engagement_time_msec, churned
    FROM `PROJECT_ID.DATASET.ga4_churn_pipeline_features`;

    SET retrained_roc_auc = (SELECT roc_auc FROM ML.EVALUATE(MODEL `PROJECT_ID.DATASET.ga4_churn_pipeline_model`));

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
-- Verified live: drift detected in 5/12 features (total_engagement_time_msec
-- ~0.49, n_begin_checkout ~0.19, n_add_to_cart ~0.18, n_events ~0.14,
-- n_page_view ~0.13, all JENSEN_SHANNON_DIVERGENCE) -- a real, explainable
-- finding: the NEW_ARRIVALS window includes Black Friday/Cyber Monday
-- (2020-11-27/30), a genuine seasonal behavior shift, not a data-quality
-- artifact. Retrain result: roc_auc improved from ~0.73-0.74 to ~0.77 -- a
-- real, positive outcome from folding the newer, larger, more recent cohort
-- back into training rather than serving indefinitely on pre-holiday data
-- alone. (BOOSTED_TREE_CLASSIFIER has a small amount of run-to-run training
-- variation -- exact figures drift slightly across runs; the direction and
-- rough size of the finding is durable.)
-- SELECT ERROR() raises the report as the job's error message -- the
-- intended alerting idiom, caught programmatically (see the notebook), not
-- a genuine query failure.


-- =============================================================================
-- Cleanup
-- =============================================================================
-- DROP MODEL IF EXISTS `PROJECT_ID.DATASET.ga4_churn_pipeline_model`;
-- DROP TABLE IF EXISTS `PROJECT_ID.DATASET.ga4_churn_pipeline_features`;
