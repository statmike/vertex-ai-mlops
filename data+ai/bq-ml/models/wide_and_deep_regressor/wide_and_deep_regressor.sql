-- Wide & Deep Regressor — Progressive SQL Examples (BigQuery ML)
-- =============================================================
-- Regression with CREATE MODEL (model_type = 'DNN_LINEAR_COMBINED_REGRESSOR')
-- -- a jointly-trained combination of a WIDE linear model and a DEEP neural
-- network, trained with TensorFlow inside BigQuery. Walks the full model
-- lifecycle: create -> evaluate -> predict -> explain -> inspect ->
-- preprocess -> hyperparameter-tune.
--
-- Data: bigquery-public-data.ml_datasets.penguins
--       Label: body_mass_g (continuous)
--       Same data + label as models/linear_regression/,
--       models/boosted_tree_regressor/, models/random_forest_regressor/,
--       and models/dnn_regressor/ -- compare r2_score across all five
--       techniques directly.
--       Rows with a NULL label or an invalid sex value ('.') are filtered out.
--
-- Full reference: ../../RESOURCES.md
-- Official docs:
--   CREATE MODEL (wide-and-deep): https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-wnd-models
--   The CREATE MODEL statement:   https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create


-- =============================================================================
-- Example 1: CREATE MODEL — train a wide-and-deep regressor
-- =============================================================================
-- Same option shape as models/dnn_regressor/ minus auto_class_weights
-- (classifier-only).
--
-- GOTCHA (verified -- same finding as models/dnn_regressor/, now confirmed
-- for this model type too): on this small (333-row) dataset, with UNSCALED
-- numeric features and the default learn_rate=0.001, this model is badly
-- broken: r2_score ~ -27.4 (far worse than predicting the mean).
-- early_stop=TRUE (the default) stops training after only 2 iterations.
-- See Example 6 for the fix (same recipe as DNN_REGRESSOR: scale the
-- numeric features AND raise learn_rate well above default) -- see
-- models/dnn_regressor/ for the detailed diagnostic walkthrough of why
-- scaling alone is not enough; this notebook applies that lesson directly
-- rather than re-deriving it.
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.wide_deep_regressor_penguins`
OPTIONS(
  model_type = 'DNN_LINEAR_COMBINED_REGRESSOR',
  input_label_cols = ['body_mass_g'],
  hidden_units = [64, 32],
  activation_fn = 'RELU',
  dropout = 0.15,
  max_iterations = 20,
  early_stop = TRUE,
  data_split_method = 'AUTO_SPLIT',
  enable_global_explain = TRUE
) AS
SELECT
  species, island, culmen_length_mm, culmen_depth_mm, flipper_length_mm, sex, body_mass_g
FROM `bigquery-public-data.ml_datasets.penguins`
WHERE body_mass_g IS NOT NULL AND sex IN ('MALE', 'FEMALE');


-- =============================================================================
-- Example 2: ML.EVALUATE — regression metrics
-- =============================================================================
-- Expect a strongly negative r2_score here -- see the Example 1 gotcha.
SELECT *
FROM ML.EVALUATE(MODEL `PROJECT_ID.DATASET.wide_deep_regressor_penguins`);


-- =============================================================================
-- Example 3: ML.PREDICT — predicted body mass
-- =============================================================================
SELECT
  predicted_body_mass_g,
  species,
  flipper_length_mm
FROM ML.PREDICT(
  MODEL `PROJECT_ID.DATASET.wide_deep_regressor_penguins`,
  (SELECT * FROM `bigquery-public-data.ml_datasets.penguins`
   WHERE body_mass_g IS NOT NULL AND sex IN ('MALE', 'FEMALE') LIMIT 10)
);


-- =============================================================================
-- Example 4: ML.EXPLAIN_PREDICT and ML.GLOBAL_EXPLAIN — explainability
-- =============================================================================
-- No ML.FEATURE_IMPORTANCE (tree-only) or ML.WEIGHTS/ML.ADVANCED_WEIGHTS
-- (no coefficients) for this model type -- same as DNN.
SELECT
  predicted_body_mass_g,
  top_feature_attributions
FROM ML.EXPLAIN_PREDICT(
  MODEL `PROJECT_ID.DATASET.wide_deep_regressor_penguins`,
  (SELECT * FROM `bigquery-public-data.ml_datasets.penguins`
   WHERE body_mass_g IS NOT NULL AND sex IN ('MALE', 'FEMALE') LIMIT 5),
  STRUCT(5 AS top_k_features)
);

SELECT *
FROM ML.GLOBAL_EXPLAIN(MODEL `PROJECT_ID.DATASET.wide_deep_regressor_penguins`)
ORDER BY attribution DESC;


-- =============================================================================
-- Example 5: ML.FEATURE_INFO and ML.TRAINING_INFO — introspect the model
-- =============================================================================
SELECT *
FROM ML.FEATURE_INFO(MODEL `PROJECT_ID.DATASET.wide_deep_regressor_penguins`);

-- TRAINING_INFO: verified -- only 2 iterations run before early_stop kicks
-- in, same pattern as models/dnn_regressor/.
SELECT
  iteration,
  loss,
  eval_loss,
  learning_rate,
  duration_ms
FROM ML.TRAINING_INFO(MODEL `PROJECT_ID.DATASET.wide_deep_regressor_penguins`)
ORDER BY iteration;


-- =============================================================================
-- Example 6: The fix — TRANSFORM (scaling) + a higher learn_rate
-- =============================================================================
-- Same fix as models/dnn_regressor/: scale the numeric features AND raise
-- learn_rate to 0.05 (50x the 0.001 default), with more max_iterations
-- headroom. Verified: r2_score reaches 0.79 with the default
-- hidden_units=[64,32] -- a real fix (up from -27.4), though notably
-- lower than DNN Regressor's ~0.86 with the equivalent fix on the same
-- data. Example 7's hyperparameter tuning closes most of that gap by
-- finding a better hidden_units value for this small dataset.
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.wide_deep_regressor_penguins_transform`
TRANSFORM(
  ML.STANDARD_SCALER(culmen_length_mm) OVER() AS culmen_length_mm,
  ML.STANDARD_SCALER(culmen_depth_mm) OVER() AS culmen_depth_mm,
  ML.STANDARD_SCALER(flipper_length_mm) OVER() AS flipper_length_mm,
  species, island, sex, body_mass_g
)
OPTIONS(
  model_type = 'DNN_LINEAR_COMBINED_REGRESSOR',
  input_label_cols = ['body_mass_g'],
  hidden_units = [64, 32],
  activation_fn = 'RELU',
  learn_rate = 0.05,
  dropout = 0.15,
  max_iterations = 30,
  early_stop = TRUE,
  data_split_method = 'AUTO_SPLIT',
  enable_global_explain = TRUE
) AS
SELECT
  species, island, culmen_length_mm, culmen_depth_mm, flipper_length_mm, sex, body_mass_g
FROM `bigquery-public-data.ml_datasets.penguins`
WHERE body_mass_g IS NOT NULL AND sex IN ('MALE', 'FEMALE');

-- Confirm the fix with ML.EVALUATE.
SELECT *
FROM ML.EVALUATE(MODEL `PROJECT_ID.DATASET.wide_deep_regressor_penguins_transform`);

-- Predict on RAW rows -- scaling is applied automatically inside the model.
SELECT predicted_body_mass_g, species, flipper_length_mm
FROM ML.PREDICT(
  MODEL `PROJECT_ID.DATASET.wide_deep_regressor_penguins_transform`,
  (SELECT * FROM `bigquery-public-data.ml_datasets.penguins`
   WHERE body_mass_g IS NOT NULL AND sex IN ('MALE', 'FEMALE') LIMIT 5)
);


-- =============================================================================
-- Example 7: Hyperparameter tuning — NUM_TRIALS + HPARAM_CANDIDATES + HPARAM_RANGE
-- =============================================================================
-- learn_rate and optimizer are NOT tunable for this model type (verified --
-- see models/wide_and_deep_classifier/ Example 10 gotcha), so learn_rate
-- stays fixed at the known-good 0.05 from Example 6 while tuning
-- hidden_units (HPARAM_CANDIDATES) and dropout (HPARAM_RANGE) instead.
-- Verified: all 4 trials succeeded (no failures), all landed in the good
-- region already (since learn_rate is fixed, not searched) -- unlike
-- models/dnn_regressor/'s tuning step, there is no risk here of trials
-- getting stuck in the catastrophic unscaled/low-learn_rate region.
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.wide_deep_regressor_penguins_tuned`
TRANSFORM(
  ML.STANDARD_SCALER(culmen_length_mm) OVER() AS culmen_length_mm,
  ML.STANDARD_SCALER(culmen_depth_mm) OVER() AS culmen_depth_mm,
  ML.STANDARD_SCALER(flipper_length_mm) OVER() AS flipper_length_mm,
  species, island, sex, body_mass_g
)
OPTIONS(
  model_type = 'DNN_LINEAR_COMBINED_REGRESSOR',
  input_label_cols = ['body_mass_g'],
  learn_rate = 0.05,
  num_trials = 4,
  max_parallel_trials = 2,
  hparam_tuning_objectives = ['r2_score'],
  hidden_units = HPARAM_CANDIDATES([STRUCT([64, 32]), STRUCT([32, 16])]),
  dropout = HPARAM_RANGE(0.0, 0.3)
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
FROM ML.TRIAL_INFO(MODEL `PROJECT_ID.DATASET.wide_deep_regressor_penguins_tuned`)
ORDER BY r2_score DESC;


-- =============================================================================
-- Cleanup
-- =============================================================================
-- DROP MODEL IF EXISTS `PROJECT_ID.DATASET.wide_deep_regressor_penguins`;
-- DROP MODEL IF EXISTS `PROJECT_ID.DATASET.wide_deep_regressor_penguins_transform`;
-- DROP MODEL IF EXISTS `PROJECT_ID.DATASET.wide_deep_regressor_penguins_tuned`;
