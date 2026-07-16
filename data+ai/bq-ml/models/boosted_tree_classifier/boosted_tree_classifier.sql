-- Boosted Tree Classifier — Progressive SQL Examples (BigQuery ML)
-- =============================================================
-- Binary classification with CREATE MODEL (model_type = 'BOOSTED_TREE_CLASSIFIER'),
-- an XGBoost gradient-boosted tree ensemble. Walks the full model lifecycle:
-- create -> evaluate -> inspect -> predict -> explain -> hyperparameter-tune.
--
-- Data: bigquery-public-data.ml_datasets.census_adult_income
--       Label: income_bracket ('<=50K' / '>50K')
--       Same data + label as models/logistic_regression/ -- compare roc_auc
--       and feature attributions between the two techniques directly.
--
-- Full reference: ../../RESOURCES.md
-- Official docs:
--   CREATE MODEL (boosted tree): https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-boosted-tree
--   The CREATE MODEL statement:  https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create


-- =============================================================================
-- Example 1: CREATE MODEL — train a boosted tree classifier
-- =============================================================================
-- model_type + input_label_cols are the essentials. AUTO_SPLIT holds out a
-- portion of rows for evaluation; AUTO_CLASS_WEIGHTS balances the classes;
-- enable_global_explain is required for ML.GLOBAL_EXPLAIN later.
--
-- Training takes several minutes: the first boosting iteration pays a large
-- one-time data-loading/indexing cost (XGBoost workers spin up), then each
-- subsequent iteration is fast. Don't be alarmed by a slow first iteration in
-- ML.TRAINING_INFO (Example 8) -- that's expected, not a stall.
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.boosted_tree_classifier_income`
OPTIONS(
  model_type = 'BOOSTED_TREE_CLASSIFIER',
  input_label_cols = ['income_bracket'],
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
-- Precision, recall, accuracy, f1, log_loss, roc_auc on the eval split.
SELECT *
FROM ML.EVALUATE(MODEL `PROJECT_ID.DATASET.boosted_tree_classifier_income`);


-- =============================================================================
-- Example 3: ML.CONFUSION_MATRIX — counts by predicted vs actual
-- =============================================================================
SELECT *
FROM ML.CONFUSION_MATRIX(MODEL `PROJECT_ID.DATASET.boosted_tree_classifier_income`);


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
FROM ML.ROC_CURVE(MODEL `PROJECT_ID.DATASET.boosted_tree_classifier_income`)
ORDER BY threshold;


-- =============================================================================
-- Example 5: ML.PREDICT — predicted label + class probabilities
-- =============================================================================
SELECT
  predicted_income_bracket,
  predicted_income_bracket_probs
FROM ML.PREDICT(
  MODEL `PROJECT_ID.DATASET.boosted_tree_classifier_income`,
  (SELECT * FROM `bigquery-public-data.ml_datasets.census_adult_income` LIMIT 10)
);


-- =============================================================================
-- Example 6: ML.EXPLAIN_PREDICT — per-row feature attributions
-- =============================================================================
SELECT
  predicted_income_bracket,
  top_feature_attributions
FROM ML.EXPLAIN_PREDICT(
  MODEL `PROJECT_ID.DATASET.boosted_tree_classifier_income`,
  (SELECT * FROM `bigquery-public-data.ml_datasets.census_adult_income` LIMIT 10),
  STRUCT(5 AS top_k_features)
);


-- =============================================================================
-- Example 7: ML.GLOBAL_EXPLAIN and ML.FEATURE_IMPORTANCE — two views of importance
-- =============================================================================
-- ML.GLOBAL_EXPLAIN: mean absolute Shapley-style attribution across the eval set.
-- ML.FEATURE_IMPORTANCE: tree-specific, split-based (weight/gain/cover) -- this
-- function does NOT apply to GLMs (see models/logistic_regression/), only to
-- tree ensembles. The two can rank features differently -- that's expected;
-- they measure different things (attribution vs. how the trees actually split).
SELECT *
FROM ML.GLOBAL_EXPLAIN(MODEL `PROJECT_ID.DATASET.boosted_tree_classifier_income`)
ORDER BY attribution DESC;

SELECT *
FROM ML.FEATURE_IMPORTANCE(MODEL `PROJECT_ID.DATASET.boosted_tree_classifier_income`)
ORDER BY importance_gain DESC;


-- =============================================================================
-- Example 8: ML.FEATURE_INFO and ML.TRAINING_INFO — introspect the model
-- =============================================================================
SELECT *
FROM ML.FEATURE_INFO(MODEL `PROJECT_ID.DATASET.boosted_tree_classifier_income`);

-- TRAINING_INFO: per-iteration loss curve. early_stop=TRUE (the default) stops
-- once improvement falls below min_rel_progress -- expect fewer than the
-- max_iterations=20 default. Note iteration numbering starts at 1 (not 0, as
-- in the LOGISTIC_REG/LINEAR_REG GLM notebooks).
SELECT
  iteration,
  loss,
  eval_loss,
  learning_rate,
  duration_ms
FROM ML.TRAINING_INFO(MODEL `PROJECT_ID.DATASET.boosted_tree_classifier_income`)
ORDER BY iteration;


-- =============================================================================
-- Example 9: EXPORT MODEL — visualize an individual tree
-- =============================================================================
-- EXPORT MODEL writes the trained ensemble to Cloud Storage as an XGBoost
-- Booster file (model.bst). Downloading it and loading it with the `xgboost`
-- Python library lets you plot an individual tree's structure -- see the
-- notebook for the Python side (xgboost.plot_tree).
--
-- GOTCHA (verified): BQML exports using XGBoost 0.82's legacy binary format.
-- Modern xgboost (2.0+, the current pip default) CANNOT load this file --
-- xgb.Booster().load_model('model.bst') raises "Check failed: str[0] == '{'".
-- Pin an older version to load it (verified working: xgboost==1.7.6).
-- Also: the export does not preserve feature names -- Booster.feature_names
-- comes back None; set it manually to the training query's non-label column
-- order (assumed 1:1, verified against the split thresholds in this example).
EXPORT MODEL `PROJECT_ID.DATASET.boosted_tree_classifier_income`
OPTIONS (URI = 'gs://BUCKET/bq_ml/boosted_tree_classifier/model');


-- =============================================================================
-- Example 10: In-model preprocessing with the TRANSFORM clause
-- =============================================================================
-- TRANSFORM applies preprocessing that is saved with the model and reapplied
-- automatically at predict time. Here we quantile-bucketize age into 10 bins
-- instead of using it as a raw numeric feature -- ML.QUANTILE_BUCKETIZE is an
-- analytic function so it requires an empty OVER().
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.boosted_tree_classifier_income_transform`
TRANSFORM(
  ML.QUANTILE_BUCKETIZE(age, 10) OVER() AS age_bucket,
  education, marital_status, occupation, relationship, hours_per_week, income_bracket
)
OPTIONS(
  model_type = 'BOOSTED_TREE_CLASSIFIER',
  input_label_cols = ['income_bracket'],
  auto_class_weights = TRUE
) AS
SELECT age, education, marital_status, occupation, relationship, hours_per_week, income_bracket
FROM `bigquery-public-data.ml_datasets.census_adult_income`;

-- Predict on RAW rows -- bucketizing is applied automatically inside the model.
SELECT predicted_income_bracket, age
FROM ML.PREDICT(
  MODEL `PROJECT_ID.DATASET.boosted_tree_classifier_income_transform`,
  (SELECT * FROM `bigquery-public-data.ml_datasets.census_adult_income` LIMIT 5)
);


-- =============================================================================
-- Example 11: Hyperparameter tuning — NUM_TRIALS + HPARAM_RANGE
-- =============================================================================
-- Tune the boosting shrinkage (learn_rate) and tree depth. Inspect trials
-- with ML.TRIAL_INFO.
--
-- Individual trials can occasionally fail with a transient error (status =
-- 'FAILED', e.g. "An internal error happened during trial training"), which
-- shows up as a NULL objective metric for that trial in ML.TRIAL_INFO. This
-- does not fail the overall job -- BigQuery keeps the best-performing
-- *successful* trial as is_optimal. Check status/error_message if a trial's
-- metric looks off.
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.boosted_tree_classifier_income_tuned`
OPTIONS(
  model_type = 'BOOSTED_TREE_CLASSIFIER',
  input_label_cols = ['income_bracket'],
  auto_class_weights = TRUE,
  num_trials = 6,
  max_parallel_trials = 3,
  hparam_tuning_objectives = ['roc_auc'],
  learn_rate = HPARAM_RANGE(0.05, 0.3),
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
FROM ML.TRIAL_INFO(MODEL `PROJECT_ID.DATASET.boosted_tree_classifier_income_tuned`)
ORDER BY roc_auc DESC;


-- =============================================================================
-- Cleanup
-- =============================================================================
-- DROP MODEL IF EXISTS `PROJECT_ID.DATASET.boosted_tree_classifier_income`;
-- DROP MODEL IF EXISTS `PROJECT_ID.DATASET.boosted_tree_classifier_income_transform`;
-- DROP MODEL IF EXISTS `PROJECT_ID.DATASET.boosted_tree_classifier_income_tuned`;
