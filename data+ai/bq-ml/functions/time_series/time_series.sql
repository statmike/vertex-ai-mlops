-- Time Series Decomposition — Progressive SQL Examples (BigQuery ML model-free functions)
-- =============================================================
-- Three table-valued functions that decompose a time series without a model:
-- ML.TREND (trend component), ML.SEASONALITY (per-period seasonal components),
-- ML.DETECT_CHANGE_POINTS (sustained structural shifts). No CREATE MODEL, no
-- model object, no connection -- a TVF straight over a table or query.
--
-- All three take a relation as the first positional argument and the column
-- names as STRING named arguments. Preview as of 2026-08-20.
--
-- GOTCHA these are not the same thing as ML.DETECT_ANOMALIES. See Example 7 --
-- measured on this exact series, ML.DETECT_CHANGE_POINTS' change windows and
-- ML.DETECT_ANOMALIES' row-level anomalies had *zero* overlap. Three different
-- questions, three different functions:
--   row-level outlier      -> ML.DETECT_ANOMALIES     (models/arima_plus/, kmeans, pca, autoencoder)
--   sustained shift        -> ML.DETECT_CHANGE_POINTS (this file)
--   dataset-level drift    -> ML.VALIDATE_DATA_DRIFT  (functions/data_quality/)
--
-- GOTCHA all three functions gap-fill a series to a regular frequency before
-- doing anything else, and on gapped data that is not a detail. Example 5 shows
-- ML.DETECT_CHANGE_POINTS reporting both edges of a 182-day ingestion outage as
-- structural change points. Check a series for outages before acting on one.
--
-- Data: bigquery-public-data.new_york_citibike.citibike_trips, aggregated to
--       daily trip counts for five stations -- the identical series used by
--       models/arima_plus/, so the head-to-head in Example 6 is apples-to-apples.
--
-- Full reference: ../../RESOURCES.md
-- Official docs:
--   ML.TREND:                 https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-trend
--   ML.SEASONALITY:           https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-seasonality
--   ML.DETECT_CHANGE_POINTS:  https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-detect-change-points


-- =============================================================================
-- Setup: the shared daily-trips table (identical recipe to models/arima_plus/)
-- =============================================================================
CREATE OR REPLACE TABLE `PROJECT_ID.DATASET.time_series_trips` AS
WITH daily AS (
  SELECT start_station_name, DATE(starttime) AS date, COUNT(*) AS num_trips
  FROM `bigquery-public-data.new_york_citibike.citibike_trips`
  WHERE start_station_name IN (
    'Pershing Square North', 'E 17 St & Broadway', 'W 21 St & 6 Ave',
    'Lafayette St & E 8 St', 'West St & Chambers St')
  GROUP BY start_station_name, date
)
SELECT *, IF(date > DATE('2018-05-03'), 'TEST', 'TRAIN') AS splits FROM daily;

-- 7,544 rows. NOTE these series have gaps -- days with no trips produce no row.
-- Per station, TRAIN split, raw rows vs. the calendar span they cover:
--   Pershing Square North   1,153 rows over 1,341 days (2014-09-01 .. 2018-05-03)
--   E 17 St & Broadway      1,580 rows over 1,768 days (2013-07-01 .. 2018-05-03)
--   W 21 St & 6 Ave         1,581 rows over 1,768 days
--   West St & Chambers St   1,582 rows over 1,768 days
--   Lafayette St & E 8 St   1,508 rows over 1,768 days
-- The gaps matter: all three functions gap-fill internally. See Examples 5 and 9.
-- They are also not evenly scattered. 'Pershing Square North' has a single
-- CONTIGUOUS 182-day outage, 2016-10-01 .. 2017-03-31, which accounts for 182 of
-- its 188 missing days. Example 5 turns on that fact.


-- =============================================================================
-- Example 1: ML.TREND -- the trend component, no model required
-- =============================================================================
-- Signature, as enumerated by the server when given a bad argument:
--   ML.TREND(TABLE, timestamp_col => STRING, data_col => STRING,
--            [id_cols => ARRAY<STRING>], [horizon => INT64],
--            [smoothing_window_size => INT64], [adjust_step_changes => BOOL])
SELECT *
FROM ML.TREND(
  (SELECT date, num_trips FROM `PROJECT_ID.DATASET.time_series_trips`
   WHERE start_station_name = 'Pershing Square North' AND splits = 'TRAIN'),
  timestamp_col => 'date',
  data_col => 'num_trips'
)
ORDER BY date
LIMIT 10;

-- Output schema, in order: date, time_series_type, num_trips, trend, status.
-- The timestamp and data columns come back under their ORIGINAL names -- the
-- output is not renamed to a generic `time_series_timestamp`/`_data` the way
-- ML.FORECAST's is. `trend` is the added column.
--
-- GOTCHA `num_trips` comes back FLOAT64 even though the input is an INT64
-- COUNT(*), because the function returns the gap-filled/preprocessed series
-- rather than echoing your raw values.
--
-- GOTCHA `status` is the empty string '' on success, never NULL. Measured on all
-- three functions: every returned row had status = '' with LENGTH 0 and
-- IS NULL = false. Test it with `status = ''` or `LENGTH(status) = 0`, not with
-- `status IS NULL` -- the NULL test silently matches nothing.


-- =============================================================================
-- Example 2: named arguments -- ordering, case, and what is optional
-- =============================================================================
-- Only the relation, timestamp_col and data_col are required. Argument NAMES are
-- case-insensitive: the signature prints SEASONALITIES in caps, but
-- `seasonalities => [...]` and `Timestamp_Col => 'date'` are both accepted.
SELECT date, num_trips, ROUND(trend, 2) AS trend
FROM ML.TREND(
  (SELECT date, num_trips FROM `PROJECT_ID.DATASET.time_series_trips`
   WHERE start_station_name = 'Pershing Square North' AND splits = 'TRAIN'),
  data_col => 'num_trips',          -- order among named arguments does not matter
  timestamp_col => 'date',
  smoothing_window_size => 30
)
ORDER BY date
LIMIT 5;

-- Measured effect of smoothing_window_size => 30 vs the default, same 1,341 rows:
--   mean absolute difference in `trend`  17.237
--   stddev of `trend`  99.99 (default) -> 96.58 (window 30)
-- A real but modest smoothing effect on this series.


-- =============================================================================
-- Example 3: adjust_step_changes -- the default differs from ARIMA_PLUS's
-- =============================================================================
-- GOTCHA ML.TREND defaults adjust_step_changes to FALSE. The ARIMA_PLUS model
-- defaults the equivalent option to TRUE. Verified by differencing all three
-- variants over the same 1,341 rows:
--   default vs adjust_step_changes => FALSE   summed |difference| = 0.0
--   default vs adjust_step_changes => TRUE    summed |difference| = 91,344.17
-- and by reading the resolved option off a trained model
-- (`bq show --format=prettyjson --model ...`), which reports
-- "adjustStepChanges": true. So a naive ML.TREND call does NOT reproduce
-- models/arima_plus/'s trend -- you have to opt in. See Example 6.
SELECT
  t_def.date,
  ROUND(t_def.trend, 2)  AS trend_default,
  ROUND(t_adj.trend, 2)  AS trend_step_adjusted,
  ROUND(ABS(t_def.trend - t_adj.trend), 2) AS abs_diff
FROM ML.TREND(
       (SELECT date, num_trips FROM `PROJECT_ID.DATASET.time_series_trips`
        WHERE start_station_name = 'Pershing Square North' AND splits = 'TRAIN'),
       timestamp_col => 'date', data_col => 'num_trips') AS t_def
JOIN ML.TREND(
       (SELECT date, num_trips FROM `PROJECT_ID.DATASET.time_series_trips`
        WHERE start_station_name = 'Pershing Square North' AND splits = 'TRAIN'),
       timestamp_col => 'date', data_col => 'num_trips',
       adjust_step_changes => TRUE) AS t_adj
  USING (date)
ORDER BY abs_diff DESC
LIMIT 5;

-- Measured across the full series: mean |difference| 68.116, max 132.533.


-- =============================================================================
-- Example 4: ML.SEASONALITY -- one column per period, fixed schema
-- =============================================================================
-- Signature:
--   ML.SEASONALITY(TABLE, timestamp_col => STRING, data_col => STRING,
--                  [id_cols => ARRAY<STRING>], [SEASONALITIES => ARRAY<STRING>],
--                  [horizon => INT64])
SELECT *
FROM ML.SEASONALITY(
  (SELECT date, num_trips FROM `PROJECT_ID.DATASET.time_series_trips`
   WHERE start_station_name = 'Pershing Square North' AND splits = 'TRAIN'),
  timestamp_col => 'date',
  data_col => 'num_trips'
)
ORDER BY date
LIMIT 10;

-- Output schema, in order: date, time_series_type, num_trips, then ONE COLUMN
-- PER PERIOD in DESCENDING period length -- yearly, quarterly, monthly, weekly,
-- daily -- then status.
--
-- GOTCHA the schema is FIXED. A period the function did not fit is not omitted
-- from the schema; it comes back NULL for every row. On this daily series only
-- two of the five populate -- measured over all 1,341 rows:
--   yearly     0 NULLs   <- fitted
--   weekly     0 NULLs   <- fitted
--   quarterly  1,341 NULLs
--   monthly    1,341 NULLs
--   daily      1,341 NULLs
-- So `SELECT *` gives you three all-NULL columns and no indication of why.
-- Detect what was actually fitted with a COUNTIF(... IS NULL) pass, not by
-- reading the schema.

-- Restrict which periods are fitted with SEASONALITIES:
SELECT date, num_trips, ROUND(weekly, 3) AS weekly, ROUND(yearly, 3) AS yearly
FROM ML.SEASONALITY(
  (SELECT date, num_trips FROM `PROJECT_ID.DATASET.time_series_trips`
   WHERE start_station_name = 'Pershing Square North' AND splits = 'TRAIN'),
  timestamp_col => 'date',
  data_col => 'num_trips',
  SEASONALITIES => ['WEEKLY', 'YEARLY']
)
ORDER BY date
LIMIT 5;

-- Accepted SEASONALITIES values, established by sweeping candidates against the
-- server: DAILY, WEEKLY, MONTHLY, QUARTERLY, YEARLY. The VALUES are
-- case-insensitive too -- 'weekly' and 'Weekly' are both accepted.
--
-- GOTCHA the rejection message is not uniformly helpful. Three rejected strings
-- come back with the valid set spelled out:
--   HOURLY / NO_SEASONALITY / AUTO
--     -> "Invalid seasonality value 'HOURLY' in SEASONALITIES. Supported values
--         are YEARLY, QUARTERLY, MONTHLY, WEEKLY, DAILY."
-- but any other string -- MINUTELY, PER_MINUTE, PER_HOUR, AUTO_FREQUENCY,
-- ANNUAL, '' or an outright typo -- gets the bare form with no enumeration:
--     -> "Invalid seasonality value 'BOGUS' in SEASONALITIES."
-- The three that do enumerate are plausible-but-wrong guesses drawn from
-- neighbouring BQML vocabulary; several other tokens from that same vocabulary
-- (PER_MINUTE, AUTO_FREQUENCY, PER_HOUR) do NOT enumerate, so this is a recorded
-- observation about the message, not an inferred rule about which strings the
-- parser recognizes. Practical consequence: a typo tells you nothing, so keep
-- the valid list above at hand rather than relying on the error to supply it.


-- =============================================================================
-- Example 5: ML.DETECT_CHANGE_POINTS -- windows, not per-row flags
-- =============================================================================
-- Signature (the shortest of the three -- no horizon, no tuning options):
--   ML.DETECT_CHANGE_POINTS(TABLE, timestamp_col => STRING, data_col => STRING,
--                           [id_cols => ARRAY<STRING>])
SELECT
  begin_timestamp, end_timestamp, status,
  metrics.count, ROUND(metrics.avg, 2) AS avg,
  metrics.min, metrics.max, ROUND(metrics.stddev, 2) AS stddev
FROM ML.DETECT_CHANGE_POINTS(
  (SELECT date, num_trips FROM `PROJECT_ID.DATASET.time_series_trips`
   WHERE start_station_name = 'Pershing Square North' AND splits = 'TRAIN'),
  timestamp_col => 'date',
  data_col => 'num_trips'
);

-- GOTCHA this does NOT return one row per input row. It returns one row per
-- detected change WINDOW. On this series it returned exactly 2 rows:
--   2016-09-28 -> 2016-10-04   count 7, avg 346.98, min 192.34, max 783, sd 264.36
--   2017-04-01 -> 2017-04-03   count 3, avg 297.33, min 118.00, max 620, sd 280.02
-- There is no `is_change_point` boolean to filter on and no full-partition
-- output to join back -- to attribute a row to a window you range-join on
-- `date BETWEEN begin_timestamp AND end_timestamp` (Example 7 does exactly that).
--
-- GOTCHA the `metrics` struct is computed over the GAP-FILLED series, not over
-- your raw rows, so it will not tie out against a plain GROUP BY over the same
-- date range. In the first window the base table has only 3 rows
-- (2016-09-28/29/30 -- Oct 1-4 are simply absent) but metrics.count is 7, one
-- per calendar day. metrics.min is 192.33879781420765, a fraction, even though
-- num_trips is an integer COUNT(*) -- that value is interpolated, not observed:
--   raw aggregate for 2016-09-28..2016-10-04:  n 3, avg 552.33, min 194, max 783, sd 314.57
--   metrics reported by the function:          n 7, avg 346.98, min 192.34, max 783, sd 264.36
-- Same window, different numbers, because they describe different series.

-- GOTCHA -- and this is the one that matters -- on a gapped series the
-- gap-filling MANUFACTURES the structural break the function then reports.
-- Line the two detected windows up against the outage noted in Setup:
--   detected 2016-09-28 -> 2016-10-04   |  outage BEGINS 2016-10-01
--   detected 2017-04-01 -> 2017-04-03   |  outage ENDS   2017-03-31
-- Both change points sit on the two EDGES of the single 182-day outage. The
-- function is not wrong: after interpolation the series really does step down
-- into a flat stretch and step back up out of it. But the shift it found is an
-- artifact of missing data, not a change in ridership. Check a series for
-- outages before acting on a change point, or the alert fires on your pipeline
-- rather than on your business. Confirm with:
SELECT date, num_trips
FROM `PROJECT_ID.DATASET.time_series_trips`
WHERE start_station_name = 'Pershing Square North'
  AND date BETWEEN DATE('2016-09-26') AND DATE('2017-04-05')
ORDER BY date;
-- 10 rows present across a 192-day range: 2016-09-26..30 and 2017-04-01..05.


-- =============================================================================
-- Example 6: head-to-head against ARIMA_PLUS -- how close is "model-free"?
-- =============================================================================
-- ML.TREND and ML.SEASONALITY run the ARIMA_PLUS decomposition without
-- materializing a model. Train the model on the identical series and difference
-- the components to see exactly how identical "the same algorithm" is.
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.time_series_scratch_arima`
OPTIONS(
  model_type = 'ARIMA_PLUS',
  time_series_timestamp_col = 'date',
  time_series_data_col = 'num_trips',
  horizon = 7
) AS
SELECT date, num_trips FROM `PROJECT_ID.DATASET.time_series_trips`
WHERE start_station_name = 'Pershing Square North' AND splits = 'TRAIN';

WITH arima AS (
  SELECT DATE(time_series_timestamp) AS date,
         trend                   AS arima_trend,
         seasonal_period_weekly  AS arima_weekly,
         seasonal_period_yearly  AS arima_yearly
  FROM ML.EXPLAIN_FORECAST(MODEL `PROJECT_ID.DATASET.time_series_scratch_arima`,
                           STRUCT(7 AS horizon))
  WHERE time_series_type = 'history'
),
tvf_trend AS (
  SELECT date, trend
  FROM ML.TREND(
    (SELECT date, num_trips FROM `PROJECT_ID.DATASET.time_series_trips`
     WHERE start_station_name = 'Pershing Square North' AND splits = 'TRAIN'),
    timestamp_col => 'date', data_col => 'num_trips',
    adjust_step_changes => TRUE)          -- match the model's default
  WHERE time_series_type = 'history'
),
tvf_seasonality AS (
  SELECT date, weekly, yearly
  FROM ML.SEASONALITY(
    (SELECT date, num_trips FROM `PROJECT_ID.DATASET.time_series_trips`
     WHERE start_station_name = 'Pershing Square North' AND splits = 'TRAIN'),
    timestamp_col => 'date', data_col => 'num_trips')
  WHERE time_series_type = 'history'
)
SELECT
  COUNT(*) AS n,
  ROUND(AVG(ABS(arima_trend  - trend)),  3) AS trend_mean_abs_diff,
  ROUND(CORR(arima_trend, trend),        4) AS trend_corr,
  ROUND(AVG(ABS(arima_weekly - weekly)), 3) AS weekly_mean_abs_diff,
  ROUND(CORR(arima_weekly, weekly),      4) AS weekly_corr,
  ROUND(AVG(ABS(arima_yearly - yearly)), 3) AS yearly_mean_abs_diff,
  ROUND(CORR(arima_yearly, yearly),      4) AS yearly_corr
FROM arima JOIN tvf_trend USING (date) JOIN tvf_seasonality USING (date);

-- Measured result (n = 1,341):
--   weekly   mean abs diff 0.0     corr 1.0      <- BIT-IDENTICAL
--   yearly   mean abs diff 0.0     corr 1.0      <- BIT-IDENTICAL
--   trend    mean abs diff 8.337   corr 0.9955   <- very close, not identical
--
-- So ML.SEASONALITY reproduces the ARIMA_PLUS seasonal decomposition exactly.
-- ML.TREND, even with adjust_step_changes => TRUE, does not quite: median
-- |difference| 5.755, p95 25.121, max 58.555.
--
-- Two option differences remain between the two calls and this comparison does
-- not separate them, so no single cause is claimed here: the trained model also
-- reports "cleanSpikesAndDips": true (ML.TREND exposes no equivalent option)
-- and "trendSmoothingWindowSize": -1 (auto), whereas ML.TREND's
-- smoothing_window_size default is unspecified. Either or both could account
-- for the residual.
--
-- Practical reading: reach for ML.SEASONALITY freely as a drop-in for the
-- model's seasonal components -- it is the same numbers without the CREATE
-- MODEL. Treat ML.TREND as very close but not a substitute if you need to
-- reproduce a specific model's trend to the digit.


-- =============================================================================
-- Example 7: change points are NOT anomalies -- measured on the same series
-- =============================================================================
WITH change_windows AS (
  SELECT DATE(begin_timestamp) AS b, DATE(end_timestamp) AS e
  FROM ML.DETECT_CHANGE_POINTS(
    (SELECT date, num_trips FROM `PROJECT_ID.DATASET.time_series_trips`
     WHERE start_station_name = 'Pershing Square North' AND splits = 'TRAIN'),
    timestamp_col => 'date', data_col => 'num_trips')
),
anomalies AS (
  SELECT DATE(date) AS d
  FROM ML.DETECT_ANOMALIES(MODEL `PROJECT_ID.DATASET.time_series_scratch_arima`,
                           STRUCT(0.95 AS anomaly_prob_threshold))
  WHERE is_anomaly
)
SELECT
  (SELECT COUNT(*) FROM anomalies)      AS row_level_anomalies,
  (SELECT COUNT(*) FROM change_windows) AS change_windows,
  (SELECT COUNT(*) FROM anomalies a JOIN change_windows c
    ON a.d BETWEEN c.b AND c.e)         AS overlap;

-- Measured: 79 anomalies, 2 change windows, overlap 0.
-- Not one of the 79 row-level anomalies falls inside a detected change window.
-- These are orthogonal detectors, not two sensitivities of one detector -- worth
-- knowing before wiring either into an alert, because "we already alert on
-- anomalies" does not mean structural shifts are covered.
--
-- Read the zero for what it is, though. On THIS series the separation is
-- sharper than it would generally be, for the reason Example 5 gives: the change
-- windows sit at the edges of an interpolated stretch, which is smooth by
-- construction and so contains nothing for a row-level detector to flag. The
-- result demonstrates that the two functions answer different questions; it is
-- not a measurement of how far apart their answers usually fall.


-- =============================================================================
-- Example 8: horizon -- these functions also forecast
-- =============================================================================
-- GOTCHA `horizon` is not a windowing or row-limit parameter. Supplying it makes
-- ML.TREND and ML.SEASONALITY EXTEND the series into the future: the extra rows
-- come back with time_series_type = 'forecast' alongside the 'history' rows.
-- ML.DETECT_CHANGE_POINTS has no horizon argument.
SELECT date, num_trips, ROUND(trend, 2) AS trend, time_series_type
FROM ML.TREND(
  (SELECT date, num_trips FROM `PROJECT_ID.DATASET.time_series_trips`
   WHERE start_station_name = 'Pershing Square North' AND splits = 'TRAIN'),
  timestamp_col => 'date',
  data_col => 'num_trips',
  horizon => 7
)
WHERE time_series_type = 'forecast'
ORDER BY date;

-- Returns 7 rows, 2018-05-04 .. 2018-05-10, alongside 1,341 'history' rows.
-- The TRAIN split ends 2018-05-03, so these extend exactly one horizon past it.
--
-- GOTCHA the data column is NOT NULL on forecast rows -- `num_trips` carries the
-- FORECAST VALUE there (551.60, 218.90, 173.72, 575.77, 690.72, 687.88, 715.53),
-- while `trend` carries only the trend component (455.0-455.6, nearly flat).
-- Nothing in the schema distinguishes an actual from a forecast except
-- `time_series_type`, so an unfiltered AVG(num_trips) silently mixes the two.


-- =============================================================================
-- Example 9: id_cols -- many series in one call
-- =============================================================================
-- All three functions take id_cols => ARRAY<STRING> to decompose each series
-- independently in a single pass, the same way ARIMA_PLUS's
-- time_series_id_col does. The id columns are echoed in the output.
SELECT start_station_name, COUNT(*) AS rows_returned,
       MIN(date) AS first_date, MAX(date) AS last_date
FROM ML.TREND(
  (SELECT start_station_name, date, num_trips
   FROM `PROJECT_ID.DATASET.time_series_trips` WHERE splits = 'TRAIN'),
  timestamp_col => 'date',
  data_col => 'num_trips',
  id_cols => ['start_station_name']
)
GROUP BY start_station_name
ORDER BY start_station_name;

-- This makes the gap-filling from Example 5 visible per series. Every station
-- comes back with one row per calendar day between its own first and last
-- observation -- more rows than the base table holds:
--   station                 raw rows -> returned rows
--   E 17 St & Broadway         1,580 -> 1,768
--   Lafayette St & E 8 St      1,508 -> 1,768
--   Pershing Square North      1,153 -> 1,341
--   W 21 St & 6 Ave            1,581 -> 1,768
--   West St & Chambers St      1,582 -> 1,768
-- Each series is filled to ITS OWN span, not to a common calendar: Pershing
-- Square North returns fewer rows only because it starts 2014-09-01 while the
-- other four start 2013-07-01. The function neither pads a late-starting series
-- backwards nor truncates the others to match.

-- Change points across all five stations at once:
SELECT start_station_name, begin_timestamp, end_timestamp, metrics.count
FROM ML.DETECT_CHANGE_POINTS(
  (SELECT start_station_name, date, num_trips
   FROM `PROJECT_ID.DATASET.time_series_trips` WHERE splits = 'TRAIN'),
  timestamp_col => 'date',
  data_col => 'num_trips',
  id_cols => ['start_station_name']
)
ORDER BY start_station_name, begin_timestamp;

-- Seven windows across the five stations. Four of the five open a window in the
-- last week of September 2016 -- the shared outage, once per series.
--
-- Rather than eyeball that, separate artifacts from real findings mechanically:
-- label each window with the size of the data gap whose edge it contains, if any.
WITH gaps AS (
  SELECT
    start_station_name,
    LAG(date) OVER (PARTITION BY start_station_name ORDER BY date) AS last_before,
    date AS first_after,
    DATE_DIFF(date, LAG(date) OVER (PARTITION BY start_station_name ORDER BY date), DAY) - 1 AS missing_days
  FROM `PROJECT_ID.DATASET.time_series_trips`
  WHERE splits = 'TRAIN'
),
change_windows AS (
  SELECT start_station_name, DATE(begin_timestamp) AS b, DATE(end_timestamp) AS e
  FROM ML.DETECT_CHANGE_POINTS(
    (SELECT start_station_name, date, num_trips
     FROM `PROJECT_ID.DATASET.time_series_trips` WHERE splits = 'TRAIN'),
    timestamp_col => 'date', data_col => 'num_trips',
    id_cols => ['start_station_name'])
)
SELECT
  c.start_station_name, c.b AS begin_date, c.e AS end_date,
  (SELECT MAX(g.missing_days) FROM gaps g
    WHERE g.start_station_name = c.start_station_name
      AND g.missing_days >= 3
      AND (g.last_before BETWEEN c.b AND c.e OR g.first_after BETWEEN c.b AND c.e)
  ) AS gap_edge_missing_days     -- NULL => not explained by a gap
FROM change_windows c
ORDER BY c.start_station_name, c.b;

-- SIX OF THE SEVEN windows sit on the edge of a data gap. Only one does not:
-- 'West St & Chambers St', 2016-04-27 .. 2016-05-07, which has all 11 days
-- present and a genuine level shift across it: averaging the raw daily counts,
-- the 30 days before the window run 248.1 trips/day, the window itself 210.9,
-- and the 30 days after 373.4.
--
-- That is the practical workflow for this function and it is two queries long:
-- profile the gaps, then keep the change points that do not land on one. Without
-- that filter, six of seven findings here would have been an ingestion story
-- reported as a ridership story.


-- =============================================================================
-- Cleanup
-- =============================================================================
DROP MODEL IF EXISTS `PROJECT_ID.DATASET.time_series_scratch_arima`;
DROP TABLE IF EXISTS `PROJECT_ID.DATASET.time_series_trips`;
