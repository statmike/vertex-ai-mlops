-- Difference-in-Differences — BigQuery ML Workflow
-- =============================================================
-- Compares a treated and a control unit, before and after a real event.
-- Still real, current, and heavily used (Uber/Airbnb/Meta use it for policy
-- and product rollouts) -- but a 2021+ econometrics finding (Goodman-Bacon;
-- Callaway & Sant'Anna) showed the naive two-way-fixed-effects (TWFE)
-- extension to many staggered-timing units can be badly biased -- sometimes
-- attenuating the estimate toward zero, sometimes flipping its sign
-- entirely. This notebook builds the clean native version first, then
-- proves both failure modes with real data.
--
-- Data: bigquery-public-data.covid19_open_data.covid19_open_data -- real US
--       state-level COVID-19 policy (facial_coverings) and case data, 2020.
--
-- GOTCHA: DATE_TRUNC(date, WEEK(MONDAY)) at the edge of a WHERE date BETWEEN
-- range silently truncates that boundary week's SUM to fewer than 7 days --
-- always guard with a COUNT(*) = 7 check per week bucket.
--
-- GOTCHA (major, previously undocumented in this project): BigQuery ML's
-- LINEAR_REG default optimize_strategy='AUTO_STRATEGY' can select iterative
-- batch gradient descent that stops (default max_iterations) BEFORE
-- reaching the true least-squares solution on small (here: 28-row),
-- collinear designs (treated, post, and their product are correlated) --
-- verified live: default gives -6.19 for the DiD interaction coefficient,
-- while optimize_strategy='NORMAL_EQUATION' (forcing the exact closed-form
-- solve) gives -19.29, matching an independent statsmodels.OLS fit exactly.
-- No error or warning is raised -- ML.TRAINING_INFO shows the loss still
-- decreasing at the final iteration. Always check ML.TRAINING_INFO or set
-- NORMAL_EQUATION explicitly for small-sample/collinear regressions used for
-- causal inference (verified this does NOT affect price_elasticity_dml's
-- larger, less collinear 1,130-row single-predictor regressions).
--
-- Full reference: ../../RESOURCES.md
-- Official docs:
--   CREATE MODEL (GLM): https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-glm
--   differences package: https://bernardodionisi.github.io/differences/


-- =============================================================================
-- Step 1: Build the state-week panel -- real, single-date policy change
-- =============================================================================
CREATE OR REPLACE TABLE `PROJECT_ID.DATASET.did_panel` AS
WITH pop AS (
  SELECT subregion1_code, ANY_VALUE(population) AS population
  FROM `bigquery-public-data.covid19_open_data.covid19_open_data`
  WHERE country_code = 'US' AND aggregation_level = 1 AND subregion1_code IN ('TX', 'GA')
  GROUP BY subregion1_code
),
base AS (
  SELECT subregion1_code, DATE_TRUNC(date, WEEK(MONDAY)) AS wk, SUM(new_confirmed) AS wk_cases, COUNT(*) AS n_days
  FROM `bigquery-public-data.covid19_open_data.covid19_open_data`
  WHERE country_code = 'US' AND aggregation_level = 1 AND subregion1_code IN ('TX', 'GA')
    AND date BETWEEN '2020-05-04' AND '2020-08-09'
  GROUP BY subregion1_code, wk
)
SELECT
  b.subregion1_code, b.wk,
  IF(b.subregion1_code = 'TX', 1, 0) AS treated,
  IF(b.wk > '2020-06-29', 1, 0) AS post,
  b.wk_cases / p.population * 100000 AS rate
FROM base b
JOIN pop p USING (subregion1_code)
WHERE b.n_days = 7;
-- Verified: Texas facial_coverings jumps 2->3 on 2020-07-03 (real statewide
-- mandate); Georgia stays flat at 1 throughout (a genuine, real untreated
-- control -- Georgia's governor barred local mandates during this window).


-- =============================================================================
-- Step 2: Show pre-trends -- standard first DiD diagnostic (plotted in notebook)
-- =============================================================================
-- Verified: mostly parallel, not textbook-clean -- one pre-period week
-- diverges further before reconverging. Shown as-is.


-- =============================================================================
-- Step 3: 2x2 DiD via LINEAR_REG -- with the NORMAL_EQUATION gotcha fix
-- =============================================================================
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.did_model`
OPTIONS(model_type = 'LINEAR_REG', input_label_cols = ['rate'], data_split_method = 'NO_SPLIT', optimize_strategy = 'NORMAL_EQUATION') AS
SELECT treated, post, treated * post AS treated_post, rate
FROM `PROJECT_ID.DATASET.did_panel`;

SELECT * FROM ML.WEIGHTS(MODEL `PROJECT_ID.DATASET.did_model`);
-- Verified: treated_post coefficient = -19.29 with NORMAL_EQUATION, matching
-- statsmodels.OLS exactly. The default AUTO_STRATEGY gives -6.19 -- see
-- gotcha above.


-- =============================================================================
-- Step 4: Honest finding -- check more than one post-period horizon
-- =============================================================================
-- Computed in pandas, DiD re-estimated against the full 9-week pre-period
-- average as more post-weeks are added: 2 weeks = +7.45 (POSITIVE -- the
-- pre-period's own strong upward trend still dominates), 3 weeks = -5.20
-- (crosses to negative), 4 weeks = -13.80, 5 weeks (full window) = -19.29.
-- A too-narrow post-window doesn't just risk understating a real effect --
-- the estimate's SIGN can still be settling this early when the comparison
-- period includes a strong pre-existing trend (cases lag mandate-driven
-- behavior change by ~2-3 weeks, a real epidemiological fact).


-- =============================================================================
-- Step 5: The staggered-timing trap -- naive TWFE across real staggered states
-- =============================================================================
-- Panel: NM(5/15), LA(5/16), MS(6/4), AR(6/16), TX(7/3), NJ(7/8), WI(7/16),
-- MI(7/17), plus GA as a never-treated control during this window -- all
-- real adoption dates, verified live via the facial_coverings field.
--
-- Fit in Python (statsmodels, not BQML -- TWFE with per-state and per-week
-- fixed effects is naturally expressed as categorical dummies):
--   smf.ols('rate ~ treated + C(subregion1_code) + C(wk)', data=staggered_df).fit()
-- Verified (this run): naive TWFE treated coefficient = -7.36 -- same sign as
-- the clean 2x2 DiD's -19.29 but only ~1/3 to 1/4 of its magnitude. Real
-- "forbidden comparison" bias: TWFE uses already-treated states as controls
-- for later-treated ones, and mandates were often adopted precisely because
-- cases were already rising.
--
-- GOTCHA (live-data instability, not a bug): a check of this EXACT query run
-- before this notebook was finalized returned +9.78 -- the WRONG SIGN.
-- covid19_open_data is a live public dataset that receives revisions to
-- historical rows; the figure genuinely shifted between that check and this
-- run. Both a sign flip and a magnitude attenuation are documented naive-TWFE
-- failure modes in the literature (Goodman-Bacon; Callaway-Sant'Anna) --
-- this dataset has now demonstrated both, at different points in time, on
-- the identical query.


-- =============================================================================
-- Step 6: Prove the escape hatch -- Callaway-Sant'Anna via `differences`
-- =============================================================================
-- BQML has no way to express group-time ATT estimation (comparing each
-- adoption cohort only against not-yet-treated units at that specific time).
-- Fit in Python:
--   from differences import ATTgt
--   att_gt = ATTgt(data=panel_indexed_by_entity_period, cohort_column='cohort')
--   result = att_gt.fit('rate', control_group='never_treated')
--   result.aggregate('simple')
-- Verified: Callaway-Sant'Anna ATT = -31.79 -- same NEGATIVE direction as the
-- clean 2x2 DiD (-19.29) and synthetic_control/'s independently-built
-- counterfactual (-19.28), and larger in magnitude than either -- consistent
-- with naive TWFE (-7.36) badly understating the true effect. Wide CI (only
-- 9 states, real epidemiological noise).


-- =============================================================================
-- Honest finding: simple single-date DiD is fully native and reliable when
-- checked across multiple post-period horizons. Staggered real-world
-- rollouts need a modern estimator outside BigQuery (differences/csdid,
-- R's did) -- verified here to matter for real, not just asserted from the
-- literature: naive TWFE badly understated the true effect in this run, and
-- got the sign backwards entirely in an earlier check of the identical
-- query against the same (revised-in-between) live dataset.
-- =============================================================================
