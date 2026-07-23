-- Customer Segmentation — BigQuery ML Workflow
-- =============================================================
-- RFM (Recency/Frequency/Monetary) feature engineering from raw order
-- history, then KMEANS clustering to segment customers into actionable
-- business groups. Contrast with models/kmeans/'s penguins mechanism demo:
-- this is the real business-clustering version, on real e-commerce order
-- data with a genuine "what do we do about each segment" payoff.
--
-- Data: bigquery-public-data.thelook_ecommerce (orders, order_items) --
--       real e-commerce order history, ~28K customers with orders before
--       a fixed 2024-01-01 analysis cutoff (kept fixed so results don't
--       shift every time this notebook is re-run in the future).
--
-- Full reference: ../../RESOURCES.md
-- Official docs:
--   CREATE MODEL (KMEANS): https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-kmeans
--   ML.CENTROIDS:          https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-centroids


-- =============================================================================
-- Step 1: RFM feature engineering from raw order history
-- =============================================================================
CREATE OR REPLACE TABLE `PROJECT_ID.DATASET.customer_segmentation_rfm` AS
WITH order_value AS (
  SELECT order_id, user_id, SUM(sale_price) AS order_total
  FROM `bigquery-public-data.thelook_ecommerce.order_items`
  GROUP BY order_id, user_id
)
SELECT
  o.user_id,
  DATE_DIFF(DATE '2024-01-01', MAX(DATE(o.created_at)), DAY) AS recency_days,
  COUNT(DISTINCT o.order_id) AS frequency,
  SUM(ov.order_total) AS monetary
FROM `bigquery-public-data.thelook_ecommerce.orders` o
JOIN order_value ov USING (order_id, user_id)
WHERE o.created_at < '2024-01-01'
GROUP BY o.user_id;
-- Verified: ~27,700 customers, avg ~1.3 orders/customer, avg recency ~493
-- days -- most customers in this dataset order rarely, which is exactly
-- the kind of pattern RFM segmentation is meant to surface.


-- =============================================================================
-- Step 2: KMEANS on standardized RFM features (raw scale would let monetary,
-- which ranges into the thousands, dominate distance calculations)
-- =============================================================================
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.customer_segmentation_kmeans`
TRANSFORM(
  ML.STANDARD_SCALER(recency_days) OVER() AS recency_scaled,
  ML.STANDARD_SCALER(frequency) OVER() AS frequency_scaled,
  ML.STANDARD_SCALER(monetary) OVER() AS monetary_scaled
)
OPTIONS(model_type = 'KMEANS', num_clusters = 4, kmeans_init_method = 'KMEANS++') AS
SELECT recency_days, frequency, monetary
FROM `PROJECT_ID.DATASET.customer_segmentation_rfm`;
-- GOTCHA (same lesson as models/kmeans/): user_id must NOT be in the
-- TRAINING query/TRANSFORM -- it would become a raw, unscaled feature that
-- badly distorts every distance calculation (verified live: this was
-- caught during pre-validation). Keep the training query to feature
-- columns only; join user_id back via ML.PREDICT afterward instead.


-- =============================================================================
-- Step 3: ML.EVALUATE + ML.CENTROIDS -- inspect the fitted segments
-- =============================================================================
SELECT * FROM ML.EVALUATE(MODEL `PROJECT_ID.DATASET.customer_segmentation_kmeans`);

SELECT centroid_id, feature, numerical_value
FROM ML.CENTROIDS(MODEL `PROJECT_ID.DATASET.customer_segmentation_kmeans`)
ORDER BY centroid_id, feature;


-- =============================================================================
-- Step 4: ML.PREDICT on the full RFM table, aggregate to real segment profiles
-- =============================================================================
SELECT
  CENTROID_ID,
  COUNT(*) AS n_customers,
  ROUND(AVG(recency_days)) AS avg_recency_days,
  ROUND(AVG(frequency), 2) AS avg_frequency,
  ROUND(AVG(monetary), 2) AS avg_monetary
FROM ML.PREDICT(
  MODEL `PROJECT_ID.DATASET.customer_segmentation_kmeans`,
  TABLE `PROJECT_ID.DATASET.customer_segmentation_rfm`
)
GROUP BY CENTROID_ID
ORDER BY CENTROID_ID;
-- Verified live, 4 real, interpretable segments (exact centroid numbering
-- and precise values vary run to run -- KMEANS is non-deterministic, see
-- models/kmeans/ -- always read the actual numbers from YOUR OWN output,
-- not from this comment. This shape is the reproducible finding, observed
-- consistently across THREE independent retrainings):
--   ~50-53% of customers, best recency, ~1.0 orders, ~$74-77  avg -- recent, low-value (the majority)
--   ~19-27% of customers, worst recency (~1000+ days),  ~1.0 orders, ~$80-85  avg -- lapsed / lost
--   ~17-19% of customers, good recency, high frequency (~2.2-2.25 orders), ~$141-157 avg -- loyal regulars
--   ~5-6%   of customers, moderate recency, above-avg frequency, highest spend (~$450-483) avg -- champions


-- =============================================================================
-- Cleanup
-- =============================================================================
-- DROP MODEL IF EXISTS `PROJECT_ID.DATASET.customer_segmentation_kmeans`;
-- DROP TABLE IF EXISTS `PROJECT_ID.DATASET.customer_segmentation_rfm`;
