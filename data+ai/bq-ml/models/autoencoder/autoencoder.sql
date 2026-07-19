-- Autoencoder — Progressive SQL Examples (BigQuery ML)
-- =============================================================
-- Unsupervised nonlinear dimensionality reduction with CREATE MODEL
-- (model_type = 'AUTOENCODER') -- a symmetric feed-forward network that
-- compresses rows into a small latent space and reconstructs them; the
-- middle hidden_units value is the latent dimension. No label column.
-- Walks the full model lifecycle: create -> evaluate -> diagnose a real
-- training failure -> fix -> predict -> visualize -> reconstruction loss
-- -> detect anomalies -> generate embeddings -> preprocess -> tune.
--
-- Data: bigquery-public-data.ml_datasets.penguins
--       No label -- same 4 numeric measurements as models/kmeans/ and
--       models/pca/ (culmen_length_mm, culmen_depth_mm,
--       flipper_length_mm, body_mass_g). species/island/sex are NOT
--       training features; species is carried through ML.PREDICT
--       afterward as an external check, same convention as the other
--       two unsupervised notebooks. 342 of 344 rows remain after
--       filtering body_mass_g IS NOT NULL.
--
-- Full reference: ../../RESOURCES.md
-- Official docs:
--   CREATE MODEL (autoencoder): https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-autoencoder
--   ML.RECONSTRUCTION_LOSS: https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-reconstruction-loss
--   The CREATE MODEL statement: https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create


-- =============================================================================
-- Example 1: CREATE MODEL — the naive attempt (RELU, the default activation)
-- =============================================================================
-- hidden_units=[3,2,3] gives a 2-dimensional latent space (the middle
-- value) -- small on purpose, for a direct visual comparison with
-- models/pca/'s 2-component projection on the same 4 features.
-- activation_fn='RELU' is BigQuery ML's own default.
--
-- GOTCHA (verified across three independent retrains): with RELU on this
-- small, narrow network, a substantial and highly variable share of
-- rows have BOTH latent dimensions simultaneously pinned to exactly 0.0
-- -- a classic dying-ReLU symptom: once a ReLU unit's input goes
-- negative across most of the dataset, its gradient is zero there and
-- it can't recover during training. The severity varies widely by
-- retrain (see Example 11) -- observed n_both_zero/n_total rates so
-- far: 40%, 50%, and 65%. Sometimes one entire latent column is pinned
-- to 0.0 for every single row; other times the zeros spread unevenly
-- across both columns instead -- but the underlying dying-ReLU symptom
-- itself shows up every time. The aggregate ML.EVALUATE
-- metrics still look like "a model trained" (they don't error or come
-- back NULL) -- this failure is only visible by directly inspecting
-- ML.PREDICT's latent_col_* output, not from ML.EVALUATE alone. See
-- Example 2's aggregate numbers, which look plausible in isolation.
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.autoencoder_penguins`
OPTIONS(
  model_type = 'AUTOENCODER',
  hidden_units = [3, 2, 3],
  activation_fn = 'RELU',
  learn_rate = 0.01,
  max_iterations = 30
) AS
SELECT culmen_length_mm, culmen_depth_mm, flipper_length_mm, body_mass_g
FROM `bigquery-public-data.ml_datasets.penguins`
WHERE body_mass_g IS NOT NULL;


-- =============================================================================
-- Example 2: ML.EVALUATE — the metrics alone don't reveal the collapse
-- =============================================================================
-- mean_absolute_error / mean_squared_error / mean_squared_log_error are
-- reconstruction-error metrics (no label). These numbers alone look
-- like a model that trained normally -- the dead-latent-unit problem
-- from Example 1 is invisible here; you have to check ML.PREDICT's
-- actual latent_col_* values to catch it (Example 3).
SELECT *
FROM ML.EVALUATE(MODEL `PROJECT_ID.DATASET.autoencoder_penguins`);


-- =============================================================================
-- Example 3: ML.PREDICT — diagnose the dead latent unit directly
-- =============================================================================
-- Aggregate min/max/zero-count across all rows exposes the collapse
-- directly -- run this against your own trained model and compare the
-- shape of the result to Example 11's discussion of run-to-run variance.
SELECT
  MIN(latent_col_1) AS min_l1, MAX(latent_col_1) AS max_l1,
  MIN(latent_col_2) AS min_l2, MAX(latent_col_2) AS max_l2,
  COUNTIF(latent_col_1 = 0.0 AND latent_col_2 = 0.0) AS n_both_zero,
  COUNT(*) AS n_total
FROM ML.PREDICT(
  MODEL `PROJECT_ID.DATASET.autoencoder_penguins`,
  (SELECT culmen_length_mm, culmen_depth_mm, flipper_length_mm, body_mass_g
   FROM `bigquery-public-data.ml_datasets.penguins`
   WHERE body_mass_g IS NOT NULL)
);


-- =============================================================================
-- Example 4: CREATE MODEL — the fix (TANH activation)
-- =============================================================================
-- Same architecture, only activation_fn changes: RELU -> TANH. TANH has
-- no "dead zone" -- its gradient is nonzero everywhere except at its
-- (rare, exact) saturation points -- so it can't collapse the same way.
--
-- Verified: this single change fixes both problems at once. No
-- dead latent units (both latent_col_1 and latent_col_2 take a full
-- range of nonzero values across all 342 rows), AND reconstruction
-- quality improves substantially and consistently: mean_squared_error
-- lands around ~0.21 with TANH every time this has been tested, well
-- below the RELU baseline from Example 2 (observed anywhere from ~0.66
-- to ~0.94 across different retrains, itself a symptom of the
-- collapse's variable severity -- see Example 11). The exact
-- improvement ratio isn't fixed since it depends on how badly RELU
-- happened to collapse on a given retrain, but the direction and the
-- ~0.21 landing point for TANH are consistent.
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.autoencoder_penguins_fix`
OPTIONS(
  model_type = 'AUTOENCODER',
  hidden_units = [3, 2, 3],
  activation_fn = 'TANH',
  learn_rate = 0.01,
  max_iterations = 30
) AS
SELECT culmen_length_mm, culmen_depth_mm, flipper_length_mm, body_mass_g
FROM `bigquery-public-data.ml_datasets.penguins`
WHERE body_mass_g IS NOT NULL;

SELECT *
FROM ML.EVALUATE(MODEL `PROJECT_ID.DATASET.autoencoder_penguins_fix`);


-- =============================================================================
-- Example 5: ML.PREDICT — the latent space, with species as an external check
-- =============================================================================
-- Returns latent_col_1/latent_col_2 (the 2D bottleneck) alongside the
-- reconstructed input columns. species is passed through untouched (it
-- was never a training feature) purely as an external validation check,
-- same convention as models/kmeans/ and models/pca/.
SELECT species, latent_col_1, latent_col_2
FROM ML.PREDICT(
  MODEL `PROJECT_ID.DATASET.autoencoder_penguins_fix`,
  (SELECT species, culmen_length_mm, culmen_depth_mm, flipper_length_mm, body_mass_g
   FROM `bigquery-public-data.ml_datasets.penguins`
   WHERE body_mass_g IS NOT NULL)
);


-- =============================================================================
-- Example 6: ML.RECONSTRUCTION_LOSS — per-row reconstruction diagnostics
-- =============================================================================
-- Same three metrics as ML.EVALUATE, but per input row -- use this to
-- find the specific rows the model reconstructs worst (a manual,
-- row-level view of the same signal ML.DETECT_ANOMALIES automates in
-- Example 8).
SELECT *
FROM ML.RECONSTRUCTION_LOSS(
  MODEL `PROJECT_ID.DATASET.autoencoder_penguins_fix`,
  (SELECT culmen_length_mm, culmen_depth_mm, flipper_length_mm, body_mass_g
   FROM `bigquery-public-data.ml_datasets.penguins`
   WHERE body_mass_g IS NOT NULL)
)
ORDER BY mean_squared_error DESC
LIMIT 10;


-- =============================================================================
-- Example 7: ML.FEATURE_INFO — introspect the training features
-- =============================================================================
SELECT *
FROM ML.FEATURE_INFO(MODEL `PROJECT_ID.DATASET.autoencoder_penguins_fix`);


-- =============================================================================
-- Example 8: ML.DETECT_ANOMALIES — reconstruction-based outlier detection
-- =============================================================================
-- GOTCHA (verified, same as models/kmeans/ and models/pca/): the
-- input-data argument is REQUIRED for AUTOENCODER too -- calling this
-- with only (MODEL, STRUCT(contamination)) errors immediately:
-- "DETECT_ANOMALIES expects 3 arguments for AUTOENCODER models but 2
-- were passed." All three unsupervised model types in this project
-- share this requirement.
--
-- contamination=0.05 flags the 5% of rows with the largest
-- reconstruction error (mean_squared_error) as anomalies.
SELECT *
FROM ML.DETECT_ANOMALIES(
  MODEL `PROJECT_ID.DATASET.autoencoder_penguins_fix`,
  STRUCT(0.05 AS contamination),
  (SELECT culmen_length_mm, culmen_depth_mm, flipper_length_mm, body_mass_g
   FROM `bigquery-public-data.ml_datasets.penguins`
   WHERE body_mass_g IS NOT NULL)
)
WHERE is_anomaly
ORDER BY mean_squared_error DESC;


-- =============================================================================
-- Example 9: ML.GENERATE_EMBEDDING — package the latent space as a single array
-- =============================================================================
-- Wraps the same latent_col_1/latent_col_2 values from Example 5 into a
-- single ml_generate_embedding_result ARRAY<FLOAT> column -- purpose-built
-- for VECTOR_SEARCH. Verified: the array values match ML.PREDICT's
-- latent_col_1/latent_col_2 columns exactly, in order.
SELECT species, ml_generate_embedding_result
FROM ML.GENERATE_EMBEDDING(
  MODEL `PROJECT_ID.DATASET.autoencoder_penguins_fix`,
  (SELECT species, culmen_length_mm, culmen_depth_mm, flipper_length_mm, body_mass_g
   FROM `bigquery-public-data.ml_datasets.penguins`
   WHERE body_mass_g IS NOT NULL LIMIT 5)
);


-- =============================================================================
-- Example 10: manual ML.NORMALIZER vs. ML.GENERATE_EMBEDDING, then VECTOR_SEARCH
-- =============================================================================
-- Two ways to get an embedding, compared directly:
--   (a) Manual: ML.PREDICT -> wrap latent_col_1/latent_col_2 into an ARRAY
--       yourself -> ML.NORMALIZER(..., 2) to give it unit (L2) norm.
--   (b) Automated: ML.GENERATE_EMBEDDING -> ml_generate_embedding_result,
--       already an ARRAY, no manual column-wrangling needed.
--
-- GOTCHA (verified): ML.GENERATE_EMBEDDING does NOT normalize its output --
-- its raw ml_generate_embedding_result is bit-for-bit identical to
-- ML.PREDICT's un-normalized latent_col_1/latent_col_2 (already shown in
-- Example 9). Applying ML.NORMALIZER to (a)'s manual array and to (b)'s
-- raw array independently produces the exact same normalized vector --
-- confirmed row-by-row below. So ML.GENERATE_EMBEDDING's real convenience
-- is NOT built-in normalization (there isn't any) -- it's simply not
-- having to enumerate latent_col_1..N into an ARRAY literal yourself,
-- which matters more as the latent dimension grows.
WITH base AS (
  SELECT species, culmen_length_mm, culmen_depth_mm, flipper_length_mm, body_mass_g,
    ROW_NUMBER() OVER() AS row_id
  FROM `bigquery-public-data.ml_datasets.penguins`
  WHERE body_mass_g IS NOT NULL
  LIMIT 5
),
manual AS (
  SELECT row_id, ML.NORMALIZER([latent_col_1, latent_col_2]) AS embedding_manual
  FROM ML.PREDICT(MODEL `PROJECT_ID.DATASET.autoencoder_penguins_fix`, TABLE base)
),
auto AS (
  SELECT row_id, ml_generate_embedding_result AS embedding_auto_raw,
    ML.NORMALIZER(ml_generate_embedding_result) AS embedding_auto_normalized
  FROM ML.GENERATE_EMBEDDING(MODEL `PROJECT_ID.DATASET.autoencoder_penguins_fix`, TABLE base)
)
SELECT m.row_id, m.embedding_manual, a.embedding_auto_raw, a.embedding_auto_normalized
FROM manual m JOIN auto a USING (row_id)
ORDER BY row_id;

-- VECTOR_SEARCH does not accept ML.PREDICT/ML.GENERATE_EMBEDDING output
-- directly as its base-table argument ("Unsupported query pattern") --
-- materialize the embeddings into a real table first.
CREATE OR REPLACE TABLE `PROJECT_ID.DATASET.autoencoder_embeddings` AS
SELECT species, ml_generate_embedding_result AS embedding_raw,
  ML.NORMALIZER(ml_generate_embedding_result) AS embedding_normalized
FROM ML.GENERATE_EMBEDDING(
  MODEL `PROJECT_ID.DATASET.autoencoder_penguins_fix`,
  (SELECT species, culmen_length_mm, culmen_depth_mm, flipper_length_mm, body_mass_g
   FROM `bigquery-public-data.ml_datasets.penguins`
   WHERE body_mass_g IS NOT NULL)
);

-- GOTCHA (verified): normalized-embedding + DOT_PRODUCT and
-- raw-embedding + COSINE produce mathematically equivalent results --
-- COSINE distance = 1 - cosine_similarity, DOT_PRODUCT distance (on unit
-- vectors) = -cosine_similarity, and the two queries below return
-- identical rankings with distances that convert exactly between the two
-- formulas. Practical implication: ML.NORMALIZER is unnecessary for
-- VECTOR_SEARCH specifically -- use distance_type='COSINE' directly on
-- ML.GENERATE_EMBEDDING's raw output and skip the normalization step
-- entirely, unless you need normalized vectors for something else.
SELECT query.species AS query_species, base.species AS neighbor_species, distance
FROM VECTOR_SEARCH(
  TABLE `PROJECT_ID.DATASET.autoencoder_embeddings`, 'embedding_normalized',
  (SELECT species, embedding_normalized FROM `PROJECT_ID.DATASET.autoencoder_embeddings` LIMIT 1),
  top_k => 5,
  distance_type => 'DOT_PRODUCT'
)
ORDER BY distance;

SELECT query.species AS query_species, base.species AS neighbor_species, distance
FROM VECTOR_SEARCH(
  TABLE `PROJECT_ID.DATASET.autoencoder_embeddings`, 'embedding_raw',
  (SELECT species, embedding_raw FROM `PROJECT_ID.DATASET.autoencoder_embeddings` LIMIT 1),
  top_k => 5,
  distance_type => 'COSINE'
)
ORDER BY distance;


-- =============================================================================
-- Example 11: retraining reproduces ML.EVALUATE exactly, but NOT the latent space
-- =============================================================================
-- GOTCHA (verified): retraining Example 1's exact RELU model (same
-- name, same SQL) reproduces ML.EVALUATE's mean_absolute_error /
-- mean_squared_error / mean_squared_log_error bit-for-bit -- the
-- learned reconstruction FUNCTION is deterministic, same as DNN_* (see
-- models/dnn_regressor/). But the two runs' actual latent_col_* values
-- are meaningfully different: the first run had latent_col_2 dead
-- (pinned to exactly 0.0 for all rows); the second run's latent_col_2
-- ranged up to ~0.9, and latent_col_1's range changed too. This is a
-- real, explainable property, not a bug: a generic autoencoder
-- bottleneck has no constraint forcing a unique, ordered basis the way
-- PCA's variance-ranked components do (see models/pca/) -- any
-- invertible transform of the latent space paired with the inverse
-- transform in the decoder reconstructs identically, so different
-- training runs can land on equally good but differently-shaped latent
-- geometries. Practical implication: treat the autoencoder's overall
-- reconstruction quality (ML.EVALUATE) as reproducible under a fixed
-- model name, but don't assume any individual latent_col_N carries a
-- fixed, comparable meaning across retrains the way PCA's
-- principal_component_N does.


-- =============================================================================
-- Example 12: In-model preprocessing with the TRANSFORM clause
-- =============================================================================
-- Adds island as a categorical feature alongside the four numeric
-- measurements. Verified: mean_squared_error improves from ~0.21 to
-- ~0.13. This makes sense: island only has 3 categories, one-hot
-- encoded -- the model reconstructs a low-cardinality categorical
-- almost perfectly, which pulls the average per-dimension
-- reconstruction error down across the board. Not a gotcha -- an
-- expected consequence of adding an easy-to-reconstruct feature to the
-- averaged error metric.
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.autoencoder_penguins_transform`
TRANSFORM(
  culmen_length_mm, culmen_depth_mm, flipper_length_mm, body_mass_g, island
)
OPTIONS(
  model_type = 'AUTOENCODER',
  hidden_units = [3, 2, 3],
  activation_fn = 'TANH',
  learn_rate = 0.01,
  max_iterations = 30
) AS
SELECT culmen_length_mm, culmen_depth_mm, flipper_length_mm, body_mass_g, island
FROM `bigquery-public-data.ml_datasets.penguins`
WHERE body_mass_g IS NOT NULL;

SELECT *
FROM ML.EVALUATE(MODEL `PROJECT_ID.DATASET.autoencoder_penguins_transform`);


-- =============================================================================
-- Example 13: Hyperparameter tuning — NUM_TRIALS + HPARAM_CANDIDATES/HPARAM_RANGE
-- =============================================================================
-- Tunes activation_fn (RELU vs TANH) and learn_rate together, minimizing
-- mean_squared_error.
--
-- Result below, honestly reported as-is: this run's 4-trial search
-- sampled 3 RELU configurations (learn_rate 0.0060, 0.0010, 0.0018) and
-- only 1 TANH configuration (learn_rate 0.0024), with a RELU trial
-- winning (mean_squared_error=0.967). This does NOT confirm Example 4's
-- finding that TANH beats RELU -- every one of these 4 tuned trials
-- scored worse than BOTH Example 2's untuned RELU baseline (~0.66-0.94)
-- and Example 4's untuned TANH fix (~0.21). With only 4 trials spread
-- across two hyperparameters at once, the search is too sparse to
-- reliably explore either dimension -- a small trial budget can fail to
-- find a known-good region, the same limitation already documented for
-- models/dnn_regressor/'s hyperparameter tuning. Don't treat a
-- small-budget tuning result as evidence for or against a specific
-- hyperparameter's importance -- Example 4's direct, controlled,
-- same-learn_rate comparison remains the reliable evidence that TANH
-- fixes the collapse, not this tuning search.
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.autoencoder_penguins_tuned`
OPTIONS(
  model_type = 'AUTOENCODER',
  hidden_units = [3, 2, 3],
  activation_fn = HPARAM_CANDIDATES(['RELU', 'TANH']),
  learn_rate = HPARAM_RANGE(0.001, 0.05),
  max_iterations = 30,
  num_trials = 4,
  max_parallel_trials = 2,
  hparam_tuning_objectives = ['mean_squared_error']
) AS
SELECT culmen_length_mm, culmen_depth_mm, flipper_length_mm, body_mass_g
FROM `bigquery-public-data.ml_datasets.penguins`
WHERE body_mass_g IS NOT NULL;

SELECT
  trial_id,
  hyperparameters,
  hparam_tuning_evaluation_metrics.mean_squared_error AS mean_squared_error,
  is_optimal
FROM ML.TRIAL_INFO(MODEL `PROJECT_ID.DATASET.autoencoder_penguins_tuned`)
ORDER BY mean_squared_error ASC;


-- =============================================================================
-- Cleanup
-- =============================================================================
-- DROP MODEL IF EXISTS `PROJECT_ID.DATASET.autoencoder_penguins`;
-- DROP MODEL IF EXISTS `PROJECT_ID.DATASET.autoencoder_penguins_fix`;
-- DROP MODEL IF EXISTS `PROJECT_ID.DATASET.autoencoder_penguins_transform`;
-- DROP MODEL IF EXISTS `PROJECT_ID.DATASET.autoencoder_penguins_tuned`;
