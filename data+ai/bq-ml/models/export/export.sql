-- EXPORT MODEL — Progressive SQL Examples (BigQuery ML)
-- =============================================================
-- EXPORT MODEL writes a trained BQML model to Cloud Storage in a portable
-- format, so it can be served OUTSIDE BigQuery -- with TF Serving,
-- Vertex AI, or loaded directly with the matching library. No connection
-- is needed for the export itself (only GCS write IAM).
--
-- Data: bigquery-public-data.ml_datasets.census_adult_income (same
--       feature/label set as models/logistic_regression/ and
--       models/boosted_tree_classifier/) -- one LOGISTIC_REG (exports as
--       TensorFlow SavedModel, the default format for most model types)
--       and one small BOOSTED_TREE_CLASSIFIER (exports as an XGBoost
--       Booster -- the alternative format, specific to tree ensembles).
--
-- Full reference: ../../RESOURCES.md
-- Official docs:
--   EXPORT MODEL statement: https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-export-model
--   Exporting models:       https://cloud.google.com/bigquery/docs/exporting-models


-- =============================================================================
-- Example 1: Train a small LOGISTIC_REG model to export
-- =============================================================================
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.export_logistic_regression_income`
OPTIONS(
  model_type = 'LOGISTIC_REG',
  input_label_cols = ['income_bracket'],
  auto_class_weights = TRUE
) AS
SELECT
  age, workclass, education, education_num, marital_status, occupation,
  relationship, race, sex, hours_per_week, native_country, income_bracket
FROM `bigquery-public-data.ml_datasets.census_adult_income`;


-- =============================================================================
-- Example 2: EXPORT MODEL — TensorFlow SavedModel (the default format)
-- =============================================================================
-- GLMs, DNNs, KMEANS, PCA, AUTOENCODER, and TRANSFORM_ONLY all export as a
-- TensorFlow SavedModel by default -- no destination_format needed in SQL
-- (the CLI equivalent lets you choose explicitly, see Example 6).
--
-- Verified: the exported signature exposes one named input tensor PER
-- FEATURE COLUMN (not a single packed array) -- e.g. `age`, `workclass`,
-- `education`, ... -- and three named outputs:
-- `{label}_probs`, `{label}_values`, `predicted_{label}`. Categorical
-- vocabularies (education.txt, workclass.txt, ...) are written as
-- separate asset files alongside the graph.
EXPORT MODEL `PROJECT_ID.DATASET.export_logistic_regression_income`
OPTIONS (URI = 'gs://BUCKET/bq_ml/export/logistic_regression/model');


-- =============================================================================
-- Example 3: Train a small BOOSTED_TREE_CLASSIFIER to export
-- =============================================================================
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.export_boosted_tree_income`
OPTIONS(
  model_type = 'BOOSTED_TREE_CLASSIFIER',
  input_label_cols = ['income_bracket'],
  max_iterations = 20
) AS
SELECT
  age, workclass, education, education_num, marital_status, occupation,
  relationship, race, sex, hours_per_week, native_country, income_bracket
FROM `bigquery-public-data.ml_datasets.census_adult_income`;


-- =============================================================================
-- Example 4: EXPORT MODEL — XGBoost Booster (tree ensembles only)
-- =============================================================================
-- BOOSTED_TREE_*/RANDOM_FOREST_* export as an XGBoost Booster (model.bst),
-- not a TensorFlow SavedModel -- the format is chosen by model type, not
-- by an OPTIONS argument in SQL (the bq CLI's --destination_format flag,
-- Example 6, is the only place you choose explicitly).
--
-- GOTCHA (verified, same as models/boosted_tree_classifier/'s tree-viz
-- step): loading this file locally needs xgboost<2.0 pinned (BQML exports
-- using an old XGBoost binary format that modern xgboost 2.0+ cannot
-- read) and feature_names reassigned manually after loading (the export
-- does not preserve them).
EXPORT MODEL `PROJECT_ID.DATASET.export_boosted_tree_income`
OPTIONS (URI = 'gs://BUCKET/bq_ml/export/boosted_tree/model');


-- =============================================================================
-- Example 5: model_registry='VERTEX_AI' — register at CREATE MODEL time
-- =============================================================================
-- An alternative/complement to EXPORT MODEL: register the trained model
-- directly to Vertex AI Model Registry as a side effect of CREATE MODEL --
-- no manual export/upload step, no live serving cost (registry storage
-- only, nothing is deployed to an endpoint yet).
--
-- Verified: `gcloud ai models list` shows the registered model under
-- `vertex_ai_model_id` immediately after CREATE MODEL completes.
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.export_logistic_regression_registry`
OPTIONS(
  model_type = 'LOGISTIC_REG',
  input_label_cols = ['income_bracket'],
  model_registry = 'VERTEX_AI',
  vertex_ai_model_id = 'bq_ml_export_demo_logreg'
) AS
SELECT
  age, workclass, education, education_num, marital_status, occupation,
  relationship, race, sex, hours_per_week, native_country, income_bracket
FROM `bigquery-public-data.ml_datasets.census_adult_income`;


-- =============================================================================
-- Example 6: bq extract --model — the CLI equivalent of EXPORT MODEL
-- =============================================================================
-- Same result as Example 2, run from the shell instead of SQL.
-- --destination_format lets you choose explicitly (ML_TF_SAVED_MODEL is
-- the default; ML_XGBOOST_BOOSTER is the only other option, for tree
-- ensembles).
--   bq extract --model \
--     --destination_format=ML_TF_SAVED_MODEL \
--     PROJECT_ID:DATASET.export_logistic_regression_income \
--     gs://BUCKET/bq_ml/export/cli_extract/model


-- =============================================================================
-- Cleanup
-- =============================================================================
-- DROP MODEL IF EXISTS `PROJECT_ID.DATASET.export_logistic_regression_income`;
-- DROP MODEL IF EXISTS `PROJECT_ID.DATASET.export_boosted_tree_income`;
-- DROP MODEL IF EXISTS `PROJECT_ID.DATASET.export_logistic_regression_registry`;
-- -- Verified: dropping a model that was registered via model_registry='VERTEX_AI'
-- -- also removes its Vertex AI Model Registry entry -- no separate `gcloud ai
-- -- models delete` step needed.
-- (delete the 3 GCS model directories uploaded for this notebook)
