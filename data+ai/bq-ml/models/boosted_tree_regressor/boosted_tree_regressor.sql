-- Boosted Tree Regressor — Progressive SQL Examples (BigQuery ML)
-- =============================================================
-- Regression with CREATE MODEL (model_type = 'BOOSTED_TREE_REGRESSOR'),
-- an XGBoost gradient-boosted tree ensemble. Walks the full model lifecycle:
-- create -> evaluate -> predict -> explain -> visualize -> preprocess ->
-- hyperparameter-tune.
--
-- Data: bigquery-public-data.ml_datasets.penguins
--       Label: body_mass_g (continuous)
--       Same data + label as models/linear_regression/ -- compare r2_score
--       and feature attributions between the two techniques directly.
--       Rows with a NULL label or an invalid sex value ('.') are filtered out.
--
-- Full reference: ../../RESOURCES.md
-- Official docs:
--   CREATE MODEL (boosted tree): https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-boosted-tree
--   The CREATE MODEL statement:  https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create


-- =============================================================================
-- Example 1: CREATE MODEL — train a boosted tree regressor
-- =============================================================================
-- model_type + input_label_cols are the essentials. AUTO_SPLIT holds out a
-- portion of rows for evaluation; enable_global_explain is required for
-- ML.GLOBAL_EXPLAIN later. Unlike the classifier, there is no
-- auto_class_weights option for regression.
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.boosted_tree_regressor_penguins`
OPTIONS(
  model_type = 'BOOSTED_TREE_REGRESSOR',
  input_label_cols = ['body_mass_g'],
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
FROM ML.EVALUATE(MODEL `PROJECT_ID.DATASET.boosted_tree_regressor_penguins`);


-- =============================================================================
-- Example 3: ML.PREDICT — predicted body mass
-- =============================================================================
SELECT
  predicted_body_mass_g,
  species,
  flipper_length_mm
FROM ML.PREDICT(
  MODEL `PROJECT_ID.DATASET.boosted_tree_regressor_penguins`,
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
  MODEL `PROJECT_ID.DATASET.boosted_tree_regressor_penguins`,
  (SELECT * FROM `bigquery-public-data.ml_datasets.penguins`
   WHERE body_mass_g IS NOT NULL AND sex IN ('MALE', 'FEMALE') LIMIT 5),
  STRUCT(5 AS top_k_features)
);


-- =============================================================================
-- Example 5: ML.GLOBAL_EXPLAIN and ML.FEATURE_IMPORTANCE — two views of importance
-- =============================================================================
-- ML.GLOBAL_EXPLAIN: mean absolute Shapley-style attribution across the eval set.
-- ML.FEATURE_IMPORTANCE: tree-specific, split-based (weight/gain/cover) -- this
-- function does NOT apply to GLMs (see models/linear_regression/), only to
-- tree ensembles. The two can rank features differently -- that's expected;
-- they measure different things (attribution vs. how the trees actually split).
SELECT *
FROM ML.GLOBAL_EXPLAIN(MODEL `PROJECT_ID.DATASET.boosted_tree_regressor_penguins`)
ORDER BY attribution DESC;

SELECT *
FROM ML.FEATURE_IMPORTANCE(MODEL `PROJECT_ID.DATASET.boosted_tree_regressor_penguins`)
ORDER BY importance_gain DESC;


-- =============================================================================
-- Example 6: ML.FEATURE_INFO and ML.TRAINING_INFO — introspect the model
-- =============================================================================
SELECT *
FROM ML.FEATURE_INFO(MODEL `PROJECT_ID.DATASET.boosted_tree_regressor_penguins`);

-- TRAINING_INFO: per-iteration loss curve. early_stop=TRUE (the default) stops
-- once improvement falls below min_rel_progress. Note iteration numbering
-- starts at 1 (not 0, as in the LOGISTIC_REG/LINEAR_REG GLM notebooks).
SELECT
  iteration,
  loss,
  eval_loss,
  learning_rate,
  duration_ms
FROM ML.TRAINING_INFO(MODEL `PROJECT_ID.DATASET.boosted_tree_regressor_penguins`)
ORDER BY iteration;


-- =============================================================================
-- Example 7: EXPORT MODEL — visualize an individual tree
-- =============================================================================
-- EXPORT MODEL writes the trained ensemble to Cloud Storage as an XGBoost
-- Booster file (model.bst). Downloading it and loading it with the `xgboost`
-- Python library lets you plot an individual tree's structure -- see the
-- notebook for the Python side (xgboost.plot_tree).
--
-- GOTCHA (verified in models/boosted_tree_classifier/, holds here too): BQML
-- exports using XGBoost 0.82's legacy binary format. Modern xgboost (2.0+,
-- the current pip default) CANNOT load this file -- pin an older version
-- (verified working: xgboost==1.7.6). The export also does not preserve
-- feature names -- set Booster.feature_names manually to the training
-- query's non-label column order. Regressor-specific: loading also prints
-- "reg:linear is now deprecated in favor of reg:squarederror" -- a harmless
-- legacy-objective-name warning, not an error.
EXPORT MODEL `PROJECT_ID.DATASET.boosted_tree_regressor_penguins`
OPTIONS (URI = 'gs://BUCKET/bq_ml/boosted_tree_regressor/model');


-- =============================================================================
-- Example 8: In-model preprocessing with the TRANSFORM clause
-- =============================================================================
-- TRANSFORM applies preprocessing that is saved with the model and reapplied
-- automatically at predict time. Here we label-encode the categorical
-- features into ordinals -- ML.LABEL_ENCODER is an analytic function so it
-- requires an empty OVER().
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.boosted_tree_regressor_penguins_transform`
TRANSFORM(
  ML.LABEL_ENCODER(species) OVER() AS species,
  ML.LABEL_ENCODER(island) OVER() AS island,
  ML.LABEL_ENCODER(sex) OVER() AS sex,
  culmen_length_mm, culmen_depth_mm, flipper_length_mm, body_mass_g
)
OPTIONS(
  model_type = 'BOOSTED_TREE_REGRESSOR',
  input_label_cols = ['body_mass_g']
) AS
SELECT species, island, culmen_length_mm, culmen_depth_mm, flipper_length_mm, sex, body_mass_g
FROM `bigquery-public-data.ml_datasets.penguins`
WHERE body_mass_g IS NOT NULL AND sex IN ('MALE', 'FEMALE');

-- Predict on RAW rows -- label-encoding is applied automatically inside the model.
SELECT predicted_body_mass_g, species, island, sex
FROM ML.PREDICT(
  MODEL `PROJECT_ID.DATASET.boosted_tree_regressor_penguins_transform`,
  (SELECT * FROM `bigquery-public-data.ml_datasets.penguins`
   WHERE body_mass_g IS NOT NULL AND sex IN ('MALE', 'FEMALE') LIMIT 5)
);


-- =============================================================================
-- Example 9: Hyperparameter tuning — NUM_TRIALS + HPARAM_RANGE
-- =============================================================================
-- Tune the boosting shrinkage (learn_rate) and tree depth. Inspect trials
-- with ML.TRIAL_INFO. Individual trials can occasionally fail with a
-- transient error (status = 'FAILED'), showing a NULL objective metric for
-- that trial without failing the overall job -- see models/boosted_tree_classifier/
-- and the RESOURCES.md ML.TRIAL_INFO entry.
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.boosted_tree_regressor_penguins_tuned`
OPTIONS(
  model_type = 'BOOSTED_TREE_REGRESSOR',
  input_label_cols = ['body_mass_g'],
  num_trials = 6,
  max_parallel_trials = 3,
  hparam_tuning_objectives = ['r2_score'],
  learn_rate = HPARAM_RANGE(0.05, 0.3),
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
FROM ML.TRIAL_INFO(MODEL `PROJECT_ID.DATASET.boosted_tree_regressor_penguins_tuned`)
ORDER BY r2_score DESC;


-- =============================================================================
-- Cleanup
-- =============================================================================
-- DROP MODEL IF EXISTS `PROJECT_ID.DATASET.boosted_tree_regressor_penguins`;
-- DROP MODEL IF EXISTS `PROJECT_ID.DATASET.boosted_tree_regressor_penguins_transform`;
-- DROP MODEL IF EXISTS `PROJECT_ID.DATASET.boosted_tree_regressor_penguins_tuned`;
