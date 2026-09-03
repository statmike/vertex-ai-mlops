-- Linear Regression — Progressive SQL Examples (BigQuery ML)
-- =============================================================
-- Regression with CREATE MODEL (model_type = 'LINEAR_REG').
-- Walks the full model lifecycle: create -> evaluate -> predict ->
-- explain -> inspect weights -> in-model preprocessing ->
-- hyperparameter-tune.
--
-- Data: bigquery-public-data.ml_datasets.penguins
--       Label: body_mass_g (continuous)
--       Rows with a NULL label or an invalid sex value ('.') are filtered out.
--
-- Full reference: ../../RESOURCES.md
-- Official docs:
--   CREATE MODEL (GLM: linear & logistic reg): https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-glm
--   The CREATE MODEL statement:                https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create


-- =============================================================================
-- Example 1: CREATE MODEL — train a linear regression model
-- =============================================================================
-- model_type + input_label_cols are the essentials. AUTO_SPLIT holds out a
-- portion of rows for evaluation; enable_global_explain is required for
-- ML.GLOBAL_EXPLAIN later.
--
-- category_encoding_method = 'DUMMY_ENCODING' drops one baseline category per
-- categorical feature instead of one-hot-encoding all of them. This matters
-- for ML.WEIGHTS (Example 6): with the default ONE_HOT_ENCODING, categorical
-- dummies + the intercept are collinear (rank-deficient), so individual
-- category_weights are NOT uniquely identified -- re-running CREATE MODEL
-- with a different random AUTO_SPLIT can swing a category's weight by
-- thousands of grams, even though predictions stay stable. DUMMY_ENCODING
-- fixes this: one category per feature gets a pinned weight of 0.0 (the
-- baseline), and every other category's weight is a stable, well-defined
-- delta from it.
--
-- calculate_p_values = TRUE adds the statistical machinery ML.ADVANCED_WEIGHTS
-- needs (Example 7). It must be set here, at CREATE MODEL time -- there is no
-- way to add p-values to an already-trained model. It also requires
-- DUMMY_ENCODING (already set above) and l1_reg = 0, which is the default but
-- is stated explicitly so the dependency is visible.
--
-- Verified: this CREATE MODEL emits a warning --
--   "Since model contains categorical values, regression statistics will not
--    be calculated for unstandardized intercept."
-- That is expected, not a failure. See Example 7 for how to get intercept
-- statistics anyway.
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.linear_regression_penguins`
OPTIONS(
  model_type = 'LINEAR_REG',
  input_label_cols = ['body_mass_g'],
  data_split_method = 'AUTO_SPLIT',
  category_encoding_method = 'DUMMY_ENCODING',
  calculate_p_values = TRUE,   -- required for ML.ADVANCED_WEIGHTS (Example 7)
  l1_reg = 0,                  -- required for ML.ADVANCED_WEIGHTS; 0 is the default
  enable_global_explain = TRUE
) AS
SELECT
  species, island, culmen_length_mm, culmen_depth_mm, flipper_length_mm, sex, body_mass_g
FROM `bigquery-public-data.ml_datasets.penguins`
WHERE body_mass_g IS NOT NULL AND sex IN ('MALE', 'FEMALE');


-- =============================================================================
-- Example 2: ML.EVALUATE — regression metrics
-- =============================================================================
-- Mean absolute/squared error, R^2, and explained variance on the eval split.
SELECT *
FROM ML.EVALUATE(MODEL `PROJECT_ID.DATASET.linear_regression_penguins`);


-- =============================================================================
-- Example 3: ML.PREDICT — predicted body mass
-- =============================================================================
SELECT
  predicted_body_mass_g,
  species,
  flipper_length_mm
FROM ML.PREDICT(
  MODEL `PROJECT_ID.DATASET.linear_regression_penguins`,
  (SELECT * FROM `bigquery-public-data.ml_datasets.penguins`
   WHERE body_mass_g IS NOT NULL AND sex IN ('MALE', 'FEMALE') LIMIT 10)
);


-- =============================================================================
-- Example 4: ML.EXPLAIN_PREDICT — per-row feature attributions
-- =============================================================================
-- Shows which features pushed each individual prediction up or down.
SELECT
  predicted_body_mass_g,
  top_feature_attributions
FROM ML.EXPLAIN_PREDICT(
  MODEL `PROJECT_ID.DATASET.linear_regression_penguins`,
  (SELECT * FROM `bigquery-public-data.ml_datasets.penguins`
   WHERE body_mass_g IS NOT NULL AND sex IN ('MALE', 'FEMALE') LIMIT 5),
  STRUCT(5 AS top_k_features)
);


-- =============================================================================
-- Example 5: ML.GLOBAL_EXPLAIN — overall feature importance
-- =============================================================================
-- Requires enable_global_explain = TRUE at CREATE MODEL time (see Example 1).
SELECT *
FROM ML.GLOBAL_EXPLAIN(MODEL `PROJECT_ID.DATASET.linear_regression_penguins`)
ORDER BY attribution DESC;


-- =============================================================================
-- Example 6: ML.WEIGHTS — model coefficients
-- =============================================================================
-- Unlike classifiers, LINEAR_REG's weights are directly interpretable: e.g.
-- "each additional mm of flipper length adds ~16g of predicted body mass."
-- Numeric features get a single `weight`; categorical features expand into
-- `category_weights`. With DUMMY_ENCODING (see Example 1), one category per
-- feature is the pinned baseline (weight 0.0) and the rest are stable deltas
-- from it.
SELECT *
FROM ML.WEIGHTS(MODEL `PROJECT_ID.DATASET.linear_regression_penguins`);


-- =============================================================================
-- Example 7: ML.ADVANCED_WEIGHTS — weights with standard errors and p-values
-- =============================================================================
-- ML.WEIGHTS (Example 6) answers "how big is this coefficient?"
-- ML.ADVANCED_WEIGHTS answers "is it distinguishable from zero at all?"
--
-- It flattens the nested shape of ML.WEIGHTS: instead of numeric features in
-- `weight` and categoricals nested in `category_weights`, every coefficient is
-- one row -- `processed_input`, `category`, `weight`, `standard_error`,
-- `p_value` -- plus a final `__INTERCEPT__` row.
--
-- Requires calculate_p_values = TRUE, DUMMY_ENCODING, and l1_reg = 0 at
-- CREATE MODEL time (all set in Example 1). Total feature cardinality must be
-- under 1,000, and only LINEAR_REG and *binary* LOGISTIC_REG are supported.
SELECT
  processed_input,
  category,
  ROUND(weight, 4) AS weight,
  ROUND(standard_error, 4) AS standard_error,
  p_value
FROM ML.ADVANCED_WEIGHTS(MODEL `PROJECT_ID.DATASET.linear_regression_penguins`);

-- Verified results on this model (333 rows, closed-form NORMAL_EQUATION solver,
-- so these are reproducible rather than split-dependent):
--
--   processed_input     category      weight      standard_error   p_value
--   species             Adelie...      0.00         0.00           NaN
--   species             Chinstrap   -260.31        87.35           0.0033
--   species             Gentoo       987.76       135.37           5.9e-08
--   island              Biscoe         0.00         0.00           NaN
--   island              Dream        -13.10        57.74           0.8206
--   island              Torgersen    -48.06        60.09           0.4239
--   culmen_length_mm    NULL          18.19         7.04           0.0101
--   culmen_depth_mm     NULL          67.58        19.55           0.00085
--   flipper_length_mm   NULL          16.24         2.90           2.6e-06
--   sex                 MALE           0.00         0.00           NaN
--   sex                 FEMALE      -387.22        47.48           1.1e-08
--   __INTERCEPT__       NULL       -1112.80        NULL            NULL
--
-- The payoff: `island` is the only feature whose categories are NOT significant
-- (p = 0.82 and p = 0.42). Once species is in the model, where a penguin was
-- found tells you nothing more about its mass -- the islands differ because
-- different species live on them. ML.WEIGHTS shows non-zero island weights and
-- gives you no way to notice this; ML.ADVANCED_WEIGHTS makes it obvious.
-- Verified in the data: Gentoo appears only on Biscoe (119 rows) and Chinstrap
-- only on Dream (68), so island is largely a restatement of species.
--
-- GOTCHA: the dropped DUMMY_ENCODING baseline is the MOST FREQUENT category,
-- not the first alphabetically. Here that is Adelie (146 rows), Biscoe (163),
-- and MALE (168) -- note MALE wins over the alphabetically-earlier FEMALE.
-- Baseline rows report weight = 0.0 and standard_error = 0.0 with p_value =
-- NaN. They are placeholders, not estimates: filter with IS_NAN(p_value)
-- rather than treating 0.0 as a measured standard error.
--
-- GOTCHA: `__INTERCEPT__` comes back with NULL standard_error and NULL p_value
-- whenever the model has categorical features -- the warning Example 1 emits at
-- CREATE time. Pass STRUCT(TRUE AS standardize) to get them.

-- The standardize option rescales each numeric feature to zero mean and unit
-- variance before reporting, which also makes intercept statistics available.
SELECT
  processed_input,
  ROUND(weight, 4) AS weight,
  ROUND(standard_error, 4) AS standard_error,
  p_value
FROM ML.ADVANCED_WEIGHTS(
  MODEL `PROJECT_ID.DATASET.linear_regression_penguins`,
  STRUCT(TRUE AS standardize)
)
WHERE category IS NULL;

-- Verified: __INTERCEPT__ now reports weight 4110.72, standard_error 71.00,
-- p_value 0.0. Standardizing changes what the weights mean -- flipper_length_mm
-- goes from 16.24 (grams per mm) to 227.60 (grams per standard deviation), which
-- is the number to use when ranking features against each other.
--
-- Verified: the p_values are IDENTICAL either way (culmen_length_mm is 0.0101
-- in both). Standardizing scales weight and standard_error by the same factor,
-- so the t-statistic -- and therefore significance -- is unchanged. Standardize
-- to compare effect sizes, not to change which features count as significant.
--
-- GOTCHA: do not read the standardized intercept as the average label. It is
-- 4110.72 here while mean body_mass_g is 4207.06. Categorical features stay
-- dummy-coded rather than centered, so the intercept is the prediction at mean
-- numeric features AND baseline categories -- an Adelie male on Biscoe.


-- =============================================================================
-- Example 8: ML.FEATURE_INFO and ML.TRAINING_INFO — introspect the model
-- =============================================================================
-- FEATURE_INFO: per-feature statistics seen during training.
SELECT *
FROM ML.FEATURE_INFO(MODEL `PROJECT_ID.DATASET.linear_regression_penguins`);

-- TRAINING_INFO: per-iteration loss curve. For small/unregularized problems
-- like this one, BQML auto-selects the NORMAL_EQUATION solver, which trains
-- in a single closed-form pass -- expect exactly one row with no eval_loss.
SELECT
  iteration,
  loss,
  eval_loss,
  learning_rate,
  duration_ms
FROM ML.TRAINING_INFO(MODEL `PROJECT_ID.DATASET.linear_regression_penguins`)
ORDER BY iteration;


-- =============================================================================
-- Example 9: In-model preprocessing with the TRANSFORM clause
-- =============================================================================
-- TRANSFORM applies preprocessing that is saved with the model and reapplied
-- automatically at predict time -- no need to repeat it in ML.PREDICT.
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.linear_regression_penguins_transform`
TRANSFORM(
  ML.STANDARD_SCALER(culmen_length_mm) OVER() AS culmen_length_mm,
  ML.STANDARD_SCALER(flipper_length_mm) OVER() AS flipper_length_mm,
  species, island, sex, body_mass_g
)
OPTIONS(
  model_type = 'LINEAR_REG',
  input_label_cols = ['body_mass_g']
) AS
SELECT species, island, culmen_length_mm, flipper_length_mm, sex, body_mass_g
FROM `bigquery-public-data.ml_datasets.penguins`
WHERE body_mass_g IS NOT NULL AND sex IN ('MALE', 'FEMALE');


-- =============================================================================
-- Example 10: Hyperparameter tuning — NUM_TRIALS + HPARAM_RANGE
-- =============================================================================
-- BigQuery ML runs multiple trials over the search space and keeps the best
-- model by the tuning objective. Inspect trials with ML.TRIAL_INFO.
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.linear_regression_penguins_tuned`
OPTIONS(
  model_type = 'LINEAR_REG',
  input_label_cols = ['body_mass_g'],
  num_trials = 10,
  max_parallel_trials = 2,
  hparam_tuning_objectives = ['r2_score'],
  l1_reg = HPARAM_RANGE(0, 10),
  l2_reg = HPARAM_RANGE(0, 10)
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
FROM ML.TRIAL_INFO(MODEL `PROJECT_ID.DATASET.linear_regression_penguins_tuned`)
ORDER BY r2_score DESC;


-- =============================================================================
-- Cleanup
-- =============================================================================
-- DROP MODEL IF EXISTS `PROJECT_ID.DATASET.linear_regression_penguins`;
-- DROP MODEL IF EXISTS `PROJECT_ID.DATASET.linear_regression_penguins_transform`;
-- DROP MODEL IF EXISTS `PROJECT_ID.DATASET.linear_regression_penguins_tuned`;
