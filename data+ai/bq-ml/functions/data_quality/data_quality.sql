-- Data Quality / Model Monitoring — Progressive SQL Examples (BigQuery ML model-free functions)
-- =============================================================
-- Five functions for training/serving skew and data-drift monitoring, plus
-- descriptive-statistics helpers. Basic tier: ML.DESCRIBE_DATA,
-- ML.VALIDATE_DATA_SKEW, ML.VALIDATE_DATA_DRIFT (tabular output, anomaly
-- flags). Advanced/TFDV-compatible tier: ML.TFDV_DESCRIBE, ML.TFDV_VALIDATE
-- (emit/consume a TensorFlow DatasetFeatureStatisticsList proto as JSON).
-- None require a connection.
--
-- GOTCHA these functions are model-light but NOT the same as
-- ML.DETECT_ANOMALIES: this notebook is about DATASET-level distribution
-- shift (comparing whole datasets/time windows to each other or to stored
-- training stats). ML.DETECT_ANOMALIES (see models/kmeans/, models/pca/,
-- models/autoencoder/, models/arima_plus/, models/arima_plus_xreg/) is
-- about ROW-level outliers within one dataset. Different concept, similar
-- name.
--
-- Data: bigquery-public-data.ml_datasets.census_adult_income (same dataset
--       as models/logistic_regression/)
--
-- Full reference: ../../RESOURCES.md
-- Official docs:
--   ML.DESCRIBE_DATA:      https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-describe-data
--   ML.VALIDATE_DATA_SKEW: https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-validate-data-skew
--   ML.VALIDATE_DATA_DRIFT:https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-validate-data-drift
--   ML.TFDV_DESCRIBE:      https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-tfdv-describe
--   ML.TFDV_VALIDATE:      https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-tfdv-validate


-- =============================================================================
-- Setup: train a small scratch model (feeds ML.VALIDATE_DATA_SKEW below)
-- =============================================================================
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.data_quality_scratch_model`
OPTIONS(
  model_type = 'LOGISTIC_REG',
  input_label_cols = ['income_bracket'],
  data_split_method = 'RANDOM',
  data_split_eval_fraction = 0.2
) AS
SELECT age, workclass, education, education_num, marital_status, occupation,
       relationship, race, sex, hours_per_week, native_country, income_bracket
FROM `bigquery-public-data.ml_datasets.census_adult_income`;


-- =============================================================================
-- Example 1: ML.DESCRIBE_DATA -- descriptive stats, numeric and categorical
-- =============================================================================
SELECT name, num_rows, min, max, mean, stddev, median, quantiles
FROM ML.DESCRIBE_DATA(
  TABLE `bigquery-public-data.ml_datasets.census_adult_income`,
  STRUCT(3 AS top_k, 4 AS num_quantiles)
)
WHERE name IN ('age', 'capital_gain');

-- Categorical columns populate `unique`/`top_values` instead of numeric stats.
SELECT name, unique, top_values, num_nulls
FROM ML.DESCRIBE_DATA(
  TABLE `bigquery-public-data.ml_datasets.census_adult_income`,
  STRUCT(3 AS top_k, 4 AS num_quantiles)
)
WHERE name IN ('workclass', 'income_bracket');


-- =============================================================================
-- Example 2: MAJOR GOTCHA (verified live) -- naive LIMIT sampling looks like
-- severe skew even when it's the exact same data source
-- =============================================================================
-- The public census_adult_income table is NOT randomly ordered. Grabbing
-- "the first N rows" with LIMIT (no ORDER BY) silently returns a
-- non-representative slice -- ML.VALIDATE_DATA_SKEW correctly flags the
-- REAL distributional difference this creates, which looks like a skew
-- alarm but is actually a sampling bug, not a real serving-data problem.
SELECT input, metric, ROUND(value, 4) AS value, threshold, is_anomaly
FROM ML.VALIDATE_DATA_SKEW(
  MODEL `PROJECT_ID.DATASET.data_quality_scratch_model`,
  (SELECT age, workclass, education, education_num, marital_status, occupation,
          relationship, race, sex, hours_per_week, native_country
   FROM `bigquery-public-data.ml_datasets.census_adult_income`
   LIMIT 5000)   -- ANTI-PATTERN: no ORDER BY, non-random slice
)
ORDER BY is_anomaly DESC, input;
-- Verified: education_num flags is_anomaly=TRUE with JENSEN_SHANNON_DIVERGENCE
-- ~0.65 (threshold 0.3) -- despite being the exact same underlying table.

-- Fix: sample randomly instead of grabbing "the first N rows."
SELECT input, metric, ROUND(value, 4) AS value, threshold, is_anomaly
FROM ML.VALIDATE_DATA_SKEW(
  MODEL `PROJECT_ID.DATASET.data_quality_scratch_model`,
  (SELECT age, workclass, education, education_num, marital_status, occupation,
          relationship, race, sex, hours_per_week, native_country
   FROM `bigquery-public-data.ml_datasets.census_adult_income`
   WHERE RAND() < 0.15)   -- true random sample
)
ORDER BY is_anomaly DESC, input;
-- Verified: every column's divergence drops to near-zero, correctly
-- reporting no skew -- confirming the earlier alarm was a sampling
-- artifact, not a real problem.


-- =============================================================================
-- Example 3: ML.VALIDATE_DATA_DRIFT -- real drift between two genuinely
-- different populations (not a sampling artifact this time)
-- =============================================================================
SELECT input, metric, ROUND(value, 4) AS value, threshold, is_anomaly
FROM ML.VALIDATE_DATA_DRIFT(
  (SELECT age, education_num, hours_per_week
   FROM `bigquery-public-data.ml_datasets.census_adult_income`
   WHERE RAND() < 0.3),
  (SELECT age, education_num, hours_per_week
   FROM `bigquery-public-data.ml_datasets.census_adult_income`
   WHERE workclass = ' Self-emp-inc'),
  STRUCT(0.1 AS numerical_default_threshold)
);
-- Verified: education_num flags real drift (JS divergence ~0.18 > 0.1
-- threshold) -- incorporated self-employed workers skew toward more
-- education than the general population. A genuine, explainable finding,
-- not a sampling bug.

-- categorical_metric_type: the metric choice changes which features get
-- flagged, at the identical threshold.
SELECT input, metric, ROUND(value, 4) AS value, threshold, is_anomaly
FROM ML.VALIDATE_DATA_DRIFT(
  (SELECT sex, relationship, race
   FROM `bigquery-public-data.ml_datasets.census_adult_income`
   WHERE RAND() < 0.3),
  (SELECT sex, relationship, race
   FROM `bigquery-public-data.ml_datasets.census_adult_income`
   WHERE workclass = ' Self-emp-inc'),
  STRUCT(0.05 AS categorical_default_threshold)
)
ORDER BY input;

SELECT input, metric, ROUND(value, 4) AS value, threshold, is_anomaly
FROM ML.VALIDATE_DATA_DRIFT(
  (SELECT sex, relationship, race
   FROM `bigquery-public-data.ml_datasets.census_adult_income`
   WHERE RAND() < 0.3),
  (SELECT sex, relationship, race
   FROM `bigquery-public-data.ml_datasets.census_adult_income`
   WHERE workclass = ' Self-emp-inc'),
  STRUCT(0.05 AS categorical_default_threshold, 'JENSEN_SHANNON_DIVERGENCE' AS categorical_metric_type)
)
ORDER BY input;
-- Verified: at threshold 0.05, L_INFTY flags race (0.082), relationship
-- (0.300), and sex (0.212) as anomalies. JENSEN_SHANNON_DIVERGENCE flags
-- only relationship (0.073) -- race (0.023) and sex (0.048) drop below
-- threshold. Real, not a documentation footnote: switching metric changes
-- alerting behavior.

-- thresholds: per-column override, independent of the defaults.
SELECT input, metric, ROUND(value, 4) AS value, threshold, is_anomaly
FROM ML.VALIDATE_DATA_DRIFT(
  (SELECT age, race
   FROM `bigquery-public-data.ml_datasets.census_adult_income`
   WHERE RAND() < 0.3),
  (SELECT age, race
   FROM `bigquery-public-data.ml_datasets.census_adult_income`
   WHERE workclass = ' Self-emp-inc'),
  STRUCT([('race', 0.01)] AS thresholds)
)
ORDER BY input;
-- Verified: race's override (threshold=0.01) flags TRUE even though its
-- actual divergence (~0.08) would pass under the categorical_default_threshold
-- =0.3 that age still uses -- lets you tighten/loosen sensitivity per column.


-- =============================================================================
-- Example 4: ML.TFDV_DESCRIBE + ML.TFDV_VALIDATE -- the TFDV-proto tier
-- =============================================================================
-- Emits a TensorFlow Data Validation DatasetFeatureStatisticsList proto as
-- JSON -- same behavior as tfdv.generate_statistics_from_csv, for
-- interop with the tensorflow-data-validation Python library.
SELECT dataset_feature_statistics_list
FROM ML.TFDV_DESCRIBE(
  (SELECT age, education_num, hours_per_week
   FROM `bigquery-public-data.ml_datasets.census_adult_income`
   WHERE RAND() < 0.05)
);

-- ML.TFDV_VALIDATE compares two such protos and returns a TFDV Anomalies
-- proto (also JSON) -- the TFDV-native equivalent of Example 3 above.
WITH base AS (
  SELECT dataset_feature_statistics_list AS stats
  FROM ML.TFDV_DESCRIBE(
    (SELECT age, education_num, hours_per_week
     FROM `bigquery-public-data.ml_datasets.census_adult_income`
     WHERE RAND() < 0.3)
  )
),
compare AS (
  SELECT dataset_feature_statistics_list AS stats
  FROM ML.TFDV_DESCRIBE(
    (SELECT age, education_num, hours_per_week
     FROM `bigquery-public-data.ml_datasets.census_adult_income`
     WHERE workclass = ' Self-emp-inc')
  )
)
SELECT ML.TFDV_VALIDATE(base.stats, compare.stats, 'DRIFT') AS anomalies
FROM base, compare;
-- Same education_num drift signal as Example 3 (~0.18), confirmed by
-- parsing the JSON and inspecting anomalies.drift_skew_info -- expressed as
-- a TFDV Anomalies proto instead of a tabular row -- feed this to
-- tfdv.display_anomalies() in a full TFDV Python environment (see
-- MLOps/Model Monitoring/bqml-model-monitoring-tutorial.ipynb).

-- 'SKEW' mode: the TFDV-native equivalent of ML.VALIDATE_DATA_SKEW --
-- semantically training-vs-serving, works on any two proto statistics
-- regardless of source.
WITH training_stats AS (
  SELECT dataset_feature_statistics_list AS stats
  FROM ML.TFDV_DESCRIBE(
    (SELECT age, education_num, hours_per_week
     FROM `bigquery-public-data.ml_datasets.census_adult_income`
     WHERE RAND() < 0.3)
  )
),
serving_stats AS (
  SELECT dataset_feature_statistics_list AS stats
  FROM ML.TFDV_DESCRIBE(
    (SELECT age, education_num, hours_per_week
     FROM `bigquery-public-data.ml_datasets.census_adult_income`
     WHERE workclass = ' Self-emp-inc')
  )
)
SELECT ML.TFDV_VALIDATE(training_stats.stats, serving_stats.stats, 'SKEW') AS anomalies
FROM training_stats, serving_stats;
-- Verified: identical output structure to 'DRIFT' mode (same
-- drift_skew_info array, same divergence values, ~0.18 for education_num)
-- -- 'SKEW' vs 'DRIFT' mode changes the baseline schema's comparator type
-- (skew_comparator vs drift_comparator) and semantic framing, not the
-- underlying computation.


-- =============================================================================
-- Cleanup
-- =============================================================================
-- DROP MODEL IF EXISTS `PROJECT_ID.DATASET.data_quality_scratch_model`;
