-- DNN Regressor — Progressive SQL Examples (BigQuery ML)
-- =============================================================
-- Regression with CREATE MODEL (model_type = 'DNN_REGRESSOR'), a
-- fully-connected feed-forward neural network trained with TensorFlow
-- inside BigQuery. Walks the full model lifecycle: create -> evaluate ->
-- predict -> explain -> inspect -> preprocess -> hyperparameter-tune.
--
-- Data: bigquery-public-data.ml_datasets.penguins
--       Label: body_mass_g (continuous)
--       Same data + label as models/linear_regression/,
--       models/boosted_tree_regressor/, and models/random_forest_regressor/
--       -- compare r2_score across all four techniques directly.
--       Rows with a NULL label or an invalid sex value ('.') are filtered out.
--
-- Full reference: ../../RESOURCES.md
-- Official docs:
--   CREATE MODEL (DNN):         https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-dnn-models
--   The CREATE MODEL statement: https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create


-- =============================================================================
-- Example 1: CREATE MODEL — train a DNN regressor
-- =============================================================================
-- model_type + input_label_cols are the essentials -- same options as
-- models/dnn_classifier/ minus auto_class_weights (classifier-only).
--
-- GOTCHA (verified, important): on this small (333-row) dataset, with
-- UNSCALED numeric features (culmen_length_mm, culmen_depth_mm,
-- flipper_length_mm) and the default learn_rate=0.001, this model is badly
-- broken: r2_score ~ -27.5 (far worse than just predicting the mean).
-- early_stop=TRUE (the default) stops training after only 2 iterations --
-- ML.TRAINING_INFO (Example 6) shows eval_loss barely moves between them.
-- The network has taken only ~2 gradient steps total and never gets
-- anywhere close to converging. See Example 7 for the fix -- and note that
-- scaling the features ALONE does not fix it (verified); the binding
-- constraint here is the learn_rate, not just feature scale. Contrast with
-- models/dnn_classifier/, where the same unscaled setup still trains to a
-- competitive roc_auc.
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.dnn_regressor_penguins`
OPTIONS(
  model_type = 'DNN_REGRESSOR',
  input_label_cols = ['body_mass_g'],
  hidden_units = [64, 32],
  activation_fn = 'RELU',
  optimizer = 'ADAM',
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
-- This is the real, reproducible output of the baseline config, not a typo.
SELECT *
FROM ML.EVALUATE(MODEL `PROJECT_ID.DATASET.dnn_regressor_penguins`);


-- =============================================================================
-- Example 3: ML.PREDICT — predicted body mass
-- =============================================================================
SELECT
  predicted_body_mass_g,
  species,
  flipper_length_mm
FROM ML.PREDICT(
  MODEL `PROJECT_ID.DATASET.dnn_regressor_penguins`,
  (SELECT * FROM `bigquery-public-data.ml_datasets.penguins`
   WHERE body_mass_g IS NOT NULL AND sex IN ('MALE', 'FEMALE') LIMIT 10)
);


-- =============================================================================
-- Example 4: ML.EXPLAIN_PREDICT — per-row feature attributions
-- =============================================================================
SELECT
  predicted_body_mass_g,
  top_feature_attributions
FROM ML.EXPLAIN_PREDICT(
  MODEL `PROJECT_ID.DATASET.dnn_regressor_penguins`,
  (SELECT * FROM `bigquery-public-data.ml_datasets.penguins`
   WHERE body_mass_g IS NOT NULL AND sex IN ('MALE', 'FEMALE') LIMIT 5),
  STRUCT(5 AS top_k_features)
);


-- =============================================================================
-- Example 5: ML.GLOBAL_EXPLAIN — overall feature importance
-- =============================================================================
-- No ML.FEATURE_IMPORTANCE (tree-only) or ML.WEIGHTS/ML.ADVANCED_WEIGHTS (no
-- coefficients) for DNN models -- Integrated Gradients is the only
-- explainability mechanism, same as models/dnn_classifier/.
SELECT *
FROM ML.GLOBAL_EXPLAIN(MODEL `PROJECT_ID.DATASET.dnn_regressor_penguins`)
ORDER BY attribution DESC;


-- =============================================================================
-- Example 6: ML.FEATURE_INFO and ML.TRAINING_INFO — introspect the model
-- =============================================================================
SELECT *
FROM ML.FEATURE_INFO(MODEL `PROJECT_ID.DATASET.dnn_regressor_penguins`);

-- TRAINING_INFO: verified -- only 2 iterations run before early_stop kicks
-- in, and eval_loss (in raw grams^2, so values in the tens of millions) is
-- nearly flat between them. This is the training-side evidence for the
-- Example 1/2 gotcha.
SELECT
  iteration,
  loss,
  eval_loss,
  learning_rate,
  duration_ms
FROM ML.TRAINING_INFO(MODEL `PROJECT_ID.DATASET.dnn_regressor_penguins`)
ORDER BY iteration;


-- =============================================================================
-- Example 7: The fix — TRANSFORM (scaling) + a higher learn_rate
-- =============================================================================
-- RESOURCES.md best practice says to normalize numeric features for DNN
-- training -- true in general, but VERIFIED INSUFFICIENT alone here:
-- scaling with the default learn_rate=0.001 still gives r2_score ~ -27.4,
-- barely different from Example 1. The actual fix on this small dataset is
-- a much higher learn_rate (0.05 vs. the 0.001 default) -- with scaling,
-- more headroom (max_iterations=30), and the higher learn_rate together,
-- r2_score reaches 0.86 -- competitive with Linear Regression (~0.88),
-- though still behind Boosted Tree Regressor (~0.97) on this dataset.
-- Verified across two full Restart & Run All passes: this result
-- (r2_score = 0.861626) reproduces bit-for-bit -- training under a fixed
-- model name is not a fresh random draw each time (see Example 8 for the
-- same behavior in hyperparameter tuning). Takeaway: for small datasets,
-- the default learn_rate can be far too conservative -- early_stop then
-- locks the model in near its random initialization before it has taken
-- enough meaningful gradient steps to converge.
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.dnn_regressor_penguins_transform`
TRANSFORM(
  ML.STANDARD_SCALER(culmen_length_mm) OVER() AS culmen_length_mm,
  ML.STANDARD_SCALER(culmen_depth_mm) OVER() AS culmen_depth_mm,
  ML.STANDARD_SCALER(flipper_length_mm) OVER() AS flipper_length_mm,
  species, island, sex, body_mass_g
)
OPTIONS(
  model_type = 'DNN_REGRESSOR',
  input_label_cols = ['body_mass_g'],
  hidden_units = [64, 32],
  activation_fn = 'RELU',
  optimizer = 'ADAM',
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

-- Confirm the fix with ML.EVALUATE -- this is the number the Example 7
-- comment above promises. Verified across two full Restart & Run All
-- passes: r2_score reproduces bit-for-bit (0.861626 both times) -- like
-- Example 8's tuning search, DNN training under a fixed model name is
-- fully reproducible here, not a fresh random draw each time.
SELECT *
FROM ML.EVALUATE(MODEL `PROJECT_ID.DATASET.dnn_regressor_penguins_transform`);

-- Predict on RAW rows -- scaling is applied automatically inside the model.
SELECT predicted_body_mass_g, species, flipper_length_mm
FROM ML.PREDICT(
  MODEL `PROJECT_ID.DATASET.dnn_regressor_penguins_transform`,
  (SELECT * FROM `bigquery-public-data.ml_datasets.penguins`
   WHERE body_mass_g IS NOT NULL AND sex IN ('MALE', 'FEMALE') LIMIT 5)
);


-- =============================================================================
-- Example 8: Hyperparameter tuning — NUM_TRIALS + HPARAM_CANDIDATES + HPARAM_RANGE
-- =============================================================================
-- hidden_units is only tunable via HPARAM_CANDIDATES, and each candidate is a
-- STRUCT wrapping the whole layer-sizes array (ARRAY<STRUCT<ARRAY<INT64>>>)
-- -- verified working syntax below. learn_rate is tunable via HPARAM_RANGE --
-- given Example 7's finding, tuning learn_rate directly is exactly the
-- right lever for this dataset. Keep num_trials small; DNN training is
-- expensive (see Example 1).
--
-- GOTCHA (verified across two full runs of this exact model name): the
-- search is REPRODUCIBLE, not random. Retraining dnn_regressor_penguins_tuned
-- twice (identical SQL, no explicit seed anywhere) produced bit-for-bit
-- identical trial hyperparameters both times -- the same 4 sampled
-- learn_rate values to 17 significant digits, the same optimal trial
-- (learn_rate~0.0275, r2_score~0.87). This suggests BigQuery ML's search
-- order is tied to something about the model's identity (e.g. its resource
-- name) rather than true run-time randomness. A separate ad-hoc validation
-- model with a DIFFERENT name but the identical search-space config sampled
-- a completely different, worse set of learn_rate values (0.001-0.008,
-- stuck at r2_score ~ -27) -- so don't assume a hyperparameter search that
-- worked (or failed) for one model name will transfer if you rename or
-- duplicate the CREATE MODEL statement.
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.dnn_regressor_penguins_tuned`
TRANSFORM(
  ML.STANDARD_SCALER(culmen_length_mm) OVER() AS culmen_length_mm,
  ML.STANDARD_SCALER(culmen_depth_mm) OVER() AS culmen_depth_mm,
  ML.STANDARD_SCALER(flipper_length_mm) OVER() AS flipper_length_mm,
  species, island, sex, body_mass_g
)
OPTIONS(
  model_type = 'DNN_REGRESSOR',
  input_label_cols = ['body_mass_g'],
  num_trials = 4,
  max_parallel_trials = 2,
  hparam_tuning_objectives = ['r2_score'],
  hidden_units = HPARAM_CANDIDATES([STRUCT([64, 32]), STRUCT([32, 16])]),
  learn_rate = HPARAM_RANGE(0.001, 0.1)
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
FROM ML.TRIAL_INFO(MODEL `PROJECT_ID.DATASET.dnn_regressor_penguins_tuned`)
ORDER BY r2_score DESC;


-- =============================================================================
-- Cleanup
-- =============================================================================
-- DROP MODEL IF EXISTS `PROJECT_ID.DATASET.dnn_regressor_penguins`;
-- DROP MODEL IF EXISTS `PROJECT_ID.DATASET.dnn_regressor_penguins_transform`;
-- DROP MODEL IF EXISTS `PROJECT_ID.DATASET.dnn_regressor_penguins_tuned`;
