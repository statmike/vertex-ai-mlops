-- AutoML Regressor — Progressive SQL Examples (BigQuery ML)
-- =============================================================
-- Regression with CREATE MODEL (model_type = 'AUTOML_REGRESSOR'). Wraps
-- Vertex AI AutoML Tables: architecture search, feature engineering, and
-- hyperparameter tuning all happen inside the Vertex AI training job -- you
-- supply data and a time budget, not model structure.
--
-- Data: bigquery-public-data.samples.natality (Washington state, 2003)
--       Label: weight_pounds (continuous, birth weight)
--       Rows with a NULL label or NULL mother_age/gestation_weeks/plurality
--       are filtered out. ~80,000 rows after filtering.
--
-- GOTCHA (verified): does NOT use penguins/body_mass_g like the other five
-- regressors (models/linear_regression/, .../boosted_tree_regressor/,
-- .../random_forest_regressor/, .../dnn_regressor/, .../wide_and_deep_regressor/).
-- AutoML Tables enforces a hard minimum of 1,000 training rows -- penguins
-- (~333 rows after filtering) fails immediately with "Input data contains
-- 333 rows. The minimum number of input rows for AutoML Tables models is
-- 1000." regardless of budget_hours. This limitation is not called out in
-- the official CREATE MODEL (AutoML) reference. natality is Google's own
-- canonical BQML regression tutorial dataset and comfortably clears the
-- minimum. (AUTOML_CLASSIFIER is unaffected -- census_adult_income has
-- ~32,000 rows.)
--
-- COST/TIME WARNING: unlike every other model type in this project, this one
-- has real, substantial dollar cost and wall-clock time. Vertex AI AutoML
-- Tabular training is billed at roughly $21.25/node-hour; budget_hours = 1.0
-- (the minimum) is the cheapest possible run. VERIFIED on a real run: wall-
-- clock was 2.25 hours (ML.TRAINING_INFO duration_ms=8,103,600) for a 1-hour
-- budget -- a much larger overrun than the ~50% ceiling Google's docs imply
-- (AUTOML_CLASSIFIER on the same day took ~2.63 hours). Do not re-run
-- CREATE MODEL casually.
--
-- GOTCHA (verified): cigarette_use is NULL for 78,400 of 79,993 rows (98%)
-- in this WA/2003 slice -- not a bug, and consistent with ML.GLOBAL_EXPLAIN
-- ranking it the least-important feature by a wide margin (attribution
-- 0.0016 vs next-lowest 0.030).
--
-- Full reference: ../../RESOURCES.md
-- Official docs:
--   CREATE MODEL (AutoML): https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-automl
--   Vertex AI AutoML Tabular pricing: https://cloud.google.com/vertex-ai/pricing


-- =============================================================================
-- Example 1: CREATE MODEL — train an AutoML Tables regressor
-- =============================================================================
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.automl_regressor_natality`
OPTIONS(
  model_type = 'AUTOML_REGRESSOR',
  input_label_cols = ['weight_pounds'],
  budget_hours = 1.0,
  optimization_objective = 'MINIMIZE_RMSE'
) AS
SELECT
  mother_age, gestation_weeks, plurality, is_male, mother_married, cigarette_use, weight_pounds
FROM `bigquery-public-data.samples.natality`
WHERE year = 2003
  AND mother_residence_state = 'WA'
  AND weight_pounds IS NOT NULL
  AND mother_age IS NOT NULL
  AND gestation_weeks IS NOT NULL
  AND plurality IS NOT NULL;


-- =============================================================================
-- Example 2: ML.EVALUATE — regression metrics
-- =============================================================================
-- Same metric set as LINEAR_REG/BOOSTED_TREE_REGRESSOR/etc: mean_absolute_error,
-- mean_squared_error, mean_squared_log_error, median_absolute_error, r2_score,
-- explained_variance -- computed by AutoML on its own internal test split.
--
-- GOTCHA (verified): median_absolute_error and explained_variance both
-- return exactly 0.0, which does not look genuine (mean_absolute_error,
-- mean_squared_error -- matching ML.TRAINING_INFO's eval_loss exactly --
-- mean_squared_log_error, and r2_score=0.352 all look real/self-consistent).
-- Parallels AUTOML_CLASSIFIER's ML.EVALUATE aggregate-metric anomaly (see
-- that .sql's Example 2) -- some fields in the zero-argument evaluation
-- aggregate for AutoML model types don't appear fully populated. Could not
-- be root-caused further here since the model was already dropped
-- (Cleanup) by the time this was reviewed -- prefer mean_squared_error/
-- r2_score/mean_absolute_error, which look trustworthy.
SELECT *
FROM ML.EVALUATE(MODEL `PROJECT_ID.DATASET.automl_regressor_natality`);


-- =============================================================================
-- Example 3: ML.PREDICT
-- =============================================================================
SELECT
  predicted_weight_pounds,
  mother_age, gestation_weeks, plurality
FROM ML.PREDICT(
  MODEL `PROJECT_ID.DATASET.automl_regressor_natality`,
  (SELECT mother_age, gestation_weeks, plurality, is_male, mother_married, cigarette_use, weight_pounds
   FROM `bigquery-public-data.samples.natality`
   WHERE year = 2003 AND mother_residence_state = 'WA'
     AND weight_pounds IS NOT NULL AND mother_age IS NOT NULL
     AND gestation_weeks IS NOT NULL AND plurality IS NOT NULL
   LIMIT 10)
);


-- =============================================================================
-- Example 4: ML.GLOBAL_EXPLAIN — model-level feature attributions
-- =============================================================================
-- Unlike LINEAR_REG/BOOSTED_TREE_*, no enable_global_explain option is
-- needed -- AutoML produces attributions automatically. Only model-level
-- (not per-prediction) explanations are available: ML.EXPLAIN_PREDICT is
-- NOT supported for this model type (see Example 7).
SELECT *
FROM ML.GLOBAL_EXPLAIN(MODEL `PROJECT_ID.DATASET.automl_regressor_natality`)
ORDER BY attribution DESC;


-- =============================================================================
-- Example 5: ML.FEATURE_INFO and ML.TRAINING_INFO
-- =============================================================================
SELECT *
FROM ML.FEATURE_INFO(MODEL `PROJECT_ID.DATASET.automl_regressor_natality`);

SELECT *
FROM ML.TRAINING_INFO(MODEL `PROJECT_ID.DATASET.automl_regressor_natality`);


-- =============================================================================
-- Example 6: EXPORT MODEL
-- =============================================================================
-- Writes the trained AutoML model to Cloud Storage for Vertex AI Model
-- Registry / custom serving. Unlike BOOSTED_TREE_*/RANDOM_FOREST_*, AutoML's
-- exported artifact is an opaque ensemble -- there is no single tree/booster
-- file to load and visualize with a local library.
EXPORT MODEL `PROJECT_ID.DATASET.automl_regressor_natality`
OPTIONS (URI = 'gs://BUCKET/bq_ml/automl_regressor/model');


-- =============================================================================
-- Example 7: Functions that do NOT apply to this model type
-- =============================================================================
-- TRANSFORM is not supported for AutoML model types -- do feature
-- engineering in the training SELECT instead.
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.automl_regressor_natality_transform`
TRANSFORM(gestation_weeks, weight_pounds)
OPTIONS(
  model_type = 'AUTOML_REGRESSOR',
  input_label_cols = ['weight_pounds'],
  budget_hours = 1.0
) AS
SELECT gestation_weeks, weight_pounds
FROM `bigquery-public-data.samples.natality`
WHERE year = 2003 AND mother_residence_state = 'WA'
  AND weight_pounds IS NOT NULL AND gestation_weeks IS NOT NULL;

-- ML.WEIGHTS / ML.ADVANCED_WEIGHTS do not apply -- AutoML is not a single
-- linear/tree model with an exposable weight vector.
SELECT *
FROM ML.WEIGHTS(MODEL `PROJECT_ID.DATASET.automl_regressor_natality`);

-- ML.EXPLAIN_PREDICT does not apply -- use ML.GLOBAL_EXPLAIN (Example 4)
-- for feature attributions instead.
SELECT *
FROM ML.EXPLAIN_PREDICT(
  MODEL `PROJECT_ID.DATASET.automl_regressor_natality`,
  (SELECT mother_age, gestation_weeks, plurality, is_male, mother_married, cigarette_use, weight_pounds
   FROM `bigquery-public-data.samples.natality`
   WHERE year = 2003 AND mother_residence_state = 'WA'
     AND weight_pounds IS NOT NULL AND mother_age IS NOT NULL
     AND gestation_weeks IS NOT NULL AND plurality IS NOT NULL
   LIMIT 5)
);

-- User-configurable hyperparameter tuning (num_trials/HPARAM_RANGE/
-- HPARAM_CANDIDATES) is also not supported -- budget_hours is the only lever.
