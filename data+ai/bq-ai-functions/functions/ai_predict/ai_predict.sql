-- AI.PREDICT — Progressive SQL Examples
-- ======================================
-- Table-valued function that performs regression and classification on
-- structured data using TabFM, Google's pre-trained tabular foundation model.
-- Pass a training input and a prediction input in the same query — there is no
-- CREATE MODEL step, no training job, and no model artifact left behind.
--
-- No connection, no CREATE MODEL, no ObjectRef required.
--
-- Signature: AI.PREDICT(
--              { TABLE TRAINING_TABLE | (TRAINING_QUERY) },
--              { TABLE PREDICTION_TABLE | (PREDICTION_QUERY) }
--              [, label_col => 'LABEL_COL' ]
--            )
-- Returns: the prediction input's columns plus
--   predicted_<label>        — regression value, or the predicted class
--   predicted_<label>_probs  — classification only:
--                              ARRAY<STRUCT<label STRING, prob FLOAT64>>
-- Note: the task type follows the label column's type. STRING or BOOL runs
--   classification; INT64, FLOAT64, NUMERIC or BIGNUMERIC runs regression.
--   label_col defaults to 'label'.
-- Limits: at most 20 feature columns and at most 10 classes. Feature and label
--   columns must be STRING, BOOL, INT64, FLOAT64, NUMERIC or BIGNUMERIC.
--   Preview as of 2026-09-01.
--
-- Full reference: ../../RESOURCES.md
-- Official docs: https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-predict
--
-- Companion: AI.EVALUATE's TabFM branch takes the same two inputs and returns
-- accuracy metrics instead of predictions — see ../ai_evaluate/.


-- =============================================================================
-- Setup: A deterministic train/test split
-- =============================================================================
-- Every example hashes the whole row with FARM_FINGERPRINT(TO_JSON_STRING(p)),
-- keeping buckets 0-7 for training and 8-9 as holdout. The official examples
-- use RAND() <= 0.8 inside a CTE that is referenced twice; BigQuery does not
-- guarantee a CTE is evaluated once, so a row can land in both splits or in
-- neither. Penguins has no primary key, so the same hash doubles as the row_id
-- used to join predictions back to their actual values.
WITH penguins AS (
  SELECT
    p.*,
    FARM_FINGERPRINT(TO_JSON_STRING(p)) AS row_id,
    MOD(ABS(FARM_FINGERPRINT(TO_JSON_STRING(p))), 10) AS split_bucket
  FROM `bigquery-public-data.ml_datasets.penguins` AS p
  WHERE body_mass_g IS NOT NULL
)
SELECT
  COUNT(*) AS rows_total,
  COUNT(DISTINCT row_id) AS distinct_row_ids,
  COUNTIF(split_bucket < 8) AS training_rows,
  COUNTIF(split_bucket >= 8) AS holdout_rows
FROM penguins;


-- =============================================================================
-- Example 1: Regression — predict body mass
-- =============================================================================
-- body_mass_g is FLOAT64, so AI.PREDICT runs a regression and returns
-- predicted_body_mass_g. The prediction input drops the label and carries
-- row_id instead: extra columns in the prediction input pass through to the
-- output, which is what makes the join back to the actual values possible.
WITH penguins AS (
  SELECT
    p.*,
    FARM_FINGERPRINT(TO_JSON_STRING(p)) AS row_id,
    MOD(ABS(FARM_FINGERPRINT(TO_JSON_STRING(p))), 10) AS split_bucket
  FROM `bigquery-public-data.ml_datasets.penguins` AS p
  WHERE body_mass_g IS NOT NULL
),
predictions AS (
  SELECT *
  FROM AI.PREDICT(
    -- Training data: features + label, no row_id
    (SELECT * EXCEPT(row_id, split_bucket) FROM penguins WHERE split_bucket < 8),
    -- Prediction data: features + row_id, label removed
    (SELECT * EXCEPT(row_id, split_bucket, body_mass_g), row_id FROM penguins WHERE split_bucket >= 8),
    label_col => 'body_mass_g')
)
SELECT
  h.species,
  h.island,
  h.body_mass_g AS actual_body_mass_g,
  pr.predicted_body_mass_g,
  ROUND(pr.predicted_body_mass_g - h.body_mass_g, 1) AS error_g
FROM predictions AS pr
JOIN penguins AS h USING (row_id)
ORDER BY h.row_id
LIMIT 10;


-- =============================================================================
-- Example 2: Binary classification — predict sex and read the probabilities
-- =============================================================================
-- A STRING label switches the task to classification. predicted_sex_probs is
-- ARRAY<STRUCT<label STRING, prob FLOAT64>> — CROSS JOIN UNNEST flattens it to
-- one row per class. sex holds MALE, FEMALE and a literal '.' placeholder plus
-- NULLs, so the label needs cleaning first.
WITH penguins AS (
  SELECT
    p.*,
    FARM_FINGERPRINT(TO_JSON_STRING(p)) AS row_id,
    MOD(ABS(FARM_FINGERPRINT(TO_JSON_STRING(p))), 10) AS split_bucket
  FROM `bigquery-public-data.ml_datasets.penguins` AS p
  WHERE sex IN ('MALE', 'FEMALE')
),
predictions AS (
  SELECT *
  FROM AI.PREDICT(
    (SELECT * EXCEPT(row_id, split_bucket) FROM penguins WHERE split_bucket < 8),
    (SELECT * EXCEPT(row_id, split_bucket, sex), row_id FROM penguins WHERE split_bucket >= 8),
    label_col => 'sex')
)
SELECT
  h.species,
  h.body_mass_g,
  h.sex AS actual_sex,
  pr.predicted_sex,
  probs.label AS class_label,
  ROUND(probs.prob, 6) AS class_prob
FROM predictions AS pr
JOIN penguins AS h USING (row_id)
CROSS JOIN UNNEST(pr.predicted_sex_probs) AS probs
ORDER BY h.row_id, class_prob DESC
LIMIT 10;


-- =============================================================================
-- Example 3: Multi-class — predict species, and the 10-class ceiling
-- =============================================================================
-- A scalar subquery over predicted_species_probs pulls the winning class's
-- probability, keeping one row per prediction. Penguin species is very nearly a
-- pure function of the body measurements, so accuracy lands at or near 1.0 —
-- that is a property of this dataset, not evidence about TabFM's accuracy on
-- yours. Read degenerate metrics as a signal to find a harder test set.
WITH penguins AS (
  SELECT
    p.*,
    FARM_FINGERPRINT(TO_JSON_STRING(p)) AS row_id,
    MOD(ABS(FARM_FINGERPRINT(TO_JSON_STRING(p))), 10) AS split_bucket
  FROM `bigquery-public-data.ml_datasets.penguins` AS p
  WHERE body_mass_g IS NOT NULL
),
predictions AS (
  SELECT *
  FROM AI.PREDICT(
    (SELECT * EXCEPT(row_id, split_bucket) FROM penguins WHERE split_bucket < 8),
    (SELECT * EXCEPT(row_id, split_bucket, species), row_id FROM penguins WHERE split_bucket >= 8),
    label_col => 'species')
)
SELECT
  COUNT(*) AS holdout_rows,
  COUNT(DISTINCT h.species) AS classes_in_holdout,
  COUNTIF(pr.predicted_species = h.species) AS correct,
  ROUND(COUNTIF(pr.predicted_species = h.species) / COUNT(*), 4) AS accuracy,
  ROUND(MIN((SELECT prob FROM UNNEST(pr.predicted_species_probs) WHERE label = pr.predicted_species)), 4) AS min_confidence
FROM predictions AS pr
JOIN penguins AS h USING (row_id);

-- Classification is capped at 10 distinct label values. The cap is checked when
-- the query runs, not when it is analyzed, so this passes validation and then
-- fails a few seconds in with:
--   The total different label values cannot exceed 10 for classification task.
--   Error in ai.__predict_train expression
WITH penguins AS (
  SELECT
    p.culmen_length_mm,
    p.culmen_depth_mm,
    p.body_mass_g,
    CAST(CAST(p.flipper_length_mm AS INT64) AS STRING) AS flipper_mm,
    MOD(ABS(FARM_FINGERPRINT(TO_JSON_STRING(p))), 10) AS split_bucket
  FROM `bigquery-public-data.ml_datasets.penguins` AS p
  WHERE flipper_length_mm IS NOT NULL AND body_mass_g IS NOT NULL
)
SELECT *
FROM AI.PREDICT(
  (SELECT * EXCEPT(split_bucket) FROM penguins WHERE split_bucket < 8),
  (SELECT * EXCEPT(split_bucket, flipper_mm) FROM penguins WHERE split_bucket >= 8),
  label_col => 'flipper_mm');


-- =============================================================================
-- Example 4: label_col defaults to a column named label
-- =============================================================================
-- When the training input already has a column literally named label, omit the
-- argument — the two positional table arguments are all AI.PREDICT needs. The
-- output column follows the label name, so it returns as predicted_label.
-- AI.EVALUATE is stricter: its TabFM branch requires label_col even when the
-- column is named label.
WITH penguins AS (
  SELECT
    p.* EXCEPT(body_mass_g),
    p.body_mass_g AS label,
    MOD(ABS(FARM_FINGERPRINT(TO_JSON_STRING(p))), 10) AS split_bucket
  FROM `bigquery-public-data.ml_datasets.penguins` AS p
  WHERE body_mass_g IS NOT NULL
)
SELECT species, island, sex, predicted_label
FROM AI.PREDICT(
  (SELECT * EXCEPT(split_bucket) FROM penguins WHERE split_bucket < 8),
  (SELECT * EXCEPT(split_bucket, label) FROM penguins WHERE split_bucket >= 8))
ORDER BY predicted_label DESC
LIMIT 10;


-- =============================================================================
-- Example 5: The limits — 20 feature columns, and five allowed column types
-- =============================================================================
-- Both limits are enforced while the query is analyzed, so they fail instantly
-- and cost nothing — no model inference runs.
--
-- (a) Penguins has six features; padding to 21 fails with:
--       The number of features 21 exceeds the maximum allowed number of
--       features 20.
--     The documented escalation path is an email to bqml-feedback@google.com.
WITH wide AS (
  SELECT
    p.*,
    culmen_depth_mm * 1 AS extra_feature_01,
    culmen_depth_mm * 2 AS extra_feature_02,
    culmen_depth_mm * 3 AS extra_feature_03,
    culmen_depth_mm * 4 AS extra_feature_04,
    culmen_depth_mm * 5 AS extra_feature_05,
    culmen_depth_mm * 6 AS extra_feature_06,
    culmen_depth_mm * 7 AS extra_feature_07,
    culmen_depth_mm * 8 AS extra_feature_08,
    culmen_depth_mm * 9 AS extra_feature_09,
    culmen_depth_mm * 10 AS extra_feature_10,
    culmen_depth_mm * 11 AS extra_feature_11,
    culmen_depth_mm * 12 AS extra_feature_12,
    culmen_depth_mm * 13 AS extra_feature_13,
    culmen_depth_mm * 14 AS extra_feature_14,
    culmen_depth_mm * 15 AS extra_feature_15
  FROM `bigquery-public-data.ml_datasets.penguins` AS p
  WHERE body_mass_g IS NOT NULL
)
SELECT *
FROM AI.PREDICT(
  (SELECT * FROM wide),
  (SELECT * EXCEPT(body_mass_g) FROM wide),
  label_col => 'body_mass_g');

-- (b) Feature and label columns must be STRING, BOOL, INT64, FLOAT64, NUMERIC
--     or BIGNUMERIC. DATE, TIMESTAMP, BYTES, JSON, GEOGRAPHY, ARRAY and STRUCT
--     are rejected (verified 2026-09-01). A DATE feature fails with:
--       Incompatible table schemas for AI.PREDICT: Column(s) with unsupported
--       types: observed_on.
WITH dated AS (
  SELECT
    p.*,
    DATE_ADD(DATE '2026-01-01', INTERVAL CAST(p.culmen_length_mm AS INT64) DAY) AS observed_on
  FROM `bigquery-public-data.ml_datasets.penguins` AS p
  WHERE body_mass_g IS NOT NULL
)
SELECT *
FROM AI.PREDICT(
  (SELECT * FROM dated),
  (SELECT * EXCEPT(body_mass_g) FROM dated),
  label_col => 'body_mass_g');

-- (c) The workaround: EXTRACT the date into INT64 parts. This is a modeling
--     decision as much as a workaround — year, month and day-of-week are
--     periodic features, while a day offset from a fixed origin is a trend
--     feature. Watch the 20-column budget as you add them.
WITH dated AS (
  SELECT
    p.*,
    DATE_ADD(DATE '2026-01-01', INTERVAL CAST(p.culmen_length_mm AS INT64) DAY) AS observed_on
  FROM `bigquery-public-data.ml_datasets.penguins` AS p
  WHERE body_mass_g IS NOT NULL
),
encoded AS (
  SELECT
    * EXCEPT(observed_on),
    EXTRACT(YEAR FROM observed_on) AS observed_year,
    EXTRACT(MONTH FROM observed_on) AS observed_month,
    EXTRACT(DAYOFWEEK FROM observed_on) AS observed_dayofweek,
    MOD(ABS(FARM_FINGERPRINT(TO_JSON_STRING(dated))), 10) AS split_bucket
  FROM dated
)
SELECT species, observed_year, observed_month, observed_dayofweek, predicted_body_mass_g
FROM AI.PREDICT(
  (SELECT * EXCEPT(split_bucket) FROM encoded WHERE split_bucket < 8),
  (SELECT * EXCEPT(split_bucket, body_mass_g) FROM encoded WHERE split_bucket >= 8),
  label_col => 'body_mass_g')
ORDER BY predicted_body_mass_g DESC
LIMIT 5;


-- =============================================================================
-- Example 6: Sizing and cost
-- =============================================================================
-- Size: no maximum training-row count is documented. Measured on on-demand
-- slots (2026-09-01), a call fails with "Resources exceeded during query
-- execution: The query could not be executed in the allotted memory" at 10,000
-- training rows; 8,000 rows succeeds in ~94 s and 5,000 rows in ~93 s. That is
-- an observed resource ceiling on one billing configuration, not a documented
-- limit. Treat ~5,000 training rows as the safe working assumption. Every call
-- takes 30-95 s regardless of input size.
--
-- Cost today: during Preview, usage bills in slots on Enterprise and Enterprise
-- Plus editions, or by bytes processed under on-demand pricing.
--
-- Cost from 2026-10-30 (announced, not yet in effect): TabFM in BigQuery moves
-- to token-based pricing — TabFM tokens for the model inference plus the usual
-- slots or bytes processed for the rest of the query. Published formulas:
--   input tokens  = (train_rows * columns + predict_rows * (columns - 1)) * n_ensembles
--   output tokens = predict_rows * n_ensembles
-- at $0.05 / mtok input and $0.20 / mtok output. n_ensembles has no documented
-- value and no argument to control it, so a dollar figure is not computable
-- from the documentation as written. The query below reports the per-pass token
-- counts, i.e. everything above except the n_ensembles multiplier. On or after
-- 2026-10-30, re-check https://docs.cloud.google.com/bigquery/pricing.
--
-- AI.EVALUATE does not reuse an AI.PREDICT result: its TabFM branch takes the
-- same two inputs and runs the same inference again, so running both over one
-- split pays for the model twice.
WITH penguins AS (
  SELECT MOD(ABS(FARM_FINGERPRINT(TO_JSON_STRING(p))), 10) AS split_bucket
  FROM `bigquery-public-data.ml_datasets.penguins` AS p
  WHERE body_mass_g IS NOT NULL
),
sizing AS (
  SELECT
    COUNTIF(split_bucket < 8) AS train_rows,
    COUNTIF(split_bucket >= 8) AS predict_rows,
    7 AS columns_referenced  -- 6 feature columns + the label column
  FROM penguins
)
SELECT
  train_rows,
  predict_rows,
  columns_referenced,
  train_rows * columns_referenced + predict_rows * (columns_referenced - 1) AS input_tokens_per_pass,
  predict_rows AS output_tokens_per_pass
FROM sizing;
