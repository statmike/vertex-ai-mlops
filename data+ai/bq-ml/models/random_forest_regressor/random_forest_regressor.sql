-- Random Forest Regressor — Progressive SQL Examples (BigQuery ML)
-- =============================================================
-- Regression with CREATE MODEL (model_type = 'RANDOM_FOREST_REGRESSOR'),
-- a bagged ensemble of decision trees trained with XGBoost. Walks the full
-- model lifecycle: create -> evaluate -> predict -> explain -> visualize ->
-- preprocess -> hyperparameter-tune.
--
-- Data: bigquery-public-data.ml_datasets.penguins
--       Label: body_mass_g (continuous)
--       Same data + label as models/linear_regression/ and
--       models/boosted_tree_regressor/ -- compare r2_score across all three
--       techniques directly. Rows with a NULL label or an invalid sex value
--       ('.') are filtered out.
--
-- NOTE: on this small (333-row) dataset, random forest's bagging
-- (num_parallel_tree parallel trees, each on row/column subsamples)
-- underperforms both boosted trees and even plain linear regression --
-- verified: r2_score ~0.74 here vs. ~0.97 for boosted_tree_regressor and
-- ~0.88 for linear_regression on the identical data, even after
-- hyperparameter tuning (best tuned r2_score ~0.76). This is a genuine,
-- reproducible comparison point, not a misconfiguration -- see the notebook
-- for a fuller discussion.
--
-- Full reference: ../../RESOURCES.md
-- Official docs:
--   CREATE MODEL (random forest): https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-random-forest
--   The CREATE MODEL statement:   https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create


-- =============================================================================
-- Example 1: CREATE MODEL — train a random forest regressor
-- =============================================================================
-- GOTCHA (verified, same as random_forest_classifier): `max_iterations` is
-- NOT a valid option for RANDOM_FOREST_* -- CREATE MODEL errors immediately
-- if you set it. num_parallel_tree alone defines the forest; training is
-- single-pass by API-level guarantee, not just convention.
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.random_forest_regressor_penguins`
OPTIONS(
  model_type = 'RANDOM_FOREST_REGRESSOR',
  input_label_cols = ['body_mass_g'],
  num_parallel_tree = 50,
  tree_method = 'HIST',
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
SELECT *
FROM ML.EVALUATE(MODEL `PROJECT_ID.DATASET.random_forest_regressor_penguins`);


-- =============================================================================
-- Example 3: ML.PREDICT — predicted body mass
-- =============================================================================
SELECT
  predicted_body_mass_g,
  species,
  flipper_length_mm
FROM ML.PREDICT(
  MODEL `PROJECT_ID.DATASET.random_forest_regressor_penguins`,
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
  MODEL `PROJECT_ID.DATASET.random_forest_regressor_penguins`,
  (SELECT * FROM `bigquery-public-data.ml_datasets.penguins`
   WHERE body_mass_g IS NOT NULL AND sex IN ('MALE', 'FEMALE') LIMIT 5),
  STRUCT(5 AS top_k_features)
);


-- =============================================================================
-- Example 5: ML.GLOBAL_EXPLAIN and ML.FEATURE_IMPORTANCE — two views of importance
-- =============================================================================
-- On this small dataset with heavy column subsampling (colsample_bynode
-- default 0.8 over just 6 features), some features can end up with ZERO
-- importance/attribution -- verified: island and culmen_length_mm both
-- showed importance_weight = 0 / attribution = 0.0 in testing. This is a
-- real effect of bagging variance on a small feature set, not a bug.
SELECT *
FROM ML.GLOBAL_EXPLAIN(MODEL `PROJECT_ID.DATASET.random_forest_regressor_penguins`)
ORDER BY attribution DESC;

SELECT *
FROM ML.FEATURE_IMPORTANCE(MODEL `PROJECT_ID.DATASET.random_forest_regressor_penguins`)
ORDER BY importance_gain DESC;


-- =============================================================================
-- Example 6: ML.FEATURE_INFO and ML.TRAINING_INFO — introspect the model
-- =============================================================================
SELECT *
FROM ML.FEATURE_INFO(MODEL `PROJECT_ID.DATASET.random_forest_regressor_penguins`);

-- TRAINING_INFO: exactly one iteration (single-pass, verified), with
-- learning_rate = 1.0 -- contrast with BOOSTED_TREE_REGRESSOR's default 0.3
-- shrinkage across 20 iterations.
SELECT
  iteration,
  loss,
  eval_loss,
  learning_rate,
  duration_ms
FROM ML.TRAINING_INFO(MODEL `PROJECT_ID.DATASET.random_forest_regressor_penguins`)
ORDER BY iteration;


-- =============================================================================
-- Example 7: EXPORT MODEL — visualize a tree from a small illustrative forest
-- =============================================================================
-- Same gotchas as models/random_forest_classifier/ Example 9: the main
-- model's trees are too dense/deep to render meaningfully (every random
-- forest tree is complete, not a shallow residual-fitting stage like
-- boosting). Train a small, separate illustrative forest just for the
-- diagram.
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.random_forest_regressor_penguins_viz`
OPTIONS(
  model_type = 'RANDOM_FOREST_REGRESSOR',
  input_label_cols = ['body_mass_g'],
  num_parallel_tree = 10,
  max_tree_depth = 3
) AS
SELECT
  species, island, culmen_length_mm, culmen_depth_mm, flipper_length_mm, sex, body_mass_g
FROM `bigquery-public-data.ml_datasets.penguins`
WHERE body_mass_g IS NOT NULL AND sex IN ('MALE', 'FEMALE');

EXPORT MODEL `PROJECT_ID.DATASET.random_forest_regressor_penguins_viz`
OPTIONS (URI = 'gs://BUCKET/bq_ml/random_forest_regressor/model_viz');


-- =============================================================================
-- Example 8: In-model preprocessing with the TRANSFORM clause
-- =============================================================================
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.random_forest_regressor_penguins_transform`
TRANSFORM(
  ML.LABEL_ENCODER(species) OVER() AS species,
  ML.LABEL_ENCODER(island) OVER() AS island,
  ML.LABEL_ENCODER(sex) OVER() AS sex,
  culmen_length_mm, culmen_depth_mm, flipper_length_mm, body_mass_g
)
OPTIONS(
  model_type = 'RANDOM_FOREST_REGRESSOR',
  input_label_cols = ['body_mass_g'],
  num_parallel_tree = 50
) AS
SELECT species, island, culmen_length_mm, culmen_depth_mm, flipper_length_mm, sex, body_mass_g
FROM `bigquery-public-data.ml_datasets.penguins`
WHERE body_mass_g IS NOT NULL AND sex IN ('MALE', 'FEMALE');

-- Predict on RAW rows -- label-encoding is applied automatically inside the model.
SELECT predicted_body_mass_g, species, island, sex
FROM ML.PREDICT(
  MODEL `PROJECT_ID.DATASET.random_forest_regressor_penguins_transform`,
  (SELECT * FROM `bigquery-public-data.ml_datasets.penguins`
   WHERE body_mass_g IS NOT NULL AND sex IN ('MALE', 'FEMALE') LIMIT 5)
);


-- =============================================================================
-- Example 9: Hyperparameter tuning — NUM_TRIALS + HPARAM_RANGE
-- =============================================================================
-- Tune the forest size (num_parallel_tree) and tree depth. Verified: even
-- the best-tuned trial only reaches r2_score ~0.76 on this dataset -- still
-- well below boosted_tree_regressor's ~0.97, reinforcing the Example-1 note
-- that bagging underperforms boosting here, not a tuning shortfall.
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.random_forest_regressor_penguins_tuned`
OPTIONS(
  model_type = 'RANDOM_FOREST_REGRESSOR',
  input_label_cols = ['body_mass_g'],
  num_trials = 6,
  max_parallel_trials = 3,
  hparam_tuning_objectives = ['r2_score'],
  num_parallel_tree = HPARAM_RANGE(20, 100),
  max_tree_depth = HPARAM_RANGE(4, 8)
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
FROM ML.TRIAL_INFO(MODEL `PROJECT_ID.DATASET.random_forest_regressor_penguins_tuned`)
ORDER BY r2_score DESC;


-- =============================================================================
-- Cleanup
-- =============================================================================
-- DROP MODEL IF EXISTS `PROJECT_ID.DATASET.random_forest_regressor_penguins`;
-- DROP MODEL IF EXISTS `PROJECT_ID.DATASET.random_forest_regressor_penguins_viz`;
-- DROP MODEL IF EXISTS `PROJECT_ID.DATASET.random_forest_regressor_penguins_transform`;
-- DROP MODEL IF EXISTS `PROJECT_ID.DATASET.random_forest_regressor_penguins_tuned`;
