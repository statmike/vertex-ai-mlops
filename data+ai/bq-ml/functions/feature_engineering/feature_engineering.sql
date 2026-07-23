-- Feature Engineering — Progressive SQL Examples (BigQuery ML model-free functions)
-- =============================================================
-- ML.IMPUTER fills NULLs; ML.FEATURE_CROSS builds categorical interaction
-- terms; ML.POLYNOMIAL_EXPAND builds numeric interaction/power terms. All
-- three are usable standalone or inside a CREATE MODEL TRANSFORM clause --
-- but ML.FEATURE_CROSS and ML.POLYNOMIAL_EXPAND are NOT exportable once
-- embedded (verified live below), unlike ML.IMPUTER.
--
-- Data: bigquery-public-data.ml_datasets.penguins (same dataset as
--       ../scalers/, models/kmeans/, models/pca/, models/transform_only/)
--
-- Full reference: ../../RESOURCES.md
-- Official docs:
--   ML.IMPUTER:           https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-imputer
--   ML.FEATURE_CROSS:     https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-feature-cross
--   ML.POLYNOMIAL_EXPAND: https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-polynomial-expand


-- =============================================================================
-- Example 1: ML.IMPUTER -- fill NULLs with a train-time statistic
-- =============================================================================
SELECT
  body_mass_g,
  ML.IMPUTER(body_mass_g, 'mean') OVER() AS imputed_mean,
  ML.IMPUTER(body_mass_g, 'median') OVER() AS imputed_median,
  ML.IMPUTER(sex, 'most_frequent') OVER() AS sex_imputed_mode
FROM `bigquery-public-data.ml_datasets.penguins`
ORDER BY body_mass_g IS NULL DESC
LIMIT 3;

-- 'mean'/'median' reject string inputs; 'most_frequent' works for either
-- numeric or string columns. Requires OVER() (analytic).


-- =============================================================================
-- Example 2: ML.IMPUTER embedded in TRANSFORM -- exportable, auto-applies at predict
-- =============================================================================
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.feature_engineering_imputer_downstream`
TRANSFORM(
  species,
  ML.IMPUTER(body_mass_g, 'mean') OVER() AS body_mass_imputed,
  culmen_length_mm, culmen_depth_mm, flipper_length_mm
)
OPTIONS(model_type = 'LOGISTIC_REG', input_label_cols = ['species']) AS
SELECT species, body_mass_g, culmen_length_mm, culmen_depth_mm, flipper_length_mm
FROM `bigquery-public-data.ml_datasets.penguins`
WHERE culmen_length_mm IS NOT NULL AND culmen_depth_mm IS NOT NULL AND flipper_length_mm IS NOT NULL;

-- Verified: predicting with a NULL body_mass_g at predict time still works
-- correctly -- the model auto-imputes using the TRAINING mean, no error.
SELECT species, body_mass_g, predicted_species
FROM ML.PREDICT(
  MODEL `PROJECT_ID.DATASET.feature_engineering_imputer_downstream`,
  (SELECT species, CAST(NULL AS FLOAT64) AS body_mass_g, culmen_length_mm, culmen_depth_mm, flipper_length_mm
   FROM `bigquery-public-data.ml_datasets.penguins`
   WHERE culmen_length_mm IS NOT NULL AND culmen_depth_mm IS NOT NULL AND flipper_length_mm IS NOT NULL
   LIMIT 3)
);


-- =============================================================================
-- Example 3: ML.FEATURE_CROSS -- categorical interaction terms
-- =============================================================================
SELECT island, sex,
  ML.FEATURE_CROSS(STRUCT(island, sex)) AS crossed
FROM `bigquery-public-data.ml_datasets.penguins`
WHERE sex IS NOT NULL
LIMIT 3;
-- e.g. {'island_sex': 'Dream_FEMALE'} -- one field per crossed combination,
-- named <col_a>_<col_b>, valued <val_a>_<val_b>. Scalar function, no OVER().


-- =============================================================================
-- Example 4: ML.FEATURE_CROSS in a real TRANSFORM -- trains/predicts fine,
-- but the model is NOT exportable (verified live, exact error captured)
-- =============================================================================
-- The legacy source notebooks only ever showed ML.FEATURE_CROSS standalone,
-- never actually plugged into a live CREATE MODEL. It DOES work for
-- training and ML.PREDICT -- the "not exportable" limitation only bites at
-- EXPORT MODEL time, not before.
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.scratch_featurecross_transform_demo`
TRANSFORM(
  species,
  ML.FEATURE_CROSS(STRUCT(island, sex)) AS island_sex_cross
)
OPTIONS(model_type = 'LOGISTIC_REG', input_label_cols = ['species']) AS
SELECT species, island, sex
FROM `bigquery-public-data.ml_datasets.penguins`;
-- Trains and predicts fine (ML.PREDICT works normally). Then:

EXPORT MODEL `PROJECT_ID.DATASET.scratch_featurecross_transform_demo`
OPTIONS (URI = 'gs://BUCKET/bq_ml/feature_engineering/scratch_export/');
-- VERIFIED LIVE, exact error:
--   Error in query string: Error processing job '...': Model TRANSFORM
--   contains unsupported function for exporting. Please see
--   https://cloud.google.com/bigquery-ml/docs/exporting-models#limitations,
--   or contact bqml-feedback@google.com.
-- Same limitation applies to ML.POLYNOMIAL_EXPAND. A model that needs
-- portability/serving outside BigQuery must compute crosses/polynomial
-- terms in the INPUT query instead of inside TRANSFORM.


-- =============================================================================
-- Example 5: ML.POLYNOMIAL_EXPAND -- numeric interaction/power terms
-- =============================================================================
SELECT
  culmen_length_mm, culmen_depth_mm,
  ML.POLYNOMIAL_EXPAND(STRUCT(culmen_length_mm AS length, culmen_depth_mm AS depth), 2) AS expanded
FROM `bigquery-public-data.ml_datasets.penguins`
WHERE culmen_length_mm IS NOT NULL AND culmen_depth_mm IS NOT NULL
LIMIT 2;
-- e.g. {'length':36.6,'depth':18.4,'length_length':1339.56,'length_depth':673.44,'depth_depth':338.56}
-- <=10 features, no duplicates, all must be named. degree range [1,4], default 2.


-- =============================================================================
-- Example 6: Compounding -- a scalar function CAN wrap an analytic function's result
-- =============================================================================
-- GOTCHA: an analytic function cannot be an argument to another analytic
-- function, but a scalar function (ML.POLYNOMIAL_EXPAND, ML.FEATURE_CROSS)
-- CAN take an analytic function's result (ML.IMPUTER) as an argument.
SELECT
  body_mass_g,
  ML.POLYNOMIAL_EXPAND(
    STRUCT(ML.IMPUTER(body_mass_g, 'mean') OVER() AS mass_imputed),
    2
  ) AS expanded
FROM `bigquery-public-data.ml_datasets.penguins`
ORDER BY body_mass_g IS NULL DESC
LIMIT 3;


-- =============================================================================
-- Cleanup
-- =============================================================================
-- DROP MODEL IF EXISTS `PROJECT_ID.DATASET.feature_engineering_imputer_downstream`;
-- (scratch_featurecross_transform_demo is created and dropped within the notebook itself)
