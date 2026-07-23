-- Imported Models — Progressive SQL Examples (BigQuery ML)
-- =============================================================
-- Imported models bring a model trained OUTSIDE BigQuery -- in TensorFlow,
-- TensorFlow Lite, ONNX, or XGBoost -- into BigQuery ML from Cloud Storage
-- and run inference with ML.PREDICT natively inside BigQuery compute. No
-- Vertex AI endpoint to deploy, manage, or pay for -- but no training, no
-- TRANSFORM, no HP tuning, no ML.EVALUATE either: the model is frozen at
-- import time. All four share one shape:
--   CREATE MODEL ... OPTIONS(MODEL_TYPE='...', MODEL_PATH='gs://...')
--
-- Data: bigquery-public-data.ml_datasets.penguins (same as models/kmeans/,
--       models/pca/, models/transform_only/) -- 342 rows with all 4
--       physical measurements present. Each format is trained LOCALLY
--       (outside BigQuery, since that's the entire premise of "imported")
--       on the same 4 numeric features, then imported and scored with
--       ML.PREDICT.
--
-- Full reference: ../../RESOURCES.md
-- Official docs:
--   CREATE MODEL (TensorFlow):      https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-tensorflow
--   CREATE MODEL (TensorFlow Lite): https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-tflite
--   CREATE MODEL (ONNX):            https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-onnx
--   CREATE MODEL (XGBoost):         https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-xgboost


-- =============================================================================
-- Example 1: ONNX — import a scikit-learn model
-- =============================================================================
-- A scikit-learn LogisticRegression, converted to ONNX with skl2onnx and
-- zipmap=False (without this, sklearn-onnx emits a "sequence of map" for
-- probabilities that BigQuery ML's importer rejects: "unsupported ONNX
-- type: ONNX_TYPE_SEQUENCE").
--
-- GOTCHA (verified): BigQuery ML's ONNX importer runs on ONNX Runtime
-- 1.12.0. A model saved with a modern skl2onnx defaults to IR version 10
-- and opset 22 -- both too new. Fix at conversion/save time:
--   onnx_model.ir_version = 8          -- max supported IR version is 8
--   convert_sklearn(..., target_opset=13)   -- opset 22 is unsupported/dev-only
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.imported_onnx_penguins`
OPTIONS(
  model_type = 'ONNX',
  model_path = 'gs://BUCKET/bq_ml/imported/onnx/*'
);

-- ML.FEATURE_INFO is NOT supported for ONNX (or any imported type) --
-- verified: "Model type ONNX is not supported by FEATURE_INFO." Use the
-- Python/BigFrames client (bq.get_model(...)) to confirm import instead.
SELECT species, label, probabilities
FROM ML.PREDICT(
  MODEL `PROJECT_ID.DATASET.imported_onnx_penguins`,
  (SELECT species,
     [CAST(culmen_length_mm AS FLOAT64), CAST(culmen_depth_mm AS FLOAT64),
      CAST(flipper_length_mm AS FLOAT64), CAST(body_mass_g AS FLOAT64)] AS input
   FROM `bigquery-public-data.ml_datasets.penguins`
   WHERE body_mass_g IS NOT NULL LIMIT 5)
);


-- =============================================================================
-- Example 2: XGBOOST — import a native XGBoost Booster
-- =============================================================================
-- Trained directly with the xgboost library's own train()/DMatrix API (no
-- conversion step needed -- XGBoost is BQML's native import format for
-- this library). A binary classifier (predict "is this an Adelie
-- penguin?") keeps the declared OUTPUT a clean scalar FLOAT64 -- a
-- multiclass 'multi:softprob' objective still predicts fine, but BigQuery
-- ML silently returns an ARRAY of per-class probabilities even though
-- OUTPUT declared a single FLOAT64 field, which is confusing to read.
--
-- GOTCHA (verified, undocumented as of this writing): BigQuery ML's
-- XGBoost importer only accepts Booster files saved by XGBoost <= 1.5.1 --
-- "XGBoost model version newer than 1.5.1 is not supported." A booster
-- saved with a modern xgboost (2.x/3.x) fails to import outright. Train
-- with xgboost==1.5.1 specifically for this step (see the notebook's
-- Setup section for the numpy<2 pin this version needs).
--
-- INPUT/OUTPUT is REQUIRED here (unlike ONNX/TensorFlow) unless the
-- Booster file embeds both feature_names AND feature_types.
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.imported_xgboost_penguins`
INPUT(culmen_length_mm FLOAT64, culmen_depth_mm FLOAT64, flipper_length_mm FLOAT64, body_mass_g FLOAT64)
OUTPUT(is_adelie_prob FLOAT64)
OPTIONS(
  model_type = 'XGBOOST',
  model_path = 'gs://BUCKET/bq_ml/imported/xgboost/*'
);

SELECT species, is_adelie_prob
FROM ML.PREDICT(
  MODEL `PROJECT_ID.DATASET.imported_xgboost_penguins`,
  (SELECT species, culmen_length_mm, culmen_depth_mm, flipper_length_mm, body_mass_g
   FROM `bigquery-public-data.ml_datasets.penguins`
   WHERE body_mass_g IS NOT NULL LIMIT 5)
);

-- XGBOOST is the ONLY imported type that supports ML.FEATURE_IMPORTANCE --
-- verified working here, unlike ONNX/TENSORFLOW/TENSORFLOW_LITE.
SELECT *
FROM ML.FEATURE_IMPORTANCE(MODEL `PROJECT_ID.DATASET.imported_xgboost_penguins`);


-- =============================================================================
-- Example 3: TENSORFLOW — import a Keras SavedModel
-- =============================================================================
-- A small Keras Sequential model with a tf.keras.layers.Normalization
-- layer BAKED IN (adapted on training data) -- since imported models
-- support no TRANSFORM/preprocessing of their own, any feature scaling
-- the model needs must be part of the exported graph itself, so raw
-- column values can be fed directly at predict time.
--
-- Input must be a single ARRAY<FLOAT64> column matching the SavedModel's
-- named input signature ("input", shape (-1, 4)) -- BigQuery maps it by
-- name. Output column is auto-named output_0 (unnamed model output).
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.imported_tensorflow_penguins`
OPTIONS(
  model_type = 'TENSORFLOW',
  model_path = 'gs://BUCKET/bq_ml/imported/tensorflow/*'
);

SELECT species, output_0
FROM ML.PREDICT(
  MODEL `PROJECT_ID.DATASET.imported_tensorflow_penguins`,
  (SELECT species,
     [CAST(culmen_length_mm AS FLOAT64), CAST(culmen_depth_mm AS FLOAT64),
      CAST(flipper_length_mm AS FLOAT64), CAST(body_mass_g AS FLOAT64)] AS input
   FROM `bigquery-public-data.ml_datasets.penguins`
   WHERE body_mass_g IS NOT NULL LIMIT 5)
);

-- CORRECTION to the docs (verified live): RESOURCES.md's imported-models
-- capability table (sourced from official docs) lists ML.EXPLAIN_PREDICT
-- as supported for TENSORFLOW imports. Calling it on this model returns:
-- "TENSORFLOW model is unsupported in ml.explain_predict." Not
-- reproduced here -- treat that capability-table cell as unverified/stale
-- until confirmed against a model that does support it.
-- SELECT * FROM ML.EXPLAIN_PREDICT(MODEL `PROJECT_ID.DATASET.imported_tensorflow_penguins`, ...);


-- =============================================================================
-- Example 4: TENSORFLOW_LITE — import the same model, converted to .tflite
-- =============================================================================
-- tf.lite.TFLiteConverter.from_saved_model(...) on the exact SavedModel
-- from Example 3 -- same graph, same Normalization layer baked in, just a
-- more compact serialized format.
--
-- Verified: predictions are numerically identical to the TENSORFLOW
-- import (no quantization applied here) -- same input contract
-- (ARRAY<FLOAT64> named "input"), same output_0 column naming convention.
-- Only ML.PREDICT is supported for this type (narrower than TENSORFLOW,
-- which also nominally supports ML.EXPLAIN_PREDICT per the docs).
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.imported_tflite_penguins`
OPTIONS(
  model_type = 'TENSORFLOW_LITE',
  model_path = 'gs://BUCKET/bq_ml/imported/tflite/*'
);

SELECT species, output_0
FROM ML.PREDICT(
  MODEL `PROJECT_ID.DATASET.imported_tflite_penguins`,
  (SELECT species,
     [CAST(culmen_length_mm AS FLOAT64), CAST(culmen_depth_mm AS FLOAT64),
      CAST(flipper_length_mm AS FLOAT64), CAST(body_mass_g AS FLOAT64)] AS input
   FROM `bigquery-public-data.ml_datasets.penguins`
   WHERE body_mass_g IS NOT NULL LIMIT 5)
);


-- =============================================================================
-- Cleanup
-- =============================================================================
-- DROP MODEL IF EXISTS `PROJECT_ID.DATASET.imported_onnx_penguins`;
-- DROP MODEL IF EXISTS `PROJECT_ID.DATASET.imported_xgboost_penguins`;
-- DROP MODEL IF EXISTS `PROJECT_ID.DATASET.imported_tensorflow_penguins`;
-- DROP MODEL IF EXISTS `PROJECT_ID.DATASET.imported_tflite_penguins`;
-- (delete the 4 GCS model directories uploaded for this notebook)
