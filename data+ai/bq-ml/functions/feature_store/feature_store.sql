-- Point-in-Time Feature Retrieval — Progressive SQL Examples (BigQuery ML model-free functions)
-- =============================================================
-- Two model-free table-valued functions that answer "what did we know about
-- this entity at this moment?" -- the question a feature store exists to
-- answer. ML.FEATURES_AT_TIME retrieves every entity's vector as of ONE
-- shared timestamp (the online-serving shape). ML.ENTITY_FEATURES_AT_TIME
-- retrieves each entity's vector as of ITS OWN timestamp (the training-set
-- shape, and what prevents label leakage). Neither trains a model, neither
-- needs a connection, neither creates an object to clean up. There is no
-- feature store to provision -- the feature table is an ordinary table.
--
-- THE CENTRAL POINT the shape of your feature table decides which arguments
-- you need, and getting it backwards is silent. `ignore_feature_nulls` is
-- REQUIRED on one table shape and HARMFUL on another, with no error either
-- way. Everything below is measured on thelook_ecommerce, as of a fixed
-- 2024-01-01 cutoff, across 26,979 customers.
--
-- CONTRACT the feature table must contain a STRING column named exactly
-- `entity_id` and a TIMESTAMP column named exactly `feature_timestamp`. Every
-- other column is treated as a feature. The names are fixed, not
-- configurable, so most real tables need a rename on the way in. They are,
-- however, CASE-INSENSITIVE -- Entity_ID and Feature_TimeStamp are accepted
-- and the original casing comes back in the output. The types are not
-- negotiable either way, and all three violations fail at planning time:
--   entity_id as INT64
--     -> "feature_table column 'entity_id' can only be String type but found
--        INT64"
--   feature_timestamp as DATE
--     -> "feature_table column 'feature_timestamp' can only be Timestamp type
--        but found DATE"
--   column absent
--     -> "feature_table must include a 'feature_timestamp' column"
-- thelook's user_id is INT64, so CAST(user_id AS STRING) is mandatory, and a
-- DATE partition column will not stand in for feature_timestamp.
--
-- GOTCHA `ignore_feature_nulls` is a statement about your table, not a tuning
-- knob. On a SPARSE history (one row per feature UPDATE, NULL where that
-- update did not touch a feature) it is required: without it, 17,440 of
-- 26,979 customers came back with a NULL lifetime order count they do not
-- actually have, because their most recent row was a shipment or a delivery.
-- With it, that count drops to 0 and only genuine absences remain. On a DENSE
-- table (one row per complete observation, where NULL is a FACT) the same
-- flag fabricated data: 1,572 customers were reported with a delivery
-- duration for an order that was cancelled, still processing, or shipped but
-- not arrived -- a real measurement of a DIFFERENT, EARLIER order. Neither
-- call errors. Neither output looks wrong.
--
-- GOTCHA `feature_timestamp` in the OUTPUT is the time you ASKED for, not the
-- time the source row was written. Provenance is discarded on every row. With
-- ignore_feature_nulls => TRUE the returned row is assembled from several
-- source rows at different instants, so no single source time would even be
-- correct -- but that also means you cannot recover when any value was true.
-- If you need it, carry a copy of the event time as an ordinary feature
-- column, where it survives.
--
-- GOTCHA `num_rows` defaults to 1. Raising it returns up to N of the most
-- recent rows per entity, but ALL of them carry the same requested
-- feature_timestamp -- so nothing distinguishes them and there is nothing to
-- ORDER BY. num_rows > 1 supports aggregating recent history (average of the
-- last three ship lags); it cannot support sequencing it.
--
-- GOTCHA duplicate (entity_id, feature_timestamp) pairs make "most recent
-- row" ambiguous and the tie is broken arbitrarily -- a small, silent source
-- of run-to-run variation. Collapse simultaneous events on write.
--
-- GOTCHA `time` takes ONE timestamp, not a list. Passing an array fails with
-- "Unable to coerce type ARRAY<TIMESTAMP> to expected type TIMESTAMP". For
-- many cutoffs, use ML.ENTITY_FEATURES_AT_TIME or UNION ALL the calls.
--
-- GOTCHA ML.ENTITY_FEATURES_AT_TIME's entity table needs `entity_id` and a
-- column named `time` -- NOT `feature_timestamp`, which is the feature
-- table's name for the same idea. There is no `time` argument, because the
-- entity table IS the time argument. It is also documented as capped at
-- 100 MB, which a training set of tens of millions of rows will exceed.
--
-- GOTCHA ML.ENTITY_FEATURES_AT_TIME drops the entity table's EXTRA columns.
-- Only entity_id and the requested time come back. Your label is exactly such
-- a column, so join it back on (entity_id, feature_timestamp).
--
-- GOTCHA ML.ENTITY_FEATURES_AT_TIME is an INNER join. An entity with no
-- feature row at or before its requested instant is omitted, not returned
-- with NULL features -- verified: 26,979 requests one day before each
-- customer's first event returned 0 rows. The dropped rows are not a random
-- sample; they are precisely the cold-start cases. LEFT JOIN the entity table
-- back on if you need them.
--
-- VERIFIED, NOT A GOTCHA the output preserves the source table's column
-- order. Worth stating because it is easy to convince yourself otherwise:
-- several clients sort field names when rendering a row as JSON, including
-- `bq --format=json`. Read the order off the schema, not off a serialized row.
--
-- Docs:
-- https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-feature-time
-- https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-entity-feature-time
--
-- Companion notebook: feature_store.ipynb (builds all three table shapes and
-- measures every number quoted above).
-- Workflow: ../../workflows/feature_store/ (what point-in-time correctness is
-- worth, measured end to end).
-- =============================================================


-- Example 1: Build a SPARSE feature history from real event streams
-- -------------------------------------------------------------
-- An order is created, later shipped, later delivered. Each event knows
-- something the others do not, so each row is NULL everywhere it has nothing
-- to say. This is the normal shape of a feature history assembled from
-- independent streams -- most cells are NULL, and that is correct.
-- The final GROUP BY collapses simultaneous events so every
-- (entity_id, feature_timestamp) pair is unique; see the ambiguity GOTCHA.
CREATE OR REPLACE TABLE `bq_ml.fs_sparse` AS
WITH ord AS (
  SELECT o.order_id,
         CAST(o.user_id AS STRING) AS entity_id,   -- STRING is mandatory
         o.created_at, o.shipped_at, o.delivered_at, o.status, o.num_of_item,
         SUM(oi.sale_price) AS order_value
  FROM `bigquery-public-data.thelook_ecommerce.orders` o
  JOIN `bigquery-public-data.thelook_ecommerce.order_items` oi USING (order_id)
  WHERE o.created_at < TIMESTAMP '2024-01-01'
  GROUP BY 1, 2, 3, 4, 5, 6, 7
),
events AS (
  SELECT entity_id, created_at AS feature_timestamp,
         COUNT(*)               OVER w AS lifetime_orders,
         ROUND(SUM(order_value) OVER w, 2) AS lifetime_spend,
         CAST(NULL AS FLOAT64) AS last_ship_lag_h,
         CAST(NULL AS FLOAT64) AS last_delivery_lag_h
  FROM ord
  WINDOW w AS (PARTITION BY entity_id ORDER BY created_at ROWS UNBOUNDED PRECEDING)
  UNION ALL
  SELECT entity_id, shipped_at, NULL, NULL,
         ROUND(TIMESTAMP_DIFF(shipped_at, created_at, MINUTE) / 60, 2), NULL
  FROM ord WHERE shipped_at IS NOT NULL
  UNION ALL
  SELECT entity_id, delivered_at, NULL, NULL, NULL,
         ROUND(TIMESTAMP_DIFF(delivered_at, shipped_at, MINUTE) / 60, 2)
  FROM ord WHERE delivered_at IS NOT NULL
)
SELECT entity_id, feature_timestamp,
       MAX(lifetime_orders)     AS lifetime_orders,
       MAX(lifetime_spend)      AS lifetime_spend,
       MAX(last_ship_lag_h)     AS last_ship_lag_h,
       MAX(last_delivery_lag_h) AS last_delivery_lag_h
FROM events
GROUP BY entity_id, feature_timestamp;
-- 68,833 rows, 26,979 customers.


-- Example 2: One customer's history -- no single row describes them
-- -------------------------------------------------------------
SELECT feature_timestamp, lifetime_orders, lifetime_spend,
       last_ship_lag_h, last_delivery_lag_h
FROM `bq_ml.fs_sparse`
WHERE entity_id = '10000'
ORDER BY feature_timestamp;
-- Six rows across four years. The order count lives on one row, the ship lag
-- on another, the delivery lag on a third.


-- Example 3: The default call -- correct, and nearly useless on a sparse table
-- -------------------------------------------------------------
SELECT COUNT(*) AS entities,
       COUNTIF(lifetime_orders IS NULL)     AS null_lifetime_orders,
       COUNTIF(last_ship_lag_h IS NULL)     AS null_ship_lag,
       COUNTIF(last_delivery_lag_h IS NULL) AS null_delivery_lag
FROM ML.FEATURES_AT_TIME(
  TABLE `bq_ml.fs_sparse`,
  time => TIMESTAMP '2024-01-01',
  num_rows => 1);
-- 26,979 | 17,440 | 18,866 | 17,649
-- Nearly two thirds of these customers appear to have no order count at all,
-- and every one of them has ordered -- that is where the rows came from. The
-- retrieval is right; the most recent row is just usually a shipment.


-- Example 4: ignore_feature_nulls => TRUE -- the sparse-shape reassembler
-- -------------------------------------------------------------
-- Per feature column, walk back to the most recent row where THAT column is
-- non-NULL, independently of the others.
SELECT COUNT(*) AS entities,
       COUNTIF(lifetime_orders IS NULL)     AS null_lifetime_orders,
       COUNTIF(last_ship_lag_h IS NULL)     AS null_ship_lag,
       COUNTIF(last_delivery_lag_h IS NULL) AS null_delivery_lag
FROM ML.FEATURES_AT_TIME(
  TABLE `bq_ml.fs_sparse`,
  time => TIMESTAMP '2024-01-01',
  num_rows => 1,
  ignore_feature_nulls => TRUE);
-- 26,979 | 0 | 8,057 | 16,083
-- lifetime_orders goes to ZERO nulls. The remaining gaps are honest: those
-- customers genuinely never had an order ship or arrive before the cutoff.
-- The shape artifact is gone and the real absences survive.


-- Example 5: The row that never existed -- and why that is the point
-- -------------------------------------------------------------
SELECT 'history' AS source, CAST(feature_timestamp AS STRING) AS ts,
       lifetime_orders, lifetime_spend, last_ship_lag_h, last_delivery_lag_h
FROM `bq_ml.fs_sparse`
WHERE entity_id = '10000' AND feature_timestamp < TIMESTAMP '2024-01-01'
UNION ALL
SELECT 'default', CAST(feature_timestamp AS STRING),
       lifetime_orders, lifetime_spend, last_ship_lag_h, last_delivery_lag_h
FROM ML.FEATURES_AT_TIME(
  (SELECT * FROM `bq_ml.fs_sparse` WHERE entity_id = '10000'),
  time => TIMESTAMP '2024-01-01', num_rows => 1)
UNION ALL
SELECT 'ignore_feature_nulls', CAST(feature_timestamp AS STRING),
       lifetime_orders, lifetime_spend, last_ship_lag_h, last_delivery_lag_h
FROM ML.FEATURES_AT_TIME(
  (SELECT * FROM `bq_ml.fs_sparse` WHERE entity_id = '10000'),
  time => TIMESTAMP '2024-01-01', num_rows => 1, ignore_feature_nulls => TRUE)
ORDER BY source, ts;
-- Verified: the DEFAULT row takes everything from the 2021-12-12 delivery and
-- reports a customer with no orders and no spend. The IGNORE_FEATURE_NULLS
-- row takes lifetime_orders/lifetime_spend from 2021-12-07, last_ship_lag_h
-- from 2021-12-08, and last_delivery_lag_h from 2021-12-12 -- three different
-- source rows, assembled into one vector that exists in no row of the table.
-- On a sparse history that is not a hazard, it is the entire job.


-- Example 6: The SAME flag on a DENSE table fabricates data
-- -------------------------------------------------------------
-- One row per order, every column populated from that order's own record.
-- days_to_deliver is NULL for orders that were cancelled, are processing, or
-- have shipped but not arrived. That NULL is a FACT about the order.
CREATE OR REPLACE TABLE `bq_ml.fs_dense` AS
SELECT CAST(o.user_id AS STRING) AS entity_id,
       o.created_at AS feature_timestamp,
       o.num_of_item AS items_in_order,
       o.status      AS order_status,
       ROUND(TIMESTAMP_DIFF(o.delivered_at, o.created_at, MINUTE) / 24 / 60, 2)
         AS days_to_deliver
FROM `bigquery-public-data.thelook_ecommerce.orders` o
WHERE o.created_at < TIMESTAMP '2024-01-01';
-- 34,546 rows, 26,979 customers, 22,569 NULL days_to_deliver.

WITH d AS (
  SELECT * FROM ML.FEATURES_AT_TIME(TABLE `bq_ml.fs_dense`,
                                    time => TIMESTAMP '2024-01-01', num_rows => 1)
),
g AS (
  SELECT * FROM ML.FEATURES_AT_TIME(TABLE `bq_ml.fs_dense`,
                                    time => TIMESTAMP '2024-01-01', num_rows => 1,
                                    ignore_feature_nulls => TRUE)
)
SELECT d.order_status AS latest_order_status,
       COUNT(*) AS entities,
       COUNTIF(d.days_to_deliver IS NULL) AS null_with_default,
       COUNTIF(g.days_to_deliver IS NULL) AS null_with_ignore_nulls,
       COUNTIF(d.days_to_deliver IS NULL AND g.days_to_deliver IS NOT NULL) AS fabricated
FROM d JOIN g USING (entity_id)
GROUP BY latest_order_status
ORDER BY latest_order_status;
-- Verified: Cancelled 387 + Processing 478 + Shipped 707 = 1,572 customers now
-- carry a delivery duration for an order that was never delivered. Complete
-- and Returned are untouched, so a spot check of a few rows looks fine.
--
--   feature table | ignore_feature_nulls => TRUE does        | verdict
--   sparse        | repairs 17,440 storage-artifact NULLs    | REQUIRED
--   dense         | invents 1,572 delivery times             | HARMFUL


-- Example 7: The default call is EXACTLY a QUALIFY ROW_NUMBER window
-- -------------------------------------------------------------
-- Two empty results mean the sets are identical.
WITH fn AS (
  SELECT entity_id, feature_timestamp, items_in_order, order_status, days_to_deliver
  FROM ML.FEATURES_AT_TIME(TABLE `bq_ml.fs_dense`,
                           time => TIMESTAMP '2024-01-01', num_rows => 1)
),
latest AS (
  SELECT * FROM `bq_ml.fs_dense`
  WHERE feature_timestamp <= TIMESTAMP '2024-01-01'
  QUALIFY ROW_NUMBER() OVER (PARTITION BY entity_id ORDER BY feature_timestamp DESC) = 1
),
hand AS (
  SELECT entity_id, TIMESTAMP '2024-01-01' AS feature_timestamp,
         items_in_order, order_status, days_to_deliver
  FROM latest
)
SELECT (SELECT COUNT(*) FROM (SELECT * FROM fn   EXCEPT DISTINCT SELECT * FROM hand)) AS in_function_not_hand,
       (SELECT COUNT(*) FROM (SELECT * FROM hand EXCEPT DISTINCT SELECT * FROM fn))   AS in_hand_not_function;
-- 0 | 0. The function is not doing anything you could not write yourself.


-- Example 8: ...but the hand-written form has a trap in it
-- -------------------------------------------------------------
-- Example 7's `hand` CTE is deliberately two steps: pick the latest row, THEN
-- overwrite feature_timestamp. Collapsing them is the obvious simplification
-- and it is wrong. BigQuery resolves QUALIFY AFTER the SELECT list, so a
-- select-list alias is visible to it: `TIMESTAMP '...' AS feature_timestamp`
-- makes the window's ORDER BY order by the CONSTANT. Every row ties and
-- ROW_NUMBER picks arbitrarily. No error, no warning.
WITH fn AS (
  SELECT entity_id, lifetime_orders, lifetime_spend, last_ship_lag_h, last_delivery_lag_h
  FROM ML.FEATURES_AT_TIME(TABLE `bq_ml.fs_sparse`,
                           time => TIMESTAMP '2024-01-01', num_rows => 1)
),
shadowed AS (
  SELECT entity_id, TIMESTAMP '2024-01-01' AS feature_timestamp,   -- shadows the column below
         lifetime_orders, lifetime_spend, last_ship_lag_h, last_delivery_lag_h
  FROM `bq_ml.fs_sparse`
  WHERE feature_timestamp <= TIMESTAMP '2024-01-01'
  QUALIFY ROW_NUMBER() OVER (PARTITION BY entity_id ORDER BY feature_timestamp DESC) = 1
)
SELECT COUNT(*) AS entities_compared,
       COUNTIF(f.lifetime_orders     IS DISTINCT FROM s.lifetime_orders
            OR f.lifetime_spend      IS DISTINCT FROM s.lifetime_spend
            OR f.last_ship_lag_h     IS DISTINCT FROM s.last_ship_lag_h
            OR f.last_delivery_lag_h IS DISTINCT FROM s.last_delivery_lag_h) AS entities_disagreeing
FROM fn f JOIN (SELECT * EXCEPT (feature_timestamp) FROM shadowed) s USING (entity_id);
-- Verified: roughly 46% of 26,979 entities get a different -- wrong -- vector,
-- from a query that runs cleanly and reads correctly. The exact count MOVES
-- between runs, which is the tell: with every row tied on a constant there is
-- no defined winner. The function has no select list to shadow anything with,
-- so it cannot be broken this way. Better reason to use it than brevity.


-- Example 9: EAV storage -- pivot back, then retrieve
-- -------------------------------------------------------------
-- One row per OBSERVATION. A new feature needs no schema change, just a new
-- value of feature_name. The value is a STRUCT with one field per type.
CREATE OR REPLACE TABLE `bq_ml.fs_eav` AS
SELECT entity_id AS entity_key, feature_timestamp, feature_name,
       STRUCT(CAST(NULL AS STRING)  AS string_value,
              CAST(v AS INT64)      AS int_value,
              CAST(NULL AS FLOAT64) AS float_value,
              CAST(NULL AS BOOL)    AS bool_value) AS feature_value
FROM `bq_ml.fs_sparse`
UNPIVOT (v FOR feature_name IN (lifetime_orders))
UNION ALL
SELECT entity_id, feature_timestamp, feature_name,
       STRUCT(NULL, NULL, CAST(v AS FLOAT64), NULL)
FROM `bq_ml.fs_sparse`
UNPIVOT (v FOR feature_name IN (lifetime_spend, last_ship_lag_h, last_delivery_lag_h));
-- UNPIVOT drops NULLs, so EAV stores only what was observed -- that is the
-- shape's whole appeal: lifetime_orders 34,546 observations against
-- last_delivery_lag_h 11,977.

-- ML.FEATURES_AT_TIME needs one column per feature, so pivot on the way in.
-- Because EAV omits unobserved values, the pivot reproduces the SPARSE shape
-- exactly -- so it needs ignore_feature_nulls for the same reason Example 4 did.
SELECT COUNT(*) AS entities,
       COUNTIF(lifetime_orders IS NULL)     AS null_lifetime_orders,
       COUNTIF(last_delivery_lag_h IS NULL) AS null_delivery_lag
FROM ML.FEATURES_AT_TIME(
  (SELECT entity_key AS entity_id, feature_timestamp,
          MAX(IF(feature_name = 'lifetime_orders',     feature_value.int_value,   NULL)) AS lifetime_orders,
          MAX(IF(feature_name = 'lifetime_spend',      feature_value.float_value, NULL)) AS lifetime_spend,
          MAX(IF(feature_name = 'last_ship_lag_h',     feature_value.float_value, NULL)) AS last_ship_lag_h,
          MAX(IF(feature_name = 'last_delivery_lag_h', feature_value.float_value, NULL)) AS last_delivery_lag_h
   FROM `bq_ml.fs_eav`
   GROUP BY entity_id, feature_timestamp),
  time => TIMESTAMP '2024-01-01', num_rows => 1, ignore_feature_nulls => TRUE);
-- 26,979 | 0 | 16,083 -- identical to Example 4. The round trip holds: storage
-- shape is a storage decision and does not change the answer. The cost is in
-- the pivot, where every feature must be named twice.


-- Example 10: num_rows returns more history, and erases which is which
-- -------------------------------------------------------------
SELECT entity_id, feature_timestamp, lifetime_orders, last_ship_lag_h, last_delivery_lag_h
FROM ML.FEATURES_AT_TIME(
  (SELECT * FROM `bq_ml.fs_sparse` WHERE entity_id = '10000'),
  time => TIMESTAMP '2024-01-01', num_rows => 3);
-- Three rows, ALL carrying the same feature_timestamp (the requested time).
-- The source timestamps that distinguish them are gone and no other column
-- recovers them. Row counts across the whole table: num_rows 1 -> 26,979,
-- 2 -> 46,547, 3 -> 59,217 (entities constant at 26,979).


-- Example 11: ML.ENTITY_FEATURES_AT_TIME -- a different instant per entity
-- -------------------------------------------------------------
-- The entity table supplies the per-entity instants and needs `entity_id`
-- plus a column named `time`. There is no `time` ARGUMENT -- the entity table
-- IS the time argument.
CREATE OR REPLACE TABLE `bq_ml.fs_entities` AS
SELECT CAST(user_id AS STRING) AS entity_id,
       created_at AS time,
       order_id,
       status AS order_status
FROM `bigquery-public-data.thelook_ecommerce.orders`
WHERE created_at BETWEEN TIMESTAMP '2023-06-01' AND TIMESTAMP '2023-12-31';

SELECT *
FROM ML.ENTITY_FEATURES_AT_TIME(
  TABLE `bq_ml.fs_sparse`,
  TABLE `bq_ml.fs_entities`,
  num_rows => 1, ignore_feature_nulls => TRUE)
ORDER BY entity_id, feature_timestamp
LIMIT 5;
-- Verified: order_id and order_status are GONE. Only entity_id and the
-- requested instant (returned in feature_timestamp) survive. Since the label
-- is exactly such a column, join it back on (entity_id, feature_timestamp).


-- Example 12: it is an INNER join, and the rows it drops are the ones you want
-- -------------------------------------------------------------
-- Ask for features one day BEFORE each customer's first event.
WITH cold AS (
  SELECT entity_id, TIMESTAMP_SUB(MIN(feature_timestamp), INTERVAL 1 DAY) AS time
  FROM `bq_ml.fs_sparse`
  GROUP BY entity_id
)
SELECT (SELECT COUNT(*) FROM cold) AS requests,
       (SELECT COUNT(*) FROM ML.ENTITY_FEATURES_AT_TIME(
          TABLE `bq_ml.fs_sparse`,
          (SELECT * FROM cold),
          num_rows => 1, ignore_feature_nulls => TRUE)) AS returned;
-- 26,979 requests -> 0 returned. Entities with no history at or before the
-- requested instant are OMITTED, not returned with NULL features, so the
-- output is silently smaller than the input. The dropped rows are precisely
-- the cold-start cases -- new customers, new products, the first weeks of any
-- entity's life. Dropping them makes a training set look cleaner and a model
-- look better while removing the population it will most be asked about.
-- LEFT JOIN the entity table back on and decide explicitly what a missing
-- vector means.


-- Example 13: serving -- the online vector, one call
-- -------------------------------------------------------------
SELECT entity_id, lifetime_orders, lifetime_spend, last_ship_lag_h, last_delivery_lag_h
FROM ML.FEATURES_AT_TIME(
  TABLE `bq_ml.fs_sparse`,
  time => TIMESTAMP '2024-01-01',   -- or CURRENT_TIMESTAMP() in production
  num_rows => 1,
  ignore_feature_nulls => TRUE)
ORDER BY lifetime_spend DESC
LIMIT 10;
-- Same table, same arguments, same feature definitions as the training-set
-- build in Example 11 -- offline/online parity without operating a feature
-- store. See ../../workflows/feature_store/ for the end-to-end version, where
-- the leaky and point-in-time-correct training sets are trained and compared.


-- Cleanup
-- -------------------------------------------------------------
DROP TABLE IF EXISTS `bq_ml.fs_sparse`;
DROP TABLE IF EXISTS `bq_ml.fs_dense`;
DROP TABLE IF EXISTS `bq_ml.fs_eav`;
DROP TABLE IF EXISTS `bq_ml.fs_entities`;
