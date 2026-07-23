-- Bucketizing — Progressive SQL Examples (BigQuery ML model-free functions)
-- =============================================================
-- Three functions that convert a continuous/string value into a discrete
-- bucket: ML.BUCKETIZE (manual split points, scalar), ML.QUANTILE_BUCKETIZE
-- (equal-frequency bins, analytic -- requires OVER()), and ML.HASH_BUCKETIZE
-- (deterministic string hashing into N buckets, scalar). All three are
-- exportable when used inside a CREATE MODEL TRANSFORM clause.
--
-- Data: bigquery-public-data.ml_datasets.penguins (same dataset as
--       ../scalers/, ../feature_engineering/, ../encoding/)
--
-- Full reference: ../../RESOURCES.md
-- Official docs:
--   ML.BUCKETIZE:          https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-bucketize
--   ML.QUANTILE_BUCKETIZE: https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-quantile-bucketize
--   ML.HASH_BUCKETIZE:     https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-hash-bucketize


-- =============================================================================
-- Example 1: ML.BUCKETIZE -- manual split points, 3 output formats
-- =============================================================================
SELECT
  body_mass_g,
  ML.BUCKETIZE(body_mass_g, [3000, 4000, 5000]) AS bucket_names,
  ML.BUCKETIZE(body_mass_g, [3000, 4000, 5000], FALSE, 'bucket_ranges') AS bucket_ranges,
  ML.BUCKETIZE(body_mass_g, [3000, 4000, 5000], FALSE, 'bucket_ranges_json') AS bucket_ranges_json
FROM `bigquery-public-data.ml_datasets.penguins`
WHERE body_mass_g IS NOT NULL
ORDER BY body_mass_g
LIMIT 5;


-- =============================================================================
-- Example 2: GOTCHA -- what exclude_boundaries=TRUE actually does (verified live)
-- =============================================================================
-- RESOURCES.md's docs-derived description says exclude_boundaries "drops the
-- implicit lower (-inf) and upper (+inf) overflow buckets so only interior
-- bins remain." That phrasing is easy to misread as "out-of-range values
-- become NULL." Verified live: they do NOT become NULL -- instead, the
-- OUTERMOST split points are effectively dropped, merging the overflow
-- bucket into its nearest interior neighbor. With split points [10, 20, 30]:
--   Default (4 bins):  (-inf,10)  [10,20)  [20,30)  [30,+inf)
--   Excluded (2 bins):    (-inf,20)          [20,+inf)
-- i.e. the first and last split points (10 and 30) disappear entirely,
-- leaving only the middle one (20) -- NOT "values outside [10,30] become NULL."
SELECT
  x,
  ML.BUCKETIZE(x, [10, 20, 30], FALSE, 'bucket_ranges') AS default_ranges,
  ML.BUCKETIZE(x, [10, 20, 30], TRUE, 'bucket_ranges') AS excluded_ranges
FROM UNNEST([0.0, 10.0, 15.0, 20.0, 25.0, 30.0, 40.0]) AS x;


-- =============================================================================
-- Example 3: ML.QUANTILE_BUCKETIZE -- equal-frequency bins (analytic, needs OVER())
-- =============================================================================
SELECT
  culmen_length_mm,
  ML.QUANTILE_BUCKETIZE(culmen_length_mm, 4) OVER() AS quantile_bucket,
  ML.QUANTILE_BUCKETIZE(culmen_length_mm, 4, 'bucket_ranges') OVER() AS quantile_ranges
FROM `bigquery-public-data.ml_datasets.penguins`
WHERE culmen_length_mm IS NOT NULL
ORDER BY culmen_length_mm
LIMIT 5;


-- =============================================================================
-- Example 4: ML.HASH_BUCKETIZE -- deterministic string hashing (scalar)
-- =============================================================================
SELECT DISTINCT island,
  ML.HASH_BUCKETIZE(island, 0) AS raw_hash,   -- hash_bucket_size=0 -> hash only, no modulo
  ML.HASH_BUCKETIZE(island, 3) AS bucket_mod3 -- modulo into 3 buckets
FROM `bigquery-public-data.ml_datasets.penguins`
ORDER BY island;


-- =============================================================================
-- Example 5: Embedded in a real CREATE MODEL TRANSFORM
-- =============================================================================
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.bucketizing_downstream_logistic_regression`
TRANSFORM(
  species,
  ML.QUANTILE_BUCKETIZE(body_mass_g, 4) OVER() AS body_mass_bucket,
  ML.HASH_BUCKETIZE(island, 10) AS island_hashed
)
OPTIONS(model_type = 'LOGISTIC_REG', input_label_cols = ['species']) AS
SELECT species, body_mass_g, island
FROM `bigquery-public-data.ml_datasets.penguins`
WHERE body_mass_g IS NOT NULL;

-- Verified accuracy ~0.81 -- BQML auto-encodes the STRING bucket labels and
-- INT64 hash buckets like any other categorical/numeric feature.
SELECT * FROM ML.EVALUATE(MODEL `PROJECT_ID.DATASET.bucketizing_downstream_logistic_regression`);


-- =============================================================================
-- Cleanup
-- =============================================================================
-- DROP MODEL IF EXISTS `PROJECT_ID.DATASET.bucketizing_downstream_logistic_regression`;
