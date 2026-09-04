-- AI.DETECT_ANOMALIES — Progressive SQL Examples
-- ================================================
-- Table-valued function that detects anomalies using TimesFM.
-- Forecasts baseline from history, flags deviations in target data.
--
-- Returns: time_series_timestamp, time_series_data, is_anomaly,
--          lower/upper_bound, anomaly_probability, status
--
-- Model version: the default is TimesFM 2.5 (it was 2.0 and moved with no
--   release note). Pin `model` so a future default move cannot shift your
--   numbers -- but pinning does NOT make this function reproducible. A
--   minority of runs return a different result with `model` and
--   `context_window` both pinned and the query cache off; the same behavior is
--   measured in detail on AI.EVALUATE, where 2 of 16 pinned runs moved the
--   reported error by ~32%. Materialize the anomaly table once and read the
--   stored rows rather than re-running the function.
--
-- Full reference: ../../RESOURCES.md
-- Official docs: https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-detect-anomalies
--
-- Looking for sustained level shifts rather than individual outlying points?
-- See ../../../bq-ml/functions/time_series/ -- ML.DETECT_CHANGE_POINTS finds
-- structural change windows with no model and no forecast baseline. A spike
-- that returns to normal is an anomaly, not a change point; a permanent step
-- up in volume is a change point that may never register as an anomaly.


-- =============================================================================
-- Example 1: Basic anomaly detection
-- =============================================================================
SELECT *
FROM AI.DETECT_ANOMALIES(
  TABLE `PROJECT_ID.DATASET.ai_detect_anomalies_history`,
  TABLE `PROJECT_ID.DATASET.ai_detect_anomalies_target`,
  data_col => 'daily_sales',
  timestamp_col => 'date'
)
ORDER BY time_series_timestamp;


-- =============================================================================
-- Example 2: Stricter threshold (only extreme anomalies)
-- =============================================================================
-- anomaly_prob_threshold default is 0.95.
-- Higher = fewer anomalies (only the most extreme); Lower = more anomalies.
SELECT time_series_timestamp, time_series_data, is_anomaly,
  ROUND(anomaly_probability, 4) AS anomaly_prob
FROM AI.DETECT_ANOMALIES(
  TABLE `PROJECT_ID.DATASET.ai_detect_anomalies_history`,
  TABLE `PROJECT_ID.DATASET.ai_detect_anomalies_target`,
  data_col => 'daily_sales',
  timestamp_col => 'date',
  anomaly_prob_threshold => 0.99
)
ORDER BY anomaly_prob DESC;


-- =============================================================================
-- Example 3: Only anomalous points
-- =============================================================================
SELECT time_series_timestamp, time_series_data, anomaly_probability
FROM AI.DETECT_ANOMALIES(
  TABLE `PROJECT_ID.DATASET.ai_detect_anomalies_history`,
  TABLE `PROJECT_ID.DATASET.ai_detect_anomalies_target`,
  data_col => 'daily_sales',
  timestamp_col => 'date'
)
WHERE is_anomaly = TRUE
ORDER BY anomaly_probability DESC;
