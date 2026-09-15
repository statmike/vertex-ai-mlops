-- Model Monitoring — Progressive SQL Examples (BigQuery ML model-free functions)
-- =============================================================
-- Four functions for training/serving skew and data-drift monitoring.
-- Basic tier: ML.VALIDATE_DATA_SKEW, ML.VALIDATE_DATA_DRIFT (tabular
-- output, anomaly flags). Advanced/TFDV-compatible tier: ML.TFDV_DESCRIBE,
-- ML.TFDV_VALIDATE (emit/consume a TensorFlow DatasetFeatureStatisticsList
-- proto as JSON). None require a connection.
--
-- GOTCHA these functions are model-light but NOT the same as
-- ML.DETECT_ANOMALIES: this notebook is about DATASET-level distribution
-- shift (comparing whole datasets/time windows to each other or to stored
-- training stats). ML.DETECT_ANOMALIES (see models/kmeans/, models/pca/,
-- models/autoencoder/, models/arima_plus/, models/arima_plus_xreg/) is
-- about ROW-level outliers within one dataset. Different concept, similar
-- name.
--
-- These functions all answer "has this dataset CHANGED." The prior question
-- -- what is in this dataset at all -- is ../exploration/, where
-- ML.DESCRIBE_DATA profiles the columns and ML.CORRELATION measures what
-- moves with the target. Profile there, monitor here.
--
-- Data: bigquery-public-data.ml_datasets.census_adult_income (same dataset
--       as models/logistic_regression/)
--
-- Full reference: ../../RESOURCES.md
-- Official docs:
--   ML.VALIDATE_DATA_SKEW: https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-validate-data-skew
--   ML.VALIDATE_DATA_DRIFT:https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-validate-data-drift
--   ML.TFDV_DESCRIBE:      https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-tfdv-describe
--   ML.TFDV_VALIDATE:      https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-tfdv-validate


-- =============================================================================
-- Setup: train a small scratch model (feeds ML.VALIDATE_DATA_SKEW below)
-- =============================================================================
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.model_monitoring_scratch_model`
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
-- Example 1: MAJOR GOTCHA (verified live) -- naive LIMIT sampling looks like
-- severe skew even when it's the exact same data source
-- =============================================================================
-- The public census_adult_income table is NOT randomly ordered. Grabbing
-- "the first N rows" with LIMIT (no ORDER BY) silently returns a
-- non-representative slice -- ML.VALIDATE_DATA_SKEW correctly flags the
-- REAL distributional difference this creates, which looks like a skew
-- alarm but is actually a sampling bug, not a real serving-data problem.
SELECT input, metric, ROUND(value, 4) AS value, threshold, is_anomaly
FROM ML.VALIDATE_DATA_SKEW(
  MODEL `PROJECT_ID.DATASET.model_monitoring_scratch_model`,
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
  MODEL `PROJECT_ID.DATASET.model_monitoring_scratch_model`,
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
-- Example 2: ML.VALIDATE_DATA_DRIFT -- real drift between two genuinely
-- different populations (not a sampling artifact this time)
-- =============================================================================
-- Both populations are WHERE clauses on workclass, so they are disjoint and
-- deterministic -- the same two sets of rows on every run. Example 4 below
-- reproduces these exact values by hand, which a RAND() sample could not
-- support across two separate queries.
SELECT input, metric, ROUND(value, 4) AS value, threshold, is_anomaly
FROM ML.VALIDATE_DATA_DRIFT(
  (SELECT age, education_num, hours_per_week
   FROM `bigquery-public-data.ml_datasets.census_adult_income`
   WHERE workclass != ' Self-emp-inc'),
  (SELECT age, education_num, hours_per_week
   FROM `bigquery-public-data.ml_datasets.census_adult_income`
   WHERE workclass = ' Self-emp-inc'),
  STRUCT(0.1 AS numerical_default_threshold)
);
-- Verified: age 0.0811 (FALSE), education_num 0.1813 (TRUE, above the 0.1
-- threshold), hours_per_week 0.0954 (FALSE) -- incorporated self-employed
-- workers do skew toward more education than everyone else. The direction is
-- real; Example 4 shows the magnitude is an artifact of how the numeric
-- metric is computed.

-- categorical_metric_type: the metric choice changes which features get
-- flagged, at the identical threshold.
SELECT input, metric, ROUND(value, 4) AS value, threshold, is_anomaly
FROM ML.VALIDATE_DATA_DRIFT(
  (SELECT sex, relationship, race
   FROM `bigquery-public-data.ml_datasets.census_adult_income`
   WHERE workclass != ' Self-emp-inc'),
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
   WHERE workclass != ' Self-emp-inc'),
  (SELECT sex, relationship, race
   FROM `bigquery-public-data.ml_datasets.census_adult_income`
   WHERE workclass = ' Self-emp-inc'),
  STRUCT(0.05 AS categorical_default_threshold, 'JENSEN_SHANNON_DIVERGENCE' AS categorical_metric_type)
)
ORDER BY input;
-- Verified: at threshold 0.05, L_INFTY flags race (0.0804), relationship
-- (0.3097), and sex (0.2173) as anomalies. JENSEN_SHANNON_DIVERGENCE flags
-- only relationship (0.0792) -- race (0.0244) and sex (0.0497) drop below
-- threshold, sex by three ten-thousandths. Real, not a documentation
-- footnote: switching metric redraws the alert boundary.

-- thresholds: per-column override, independent of the defaults.
SELECT input, metric, ROUND(value, 4) AS value, threshold, is_anomaly
FROM ML.VALIDATE_DATA_DRIFT(
  (SELECT age, race
   FROM `bigquery-public-data.ml_datasets.census_adult_income`
   WHERE workclass != ' Self-emp-inc'),
  (SELECT age, race
   FROM `bigquery-public-data.ml_datasets.census_adult_income`
   WHERE workclass = ' Self-emp-inc'),
  STRUCT([('race', 0.01)] AS thresholds)
)
ORDER BY input;
-- Verified: race's override (threshold=0.01) flags TRUE even though its
-- L_INFTY of 0.0804 would pass comfortably under the default of 0.3 that age
-- (0.0811) still uses -- lets you tighten/loosen sensitivity per column.


-- =============================================================================
-- Example 3: ML.TFDV_DESCRIBE + ML.TFDV_VALIDATE -- the TFDV-proto tier
-- =============================================================================
-- Emits a TensorFlow Data Validation DatasetFeatureStatisticsList proto as
-- JSON -- same behavior as tfdv.generate_statistics_from_csv, for
-- interop with the tensorflow-data-validation Python library.
SELECT dataset_feature_statistics_list
FROM ML.TFDV_DESCRIBE(
  (SELECT age, education_num, hours_per_week
   FROM `bigquery-public-data.ml_datasets.census_adult_income`
   WHERE workclass != ' Self-emp-inc')
);

-- ML.TFDV_VALIDATE compares two such protos and returns a TFDV Anomalies
-- proto (also JSON) -- the TFDV-native equivalent of Example 2 above.
WITH base AS (
  SELECT dataset_feature_statistics_list AS stats
  FROM ML.TFDV_DESCRIBE(
    (SELECT age, education_num, hours_per_week
     FROM `bigquery-public-data.ml_datasets.census_adult_income`
     WHERE workclass != ' Self-emp-inc')
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
-- Same education_num drift signal as Example 2 (0.181256), confirmed by
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
     WHERE workclass != ' Self-emp-inc')
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
-- drift_skew_info array, same divergence values, 0.181256 for education_num)
-- -- 'SKEW' vs 'DRIFT' mode changes the baseline schema's comparator type
-- (skew_comparator vs drift_comparator) and semantic framing, not the
-- underlying computation.


-- =============================================================================
-- Example 4: what a numeric drift value is actually computed from
-- =============================================================================
-- The categorical metrics are statistics of the data: L_INFTY is the largest
-- absolute difference in category proportion, and Jensen-Shannon divergence
-- (base-2 logs, no square root) is the average of the two KL divergences from
-- the mixture distribution. Both reproduce by hand, exactly.
--
-- The numeric metric is not. It is the Jensen-Shannon divergence of two
-- ten-bucket equal-width histograms -- and each input's bucket edges span
-- that input's own MIN to its own MAX. When the two ranges differ, the grids
-- are offset, the histograms are realigned onto the union of both edge sets
-- assuming uniform density inside a bucket, and the realignment manufactures
-- a difference the values themselves do not hold.
--
-- The ranges that set those edges:
SELECT
  workclass = ' Self-emp-inc' AS is_compare,
  COUNT(*) AS n,
  MIN(education_num) AS min_education_num,
  MAX(education_num) AS max_education_num
FROM `bigquery-public-data.ml_datasets.census_adult_income`
GROUP BY is_compare
ORDER BY is_compare;
-- Verified: 31,445 base rows spanning 1 to 16, and 1,116 comparison rows
-- spanning 2 to 16. Ten buckets over 1..16 is 1.5 wide; ten over 2..16 is
-- 1.4 wide. The two grids share exactly one edge.

-- Add one row holding a value the base population already has 51 of, chosen
-- only so the two ranges match, and the alarm clears.
SELECT input, ROUND(value, 6) AS value, threshold, is_anomaly
FROM ML.VALIDATE_DATA_DRIFT(
  (SELECT education_num
   FROM `bigquery-public-data.ml_datasets.census_adult_income`
   WHERE workclass != ' Self-emp-inc'),
  (SELECT education_num
   FROM `bigquery-public-data.ml_datasets.census_adult_income`
   WHERE workclass = ' Self-emp-inc'
   UNION ALL
   SELECT 1),
  STRUCT(0.1 AS numerical_default_threshold)
);
-- Verified: 0.181256 / is_anomaly=TRUE becomes 0.036175 / is_anomaly=FALSE,
-- from one added row in 1,116. The row is not an outlier -- it matters only
-- because it is the comparison population's new minimum, which re-cuts all
-- ten bucket edges onto the base population's.
--
-- This is TFDV semantics, not a bug: the metric is defined on the statistics
-- proto rather than on the data, and the proto's histogram is a fixed-size
-- summary. Three properties combine -- ten buckets regardless of cardinality,
-- per-dataset edges, and uniform density assumed inside a bucket.
--
-- Three consequences, in increasing order of effort:
--   1. On categorical columns, both metrics are statistics of the data. No
--      histogram is involved. Read them as they come.
--   2. A numeric drift value is only meaningful alongside the two ranges it
--      was computed from -- ML.DESCRIBE_DATA's min/max in ../exploration/ is
--      the cheapest way to see them.
--   3. Where a numeric column's range moves between windows for reasons that
--      are not drift, bucketize it yourself (ML.BUCKETIZE with fixed split
--      points, or a CASE) and monitor the bucket label as a categorical
--      column. Then the edges are yours and identical in every window.
--
-- The notebook (model_monitoring.ipynb, Step 5) reproduces all of this
-- numerically: both categorical metrics by hand to the last bit, the
-- histograms pulled out of the ML.TFDV_DESCRIBE proto, and BigQuery's three
-- numeric values reproduced from them.


-- =============================================================================
-- Cleanup
-- =============================================================================
-- DROP MODEL IF EXISTS `PROJECT_ID.DATASET.model_monitoring_scratch_model`;
