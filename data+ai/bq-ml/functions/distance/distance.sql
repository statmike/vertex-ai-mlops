-- Distance / Vectors — Progressive SQL Examples (BigQuery ML model-free functions)
-- =============================================================
-- Two model-free scalar functions with NO example anywhere in this repo
-- before this notebook: ML.DISTANCE (pairwise distance between two equal-
-- length vectors) and ML.LP_NORM (the magnitude of a single vector). Neither
-- requires a model -- they operate on plain ARRAY<FLOAT64>/ARRAY<INT64> data.
--
-- Data: literal arrays for core mechanics, plus real PCA embeddings trained
--       on bigquery-public-data.ml_datasets.penguins (same dataset as every
--       other functions/ notebook and models/pca/).
--
-- Full reference: ../../RESOURCES.md
-- Official docs:
--   ML.DISTANCE: https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-distance
--   ML.LP_NORM:  https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-lp-norm


-- =============================================================================
-- Example 1: ML.DISTANCE -- all three metrics, and cosine distance vs similarity
-- =============================================================================
SELECT
  ML.DISTANCE([1.0, 2.0, 3.0], [4.0, 5.0, 6.0], 'EUCLIDEAN') AS euclidean,
  ML.DISTANCE([1.0, 2.0, 3.0], [4.0, 5.0, 6.0], 'MANHATTAN') AS manhattan,
  ML.DISTANCE([1.0, 2.0, 3.0], [4.0, 5.0, 6.0], 'COSINE') AS cosine_distance,
  1 - ML.DISTANCE([1.0, 2.0, 3.0], [4.0, 5.0, 6.0], 'COSINE') AS cosine_similarity,
  ML.DISTANCE([1.0, 2.0, 3.0], [4.0, 5.0, 6.0]) AS default_metric;  -- EUCLIDEAN when omitted

-- ML.DISTANCE returns cosine DISTANCE, not similarity -- compute
-- 1 - ML.DISTANCE(..., 'COSINE') for similarity, same pattern already used
-- in ../../../bq-ai-functions/functions/ai_embed/ai_embed.sql.


-- =============================================================================
-- Example 2: ML.LP_NORM, and a live cross-check against ML.NORMALIZER (../scalers/)
-- =============================================================================
-- VERIFIED LIVE: ML.NORMALIZER(v, p) == v / ML.LP_NORM(v, p), element-wise --
-- ML.LP_NORM computes exactly the denominator ML.NORMALIZER uses.
SELECT
  ML.LP_NORM([3.0, 4.0], 2.0) AS l2_norm,   -- Euclidean magnitude: 5.0
  ML.LP_NORM([3.0, 4.0], 1.0) AS l1_norm,   -- Manhattan magnitude: 7.0
  ML.LP_NORM([3.0, 4.0], 0.0) AS l0_norm,   -- count of nonzero elements: 2.0
  ML.NORMALIZER([3.0, 4.0], 2) AS normalizer_p2,
  [3.0 / ML.LP_NORM([3.0, 4.0], 2.0), 4.0 / ML.LP_NORM([3.0, 4.0], 2.0)] AS manual_normalized;


-- =============================================================================
-- Example 3: deriving Jaccard similarity on binary vectors (not built into ML.DISTANCE)
-- =============================================================================
-- ML.DISTANCE only supports EUCLIDEAN/MANHATTAN/COSINE. Jaccard similarity
-- (intersection / union) for binary vectors is derivable via a dot product
-- (intersection count) and L1 norms (set sizes) -- verified live.
WITH data AS (
  SELECT [1.0, 1.0, 0.0, 1.0, 0.0] AS a, [1.0, 0.0, 0.0, 1.0, 1.0] AS b
),
computed AS (
  SELECT a, b,
    (SELECT SUM(x * y) FROM UNNEST(a) AS x WITH OFFSET i JOIN UNNEST(b) AS y WITH OFFSET j ON i = j) AS intersection,
    ML.LP_NORM(a, 1.0) AS norm_a,
    ML.LP_NORM(b, 1.0) AS norm_b
  FROM data
)
SELECT *, intersection / (norm_a + norm_b - intersection) AS jaccard_similarity
FROM computed;
-- Jaccard = 2 / (3 + 3 - 2) = 0.5 -- matches manual set-based Jaccard exactly.


-- =============================================================================
-- Example 4: real embedding similarity -- distance between two penguins'
-- PCA projections (models/pca/'s exact mechanism, reused here as data)
-- =============================================================================
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.scratch_distance_pca_demo`
OPTIONS(model_type = 'PCA', num_principal_components = 2) AS
SELECT culmen_length_mm, culmen_depth_mm, flipper_length_mm, body_mass_g
FROM `bigquery-public-data.ml_datasets.penguins`
WHERE culmen_length_mm IS NOT NULL AND culmen_depth_mm IS NOT NULL
  AND flipper_length_mm IS NOT NULL AND body_mass_g IS NOT NULL;

WITH sample_penguins AS (
  (SELECT species, culmen_length_mm, culmen_depth_mm, flipper_length_mm, body_mass_g
   FROM `bigquery-public-data.ml_datasets.penguins`
   WHERE culmen_length_mm IS NOT NULL AND culmen_depth_mm IS NOT NULL AND flipper_length_mm IS NOT NULL AND body_mass_g IS NOT NULL
   ORDER BY species LIMIT 1)
  UNION ALL
  (SELECT species, culmen_length_mm, culmen_depth_mm, flipper_length_mm, body_mass_g
   FROM `bigquery-public-data.ml_datasets.penguins`
   WHERE culmen_length_mm IS NOT NULL AND culmen_depth_mm IS NOT NULL AND flipper_length_mm IS NOT NULL AND body_mass_g IS NOT NULL
   ORDER BY species DESC LIMIT 1)
),
embeddings AS (
  SELECT species, [principal_component_1, principal_component_2] AS embedding
  FROM ML.PREDICT(MODEL `PROJECT_ID.DATASET.scratch_distance_pca_demo`, (SELECT * FROM sample_penguins))
)
SELECT
  a.species AS species_a, b.species AS species_b,
  ML.DISTANCE(a.embedding, b.embedding, 'EUCLIDEAN') AS euclidean_distance,
  1 - ML.DISTANCE(a.embedding, b.embedding, 'COSINE') AS cosine_similarity
FROM embeddings a, embeddings b
WHERE a.species < b.species;

-- Same technique used by models/pca/ Step 11's ML.GENERATE_EMBEDDING +
-- VECTOR_SEARCH pattern -- ML.DISTANCE is the brute-force equivalent for a
-- one-off pairwise comparison, without building a vector index.


-- =============================================================================
-- Cleanup
-- =============================================================================
DROP MODEL IF EXISTS `PROJECT_ID.DATASET.scratch_distance_pca_demo`;
