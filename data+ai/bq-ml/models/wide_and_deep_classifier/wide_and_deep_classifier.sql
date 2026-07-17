-- Wide & Deep Classifier — Progressive SQL Examples (BigQuery ML)
-- =============================================================
-- Binary classification with CREATE MODEL (model_type =
-- 'DNN_LINEAR_COMBINED_CLASSIFIER') -- a jointly-trained combination of a
-- WIDE linear model (memorizes feature interactions) and a DEEP neural
-- network (generalizes), trained with TensorFlow inside BigQuery. Walks
-- the full model lifecycle: create -> evaluate -> predict -> explain ->
-- inspect -> preprocess -> hyperparameter-tune.
--
-- Data: bigquery-public-data.ml_datasets.census_adult_income
--       Label: income_bracket ('<=50K' / '>50K')
--       Same data + label as models/logistic_regression/,
--       models/boosted_tree_classifier/, models/random_forest_classifier/,
--       and models/dnn_classifier/ -- compare roc_auc across all five
--       techniques directly.
--
-- Full reference: ../../RESOURCES.md
-- Official docs:
--   CREATE MODEL (wide-and-deep): https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-wnd-models
--   The CREATE MODEL statement:   https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create


-- =============================================================================
-- Example 1: CREATE MODEL — train a wide-and-deep classifier
-- =============================================================================
-- Same option shape as models/dnn_classifier/ -- hidden_units define the
-- DEEP side; the WIDE (linear) side is implicit and uses the same input
-- features. auto_class_weights balances the classes; enable_global_explain
-- is required for ML.GLOBAL_EXPLAIN later.
--
-- Verified: like DNN_CLASSIFIER, this tolerates unscaled numeric inputs
-- reasonably well on this dataset -- early_stop still cuts training to 2
-- iterations, but roc_auc lands competitively (~0.89). Contrast with
-- models/wide_and_deep_regressor/, where the same default settings on the
-- small penguins dataset produce a badly broken model (same finding as
-- models/dnn_regressor/).
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.wide_deep_classifier_income`
OPTIONS(
  model_type = 'DNN_LINEAR_COMBINED_CLASSIFIER',
  input_label_cols = ['income_bracket'],
  hidden_units = [64, 32],
  activation_fn = 'RELU',
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
FROM ML.EVALUATE(MODEL `PROJECT_ID.DATASET.wide_deep_classifier_income`);


-- =============================================================================
-- Example 3: ML.CONFUSION_MATRIX — counts by predicted vs actual
-- =============================================================================
SELECT *
FROM ML.CONFUSION_MATRIX(MODEL `PROJECT_ID.DATASET.wide_deep_classifier_income`);


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
FROM ML.ROC_CURVE(MODEL `PROJECT_ID.DATASET.wide_deep_classifier_income`)
ORDER BY threshold;


-- =============================================================================
-- Example 5: ML.PREDICT — predicted label + class probabilities
-- =============================================================================
SELECT
  predicted_income_bracket,
  predicted_income_bracket_probs
FROM ML.PREDICT(
  MODEL `PROJECT_ID.DATASET.wide_deep_classifier_income`,
  (SELECT * FROM `bigquery-public-data.ml_datasets.census_adult_income` LIMIT 10)
);


-- =============================================================================
-- Example 6: ML.EXPLAIN_PREDICT — per-row feature attributions
-- =============================================================================
-- Same as DNN: no coefficients, so attributions come from Integrated
-- Gradients rather than ML.WEIGHTS.
SELECT
  predicted_income_bracket,
  top_feature_attributions
FROM ML.EXPLAIN_PREDICT(
  MODEL `PROJECT_ID.DATASET.wide_deep_classifier_income`,
  (SELECT * FROM `bigquery-public-data.ml_datasets.census_adult_income` LIMIT 5),
  STRUCT(5 AS top_k_features)
);


-- =============================================================================
-- Example 7: ML.GLOBAL_EXPLAIN — overall feature importance
-- =============================================================================
-- Requires enable_global_explain = TRUE at CREATE MODEL time (see Example 1).
-- No ML.FEATURE_IMPORTANCE (tree-only) or ML.WEIGHTS/ML.ADVANCED_WEIGHTS (no
-- coefficients) for this model type -- same lifecycle-function gap as DNN.
SELECT *
FROM ML.GLOBAL_EXPLAIN(MODEL `PROJECT_ID.DATASET.wide_deep_classifier_income`)
ORDER BY attribution DESC;


-- =============================================================================
-- Example 8: ML.FEATURE_INFO and ML.TRAINING_INFO — introspect the model
-- =============================================================================
SELECT *
FROM ML.FEATURE_INFO(MODEL `PROJECT_ID.DATASET.wide_deep_classifier_income`);

-- TRAINING_INFO: verified -- early_stop (default TRUE) stopped training
-- after 2 iterations here, same pattern as models/dnn_classifier/.
SELECT
  iteration,
  loss,
  eval_loss,
  learning_rate,
  duration_ms
FROM ML.TRAINING_INFO(MODEL `PROJECT_ID.DATASET.wide_deep_classifier_income`)
ORDER BY iteration;


-- =============================================================================
-- Example 9: In-model preprocessing with the TRANSFORM clause
-- =============================================================================
-- Same best practice as DNN: normalize numeric inputs. Verified effect:
-- final roc_auc is about the same (~0.89), but this run took 8 iterations
-- to hit the same early-stopping rule (vs. 2 unscaled) -- a proper
-- declining loss curve instead of an almost-flat one.
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.wide_deep_classifier_income_transform`
TRANSFORM(
  ML.STANDARD_SCALER(age) OVER() AS age,
  ML.STANDARD_SCALER(education_num) OVER() AS education_num,
  ML.STANDARD_SCALER(hours_per_week) OVER() AS hours_per_week,
  workclass, education, marital_status, occupation, relationship, race, sex,
  native_country, income_bracket
)
OPTIONS(
  model_type = 'DNN_LINEAR_COMBINED_CLASSIFIER',
  input_label_cols = ['income_bracket'],
  hidden_units = [64, 32],
  activation_fn = 'RELU',
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
  MODEL `PROJECT_ID.DATASET.wide_deep_classifier_income_transform`,
  (SELECT * FROM `bigquery-public-data.ml_datasets.census_adult_income` LIMIT 5)
);


-- =============================================================================
-- Example 10: Hyperparameter tuning — NUM_TRIALS + HPARAM_CANDIDATES + HPARAM_RANGE
-- =============================================================================
-- hidden_units is only tunable via HPARAM_CANDIDATES (same STRUCT-wrapped
-- array syntax as DNN). dropout is tunable via HPARAM_RANGE.
--
-- GOTCHA (verified, differs from DNN_CLASSIFIER/DNN_REGRESSOR): learn_rate
-- and optimizer are NOT tunable for DNN_LINEAR_COMBINED_* -- both fail
-- immediately with "Unsupported hyperparameter <name> for model_type
-- DNN_LINEAR_COMBINED_CLASSIFIER", even though RESOURCES.md's general docs
-- summary lists them as tunable (that summary reflects plain DNN_*, not
-- this type). Confirmed tunable instead: hidden_units, dropout, batch_size,
-- l1_reg, l2_reg.
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.wide_deep_classifier_income_tuned`
OPTIONS(
  model_type = 'DNN_LINEAR_COMBINED_CLASSIFIER',
  input_label_cols = ['income_bracket'],
  auto_class_weights = TRUE,
  num_trials = 4,
  max_parallel_trials = 2,
  hparam_tuning_objectives = ['roc_auc'],
  hidden_units = HPARAM_CANDIDATES([STRUCT([64, 32]), STRUCT([32, 16])]),
  dropout = HPARAM_RANGE(0.0, 0.3)
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
FROM ML.TRIAL_INFO(MODEL `PROJECT_ID.DATASET.wide_deep_classifier_income_tuned`)
ORDER BY roc_auc DESC;


-- =============================================================================
-- Cleanup
-- =============================================================================
-- DROP MODEL IF EXISTS `PROJECT_ID.DATASET.wide_deep_classifier_income`;
-- DROP MODEL IF EXISTS `PROJECT_ID.DATASET.wide_deep_classifier_income_transform`;
-- DROP MODEL IF EXISTS `PROJECT_ID.DATASET.wide_deep_classifier_income_tuned`;
