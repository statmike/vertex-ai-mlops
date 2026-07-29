-- Price Elasticity via Double Machine Learning — BigQuery ML Workflow
-- =============================================================
-- Naive price/quantity regression is confounded by real factors (distribution
-- breadth, category, vendor) that drive both price and volume at once.
-- Double Machine Learning (Chernozhukov et al. 2018, the current industry
-- standard) fixes this: fit two ML models to strip out what confounders
-- explain, then estimate the effect from the residuals. Fully native to
-- BigQuery ML -- no external package needed.
--
-- Data: bigquery-public-data.iowa_liquor_sales.sales, 2022-2023, 750ml
--       bottles, 8 major categories. Cross-sectional design (one row per
--       SKU) since this dataset's retail price is state-set and fixed over
--       time for any single product -- ruling out a time-series design.
--
-- GOTCHA: item_number alone is not a safe join/grouping key -- 3 SKUs in
-- this window appear under more than one category_name. A synthetic row_id
-- (ROW_NUMBER()) is required, or downstream JOINs silently multiply rows
-- (caught live: residuals table came back with 1,136 rows instead of the
-- expected 1,130 before this fix).
--
-- GOTCHA: BigQuery ML's LINEAR_REG default optimize_strategy='AUTO_STRATEGY'
-- can select iterative gradient descent that stops early on small/collinear
-- designs without reaching the true least-squares solution -- verified this
-- does NOT affect this workflow's regressions (both the 1,130-row single-
-- predictor naive/DML fits match NORMAL_EQUATION exactly), but the fix
-- (optimize_strategy='NORMAL_EQUATION') is used anyway for a guaranteed
-- exact fit. See workflows/difference_in_differences/ for a case where this
-- gotcha DOES bite (a 28-row panel with a treated*post interaction term).
--
-- Full reference: ../../RESOURCES.md
-- Official docs:
--   CREATE MODEL (GLM): https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-glm
--   BOOSTED_TREE_REGRESSOR: https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-boosted-tree


-- =============================================================================
-- Step 1: Build the SKU panel -- one row per product, real cross-brand variation
-- =============================================================================
CREATE OR REPLACE TABLE `PROJECT_ID.DATASET.price_elasticity_panel` AS
SELECT
  ROW_NUMBER() OVER() AS row_id,
  item_number, category_name, vendor_name, pack, log_price, log_qty, log_n_stores
FROM (
  SELECT
    item_number,
    category_name,
    ANY_VALUE(vendor_name) AS vendor_name,
    ANY_VALUE(pack) AS pack,
    LN(AVG(state_bottle_retail)) AS log_price,
    LN(SUM(bottles_sold)) AS log_qty,
    LN(COUNT(DISTINCT store_number)) AS log_n_stores
  FROM `bigquery-public-data.iowa_liquor_sales.sales`
  WHERE date BETWEEN '2022-01-01' AND '2023-12-31'
    AND bottle_volume_ml = 750
    AND category_name IN (
      'AMERICAN VODKAS', 'STRAIGHT BOURBON WHISKIES', '100% AGAVE TEQUILA', 'AMERICAN FLAVORED VODKA',
      'SPICED RUM', 'IMPORTED VODKAS', 'CANADIAN WHISKIES', 'BLENDED WHISKIES'
    )
  GROUP BY item_number, category_name
  HAVING SUM(bottles_sold) > 50
);
-- Verified: 1,130 SKUs, ~154 vendors (shifts by 1-2 on a rerun -- a still-
-- updated public dataset). CORR(log_price, log_qty) = -0.52 (real
-- demand curve). CORR(log_price, log_n_stores) = -0.28 (real confounder --
-- pricier SKUs reach fewer stores).


-- =============================================================================
-- Step 2: Naive elasticity -- plain LINEAR_REG, no confounders
-- =============================================================================
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.price_elasticity_naive`
OPTIONS(model_type = 'LINEAR_REG', input_label_cols = ['log_qty']) AS
SELECT log_price, log_qty FROM `PROJECT_ID.DATASET.price_elasticity_panel`;

SELECT * FROM ML.WEIGHTS(MODEL `PROJECT_ID.DATASET.price_elasticity_naive`);
-- Verified: naive elasticity ~ -1.43.


-- =============================================================================
-- Step 3: Why DML -- distribution breadth/category/vendor confound the naive
-- number; explained in notebook markdown, no new SQL.
-- =============================================================================


-- =============================================================================
-- Step 4: 5-fold cross-fitting (reuses cross_validation/'s exact fold pattern)
-- =============================================================================
CREATE OR REPLACE TABLE `PROJECT_ID.DATASET.price_elasticity_folds` AS
SELECT *, MOD(ABS(FARM_FINGERPRINT(TO_JSON_STRING(t))), 5) AS fold
FROM `PROJECT_ID.DATASET.price_elasticity_panel` AS t;

-- Per fold i (repeat for i = 0..4): train on every OTHER fold, no held-out split needed.
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.price_elasticity_fold0_y`
OPTIONS(model_type = 'BOOSTED_TREE_REGRESSOR', input_label_cols = ['log_qty'], data_split_method = 'NO_SPLIT') AS
SELECT category_name, vendor_name, pack, log_n_stores, log_qty
FROM `PROJECT_ID.DATASET.price_elasticity_folds` WHERE fold != 0;

CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.price_elasticity_fold0_t`
OPTIONS(model_type = 'BOOSTED_TREE_REGRESSOR', input_label_cols = ['log_price'], data_split_method = 'NO_SPLIT') AS
SELECT category_name, vendor_name, pack, log_n_stores, log_price
FROM `PROJECT_ID.DATASET.price_elasticity_folds` WHERE fold != 0;
-- ... repeat for fold_1 .. fold_4 (WHERE fold != 1, != 2, != 3, != 4) ...

-- Union all 5 folds' genuinely out-of-fold residuals:
CREATE OR REPLACE TABLE `PROJECT_ID.DATASET.price_elasticity_residuals` AS
SELECT f.row_id, f.log_price, f.log_qty,
  f.log_qty - py.predicted_log_qty AS residual_qty,
  f.log_price - pt.predicted_log_price AS residual_price
FROM `PROJECT_ID.DATASET.price_elasticity_folds` f
JOIN ML.PREDICT(MODEL `PROJECT_ID.DATASET.price_elasticity_fold0_y`,
  (SELECT * FROM `PROJECT_ID.DATASET.price_elasticity_folds` WHERE fold = 0)) py USING (row_id)
JOIN ML.PREDICT(MODEL `PROJECT_ID.DATASET.price_elasticity_fold0_t`,
  (SELECT * FROM `PROJECT_ID.DATASET.price_elasticity_folds` WHERE fold = 0)) pt USING (row_id)
WHERE f.fold = 0
-- UNION ALL the same block for folds 1..4 --
;
-- Verified: 1,130 rows total across all 5 folds' UNION ALL -- exactly the
-- panel size, confirming the row_id fix above eliminated the join-fanout bug.


-- =============================================================================
-- Step 5: Final regression on residuals -- the DML-debiased elasticity
-- =============================================================================
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.price_elasticity_dml`
OPTIONS(model_type = 'LINEAR_REG', input_label_cols = ['residual_qty'], data_split_method = 'NO_SPLIT', optimize_strategy = 'NORMAL_EQUATION') AS
SELECT residual_price, residual_qty FROM `PROJECT_ID.DATASET.price_elasticity_residuals`;

SELECT * FROM ML.WEIGHTS(MODEL `PROJECT_ID.DATASET.price_elasticity_dml`);
-- Verified: DML-corrected elasticity ~ -0.71 -- less than half the naive
-- -1.43. Roughly half the apparent price sensitivity was distribution
-- breadth/category/vendor confounding, not a true price effect.


-- =============================================================================
-- Honest finding: naive elasticity (-1.43) overstates the true effect by
-- roughly 2x once distribution breadth/category/vendor confounding is
-- removed via DML (-0.71). This is a cross-sectional, cross-brand elasticity
-- (how quantity differs across SKUs at different price points within a
-- category) -- NOT a within-SKU time-series elasticity, which this
-- state-set-pricing dataset cannot support since any single SKU's price
-- barely moves over time.
-- =============================================================================
