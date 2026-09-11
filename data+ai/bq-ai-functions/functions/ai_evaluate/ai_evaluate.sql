-- AI.EVALUATE — Progressive SQL Examples
-- ========================================
-- Table-valued function with two branches. Given data_col and timestamp_col it
-- evaluates TimesFM forecast accuracy against actual values. Given label_col it
-- evaluates TabFM tabular predictions against ground truth labels, from the same
-- training and prediction relations AI.PREDICT takes.
--
-- No connection, no CREATE MODEL, no endpoint required on either branch.
--
-- Branch selection: data_col + timestamp_col => TimesFM, label_col => TabFM.
--   The two sets are mutually exclusive. label_col is required on the TabFM
--   branch, unlike AI.PREDICT where it defaults to 'label'. A numeric label_col
--   evaluates regression, a STRING or BOOL label_col evaluates classification.
--
-- Returns (TimesFM): mean_absolute_error, mean_squared_error, root_mean_squared_error,
--          mean_absolute_percentage_error, symmetric_mean_absolute_percentage_error,
--          mean_absolute_scaled_error, ai_evaluate_status
-- Returns (TabFM, numeric label): mean_absolute_error, mean_squared_error,
--          mean_squared_log_error, median_absolute_error, r2_score, explained_variance
-- Returns (TabFM, STRING label): precision, recall, accuracy, f1_score
--          (precision, recall and f1_score macro-averaged across all classes)
-- Returns (TabFM, BOOL label): the same four names, but NOT averaged -- BOOL is
--          scored as binary, so precision, recall and f1_score describe the
--          positive (TRUE) class alone. accuracy is identical under either type.
--          Measured on one imbalanced problem (12 positives of 62): the BOOL
--          label returned precision 0.5217391304347826 and recall 1.0, while the
--          STRING rendering of the identical values returned 0.7608695652173914
--          and 0.89 -- the two-class means. Four isolated runs of each agreed.
--          ML.METRICS follows the same rule; the side-by-side lives in
--          ../../../bq-ml/functions/evaluation/evaluation.sql
-- Note: the TabFM branch returns no ai_evaluate_status column and no RMSE.
--
-- TabFM limits (documented on the AI.PREDICT page): at most 20 feature columns
--   and at most 10 classes. Keep the training relation to a few thousand rows.
--
-- Reproducibility: this function is NOT reproducible run to run, on either
--   branch, and pinning `model` does not fix it. On a deterministic synthetic
--   series with `model` and `context_window` both pinned and the query cache
--   off, 2 of 16 runs returned mean_absolute_error 0.5913808905590097 where the
--   other 14 returned 0.8652198481135486 -- a ~32% swing. The majority value is
--   the correct one: it equals MAE computed by hand from AI.FORECAST output
--   over the same history and horizon. AI.FORECAST itself is stable. Not
--   explained by context window (every legal value swept), horizon truncation,
--   or version mixing -- it occurs on TimesFM 2.0 and 2.5 alike. Mechanism
--   unknown. Materialize the metric once rather than re-running this function,
--   and when a number must be defensible recompute it from AI.FORECAST output
--   with ordinary SQL, which is deterministic.
--
-- Full reference: ../../RESOURCES.md
-- Official docs: https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-evaluate


-- =============================================================================
-- Example 1: Basic evaluation
-- =============================================================================
SELECT *
FROM AI.EVALUATE(
  (SELECT * FROM `PROJECT_ID.DATASET.ai_evaluate_full` WHERE date < '2024-11-01'),
  (SELECT * FROM `PROJECT_ID.DATASET.ai_evaluate_full` WHERE date >= '2024-11-01'),
  data_col => 'daily_sales',
  timestamp_col => 'date'
);


-- =============================================================================
-- Example 2: Limited horizon
-- =============================================================================
SELECT *
FROM AI.EVALUATE(
  (SELECT * FROM `PROJECT_ID.DATASET.ai_evaluate_full` WHERE date < '2024-11-01'),
  (SELECT * FROM `PROJECT_ID.DATASET.ai_evaluate_full` WHERE date >= '2024-11-01'),
  data_col => 'daily_sales',
  timestamp_col => 'date',
  horizon => 14
);


-- =============================================================================
-- Example 3: Comparing model versions
-- =============================================================================
-- TimesFM 2.0
SELECT 'TimesFM 2.0' AS model,
  ROUND(mean_absolute_error, 2) AS mae,
  ROUND(root_mean_squared_error, 2) AS rmse
FROM AI.EVALUATE(
  (SELECT * FROM `PROJECT_ID.DATASET.ai_evaluate_full` WHERE date < '2024-11-01'),
  (SELECT * FROM `PROJECT_ID.DATASET.ai_evaluate_full` WHERE date >= '2024-11-01'),
  data_col => 'daily_sales', timestamp_col => 'date',
  horizon => 30, model => 'TimesFM 2.0'
);


-- =============================================================================
-- Example 4: Setting the context window
-- =============================================================================
-- context_window controls how many historical points the model reads.
-- TimesFM 2.0: 64, 128, 256, 512, 1024, 2048
-- TimesFM 2.5: 64, 128, 256, 512, 1024, 2048, 4096, 8192, 15360
SELECT 64 AS context_window,
  ROUND(mean_absolute_error, 2) AS mae,
  ROUND(root_mean_squared_error, 2) AS rmse
FROM AI.EVALUATE(
  (SELECT * FROM `PROJECT_ID.DATASET.ai_evaluate_full` WHERE date < '2024-11-01'),
  (SELECT * FROM `PROJECT_ID.DATASET.ai_evaluate_full` WHERE date >= '2024-11-01'),
  data_col => 'daily_sales', timestamp_col => 'date',
  horizon => 30, context_window => 64
)
UNION ALL
SELECT 512 AS context_window,
  ROUND(mean_absolute_error, 2) AS mae,
  ROUND(root_mean_squared_error, 2) AS rmse
FROM AI.EVALUATE(
  (SELECT * FROM `PROJECT_ID.DATASET.ai_evaluate_full` WHERE date < '2024-11-01'),
  (SELECT * FROM `PROJECT_ID.DATASET.ai_evaluate_full` WHERE date >= '2024-11-01'),
  data_col => 'daily_sales', timestamp_col => 'date',
  horizon => 30, context_window => 512
);


-- =============================================================================
-- Example 5: TabFM regression evaluation
-- =============================================================================
-- The TabFM branch: label_col replaces data_col and timestamp_col, and the two
-- positional relations become training data and prediction data — the same pair
-- AI.PREDICT takes. body_mass_g is FLOAT64, so regression is evaluated.
-- The prediction relation must carry the ground truth label column.
-- FARM_FINGERPRINT gives a deterministic split (239 training rows, 94 held out);
-- the RAND() split shown in the docs is not reproducible across runs.
WITH penguins AS (
  SELECT
    species, island, culmen_length_mm, culmen_depth_mm, flipper_length_mm, sex, body_mass_g,
    IF(ABS(MOD(FARM_FINGERPRINT(FORMAT('%t', t)), 10)) < 7, 'TRAIN', 'TEST') AS split
  FROM `bigquery-public-data.ml_datasets.penguins` AS t
  WHERE body_mass_g IS NOT NULL AND sex IN ('MALE', 'FEMALE')
)
SELECT *
FROM AI.EVALUATE(
  (SELECT * EXCEPT(split) FROM penguins WHERE split = 'TRAIN'),
  (SELECT * EXCEPT(split) FROM penguins WHERE split = 'TEST'),
  label_col => 'body_mass_g'
);


-- =============================================================================
-- Example 6: TabFM classification evaluation
-- =============================================================================
-- Same relations, same call — only label_col changes. sex is a STRING, so
-- classification is evaluated: precision, recall, accuracy, f1_score.
-- precision, recall and f1_score are macro-averaged across classes; there is no
-- log_loss and no roc_auc, unlike ML.EVALUATE on a trained classification model.
WITH penguins AS (
  SELECT
    species, island, culmen_length_mm, culmen_depth_mm, flipper_length_mm, sex, body_mass_g,
    IF(ABS(MOD(FARM_FINGERPRINT(FORMAT('%t', t)), 10)) < 7, 'TRAIN', 'TEST') AS split
  FROM `bigquery-public-data.ml_datasets.penguins` AS t
  WHERE body_mass_g IS NOT NULL AND sex IN ('MALE', 'FEMALE')
)
SELECT *
FROM AI.EVALUATE(
  (SELECT * EXCEPT(split) FROM penguins WHERE split = 'TRAIN'),
  (SELECT * EXCEPT(split) FROM penguins WHERE split = 'TEST'),
  label_col => 'sex'
);
