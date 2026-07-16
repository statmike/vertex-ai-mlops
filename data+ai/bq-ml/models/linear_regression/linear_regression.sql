-- Linear Regression — Progressive SQL Examples (BigQuery ML)
-- =============================================================
-- Regression with CREATE MODEL (model_type = 'LINEAR_REG').
-- Walks the full model lifecycle: create -> evaluate -> predict ->
-- explain -> inspect weights -> in-model preprocessing ->
-- hyperparameter-tune.
--
-- Data: bigquery-public-data.ml_datasets.penguins
--       Label: body_mass_g (continuous)
--       Rows with a NULL label or an invalid sex value ('.') are filtered out.
--
-- Full reference: ../../RESOURCES.md
-- Official docs:
--   CREATE MODEL (GLM: linear & logistic reg): https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-glm
--   The CREATE MODEL statement:                https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create


-- =============================================================================
-- Example 1: CREATE MODEL — train a linear regression model
-- =============================================================================
-- model_type + input_label_cols are the essentials. AUTO_SPLIT holds out a
-- portion of rows for evaluation; enable_global_explain is required for
-- ML.GLOBAL_EXPLAIN later.
--
-- category_encoding_method = 'DUMMY_ENCODING' drops one baseline category per
-- categorical feature instead of one-hot-encoding all of them. This matters
-- for ML.WEIGHTS (Example 6): with the default ONE_HOT_ENCODING, categorical
-- dummies + the intercept are collinear (rank-deficient), so individual
-- category_weights are NOT uniquely identified -- re-running CREATE MODEL
-- with a different random AUTO_SPLIT can swing a category's weight by
-- thousands of grams, even though predictions stay stable. DUMMY_ENCODING
-- fixes this: one category per feature gets a pinned weight of 0.0 (the
-- baseline), and every other category's weight is a stable, well-defined
-- delta from it.
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.linear_regression_penguins`
OPTIONS(
  model_type = 'LINEAR_REG',
  input_label_cols = ['body_mass_g'],
  data_split_method = 'AUTO_SPLIT',
  category_encoding_method = 'DUMMY_ENCODING',
  enable_global_explain = TRUE
) AS
SELECT
  species, island, culmen_length_mm, culmen_depth_mm, flipper_length_mm, sex, body_mass_g
FROM `bigquery-public-data.ml_datasets.penguins`
WHERE body_mass_g IS NOT NULL AND sex IN ('MALE', 'FEMALE');


-- =============================================================================
-- Example 2: ML.EVALUATE — regression metrics
-- =============================================================================
-- Mean absolute/squared error, R^2, and explained variance on the eval split.
SELECT *
FROM ML.EVALUATE(MODEL `PROJECT_ID.DATASET.linear_regression_penguins`);


-- =============================================================================
-- Example 3: ML.PREDICT — predicted body mass
-- =============================================================================
SELECT
  predicted_body_mass_g,
  species,
  flipper_length_mm
FROM ML.PREDICT(
  MODEL `PROJECT_ID.DATASET.linear_regression_penguins`,
  (SELECT * FROM `bigquery-public-data.ml_datasets.penguins`
   WHERE body_mass_g IS NOT NULL AND sex IN ('MALE', 'FEMALE') LIMIT 10)
);


-- =============================================================================
-- Example 4: ML.EXPLAIN_PREDICT — per-row feature attributions
-- =============================================================================
-- Shows which features pushed each individual prediction up or down.
SELECT
  predicted_body_mass_g,
  top_feature_attributions
FROM ML.EXPLAIN_PREDICT(
  MODEL `PROJECT_ID.DATASET.linear_regression_penguins`,
  (SELECT * FROM `bigquery-public-data.ml_datasets.penguins`
   WHERE body_mass_g IS NOT NULL AND sex IN ('MALE', 'FEMALE') LIMIT 5),
  STRUCT(5 AS top_k_features)
);


-- =============================================================================
-- Example 5: ML.GLOBAL_EXPLAIN — overall feature importance
-- =============================================================================
-- Requires enable_global_explain = TRUE at CREATE MODEL time (see Example 1).
SELECT *
FROM ML.GLOBAL_EXPLAIN(MODEL `PROJECT_ID.DATASET.linear_regression_penguins`)
ORDER BY attribution DESC;


-- =============================================================================
-- Example 6: ML.WEIGHTS — model coefficients
-- =============================================================================
-- Unlike classifiers, LINEAR_REG's weights are directly interpretable: e.g.
-- "each additional mm of flipper length adds ~16g of predicted body mass."
-- Numeric features get a single `weight`; categorical features expand into
-- `category_weights`. With DUMMY_ENCODING (see Example 1), one category per
-- feature is the pinned baseline (weight 0.0) and the rest are stable deltas
-- from it.
SELECT *
FROM ML.WEIGHTS(MODEL `PROJECT_ID.DATASET.linear_regression_penguins`);


-- =============================================================================
-- Example 7: ML.FEATURE_INFO and ML.TRAINING_INFO — introspect the model
-- =============================================================================
-- FEATURE_INFO: per-feature statistics seen during training.
SELECT *
FROM ML.FEATURE_INFO(MODEL `PROJECT_ID.DATASET.linear_regression_penguins`);

-- TRAINING_INFO: per-iteration loss curve. For small/unregularized problems
-- like this one, BQML auto-selects the NORMAL_EQUATION solver, which trains
-- in a single closed-form pass -- expect exactly one row with no eval_loss.
SELECT
  iteration,
  loss,
  eval_loss,
  learning_rate,
  duration_ms
FROM ML.TRAINING_INFO(MODEL `PROJECT_ID.DATASET.linear_regression_penguins`)
ORDER BY iteration;


-- =============================================================================
-- Example 8: In-model preprocessing with the TRANSFORM clause
-- =============================================================================
-- TRANSFORM applies preprocessing that is saved with the model and reapplied
-- automatically at predict time -- no need to repeat it in ML.PREDICT.
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.linear_regression_penguins_transform`
TRANSFORM(
  ML.STANDARD_SCALER(culmen_length_mm) OVER() AS culmen_length_mm,
  ML.STANDARD_SCALER(flipper_length_mm) OVER() AS flipper_length_mm,
  species, island, sex, body_mass_g
)
OPTIONS(
  model_type = 'LINEAR_REG',
  input_label_cols = ['body_mass_g']
) AS
SELECT species, island, culmen_length_mm, flipper_length_mm, sex, body_mass_g
FROM `bigquery-public-data.ml_datasets.penguins`
WHERE body_mass_g IS NOT NULL AND sex IN ('MALE', 'FEMALE');


-- =============================================================================
-- Example 9: Hyperparameter tuning — NUM_TRIALS + HPARAM_RANGE
-- =============================================================================
-- BigQuery ML runs multiple trials over the search space and keeps the best
-- model by the tuning objective. Inspect trials with ML.TRIAL_INFO.
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.linear_regression_penguins_tuned`
OPTIONS(
  model_type = 'LINEAR_REG',
  input_label_cols = ['body_mass_g'],
  num_trials = 10,
  max_parallel_trials = 2,
  hparam_tuning_objectives = ['r2_score'],
  l1_reg = HPARAM_RANGE(0, 10),
  l2_reg = HPARAM_RANGE(0, 10)
) AS
SELECT
  species, island, culmen_length_mm, culmen_depth_mm, flipper_length_mm, sex, body_mass_g
FROM `bigquery-public-data.ml_datasets.penguins`
WHERE body_mass_g IS NOT NULL AND sex IN ('MALE', 'FEMALE');

-- Inspect each trial's hyperparameters and objective score.
SELECT
  trial_id,
  hyperparameters,
  hparam_tuning_evaluation_metrics.r2_score AS r2_score,
  is_optimal
FROM ML.TRIAL_INFO(MODEL `PROJECT_ID.DATASET.linear_regression_penguins_tuned`)
ORDER BY r2_score DESC;


-- =============================================================================
-- Cleanup
-- =============================================================================
-- DROP MODEL IF EXISTS `PROJECT_ID.DATASET.linear_regression_penguins`;
-- DROP MODEL IF EXISTS `PROJECT_ID.DATASET.linear_regression_penguins_transform`;
-- DROP MODEL IF EXISTS `PROJECT_ID.DATASET.linear_regression_penguins_tuned`;
