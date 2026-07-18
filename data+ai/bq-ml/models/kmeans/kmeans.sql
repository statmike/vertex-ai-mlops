-- K-Means — Progressive SQL Examples (BigQuery ML)
-- =============================================================
-- Unsupervised clustering with CREATE MODEL (model_type = 'KMEANS').
-- Partitions rows into k clusters by nearest centroid, with no label
-- column. Walks the full model lifecycle: create -> evaluate -> predict ->
-- visualize -> inspect centroids -> detect anomalies -> preprocess ->
-- hyperparameter-tune.
--
-- Data: bigquery-public-data.ml_datasets.penguins
--       No label -- clustering on the four continuous physical
--       measurements only (culmen_length_mm, culmen_depth_mm,
--       flipper_length_mm, body_mass_g). species/island/sex are NOT
--       used as training features, but species is carried through
--       ML.PREDICT afterward as an external check: does unsupervised
--       clustering on raw measurements recover the real species groups?
--       Rows with a NULL body_mass_g are filtered out (342 of 344 rows
--       remain -- a different N than the classification/regression
--       notebooks, which also filter on sex).
--
-- Full reference: ../../RESOURCES.md
-- Official docs:
--   CREATE MODEL (K-means): https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-kmeans
--   The CREATE MODEL statement: https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create


-- =============================================================================
-- Example 1: CREATE MODEL — train a k-means clustering model
-- =============================================================================
-- model_type is the only essential -- there's no input_label_cols for
-- unsupervised models. num_clusters=3 is a deliberate, informed choice
-- here (3 penguin species), not a default guess. kmeans_init_method=
-- 'KMEANS++' gives more stable, generally better convergence than the
-- RANDOM default -- though see Example 9: even with KMEANS++, retraining
-- is not fully deterministic. standardize_features defaults to TRUE --
-- important here since body_mass_g (thousands of grams) and
-- culmen_depth_mm (tens of mm) are on wildly different scales.
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.kmeans_penguins`
OPTIONS(
  model_type = 'KMEANS',
  num_clusters = 3,
  kmeans_init_method = 'KMEANS++',
  distance_type = 'EUCLIDEAN'
) AS
SELECT culmen_length_mm, culmen_depth_mm, flipper_length_mm, body_mass_g
FROM `bigquery-public-data.ml_datasets.penguins`
WHERE body_mass_g IS NOT NULL;


-- =============================================================================
-- Example 2: ML.EVALUATE — clustering quality metrics
-- =============================================================================
-- davies_bouldin_index: average similarity between each cluster and its
-- most-similar other cluster (lower is better -- more separated clusters).
-- mean_squared_distance: average squared distance from each point to its
-- assigned centroid (lower is better -- tighter clusters). Neither metric
-- needs or uses a label -- this is intrinsic cluster quality, not
-- agreement with any ground truth.
SELECT *
FROM ML.EVALUATE(MODEL `PROJECT_ID.DATASET.kmeans_penguins`);


-- =============================================================================
-- Example 3: ML.PREDICT — assign a cluster to each row
-- =============================================================================
-- Returns CENTROID_ID (the assigned cluster) and NEAREST_CENTROIDS_DISTANCE
-- (distance to every centroid, ordered nearest-first). species is passed
-- through untouched (it wasn't a training feature) purely so we can check,
-- as an external validation, how well the unsupervised clusters line up
-- with the real species labels.
--
-- Result below, honestly reported as-is: one cluster recovers Gentoo
-- penguins almost perfectly, but the other two mix Adelie and Chinstrap --
-- those two species overlap more in body measurements than either does
-- with Gentoo. Unsupervised clustering finds real structure here, but not
-- a perfect species partition. Caveat (see Example 7): K-means retraining
-- is non-deterministic, so re-running this exact query can shift which
-- species end up cleanly separated and which overlap -- don't treat this
-- specific split as guaranteed to reproduce bit-for-bit.
SELECT species, CENTROID_ID, COUNT(*) AS n
FROM ML.PREDICT(
  MODEL `PROJECT_ID.DATASET.kmeans_penguins`,
  (SELECT species, culmen_length_mm, culmen_depth_mm, flipper_length_mm, body_mass_g
   FROM `bigquery-public-data.ml_datasets.penguins`
   WHERE body_mass_g IS NOT NULL)
)
GROUP BY species, CENTROID_ID
ORDER BY species, CENTROID_ID;


-- =============================================================================
-- Example 4: ML.CENTROIDS — inspect the cluster centers
-- =============================================================================
-- One row per (centroid_id, feature) with the centroid's coordinate on
-- that feature -- this is how you interpret what each cluster "means"
-- (e.g. cluster 3's centroid has the highest body_mass_g and
-- flipper_length_mm -- consistent with it being the Gentoo cluster,
-- the largest of the three species).
SELECT *
FROM ML.CENTROIDS(MODEL `PROJECT_ID.DATASET.kmeans_penguins`)
ORDER BY centroid_id, feature;


-- =============================================================================
-- Example 5: ML.FEATURE_INFO — introspect the training features
-- =============================================================================
SELECT *
FROM ML.FEATURE_INFO(MODEL `PROJECT_ID.DATASET.kmeans_penguins`);


-- =============================================================================
-- Example 6: ML.DETECT_ANOMALIES — distance-based outlier detection
-- =============================================================================
-- GOTCHA (verified): for KMEANS, the input-data argument is REQUIRED --
-- unlike the general 2-argument form that works for some other model
-- types, calling this with only (MODEL, STRUCT(contamination)) errors
-- immediately: "DETECT_ANOMALIES expects 3 arguments for KMEANS models
-- but 2 were passed." Always pass the scoring data as the 3rd argument.
--
-- contamination=0.05 flags the 5% of rows with the largest
-- normalized_distance from their nearest centroid as anomalies.
SELECT *
FROM ML.DETECT_ANOMALIES(
  MODEL `PROJECT_ID.DATASET.kmeans_penguins`,
  STRUCT(0.05 AS contamination),
  (SELECT culmen_length_mm, culmen_depth_mm, flipper_length_mm, body_mass_g
   FROM `bigquery-public-data.ml_datasets.penguins`
   WHERE body_mass_g IS NOT NULL)
)
WHERE is_anomaly
ORDER BY normalized_distance DESC;


-- =============================================================================
-- Example 7: In-model preprocessing with the TRANSFORM clause
-- =============================================================================
-- Adds island as a categorical feature alongside the four scaled numeric
-- measurements (BQML auto-one-hot-encodes categorical columns; explicit
-- ML.STANDARD_SCALER on the numerics here is redundant with the model's
-- own standardize_features=TRUE default, but shown for clarity).
--
-- GOTCHA (verified): K-means retraining is genuinely non-deterministic
-- here, even with kmeans_init_method='KMEANS++'. Retraining both the
-- baseline (Example 1) and this model multiple times on identical SQL
-- shows davies_bouldin_index and the specific cluster-to-species
-- alignment both vary meaningfully across separate CREATE OR REPLACE
-- MODEL calls on the exact same SQL -- sometimes the baseline's
-- davies_bouldin_index is lower, sometimes this transform's is; sometimes
-- Gentoo ends up in one clean cluster, sometimes it's split, regardless of
-- whether island was included. This means a SINGLE before/after
-- comparison is not reliable evidence that a specific feature change
-- causes a specific effect -- you'd need to retrain each config multiple
-- times and look at the range, not one sample. Separately:
-- davies_bouldin_index measures internal cluster separation in whatever
-- feature space you give it -- it says nothing about whether the
-- resulting clusters line up with any domain-meaningful grouping, so
-- don't treat a lower value alone as proof of a "better" or "more useful"
-- clustering.
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.kmeans_penguins_transform`
TRANSFORM(
  ML.STANDARD_SCALER(culmen_length_mm) OVER() AS culmen_length_mm,
  ML.STANDARD_SCALER(culmen_depth_mm) OVER() AS culmen_depth_mm,
  ML.STANDARD_SCALER(flipper_length_mm) OVER() AS flipper_length_mm,
  ML.STANDARD_SCALER(body_mass_g) OVER() AS body_mass_g,
  island
)
OPTIONS(
  model_type = 'KMEANS',
  num_clusters = 3,
  kmeans_init_method = 'KMEANS++',
  distance_type = 'EUCLIDEAN'
) AS
SELECT culmen_length_mm, culmen_depth_mm, flipper_length_mm, body_mass_g, island
FROM `bigquery-public-data.ml_datasets.penguins`
WHERE body_mass_g IS NOT NULL;

-- Confirm with ML.EVALUATE -- see the comment above for why comparing this
-- number to Example 2's isn't as simple as "higher/lower is the effect of
-- adding island."
SELECT *
FROM ML.EVALUATE(MODEL `PROJECT_ID.DATASET.kmeans_penguins_transform`);

SELECT species, CENTROID_ID, COUNT(*) AS n
FROM ML.PREDICT(
  MODEL `PROJECT_ID.DATASET.kmeans_penguins_transform`,
  (SELECT species, culmen_length_mm, culmen_depth_mm, flipper_length_mm, body_mass_g, island
   FROM `bigquery-public-data.ml_datasets.penguins`
   WHERE body_mass_g IS NOT NULL)
)
GROUP BY species, CENTROID_ID
ORDER BY species, CENTROID_ID;


-- =============================================================================
-- Example 8: Hyperparameter tuning — NUM_TRIALS + HPARAM_RANGE
-- =============================================================================
-- num_clusters is the primary tunable option, searched via HPARAM_RANGE
-- with the default davies_bouldin_index objective (minimize -- lower is
-- better cluster separation).
--
-- Result below, honestly reported as-is -- and another instance of the
-- non-determinism from Example 7: one run of this exact tuning
-- configuration selected num_clusters=2 as optimal; a separate
-- pre-validation run of the identical search space selected
-- num_clusters=3 (matching the true species count) instead. Both are
-- real outputs of the identical config -- they just landed on different
-- local optima. Don't treat a single HP-tuning run's chosen value as the
-- definitive answer for num_clusters on this kind of data.
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.kmeans_penguins_tuned`
OPTIONS(
  model_type = 'KMEANS',
  num_clusters = HPARAM_RANGE(2, 10),
  kmeans_init_method = 'KMEANS++',
  distance_type = 'EUCLIDEAN',
  num_trials = 6,
  max_parallel_trials = 3,
  hparam_tuning_objectives = ['davies_bouldin_index']
) AS
SELECT culmen_length_mm, culmen_depth_mm, flipper_length_mm, body_mass_g
FROM `bigquery-public-data.ml_datasets.penguins`
WHERE body_mass_g IS NOT NULL;

-- Inspect each trial's hyperparameters and objective score.
SELECT
  trial_id,
  hyperparameters,
  hparam_tuning_evaluation_metrics.davies_bouldin_index AS davies_bouldin_index,
  is_optimal
FROM ML.TRIAL_INFO(MODEL `PROJECT_ID.DATASET.kmeans_penguins_tuned`)
ORDER BY davies_bouldin_index ASC;


-- =============================================================================
-- Cleanup
-- =============================================================================
-- DROP MODEL IF EXISTS `PROJECT_ID.DATASET.kmeans_penguins`;
-- DROP MODEL IF EXISTS `PROJECT_ID.DATASET.kmeans_penguins_transform`;
-- DROP MODEL IF EXISTS `PROJECT_ID.DATASET.kmeans_penguins_tuned`;
