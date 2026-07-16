-- Random Forest Classifier — Progressive SQL Examples (BigQuery ML)
-- =============================================================
-- Binary classification with CREATE MODEL (model_type = 'RANDOM_FOREST_CLASSIFIER'),
-- a bagged ensemble of decision trees trained with XGBoost. Walks the full
-- model lifecycle: create -> evaluate -> inspect -> predict -> explain ->
-- visualize -> preprocess -> hyperparameter-tune.
--
-- Data: bigquery-public-data.ml_datasets.census_adult_income
--       Label: income_bracket ('<=50K' / '>50K')
--       Same data + label as models/logistic_regression/ and
--       models/boosted_tree_classifier/ -- compare roc_auc across all three
--       techniques directly.
--
-- Full reference: ../../RESOURCES.md
-- Official docs:
--   CREATE MODEL (random forest): https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-random-forest
--   The CREATE MODEL statement:   https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create


-- =============================================================================
-- Example 1: CREATE MODEL — train a random forest classifier
-- =============================================================================
-- model_type + input_label_cols are the essentials. num_parallel_tree is what
-- makes it a "forest" (many trees trained in parallel on row/column
-- subsamples) rather than a single boosted sequence. AUTO_SPLIT holds out a
-- portion of rows for evaluation; AUTO_CLASS_WEIGHTS balances the classes;
-- enable_global_explain is required for ML.GLOBAL_EXPLAIN later.
--
-- GOTCHA (verified): `max_iterations` is NOT a valid option for
-- RANDOM_FOREST_* at all -- CREATE MODEL errors immediately with "Option(s)
-- MAX_ITERATIONS are not supported for RANDOM_FOREST_CLASSIFIER model
-- training" if you set it. This is an API-level guarantee that random
-- forest training is single-pass -- unlike BOOSTED_TREE_*, where
-- max_iterations is a central hyperparameter, num_parallel_tree alone
-- defines the forest here.
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.random_forest_classifier_income`
OPTIONS(
  model_type = 'RANDOM_FOREST_CLASSIFIER',
  input_label_cols = ['income_bracket'],
  num_parallel_tree = 50,
  tree_method = 'HIST',
  auto_class_weights = TRUE,
  data_split_method = 'AUTO_SPLIT',
  enable_global_explain = TRUE
) AS
SELECT
  age, workclass, education, education_num, marital_status, occupation,
  relationship, race, sex, hours_per_week, native_country, income_bracket
FROM `bigquery-public-data.ml_datasets.census_adult_income`;


-- =============================================================================
-- Example 2: ML.EVALUATE — classification metrics
-- =============================================================================
SELECT *
FROM ML.EVALUATE(MODEL `PROJECT_ID.DATASET.random_forest_classifier_income`);


-- =============================================================================
-- Example 3: ML.CONFUSION_MATRIX — counts by predicted vs actual
-- =============================================================================
SELECT *
FROM ML.CONFUSION_MATRIX(MODEL `PROJECT_ID.DATASET.random_forest_classifier_income`);


-- =============================================================================
-- Example 4: ML.ROC_CURVE — thresholds, recall, false positive rate
-- =============================================================================
SELECT
  threshold,
  recall,
  false_positive_rate,
  true_positives,
  false_positives,
  true_negatives,
  false_negatives
FROM ML.ROC_CURVE(MODEL `PROJECT_ID.DATASET.random_forest_classifier_income`)
ORDER BY threshold;


-- =============================================================================
-- Example 5: ML.PREDICT — predicted label + class probabilities
-- =============================================================================
SELECT
  predicted_income_bracket,
  predicted_income_bracket_probs
FROM ML.PREDICT(
  MODEL `PROJECT_ID.DATASET.random_forest_classifier_income`,
  (SELECT * FROM `bigquery-public-data.ml_datasets.census_adult_income` LIMIT 10)
);


-- =============================================================================
-- Example 6: ML.EXPLAIN_PREDICT — per-row feature attributions
-- =============================================================================
SELECT
  predicted_income_bracket,
  top_feature_attributions
FROM ML.EXPLAIN_PREDICT(
  MODEL `PROJECT_ID.DATASET.random_forest_classifier_income`,
  (SELECT * FROM `bigquery-public-data.ml_datasets.census_adult_income` LIMIT 10),
  STRUCT(5 AS top_k_features)
);


-- =============================================================================
-- Example 7: ML.GLOBAL_EXPLAIN and ML.FEATURE_IMPORTANCE — two views of importance
-- =============================================================================
-- Same distinction as boosted trees: ML.GLOBAL_EXPLAIN is Shapley-style
-- attribution; ML.FEATURE_IMPORTANCE is tree-specific split-based (weight/
-- gain/cover). Neither applies to GLMs (see models/logistic_regression/).
SELECT *
FROM ML.GLOBAL_EXPLAIN(MODEL `PROJECT_ID.DATASET.random_forest_classifier_income`)
ORDER BY attribution DESC;

SELECT *
FROM ML.FEATURE_IMPORTANCE(MODEL `PROJECT_ID.DATASET.random_forest_classifier_income`)
ORDER BY importance_gain DESC;


-- =============================================================================
-- Example 8: ML.FEATURE_INFO and ML.TRAINING_INFO — introspect the model
-- =============================================================================
SELECT *
FROM ML.FEATURE_INFO(MODEL `PROJECT_ID.DATASET.random_forest_classifier_income`);

-- TRAINING_INFO: random forest trains in exactly ONE iteration (verified --
-- this is the "single-pass" behavior from Example 1's gotcha), with
-- learning_rate = 1.0 (contrast with BOOSTED_TREE_*'s default 0.3 shrinkage
-- across many iterations -- a forest averages full-strength trees rather
-- than sequentially shrinking residual corrections).
SELECT
  iteration,
  loss,
  eval_loss,
  learning_rate,
  duration_ms
FROM ML.TRAINING_INFO(MODEL `PROJECT_ID.DATASET.random_forest_classifier_income`)
ORDER BY iteration;


-- =============================================================================
-- Example 9: EXPORT MODEL — visualize a tree from a small illustrative forest
-- =============================================================================
-- Same EXPORT MODEL + xgboost mechanism as models/boosted_tree_classifier/
-- (same two gotchas: pin xgboost==1.7.6; feature_names must be reassigned
-- manually). But there is a THIRD, random-forest-specific gotcha, verified:
--
-- A full-power random forest tree (num_parallel_tree=50, default
-- max_tree_depth=6) is too dense to render meaningfully -- unlike a boosted
-- tree's shallow early-round tree (fit on residuals), EVERY random forest
-- tree is a complete, independently-trained tree. The Example-1 model's
-- tree 0 has 2,435 node-dump lines and depth 15 -- xgboost.plot_tree()
-- triggers a "graph is too large for cairo-renderer bitmaps" warning and
-- the rendered PNG is illegible.
--
-- Fix (verified): train a small, SEPARATE illustrative forest just for
-- visualization -- fewer, shallower trees -- rather than trying to render
-- the main model's tree. This mirrors real practice: nobody eyeballs a
-- full-depth production random forest tree either; ML.FEATURE_IMPORTANCE
-- (Example 7) is the right tool for that. The illustrative forest below
-- (num_parallel_tree=10, max_tree_depth=3) renders a clean, legible
-- diagram (15 node-dump lines).
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.random_forest_classifier_income_viz`
OPTIONS(
  model_type = 'RANDOM_FOREST_CLASSIFIER',
  input_label_cols = ['income_bracket'],
  num_parallel_tree = 10,
  max_tree_depth = 3
) AS
SELECT
  age, workclass, education, education_num, marital_status, occupation,
  relationship, race, sex, hours_per_week, native_country, income_bracket
FROM `bigquery-public-data.ml_datasets.census_adult_income`;

EXPORT MODEL `PROJECT_ID.DATASET.random_forest_classifier_income_viz`
OPTIONS (URI = 'gs://BUCKET/bq_ml/random_forest_classifier/model_viz');


-- =============================================================================
-- Example 10: In-model preprocessing with the TRANSFORM clause
-- =============================================================================
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.random_forest_classifier_income_transform`
TRANSFORM(
  ML.QUANTILE_BUCKETIZE(age, 10) OVER() AS age_bucket,
  education, marital_status, occupation, relationship, hours_per_week, income_bracket
)
OPTIONS(
  model_type = 'RANDOM_FOREST_CLASSIFIER',
  input_label_cols = ['income_bracket'],
  num_parallel_tree = 50,
  auto_class_weights = TRUE
) AS
SELECT age, education, marital_status, occupation, relationship, hours_per_week, income_bracket
FROM `bigquery-public-data.ml_datasets.census_adult_income`;

-- Predict on RAW rows -- bucketizing is applied automatically inside the model.
SELECT predicted_income_bracket, age
FROM ML.PREDICT(
  MODEL `PROJECT_ID.DATASET.random_forest_classifier_income_transform`,
  (SELECT * FROM `bigquery-public-data.ml_datasets.census_adult_income` LIMIT 5)
);


-- =============================================================================
-- Example 11: Hyperparameter tuning — NUM_TRIALS + HPARAM_RANGE
-- =============================================================================
-- Tune the forest size (num_parallel_tree) and tree depth. Inspect trials
-- with ML.TRIAL_INFO. As with boosted trees, individual trials can
-- occasionally fail with a transient error (status = 'FAILED', NULL
-- objective metric) without failing the overall job.
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.random_forest_classifier_income_tuned`
OPTIONS(
  model_type = 'RANDOM_FOREST_CLASSIFIER',
  input_label_cols = ['income_bracket'],
  auto_class_weights = TRUE,
  num_trials = 6,
  max_parallel_trials = 3,
  hparam_tuning_objectives = ['roc_auc'],
  num_parallel_tree = HPARAM_RANGE(20, 100),
  max_tree_depth = HPARAM_RANGE(4, 8)
) AS
SELECT
  age, workclass, education, education_num, marital_status, occupation,
  relationship, race, sex, hours_per_week, native_country, income_bracket
FROM `bigquery-public-data.ml_datasets.census_adult_income`;

-- Inspect each trial's hyperparameters and objective score.
SELECT
  trial_id,
  hyperparameters,
  hparam_tuning_evaluation_metrics.roc_auc AS roc_auc,
  is_optimal
FROM ML.TRIAL_INFO(MODEL `PROJECT_ID.DATASET.random_forest_classifier_income_tuned`)
ORDER BY roc_auc DESC;


-- =============================================================================
-- Cleanup
-- =============================================================================
-- DROP MODEL IF EXISTS `PROJECT_ID.DATASET.random_forest_classifier_income`;
-- DROP MODEL IF EXISTS `PROJECT_ID.DATASET.random_forest_classifier_income_viz`;
-- DROP MODEL IF EXISTS `PROJECT_ID.DATASET.random_forest_classifier_income_transform`;
-- DROP MODEL IF EXISTS `PROJECT_ID.DATASET.random_forest_classifier_income_tuned`;
