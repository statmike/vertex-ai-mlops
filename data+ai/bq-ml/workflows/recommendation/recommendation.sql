-- Recommendation — BigQuery ML Workflow
-- =============================================================
-- Extends models/matrix_factorization/'s algorithm demo into a full
-- workflow: a non-personalized popularity baseline (to quantify what
-- personalization actually buys you), batch top-N generation for many
-- users at once (the real production pattern), and an empirical deep-dive
-- into cold-start behavior.
--
-- COST NOTE: MATRIX_FACTORIZATION requires a slot reservation to train --
-- same real-dollar-cost Enterprise autoscale reservation already used in
-- models/matrix_factorization/ (0 baseline slots, autoscale to 100, billed
-- per-second only while queries run, no capacity commitment).
--
-- Data: bigquery-public-data.google_analytics_sample.ga_sessions_* (July
--       2017) -- same IMPLICIT-feedback setup as models/matrix_factorization/,
--       for direct comparability.
--
-- Full reference: ../../RESOURCES.md
-- Official docs:
--   CREATE MODEL (MATRIX_FACTORIZATION): https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-matrix-factorization
--   ML.RECOMMEND: https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-recommend


-- =============================================================================
-- Step 1: Train MATRIX_FACTORIZATION (identical setup to models/matrix_factorization/,
-- for a fair, directly comparable baseline)
-- =============================================================================
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.recommendation_mf`
OPTIONS(
  model_type = 'MATRIX_FACTORIZATION',
  feedback_type = 'IMPLICIT',
  user_col = 'visitor_id',
  item_col = 'product_name',
  rating_col = 'view_count',
  num_factors = 16
) AS
SELECT
  fullVisitorId AS visitor_id,
  product.v2ProductName AS product_name,
  COUNT(*) AS view_count
FROM `bigquery-public-data.google_analytics_sample.ga_sessions_*`,
UNNEST(hits) AS hits,
UNNEST(hits.product) AS product
WHERE _TABLE_SUFFIX BETWEEN '20170701' AND '20170801'
  AND product.v2ProductName IS NOT NULL AND product.v2ProductName != '(not set)'
GROUP BY visitor_id, product_name;

SELECT * FROM ML.EVALUATE(MODEL `PROJECT_ID.DATASET.recommendation_mf`);
-- Verified: mean_average_precision ~0.86 -- consistent with
-- models/matrix_factorization/'s untuned baseline (retraining is
-- non-deterministic, see that notebook's verified note).


-- =============================================================================
-- Step 2: Non-personalized popularity baseline -- what "no ML" looks like
-- =============================================================================
CREATE OR REPLACE TABLE `PROJECT_ID.DATASET.recommendation_popularity` AS
SELECT
  product.v2ProductName AS product_name,
  COUNT(*) AS total_views
FROM `bigquery-public-data.google_analytics_sample.ga_sessions_*`,
UNNEST(hits) AS hits,
UNNEST(hits.product) AS product
WHERE _TABLE_SUFFIX BETWEEN '20170701' AND '20170801'
  AND product.v2ProductName IS NOT NULL AND product.v2ProductName != '(not set)'
GROUP BY product_name
ORDER BY total_views DESC;


-- =============================================================================
-- Step 3: Batch top-N generation for many users at once (the real production
-- pattern -- models/matrix_factorization/ only demos one user/one item at a time)
-- =============================================================================
SELECT visitor_id, product_name, predicted_view_count_confidence, rank
FROM (
  SELECT
    visitor_id, product_name, predicted_view_count_confidence,
    ROW_NUMBER() OVER (PARTITION BY visitor_id ORDER BY predicted_view_count_confidence DESC) AS rank
  FROM ML.RECOMMEND(
    MODEL `PROJECT_ID.DATASET.recommendation_mf`,
    (SELECT DISTINCT fullVisitorId AS visitor_id
     FROM `bigquery-public-data.google_analytics_sample.ga_sessions_*`
     WHERE _TABLE_SUFFIX BETWEEN '20170701' AND '20170801'
     LIMIT 5)
  )
)
WHERE rank <= 5
ORDER BY visitor_id, rank;


-- =============================================================================
-- Step 4: Does personalization actually differ from popularity? (quantified)
-- =============================================================================
WITH personalized AS (
  SELECT product_name
  FROM ML.RECOMMEND(
    MODEL `PROJECT_ID.DATASET.recommendation_mf`,
    (SELECT '7953155863181185949' AS visitor_id)   -- a real visitor_id from the training data
  )
  ORDER BY predicted_view_count_confidence DESC
  LIMIT 10
),
popularity AS (
  SELECT product_name FROM `PROJECT_ID.DATASET.recommendation_popularity` LIMIT 10
)
SELECT COUNT(*) AS overlap_count
FROM personalized JOIN popularity USING (product_name);
-- Verified: 0/10 overlap for this user -- this user's personalized top-10
-- shares NOTHING with the global top-10 most-viewed products. Strong
-- evidence personalization is doing real, distinct work, not just
-- reproducing what's already popular.


-- =============================================================================
-- Step 5: Cold-start deep dive -- what actually happens for an absent user?
-- =============================================================================
-- GOTCHA (verified, extends models/matrix_factorization/'s note): calling
-- ML.RECOMMEND for a visitor_id NOT in training does not error -- it
-- silently returns a ranking. Proving this ranking is NOT personalized:
-- two different absent visitor_ids get the IDENTICAL top-5 list.
SELECT '__cold_user_a__' AS probe, product_name, predicted_view_count_confidence
FROM ML.RECOMMEND(MODEL `PROJECT_ID.DATASET.recommendation_mf`, (SELECT '__cold_user_a__' AS visitor_id))
ORDER BY predicted_view_count_confidence DESC LIMIT 5;

SELECT '__cold_user_b__' AS probe, product_name, predicted_view_count_confidence
FROM ML.RECOMMEND(MODEL `PROJECT_ID.DATASET.recommendation_mf`, (SELECT '__cold_user_b__' AS visitor_id))
ORDER BY predicted_view_count_confidence DESC LIMIT 5;
-- Verified: identical product_name lists in identical order for both
-- probes -- confirming the "recommendation" for an absent user is really
-- just the model's global item-bias ranking, not personalization.

-- How does that fallback ranking compare to the popularity baseline?
WITH cold AS (
  SELECT product_name
  FROM ML.RECOMMEND(MODEL `PROJECT_ID.DATASET.recommendation_mf`, (SELECT '__cold_user_a__' AS visitor_id))
  ORDER BY predicted_view_count_confidence DESC LIMIT 10
),
popularity AS (
  SELECT product_name FROM `PROJECT_ID.DATASET.recommendation_popularity` LIMIT 10
)
SELECT COUNT(*) AS overlap_count
FROM cold JOIN popularity USING (product_name);
-- Verified: substantial overlap across independent runs (6/10 and 9/10 --
-- MATRIX_FACTORIZATION retraining is non-deterministic, see
-- models/matrix_factorization/) -- MATRIX_FACTORIZATION's own built-in
-- fallback for absent users already closely approximates the popularity
-- baseline. Practical implication: for truly new users, you likely don't
-- need a separate cold-start/popularity system bolted on -- ML.RECOMMEND's
-- default behavior for an absent visitor_id already does something very
-- close to that automatically.


-- =============================================================================
-- Cleanup
-- =============================================================================
-- DROP MODEL IF EXISTS `PROJECT_ID.DATASET.recommendation_mf`;
-- DROP TABLE IF EXISTS `PROJECT_ID.DATASET.recommendation_popularity`;
-- (then delete the temporary reservation + assignment, see notebook)
