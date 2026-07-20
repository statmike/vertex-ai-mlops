-- Contribution Analysis — Progressive SQL Examples (BigQuery ML)
-- =============================================================
-- Trains a contribution analysis (a.k.a. key-driver) MODEL with
-- CREATE MODEL (model_type = 'CONTRIBUTION_ANALYSIS') -- detects which
-- segments of multi-dimensional data most explain a change in a metric
-- between a test set and a control set. Not a predictive model -- no
-- ML.PREDICT; insights are read afterward with ML.GET_INSIGHTS.
--
-- SCOPE / CROSS-LINK: the simplified, model-free equivalent --
-- AI.KEY_DRIVERS (a single table-valued function, no CREATE MODEL) --
-- is owned by ../../../bq-ai-functions/RESOURCES.md and
-- functions/ai_key_drivers/. This notebook uses the SAME dataset and
-- the SAME test/control split as that sibling notebook (NYC Citi Bike,
-- April 2016 vs April 2017) specifically to make a direct, apples-to-
-- apples comparison possible, and focuses on what CONTRIBUTION_ANALYSIS
-- can do that AI.KEY_DRIVERS cannot: summable-ratio and
-- summable-by-category metrics, and more than 12 dimensions.
--
-- Data: bigquery-public-data.new_york_citibike.citibike_trips
--       Test = April 2017, control = April 2016. Metric: trip duration
--       (seconds). Dimensions: user type, gender, start station (plus
--       an extra n=1/bikeid column for the ratio/category examples).
--
-- Full reference: ../../RESOURCES.md
-- Official docs:
--   CREATE MODEL (contribution analysis): https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-contribution-analysis
--   ML.GET_INSIGHTS: https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-get-insights
--   Contribution analysis overview: https://cloud.google.com/bigquery/docs/contribution-analysis


-- =============================================================================
-- Setup: Materialize the training data
-- =============================================================================
-- n=1 (for the ratio-metric example) and bikeid (for the category-metric
-- example) are included alongside the core columns. GOTCHA (verified):
-- CONTRIBUTION_ANALYSIS's training SELECT may contain ONLY the columns
-- referenced by contribution_metric, dimension_id_cols, and is_test_col
-- -- any extra column errors immediately ("Only is_test, dimension id,
-- and contribution metric columns are allowed as input columns"). Each
-- example below SELECTs only the exact subset of these columns it needs.
CREATE OR REPLACE TABLE `PROJECT_ID.DATASET.contribution_analysis_trips` AS
SELECT
  tripduration,
  1 AS n,
  bikeid,
  usertype,
  gender,
  start_station_name,
  (EXTRACT(YEAR FROM starttime) = 2017) AS is_test
FROM `bigquery-public-data.new_york_citibike.citibike_trips`
WHERE EXTRACT(MONTH FROM starttime) = 4
  AND EXTRACT(YEAR FROM starttime) IN (2016, 2017)
  AND tripduration IS NOT NULL;


-- =============================================================================
-- Example 1: CREATE MODEL — a summable metric (matches AI.KEY_DRIVERS exactly)
-- =============================================================================
-- contribution_metric='SUM(tripduration)' is the plain summable form --
-- the same capability AI.KEY_DRIVERS covers with metric_col='tripduration'.
-- Same data, same test/control split, same dimensions as
-- ../../../bq-ai-functions/functions/ai_key_drivers/ai_key_drivers.sql
-- Example 1, for direct comparison.
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.contribution_analysis_summable`
OPTIONS(
  model_type = 'CONTRIBUTION_ANALYSIS',
  contribution_metric = 'SUM(tripduration)',
  dimension_id_cols = ['usertype', 'gender', 'start_station_name'],
  is_test_col = 'is_test',
  top_k_insights_by_apriori_support = 15,
  pruning_method = 'PRUNE_REDUNDANT_INSIGHTS'
) AS
SELECT tripduration, usertype, gender, start_station_name, is_test
FROM `PROJECT_ID.DATASET.contribution_analysis_trips`;


-- =============================================================================
-- Example 2: ML.GET_INSIGHTS — summable-metric output shape
-- =============================================================================
-- Verified output columns for a SUMMABLE metric: contributors,
-- metric_test, metric_control, difference, relative_difference,
-- unexpected_difference, relative_unexpected_difference,
-- apriori_support, contribution (= ABS(difference)) -- plus each
-- dimension broken out into its own column (usertype, gender,
-- start_station_name here). This exactly matches AI.KEY_DRIVERS'
-- output shape (drivers/metric_interest/metric_reference vs.
-- contributors/metric_test/metric_control -- same fields, different
-- names).
SELECT *
FROM ML.GET_INSIGHTS(MODEL `PROJECT_ID.DATASET.contribution_analysis_summable`)
ORDER BY contribution DESC
LIMIT 10;


-- =============================================================================
-- Example 3: CREATE MODEL — a summable-RATIO metric (beyond AI.KEY_DRIVERS)
-- =============================================================================
-- contribution_metric='SUM(a)/SUM(b)' -- AI.KEY_DRIVERS has no equivalent;
-- it only supports a single summable column. Here SUM(tripduration)/SUM(n)
-- is average trip duration, expressed as a ratio of two summable
-- quantities (n=1 per row, so SUM(n) = row count).
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.contribution_analysis_ratio`
OPTIONS(
  model_type = 'CONTRIBUTION_ANALYSIS',
  contribution_metric = 'SUM(tripduration)/SUM(n)',
  dimension_id_cols = ['usertype', 'gender', 'start_station_name'],
  is_test_col = 'is_test',
  top_k_insights_by_apriori_support = 15,
  pruning_method = 'PRUNE_REDUNDANT_INSIGHTS'
) AS
SELECT tripduration, n, usertype, gender, start_station_name, is_test
FROM `PROJECT_ID.DATASET.contribution_analysis_trips`;


-- =============================================================================
-- Example 4: ML.GET_INSIGHTS — the RATIO metric has a DIFFERENT output shape
-- =============================================================================
-- GOTCHA (verified): a ratio metric's ML.GET_INSIGHTS output is NOT the
-- same shape as Example 2's summable output. difference/
-- relative_difference/unexpected_difference/relative_unexpected_difference
-- are gone; in their place: metric_test_over_metric_control,
-- metric_test_over_complement, metric_control_over_complement, and
-- aumann_shapley_attribution. contribution here EQUALS
-- ABS(aumann_shapley_attribution) (a Shapley-value-based attribution) --
-- not ABS(difference) as it is for summable metrics, but the same
-- "take the absolute value" pattern (verified on rows where
-- aumann_shapley_attribution is negative, e.g. usertype=Subscriber:
-- aumann_shapley_attribution=-49.86, contribution=49.86). Don't assume
-- ML.GET_INSIGHTS has one fixed output schema across metric types.
SELECT *
FROM ML.GET_INSIGHTS(MODEL `PROJECT_ID.DATASET.contribution_analysis_ratio`)
ORDER BY contribution DESC
LIMIT 10;


-- =============================================================================
-- Example 5: CREATE MODEL — a summable-by-CATEGORY metric (beyond AI.KEY_DRIVERS)
-- =============================================================================
-- contribution_metric='SUM(a)/COUNT(DISTINCT b)' -- also beyond
-- AI.KEY_DRIVERS. SUM(tripduration)/COUNT(DISTINCT bikeid) is total ride
-- minutes accumulated per unique bike used -- a bike-utilization measure.
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.contribution_analysis_category`
OPTIONS(
  model_type = 'CONTRIBUTION_ANALYSIS',
  contribution_metric = 'SUM(tripduration)/COUNT(DISTINCT bikeid)',
  dimension_id_cols = ['usertype', 'gender', 'start_station_name'],
  is_test_col = 'is_test',
  top_k_insights_by_apriori_support = 15,
  pruning_method = 'PRUNE_REDUNDANT_INSIGHTS'
) AS
SELECT tripduration, bikeid, usertype, gender, start_station_name, is_test
FROM `PROJECT_ID.DATASET.contribution_analysis_trips`;


-- =============================================================================
-- Example 6: ML.GET_INSIGHTS — the CATEGORY metric has a THIRD output shape
-- =============================================================================
-- GOTCHA (verified): summable-by-category's output is a third distinct
-- shape -- difference/relative_difference return (like summable), but
-- unexpected_difference/relative_unexpected_difference are replaced by
-- metric_test_over_population/metric_control_over_population.
-- contribution here is ABS(difference) again (like summable), not
-- aumann_shapley_attribution. Three metric types, three different
-- ML.GET_INSIGHTS schemas -- verified directly, not documented in the
-- official reference at the time this was tested.
SELECT *
FROM ML.GET_INSIGHTS(MODEL `PROJECT_ID.DATASET.contribution_analysis_category`)
ORDER BY contribution DESC
LIMIT 10;


-- =============================================================================
-- Example 7: More than 12 dimensions (beyond AI.KEY_DRIVERS' cap)
-- =============================================================================
-- AI.KEY_DRIVERS caps dimension_cols at 12. Verified: CONTRIBUTION_ANALYSIS
-- accepts 13 (tested with all-low-cardinality dimensions to isolate
-- dimension COUNT from per-dimension cardinality). GOTCHA (verified,
-- real cost tradeoff): this took ~13 minutes to train, vs. ~5 seconds
-- for Example 1's 3-dimension model on the same row count -- more
-- dimensions is combinatorially more expensive, even at low cardinality
-- per dimension. A separate attempt with 13 dimensions where several
-- were HIGH-cardinality (raw station IDs, individual bike IDs) ran for
-- over 18 minutes and then failed with a generic internal-error message
-- rather than a clean validation error -- BigQuery framed it as
-- "usually a transient issue," but it did not reproduce with
-- low-cardinality dimensions at the same count, suggesting per-dimension
-- cardinality (not just dimension count) drives the real cost/risk.
CREATE OR REPLACE TABLE `PROJECT_ID.DATASET.contribution_analysis_trips_lowcard` AS
SELECT
  tripduration,
  usertype,
  gender,
  CAST(EXTRACT(HOUR FROM starttime) AS STRING) AS start_hour,
  CAST(EXTRACT(DAYOFWEEK FROM starttime) AS STRING) AS day_of_week,
  CAST(EXTRACT(DAY FROM starttime) AS STRING) AS day_of_month,
  CASE WHEN birth_year < 1970 THEN 'older' WHEN birth_year < 1990 THEN 'middle' ELSE 'younger' END AS age_band,
  CASE WHEN start_station_id = end_station_id THEN 'round_trip' ELSE 'one_way' END AS trip_type,
  CASE WHEN tripduration > 600 THEN 'long' ELSE 'short' END AS duration_band,
  CASE WHEN EXTRACT(DAYOFWEEK FROM starttime) IN (1,7) THEN 'weekend' ELSE 'weekday' END AS is_weekend,
  CASE WHEN EXTRACT(HOUR FROM starttime) BETWEEN 7 AND 9 OR EXTRACT(HOUR FROM starttime) BETWEEN 16 AND 18 THEN 'rush' ELSE 'non_rush' END AS is_rush_hour,
  CASE WHEN EXTRACT(HOUR FROM starttime) BETWEEN 22 AND 23 OR EXTRACT(HOUR FROM starttime) BETWEEN 0 AND 5 THEN 'night' ELSE 'day' END AS is_night,
  CAST(NTILE(4) OVER (ORDER BY tripduration) AS STRING) AS duration_quartile,
  CASE WHEN EXTRACT(DAY FROM starttime) <= 15 THEN 'first_half' ELSE 'second_half' END AS month_half,
  (EXTRACT(YEAR FROM starttime) = 2017) AS is_test
FROM `bigquery-public-data.new_york_citibike.citibike_trips`
WHERE EXTRACT(MONTH FROM starttime) = 4
  AND EXTRACT(YEAR FROM starttime) IN (2016, 2017)
  AND tripduration IS NOT NULL;

CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.contribution_analysis_13dims`
OPTIONS(
  model_type = 'CONTRIBUTION_ANALYSIS',
  contribution_metric = 'SUM(tripduration)',
  dimension_id_cols = ['usertype', 'gender', 'start_hour', 'day_of_week', 'day_of_month', 'age_band', 'trip_type', 'duration_band', 'is_weekend', 'is_rush_hour', 'is_night', 'duration_quartile', 'month_half'],
  is_test_col = 'is_test',
  top_k_insights_by_apriori_support = 10,
  pruning_method = 'PRUNE_REDUNDANT_INSIGHTS'
) AS
SELECT * FROM `PROJECT_ID.DATASET.contribution_analysis_trips_lowcard`;

SELECT contributors, contribution
FROM ML.GET_INSIGHTS(MODEL `PROJECT_ID.DATASET.contribution_analysis_13dims`)
ORDER BY contribution DESC
LIMIT 10;


-- =============================================================================
-- Example 8: min_apriori_support / top_k_insights_by_apriori_support / pruning_method
-- =============================================================================
-- Verified: min_apriori_support and top_k_insights_by_apriori_support
-- are genuinely mutually exclusive -- specifying both errors immediately
-- ("Please specify only one of the MIN_APRIORI_SUPPORT or
-- TOP_K_INSIGHTS_BY_APRIORI_SUPPORT options.").
--
-- Verified: pruning_method has a dramatic effect on output size.
-- NO_PRUNING with a low min_apriori_support (0.001) on the same 3
-- dimensions as Example 1 returned 1,559 insight rows; Example 1's
-- PRUNE_REDUNDANT_INSIGHTS + top_k=15 returned exactly 15. Use
-- top_k_insights_by_apriori_support + PRUNE_REDUNDANT_INSIGHTS (the
-- default in every other example here) unless you specifically need
-- every subset-redundant segment.
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.contribution_analysis_no_pruning`
OPTIONS(
  model_type = 'CONTRIBUTION_ANALYSIS',
  contribution_metric = 'SUM(tripduration)',
  dimension_id_cols = ['usertype', 'gender', 'start_station_name'],
  is_test_col = 'is_test',
  min_apriori_support = 0.001,
  pruning_method = 'NO_PRUNING'
) AS
SELECT tripduration, usertype, gender, start_station_name, is_test
FROM `PROJECT_ID.DATASET.contribution_analysis_trips`;

SELECT COUNT(*) AS n_insights
FROM ML.GET_INSIGHTS(MODEL `PROJECT_ID.DATASET.contribution_analysis_no_pruning`);


-- =============================================================================
-- Example 9: Functions that do NOT apply to this model type
-- =============================================================================
-- GOTCHA (verified): no TRANSFORM clause -- errors immediately
-- ("Transform clause is not supported for the model type
-- CONTRIBUTION_ANALYSIS").
--
-- GOTCHA (verified): ML.PREDICT and ML.EVALUATE both error, but with
-- unhelpful messages that don't clearly say "not supported for this
-- model type" -- ML.PREDICT complains a 'contributors' column is
-- missing from the input; ML.EVALUATE called with no arguments says the
-- model "was not evaluated during training" and asks for data to
-- evaluate with. Passing a data argument doesn't help either -- it then
-- asks for a 'label' column instead, which this model type doesn't
-- have. This model type simply has no ML.PREDICT/ML.EVALUATE --
-- ML.GET_INSIGHTS is the only way to read results.
--
-- SELECT * FROM ML.PREDICT(MODEL `PROJECT_ID.DATASET.contribution_analysis_summable`, (SELECT 1));
-- SELECT * FROM ML.EVALUATE(MODEL `PROJECT_ID.DATASET.contribution_analysis_summable`);


-- =============================================================================
-- Cleanup
-- =============================================================================
-- DROP MODEL IF EXISTS `PROJECT_ID.DATASET.contribution_analysis_summable`;
-- DROP MODEL IF EXISTS `PROJECT_ID.DATASET.contribution_analysis_ratio`;
-- DROP MODEL IF EXISTS `PROJECT_ID.DATASET.contribution_analysis_category`;
-- DROP MODEL IF EXISTS `PROJECT_ID.DATASET.contribution_analysis_13dims`;
-- DROP MODEL IF EXISTS `PROJECT_ID.DATASET.contribution_analysis_no_pruning`;
-- DROP TABLE IF EXISTS `PROJECT_ID.DATASET.contribution_analysis_trips`;
-- DROP TABLE IF EXISTS `PROJECT_ID.DATASET.contribution_analysis_trips_lowcard`;
