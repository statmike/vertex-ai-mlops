-- Churn / Retention — BigQuery ML Workflow
-- =============================================================
-- Define churn from real order-history gaps (not a synthetic label), engineer
-- features, train a BOOSTED_TREE_CLASSIFIER, evaluate honestly (including a
-- metric-literacy lesson -- richer features barely move ROC AUC despite
-- clearly improving accuracy/F1/recall), then explain drivers. Reuses
-- workflows/customer_segmentation/'s dataset for narrative continuity.
--
-- Data: bigquery-public-data.thelook_ecommerce (orders, order_items, users)
--
-- Full reference: ../../RESOURCES.md
-- Official docs:
--   CREATE MODEL (BOOSTED_TREE_CLASSIFIER): https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-boosted-tree
--   ML.GLOBAL_EXPLAIN: https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-global-explain
--   ML.EXPLAIN_PREDICT: https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-explain-predict


-- =============================================================================
-- Step 1: Define churn from a fixed feature cutoff + forward label window
-- =============================================================================
-- Feature cutoff: 2024-01-01 (matches workflows/customer_segmentation/).
-- Label window: the following 180 days (through 2024-06-29). A customer who
-- ordered before the cutoff but placed NO order in the label window is
-- labeled churned=TRUE. Both dates are far enough in the past that this is
-- real observed history, not a synthetic/simulated forward projection.
CREATE OR REPLACE TABLE `PROJECT_ID.DATASET.churn_retention_features` AS
WITH order_value AS (
  SELECT order_id, user_id, SUM(sale_price) AS order_total,
         COUNT(DISTINCT product_id) AS n_products,
         MAX(CASE WHEN returned_at IS NOT NULL THEN 1 ELSE 0 END) AS had_return
  FROM `bigquery-public-data.thelook_ecommerce.order_items`
  GROUP BY order_id, user_id
),
rfm AS (
  SELECT
    o.user_id,
    DATE_DIFF(DATE '2024-01-01', MAX(DATE(o.created_at)), DAY) AS recency_days,
    COUNT(DISTINCT o.order_id) AS frequency,
    SUM(ov.order_total) AS monetary,
    SUM(ov.order_total) / COUNT(DISTINCT o.order_id) AS avg_order_value,
    SUM(ov.n_products) AS distinct_products,
    AVG(ov.had_return) AS return_rate
  FROM `bigquery-public-data.thelook_ecommerce.orders` o
  JOIN order_value ov USING (order_id, user_id)
  WHERE o.created_at < '2024-01-01'
  GROUP BY o.user_id
),
future_activity AS (
  SELECT DISTINCT user_id
  FROM `bigquery-public-data.thelook_ecommerce.orders`
  WHERE created_at >= '2024-01-01' AND created_at < '2024-06-29'
)
SELECT
  r.*, u.age, u.gender, u.traffic_source,
  DATE_DIFF(DATE '2024-01-01', DATE(u.created_at), DAY) AS tenure_days,
  fa.user_id IS NULL AS churned
FROM rfm r
JOIN `bigquery-public-data.thelook_ecommerce.users` u ON r.user_id = u.id
LEFT JOIN future_activity fa USING (user_id);
-- Verified: 27,716 customers, 25,280 churned (91.2%) / 2,436 retained (8.8%).
-- The extreme imbalance is itself a real finding for this dataset: most
-- customers never place a second order regardless of features.


-- =============================================================================
-- Step 2: Baseline -- BOOSTED_TREE_CLASSIFIER on RFM features alone
-- =============================================================================
-- auto_class_weights = TRUE: with a 91% base churn rate, a model that always
-- predicts "churned" gets 91% accuracy while being useless -- class
-- weighting forces the model to actually learn the minority (retained) class.
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.churn_retention_baseline`
OPTIONS(
  model_type = 'BOOSTED_TREE_CLASSIFIER',
  input_label_cols = ['churned'],
  auto_class_weights = TRUE,
  data_split_method = 'AUTO_SPLIT',
  enable_global_explain = TRUE
) AS
SELECT recency_days, frequency, monetary, churned
FROM `PROJECT_ID.DATASET.churn_retention_features`;

SELECT * FROM ML.EVALUATE(MODEL `PROJECT_ID.DATASET.churn_retention_baseline`);
-- Verified: accuracy 0.493, precision 0.922, recall 0.485, f1 0.635,
-- roc_auc 0.531 -- barely above random (0.5). RFM alone, from a single
-- snapshot, does not meaningfully separate churners from retained customers
-- in this dataset.


-- =============================================================================
-- Step 3: Richer feature engineering -- behavior + demographics
-- =============================================================================
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.churn_retention_model`
OPTIONS(
  model_type = 'BOOSTED_TREE_CLASSIFIER',
  input_label_cols = ['churned'],
  auto_class_weights = TRUE,
  data_split_method = 'AUTO_SPLIT',
  enable_global_explain = TRUE
) AS
SELECT recency_days, frequency, monetary, avg_order_value, distinct_products,
       return_rate, age, gender, traffic_source, tenure_days, churned
FROM `PROJECT_ID.DATASET.churn_retention_features`;

SELECT * FROM ML.EVALUATE(MODEL `PROJECT_ID.DATASET.churn_retention_model`);
-- Verified: accuracy 0.597, precision 0.929, recall 0.605, f1 0.733,
-- roc_auc 0.544. HONEST FINDING: accuracy/recall/F1 improve meaningfully
-- with richer features, but roc_auc barely moves (0.531 -> 0.544) -- not a
-- contradiction: roc_auc measures ranking quality across every threshold,
-- while accuracy/recall/F1 are read off a single fixed 0.5 cutoff. Richer
-- features shifted predicted probabilities relative to 0.5 without much
-- improving how well the model ranks churners above non-churners overall.
-- This synthetic e-commerce generator simply does not encode a strong
-- individual-level churn signal. A real production churn model would need
-- richer behavioral signal (browsing/session data, email engagement,
-- support tickets) than a raw transaction history alone provides.
--
-- ML.CONFUSION_MATRIX (expected_label=true row: FALSE=1997, TRUE=3059)
-- confirms recall=3059/5056=0.605 is recall on the CHURNED class (TRUE) --
-- not the retained class -- exactly matching ML.EVALUATE.


-- =============================================================================
-- Step 4: ML.GLOBAL_EXPLAIN + ML.FEATURE_IMPORTANCE -- what drives the model
-- =============================================================================
SELECT * FROM ML.GLOBAL_EXPLAIN(MODEL `PROJECT_ID.DATASET.churn_retention_model`)
ORDER BY attribution DESC;
-- Verified: tenure_days is the dominant driver (attribution 0.072), then
-- frequency (0.028), recency_days (0.015), age (0.015) -- account age
-- matters more than any single RFM feature.

SELECT * FROM ML.FEATURE_IMPORTANCE(MODEL `PROJECT_ID.DATASET.churn_retention_model`)
ORDER BY importance_gain DESC;
-- Verified: this ranking (by importance_gain) does NOT match GLOBAL_EXPLAIN's
-- (by attribution) -- return_rate is 8th-of-9 by attribution but 3rd by
-- gain. Different questions: gain = how useful a feature is WHEN the tree
-- splits on it (a rarely-used feature can still have high average gain);
-- attribution = a feature's typical contribution across all predictions,
-- split frequency included. Neither ranking is "more correct."


-- =============================================================================
-- Step 5: ML.EXPLAIN_PREDICT -- per-customer driver attribution
-- =============================================================================
SELECT
  predicted_churned,
  top_feature_attributions
FROM ML.EXPLAIN_PREDICT(
  MODEL `PROJECT_ID.DATASET.churn_retention_model`,
  (SELECT * FROM `PROJECT_ID.DATASET.churn_retention_features` LIMIT 5),
  STRUCT(3 AS top_k_features)
);


-- =============================================================================
-- Step 6: Tie back to customer_segmentation -- does being a frequent/high-
-- value customer actually reduce churn risk in this dataset? (order count is
-- a simple proxy for segmentation's KMEANS segments, which are driven jointly
-- by recency/frequency/monetary -- not identical to a hard frequency cutoff)
-- =============================================================================
SELECT
  CASE WHEN frequency = 1 THEN '1 order' ELSE '2+ orders' END AS frequency_group,
  COUNT(*) AS n_customers,
  ROUND(AVG(CAST(churned AS INT64)), 3) AS churn_rate
FROM `PROJECT_ID.DATASET.churn_retention_features`
GROUP BY frequency_group
ORDER BY frequency_group;
-- Verified: 1-order customers churn at 91.6%; 2+ order customers (the
-- "loyal regulars"/"champions" segments from customer_segmentation) still
-- churn at 90.0% -- barely lower. A genuinely useful, slightly deflating
-- finding: in this dataset, being a repeat/high-value customer does not
-- meaningfully protect against churn, which helps explain why the
-- classifier's roc_auc stays low even with richer features.


-- =============================================================================
-- Cleanup
-- =============================================================================
-- DROP MODEL IF EXISTS `PROJECT_ID.DATASET.churn_retention_baseline`;
-- DROP MODEL IF EXISTS `PROJECT_ID.DATASET.churn_retention_model`;
-- DROP TABLE IF EXISTS `PROJECT_ID.DATASET.churn_retention_features`;
