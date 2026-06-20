-- Logistic Regression — Progressive SQL Examples (BigQuery ML)
-- =============================================================
-- Binary classification with CREATE MODEL (model_type = 'LOGISTIC_REG').
-- Walks the full model lifecycle: create -> evaluate -> inspect ->
-- predict -> explain -> hyperparameter-tune.
--
-- Data: bigquery-public-data.ml_datasets.census_adult_income
--       Label: income_bracket ('<=50K' / '>50K')
--
-- Full reference: ../../RESOURCES.md
-- Official docs:
--   CREATE MODEL (logistic reg): https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-glm
--   The CREATE MODEL statement:  https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create


-- =============================================================================
-- Example 1: CREATE MODEL — train a logistic regression classifier
-- =============================================================================
-- model_type + input_label_cols are the essentials. AUTO_SPLIT holds out a
-- portion of rows for evaluation; AUTO_CLASS_WEIGHTS balances the classes.
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.logistic_regression_income`
OPTIONS(
  model_type = 'LOGISTIC_REG',
  input_label_cols = ['income_bracket'],
  auto_class_weights = TRUE,
  data_split_method = 'AUTO_SPLIT',
  enable_global_explain = TRUE   -- required for ML.GLOBAL_EXPLAIN later
) AS
SELECT
  age, workclass, education, education_num, marital_status, occupation,
  relationship, race, sex, hours_per_week, native_country, income_bracket
FROM `bigquery-public-data.ml_datasets.census_adult_income`;


-- =============================================================================
-- Example 2: ML.EVALUATE — classification metrics
-- =============================================================================
-- Precision, recall, accuracy, f1, log_loss, roc_auc on the eval split.
SELECT *
FROM ML.EVALUATE(MODEL `PROJECT_ID.DATASET.logistic_regression_income`);


-- =============================================================================
-- Example 3: ML.CONFUSION_MATRIX — counts by predicted vs actual
-- =============================================================================
SELECT *
FROM ML.CONFUSION_MATRIX(MODEL `PROJECT_ID.DATASET.logistic_regression_income`);


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
FROM ML.ROC_CURVE(MODEL `PROJECT_ID.DATASET.logistic_regression_income`)
ORDER BY threshold;


-- =============================================================================
-- Example 5: ML.PREDICT — predicted label + class probabilities
-- =============================================================================
-- predicted_<label> is the chosen class; predicted_<label>_probs holds the
-- probability for each class.
SELECT
  predicted_income_bracket,
  predicted_income_bracket_probs
FROM ML.PREDICT(
  MODEL `PROJECT_ID.DATASET.logistic_regression_income`,
  (SELECT * FROM `bigquery-public-data.ml_datasets.census_adult_income` LIMIT 10)
);


-- =============================================================================
-- Example 6: ML.EXPLAIN_PREDICT — per-row feature attributions
-- =============================================================================
-- Shows which features pushed each individual prediction up or down.
SELECT
  predicted_income_bracket,
  top_feature_attributions
FROM ML.EXPLAIN_PREDICT(
  MODEL `PROJECT_ID.DATASET.logistic_regression_income`,
  (SELECT * FROM `bigquery-public-data.ml_datasets.census_adult_income` LIMIT 10),
  STRUCT(5 AS top_k_features)
);


-- =============================================================================
-- Example 7: ML.GLOBAL_EXPLAIN — overall feature importance
-- =============================================================================
-- Requires enable_global_explain = TRUE at CREATE MODEL time (see Example 1).
SELECT *
FROM ML.GLOBAL_EXPLAIN(MODEL `PROJECT_ID.DATASET.logistic_regression_income`)
ORDER BY attribution DESC;


-- =============================================================================
-- Example 8: ML.FEATURE_INFO and ML.TRAINING_INFO — introspect the model
-- =============================================================================
-- FEATURE_INFO: per-feature statistics seen during training.
SELECT *
FROM ML.FEATURE_INFO(MODEL `PROJECT_ID.DATASET.logistic_regression_income`);

-- TRAINING_INFO: per-iteration loss curve.
SELECT
  iteration,
  loss,
  eval_loss,
  learning_rate,
  duration_ms
FROM ML.TRAINING_INFO(MODEL `PROJECT_ID.DATASET.logistic_regression_income`)
ORDER BY iteration;


-- =============================================================================
-- Example 9: In-model preprocessing with the TRANSFORM clause
-- =============================================================================
-- TRANSFORM applies preprocessing that is saved with the model and reapplied
-- automatically at predict time — no need to repeat it in ML.PREDICT.
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.logistic_regression_income_transform`
TRANSFORM(
  ML.STANDARD_SCALER(age) OVER() AS age,
  ML.STANDARD_SCALER(hours_per_week) OVER() AS hours_per_week,
  education, marital_status, occupation, relationship, income_bracket
)
OPTIONS(
  model_type = 'LOGISTIC_REG',
  input_label_cols = ['income_bracket'],
  auto_class_weights = TRUE
) AS
SELECT
  age, hours_per_week, education, marital_status, occupation,
  relationship, income_bracket
FROM `bigquery-public-data.ml_datasets.census_adult_income`;


-- =============================================================================
-- Example 10: Hyperparameter tuning — NUM_TRIALS + HPARAM_RANGE
-- =============================================================================
-- BigQuery ML runs multiple trials over the search space and keeps the best
-- model by the tuning objective. Inspect trials with ML.TRIAL_INFO.
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.logistic_regression_income_tuned`
OPTIONS(
  model_type = 'LOGISTIC_REG',
  input_label_cols = ['income_bracket'],
  num_trials = 10,
  max_parallel_trials = 2,
  hparam_tuning_objectives = ['roc_auc'],
  l1_reg = HPARAM_RANGE(0, 1),
  l2_reg = HPARAM_RANGE(0, 1)
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
FROM ML.TRIAL_INFO(MODEL `PROJECT_ID.DATASET.logistic_regression_income_tuned`)
ORDER BY roc_auc DESC;


-- =============================================================================
-- Cleanup
-- =============================================================================
-- DROP MODEL IF EXISTS `PROJECT_ID.DATASET.logistic_regression_income`;
-- DROP MODEL IF EXISTS `PROJECT_ID.DATASET.logistic_regression_income_transform`;
-- DROP MODEL IF EXISTS `PROJECT_ID.DATASET.logistic_regression_income_tuned`;
