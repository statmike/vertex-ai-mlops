-- DNN Classifier — Progressive SQL Examples (BigQuery ML)
-- =============================================================
-- Binary classification with CREATE MODEL (model_type = 'DNN_CLASSIFIER'),
-- a fully-connected feed-forward neural network trained with TensorFlow
-- inside BigQuery. Walks the full model lifecycle: create -> evaluate ->
-- predict -> explain -> inspect -> preprocess -> hyperparameter-tune.
--
-- Data: bigquery-public-data.ml_datasets.census_adult_income
--       Label: income_bracket ('<=50K' / '>50K')
--       Same data + label as models/logistic_regression/,
--       models/boosted_tree_classifier/, and models/random_forest_classifier/
--       -- compare roc_auc across all four techniques directly.
--
-- Full reference: ../../RESOURCES.md
-- Official docs:
--   CREATE MODEL (DNN):         https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-dnn-models
--   The CREATE MODEL statement: https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create


-- =============================================================================
-- Example 1: CREATE MODEL — train a DNN classifier
-- =============================================================================
-- model_type + input_label_cols are the essentials. hidden_units=[64,32]
-- gives the network two fully-connected layers; dropout and early_stop guard
-- against overfitting; auto_class_weights balances the classes;
-- enable_global_explain is required for ML.GLOBAL_EXPLAIN later.
--
-- GOTCHA (verified): unlike the tree models, DNN training is genuinely slow
-- -- this single CREATE MODEL took ~12-46 minutes in testing (wall time
-- varies a lot with concurrent BigQuery load in the project -- see
-- RESOURCES.md), for a training set of only ~32K rows. With the DEFAULT
-- learn_rate (0.001) and early_stop=TRUE, training stopped after just 2
-- iterations here (min_rel_progress not met) -- see ML.TRAINING_INFO in
-- Example 8. Despite the short training run, roc_auc still lands
-- competitively with Logistic Regression / Boosted Tree / Random Forest on
-- this dataset (~0.89) because the classification loss surface tolerates
-- unscaled numeric inputs (age, education_num, hours_per_week) much better
-- than the regression case does -- contrast with models/dnn_regressor/,
-- where the same default settings produce a badly broken model.
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.dnn_classifier_income`
OPTIONS(
  model_type = 'DNN_CLASSIFIER',
  input_label_cols = ['income_bracket'],
  hidden_units = [64, 32],
  activation_fn = 'RELU',
  optimizer = 'ADAM',
  dropout = 0.15,
  max_iterations = 20,
  early_stop = TRUE,
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
FROM ML.EVALUATE(MODEL `PROJECT_ID.DATASET.dnn_classifier_income`);


-- =============================================================================
-- Example 3: ML.CONFUSION_MATRIX — counts by predicted vs actual
-- =============================================================================
SELECT *
FROM ML.CONFUSION_MATRIX(MODEL `PROJECT_ID.DATASET.dnn_classifier_income`);


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
FROM ML.ROC_CURVE(MODEL `PROJECT_ID.DATASET.dnn_classifier_income`)
ORDER BY threshold;


-- =============================================================================
-- Example 5: ML.PREDICT — predicted label + class probabilities
-- =============================================================================
SELECT
  predicted_income_bracket,
  predicted_income_bracket_probs
FROM ML.PREDICT(
  MODEL `PROJECT_ID.DATASET.dnn_classifier_income`,
  (SELECT * FROM `bigquery-public-data.ml_datasets.census_adult_income` LIMIT 10)
);


-- =============================================================================
-- Example 6: ML.EXPLAIN_PREDICT — per-row feature attributions
-- =============================================================================
-- DNNs have no coefficients (see the ML.WEIGHTS gap noted below), so
-- attributions come from Integrated Gradients instead -- the same mechanism
-- used for ML.GLOBAL_EXPLAIN in Example 7.
SELECT
  predicted_income_bracket,
  top_feature_attributions
FROM ML.EXPLAIN_PREDICT(
  MODEL `PROJECT_ID.DATASET.dnn_classifier_income`,
  (SELECT * FROM `bigquery-public-data.ml_datasets.census_adult_income` LIMIT 5),
  STRUCT(5 AS top_k_features)
);


-- =============================================================================
-- Example 7: ML.GLOBAL_EXPLAIN — overall feature importance
-- =============================================================================
-- Requires enable_global_explain = TRUE at CREATE MODEL time (see Example 1).
-- Integrated-Gradients based -- there is no ML.FEATURE_IMPORTANCE (tree-only)
-- or ML.WEIGHTS/ML.ADVANCED_WEIGHTS (no coefficients) for DNN models.
SELECT *
FROM ML.GLOBAL_EXPLAIN(MODEL `PROJECT_ID.DATASET.dnn_classifier_income`)
ORDER BY attribution DESC;


-- =============================================================================
-- Example 8: ML.FEATURE_INFO and ML.TRAINING_INFO — introspect the model
-- =============================================================================
SELECT *
FROM ML.FEATURE_INFO(MODEL `PROJECT_ID.DATASET.dnn_classifier_income`);

-- TRAINING_INFO: per-iteration loss curve. Verified: with the default
-- learn_rate=0.001, this model's early_stop=TRUE kicked in after only 2
-- iterations (loss barely improved between them) -- contrast with Example 9,
-- where scaling the numeric features lets training run for several more
-- iterations before the same early-stopping rule triggers.
SELECT
  iteration,
  loss,
  eval_loss,
  learning_rate,
  duration_ms
FROM ML.TRAINING_INFO(MODEL `PROJECT_ID.DATASET.dnn_classifier_income`)
ORDER BY iteration;


-- =============================================================================
-- Example 9: In-model preprocessing with the TRANSFORM clause
-- =============================================================================
-- RESOURCES.md best practice: normalize numeric inputs before training a
-- DNN -- gradient-based training is sensitive to feature scale. Verified
-- effect here: final roc_auc is about the same as Example 1 (~0.89), but
-- scaling changes the training dynamics -- this run took 8 iterations to
-- hit the same early-stopping rule (vs. 2 unscaled), with a proper
-- declining loss curve instead of an almost-flat one. See
-- models/dnn_regressor/ for a case where scaling (and a higher learn_rate)
-- is the difference between a broken model and a good one.
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.dnn_classifier_income_transform`
TRANSFORM(
  ML.STANDARD_SCALER(age) OVER() AS age,
  ML.STANDARD_SCALER(education_num) OVER() AS education_num,
  ML.STANDARD_SCALER(hours_per_week) OVER() AS hours_per_week,
  workclass, education, marital_status, occupation, relationship, race, sex,
  native_country, income_bracket
)
OPTIONS(
  model_type = 'DNN_CLASSIFIER',
  input_label_cols = ['income_bracket'],
  hidden_units = [64, 32],
  activation_fn = 'RELU',
  optimizer = 'ADAM',
  dropout = 0.15,
  max_iterations = 20,
  early_stop = TRUE,
  auto_class_weights = TRUE,
  data_split_method = 'AUTO_SPLIT',
  enable_global_explain = TRUE
) AS
SELECT
  age, workclass, education, education_num, marital_status, occupation,
  relationship, race, sex, hours_per_week, native_country, income_bracket
FROM `bigquery-public-data.ml_datasets.census_adult_income`;

-- Predict on RAW rows -- scaling is applied automatically inside the model.
SELECT predicted_income_bracket, age
FROM ML.PREDICT(
  MODEL `PROJECT_ID.DATASET.dnn_classifier_income_transform`,
  (SELECT * FROM `bigquery-public-data.ml_datasets.census_adult_income` LIMIT 5)
);


-- =============================================================================
-- Example 10: Hyperparameter tuning — NUM_TRIALS + HPARAM_CANDIDATES + HPARAM_RANGE
-- =============================================================================
-- hidden_units is only tunable via HPARAM_CANDIDATES, and each candidate is a
-- STRUCT wrapping the whole layer-sizes array (ARRAY<STRUCT<ARRAY<INT64>>>)
-- -- verified working syntax below. learn_rate is tunable via HPARAM_RANGE.
-- Given how expensive DNN training is (see Example 1), keep num_trials small.
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.dnn_classifier_income_tuned`
OPTIONS(
  model_type = 'DNN_CLASSIFIER',
  input_label_cols = ['income_bracket'],
  auto_class_weights = TRUE,
  num_trials = 4,
  max_parallel_trials = 2,
  hparam_tuning_objectives = ['roc_auc'],
  hidden_units = HPARAM_CANDIDATES([STRUCT([64, 32]), STRUCT([32, 16])]),
  learn_rate = HPARAM_RANGE(0.001, 0.05)
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
FROM ML.TRIAL_INFO(MODEL `PROJECT_ID.DATASET.dnn_classifier_income_tuned`)
ORDER BY roc_auc DESC;


-- =============================================================================
-- Cleanup
-- =============================================================================
-- DROP MODEL IF EXISTS `PROJECT_ID.DATASET.dnn_classifier_income`;
-- DROP MODEL IF EXISTS `PROJECT_ID.DATASET.dnn_classifier_income_transform`;
-- DROP MODEL IF EXISTS `PROJECT_ID.DATASET.dnn_classifier_income_tuned`;
