-- AI.FORECAST — Progressive SQL Examples
-- ========================================
-- Table-valued function for time series forecasting using TimesFM.
-- No model creation or training required.
--
-- Returns: forecast_timestamp, forecast_value, confidence_level,
--          prediction_interval_lower/upper_bound, ai_forecast_status
--
-- Full reference: ../../RESOURCES.md
-- Official docs: https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-forecast


-- =============================================================================
-- Setup: Create sample time series
-- =============================================================================
CREATE OR REPLACE TABLE `PROJECT_ID.DATASET.ai_forecast_sales` AS
WITH dates AS (
  SELECT date FROM UNNEST(GENERATE_DATE_ARRAY('2024-01-01', '2024-12-31')) AS date
)
SELECT date,
  GREATEST(0, 1000 + EXTRACT(DAYOFYEAR FROM date) * 2
    + CASE EXTRACT(DAYOFWEEK FROM date)
        WHEN 1 THEN -200 WHEN 7 THEN 300 WHEN 6 THEN 200 ELSE 0
      END
    + CAST(200 * (RAND() - 0.5) AS INT64)
  ) AS daily_sales
FROM dates;


-- =============================================================================
-- Example 1: Basic forecast (default 10 time steps)
-- =============================================================================
SELECT *
FROM AI.FORECAST(
  TABLE `PROJECT_ID.DATASET.ai_forecast_sales`,
  data_col => 'daily_sales',
  timestamp_col => 'date'
);


-- =============================================================================
-- Example 2: Custom horizon
-- =============================================================================
SELECT *
FROM AI.FORECAST(
  TABLE `PROJECT_ID.DATASET.ai_forecast_sales`,
  data_col => 'daily_sales',
  timestamp_col => 'date',
  horizon => 30
);


-- =============================================================================
-- Example 3: Include historical data
-- =============================================================================
SELECT *
FROM AI.FORECAST(
  (SELECT * FROM `PROJECT_ID.DATASET.ai_forecast_sales` WHERE date >= '2024-11-01'),
  data_col => 'daily_sales',
  timestamp_col => 'date',
  horizon => 14,
  output_historical_time_series => TRUE
)
ORDER BY time_series_timestamp;


-- =============================================================================
-- Example 4: Confidence level
-- =============================================================================
SELECT *
FROM AI.FORECAST(
  TABLE `PROJECT_ID.DATASET.ai_forecast_sales`,
  data_col => 'daily_sales',
  timestamp_col => 'date',
  horizon => 14,
  confidence_level => 0.99
);
