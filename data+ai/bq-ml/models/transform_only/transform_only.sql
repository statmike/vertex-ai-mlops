-- TRANSFORM_ONLY — Progressive SQL Examples (BigQuery ML)
-- =============================================================
-- A model that contains ONLY a TRANSFORM clause -- no learning algorithm.
-- It packages a set of feature-preprocessing rules (plus the statistics
-- computed at creation time, e.g. the mean/stddev ML.STANDARD_SCALER
-- needs) as a reusable, exportable model object. There is no estimator to
-- train, evaluate, or explain -- the model's "output" is the preprocessed
-- data, materialized via ML.TRANSFORM. Decouples feature engineering from
-- model training so the same preprocessing can be reused across many
-- downstream models and serving paths, with train/serve statistics frozen
-- at creation time (no training/serving skew).
--
-- Data: bigquery-public-data.ml_datasets.penguins
--       Same dataset as models/kmeans/, models/pca/, models/autoencoder/.
--       Builds a small preprocessing pipeline (impute + scale + one-hot
--       encode) over the four physical measurements + sex, then feeds the
--       pipeline's output into a downstream LOGISTIC_REG classifier
--       predicting species.
--
-- Full reference: ../../RESOURCES.md
-- Official docs:
--   CREATE MODEL (transform-only): https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-transform
--   ML.TRANSFORM: https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-transform
--   TRANSFORM clause: https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create#transform


-- =============================================================================
-- Example 1: CREATE MODEL — a preprocessing pipeline with no estimator
-- =============================================================================
-- model_type = 'TRANSFORM_ONLY' is the only option that applies -- no
-- input_label_cols, no learning options (any would error). Every
-- transformed column needs an explicit alias (anonymous expressions are
-- rejected); species and island pass through untransformed.
--
-- ML.IMPUTER needs a strategy argument ('mean'/'median'/'most_frequent') --
-- it is NOT a single-argument function like the scalers.
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.transform_only_penguins`
TRANSFORM(
  species,
  island,
  ML.IMPUTER(body_mass_g, 'mean') OVER() AS body_mass_g,
  ML.STANDARD_SCALER(culmen_length_mm) OVER() AS culmen_length_mm,
  ML.STANDARD_SCALER(culmen_depth_mm) OVER() AS culmen_depth_mm,
  ML.ROBUST_SCALER(flipper_length_mm) OVER() AS flipper_length_mm,
  ML.ONE_HOT_ENCODER(sex) OVER() AS sex_encoded
)
OPTIONS(
  model_type = 'TRANSFORM_ONLY'
) AS
SELECT species, island, sex, body_mass_g, culmen_length_mm, culmen_depth_mm, flipper_length_mm
FROM `bigquery-public-data.ml_datasets.penguins`;


-- =============================================================================
-- Example 2: ML.TRANSFORM — apply the pipeline to new data
-- =============================================================================
-- Returns exactly the columns the TRANSFORM clause produces (species,
-- island, body_mass_g, culmen_length_mm, culmen_depth_mm,
-- flipper_length_mm, sex_encoded) for the columns it DOES consume.
--
-- GOTCHA (verified): any extra column present in ML.TRANSFORM's input
-- query but NOT referenced anywhere in the TRANSFORM clause passes
-- straight through untouched, appended after the transform outputs -- here
-- that's raw `sex` sitting alongside its own encoded `sex_encoded`. This
-- is useful (carry an id/label through without re-listing it in the
-- pipeline) but easy to mistake for the pipeline itself re-emitting a raw
-- column -- it's really just "unused input passed through."
SELECT *
FROM ML.TRANSFORM(
  MODEL `PROJECT_ID.DATASET.transform_only_penguins`,
  (SELECT species, island, sex, body_mass_g, culmen_length_mm, culmen_depth_mm, flipper_length_mm
   FROM `bigquery-public-data.ml_datasets.penguins`
   LIMIT 5)
);


-- =============================================================================
-- Example 3: ML.FEATURE_INFO — pre-transform summary statistics
-- =============================================================================
-- Reports the RAW input columns' stats (min/max/mean/median/stddev,
-- category_count, null_count) -- e.g. sex has null_count=10 (the rows
-- ML.IMPUTER/ML.ONE_HOT_ENCODER handle), confirming why the pipeline
-- exists in the first place.
SELECT *
FROM ML.FEATURE_INFO(MODEL `PROJECT_ID.DATASET.transform_only_penguins`);


-- =============================================================================
-- Example 4: EXPORT MODEL — a transform-only model exports too
-- =============================================================================
-- Unlike a trained estimator (TensorFlow SavedModel with weights), a
-- transform-only export is just the preprocessing graph: a
-- `transform/saved_model.pb` (plus assets/variables for the frozen
-- statistics) -- no predictive weights, since there's no estimator.
-- EXPORT MODEL `PROJECT_ID.DATASET.transform_only_penguins`
-- OPTIONS (URI = 'gs://BUCKET/bq_ml/transform_only/model');


-- =============================================================================
-- Example 5: Feed the pipeline's output into a downstream CREATE MODEL
-- =============================================================================
-- The downstream model has NO embedded TRANSFORM of its own -- it trains
-- directly on the already-transformed columns coming out of
-- ML.TRANSFORM. This is the "feature-store style" pattern: one shared
-- pipeline, reused across many downstream models, each choosing which
-- transformed columns to consume.
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.transform_only_downstream`
OPTIONS(
  model_type = 'LOGISTIC_REG',
  input_label_cols = ['species']
) AS
SELECT species, island, body_mass_g, culmen_length_mm, culmen_depth_mm, flipper_length_mm
FROM ML.TRANSFORM(
  MODEL `PROJECT_ID.DATASET.transform_only_penguins`,
  (SELECT species, island, sex, body_mass_g, culmen_length_mm, culmen_depth_mm, flipper_length_mm
   FROM `bigquery-public-data.ml_datasets.penguins`
   WHERE body_mass_g IS NOT NULL)
);

SELECT *
FROM ML.EVALUATE(MODEL `PROJECT_ID.DATASET.transform_only_downstream`);


-- =============================================================================
-- Example 6: The gotcha — predicting on RAW data silently gives garbage
-- =============================================================================
-- Because the downstream model has no embedded TRANSFORM, ML.PREDICT does
-- NOT know to re-apply the pipeline. Feeding it raw (untransformed)
-- feature values doesn't error -- BQML happily predicts using values on
-- the wrong scale -- it just gives WRONG answers.
--
-- Verified live: every one of these rows predicts "Gentoo penguin" (the
-- largest species) regardless of the row's true species, because raw
-- body_mass_g/culmen_* values are far outside the z-score-scaled range
-- the model was actually trained on.
SELECT species, predicted_species
FROM ML.PREDICT(
  MODEL `PROJECT_ID.DATASET.transform_only_downstream`,
  (SELECT species, island, body_mass_g, culmen_length_mm, culmen_depth_mm, flipper_length_mm
   FROM `bigquery-public-data.ml_datasets.penguins`
   WHERE body_mass_g IS NOT NULL LIMIT 5)
);


-- =============================================================================
-- Example 7: The fix — re-apply ML.TRANSFORM before ML.PREDICT
-- =============================================================================
-- Wrapping the same raw rows in ML.TRANSFORM first reproduces the exact
-- preprocessing used at training time, and predictions become correct
-- again. This re-application is the price of a transform-only model's
-- reusability -- contrast with an EMBEDDED TRANSFORM clause on a
-- predictive model (e.g. models/pca/'s Step 10), which auto-applies at
-- predict time with no re-application needed, but isn't reusable across
-- other models the way a standalone TRANSFORM_ONLY model is.
SELECT species, predicted_species
FROM ML.PREDICT(
  MODEL `PROJECT_ID.DATASET.transform_only_downstream`,
  (SELECT species, island, body_mass_g, culmen_length_mm, culmen_depth_mm, flipper_length_mm
   FROM ML.TRANSFORM(
     MODEL `PROJECT_ID.DATASET.transform_only_penguins`,
     (SELECT species, island, sex, body_mass_g, culmen_length_mm, culmen_depth_mm, flipper_length_mm
      FROM `bigquery-public-data.ml_datasets.penguins`
      WHERE body_mass_g IS NOT NULL LIMIT 5)
   )
  )
);


-- =============================================================================
-- Cleanup
-- =============================================================================
-- DROP MODEL IF EXISTS `PROJECT_ID.DATASET.transform_only_penguins`;
-- DROP MODEL IF EXISTS `PROJECT_ID.DATASET.transform_only_downstream`;
-- (delete the GCS export blobs from Example 4, if run)
