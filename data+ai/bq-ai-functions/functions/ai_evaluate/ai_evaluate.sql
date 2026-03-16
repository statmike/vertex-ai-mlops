-- AI.EVALUATE — Progressive SQL Examples
-- ========================================
-- Table-valued function that evaluates TimesFM forecast accuracy.
-- Compares forecast against actual values.
--
-- Returns: mean_absolute_error, mean_squared_error, root_mean_squared_error,
--          mean_absolute_percentage_error, symmetric_mean_absolute_percentage_error,
--          ai_evaluate_status
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
