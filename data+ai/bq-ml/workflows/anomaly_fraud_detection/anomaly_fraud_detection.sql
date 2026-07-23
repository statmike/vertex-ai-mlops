-- Anomaly / Fraud Detection — BigQuery ML Workflow
-- =============================================================
-- The real ground-truth validation the 5 existing ML.DETECT_ANOMALIES demos
-- (models/kmeans/, models/pca/, models/autoencoder/, models/arima_plus/,
-- models/arima_plus_xreg/) all lack: a dataset with genuine labeled fraud.
-- Trains unsupervised detection (PCA, then AUTOENCODER) on features only (no
-- Class label), scores with ML.DETECT_ANOMALIES, and evaluates real
-- precision/recall against the Class label -- then contrasts with a
-- supervised BOOSTED_TREE_CLASSIFIER trained WITH the label.
--
-- GOTCHA this is row-level anomaly detection within one dataset -- distinct
-- from functions/data_quality/'s ML.VALIDATE_DATA_SKEW/DRIFT, which compare
-- whole datasets/time windows to each other (dataset-level distribution
-- shift). Different concept, similar-sounding name.
--
-- Data: bigquery-public-data.ml_datasets.ulb_fraud_detection (the classic
--       ULB/Kaggle credit-card-fraud dataset -- 284,807 rows, 492 real
--       fraud cases (0.17%), Time/V1-V28 (already PCA-anonymized by the
--       original data providers)/Amount/Class).
--
-- Full reference: ../../RESOURCES.md
-- Official docs:
--   ML.DETECT_ANOMALIES: https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-detect-anomalies


-- =============================================================================
-- Step 1: Unsupervised PCA -- train on features only, no Class label
-- =============================================================================
-- MAJOR GOTCHA (verified live, new finding -- refines RESOURCES.md's "PCA is
-- fully deterministic" claim): training with pca_explained_variance_ratio
-- (a variable component COUNT, chosen to hit a variance target) produced
-- wildly different ML.DETECT_ANOMALIES results across otherwise-identical
-- retrainings -- TP counts of 3, 235, and 279 (out of 492 real frauds)
-- across three separate `CREATE OR REPLACE MODEL` runs of the EXACT same
-- statement -- even though ML.EVALUATE's total_explained_variance_ratio was
-- bit-for-bit stable (~0.95473) every time. Near-threshold eigenvalues can
-- flip which exact components get retained between runs, which swings
-- per-row reconstruction error dramatically even though the aggregate
-- variance captured looks identical. FIX: use a FIXED num_principal_components
-- instead -- substantially more stable (though not perfectly bit-for-bit)
-- across retrainings, verified with two independent runs both landing in
-- the TP=114-124 range.
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.anomaly_fraud_pca`
OPTIONS(
  model_type = 'PCA',
  num_principal_components = 10,
  scale_features = TRUE
) AS
SELECT * EXCEPT(Class)
FROM `bigquery-public-data.ml_datasets.ulb_fraud_detection`;

-- Score with the TRUE fraud rate as contamination (an "oracle" choice --
-- in a real scenario you wouldn't know this in advance, but it isolates
-- the method's ceiling performance from the guesswork of picking contamination).
SELECT is_anomaly, Class, COUNT(*) AS n
FROM ML.DETECT_ANOMALIES(
  MODEL `PROJECT_ID.DATASET.anomaly_fraud_pca`,
  STRUCT(0.001727 AS contamination),
  (SELECT * FROM `bigquery-public-data.ml_datasets.ulb_fraud_detection`)
)
GROUP BY is_anomaly, Class
ORDER BY is_anomaly DESC, Class;
-- Verified (num_principal_components=10, across independent runs):
-- TP~114-132, precision ~20-24%, recall ~23-27%. Modest but real signal --
-- and far more reproducible than the pca_explained_variance_ratio mode above.


-- =============================================================================
-- Step 2: Unsupervised AUTOENCODER -- same features, a nonlinear method
-- =============================================================================
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.anomaly_fraud_autoencoder`
OPTIONS(
  model_type = 'AUTOENCODER',
  hidden_units = [16, 8, 16],
  activation_fn = 'RELU',
  batch_size = 512,
  max_iterations = 10
) AS
SELECT * EXCEPT(Class)
FROM `bigquery-public-data.ml_datasets.ulb_fraud_detection`;

SELECT is_anomaly, Class, COUNT(*) AS n
FROM ML.DETECT_ANOMALIES(
  MODEL `PROJECT_ID.DATASET.anomaly_fraud_autoencoder`,
  STRUCT(0.001727 AS contamination),
  (SELECT * FROM `bigquery-public-data.ml_datasets.ulb_fraud_detection`)
)
GROUP BY is_anomaly, Class
ORDER BY is_anomaly DESC, Class;
-- Verified: TP~132-145 across runs -- precision ~23-26%, recall ~27-29%.
-- Comparable to PCA's stabilized (num_principal_components) result, not
-- dramatically better -- on this already-decorrelated feature set (V1-V28
-- are themselves PCA outputs from the original data providers), the
-- nonlinear autoencoder doesn't have an obvious edge over well-configured
-- PCA. AUTOENCODER retraining is itself non-deterministic (see
-- models/autoencoder/), same caveat as PCA above.


-- =============================================================================
-- Step 3: Supervised BOOSTED_TREE_CLASSIFIER -- trained WITH the Class label
-- =============================================================================
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.anomaly_fraud_supervised`
OPTIONS(
  model_type = 'BOOSTED_TREE_CLASSIFIER',
  input_label_cols = ['Class'],
  auto_class_weights = TRUE,
  data_split_method = 'AUTO_SPLIT'
) AS
SELECT *
FROM `bigquery-public-data.ml_datasets.ulb_fraud_detection`;

SELECT * FROM ML.EVALUATE(MODEL `PROJECT_ID.DATASET.anomaly_fraud_supervised`);
-- Verified (on the automatic held-out eval split): precision 0.271,
-- recall 0.867, roc_auc 0.966. HONEST COMPARISON NOTE: this is evaluated
-- on a held-out split (~15 real fraud cases), while Steps 1-2 scored the
-- FULL dataset (unsupervised methods have no train/test split concern
-- since they never see labels) -- the populations aren't identically
-- sized, but the takeaway is directionally clear and large: recall triples
-- (29% -> 87%) when you have labels to train directly on the exact fraud
-- pattern you're trying to catch.


-- =============================================================================
-- Cleanup
-- =============================================================================
-- DROP MODEL IF EXISTS `PROJECT_ID.DATASET.anomaly_fraud_pca`;
-- DROP MODEL IF EXISTS `PROJECT_ID.DATASET.anomaly_fraud_autoencoder`;
-- DROP MODEL IF EXISTS `PROJECT_ID.DATASET.anomaly_fraud_supervised`;
