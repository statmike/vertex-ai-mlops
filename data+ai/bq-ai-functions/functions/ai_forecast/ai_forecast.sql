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
--
-- Univariate forecasting is GA. Multivariate forecasting (target_cols,
-- past/future covariates) and the TimesFM 3.0 model are Preview -- Examples 6-7.
--
-- Need custom holiday effects, hierarchical reconciliation, explainable
-- components (ML.EXPLAIN_FORECAST), or forecast bounds? See
-- ../../../bq-ml/models/arima_plus/ (the trainable ARIMA_PLUS model).
-- External regressors are no longer the dividing line: ARIMA_PLUS_XREG
-- and TimesFM 3.0's covariates both take them. AI.FORECAST is the faster,
-- zero-setup alternative; ARIMA_PLUS is the answer once you need that level
-- of control and explanation.
--
-- Want to describe the history rather than predict the future? See
-- ../../../bq-ml/functions/time_series/ -- ML.TREND, ML.SEASONALITY and
-- ML.DETECT_CHANGE_POINTS are model-free TVFs for trend, seasonal components
-- and sustained structural change points.


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


-- =============================================================================
-- Example 5: Pin the model version
-- =============================================================================
-- The default is TimesFM 2.5; 'TimesFM 3.0' (Preview) is the other accepted
-- value. Pin it whenever the numbers have to be reproducible -- an unpinned
-- call follows the default when it moves.
SELECT *
FROM AI.FORECAST(
  TABLE `PROJECT_ID.DATASET.ai_forecast_sales`,
  data_col => 'daily_sales',
  timestamp_col => 'date',
  horizon => 14,
  model => 'TimesFM 2.5'
);


-- =============================================================================
-- Example 6: TimesFM 3.0 (Preview) -- multivariate forecasting with target_cols
-- =============================================================================
-- Two related daily series plus two covariates. History: 2024. Future: 14 days
-- with the targets NULL and the future covariates populated (used in Example 7).
CREATE OR REPLACE TABLE `PROJECT_ID.DATASET.ai_forecast_sales_mv` AS
WITH days AS (
  SELECT date,
    EXTRACT(DAYOFWEEK FROM date) AS dow,
    DATE_DIFF(date, DATE '2024-01-01', DAY) AS t
  FROM UNNEST(GENERATE_DATE_ARRAY('2024-01-01', '2025-01-14')) AS date
)
SELECT
  date,
  IF(date <= '2024-12-31', GREATEST(0,
    1000 + t * 2
    + CASE dow WHEN 1 THEN -200 WHEN 7 THEN 300 WHEN 6 THEN 200 ELSE 0 END
    + IF(MOD(t + 20, 30) < 3, 400, 0)            -- promotion lift
    + CAST(200 * (RAND() - 0.5) AS INT64)), NULL) AS daily_sales,
  IF(date <= '2024-12-31', GREATEST(0,
    5000 + t * 5
    + CASE dow WHEN 1 THEN -800 WHEN 7 THEN 1200 WHEN 6 THEN 800 ELSE 0 END
    + CAST(600 * (RAND() - 0.5) AS INT64)), NULL) AS web_visits,
  IF(MOD(t + 20, 30) < 3, 1, 0) AS promo_flag,   -- known in advance
  IF(dow IN (1, 7), 1, 0) AS is_weekend          -- known in advance
FROM days;

-- target_cols replaces data_col and requires model => 'TimesFM 3.0'.
-- Output: the timestamp column keeps its input name; each target is a
-- STRUCT<value, prediction_interval_lower_bound, prediction_interval_upper_bound>.
SELECT
  date,
  daily_sales.value AS sales_forecast,
  daily_sales.prediction_interval_lower_bound AS sales_lower,
  daily_sales.prediction_interval_upper_bound AS sales_upper,
  web_visits.value AS visits_forecast,
  time_series_type,
  ai_forecast_status
FROM AI.FORECAST(
  (SELECT date, daily_sales, web_visits
   FROM `PROJECT_ID.DATASET.ai_forecast_sales_mv`
   WHERE date <= '2024-12-31'),
  target_cols => ['daily_sales', 'web_visits'],
  timestamp_col => 'date',
  model => 'TimesFM 3.0',
  horizon => 7
)
ORDER BY date;


-- =============================================================================
-- Example 7: Past and future covariates (TimesFM 3.0, Preview)
-- =============================================================================
-- past_covariate_cols: known only historically (NULL on the future rows).
-- future_covariate_cols: known for past and future -- supply them on every
-- future row you want forecast. horizon is capped by the future rows present.
SELECT
  date,
  daily_sales.value AS sales_forecast,
  daily_sales.prediction_interval_lower_bound AS lower,
  daily_sales.prediction_interval_upper_bound AS upper
FROM AI.FORECAST(
  TABLE `PROJECT_ID.DATASET.ai_forecast_sales_mv`,
  target_cols => ['daily_sales'],
  timestamp_col => 'date',
  model => 'TimesFM 3.0',
  horizon => 14,
  past_covariate_cols => ['web_visits'],
  future_covariate_cols => ['promo_flag', 'is_weekend']
)
ORDER BY date;
