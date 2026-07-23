-- Scalers — Progressive SQL Examples (BigQuery ML model-free functions)
-- =============================================================
-- Five manual feature-preprocessing functions that rescale numerical inputs:
-- ML.STANDARD_SCALER, ML.MIN_MAX_SCALER, ML.MAX_ABS_SCALER, ML.ROBUST_SCALER
-- (all analytic -- require an empty OVER()) and ML.NORMALIZER (scalar --
-- row-wise on an ARRAY, no OVER()). All can be used standalone or inside a
-- CREATE MODEL TRANSFORM clause, where the learned statistics travel with
-- the model and reapply automatically at ML.PREDICT.
--
-- Data: bigquery-public-data.ml_datasets.penguins (same dataset as
--       models/kmeans/, models/pca/, models/autoencoder/, models/transform_only/)
--
-- Full reference: ../../RESOURCES.md
-- Official docs:
--   Manual feature preprocessing: https://cloud.google.com/bigquery/docs/manual-preprocessing
--   STANDARD_SCALER: https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-standard-scaler
--   MIN_MAX_SCALER:  https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-min-max-scaler
--   MAX_ABS_SCALER:  https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-max-abs-scaler
--   ROBUST_SCALER:   https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-robust-scaler
--   NORMALIZER:      https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-normalizer


-- =============================================================================
-- Example 1: ML.STANDARD_SCALER -- z-score, and a real gotcha in "matches AVG/STDDEV"
-- =============================================================================
-- VERIFIED LIVE: ML.STANDARD_SCALER uses the POPULATION standard deviation
-- (STDDEV_POP, divide by N), not the sample standard deviation BigQuery's
-- plain STDDEV()/STDDEV_SAMP() computes by default (divide by N-1). The two
-- differ by a small but real amount -- on this column, about 0.15% at the
-- extremes. A naive "let me verify this manually" check using STDDEV(x)
-- will NOT match ML.STANDARD_SCALER's output; STDDEV_POP(x) will.
SELECT
  culmen_length_mm,
  ML.STANDARD_SCALER(culmen_length_mm) OVER() AS standard_scaled,
  (culmen_length_mm - AVG(culmen_length_mm) OVER()) / STDDEV_SAMP(culmen_length_mm) OVER() AS manual_sample_stddev,  -- does NOT match
  (culmen_length_mm - AVG(culmen_length_mm) OVER()) / STDDEV_POP(culmen_length_mm) OVER() AS manual_population_stddev  -- matches exactly
FROM `bigquery-public-data.ml_datasets.penguins`
WHERE culmen_length_mm IS NOT NULL
ORDER BY culmen_length_mm
LIMIT 5;


-- =============================================================================
-- Example 2: ML.MIN_MAX_SCALER -- and the verified prediction-time capping gotcha
-- =============================================================================
SELECT
  culmen_length_mm,
  ML.MIN_MAX_SCALER(culmen_length_mm) OVER() AS min_max_scaled
FROM `bigquery-public-data.ml_datasets.penguins`
WHERE culmen_length_mm IS NOT NULL
ORDER BY culmen_length_mm
LIMIT 5;

-- VERIFIED LIVE via a real CREATE MODEL + ML.TRANSFORM: values outside the
-- training min/max are CAPPED to 0 or 1 at predict time, not extrapolated
-- past the bounds. Trained on culmen_length_mm in [32.1, 59.6]:
--   20.0  (below training min) -> 0.0   (capped, not negative)
--   100.0 (above training max) -> 1.0   (capped, not > 1)
-- See the notebook's Step 2 for the CREATE MODEL + ML.TRANSFORM proof.


-- =============================================================================
-- Example 3: ML.MAX_ABS_SCALER -- preserves sign, no centering
-- =============================================================================
-- Unlike the other scalers, this doesn't shift the data toward zero -- it only
-- divides by the max absolute value, so sign and relative sparsity survive.
SELECT x, ML.MAX_ABS_SCALER(x) OVER() AS max_abs_scaled
FROM UNNEST([-10.0, -5.0, 0.0, 5.0, 8.0, 10.0]) AS x
ORDER BY x;


-- =============================================================================
-- Example 4: ML.ROBUST_SCALER -- outlier-robust, with all 3 optional params
-- =============================================================================
SELECT
  culmen_length_mm,
  ML.ROBUST_SCALER(culmen_length_mm) OVER() AS robust_default,                          -- quantile_range=[25,75], with_median=TRUE, with_quantile_range=TRUE
  ML.ROBUST_SCALER(culmen_length_mm, [10, 90]) OVER() AS robust_custom_quantile_range,   -- wider IQR-equivalent
  ML.ROBUST_SCALER(culmen_length_mm, [25, 75], FALSE) OVER() AS robust_no_median,        -- don't subtract median
  ML.ROBUST_SCALER(culmen_length_mm, [25, 75], TRUE, FALSE) OVER() AS robust_no_scaling  -- just x - median, no IQR division
FROM `bigquery-public-data.ml_datasets.penguins`
WHERE culmen_length_mm IS NOT NULL
ORDER BY culmen_length_mm
LIMIT 5;

-- Outlier robustness, verified live: inject one extreme outlier (500 vs a
-- normal 10-14 range). ML.STANDARD_SCALER's mean/stddev are dragged toward
-- the outlier, compressing every normal point into an indistinguishable
-- narrow band (-0.35 to -0.32). ML.ROBUST_SCALER's median/IQR ignore the
-- outlier entirely -- normal points stay well-spread (-0.8 to 0.8).
WITH data AS (
  SELECT x FROM UNNEST([10.0, 10.5, 11.0, 11.5, 12.0, 12.5, 13.0, 13.5, 14.0, 500.0]) AS x
)
SELECT
  x,
  ROUND(ML.STANDARD_SCALER(x) OVER(), 3) AS standard_scaled,
  ROUND(ML.ROBUST_SCALER(x) OVER(), 3) AS robust_scaled
FROM data
ORDER BY x;


-- =============================================================================
-- Example 5: ML.NORMALIZER -- row-wise unit-norm scaling of an ARRAY (no OVER())
-- =============================================================================
SELECT arr,
  ML.NORMALIZER(arr) AS p2_default,
  ML.NORMALIZER(arr, 1) AS p1_manhattan,
  ML.NORMALIZER(arr, 0) AS p0,
  ML.NORMALIZER(arr, CAST('+inf' AS FLOAT64)) AS p_inf
FROM (SELECT [3.0, 4.0] AS arr);

-- Applied to a real per-penguin feature vector -- each ROW gets unit norm,
-- not each column (semantically different from the column scalers above).
SELECT
  species,
  [culmen_length_mm, culmen_depth_mm, flipper_length_mm] AS measurements,
  ML.NORMALIZER([culmen_length_mm, culmen_depth_mm, flipper_length_mm]) AS normalized
FROM `bigquery-public-data.ml_datasets.penguins`
WHERE culmen_length_mm IS NOT NULL AND culmen_depth_mm IS NOT NULL AND flipper_length_mm IS NOT NULL
LIMIT 3;


-- =============================================================================
-- Example 6: NULLs pass through untouched -- scalers don't impute
-- =============================================================================
-- Verified: a NULL input produces a NULL output (not an error, not 0) --
-- pandas/BigFrames render that NULL as NaN once downloaded, which can look
-- alarming but is just NULL's normal numeric-dtype rendering, not a BQML bug.
-- Pair scalers with ML.IMPUTER first if NULLs need a real value
-- (see ../feature_engineering/ for ML.IMPUTER).
SELECT body_mass_g, ML.STANDARD_SCALER(body_mass_g) OVER() AS scaled
FROM `bigquery-public-data.ml_datasets.penguins`
ORDER BY body_mass_g IS NULL DESC
LIMIT 3;


-- =============================================================================
-- Example 7: All five scalers side by side, one column
-- =============================================================================
SELECT
  culmen_length_mm,
  ROUND(ML.STANDARD_SCALER(culmen_length_mm) OVER(), 3) AS standard,
  ROUND(ML.MIN_MAX_SCALER(culmen_length_mm) OVER(), 3) AS min_max,
  ROUND(ML.MAX_ABS_SCALER(culmen_length_mm) OVER(), 3) AS max_abs,
  ROUND(ML.ROBUST_SCALER(culmen_length_mm) OVER(), 3) AS robust
FROM `bigquery-public-data.ml_datasets.penguins`
WHERE culmen_length_mm IS NOT NULL
ORDER BY culmen_length_mm
LIMIT 5;


-- =============================================================================
-- Example 8: Embedded in a real CREATE MODEL TRANSFORM -- auto-applies at ML.PREDICT
-- =============================================================================
-- Contrast with models/transform_only/: THIS model embeds the TRANSFORM
-- directly (not a standalone TRANSFORM_ONLY pipeline), so ML.PREDICT on raw,
-- unscaled input auto-applies the same scaling used at training time --
-- no separate ML.TRANSFORM call needed, no risk of the "predict on raw data
-- silently gives garbage" gotcha models/transform_only/ Step 7 demonstrates.
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.scalers_downstream_logistic_regression`
TRANSFORM(
  species,
  ML.STANDARD_SCALER(culmen_length_mm) OVER() AS culmen_length_scaled,
  ML.STANDARD_SCALER(culmen_depth_mm) OVER() AS culmen_depth_scaled,
  ML.ROBUST_SCALER(flipper_length_mm) OVER() AS flipper_length_scaled
)
OPTIONS(model_type = 'LOGISTIC_REG', input_label_cols = ['species']) AS
SELECT species, culmen_length_mm, culmen_depth_mm, flipper_length_mm
FROM `bigquery-public-data.ml_datasets.penguins`
WHERE culmen_length_mm IS NOT NULL AND culmen_depth_mm IS NOT NULL AND flipper_length_mm IS NOT NULL;

-- Verified: roc_auc = 1.0, accuracy > 0.99 -- and ML.PREDICT on RAW
-- (unscaled) culmen_length_mm/culmen_depth_mm/flipper_length_mm values
-- predicts correctly, since the scaling is baked into the model.
SELECT species, predicted_species
FROM ML.PREDICT(
  MODEL `PROJECT_ID.DATASET.scalers_downstream_logistic_regression`,
  (SELECT species, culmen_length_mm, culmen_depth_mm, flipper_length_mm
   FROM `bigquery-public-data.ml_datasets.penguins`
   WHERE culmen_length_mm IS NOT NULL AND culmen_depth_mm IS NOT NULL AND flipper_length_mm IS NOT NULL
   LIMIT 5)
);


-- =============================================================================
-- Cleanup
-- =============================================================================
-- DROP MODEL IF EXISTS `PROJECT_ID.DATASET.scalers_downstream_logistic_regression`;
