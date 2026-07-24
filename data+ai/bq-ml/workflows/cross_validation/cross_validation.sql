-- Cross-Validation — BigQuery ML Workflow
-- =============================================================
-- BigQuery ML has NO native k-fold cross-validation -- CREATE MODEL's
-- data_split_method only supports single-split holdout (AUTO_SPLIT, RANDOM,
-- CUSTOM, SEQ, NO_SPLIT). Hand-roll k-fold with deterministic hash-based
-- fold assignment, train k LOGISTIC_REG models submitted concurrently, and
-- compare per-fold metric variance against a same-model-type single holdout.
--
-- Motivating problem, reused from workflows/anomaly_fraud_detection/: that
-- workflow's supervised BOOSTED_TREE_CLASSIFIER had a held-out eval split
-- with only ~15 real fraud cases (ML.CONFUSION_MATRIX: TP=13, FN=2) -- a
-- metric estimated from just 15 positive examples is exactly the kind of
-- high-variance situation cross-validation exists to quantify.
--
-- Data: bigquery-public-data.ml_datasets.ulb_fraud_detection (same as
--       workflows/anomaly_fraud_detection/)
--
-- Full reference: ../../RESOURCES.md
-- Official docs:
--   CREATE MODEL: https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create
--   ML.EVALUATE:  https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-evaluate


-- =============================================================================
-- Step 1: Deterministic fold assignment -- 5 folds via FARM_FINGERPRINT hashing
-- =============================================================================
-- ulb_fraud_detection has no natural row-id column -- hash the full row via
-- TO_JSON_STRING for a stable, deterministic fold assignment.
CREATE OR REPLACE TABLE `PROJECT_ID.DATASET.cross_validation_folds` AS
SELECT
  *,
  MOD(ABS(FARM_FINGERPRINT(TO_JSON_STRING(t))), 5) AS fold
FROM `bigquery-public-data.ml_datasets.ulb_fraud_detection` t;
-- Verified: 5 folds, ~56.7K-57.2K rows each, 81-111 real fraud cases per
-- fold (out of 492 total) -- the fold-to-fold fraud-count spread (81 vs
-- 111, nearly 40% relative difference) is itself a first hint of why a
-- single split's estimate can be noisy for a rare-event problem.


-- =============================================================================
-- Step 2: Train 5 per-fold LOGISTIC_REG models (submit concurrently)
-- =============================================================================
-- Each fold model trains on every row EXCEPT its own fold (NO_SPLIT since
-- fold assignment is manual, not BQML's own split). Submit all 5
-- CREATE MODEL statements without waiting, then wait for all -- BigQuery
-- runs distinctly-named CREATE MODEL jobs from one client in true parallel
-- (same pattern verified in workflows/regression_based_forecasting/).
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.cross_validation_fold_0`
OPTIONS(model_type = 'LOGISTIC_REG', input_label_cols = ['Class'],
        auto_class_weights = TRUE, data_split_method = 'NO_SPLIT') AS
SELECT * EXCEPT(fold) FROM `PROJECT_ID.DATASET.cross_validation_folds` WHERE fold != 0;
-- ... repeat for fold_1 .. fold_4 (WHERE fold != 1, != 2, != 3, != 4) --
-- see the notebook for concurrent job submission.


-- =============================================================================
-- Step 3: Per-fold ML.EVALUATE against each held-out fold, UNION ALL
-- =============================================================================
SELECT 0 AS fold, * FROM ML.EVALUATE(MODEL `PROJECT_ID.DATASET.cross_validation_fold_0`,
  (SELECT * EXCEPT(fold) FROM `PROJECT_ID.DATASET.cross_validation_folds` WHERE fold = 0))
UNION ALL
SELECT 1 AS fold, * FROM ML.EVALUATE(MODEL `PROJECT_ID.DATASET.cross_validation_fold_1`,
  (SELECT * EXCEPT(fold) FROM `PROJECT_ID.DATASET.cross_validation_folds` WHERE fold = 1))
UNION ALL
SELECT 2 AS fold, * FROM ML.EVALUATE(MODEL `PROJECT_ID.DATASET.cross_validation_fold_2`,
  (SELECT * EXCEPT(fold) FROM `PROJECT_ID.DATASET.cross_validation_folds` WHERE fold = 2))
UNION ALL
SELECT 3 AS fold, * FROM ML.EVALUATE(MODEL `PROJECT_ID.DATASET.cross_validation_fold_3`,
  (SELECT * EXCEPT(fold) FROM `PROJECT_ID.DATASET.cross_validation_folds` WHERE fold = 3))
UNION ALL
SELECT 4 AS fold, * FROM ML.EVALUATE(MODEL `PROJECT_ID.DATASET.cross_validation_fold_4`,
  (SELECT * EXCEPT(fold) FROM `PROJECT_ID.DATASET.cross_validation_folds` WHERE fold = 4))
ORDER BY fold;
-- Verified real spread across folds: precision 0.068-0.099, recall
-- 0.847-0.932, roc_auc 0.968-0.985 -- meaningful fold-to-fold variance on
-- every metric, from the exact same modeling recipe applied to 5 different
-- 80%-of-data training sets.


-- =============================================================================
-- Step 4: Aggregate (mean +/- stddev) vs. a same-model-type single holdout
-- =============================================================================
-- (aggregate the Step 3 result with AVG/STDDEV per metric)

-- A single random 80/20 holdout, same model type/options, for a fair,
-- controlled comparison (NOT a cross-model comparison against
-- anomaly_fraud_detection's BOOSTED_TREE_CLASSIFIER -- that would confound
-- model choice with sampling variance).
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.cross_validation_single_holdout`
OPTIONS(model_type = 'LOGISTIC_REG', input_label_cols = ['Class'],
        auto_class_weights = TRUE, data_split_method = 'RANDOM',
        data_split_eval_fraction = 0.2) AS
SELECT * EXCEPT(fold) FROM `PROJECT_ID.DATASET.cross_validation_folds`;

SELECT * FROM ML.EVALUATE(MODEL `PROJECT_ID.DATASET.cross_validation_single_holdout`);
-- Verified: precision=0.089, recall=0.893, roc_auc=0.974. 5-fold mean+-std:
-- precision 0.083+-0.014, recall 0.901+-0.030, roc_auc 0.980+-0.007. The
-- single holdout's precision/recall land close to their fold means; its
-- roc_auc lands on the low side (~1 stddev below the fold mean) -- a real,
-- honest illustration that even a single holdout that "looks fine" carries
-- meaningful uncertainty a single number can't reveal on its own.


-- =============================================================================
-- Cleanup
-- =============================================================================
-- DROP MODEL IF EXISTS `PROJECT_ID.DATASET.cross_validation_fold_0`; (repeat through fold_4)
-- DROP MODEL IF EXISTS `PROJECT_ID.DATASET.cross_validation_single_holdout`;
-- DROP TABLE IF EXISTS `PROJECT_ID.DATASET.cross_validation_folds`;
