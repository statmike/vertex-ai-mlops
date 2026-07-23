-- Encoding — Progressive SQL Examples (BigQuery ML model-free functions)
-- =============================================================
-- Three categorical-encoding functions, all analytic (require OVER()):
-- ML.ONE_HOT_ENCODER (scalar STRING -> sparse one-hot/dummy vector),
-- ML.LABEL_ENCODER (scalar STRING -> ordinal INT64), and
-- ML.MULTI_HOT_ENCODER (ARRAY<STRING> -> sparse multi-hot vector).
--
-- Data: bigquery-public-data.ml_datasets.penguins (same dataset as
--       ../scalers/, ../feature_engineering/, models/transform_only/)
--
-- Full reference: ../../RESOURCES.md
-- Official docs:
--   ML.ONE_HOT_ENCODER:   https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-one-hot-encoder
--   ML.MULTI_HOT_ENCODER: https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-multi-hot-encoder
--   ML.LABEL_ENCODER:     https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-label-encoder


-- =============================================================================
-- Example 1: ML.ONE_HOT_ENCODER -- default, dummy (drop='most_frequent'), top_k, frequency_threshold
-- =============================================================================
SELECT DISTINCT x,
  ML.ONE_HOT_ENCODER(x) OVER() AS onehot_default,
  ML.ONE_HOT_ENCODER(x, 'most_frequent') OVER() AS onehot_dummy,
  ML.ONE_HOT_ENCODER(x, 'none', 32000, 0) OVER() AS onehot_no_threshold
FROM UNNEST(['a','a','a','a','a','a', 'b','b','b','b','b','b','b', 'c','c','c']) AS x
ORDER BY x;


-- =============================================================================
-- Example 2: MAJOR GOTCHA -- the current default frequency_threshold=5 silently
-- drops any category appearing fewer than 5 times, verified live
-- =============================================================================
-- Older repo notebooks cite default top_k=1,000,000 / frequency_threshold=0
-- (no threshold at all). Current docs specify top_k=32,000 / frequency_threshold=5.
-- This is NOT just a documentation footnote -- it changes real output. With
-- 'a' appearing 6x, 'b' appearing 7x, 'c' appearing only 3x:
SELECT DISTINCT x,
  ML.ONE_HOT_ENCODER(x) OVER() AS current_default_freq5,        -- 'c' (3x, <5) silently drops to index 0
  ML.ONE_HOT_ENCODER(x, 'none', 32000, 0) OVER() AS legacy_style_freq0  -- 'c' keeps its own index
FROM UNNEST(['a','a','a','a','a','a', 'b','b','b','b','b','b','b', 'c','c','c']) AS x
ORDER BY x;
-- Verified: under the CURRENT default, 'c' collapses into bucket 0 --
-- indistinguishable from NULL/unseen-at-predict. On any real dataset with a
-- rare-but-meaningful category (<5 occurrences), the current default silently
-- discards it unless you explicitly pass frequency_threshold=0 or lower.


-- =============================================================================
-- Example 3: ML.LABEL_ENCODER and ML.MULTI_HOT_ENCODER, on real penguin columns
-- =============================================================================
-- island has plenty of rows per category (Biscoe/Dream/Torgersen), so none
-- get dropped by the default frequency_threshold=5 -- unlike Example 2's
-- tiny synthetic categories.
SELECT DISTINCT island,
  ML.ONE_HOT_ENCODER(island) OVER() AS island_onehot,
  ML.LABEL_ENCODER(island) OVER() AS island_label
FROM `bigquery-public-data.ml_datasets.penguins`
ORDER BY island;

-- ML.MULTI_HOT_ENCODER on an ARRAY<STRING> column -- one feature per unique
-- element across all rows, not per row.
SELECT arr, ML.MULTI_HOT_ENCODER(arr, 100, 0) OVER() AS multi_hot
FROM UNNEST([
  STRUCT(['tag_a', 'tag_b'] AS arr),
  STRUCT(['tag_b', 'tag_c'] AS arr),
  STRUCT(['tag_a'] AS arr)
]);


-- =============================================================================
-- Example 4: Embedded in a real CREATE MODEL TRANSFORM
-- =============================================================================
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.encoding_downstream_logistic_regression`
TRANSFORM(
  species,
  ML.ONE_HOT_ENCODER(island) OVER() AS island_encoded,
  ML.LABEL_ENCODER(sex) OVER() AS sex_encoded
)
OPTIONS(model_type = 'LOGISTIC_REG', input_label_cols = ['species']) AS
SELECT species, island, sex
FROM `bigquery-public-data.ml_datasets.penguins`;

-- Verified accuracy ~0.71 (island+sex alone are modestly predictive of
-- species -- not the point here; the point is both encoders' vocabularies
-- travel with the model and auto-apply at ML.PREDICT).
SELECT * FROM ML.EVALUATE(MODEL `PROJECT_ID.DATASET.encoding_downstream_logistic_regression`);


-- =============================================================================
-- Cleanup
-- =============================================================================
-- DROP MODEL IF EXISTS `PROJECT_ID.DATASET.encoding_downstream_logistic_regression`;
