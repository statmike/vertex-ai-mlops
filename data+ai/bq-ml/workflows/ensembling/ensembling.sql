-- Ensembling — BigQuery ML Workflow
-- =============================================================
-- Stacked ensemble combining 3 heterogeneous model types -- LOGISTIC_REG
-- (linear), BOOSTED_TREE_CLASSIFIER (boosting), RANDOM_FOREST_CLASSIFIER
-- (bagging) -- trained on the identical recipe already validated in
-- models/logistic_regression/, models/boosted_tree_classifier/, and
-- models/random_forest_classifier/. Self-contained: retrains its own small
-- copies rather than depending on those notebooks' models still existing
-- (they get dropped by their own Cleanup steps).
--
-- GOTCHA, an improvement over the legacy 03-series notebook this
-- modernizes: uses a 3-way TRAIN/VALIDATE/TEST split, not 2-way. Base
-- models train on TRAIN only; their predictions on VALIDATE (data they
-- never trained on) become the meta-model's training features. This avoids
-- the classic stacking-leakage mistake of training a meta-model on base
-- models' in-sample (TRAIN-split) predictions, which would make the
-- ensemble's apparent lift partly an illusion of overfitting rather than
-- real generalization. TEST is held out from everything until the final
-- comparison.
--
-- GOTCHA: census_adult_income has no natural row-id column, and joining
-- predictions on raw feature columns causes fan-out duplicates (multiple
-- people can share identical feature values) -- verified live: an initial
-- attempt joining on feature columns produced 11,027 rows from a
-- 6,587-row VALIDATE split. Fixed by adding a synthetic ROW_NUMBER() row_id
-- at split-creation time and joining on that instead.
--
-- Data: bigquery-public-data.ml_datasets.census_adult_income (same
--       feature set/label as models/logistic_regression/,
--       models/boosted_tree_classifier/, models/random_forest_classifier/)
--
-- Full reference: ../../RESOURCES.md
-- Official docs:
--   CREATE MODEL: https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create
--   ML.PREDICT:   https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-predict


-- =============================================================================
-- Step 0: 3-way TRAIN/VALIDATE/TEST split (60/20/20) + a stable row_id
-- =============================================================================
CREATE OR REPLACE TABLE `PROJECT_ID.DATASET.ensembling_split` AS
SELECT
  ROW_NUMBER() OVER() AS row_id,
  *,
  CASE
    WHEN MOD(ABS(FARM_FINGERPRINT(TO_JSON_STRING(t))), 10) < 6 THEN 'TRAIN'
    WHEN MOD(ABS(FARM_FINGERPRINT(TO_JSON_STRING(t))), 10) < 8 THEN 'VALIDATE'
    ELSE 'TEST'
  END AS split
FROM `bigquery-public-data.ml_datasets.census_adult_income` t;
-- Verified: TRAIN=19,432 / VALIDATE=6,587 / TEST=6,542 rows, similar
-- positive-class rate (~24%) in each split.


-- =============================================================================
-- Step 1: Train 3 base models on TRAIN only (identical recipes to models/*)
-- =============================================================================
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.ensembling_logistic`
OPTIONS(model_type = 'LOGISTIC_REG', input_label_cols = ['income_bracket'],
        auto_class_weights = TRUE, data_split_method = 'NO_SPLIT') AS
SELECT age, workclass, education, education_num, marital_status, occupation,
       relationship, race, sex, hours_per_week, native_country, income_bracket
FROM `PROJECT_ID.DATASET.ensembling_split` WHERE split = 'TRAIN';

CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.ensembling_boosted`
OPTIONS(model_type = 'BOOSTED_TREE_CLASSIFIER', input_label_cols = ['income_bracket'],
        auto_class_weights = TRUE, data_split_method = 'NO_SPLIT') AS
SELECT age, workclass, education, education_num, marital_status, occupation,
       relationship, race, sex, hours_per_week, native_country, income_bracket
FROM `PROJECT_ID.DATASET.ensembling_split` WHERE split = 'TRAIN';

CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.ensembling_rf`
OPTIONS(model_type = 'RANDOM_FOREST_CLASSIFIER', input_label_cols = ['income_bracket'],
        num_parallel_tree = 50, tree_method = 'HIST', auto_class_weights = TRUE,
        data_split_method = 'NO_SPLIT') AS
SELECT age, workclass, education, education_num, marital_status, occupation,
       relationship, race, sex, hours_per_week, native_country, income_bracket
FROM `PROJECT_ID.DATASET.ensembling_split` WHERE split = 'TRAIN';
-- Submitted concurrently in the notebook (same pattern as
-- workflows/regression_based_forecasting/ and workflows/cross_validation/).


-- =============================================================================
-- Step 2: Meta-features -- predict each base model on VALIDATE, join on row_id
-- =============================================================================
CREATE OR REPLACE TABLE `PROJECT_ID.DATASET.ensembling_meta_features` AS
WITH
logistic_pred AS (
  SELECT row_id, income_bracket,
         (SELECT prob FROM UNNEST(predicted_income_bracket_probs) WHERE label = ' >50K') AS pred_logistic
  FROM ML.PREDICT(MODEL `PROJECT_ID.DATASET.ensembling_logistic`,
    (SELECT * FROM `PROJECT_ID.DATASET.ensembling_split` WHERE split = 'VALIDATE'))
),
boosted_pred AS (
  SELECT row_id,
         (SELECT prob FROM UNNEST(predicted_income_bracket_probs) WHERE label = ' >50K') AS pred_boosted
  FROM ML.PREDICT(MODEL `PROJECT_ID.DATASET.ensembling_boosted`,
    (SELECT * FROM `PROJECT_ID.DATASET.ensembling_split` WHERE split = 'VALIDATE'))
),
rf_pred AS (
  SELECT row_id,
         (SELECT prob FROM UNNEST(predicted_income_bracket_probs) WHERE label = ' >50K') AS pred_rf
  FROM ML.PREDICT(MODEL `PROJECT_ID.DATASET.ensembling_rf`,
    (SELECT * FROM `PROJECT_ID.DATASET.ensembling_split` WHERE split = 'VALIDATE'))
)
SELECT l.row_id, l.income_bracket, l.pred_logistic, b.pred_boosted, r.pred_rf
FROM logistic_pred l
JOIN boosted_pred b USING (row_id)
JOIN rf_pred r USING (row_id);


-- =============================================================================
-- Step 3a: Stacked meta-model -- LOGISTIC_REG trained on VALIDATE's meta-features
-- =============================================================================
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.ensembling_stacker`
OPTIONS(model_type = 'LOGISTIC_REG', input_label_cols = ['income_bracket'],
        auto_class_weights = TRUE, data_split_method = 'NO_SPLIT') AS
SELECT pred_logistic, pred_boosted, pred_rf, income_bracket
FROM `PROJECT_ID.DATASET.ensembling_meta_features`;


-- =============================================================================
-- Step 3b + 4: Final honest comparison on TEST -- 3 base models, simple
-- average ensemble (no training), and the stacked meta-model
-- =============================================================================
CREATE OR REPLACE TABLE `PROJECT_ID.DATASET.ensembling_meta_features_test` AS
WITH
logistic_pred AS (
  SELECT row_id, income_bracket,
         (SELECT prob FROM UNNEST(predicted_income_bracket_probs) WHERE label = ' >50K') AS pred_logistic
  FROM ML.PREDICT(MODEL `PROJECT_ID.DATASET.ensembling_logistic`,
    (SELECT * FROM `PROJECT_ID.DATASET.ensembling_split` WHERE split = 'TEST'))
),
boosted_pred AS (
  SELECT row_id,
         (SELECT prob FROM UNNEST(predicted_income_bracket_probs) WHERE label = ' >50K') AS pred_boosted
  FROM ML.PREDICT(MODEL `PROJECT_ID.DATASET.ensembling_boosted`,
    (SELECT * FROM `PROJECT_ID.DATASET.ensembling_split` WHERE split = 'TEST'))
),
rf_pred AS (
  SELECT row_id,
         (SELECT prob FROM UNNEST(predicted_income_bracket_probs) WHERE label = ' >50K') AS pred_rf
  FROM ML.PREDICT(MODEL `PROJECT_ID.DATASET.ensembling_rf`,
    (SELECT * FROM `PROJECT_ID.DATASET.ensembling_split` WHERE split = 'TEST'))
)
SELECT l.row_id, l.income_bracket, l.pred_logistic, b.pred_boosted, r.pred_rf
FROM logistic_pred l
JOIN boosted_pred b USING (row_id)
JOIN rf_pred r USING (row_id);

-- Base models, each evaluated on TEST:
SELECT 'logistic' AS model, * FROM ML.EVALUATE(MODEL `PROJECT_ID.DATASET.ensembling_logistic`,
  (SELECT * FROM `PROJECT_ID.DATASET.ensembling_split` WHERE split = 'TEST'))
UNION ALL
SELECT 'boosted_tree' AS model, * FROM ML.EVALUATE(MODEL `PROJECT_ID.DATASET.ensembling_boosted`,
  (SELECT * FROM `PROJECT_ID.DATASET.ensembling_split` WHERE split = 'TEST'))
UNION ALL
SELECT 'random_forest' AS model, * FROM ML.EVALUATE(MODEL `PROJECT_ID.DATASET.ensembling_rf`,
  (SELECT * FROM `PROJECT_ID.DATASET.ensembling_split` WHERE split = 'TEST'));
-- Verified (RANDOM_FOREST_CLASSIFIER varies slightly run to run):
-- logistic precision~0.552/recall~0.823/roc_auc~0.891;
-- boosted_tree precision~0.538/recall~0.851/roc_auc~0.893;
-- random_forest precision~0.55-0.57/recall~0.75-0.76/roc_auc~0.884.

-- Simple ensemble (no training) -- average predicted probability, threshold 0.5:
WITH scored AS (
  SELECT income_bracket, (pred_logistic + pred_boosted + pred_rf) / 3 AS pred_avg
  FROM `PROJECT_ID.DATASET.ensembling_meta_features_test`
),
labeled AS (
  SELECT income_bracket = ' >50K' AS actual_positive, pred_avg >= 0.5 AS predicted_positive
  FROM scored
)
SELECT
  COUNTIF(actual_positive AND predicted_positive) AS tp,
  COUNTIF(NOT actual_positive AND predicted_positive) AS fp,
  COUNTIF(actual_positive AND NOT predicted_positive) AS fn,
  COUNTIF(NOT actual_positive AND NOT predicted_positive) AS tn
FROM labeled;
-- Verified: precision~0.56, recall~0.82, accuracy~0.806, f1~0.666
-- (exact TP/FP/FN/TN counts vary slightly run to run along with
-- RANDOM_FOREST_CLASSIFIER's contribution to the average).

-- Stacked meta-model, evaluated on TEST:
SELECT * FROM ML.EVALUATE(MODEL `PROJECT_ID.DATASET.ensembling_stacker`,
  (SELECT pred_logistic, pred_boosted, pred_rf, income_bracket
   FROM `PROJECT_ID.DATASET.ensembling_meta_features_test`));
-- Verified (values vary slightly run to run -- RANDOM_FOREST_CLASSIFIER
-- retraining is non-deterministic, see models/random_forest_classifier/):
-- stacker precision~0.55, recall~0.84, accuracy~0.801, f1~0.665,
-- roc_auc~0.896.
--
-- HONEST FINDING, in two parts since the two ensembling techniques don't
-- agree on which metric wins: (1) the stacked meta-model achieves the
-- HIGHEST roc_auc of all 5 candidates (~0.896 vs. the best individual base
-- model, boosted_tree, at ~0.893) -- a genuine, if modest, ranking-quality
-- win. (2) On F1 (a fixed-threshold metric), the simple-average ensemble
-- edges out the stacker instead (~0.665 vs ~0.663) -- the free, no-training
-- approach is slightly better here, not worse. Neither result is dramatic.
-- Unlike the legacy notebook (whose ensemble did NOT clearly beat its best
-- individual model at all) and several other workflows in this project
-- (recommendation, embeddings_classification) where the simpler baseline
-- won outright, here ensembling helps a little, in a metric-dependent way
-- -- report exactly as measured rather than forcing either narrative.


-- =============================================================================
-- Cleanup
-- =============================================================================
-- DROP MODEL IF EXISTS `PROJECT_ID.DATASET.ensembling_logistic`;
-- DROP MODEL IF EXISTS `PROJECT_ID.DATASET.ensembling_boosted`;
-- DROP MODEL IF EXISTS `PROJECT_ID.DATASET.ensembling_rf`;
-- DROP MODEL IF EXISTS `PROJECT_ID.DATASET.ensembling_stacker`;
-- DROP TABLE IF EXISTS `PROJECT_ID.DATASET.ensembling_split`;
-- DROP TABLE IF EXISTS `PROJECT_ID.DATASET.ensembling_meta_features`;
-- DROP TABLE IF EXISTS `PROJECT_ID.DATASET.ensembling_meta_features_test`;
