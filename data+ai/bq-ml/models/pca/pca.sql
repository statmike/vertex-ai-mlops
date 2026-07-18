-- PCA — Progressive SQL Examples (BigQuery ML)
-- =============================================================
-- Unsupervised dimensionality reduction with CREATE MODEL (model_type =
-- 'PCA') -- transforms correlated features into a smaller set of
-- orthogonal principal components ordered by variance explained. No label
-- column. Walks the full model lifecycle: create -> evaluate -> predict ->
-- visualize -> inspect components -> detect anomalies -> preprocess ->
-- alternative component-selection approach (PCA has no hyperparameter
-- tuning).
--
-- Data: bigquery-public-data.ml_datasets.penguins
--       No label -- reduces the four continuous physical measurements
--       (culmen_length_mm, culmen_depth_mm, flipper_length_mm,
--       body_mass_g) to 2 principal components. species/island/sex are
--       NOT training features, but species is carried through ML.PREDICT
--       afterward as an external check, same convention as models/kmeans/.
--       342 of 344 rows remain after filtering body_mass_g IS NOT NULL.
--
-- Full reference: ../../RESOURCES.md
-- Official docs:
--   CREATE MODEL (PCA): https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-pca
--   The CREATE MODEL statement: https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create


-- =============================================================================
-- Example 1: CREATE MODEL — train a PCA model
-- =============================================================================
-- model_type is the only essential -- there's no input_label_cols for
-- unsupervised models. Exactly one of num_principal_components /
-- pca_explained_variance_ratio is required; num_principal_components=2
-- is chosen here for a clean 2D visualization (Example 8 demonstrates the
-- pca_explained_variance_ratio alternative). scale_features defaults to
-- TRUE -- important since body_mass_g (thousands of grams) and
-- culmen_depth_mm (tens of mm) are on very different scales.
--
-- Verified: unlike models/kmeans/, PCA is fully deterministic --
-- retraining this exact model produced a bit-for-bit identical
-- total_explained_variance_ratio. PCA is a closed-form eigendecomposition,
-- not an iterative algorithm with random initialization, so there is no
-- retraining variance to worry about here. A third independent training,
-- via bigframes.ml.decomposition.PCA under a completely different model
-- name (see the notebook's BigFrames section), reproduced the exact same
-- value again -- a contrast to KMEANS, where BigFrames' independently
-- trained model produced yet a different value each time.
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.pca_penguins`
OPTIONS(
  model_type = 'PCA',
  num_principal_components = 2,
  scale_features = TRUE,
  pca_solver = 'AUTO'
) AS
SELECT culmen_length_mm, culmen_depth_mm, flipper_length_mm, body_mass_g
FROM `bigquery-public-data.ml_datasets.penguins`
WHERE body_mass_g IS NOT NULL;


-- =============================================================================
-- Example 2: ML.EVALUATE — variance-based quality metric
-- =============================================================================
-- total_explained_variance_ratio: fraction of total variance captured by
-- the retained components. No label, no agreement-with-ground-truth
-- metric -- this is intrinsic to the projection itself.
SELECT *
FROM ML.EVALUATE(MODEL `PROJECT_ID.DATASET.pca_penguins`);


-- =============================================================================
-- Example 3: ML.PREDICT — project rows onto the principal components
-- =============================================================================
-- Returns principal_component_1..N. species is passed through untouched
-- (it wasn't a training feature) purely as an external check on whether
-- the unsupervised projection separates species visually.
SELECT species, principal_component_1, principal_component_2
FROM ML.PREDICT(
  MODEL `PROJECT_ID.DATASET.pca_penguins`,
  (SELECT species, culmen_length_mm, culmen_depth_mm, flipper_length_mm, body_mass_g
   FROM `bigquery-public-data.ml_datasets.penguins`
   WHERE body_mass_g IS NOT NULL)
);


-- =============================================================================
-- Example 4: ML.PRINCIPAL_COMPONENTS — inspect the component loadings
-- =============================================================================
-- One row per (principal_component_id, feature) with that feature's
-- loading (eigenvector coefficient) on that component.
--
-- GOTCHA (verified): principal_component_id is 0-indexed (0, 1, ...) --
-- unlike KMEANS' centroid_id, which is 1-indexed (1, 2, 3, ...). Don't
-- assume consistent indexing conventions across unsupervised model types.
--
-- Interpretation: component 0's loadings are negative on body_mass_g,
-- culmen_length_mm, and flipper_length_mm but positive on
-- culmen_depth_mm -- a "body size" axis (bigger penguins score more
-- negative), consistent with the real biology (Gentoo, the largest
-- species, also has a shallower bill relative to its size than
-- Adelie/Chinstrap).
SELECT *
FROM ML.PRINCIPAL_COMPONENTS(MODEL `PROJECT_ID.DATASET.pca_penguins`)
ORDER BY principal_component_id, feature;


-- =============================================================================
-- Example 5: ML.PRINCIPAL_COMPONENT_INFO — variance per component
-- =============================================================================
-- eigenvalue, explained_variance_ratio, and cumulative_explained_variance_ratio
-- per component -- use this to pick a sensible component count via the
-- "elbow" in cumulative variance. Here component 0 alone explains ~69% of
-- variance; adding component 1 brings the total to ~88%.
SELECT *
FROM ML.PRINCIPAL_COMPONENT_INFO(MODEL `PROJECT_ID.DATASET.pca_penguins`);


-- =============================================================================
-- Example 6: ML.FEATURE_INFO — introspect the training features
-- =============================================================================
SELECT *
FROM ML.FEATURE_INFO(MODEL `PROJECT_ID.DATASET.pca_penguins`);


-- =============================================================================
-- Example 7: ML.DETECT_ANOMALIES — reconstruction-based outlier detection
-- =============================================================================
-- GOTCHA (verified, same as models/kmeans/): the input-data argument is
-- REQUIRED for PCA too -- calling this with only (MODEL,
-- STRUCT(contamination)) errors immediately: "DETECT_ANOMALIES expects 3
-- arguments for PCA models but 2 were passed." Always pass the scoring
-- data as the 3rd argument. This resolves a question left open in
-- models/kmeans/'s RESOURCES.md entry (whether the requirement was
-- KMEANS-specific) -- it is not; PCA shares it.
--
-- contamination=0.05 flags the 5% of rows with the largest reconstruction
-- error (mean_squared_error) as anomalies.
SELECT *
FROM ML.DETECT_ANOMALIES(
  MODEL `PROJECT_ID.DATASET.pca_penguins`,
  STRUCT(0.05 AS contamination),
  (SELECT culmen_length_mm, culmen_depth_mm, flipper_length_mm, body_mass_g
   FROM `bigquery-public-data.ml_datasets.penguins`
   WHERE body_mass_g IS NOT NULL)
)
WHERE is_anomaly
ORDER BY mean_squared_error DESC;


-- =============================================================================
-- Example 8: ML.GENERATE_EMBEDDING — package the projection as a single array
-- =============================================================================
-- Wraps the same PC1/PC2 projection from Example 3 into a single
-- ml_generate_embedding_result ARRAY<FLOAT> column -- purpose-built for
-- VECTOR_SEARCH. Verified: the array values match ML.PREDICT's
-- principal_component_1/2 columns exactly, in order.
SELECT species, ml_generate_embedding_result
FROM ML.GENERATE_EMBEDDING(
  MODEL `PROJECT_ID.DATASET.pca_penguins`,
  (SELECT species, culmen_length_mm, culmen_depth_mm, flipper_length_mm, body_mass_g
   FROM `bigquery-public-data.ml_datasets.penguins`
   WHERE body_mass_g IS NOT NULL LIMIT 5)
);


-- =============================================================================
-- Example 9: In-model preprocessing with the TRANSFORM clause
-- =============================================================================
-- Adds island as a categorical feature alongside the four numeric
-- measurements. Verified (and reproduced on a second retrain, since PCA
-- is deterministic -- see Example 1): total_explained_variance_ratio
-- DROPS from ~0.88 to ~0.76 with the same 2 components. This makes sense
-- (not a gotcha like the analogous change was for k-means): island gets
-- one-hot encoded into extra dimensions, so the same 2 components must
-- now spread their explanatory power across more total variance -- with
-- more features contributing variance, 2 components capture a smaller
-- fraction of the (larger) total.
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.pca_penguins_transform`
TRANSFORM(
  culmen_length_mm, culmen_depth_mm, flipper_length_mm, body_mass_g, island
)
OPTIONS(
  model_type = 'PCA',
  num_principal_components = 2,
  scale_features = TRUE
) AS
SELECT culmen_length_mm, culmen_depth_mm, flipper_length_mm, body_mass_g, island
FROM `bigquery-public-data.ml_datasets.penguins`
WHERE body_mass_g IS NOT NULL;

SELECT *
FROM ML.EVALUATE(MODEL `PROJECT_ID.DATASET.pca_penguins_transform`);


-- =============================================================================
-- Example 10: pca_explained_variance_ratio — an alternative to a fixed count
-- =============================================================================
-- PCA has no hyperparameter tuning (num_trials/HPARAM_RANGE do not apply),
-- so unlike every supervised/KMEANS notebook in this project, there's no
-- ML.TRIAL_INFO step here. Instead, pca_explained_variance_ratio lets you
-- target a retained-information level and let BigQuery ML pick the
-- component count automatically.
--
-- Verified: targeting 0.90 selects 3 components (2 components only reach
-- ~0.88, just short of the 0.90 target -- the 3rd is needed to cross it),
-- reaching a cumulative ratio of ~0.97.
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.pca_penguins_variance`
OPTIONS(
  model_type = 'PCA',
  pca_explained_variance_ratio = 0.90,
  scale_features = TRUE
) AS
SELECT culmen_length_mm, culmen_depth_mm, flipper_length_mm, body_mass_g
FROM `bigquery-public-data.ml_datasets.penguins`
WHERE body_mass_g IS NOT NULL;

SELECT *
FROM ML.EVALUATE(MODEL `PROJECT_ID.DATASET.pca_penguins_variance`);

SELECT *
FROM ML.PRINCIPAL_COMPONENT_INFO(MODEL `PROJECT_ID.DATASET.pca_penguins_variance`);


-- =============================================================================
-- Cleanup
-- =============================================================================
-- DROP MODEL IF EXISTS `PROJECT_ID.DATASET.pca_penguins`;
-- DROP MODEL IF EXISTS `PROJECT_ID.DATASET.pca_penguins_transform`;
-- DROP MODEL IF EXISTS `PROJECT_ID.DATASET.pca_penguins_variance`;
