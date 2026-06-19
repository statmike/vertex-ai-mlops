-- AI.KEY_DRIVERS — Progressive SQL Examples
-- ==========================================
-- Table-valued function for key driver / contribution analysis. Identifies the
-- data segments that cause statistically significant changes to a summable
-- metric between an interest set and a reference set.
-- No model creation, connection, or endpoint required.
--
-- Requires: a table/subquery with a summable metric, a BOOL interest/reference
-- column, and 1-12 dimension columns (INT64, BOOL, or STRING)
--
-- Returns: drivers (segment), metric_interest, metric_reference, difference,
--          relative_difference, unexpected_difference,
--          relative_unexpected_difference, apriori_support, contribution
-- Limit: maximum 12 dimensions; summable metrics only
--
-- Full reference: ../../RESOURCES.md
-- Official docs: https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-key-drivers


-- =============================================================================
-- Setup: Materialize a compact slice of NYC Citi Bike data
-- =============================================================================
-- Interest = April 2017, Reference = April 2016. The summable metric is trip
-- duration (seconds). Dimensions: user type, gender, and start station.
CREATE OR REPLACE TABLE `PROJECT_ID.DATASET.ai_key_drivers_trips` AS
SELECT
  tripduration,
  usertype,
  gender,
  start_station_name,
  (EXTRACT(YEAR FROM starttime) = 2017) AS is_interest
FROM `bigquery-public-data.new_york_citibike.citibike_trips`
WHERE EXTRACT(MONTH FROM starttime) = 4
  AND EXTRACT(YEAR FROM starttime) IN (2016, 2017)
  AND tripduration IS NOT NULL;


-- =============================================================================
-- Example 1: Basic key driver analysis
-- =============================================================================
-- Which segments most explain the year-over-year change in trip duration?
-- top_k returns the highest-support insights and prunes the rest.
SELECT * EXCEPT(usertype, gender, start_station_name)
FROM AI.KEY_DRIVERS(
  TABLE `PROJECT_ID.DATASET.ai_key_drivers_trips`,
  metric_col => 'tripduration',
  dimension_cols => ['usertype', 'gender', 'start_station_name'],
  interest_label_col => 'is_interest',
  top_k => 15
);


-- =============================================================================
-- Example 2: SUM(metric) form is equivalent to the bare column name
-- =============================================================================
-- metric_col accepts either 'tripduration' or 'SUM(tripduration)'.
SELECT drivers, metric_interest, metric_reference, difference
FROM AI.KEY_DRIVERS(
  TABLE `PROJECT_ID.DATASET.ai_key_drivers_trips`,
  metric_col => 'SUM(tripduration)',
  dimension_cols => ['usertype', 'gender'],
  interest_label_col => 'is_interest',
  top_k => 10
)
ORDER BY contribution DESC;


-- =============================================================================
-- Example 3: Rank by unexpected_difference — segments defying the overall trend
-- =============================================================================
-- unexpected_difference compares a segment's actual change to the change
-- expected from all other segments. Large values flag surprising movers.
SELECT
  drivers,
  difference,
  unexpected_difference,
  apriori_support
FROM AI.KEY_DRIVERS(
  TABLE `PROJECT_ID.DATASET.ai_key_drivers_trips`,
  metric_col => 'tripduration',
  dimension_cols => ['usertype', 'gender', 'start_station_name'],
  interest_label_col => 'is_interest',
  top_k => 25
)
ORDER BY ABS(unexpected_difference) DESC
LIMIT 10;


-- =============================================================================
-- Example 4: min_apriori_support threshold (mutually exclusive with top_k)
-- =============================================================================
-- Use min_apriori_support => 0 to return every segment regardless of size.
-- Cannot be combined with top_k.
SELECT drivers, difference, relative_difference, apriori_support
FROM AI.KEY_DRIVERS(
  TABLE `PROJECT_ID.DATASET.ai_key_drivers_trips`,
  metric_col => 'tripduration',
  dimension_cols => ['usertype', 'gender'],
  interest_label_col => 'is_interest',
  min_apriori_support => 0.05
)
ORDER BY contribution DESC;


-- =============================================================================
-- Example 5: enable_pruning => FALSE — see redundant insights
-- =============================================================================
-- By default redundant insights are pruned. Set FALSE to see the full
-- unpruned breakdown (more rows, including subset segments).
SELECT drivers, difference, contribution
FROM AI.KEY_DRIVERS(
  TABLE `PROJECT_ID.DATASET.ai_key_drivers_trips`,
  metric_col => 'tripduration',
  dimension_cols => ['usertype', 'gender'],
  interest_label_col => 'is_interest',
  min_apriori_support => 0.05,
  enable_pruning => FALSE
)
ORDER BY contribution DESC;


-- =============================================================================
-- Example 6: Interpreting the output columns
-- =============================================================================
-- relative_difference = difference / metric_reference (percent change)
-- contribution        = ABS(difference)               (magnitude of the move)
-- A new segment present only in the interest set has a NULL relative_difference
-- (its metric_reference is 0).
SELECT
  drivers,
  metric_interest,
  metric_reference,
  difference,
  ROUND(relative_difference, 3) AS pct_change,
  contribution
FROM AI.KEY_DRIVERS(
  TABLE `PROJECT_ID.DATASET.ai_key_drivers_trips`,
  metric_col => 'tripduration',
  dimension_cols => ['usertype', 'gender', 'start_station_name'],
  interest_label_col => 'is_interest',
  top_k => 15
)
ORDER BY contribution DESC;


-- =============================================================================
-- Example 7: Inline subquery — build the interest/reference split on the fly
-- =============================================================================
-- No pre-materialized table needed: construct the BOOL interest column and
-- dimensions directly in a subquery over the raw data.
SELECT * EXCEPT(usertype, gender)
FROM AI.KEY_DRIVERS(
  (SELECT
     tripduration,
     usertype,
     gender,
     (EXTRACT(YEAR FROM starttime) = 2017) AS is_interest
   FROM `bigquery-public-data.new_york_citibike.citibike_trips`
   WHERE EXTRACT(MONTH FROM starttime) = 4
     AND EXTRACT(YEAR FROM starttime) IN (2016, 2017)
     AND tripduration IS NOT NULL),
  metric_col => 'tripduration',
  dimension_cols => ['usertype', 'gender'],
  interest_label_col => 'is_interest',
  top_k => 10
)
ORDER BY contribution DESC;
