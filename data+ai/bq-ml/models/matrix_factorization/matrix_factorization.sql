-- Matrix Factorization — Progressive SQL Examples (BigQuery ML)
-- =============================================================
-- Collaborative-filtering recommendation model with CREATE MODEL
-- (model_type = 'MATRIX_FACTORIZATION') -- factorizes a sparse
-- (user, item, rating) matrix into low-dimensional user and item latent
-- factor vectors, then scores/recommends the (mostly missing) pairs via
-- ML.RECOMMEND. Walks the full lifecycle: create -> evaluate ->
-- recommend -> inspect factors -> generate embeddings -> item-item
-- similarity via VECTOR_SEARCH -> introspect features/training -> tune.
--
-- PREREQUISITE, UNIQUE TO THIS MODEL TYPE IN THIS PROJECT: unlike every
-- other model type here, MATRIX_FACTORIZATION cannot train under
-- on-demand (per-byte) pricing -- it requires a BigQuery slot
-- reservation. The companion notebook creates a temporary autoscaling
-- reservation (BigQuery Editions, ENTERPRISE, no capacity commitment --
-- billed per-second only while actually used) before Example 1 and
-- deletes it in Cleanup. Running the examples below standalone requires
-- the same reservation to exist and be assigned to your project first.
-- Cost is real, not hypothetical: building and validating this file
-- consumed ~6.4 cumulative slot-hours of measured usage (base model +
-- tuning job + a BigFrames retrain) -- check current BigQuery Editions
-- pricing before running.
--
-- Data: bigquery-public-data.google_analytics_sample.ga_sessions_*
--       (Google Merchandise Store demo data, July 2017). IMPLICIT
--       feedback: (fullVisitorId, v2ProductName, view_count) where
--       view_count is a proxy signal (product-detail-page views), not
--       an explicit star rating. Aggregated to 42,178 users x 320 items
--       across ~1.3M interactions.
--
-- Full reference: ../../RESOURCES.md
-- Official docs:
--   CREATE MODEL (matrix factorization): https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-matrix-factorization
--   ML.RECOMMEND: https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-recommend
--   The CREATE MODEL statement: https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create


-- =============================================================================
-- Example 1: CREATE MODEL — train an IMPLICIT-feedback recommender
-- =============================================================================
-- feedback_type='IMPLICIT' fits here -- view_count is a behavioral proxy
-- signal, not an explicit 1-5 star rating (that would be
-- feedback_type='EXPLICIT', with a different set of ML.EVALUATE metrics
-- -- see RESOURCES.md). num_factors=16 is a deliberate, modest choice
-- for a 320-item catalog. There is no TRANSFORM clause for this model
-- type -- the training SELECT must produce exactly the user/item/rating
-- triple.
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.matrix_factorization_ga`
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


-- =============================================================================
-- Example 2: ML.EVALUATE — ranking-quality metrics (IMPLICIT)
-- =============================================================================
-- IMPLICIT feedback gets ranking-style metrics -- mean_average_precision
-- and normalized_discounted_cumulative_gain (both higher-is-better,
-- bounded [0,1]) plus mean_squared_error and average_rank. EXPLICIT
-- models get a different, regression-style metric set instead (see
-- RESOURCES.md) -- the two feedback types are not evaluated the same
-- way.
--
-- Verified: retraining this exact model (same name, same SQL) does not
-- reproduce mean_average_precision exactly -- one training run reached
-- 0.873, another reached 0.860. Matrix factorization's WALS training
-- shows measurable retraining variance, similar to models/kmeans/ and
-- RANDOM_FOREST_* elsewhere in this project, unlike PCA's full
-- determinism or the DNN family's bit-for-bit reproducibility under a
-- fixed name.
SELECT *
FROM ML.EVALUATE(MODEL `PROJECT_ID.DATASET.matrix_factorization_ga`);


-- =============================================================================
-- Example 3: ML.RECOMMEND — top items for one user
-- =============================================================================
-- Passing only the user column scores every item for that user.
--
-- GOTCHA (verified): calling this for a visitor_id NOT present in the
-- training data does NOT error -- it silently returns a full ranked
-- list. RESOURCES.md's general cold-start limitation note ("cannot
-- recommend for users or items absent from training data") describes
-- the intent, not the observed runtime behavior here: comparing the
-- output for a confirmed real trained user against an obviously fake
-- user ID shows completely different top-5 lists, consistent with the
-- fake user falling back to item-side bias/popularity alone rather than
-- genuine personalization (no user factor was ever learned for it).
-- Don't assume a non-empty ML.RECOMMEND result means the input user/item
-- actually existed in training.
SELECT visitor_id, product_name, predicted_view_count_confidence
FROM ML.RECOMMEND(
  MODEL `PROJECT_ID.DATASET.matrix_factorization_ga`,
  (SELECT '9790296909741758431' AS visitor_id)
)
ORDER BY predicted_view_count_confidence DESC
LIMIT 5;


-- =============================================================================
-- Example 4: ML.RECOMMEND — top users for one item
-- =============================================================================
-- Passing only the item column scores every user for that item -- the
-- symmetric counterpart to Example 3.
SELECT visitor_id, product_name, predicted_view_count_confidence
FROM ML.RECOMMEND(
  MODEL `PROJECT_ID.DATASET.matrix_factorization_ga`,
  (SELECT 'Google Youth Girl Hoodie' AS product_name)
)
ORDER BY predicted_view_count_confidence DESC
LIMIT 5;


-- =============================================================================
-- Example 5: ML.WEIGHTS — inspect the learned user/item factor vectors
-- =============================================================================
-- One row per user AND per item (distinguished by processed_input),
-- each with a factor_weights ARRAY<STRUCT<factor, weight>> (length =
-- num_factors) and an intercept (per-user/per-item bias term).
--
-- GOTCHA (verified): there is also exactly one extra row with
-- processed_input=NULL and feature='global__INTERCEPT__' -- the single
-- global bias term shared across the whole model, separate from every
-- user's/item's own intercept.
SELECT processed_input, COUNT(*) AS n
FROM ML.WEIGHTS(MODEL `PROJECT_ID.DATASET.matrix_factorization_ga`)
GROUP BY processed_input;


-- =============================================================================
-- Example 6: ML.GENERATE_EMBEDDING — factor vectors as embeddings
-- =============================================================================
-- GOTCHA (verified): for MATRIX_FACTORIZATION, ML.GENERATE_EMBEDDING
-- takes ONLY the model -- no input table/query argument at all. Passing
-- one errors immediately: "Function ML.GENERATE_EMBEDDING for
-- MATRIX_FACTORIZATION models only expects 1 argument but 2 were
-- passed." This is a genuinely different signature from PCA/AUTOENCODER
-- (both of which require a 2nd input-data argument) -- it returns
-- embeddings for EVERY user and item in the model in one call, mirroring
-- ML.WEIGHTS' processed_input/feature shape rather than ML.PREDICT's.
--
-- Second GOTCHA (verified): the embedding array has num_factors + 1
-- elements (17 here, not 16) -- one more than ML.WEIGHTS' factor_weights
-- array for the same model (confirmed 16 elements there, matching
-- num_factors exactly). The extra element is almost certainly the
-- per-user/per-item intercept appended onto the raw factor vector.
-- Don't assume the embedding array length always equals num_factors for
-- this model type.
SELECT processed_input, feature, ml_generate_embedding_result
FROM ML.GENERATE_EMBEDDING(MODEL `PROJECT_ID.DATASET.matrix_factorization_ga`)
LIMIT 5;


-- =============================================================================
-- Example 7: Item-item similarity with VECTOR_SEARCH
-- =============================================================================
-- Materialize the item embeddings (filtering Example 6's output to
-- processed_input='product_name') into a real table -- VECTOR_SEARCH
-- doesn't accept ML.GENERATE_EMBEDDING output directly as its base-table
-- argument, same limitation already verified in models/autoencoder/.
CREATE OR REPLACE TABLE `PROJECT_ID.DATASET.matrix_factorization_item_embeddings` AS
SELECT feature AS product_name, ml_generate_embedding_result AS embedding
FROM ML.GENERATE_EMBEDDING(MODEL `PROJECT_ID.DATASET.matrix_factorization_ga`)
WHERE processed_input = 'product_name';

-- Verified: querying "Google Youth Girl Hoodie" surfaces other youth
-- apparel (youth tees, youth t-shirts) as its nearest neighbors --
-- the learned item factors capture real product-category structure,
-- not just noise.
SELECT query.product_name AS query_product, base.product_name AS similar_product, distance
FROM VECTOR_SEARCH(
  TABLE `PROJECT_ID.DATASET.matrix_factorization_item_embeddings`, 'embedding',
  (SELECT product_name, embedding
   FROM `PROJECT_ID.DATASET.matrix_factorization_item_embeddings`
   WHERE product_name = 'Google Youth Girl Hoodie'),
  top_k => 6,
  distance_type => 'COSINE'
)
ORDER BY distance;


-- =============================================================================
-- Example 8: ML.FEATURE_INFO — introspect the training columns
-- =============================================================================
SELECT *
FROM ML.FEATURE_INFO(MODEL `PROJECT_ID.DATASET.matrix_factorization_ga`);


-- =============================================================================
-- Example 9: ML.TRAINING_INFO — iteration-level loss curve
-- =============================================================================
-- eval_loss is NULL throughout for this model -- unlike the supervised
-- model types in this project, MATRIX_FACTORIZATION's ML.TRAINING_INFO
-- does not populate a held-out eval_loss column here.
SELECT *
FROM ML.TRAINING_INFO(MODEL `PROJECT_ID.DATASET.matrix_factorization_ga`);


-- =============================================================================
-- Example 10: Hyperparameter tuning — NUM_TRIALS + HPARAM_RANGE
-- =============================================================================
-- Tunes num_factors, l2_reg, and wals_alpha (IMPLICIT-only) together,
-- maximizing mean_average_precision (the IMPLICIT default objective).
--
-- Verified: tuning improved on Example 2's baseline in every run tested,
-- though the exact numbers vary retrain to retrain (see Example 2) --
-- one run's best trial (num_factors=26, l2_reg=2.88, wals_alpha=49.2)
-- reached mean_average_precision=0.899 against that run's 0.860
-- baseline; a separate run's best trial (same num_factors/l2_reg,
-- wals_alpha=30.8 instead) reached 0.915 against a 0.873 baseline. The
-- qualitative result -- tuning beats the untuned baseline -- held both
-- times. Contrast with models/autoencoder/, where an equally-sized
-- 4-trial search failed to beat its untuned baseline at all.
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.matrix_factorization_ga_tuned`
OPTIONS(
  model_type = 'MATRIX_FACTORIZATION',
  feedback_type = 'IMPLICIT',
  user_col = 'visitor_id',
  item_col = 'product_name',
  rating_col = 'view_count',
  num_factors = HPARAM_RANGE(8, 32),
  l2_reg = HPARAM_RANGE(0.1, 10.0),
  wals_alpha = HPARAM_RANGE(20.0, 60.0),
  num_trials = 4,
  max_parallel_trials = 2
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

SELECT
  trial_id,
  hyperparameters,
  hparam_tuning_evaluation_metrics.mean_average_precision AS mean_average_precision,
  is_optimal
FROM ML.TRIAL_INFO(MODEL `PROJECT_ID.DATASET.matrix_factorization_ga_tuned`)
ORDER BY mean_average_precision DESC;

-- Calling ML.EVALUATE on a tuned model with no arguments returns every
-- trial's metrics in one result (one row per trial_id) -- there is no
-- STRUCT(trial_id) 2-argument form for ML.EVALUATE the way ML.RECOMMEND
-- and ML.PREDICT accept one; passing a STRUCT as a 2nd argument errors
-- ("argument 2 must be a relation").
SELECT *
FROM ML.EVALUATE(MODEL `PROJECT_ID.DATASET.matrix_factorization_ga_tuned`);


-- =============================================================================
-- Cleanup
-- =============================================================================
-- DROP MODEL IF EXISTS `PROJECT_ID.DATASET.matrix_factorization_ga`;
-- DROP MODEL IF EXISTS `PROJECT_ID.DATASET.matrix_factorization_ga_tuned`;
-- DROP TABLE IF EXISTS `PROJECT_ID.DATASET.matrix_factorization_item_embeddings`;
-- Also delete the temporary reservation/assignment -- see the companion
-- notebook's Cleanup section.
