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
-- NOTE: on this small (333-row) dataset boosting still wins, but narrowly.
-- Measured r2_score: ~0.922 for this forest, ~0.983 for
-- boosted_tree_regressor, ~0.875 for linear_regression on identical data.
-- The forest reaches that untuned -- the best tuned trial (Example 9) does
-- not beat it.
--
-- That ordering depends on xgboost_version. At the '0.9' default the same
-- forest scores r2_score ~0.73-0.75 because it grows only 82 splits across
-- all six features, against 2,482 at '2.1' -- verified both ways. Bagging is
-- not weak on small data; the 2019 default library under-grew the forest.
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
--
-- xgboost_version defaults to '0.9' -- a 2019 release. '2.1' (GA 2026-08-27)
-- is set here for what it does to the export in Example 7: a modern model.ubj
-- that current xgboost reads with no pinned dependency, and the legacy
-- reg:linear objective name goes away with it. Accepted values: 0.9, 1.1, 2.1.
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.random_forest_regressor_penguins`
OPTIONS(
  model_type = 'RANDOM_FOREST_REGRESSOR',
  xgboost_version = '2.1',
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
-- default 0.8 over just 6 features), how much of the feature set gets used
-- depends on how many splits the forest grows -- which xgboost_version sets.
-- At '2.1' (Example 1) all six features carry non-zero importance and
-- attribution, island lowest at importance_weight 245 / attribution ~10. At
-- the '0.9' default the forest grows only 82 splits total and island and
-- culmen_length_mm both come back at exactly ZERO -- verified both ways. A
-- zero here means an under-grown forest, not a feature with no signal.
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
--
-- The exported filename depends on xgboost_version: model.bst (legacy binary,
-- needs a pinned xgboost==1.7.6 to load) at the '0.9' default, model.ubj at
-- '2.1' as set below -- current xgboost reads that one unpinned, and the
-- objective is written as reg:squarederror instead of the deprecated
-- reg:linear. Feature names are not preserved at either version.
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.random_forest_regressor_penguins_viz`
OPTIONS(
  model_type = 'RANDOM_FOREST_REGRESSOR',
  xgboost_version = '2.1',
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
  xgboost_version = '2.1',
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
-- Tune the forest size (num_parallel_tree) and tree depth. Verified: tuning
-- does NOT beat the untuned model here -- the best trial reaches r2_score
-- ~0.917 against ~0.922 from Example 1's defaults, and all six trials land
-- in a narrow ~0.907-0.917 band. That is the low-tuning property of bagging
-- holding up, not a tuning shortfall.
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.random_forest_regressor_penguins_tuned`
OPTIONS(
  model_type = 'RANDOM_FOREST_REGRESSOR',
  xgboost_version = '2.1',
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
