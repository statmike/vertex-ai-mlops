-- Exploratory Data Analysis — Progressive SQL Examples (BigQuery ML model-free functions)
-- =============================================================
-- Two model-free table-valued functions, in the order you use them.
-- ML.DESCRIBE_DATA (GA) profiles every column of a relation: counts, nulls,
-- min/max, quantiles, top values. ML.CORRELATION (Preview) measures which
-- numeric columns move with a target column -- Pearson, Spearman, or Kendall
-- -- optionally sliced by every combination of the dimensions you name.
-- Neither trains a model, neither needs a connection, neither creates an
-- object you have to clean up.
--
-- GOTCHA the ML.DESCRIBE_DATA reference page names the standard-deviation
-- output column `stdev`. The function returns `stddev`. Selecting `stdev`
-- errors with "Unrecognized name: stdev; Did you mean stddev?".
--
-- GOTCHA ML.DESCRIBE_DATA's `num_nulls` is honest and still misleading when
-- missing values are string-encoded. On census_adult_income, `workclass`
-- reports num_nulls = 0 while its `min` is ' ?' and 1,836 rows carry that
-- placeholder. Read `min`/`max` on categorical columns -- placeholder
-- encodings live at the alphabetical edges.
--
-- GOTCHA ML.CORRELATION's SPEARMAN is NOT the textbook Spearman on tied
-- data. It is CORR() over SQL RANK() -- competition (min) ranks, not the
-- mid-ranks that SciPy/pandas/R use. On tie-free data all conventions agree;
-- on census_adult_income (education_num has 16 distinct values across 32,561
-- rows) the two answers differ in the second decimal place. KENDALL, in the
-- same function, IS the tie-corrected tau-b. One method corrects for ties
-- and the other does not.
--
-- GOTCHA KENDALL is O(n^2) and the constant is not small. Pearson and
-- Spearman return in seconds at 1,000,000 rows; a KENDALL at 100,000 rows
-- does not finish inside 12 minutes. Sample or segment before using it.
--
-- GOTCHA `segment_size` is the segment's ROW count, not the pairwise n the
-- correlation was computed from. Rows where either the target or that
-- correlation column is NULL are dropped pairwise, so `WHERE segment_size >=
-- 30` does not guarantee 30 usable pairs, and two corr_cols on the same
-- output row can rest on different sample sizes.
--
-- GOTCHA projecting the `segment` column changes `correlation` in its last
-- three digits, reproducibly, with the query cache off -- column pruning
-- changes the plan, which changes the float summation order. Never compare
-- ML.CORRELATION output across queries with `=`; round first.
--
-- Data: bigquery-public-data.ml_datasets.census_adult_income (same dataset
--       as models/logistic_regression/ and functions/data_quality/)
--
-- Full reference: ../../reference/model-free-functions.md
-- Official docs:
--   ML.DESCRIBE_DATA: https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-describe-data
--   ML.CORRELATION:   https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-correlation


-- =============================================================================
-- Example 1: ML.DESCRIBE_DATA -- descriptive stats, numeric and categorical
-- =============================================================================
-- One row per input column. top_k = how many top categorical values to
-- return (default 1); num_quantiles = numeric quantile granularity
-- (default 2, which returns three boundaries: min, median, max).
SELECT name, num_rows, num_values, num_nulls, num_zeros,
       min, max, mean, stddev, median, quantiles
FROM ML.DESCRIBE_DATA(
  TABLE `bigquery-public-data.ml_datasets.census_adult_income`,
  STRUCT(3 AS top_k, 4 AS num_quantiles)
)
WHERE name IN ('age', 'education_num', 'hours_per_week', 'capital_gain')
ORDER BY name;
-- Verified: capital_gain is a spike-at-zero column -- num_zeros = 29,849 of
-- 32,561 rows, and with num_quantiles => 4 every interior quantile boundary
-- is still 0. Any correlation involving it will read small regardless of the
-- relationship among the non-zero rows.

-- Categorical columns populate unique/top_values/avg_string_length instead
-- of the numeric stats columns.
SELECT name, unique, num_nulls, avg_string_length, min, max, top_values
FROM ML.DESCRIBE_DATA(
  TABLE `bigquery-public-data.ml_datasets.census_adult_income`,
  STRUCT(3 AS top_k, 4 AS num_quantiles)
)
WHERE name IN ('workclass', 'income_bracket')
ORDER BY name;
-- Verified: workclass reports num_nulls = 0 and min = ' ?' -- both true.
-- The missing values are string-encoded, so they are not NULLs, and `unique`
-- = 9 counts the placeholder as one of the categories.

SELECT
  COUNT(*)                              AS total_rows,
  COUNTIF(workclass IS NULL)            AS actual_nulls,
  COUNTIF(TRIM(workclass) = '?')        AS placeholder_workclass,
  COUNTIF(TRIM(occupation) = '?')       AS placeholder_occupation,
  COUNTIF(TRIM(native_country) = '?')   AS placeholder_native_country
FROM `bigquery-public-data.ml_datasets.census_adult_income`;
-- Verified: 0 actual NULLs, 1,836 placeholder workclass rows.

-- The documented output column name is wrong -- `stdev` does not exist.
-- SELECT name, stdev
-- FROM ML.DESCRIBE_DATA((SELECT age FROM `bigquery-public-data.ml_datasets.census_adult_income`));
-- Error: Unrecognized name: stdev; Did you mean stddev?


-- =============================================================================
-- Setup: a cleaned table -- string placeholders become real NULLs
-- =============================================================================
-- Fix what Example 1 found before correlating anything. This also gives
-- workclass a genuine NULL group, which Example 6 needs.
CREATE OR REPLACE TABLE `PROJECT_ID.DATASET.exploration_census` AS
SELECT
  education_num,
  age,
  hours_per_week,
  capital_gain,
  capital_loss,
  TRIM(sex)                      AS sex,
  TRIM(race)                     AS race,
  TRIM(marital_status)           AS marital_status,
  NULLIF(TRIM(workclass), '?')   AS workclass,
  TRIM(income_bracket)           AS income_bracket
FROM `bigquery-public-data.ml_datasets.census_adult_income`;


-- =============================================================================
-- Example 2: ML.CORRELATION -- one target against many metric columns
-- =============================================================================
-- Signature: one target_col and one or more target_correlation_cols, all
-- numeric. With no dimension_cols you get one row per correlation column
-- over the whole relation.
SELECT target_col, corr_col, correlation, segment_size, segment_proportion
FROM ML.CORRELATION(
  TABLE `PROJECT_ID.DATASET.exploration_census`,
  target_col => 'education_num',
  target_correlation_cols => ['age', 'hours_per_week', 'capital_gain', 'capital_loss']
)
ORDER BY ABS(correlation) DESC;
-- Verified: hours_per_week ~0.1481 is the strongest of the four; capital_gain
-- ~0.1226 is the muted number Example 1's num_zeros predicted.


-- =============================================================================
-- Example 3: PEARSON is CORR() -- to ~15 significant digits, not bit-for-bit
-- =============================================================================
WITH src AS (
  SELECT * FROM `PROJECT_ID.DATASET.exploration_census`
),
mlc AS (
  SELECT corr_col, correlation
  FROM ML.CORRELATION(TABLE src,
    target_col => 'education_num',
    target_correlation_cols => ['age', 'hours_per_week', 'capital_gain'])
),
native AS (
  SELECT 'age'            AS corr_col, CORR(education_num, age)            AS c FROM src
  UNION ALL
  SELECT 'hours_per_week',            CORR(education_num, hours_per_week)       FROM src
  UNION ALL
  SELECT 'capital_gain',              CORR(education_num, capital_gain)         FROM src
)
SELECT
  m.corr_col,
  m.correlation             AS ml_correlation,
  n.c                       AS native_corr,
  m.correlation = n.c       AS bit_identical,
  ABS(m.correlation - n.c)  AS abs_diff
FROM mlc m JOIN native n USING (corr_col)
ORDER BY corr_col;
-- Verified: same statistic, abs_diff on the order of 1e-15 -- and
-- bit_identical = FALSE. Float summation order, not a different formula.
-- Note this example also demonstrates that a WITH alias is a valid
-- `TABLE table_name` argument to the TVF.

-- The same instability, isolated: the ONLY thing that changes between these
-- two queries is whether the `segment` column is projected.
SELECT correlation FROM ML.CORRELATION(
  TABLE `PROJECT_ID.DATASET.exploration_census`,
  target_col => 'education_num', target_correlation_cols => ['age']);
SELECT correlation, segment FROM ML.CORRELATION(
  TABLE `PROJECT_ID.DATASET.exploration_census`,
  target_col => 'education_num', target_correlation_cols => ['age']);
-- Verified with the query cache off: 0.036527189464106255 without `segment`,
-- 0.036527189464106456 with it. Every projection that includes `segment`
-- returns the second value; every projection that omits it returns the
-- first. Round before comparing.


-- =============================================================================
-- Example 4: SPEARMAN uses SQL RANK() (min ranks), not mid-ranks
-- =============================================================================
WITH src AS (SELECT education_num, age FROM `PROJECT_ID.DATASET.exploration_census`),
ranked AS (
  SELECT RANK() OVER (ORDER BY education_num) AS rank_target,
         RANK() OVER (ORDER BY age)           AS rank_metric
  FROM src
)
SELECT
  ROUND((SELECT correlation FROM ML.CORRELATION(TABLE src,
           target_col => 'education_num',
           target_correlation_cols => ['age'],
           method => 'SPEARMAN')), 12)                           AS ml_spearman,
  ROUND((SELECT CORR(rank_target, rank_metric) FROM ranked), 12)  AS corr_of_sql_rank,
  (SELECT COUNT(*) - COUNT(DISTINCT education_num) FROM src)      AS tied_rows_in_target,
  (SELECT COUNT(*) - COUNT(DISTINCT age) FROM src)                AS tied_rows_in_metric;
-- Verified: identical to 12 decimal places -- ML.CORRELATION's SPEARMAN is
-- CORR() over RANK(). On education_num vs age that is ~0.069707, while
-- mid-rank (textbook / scipy.stats.spearmanr) Spearman is ~0.066345.

-- Control: with zero ties, every ranking convention is the same ranking.
WITH src AS (
  SELECT i AS t, MOD(i * 7919, 999983) AS x
  FROM UNNEST(GENERATE_ARRAY(1, 5000)) AS i
),
ranked AS (
  SELECT RANK() OVER (ORDER BY t) AS rt, RANK() OVER (ORDER BY x) AS rx FROM src
)
SELECT
  (SELECT COUNT(*) - COUNT(DISTINCT x) FROM src)  AS tied_rows_in_x,
  ROUND((SELECT correlation FROM ML.CORRELATION(TABLE src,
     target_col => 't', target_correlation_cols => ['x'], method => 'SPEARMAN')), 12) AS ml_spearman,
  ROUND((SELECT CORR(rt, rx) FROM ranked), 12)    AS corr_of_sql_rank;
-- Verified: 0 ties, and ML.CORRELATION, CORR-over-RANK, and
-- scipy.stats.spearmanr all agree exactly. So the disagreement above is a
-- tie convention, not a bug -- but it is undocumented, and it only shows up
-- on tied data, which is most real integer-coded columns.


-- =============================================================================
-- Example 5: KENDALL is tau-b -- the tie-corrected variant
-- =============================================================================
SELECT corr_col, correlation
FROM ML.CORRELATION(
  TABLE `PROJECT_ID.DATASET.exploration_census`,
  target_col => 'education_num',
  target_correlation_cols => ['age', 'hours_per_week'],
  method => 'KENDALL');
-- Verified against scipy.stats.kendalltau: education_num vs age returns
-- ~0.0530008, matching tau-b (variant='b') to ~1e-17, not tau-c (~0.0503).
-- So within one function, KENDALL corrects for ties and SPEARMAN does not.

-- Cost, measured with the query cache off and read from job.slot_millis:
-- PEARSON and SPEARMAN are startup-dominated and flat through 1,000,000
-- rows (seconds). KENDALL fits close to n^2 above n = 5,000; at n = 100,000
-- it passes 11 slot-minutes without finishing. Run it on a sample or a
-- single segment, never on a raw fact table -- SPEARMAN gives rank-based
-- robustness at PEARSON's price.


-- =============================================================================
-- Example 6: dimension_cols IS GROUP BY CUBE
-- =============================================================================
-- Not "similar to" -- the same, down to the row count.
WITH src AS (
  SELECT education_num, age, sex, race, marital_status
  FROM `PROJECT_ID.DATASET.exploration_census`
),
cube_cells AS (
  SELECT sex, race, marital_status, COUNT(*) AS n
  FROM src
  GROUP BY CUBE (sex, race, marital_status)
)
SELECT
  (SELECT COUNT(*) FROM cube_cells)                            AS group_by_cube_cells,
  (SELECT COUNT(*) FROM ML.CORRELATION(TABLE src,
     target_col => 'education_num',
     target_correlation_cols => ['age'],
     dimension_cols => ['sex', 'race', 'marital_status']))     AS ml_correlation_rows,
  (SELECT COUNT(*) FROM cube_cells WHERE n = 1)                AS single_row_cells;
-- Verified: 134 = 134. Degenerate cells are NOT dropped -- a one-row segment
-- comes back with correlation = NULL rather than being filtered out, which
-- is why the counts match exactly.

-- ARRAY_LENGTH(segment) is how many dimensions a row is NOT rolled up over.
SELECT
  ARRAY_LENGTH(segment)        AS dims_in_segment,
  COUNT(*)                     AS rows_out,
  COUNTIF(correlation IS NULL) AS null_correlations,
  MIN(segment_size)            AS smallest_segment,
  MAX(segment_size)            AS largest_segment
FROM ML.CORRELATION(
  TABLE `PROJECT_ID.DATASET.exploration_census`,
  target_col => 'education_num',
  target_correlation_cols => ['age'],
  dimension_cols => ['sex', 'race', 'marital_status'])
GROUP BY dims_in_segment
ORDER BY dims_in_segment;

-- ANTI-PATTERN: dimension_cols accepts any groupable type, including INT64.
-- Passing a continuous column gives one segment per distinct value, silently
-- -- no error, no warning. Bucketize first (see functions/bucketizing/).
SELECT
  (SELECT COUNT(DISTINCT age) FROM `PROJECT_ID.DATASET.exploration_census`) AS distinct_ages,
  (SELECT COUNT(*) FROM ML.CORRELATION(
     TABLE `PROJECT_ID.DATASET.exploration_census`,
     target_col => 'education_num',
     target_correlation_cols => ['capital_gain'],
     dimension_cols => ['age'])) AS rows_out_using_age_as_a_dimension;

-- The hard ceiling is 12, and that error IS explicit:
-- ML.CORRELATION expects the number of columns in dimension_cols to be no
-- more than 12, but 13 were provided.


-- =============================================================================
-- Example 7: two kinds of NULL in one dimension column
-- =============================================================================
-- A dimension column is NULL either because the row is a rollup OVER that
-- dimension, or because the segment IS the genuine NULL group in the data.
-- The `segment` array disambiguates: a rolled-up dimension is ABSENT from
-- it; a genuine NULL group is PRESENT with a null value.
SELECT
  CASE
    WHEN workclass IS NULL
     AND NOT EXISTS (SELECT 1 FROM UNNEST(segment) s WHERE s.dimension_col = 'workclass')
      THEN 'ALL WORKCLASSES (rollup)'
    WHEN workclass IS NULL THEN 'MISSING (was " ?")'
    ELSE workclass
  END                          AS workclass_label,
  ROUND(correlation, 4)        AS correlation,
  segment_size,
  ROUND(segment_proportion, 4) AS segment_proportion
FROM ML.CORRELATION(
  TABLE `PROJECT_ID.DATASET.exploration_census`,
  target_col => 'education_num',
  target_correlation_cols => ['hours_per_week'],
  dimension_cols => ['workclass'])
ORDER BY segment_size DESC;
-- Without the CASE, the rollup row and the missing-data row are two rows
-- both labelled NULL, adjacent in the output, with different meanings.


-- =============================================================================
-- Example 8: segment_size is not the n the correlation used
-- =============================================================================
WITH src AS (
  SELECT 1 AS t, 2.0  AS x, 10.0 AS y UNION ALL
  SELECT 2,       4.0,       20.0     UNION ALL
  SELECT 3,       6.0,       NULL     UNION ALL
  SELECT 4,       9.0,       40.0     UNION ALL
  SELECT 5,       NULL,      55.0
)
SELECT
  m.corr_col,
  m.correlation,
  m.segment_size,
  h.pairwise_n,
  h.pairwise_corr,
  ROUND(m.correlation - h.pairwise_corr, 15) AS diff_vs_pairwise
FROM ML.CORRELATION(TABLE src, target_col => 't', target_correlation_cols => ['x', 'y']) m
JOIN (
  SELECT 'x' AS corr_col, COUNTIF(x IS NOT NULL) AS pairwise_n, CORR(t, x) AS pairwise_corr FROM src
  UNION ALL
  SELECT 'y',             COUNTIF(y IS NOT NULL),               CORR(t, y)                  FROM src
) h USING (corr_col)
ORDER BY m.corr_col;
-- Verified: segment_size = 5 for both, pairwise_n = 4 for both, and the
-- correlations match CORR()'s pairwise answer. A segment_size filter is not
-- a sample-size filter.


-- =============================================================================
-- Example 9: the payoff -- the global correlation is nobody's correlation
-- =============================================================================
SELECT
  IFNULL(sex, 'ALL')            AS sex,
  IFNULL(marital_status, 'ALL') AS marital_status,
  ROUND(correlation, 4)         AS correlation,
  segment_size
FROM ML.CORRELATION(
  TABLE `PROJECT_ID.DATASET.exploration_census`,
  target_col => 'education_num',
  target_correlation_cols => ['hours_per_week'],
  dimension_cols => ['sex', 'marital_status'])
WHERE segment_size >= 500
ORDER BY correlation DESC;
-- Verified: the whole-table value (~0.1481) sits mid-table in a spread
-- running 0.0608 to 0.2721 across the 15 segments with 500+ rows, and is not
-- the answer for any group -- never-married respondents show the strongest
-- education/hours link, married ones the weakest. That is the entire
-- argument for dimension_cols.


-- =============================================================================
-- Cleanup
-- =============================================================================
-- Neither function creates a model or a connection, so the cleaned table is
-- the only object to remove.
-- DROP TABLE IF EXISTS `PROJECT_ID.DATASET.exploration_census`;
