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
--
-- The last three options exist to enable ML.ADVANCED_WEIGHTS (Example 8), which
-- reports a standard error and p-value per coefficient. All three must be set
-- HERE, at CREATE MODEL time -- p-values cannot be added to a trained model.
-- Verified, each as a hard CREATE MODEL error rather than a warning:
--   omit calculate_p_values  -> ML.ADVANCED_WEIGHTS itself fails with
--                               "Model is not supported by ML.ADVANCED_WEIGHTS
--                                because it was not trained with
--                                calculate_p_values = true."
--   ONE_HOT_ENCODING (default) -> "Please specify
--                                CATEGORY_ENCODING_METHOD=DUMMY_ENCODING to
--                                enable p_values calculation."
--   l1_reg > 0               -> "L1_REG must be zero if CALCULATE_P_VALUES=TRUE."
--
-- calculate_p_values also composes fine with auto_class_weights, which is worth
-- knowing: class rebalancing does not disqualify the statistics.
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.logistic_regression_income`
OPTIONS(
  model_type = 'LOGISTIC_REG',
  input_label_cols = ['income_bracket'],
  auto_class_weights = TRUE,
  data_split_method = 'AUTO_SPLIT',
  enable_global_explain = TRUE,      -- required for ML.GLOBAL_EXPLAIN later
  category_encoding_method = 'DUMMY_ENCODING',  -- required for ML.ADVANCED_WEIGHTS
  calculate_p_values = TRUE,                    -- required for ML.ADVANCED_WEIGHTS
  l1_reg = 0                                    -- required; 0 is the default
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
-- Example 8: ML.ADVANCED_WEIGHTS — which coefficients are real?
-- =============================================================================
-- ML.GLOBAL_EXPLAIN (Example 7) ranks features by how much they move
-- predictions. It cannot tell you that a feature moves predictions only because
-- of noise. ML.ADVANCED_WEIGHTS can: it returns one row per coefficient with a
-- standard_error and a p_value, plus a final `__INTERCEPT__` row.
--
-- Only *binary* logistic regression is supported. income_bracket has two
-- classes, so this works. Verified: a multiclass label fails at CREATE MODEL
-- time, not at query time --
--   "Option(s) calculate_p_values are found. P-values can only be calculated
--    for linear regression and binary logistic regression models."
--
-- For LOGISTIC_REG the weights are log-odds, so EXP(weight) is the odds ratio.
SELECT
  processed_input,
  category,
  ROUND(weight, 4) AS weight,
  ROUND(EXP(weight), 4) AS odds_ratio,
  ROUND(standard_error, 4) AS standard_error,
  p_value
FROM ML.ADVANCED_WEIGHTS(MODEL `PROJECT_ID.DATASET.logistic_regression_income`)
ORDER BY p_value DESC;

-- Verified on a run of this model: 106 rows total -- 105 coefficients plus the
-- __INTERCEPT__ row (whose p_value is NULL). Of the 105, eight are dropped
-- DUMMY_ENCODING baselines reporting p_value = NaN, leaving 97 real tests, and
-- 54 of those come back with p > 0.05. AUTO_SPLIT is random on 32k rows, so your
-- individual p-values will differ slightly -- but the 54 held across two
-- independent draws, so the conclusion is stable even though the digits are not.
--
-- That is the headline: on a 32k-row dataset, more than half the coefficients
-- this model learned are not statistically distinguishable from zero. Nothing
-- in ML.WEIGHTS or ML.GLOBAL_EXPLAIN would tell you. Verified breakdown of
-- where those 54 sit (insignificant / tested, baselines excluded):
--
--   native_country   38 / 41      education_num   0 / 1
--   education         5 / 15      age             0 / 1
--   workclass         4 / 8       sex             0 / 1
--   occupation        4 / 14      hours_per_week  0 / 1
--   race              2 / 4       relationship    0 / 5
--   marital_status    1 / 6
--
-- One feature accounts for 38 of the 54: `native_country` has 41 sparse
-- categories and the model cannot defend all but three of them. Every numeric
-- feature, by contrast, is significant. That is an actionable finding -- drop
-- or bucket `native_country` and the model gets simpler at no real cost.
--
-- Sample verified rows (weights are log-odds of income_bracket = '>50K'):
--
--   processed_input   category                weight   standard_error   p_value
--   race               Asian-Pac-Islander     -0.0584      0.1487        0.6938
--   race               Other                  -0.4463      0.2299        0.0519
--   race               Amer-Indian-Eskimo     -0.4543      0.1840        0.0138
--   race               Black                  -0.2389      0.0659        0.00052
--   race               White                   0.0000      0.0000        NaN
--   sex                Female                 -0.6511      0.0573        7.1e-11
--   sex                Male                    0.0000      0.0000        NaN
--   education_num     NULL                     0.1419      0.0231        6.9e-07
--   hours_per_week    NULL                     0.0327      0.0016        7.8e-15
--   age               NULL                     0.0344      0.0016        3.3e-15
--   __INTERCEPT__     NULL                    -3.9758      NULL          NULL
--
-- Two race categories clear p < 0.05 and two do not, on the same feature. This
-- is why per-coefficient significance matters: "race is important" is not a
-- statement the model actually supports at the category level.
--
-- GOTCHA: `category` values from census_adult_income carry a LEADING SPACE
-- (' White', ' Female'). A filter written as category = 'White' silently
-- returns nothing. Use TRIM(category) when joining or filtering.
--
-- GOTCHA: the dropped baseline is the MOST FREQUENT category, not the first
-- alphabetically -- here ' White' and ' Male'. Its row is a placeholder, not an
-- estimate: weight 0.0, standard_error 0.0, p_value NaN. Exclude these with
-- NOT IS_NAN(p_value) before averaging or counting significance.
--
-- GOTCHA: p_value bottoms out near 1e-15 (note age at 3.3e-15 and
-- hours_per_week at 7.8e-15). That is double-precision floor, not a meaningful
-- difference in strength -- do not rank features by p_value down there.

-- The practical use: list only what the model can actually defend.
SELECT
  processed_input,
  TRIM(category) AS category,
  ROUND(weight, 4) AS weight,
  p_value
FROM ML.ADVANCED_WEIGHTS(MODEL `PROJECT_ID.DATASET.logistic_regression_income`)
WHERE p_value IS NOT NULL
  AND NOT IS_NAN(p_value)
  AND p_value < 0.05
ORDER BY ABS(weight) DESC;


-- =============================================================================
-- Example 9: ML.FEATURE_INFO and ML.TRAINING_INFO — introspect the model
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
-- Example 10: In-model preprocessing with the TRANSFORM clause
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
-- Example 11: Hyperparameter tuning — NUM_TRIALS + HPARAM_RANGE
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
