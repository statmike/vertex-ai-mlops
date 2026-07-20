-- AutoML Classifier — Progressive SQL Examples (BigQuery ML)
-- =============================================================
-- Binary classification with CREATE MODEL (model_type = 'AUTOML_CLASSIFIER').
-- Wraps Vertex AI AutoML Tables: architecture search, feature engineering,
-- and hyperparameter tuning all happen inside the Vertex AI training job --
-- you supply data and a time budget, not model structure.
--
-- Data: bigquery-public-data.ml_datasets.census_adult_income
--       Label: income_bracket ('<=50K' / '>50K')
--       (same data/label as models/logistic_regression/, .../boosted_tree_classifier/,
--       .../random_forest_classifier/, .../dnn_classifier/, .../wide_and_deep_classifier/)
--
-- COST/TIME WARNING: unlike every other model type in this project, this one
-- has real, substantial dollar cost and wall-clock time. Vertex AI AutoML
-- Tabular training is billed at roughly $21.25/node-hour; budget_hours = 1.0
-- (the minimum) is the cheapest possible run. VERIFIED on a real run: wall-
-- clock was 2.63 hours (ML.TRAINING_INFO duration_ms=9,475,200) for a 1-hour
-- budget -- a much larger overrun than the ~50% ceiling Google's docs imply.
-- Do not re-run CREATE MODEL casually.
--
-- Full reference: ../../RESOURCES.md
-- Official docs:
--   CREATE MODEL (AutoML): https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-automl
--   Vertex AI AutoML Tabular pricing: https://cloud.google.com/vertex-ai/pricing


-- =============================================================================
-- Example 1: CREATE MODEL — train an AutoML Tables classifier
-- =============================================================================
-- model_type + input_label_cols are the essentials, same as any other model
-- type. budget_hours is AutoML's one user-facing tuning knob -- there is no
-- NUM_TRIALS / HPARAM_RANGE here; AutoML searches architectures internally.
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.automl_classifier_income`
OPTIONS(
  model_type = 'AUTOML_CLASSIFIER',
  input_label_cols = ['income_bracket'],
  budget_hours = 1.0,
  optimization_objective = 'MAXIMIZE_AU_ROC'
) AS
SELECT
  age, workclass, education, education_num, marital_status, occupation,
  relationship, race, sex, hours_per_week, native_country, income_bracket
FROM `bigquery-public-data.ml_datasets.census_adult_income`;


-- =============================================================================
-- Example 2: ML.EVALUATE — classification metrics
-- =============================================================================
-- Same metric set as LOGISTIC_REG/BOOSTED_TREE_CLASSIFIER/etc: precision,
-- recall, accuracy, f1_score, log_loss, roc_auc -- computed by AutoML on its
-- own internal test split.
--
-- GOTCHA (verified): the zero-argument form's "accuracy" is not a literal,
-- reconcilable confusion-matrix accuracy for this model type. A real run
-- returned accuracy=0.5 exactly alongside roc_auc=0.930. The model's own
-- metadata (bq show --model) confirms evaluation ran against a
-- class-balanced ~6,416-row internal eval set (3,208 per class, not the
-- natural ~76/24 income_bracket split), but accuracy=0.5/precision=0.531/
-- recall=0.509 do not match ANY of the model's 203 confidence-threshold rows
-- in binaryConfusionMatrixList (whose accuracy ranges 0.5-0.845; the literal
-- threshold=0.5 row shows accuracy=0.844, not 0.5). The exact Vertex AI
-- methodology behind this aggregate isn't visible from BigQuery's side.
-- Passing an explicit data argument sidesteps the ambiguity: evaluating
-- against the model's own training table returns a standard, self-consistent
-- accuracy=0.8508, matching a directly-computed confusion matrix exactly
-- (27,703 correct / 32,561 total). Prefer roc_auc/log_loss (threshold-
-- independent) or an explicit-data-argument call for this model type.
SELECT *
FROM ML.EVALUATE(MODEL `PROJECT_ID.DATASET.automl_classifier_income`);


-- =============================================================================
-- Example 3: ML.CONFUSION_MATRIX and ML.ROC_CURVE
-- =============================================================================
-- GOTCHA (verified): the zero-argument form ML.CONFUSION_MATRIX(MODEL ...) --
-- which works fine for ML.EVALUATE/ML.ROC_CURVE, and relies on AutoML's own
-- internal held-out eval split -- fails immediately and consistently for
-- this model type with a generic internal error ("Error: 21631273", claims
-- to be transient but is not: it reproduces on every attempt). The
-- google-cloud-bigquery client's default retry logic treats this as
-- retryable and keeps resubmitting with exponential backoff, so a
-- client.query(...).result() call on it appears to hang rather than fail
-- fast. Fix: pass an explicit data argument instead.
SELECT *
FROM ML.CONFUSION_MATRIX(
  MODEL `PROJECT_ID.DATASET.automl_classifier_income`,
  (SELECT age, workclass, education, education_num, marital_status, occupation,
          relationship, race, sex, hours_per_week, native_country, income_bracket
   FROM `bigquery-public-data.ml_datasets.census_adult_income`)
);

-- ML.ROC_CURVE's zero-argument form works fine on the same model.
SELECT threshold, recall, false_positive_rate
FROM ML.ROC_CURVE(MODEL `PROJECT_ID.DATASET.automl_classifier_income`)
ORDER BY threshold;


-- =============================================================================
-- Example 4: ML.PREDICT
-- =============================================================================
SELECT
  predicted_income_bracket,
  predicted_income_bracket_probs,
  age, occupation, education
FROM ML.PREDICT(
  MODEL `PROJECT_ID.DATASET.automl_classifier_income`,
  (SELECT * FROM `bigquery-public-data.ml_datasets.census_adult_income` LIMIT 10)
);


-- =============================================================================
-- Example 5: ML.GLOBAL_EXPLAIN — model-level feature attributions
-- =============================================================================
-- Unlike LOGISTIC_REG/BOOSTED_TREE_*, no enable_global_explain option is
-- needed -- AutoML produces attributions automatically. Only model-level
-- (not per-prediction) explanations are available: ML.EXPLAIN_PREDICT is
-- NOT supported for this model type (see Example 8).
SELECT *
FROM ML.GLOBAL_EXPLAIN(MODEL `PROJECT_ID.DATASET.automl_classifier_income`)
ORDER BY attribution DESC;


-- =============================================================================
-- Example 6: ML.FEATURE_INFO and ML.TRAINING_INFO
-- =============================================================================
SELECT *
FROM ML.FEATURE_INFO(MODEL `PROJECT_ID.DATASET.automl_classifier_income`);

SELECT *
FROM ML.TRAINING_INFO(MODEL `PROJECT_ID.DATASET.automl_classifier_income`);


-- =============================================================================
-- Example 7: EXPORT MODEL
-- =============================================================================
-- Writes the trained AutoML model to Cloud Storage for Vertex AI Model
-- Registry / custom serving. Unlike BOOSTED_TREE_*/RANDOM_FOREST_*, AutoML's
-- exported artifact is an opaque ensemble -- there is no single tree/booster
-- file to load and visualize with a local library.
EXPORT MODEL `PROJECT_ID.DATASET.automl_classifier_income`
OPTIONS (URI = 'gs://BUCKET/bq_ml/automl_classifier/model');


-- =============================================================================
-- Example 8: Functions that do NOT apply to this model type
-- =============================================================================
-- TRANSFORM is not supported for AutoML model types -- do feature
-- engineering in the training SELECT instead.
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.automl_classifier_income_transform`
TRANSFORM(age, income_bracket)
OPTIONS(
  model_type = 'AUTOML_CLASSIFIER',
  input_label_cols = ['income_bracket'],
  budget_hours = 1.0
) AS
SELECT age, income_bracket
FROM `bigquery-public-data.ml_datasets.census_adult_income`;

-- ML.WEIGHTS / ML.ADVANCED_WEIGHTS do not apply -- AutoML is not a single
-- linear/tree model with an exposable weight vector.
SELECT *
FROM ML.WEIGHTS(MODEL `PROJECT_ID.DATASET.automl_classifier_income`);

-- ML.EXPLAIN_PREDICT does not apply -- use ML.GLOBAL_EXPLAIN (Example 5)
-- for feature attributions instead.
SELECT *
FROM ML.EXPLAIN_PREDICT(
  MODEL `PROJECT_ID.DATASET.automl_classifier_income`,
  (SELECT * FROM `bigquery-public-data.ml_datasets.census_adult_income` LIMIT 5)
);

-- User-configurable hyperparameter tuning (num_trials/HPARAM_RANGE/
-- HPARAM_CANDIDATES) is also not supported -- budget_hours is the only lever.
