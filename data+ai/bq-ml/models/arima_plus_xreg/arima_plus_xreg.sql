-- ARIMA_PLUS_XREG — Progressive SQL Examples (BigQuery ML)
-- =============================================================
-- Multivariate time series forecasting with CREATE MODEL (model_type =
-- 'ARIMA_PLUS_XREG') = ARIMA_PLUS + linear external regressors. Every
-- selected column that is NOT the timestamp/data/id column becomes a
-- covariate implicitly.
--
-- Data: bigquery-public-data.new_york_citibike.citibike_trips, aggregated to
--       one row per (station, day) = daily trip count, for the same 5
--       stations as models/arima_plus/, plus 3 covariates: avg_tripduration,
--       pct_subscriber, ratio_gender. TEST = last 28 days (after
--       2018-05-03); horizon = 28 -- same window as models/arima_plus/ for
--       direct forecast-accuracy comparison.
--
-- Full reference: ../../RESOURCES.md
-- Official docs:
--   CREATE MODEL (multivariate time series): https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-multivariate-time-series
--   ML.FORECAST: https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-forecast


-- =============================================================================
-- Setup: daily trip counts + covariates per station, TRAIN/TEST split
-- =============================================================================
-- GOTCHA (verified): 4 rows (E 17 St & Broadway) have a NULL ratio_gender --
-- days where every trip had an unknown gender, so the ratio is 0/0. CREATE
-- MODEL does not error on this; it emits a warning and trains successfully.
CREATE OR REPLACE TABLE `PROJECT_ID.DATASET.arima_xreg_trips` AS
WITH daily AS (
  SELECT
    start_station_name,
    DATE(starttime) AS date,
    COUNT(*) AS num_trips,
    AVG(tripduration) AS avg_tripduration,
    SAFE_DIVIDE(COUNTIF(usertype = 'Subscriber'), COUNT(*)) AS pct_subscriber,
    SAFE_DIVIDE(COUNTIF(gender = 'female'), COUNTIF(gender IN ('male','female'))) AS ratio_gender
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
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.arima_xreg_pershing`
OPTIONS(
  model_type = 'ARIMA_PLUS_XREG',
  time_series_timestamp_col = 'date',
  time_series_data_col = 'num_trips',
  holiday_region = ['GLOBAL', 'US'],
  horizon = 28
) AS
SELECT date, num_trips, avg_tripduration, pct_subscriber, ratio_gender
FROM `PROJECT_ID.DATASET.arima_xreg_trips`
WHERE start_station_name = 'Pershing Square North' AND splits = 'TRAIN';


-- =============================================================================
-- Example 2: CREATE MODEL — multi-series (all 5 stations in one model)
-- =============================================================================
-- The old repo notebook predates GA multi-series support for XREG and works
-- around it with an EXECUTE IMMEDIATE loop / async jobs -- time_series_id_col
-- replaces that workaround directly.
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.arima_xreg_multi`
OPTIONS(
  model_type = 'ARIMA_PLUS_XREG',
  time_series_timestamp_col = 'date',
  time_series_data_col = 'num_trips',
  time_series_id_col = 'start_station_name',
  holiday_region = ['GLOBAL', 'US'],
  horizon = 28
) AS
SELECT start_station_name, date, num_trips, avg_tripduration, pct_subscriber, ratio_gender
FROM `PROJECT_ID.DATASET.arima_xreg_trips`
WHERE splits = 'TRAIN';


-- =============================================================================
-- Example 3: ML.ARIMA_EVALUATE
-- =============================================================================
SELECT * FROM ML.ARIMA_EVALUATE(MODEL `PROJECT_ID.DATASET.arima_xreg_multi`);


-- =============================================================================
-- Example 4: ML.FEATURE_INFO and ML.TRAINING_INFO
-- =============================================================================
SELECT * FROM ML.FEATURE_INFO(MODEL `PROJECT_ID.DATASET.arima_xreg_multi`);
SELECT * FROM ML.TRAINING_INFO(MODEL `PROJECT_ID.DATASET.arima_xreg_multi`);


-- =============================================================================
-- Example 5: ML.EVALUATE — forecast accuracy on the held-out TEST period
-- =============================================================================
-- GOTCHA (verified): unlike ARIMA_PLUS, this type's ML.EVALUATE does NOT
-- include mean_absolute_scaled_error -- confirmed by comparing the actual
-- output columns side by side.
SELECT *
FROM ML.EVALUATE(MODEL `PROJECT_ID.DATASET.arima_xreg_multi`,
  (SELECT start_station_name, date, num_trips, avg_tripduration, pct_subscriber, ratio_gender
   FROM `PROJECT_ID.DATASET.arima_xreg_trips` WHERE splits = 'TEST'),
  STRUCT(TRUE AS perform_aggregation));


-- =============================================================================
-- Example 6: ML.FORECAST — covariates are required
-- =============================================================================
-- GOTCHA (verified): the 2-argument form (model, STRUCT) fails immediately:
-- "Model type ARIMA_PLUS_XREG requires three parameters in ML.FORECAST."
-- Covariates must be supplied for the entire forecast horizon -- here, the
-- TEST split's actual (already-known) values, same honest framing as the
-- old repo notebook (never genuinely-unknown future covariates either).
SELECT start_station_name, forecast_timestamp, forecast_value,
       prediction_interval_lower_bound, prediction_interval_upper_bound
FROM ML.FORECAST(MODEL `PROJECT_ID.DATASET.arima_xreg_multi`,
  STRUCT(28 AS horizon, 0.9 AS confidence_level),
  (SELECT start_station_name, date, avg_tripduration, pct_subscriber, ratio_gender
   FROM `PROJECT_ID.DATASET.arima_xreg_trips` WHERE splits = 'TEST'))
ORDER BY start_station_name, forecast_timestamp;


-- =============================================================================
-- Example 7: ML.EXPLAIN_FORECAST — decomposition + per-regressor attribution
-- =============================================================================
SELECT time_series_timestamp, time_series_type, trend,
       attribution_avg_tripduration, attribution_pct_subscriber, attribution_ratio_gender
FROM ML.EXPLAIN_FORECAST(MODEL `PROJECT_ID.DATASET.arima_xreg_multi`,
  STRUCT(28 AS horizon),
  (SELECT start_station_name, date, avg_tripduration, pct_subscriber, ratio_gender
   FROM `PROJECT_ID.DATASET.arima_xreg_trips` WHERE splits = 'TEST'))
WHERE start_station_name = 'Pershing Square North'
ORDER BY time_series_timestamp;


-- =============================================================================
-- Example 8: ML.ARIMA_COEFFICIENTS — AR/MA + regression weights
-- =============================================================================
SELECT * FROM ML.ARIMA_COEFFICIENTS(MODEL `PROJECT_ID.DATASET.arima_xreg_multi`);


-- =============================================================================
-- Example 9: ML.HOLIDAY_INFO
-- =============================================================================
SELECT * FROM ML.HOLIDAY_INFO(MODEL `PROJECT_ID.DATASET.arima_xreg_multi`)
WHERE region = 'US' AND primary_date BETWEEN '2016-01-01' AND '2018-12-31'
ORDER BY primary_date;


-- =============================================================================
-- Example 10: ML.DETECT_ANOMALIES
-- =============================================================================
SELECT start_station_name, date, num_trips, is_anomaly, anomaly_probability
FROM ML.DETECT_ANOMALIES(MODEL `PROJECT_ID.DATASET.arima_xreg_multi`, STRUCT(0.95 AS anomaly_prob_threshold))
WHERE is_anomaly
ORDER BY anomaly_probability DESC;


-- =============================================================================
-- Example 11: Additional options -- same as ARIMA_PLUS, with one real
-- difference (forecast bounds are not supported at all)
-- =============================================================================
-- Custom holidays use the identical two-block syntax as ARIMA_PLUS (see
-- models/arima_plus/ for the full explanation).
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.arima_xreg_custom_holiday`
OPTIONS(
  model_type = 'ARIMA_PLUS_XREG',
  holiday_region = 'US',
  time_series_timestamp_col = 'date',
  time_series_data_col = 'num_trips',
  horizon = 7
) AS (
  training_data AS (
    SELECT date, num_trips, avg_tripduration, pct_subscriber, ratio_gender
    FROM `PROJECT_ID.DATASET.arima_xreg_trips`
    WHERE start_station_name = 'Pershing Square North' AND splits = 'TRAIN'
  ),
  custom_holiday AS (
    SELECT 'US' AS region, 'NYCMarathon' AS holiday_name, primary_date, 1 AS preholiday_days, 1 AS postholiday_days
    FROM UNNEST([DATE('2014-11-02'), DATE('2015-11-01'), DATE('2016-11-06'), DATE('2017-11-05')]) AS primary_date
  )
);

-- non_seasonal_order (manual ARIMA order) also works identically -- single
-- series only, same as ARIMA_PLUS.
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.arima_xreg_manual_order`
OPTIONS(
  model_type = 'ARIMA_PLUS_XREG',
  time_series_timestamp_col = 'date',
  time_series_data_col = 'num_trips',
  auto_arima = FALSE,
  non_seasonal_order = STRUCT(2 AS p, 1 AS d, 1 AS q),
  horizon = 7
) AS
SELECT date, num_trips, avg_tripduration, pct_subscriber, ratio_gender
FROM `PROJECT_ID.DATASET.arima_xreg_trips`
WHERE start_station_name = 'Pershing Square North' AND splits = 'TRAIN';

-- GOTCHA (verified): unlike ARIMA_PLUS -- where forecast_limit_lower_bound
-- is ACCEPTED at CREATE MODEL time but breaks ML.EXPLAIN_FORECAST --
-- ARIMA_PLUS_XREG rejects the option outright: "Option(s)
-- FORECAST_LIMIT_LOWER_BOUND are not supported for ARIMA_PLUS_XREG model
-- training." A real, different limitation between the two model types.
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.arima_xreg_bound_error`
OPTIONS(
  model_type = 'ARIMA_PLUS_XREG',
  time_series_timestamp_col = 'date',
  time_series_data_col = 'num_trips',
  forecast_limit_lower_bound = 0,
  horizon = 7
) AS
SELECT date, num_trips, avg_tripduration, pct_subscriber, ratio_gender
FROM `PROJECT_ID.DATASET.arima_xreg_trips`
WHERE start_station_name = 'Pershing Square North' AND splits = 'TRAIN';
