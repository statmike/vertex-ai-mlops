-- Feature Store Workflow — What Point-in-Time Correctness Is Actually Worth
-- =============================================================
-- A controlled, two-arm measurement of label leakage on thelook_ecommerce.
-- One feature history, two ways of querying it, one shared deterministic
-- split, and the question that actually matters at the end: what does the
-- leaky model do when production hands it the only features it can have?
--
--   Arm A  aggregate each customer's WHOLE history with GROUP BY entity_id
--          and join it to every training row.               <- the mistake
--   Arm B  retrieve each customer's vector as of THAT ORDER's timestamp with
--          ML.ENTITY_FEATURES_AT_TIME.                      <- correct
--
-- Prediction problem one training row per order, features as of the instant
-- the order was placed, label "did this customer order again within 90 days?"
--
-- HEADLINE, all measured below
--   Arm A (leaky features)                roc_auc 0.9387   log_loss 0.1241
--   Arm B (point-in-time correct)         roc_auc 0.5194   log_loss 0.2107
--   Arm A's MODEL on Arm B's features     roc_auc 0.5299   <- production
-- The gap is not an exaggeration of a real signal. It is manufactured
-- entirely: fed the features production can actually supply, the leaky model
-- lands where the honest one already was. Repeat purchase is close to
-- unpredictable from order history in this dataset, which
-- ../churn_retention/ independently found on the same orders while
-- predicting a different label (roc_auc 0.531 -> 0.544).
--
-- GOTCHA the split must be SHARED and DETERMINISTIC. Two CREATE MODEL
-- statements with independent data_split_method='RANDOM' draws are not a
-- controlled comparison -- the metric gap is then confounded with the split
-- difference. A FARM_FINGERPRINT hash of order_id plus NO_SPLIT costs one
-- expression and guarantees both arms see byte-identical train and eval rows.
--
-- GOTCHA turn the query cache OFF around retrains. BigQuery's result cache
-- keys on query TEXT, and CREATE OR REPLACE MODEL does not change the text of
-- the ML.EVALUATE that follows it. During the build of this notebook, after a
-- retrain that had genuinely changed both arms, each one reported its
-- PREVIOUS run's roc_auc to four decimals -- a stale pair of numbers that
-- looked entirely plausible. Use `bq query --nouse_cache`, or
-- QueryJobConfig(use_query_cache=False) from the client library.
--
-- GOTCHA leakage is a QUERY SHAPE, not a data problem. Both arms below read
-- one identical feature history table. The only difference is a GROUP BY with
-- no time bound.
--
-- Docs:
-- https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-entity-feature-time
-- https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-feature-time
--
-- Companion notebook: feature_store.ipynb
-- Functions in detail: ../../functions/feature_store/ (table shapes,
-- ignore_feature_nulls in both directions, the failure modes that raise no
-- error).
-- =============================================================

-- Windows. thelook_ecommerce is a rolling dataset whose newest rows advance
-- with the calendar, so every boundary here is pinned.
--   CUTOFF     2024-01-01  feature history is built strictly before this
--   TRAIN_FROM 2022-01-01  first order eligible to become a training row
--   TRAIN_TO   2023-09-30  last one, leaving room for its full 90-day label


-- Step 1: The label, and a split both arms must share
-- -------------------------------------------------------------
CREATE OR REPLACE TABLE `bq_ml.fsw_labeled` AS
WITH o AS (
  SELECT order_id, CAST(user_id AS STRING) AS entity_id, created_at
  FROM `bigquery-public-data.thelook_ecommerce.orders`
)
SELECT a.order_id,
       a.entity_id,
       a.created_at AS time,                      -- the entity table's time column
       IF(EXISTS(SELECT 1 FROM o b
                 WHERE b.entity_id = a.entity_id
                   AND b.created_at >  a.created_at
                   AND b.created_at <= TIMESTAMP_ADD(a.created_at, INTERVAL 90 DAY)),
          1, 0) AS reordered_90d,
       -- Deterministic: the same order lands in the same arm-agnostic split
       -- on every run, in every arm.
       MOD(ABS(FARM_FINGERPRINT(CAST(a.order_id AS STRING))), 10) >= 8 AS is_eval
FROM o a
WHERE a.created_at BETWEEN TIMESTAMP '2022-01-01' AND TIMESTAMP '2023-09-30';

SELECT COUNT(*) AS training_rows,
       COUNT(DISTINCT entity_id) AS customers,
       ROUND(AVG(reordered_90d), 4) AS base_rate,
       COUNTIF(NOT is_eval) AS train_rows,
       COUNTIF(is_eval) AS eval_rows
FROM `bq_ml.fsw_labeled`;
-- 19,633 rows | 17,024 customers | base rate 0.05 | 15,731 train | 3,902 eval
-- A low single-digit base rate, which is why roc_auc is the headline metric
-- below: it is the one least distorted by imbalance.


-- Step 2: One feature history, built once, used by BOTH arms
-- -------------------------------------------------------------
-- Each row records what became true about a customer at one instant and
-- nothing about any later instant -- ROWS UNBOUNDED PRECEDING over an
-- ordering by event time, so no row can see its own future. The table is
-- deliberately SPARSE (order events carry purchase features, shipment and
-- delivery events carry fulfilment features, NULL everywhere a row has
-- nothing to say), which is why every retrieval below passes
-- ignore_feature_nulls => TRUE. The trailing GROUP BY collapses simultaneous
-- events so "the most recent row" is never ambiguous.
CREATE OR REPLACE TABLE `bq_ml.fsw_history` AS
WITH ord AS (
  SELECT o.order_id, CAST(o.user_id AS STRING) AS entity_id,
         o.created_at, o.shipped_at, o.delivered_at, o.num_of_item,
         SUM(oi.sale_price) AS order_value
  FROM `bigquery-public-data.thelook_ecommerce.orders` o
  JOIN `bigquery-public-data.thelook_ecommerce.order_items` oi USING (order_id)
  WHERE o.created_at < TIMESTAMP '2024-01-01'
  GROUP BY 1, 2, 3, 4, 5, 6
),
events AS (
  SELECT entity_id, created_at AS feature_timestamp,
         COUNT(*)               OVER w AS lifetime_orders,
         ROUND(SUM(order_value) OVER w, 2) AS lifetime_spend,
         ROUND(AVG(order_value) OVER w, 2) AS avg_order_value,
         SUM(num_of_item)       OVER w AS lifetime_items,
         TIMESTAMP_DIFF(created_at, LAG(created_at) OVER p, DAY) AS days_since_prev_order,
         CAST(NULL AS FLOAT64) AS last_ship_lag_h,
         CAST(NULL AS FLOAT64) AS last_delivery_lag_h
  FROM ord
  WINDOW w AS (PARTITION BY entity_id ORDER BY created_at ROWS UNBOUNDED PRECEDING),
         p AS (PARTITION BY entity_id ORDER BY created_at)
  UNION ALL
  SELECT entity_id, shipped_at, NULL, NULL, NULL, NULL, NULL,
         ROUND(TIMESTAMP_DIFF(shipped_at, created_at, MINUTE) / 60, 2), NULL
  FROM ord WHERE shipped_at IS NOT NULL
  UNION ALL
  SELECT entity_id, delivered_at, NULL, NULL, NULL, NULL, NULL, NULL,
         ROUND(TIMESTAMP_DIFF(delivered_at, shipped_at, MINUTE) / 60, 2)
  FROM ord WHERE delivered_at IS NOT NULL
)
SELECT entity_id, feature_timestamp,
       MAX(lifetime_orders)       AS lifetime_orders,
       MAX(lifetime_spend)        AS lifetime_spend,
       MAX(avg_order_value)       AS avg_order_value,
       MAX(lifetime_items)        AS lifetime_items,
       MAX(days_since_prev_order) AS days_since_prev_order,
       MAX(last_ship_lag_h)       AS last_ship_lag_h,
       MAX(last_delivery_lag_h)   AS last_delivery_lag_h
FROM events
GROUP BY entity_id, feature_timestamp;
-- 68,833 rows | 26,979 customers | 2019-01-11 through 2024-01-07. (The latest
-- event runs past the cutoff because an order created before it can ship or
-- arrive after it; retrieval at the cutoff never sees those rows.)


-- Step 3: Arm A — the tempting mistake
-- -------------------------------------------------------------
-- Short, natural, and nothing in it looks like a bug. One row per customer
-- summarizing EVERYTHING ever known about them, joined onto every training
-- row -- so the row for an order placed in March 2022 receives features
-- computed from orders placed in 2023.
CREATE OR REPLACE TABLE `bq_ml.fsw_arm_leaky` AS
WITH all_history AS (
  SELECT entity_id,
         MAX(lifetime_orders)       AS lifetime_orders,
         MAX(lifetime_spend)        AS lifetime_spend,
         AVG(avg_order_value)       AS avg_order_value,
         MAX(lifetime_items)        AS lifetime_items,
         AVG(days_since_prev_order) AS days_since_prev_order,
         AVG(last_ship_lag_h)       AS last_ship_lag_h,
         AVG(last_delivery_lag_h)   AS last_delivery_lag_h
  FROM `bq_ml.fsw_history`
  GROUP BY entity_id                     -- <-- no time bound anywhere
)
SELECT l.order_id, l.is_eval, l.reordered_90d, h.* EXCEPT (entity_id)
FROM `bq_ml.fsw_labeled` l
JOIN all_history h USING (entity_id);


-- Step 4: Arm B — point-in-time correct
-- -------------------------------------------------------------
-- Same history, same training rows, same feature names. The retrieval is
-- anchored to each order's own timestamp, supplied by the entity table's
-- `time` column. Two mechanics apply directly:
--   * the entity table's EXTRA columns are dropped, and the label is exactly
--     such a column -- join it back on (entity_id, feature_timestamp), since
--     the function returns the requested instant under that name;
--   * the join is an INNER join, so an order whose customer has no feature
--     row at or before that instant vanishes silently. The row count is the
--     check, not a formality.
-- One production constraint that does not bite at this scale but will at
-- yours: the entity time relation is documented as capped at 100 MB. That is
-- entity_id plus time and nothing else, so it goes a long way -- but a
-- training set of tens of millions of labeled events exceeds it, and the fix
-- is to partition the build by time window or entity range and UNION ALL.
CREATE OR REPLACE TABLE `bq_ml.fsw_arm_correct` AS
SELECT l.order_id, l.is_eval, l.reordered_90d,
       f.lifetime_orders, f.lifetime_spend, f.avg_order_value, f.lifetime_items,
       f.days_since_prev_order, f.last_ship_lag_h, f.last_delivery_lag_h
FROM ML.ENTITY_FEATURES_AT_TIME(
       TABLE `bq_ml.fsw_history`,
       (SELECT entity_id, time FROM `bq_ml.fsw_labeled`),
       num_rows => 1, ignore_feature_nulls => TRUE) f
JOIN `bq_ml.fsw_labeled` l
  ON l.entity_id = f.entity_id AND l.time = f.feature_timestamp;

SELECT (SELECT COUNT(*) FROM `bq_ml.fsw_labeled`)     AS labeled_rows,
       (SELECT COUNT(*) FROM `bq_ml.fsw_arm_correct`) AS arm_b_rows,
       (SELECT COUNT(*) FROM `bq_ml.fsw_arm_leaky`)   AS arm_a_rows;
-- 19,633 | 19,633 | 19,633 -- no rows lost, the arms are row-for-row
-- comparable. That equality is a property of THIS construction (the history
-- was built from the same orders, so every order's customer necessarily has a
-- feature row at that exact instant), not a guarantee of the function.

-- What actually differs between the two feature tables, on identical rows:
SELECT 'Arm A — all-history (leaky)' AS arm,
       ROUND(AVG(lifetime_orders), 3) AS mean_lifetime_orders,
       ROUND(AVG(lifetime_spend), 2)  AS mean_lifetime_spend
FROM `bq_ml.fsw_arm_leaky`
UNION ALL
SELECT 'Arm B — as-of the order (correct)',
       ROUND(AVG(lifetime_orders), 3), ROUND(AVG(lifetime_spend), 2)
FROM `bq_ml.fsw_arm_correct`
ORDER BY arm;
-- Arm A 1.510 orders / 129.70 spend   vs   Arm B 1.308 / 111.71
-- Arm A's customers look busier and richer. Nothing was fabricated -- those
-- orders are real. They just had not happened yet at the moment each training
-- row is supposed to describe.


-- Step 5: Train both arms identically
-- -------------------------------------------------------------
-- NO_SPLIT on pre-filtered rows, so the Step 1 hash split is the only one in
-- play and BigQuery ML does no splitting of its own.
CREATE OR REPLACE MODEL `bq_ml.fsw_model_correct`
OPTIONS(model_type='LOGISTIC_REG',
        input_label_cols=['reordered_90d'],
        data_split_method='NO_SPLIT',
        enable_global_explain=FALSE) AS
SELECT * EXCEPT (order_id, is_eval)
FROM `bq_ml.fsw_arm_correct` WHERE NOT is_eval;

CREATE OR REPLACE MODEL `bq_ml.fsw_model_leaky`
OPTIONS(model_type='LOGISTIC_REG',
        input_label_cols=['reordered_90d'],
        data_split_method='NO_SPLIT',
        enable_global_explain=FALSE) AS
SELECT * EXCEPT (order_id, is_eval)
FROM `bq_ml.fsw_arm_leaky` WHERE NOT is_eval;


-- Step 6: The measured gap  [run with --nouse_cache]
-- -------------------------------------------------------------
SELECT 'Arm A — all-history (leaky)' AS arm,
       ROUND(roc_auc, 4) AS roc_auc, ROUND(log_loss, 4) AS log_loss
FROM ML.EVALUATE(MODEL `bq_ml.fsw_model_leaky`,
                 (SELECT * EXCEPT (order_id, is_eval)
                  FROM `bq_ml.fsw_arm_leaky` WHERE is_eval))
UNION ALL
SELECT 'Arm B — as-of the order (correct)',
       ROUND(roc_auc, 4), ROUND(log_loss, 4)
FROM ML.EVALUATE(MODEL `bq_ml.fsw_model_correct`,
                 (SELECT * EXCEPT (order_id, is_eval)
                  FROM `bq_ml.fsw_arm_correct` WHERE is_eval))
ORDER BY arm;
-- Arm A 0.9387 / 0.1241     Arm B 0.5194 / 0.2107
-- A very large gap, in the direction that gets a model shipped. Arm A would
-- sail through review; Arm B looks like a failed project. It is not a better
-- model. It is the same model, given the answer.


-- Step 7: Where that number came from  [run with --nouse_cache]
-- -------------------------------------------------------------
-- "Leakage" is otherwise an accusation you cannot check. Take one feature and
-- compare its two versions against the label.
SELECT 'Arm A — all-history (leaky)' AS feature_version,
       ROUND(CORR(lifetime_orders, reordered_90d), 4) AS corr_with_label,
       ROUND(AVG(IF(reordered_90d = 1, lifetime_orders, NULL)), 2) AS mean_if_reordered,
       ROUND(AVG(IF(reordered_90d = 0, lifetime_orders, NULL)), 2) AS mean_if_not
FROM `bq_ml.fsw_arm_leaky`
UNION ALL
SELECT 'Arm B — as-of the order (correct)',
       ROUND(CORR(lifetime_orders, reordered_90d), 4),
       ROUND(AVG(IF(reordered_90d = 1, lifetime_orders, NULL)), 2),
       ROUND(AVG(IF(reordered_90d = 0, lifetime_orders, NULL)), 2)
FROM `bq_ml.fsw_arm_correct`
ORDER BY feature_version;
--   version    corr     mean if reordered / not
--   Arm A      0.3065   2.51 / 1.46
--   Arm B      0.0103   1.33 / 1.31
-- Measured AS OF the order, a customer's order count says essentially nothing
-- about whether they come back. Measured over ALL history, reorderers have a
-- visibly higher count -- of course they do: if they reordered within 90
-- days, that reorder is one of the orders being counted. The all-history
-- feature does not PREDICT the label, it CONTAINS it.

SELECT processed_input AS feature, ROUND(weight, 4) AS weight
FROM ML.WEIGHTS(MODEL `bq_ml.fsw_model_leaky`)
ORDER BY ABS(weight) DESC;
-- __INTERCEPT__ -2.2276 | lifetime_orders 0.8088 | lifetime_items 0.0578 |
-- days_since_prev_order -0.0097 | last_ship_lag_h 0.0022 | ...
-- Setting the intercept aside, lifetime_orders carries a weight an order of
-- magnitude above every other feature. The model learned to read the answer
-- and largely ignored the rest of the vector.


-- Step 8: What production actually does to the leaky model  [--nouse_cache]
-- -------------------------------------------------------------
-- At serving time there is no "all history" -- a customer's future orders
-- have not happened. The only vector that can exist is the point-in-time one,
-- so the Arm A model gets scored on Arm B features whether anyone planned for
-- it or not. Same model, same eval rows, features rebuilt as-of.
SELECT 'Arm A model, leaky features (the offline claim)' AS scenario,
       ROUND(roc_auc, 4) AS roc_auc
FROM ML.EVALUATE(MODEL `bq_ml.fsw_model_leaky`,
                 (SELECT * EXCEPT (order_id, is_eval)
                  FROM `bq_ml.fsw_arm_leaky` WHERE is_eval))
UNION ALL
SELECT 'Arm A model, as-of features (production reality)', ROUND(roc_auc, 4)
FROM ML.EVALUATE(MODEL `bq_ml.fsw_model_leaky`,
                 (SELECT * EXCEPT (order_id, is_eval)
                  FROM `bq_ml.fsw_arm_correct` WHERE is_eval))
UNION ALL
SELECT 'Arm B model, as-of features (honest all along)', ROUND(roc_auc, 4)
FROM ML.EVALUATE(MODEL `bq_ml.fsw_model_correct`,
                 (SELECT * EXCEPT (order_id, is_eval)
                  FROM `bq_ml.fsw_arm_correct` WHERE is_eval))
ORDER BY roc_auc DESC;
--   the offline claim      0.9387
--   production reality     0.5299   <- the advantage does not shrink
--   honest all along       0.5194
-- It DISAPPEARS, landing essentially where the honest model already was,
-- because the feature it relied on no longer contains anything. That is the
-- real cost of leakage, and it is not the inflated metric -- it is that the
-- inflated metric bought nothing: months of work, a model card, a launch
-- decision, and a production system whose measured quality equals the model
-- that looked like a failure. The honest arm was never worse. It was the only
-- one reporting the truth.


-- Step 9: Serving — the same features, one call, no feature store
-- -------------------------------------------------------------
-- Training asked for a different instant per row, so it used
-- ML.ENTITY_FEATURES_AT_TIME. Serving asks for one instant shared by everyone
-- -- now -- so it uses ML.FEATURES_AT_TIME. Same table, same feature
-- definitions, same ignore_feature_nulls => TRUE required by the sparse
-- shape. Nothing else changes. That is offline/online parity without a
-- feature store to operate.
CREATE OR REPLACE TABLE `bq_ml.fsw_serving` AS
SELECT * FROM ML.FEATURES_AT_TIME(
  TABLE `bq_ml.fsw_history`,
  time => TIMESTAMP '2024-01-01',      -- or CURRENT_TIMESTAMP() in production
  num_rows => 1, ignore_feature_nulls => TRUE);

SELECT COUNT(*) AS customers_served,
       COUNTIF(lifetime_orders IS NULL) AS missing_order_count
FROM `bq_ml.fsw_serving`;
-- 26,979 | 0

SELECT entity_id, lifetime_orders, lifetime_spend,
       ROUND(predicted_reordered_90d_probs[OFFSET(0)].prob, 4) AS p_reorder
FROM ML.PREDICT(MODEL `bq_ml.fsw_model_correct`,
                TABLE `bq_ml.fsw_serving`)
ORDER BY p_reorder DESC
LIMIT 10;
-- Top probabilities cluster near 0.064 on 3-4 lifetime orders. The honest
-- caveat, given Step 8: this model's ranking is close to uninformative on
-- this dataset, so the ordering is not a targeting list. What the step
-- demonstrates is the MECHANISM -- the same feature definitions reaching
-- training and serving without being written twice, which is the property a
-- feature store exists to provide and the one worth keeping when you do not
-- have one.


-- Cleanup
-- -------------------------------------------------------------
DROP TABLE IF EXISTS `bq_ml.fsw_labeled`;
DROP TABLE IF EXISTS `bq_ml.fsw_history`;
DROP TABLE IF EXISTS `bq_ml.fsw_arm_leaky`;
DROP TABLE IF EXISTS `bq_ml.fsw_arm_correct`;
DROP TABLE IF EXISTS `bq_ml.fsw_serving`;
DROP MODEL IF EXISTS `bq_ml.fsw_model_correct`;
DROP MODEL IF EXISTS `bq_ml.fsw_model_leaky`;
