-- ARIMA_PLUS — Progressive SQL Examples (BigQuery ML)
-- =============================================================
-- Univariate time series forecasting with CREATE MODEL (model_type =
-- 'ARIMA_PLUS'). Automatically handles frequency detection, missing-value
-- interpolation, spike/dip cleaning, step-change adjustment, seasonal +
-- trend decomposition, and holiday effects on top of auto.ARIMA.
--
-- Data: bigquery-public-data.new_york_citibike.citibike_trips, aggregated to
--       one row per (station, day) = daily trip count, for 5 stations:
--       Pershing Square North, E 17 St & Broadway, W 21 St & 6 Ave,
--       Lafayette St & E 8 St, West St & Chambers St.
--       TEST = last 28 days of data (after 2018-05-03); horizon = 28.
--
-- Full reference: ../../RESOURCES.md
-- Official docs:
--   CREATE MODEL (time series): https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-time-series
--   ML.FORECAST: https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-forecast
--   ML.EXPLAIN_FORECAST: https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-explain-forecast


-- =============================================================================
-- Setup: daily trip counts per station, TRAIN/TEST split
-- =============================================================================
CREATE OR REPLACE TABLE `PROJECT_ID.DATASET.arima_plus_trips` AS
WITH daily AS (
  SELECT
    start_station_name,
    DATE(starttime) AS date,
    COUNT(*) AS num_trips
  FROM `bigquery-public-data.new_york_citibike.citibike_trips`
  WHERE start_station_name IN (
    'Pershing Square North', 'E 17 St & Broadway', 'W 21 St & 6 Ave',
    'Lafayette St & E 8 St', 'West St & Chambers St'
  )
  GROUP BY start_station_name, date
)
SELECT *, IF(date > DATE('2018-05-03'), 'TEST', 'TRAIN') AS splits
FROM daily;


-- =============================================================================
-- Example 1: CREATE MODEL — single series (simple starting point)
-- =============================================================================
-- No time_series_id_col -- just one station. ARIMA+ ignores a validation
-- split, so TRAIN alone (TEST held out for evaluation below) is used.
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.arima_plus_pershing`
OPTIONS(
  model_type = 'ARIMA_PLUS',
  time_series_timestamp_col = 'date',
  time_series_data_col = 'num_trips',
  holiday_region = ['GLOBAL', 'US'],
  horizon = 28
) AS
SELECT date, num_trips
FROM `PROJECT_ID.DATASET.arima_plus_trips`
WHERE start_station_name = 'Pershing Square North' AND splits = 'TRAIN';

SELECT * FROM ML.EVALUATE(MODEL `PROJECT_ID.DATASET.arima_plus_pershing`,
  (SELECT date, num_trips FROM `PROJECT_ID.DATASET.arima_plus_trips`
   WHERE start_station_name = 'Pershing Square North' AND splits = 'TEST'));

SELECT * FROM ML.FORECAST(MODEL `PROJECT_ID.DATASET.arima_plus_pershing`, STRUCT(28 AS horizon));


-- =============================================================================
-- Example 2: CREATE MODEL — multi-series (all 5 stations in one model)
-- =============================================================================
-- time_series_id_col fits+forecasts all 5 series in a single CREATE MODEL.
-- This is the model used for the rest of this file. Pershing Square North
-- has a shorter history (starts 2014-09-01, not 2013-07-01) -- multi-series
-- ARIMA+ handles series of different lengths within one model.
-- NOTE: forecast_limit_lower_bound is deliberately NOT set here -- it is
-- incompatible with ML.EXPLAIN_FORECAST (see Example 10), which is used
-- throughout the rest of this file (Example 7, Example 12).
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.arima_plus_multi`
OPTIONS(
  model_type = 'ARIMA_PLUS',
  time_series_timestamp_col = 'date',
  time_series_data_col = 'num_trips',
  time_series_id_col = 'start_station_name',
  holiday_region = ['GLOBAL', 'US'],
  horizon = 28
) AS
SELECT start_station_name, date, num_trips
FROM `PROJECT_ID.DATASET.arima_plus_trips`
WHERE splits = 'TRAIN';


-- =============================================================================
-- Example 3: ML.ARIMA_EVALUATE — per-series model selection diagnostics
-- =============================================================================
SELECT *
FROM ML.ARIMA_EVALUATE(MODEL `PROJECT_ID.DATASET.arima_plus_multi`);


-- =============================================================================
-- Example 4: ML.FEATURE_INFO and ML.TRAINING_INFO
-- =============================================================================
SELECT * FROM ML.FEATURE_INFO(MODEL `PROJECT_ID.DATASET.arima_plus_multi`);
SELECT * FROM ML.TRAINING_INFO(MODEL `PROJECT_ID.DATASET.arima_plus_multi`);


-- =============================================================================
-- Example 5: ML.EVALUATE — forecast accuracy on the held-out TEST period
-- =============================================================================
-- Without eval data, ML.EVALUATE falls back to ARIMA-fit stats (same shape
-- as ML.ARIMA_EVALUATE). With explicit data + perform_aggregation=TRUE,
-- it returns forecast-accuracy metrics per series -- including
-- mean_absolute_scaled_error, not documented as part of this type's default
-- metric set in the official reference.
SELECT *
FROM ML.EVALUATE(MODEL `PROJECT_ID.DATASET.arima_plus_multi`,
  (SELECT start_station_name, date, num_trips FROM `PROJECT_ID.DATASET.arima_plus_trips` WHERE splits = 'TEST'),
  STRUCT(TRUE AS perform_aggregation));


-- =============================================================================
-- Example 6: ML.FORECAST
-- =============================================================================
SELECT start_station_name, forecast_timestamp, forecast_value,
       prediction_interval_lower_bound, prediction_interval_upper_bound
FROM ML.FORECAST(MODEL `PROJECT_ID.DATASET.arima_plus_multi`, STRUCT(28 AS horizon, 0.9 AS confidence_level))
ORDER BY start_station_name, forecast_timestamp;


-- =============================================================================
-- Example 7: ML.EXPLAIN_FORECAST — decomposition
-- =============================================================================
SELECT time_series_timestamp, time_series_type, time_series_data, time_series_adjusted_data,
       trend, seasonal_period_weekly, seasonal_period_yearly, holiday_effect
FROM ML.EXPLAIN_FORECAST(MODEL `PROJECT_ID.DATASET.arima_plus_multi`, STRUCT(28 AS horizon))
WHERE start_station_name = 'Pershing Square North'
ORDER BY time_series_timestamp;


-- =============================================================================
-- Example 8: ML.ARIMA_COEFFICIENTS
-- =============================================================================
SELECT * FROM ML.ARIMA_COEFFICIENTS(MODEL `PROJECT_ID.DATASET.arima_plus_multi`);


-- =============================================================================
-- Example 9: ML.HOLIDAY_INFO
-- =============================================================================
SELECT * FROM ML.HOLIDAY_INFO(MODEL `PROJECT_ID.DATASET.arima_plus_multi`)
WHERE region = 'US' AND primary_date BETWEEN '2016-01-01' AND '2018-12-31'
ORDER BY primary_date;


-- =============================================================================
-- Example 10: Additional options -- custom holidays, manual ARIMA order,
-- and forecast bounds
-- =============================================================================
-- holiday_region only covers built-in regional holidays. To model an event
-- that matters for THIS series but isn't a public holiday, supply a custom
-- holiday table using the special two-block AS (training_data AS (...),
-- custom_holiday AS (...)) syntax -- no WITH keyword; training_data and
-- custom_holiday are the two required block names, not ordinary CTEs.
-- custom_holiday needs region, holiday_name (must be a valid column-name
-- string -- no spaces), primary_date, preholiday_days, postholiday_days.
-- The effect then shows up in ML.EXPLAIN_FORECAST as holiday_effect_<name>.
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.arima_plus_custom_holiday`
OPTIONS(
  model_type = 'ARIMA_PLUS',
  holiday_region = 'US',
  time_series_timestamp_col = 'date',
  time_series_data_col = 'num_trips',
  horizon = 7
) AS (
  training_data AS (
    SELECT date, num_trips
    FROM `PROJECT_ID.DATASET.arima_plus_trips`
    WHERE start_station_name = 'Pershing Square North' AND splits = 'TRAIN'
  ),
  custom_holiday AS (
    SELECT 'US' AS region, 'NYCMarathon' AS holiday_name, primary_date, 1 AS preholiday_days, 1 AS postholiday_days
    FROM UNNEST([DATE('2014-11-02'), DATE('2015-11-01'), DATE('2016-11-06'), DATE('2017-11-05')]) AS primary_date
  )
);

SELECT * FROM ML.HOLIDAY_INFO(MODEL `PROJECT_ID.DATASET.arima_plus_custom_holiday`)
WHERE holiday_name = 'NYCMarathon';

-- The custom holiday's effect appears in ML.EXPLAIN_FORECAST as
-- holiday_effect_<holiday_name> -- confirming the column exists, not that
-- the effect is large: with only 4 marathon dates in the training history,
-- the estimated effect for this station comes out at 0.0 (statistically
-- indistinguishable from no effect) -- a real, honest result, not a bug.
SELECT time_series_timestamp, holiday_effect_NYCMarathon
FROM ML.EXPLAIN_FORECAST(MODEL `PROJECT_ID.DATASET.arima_plus_custom_holiday`, STRUCT(7 AS horizon))
WHERE DATE(time_series_timestamp) BETWEEN '2016-11-04' AND '2016-11-08'
ORDER BY time_series_timestamp;

-- auto_arima is TRUE by default (used everywhere else in this file). Setting
-- auto_arima = FALSE with non_seasonal_order = STRUCT(p, d, q) disables the
-- search and pins an exact order -- single-series only.
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.arima_plus_manual_order`
OPTIONS(
  model_type = 'ARIMA_PLUS',
  time_series_timestamp_col = 'date',
  time_series_data_col = 'num_trips',
  auto_arima = FALSE,
  non_seasonal_order = STRUCT(2 AS p, 1 AS d, 1 AS q),
  horizon = 7
) AS
SELECT date, num_trips
FROM `PROJECT_ID.DATASET.arima_plus_trips`
WHERE start_station_name = 'Pershing Square North' AND splits = 'TRAIN';

SELECT non_seasonal_p, non_seasonal_d, non_seasonal_q
FROM ML.ARIMA_EVALUATE(MODEL `PROJECT_ID.DATASET.arima_plus_manual_order`);

-- GOTCHA (verified): forecast_limit_lower_bound/forecast_limit_upper_bound
-- are incompatible with ML.EXPLAIN_FORECAST. ML.FORECAST and every other
-- lifecycle function are unaffected -- only ML.EXPLAIN_FORECAST is blocked.
-- This is why arima_plus_multi (Example 2) does NOT set a bound.
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.arima_plus_bounded`
OPTIONS(
  model_type = 'ARIMA_PLUS',
  time_series_timestamp_col = 'date',
  time_series_data_col = 'num_trips',
  forecast_limit_lower_bound = 0,
  horizon = 7
) AS
SELECT date, num_trips
FROM `PROJECT_ID.DATASET.arima_plus_trips`
WHERE start_station_name = 'Pershing Square North' AND splits = 'TRAIN';

-- Works fine:
SELECT forecast_timestamp, forecast_value
FROM ML.FORECAST(MODEL `PROJECT_ID.DATASET.arima_plus_bounded`)
ORDER BY forecast_timestamp;

-- Fails: "This model was trained with either 'forecast_limit_lower_bound' or
-- 'forecast_limit_upper_bound' being specified. In this case, EXPLAIN_FORECAST
-- is not supported."
SELECT * FROM ML.EXPLAIN_FORECAST(MODEL `PROJECT_ID.DATASET.arima_plus_bounded`);


-- =============================================================================
-- Example 11: ML.DETECT_ANOMALIES
-- =============================================================================
SELECT start_station_name, date, num_trips, is_anomaly, anomaly_probability
FROM ML.DETECT_ANOMALIES(MODEL `PROJECT_ID.DATASET.arima_plus_multi`, STRUCT(0.95 AS anomaly_prob_threshold))
WHERE is_anomaly
ORDER BY anomaly_probability DESC;


-- =============================================================================
-- Example 12: GOTCHA — granularity and missing-data handling
-- =============================================================================
-- Requesting a COARSER granularity than the data errors immediately:
-- "Invalid time series: All input time intervals must be no less than the
-- interval unit specified by data_frequency (WEEKLY)"
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.arima_plus_weekly_error`
OPTIONS(
  model_type = 'ARIMA_PLUS',
  time_series_timestamp_col = 'date',
  time_series_data_col = 'num_trips',
  data_frequency = 'WEEKLY',
  horizon = 4
) AS
SELECT date, num_trips
FROM `PROJECT_ID.DATASET.arima_plus_trips`
WHERE start_station_name = 'Pershing Square North' AND splits = 'TRAIN';

-- Missing/absent days are linearly interpolated. Pershing Square North has
-- no row at all for 2015-10-20 in the source data; ML.EXPLAIN_FORECAST's
-- time_series_data for that date is 252.0 -- exactly the average of the
-- neighboring days 2015-10-19 (141) and 2015-10-21 (363): (141+363)/2=252.
SELECT time_series_timestamp, time_series_data
FROM ML.EXPLAIN_FORECAST(MODEL `PROJECT_ID.DATASET.arima_plus_multi`, STRUCT(28 AS horizon))
WHERE start_station_name = 'Pershing Square North'
  AND DATE(time_series_timestamp) BETWEEN '2015-10-18' AND '2015-10-23'
ORDER BY time_series_timestamp;
