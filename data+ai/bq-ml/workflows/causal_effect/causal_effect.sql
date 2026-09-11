-- Causal Effect — AI.CAUSAL_EFFECT, and what it is actually doing
-- =============================================================
-- AI.CAUSAL_EFFECT (Preview) is a CausalImpact-style intervention analysis:
-- it fits a counterfactual on the pre-intervention series and reports the gap
-- afterward. It takes NO control series and NO covariates -- the docs give the
-- reason, preventing bias from experiment spillover effects.
--
-- This file measures what the function does rather than restating the docs.
-- The headline: the counterfactual is reproducible BIT-FOR-BIT with a plain
-- ARIMA_PLUS model and ML.FORECAST, so the counterfactual is not what you are
-- paying for. The p-value is, and that is the one piece that does NOT
-- reproduce under any construction tried here.
--
-- Data: bigquery-public-data.covid19_open_data.covid19_open_data -- the SAME
--       Texas weekly per-100k case-rate series used by
--       ../difference_in_differences/ and ../synthetic_control/, so all three
--       estimators are measured on identical numbers in identical units.
--       2020-05-04 .. 2020-08-09, 14 weekly points: 9 pre, 5 post.
--       Texas facial_coverings jumps 2->3 on 2020-07-03 (real statewide mandate).
--
-- GOTCHA: intervention_timestamp must be a TIMESTAMP *literal*.
--   TIMESTAMP '2020-07-03'   works
--   TIMESTAMP("2020-07-03")  fails: "expects the intervention_timestamp argument
--                            to be a TIMESTAMP literal, but TIMESTAMP was provided."
--
-- GOTCHA: there is no `model` argument. AI.FORECAST accepts
-- model => 'TimesFM 2.5'; AI.CAUSAL_EFFECT rejects it with "Named argument
-- model not found in signature for call to function AI.CAUSAL_EFFECT". The
-- ARIMA_PLUS engine is fixed and cannot be swapped for TimesFM.
--
-- GOTCHA: no model artifact is produced. Verified by counting models in the
-- dataset before and after (identical) and by reading INFORMATION_SCHEMA.JOBS
-- (one SELECT job, parent_job_id NULL, no child jobs, ~13 slot-seconds). So
-- there is no ML.ARIMA_EVALUATE, no ML.EXPLAIN_FORECAST, and no way to audit
-- the counterfactual that produced the p-value. Example 4 recovers all of that
-- by building the model yourself.
--
-- GOTCHA (the one that matters for interpretation): a univariate counterfactual
-- attributes the ENTIRE deviation from the unit's own past trend to the
-- intervention. On this data that is -56.52 per week, against -19.29 from
-- difference-in-differences and -19.28 from synthetic control -- same sign,
-- roughly 3x the magnitude. The control-unit methods net out the nationwide
-- summer 2020 surge that Georgia and the donor pool also experienced; this
-- function has no way to see it. See Example 6.
--
-- Full reference: ../../RESOURCES.md
-- Official docs:
--   AI.CAUSAL_EFFECT: https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-causal-effect
--   ARIMA_PLUS:       https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-time-series
--   CausalImpact (Brodersen et al. 2015): https://google.github.io/CausalImpact/


-- =============================================================================
-- Example 1: The whole analysis in one call
-- =============================================================================
-- The series construction is shared by every example below. n_days = 7 guards
-- the boundary weeks -- DATE_TRUNC at the edge of a BETWEEN range silently
-- truncates that week's SUM to fewer than 7 days.
WITH pop AS (
  SELECT subregion1_code, ANY_VALUE(population) AS population
  FROM `bigquery-public-data.covid19_open_data.covid19_open_data`
  WHERE country_code = 'US' AND aggregation_level = 1 AND subregion1_code = 'TX'
  GROUP BY subregion1_code
),
base AS (
  SELECT subregion1_code, DATE_TRUNC(date, WEEK(MONDAY)) AS wk,
         SUM(new_confirmed) AS wk_cases, COUNT(*) AS n_days
  FROM `bigquery-public-data.covid19_open_data.covid19_open_data`
  WHERE country_code = 'US' AND aggregation_level = 1 AND subregion1_code = 'TX'
    AND date BETWEEN '2020-05-04' AND '2020-08-09'
  GROUP BY subregion1_code, wk
),
tx AS (
  SELECT TIMESTAMP(b.wk) AS wk_ts, b.wk_cases / p.population * 100000 AS rate
  FROM base b JOIN pop p USING (subregion1_code)
  WHERE b.n_days = 7
)
SELECT * FROM AI.CAUSAL_EFFECT(
  (SELECT * FROM tx),
  timestamp_col          => 'wk_ts',
  data_col               => 'rate',
  intervention_timestamp => TIMESTAMP '2020-07-03'
);
-- Verified 2026-09-11:
--   absolute_effect     -282.6061857566028
--   relative_effect       -0.22053334761305518
--   p_value                0.30481216822794477
--   prob_causal_effect     0.6951878317720552   (exactly 1 - p_value)
--   status                 ''                   (empty on success)
--
-- Fully deterministic: four consecutive runs with --nouse_cache returned all
-- four values identical to the last digit. Worth stating because most AI.*
-- functions are not -- the TimesFM-backed ones are not reproducible even with
-- the model version pinned.


-- =============================================================================
-- Example 2: The pointwise view -- output_time_series => TRUE
-- =============================================================================
-- Adds is_post_intervention, predicted_<data_col>, lower_bound, upper_bound
-- per row. The four aggregate columns repeat on every row.
-- (WITH clause from Example 1 omitted for brevity; it is unchanged.)
SELECT wk_ts, is_post_intervention, rate, predicted_rate, lower_bound, upper_bound
FROM AI.CAUSAL_EFFECT(
  (SELECT * FROM tx),
  timestamp_col          => 'wk_ts',
  data_col               => 'rate',
  intervention_timestamp => TIMESTAMP '2020-07-03',
  output_time_series     => TRUE
)
ORDER BY wk_ts;
-- Verified: the 9 pre-intervention rows carry the actual value and NULL for
-- predicted/lower/upper -- the counterfactual only exists after the cut.
--
-- wk_ts        rate      predicted_rate  lower_bound  upper_bound
-- 2020-07-06   217.594   191.831         164.741      218.920
-- 2020-07-13   227.726   224.062         163.488      284.636
-- 2020-07-20   194.287   256.293         154.934      357.653
-- 2020-07-27   188.897   288.525         140.150      436.900
-- 2020-08-03   170.356   320.756         119.856      521.657
--
-- FINDING: the counterfactual is a PERFECT STRAIGHT LINE. Consecutive
-- differences are 32.23138525 every single week, to 8 decimals. With 9
-- pre-period points on a steeply accelerating epidemic curve, auto_arima had
-- nothing to fit but a linear drift -- so the counterfactual asserts Texas
-- would have kept adding 32.2 cases per 100k every week indefinitely. That is
-- the assumption the p-value is testing against, and it is worth seeing
-- plainly before trusting the number.
--
-- The intervals are exactly symmetric about the forecast (verified to 1e-14)
-- and widen from +/-27.1 at week 1 to +/-200.9 at week 5 -- accumulating
-- forecast error, which is why a five-week-out counterfactual is nearly
-- uninformative here.


-- =============================================================================
-- Example 3: Reproduce absolute_effect and relative_effect by hand
-- =============================================================================
-- Both are plain sums over the post-intervention window. No inference involved.
WITH ts AS (
  SELECT * FROM AI.CAUSAL_EFFECT(
    (SELECT * FROM tx),
    timestamp_col => 'wk_ts', data_col => 'rate',
    intervention_timestamp => TIMESTAMP '2020-07-03', output_time_series => TRUE)
  WHERE is_post_intervention
)
SELECT
  SUM(rate - predicted_rate)                    AS manual_absolute_effect,
  SUM(rate - predicted_rate) / SUM(predicted_rate) AS manual_relative_effect,
  ANY_VALUE(absolute_effect)                    AS reported_absolute_effect,
  ANY_VALUE(relative_effect)                    AS reported_relative_effect
FROM ts;
-- Verified: manual -282.6061857566028 / -0.22053334761305518, both matching
-- the reported values exactly.
--   absolute_effect = SUM(actual - expected)
--   relative_effect = SUM(actual - expected) / SUM(expected)


-- =============================================================================
-- Example 4: Reproduce the counterfactual itself -- and get the model back
-- =============================================================================
-- Train ARIMA_PLUS on the pre-intervention window only, with default options.
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.causal_effect_arima`
OPTIONS(
  model_type              = 'ARIMA_PLUS',
  time_series_timestamp_col = 'wk_ts',
  time_series_data_col      = 'rate'
) AS
SELECT * FROM tx WHERE wk_ts < TIMESTAMP '2020-07-03';

SELECT forecast_timestamp, forecast_value,
       prediction_interval_lower_bound, prediction_interval_upper_bound
FROM ML.FORECAST(MODEL `PROJECT_ID.DATASET.causal_effect_arima`,
                 STRUCT(5 AS horizon, 0.95 AS confidence_level))
ORDER BY forecast_timestamp;
-- FINDING, and the point of this notebook: BIT-FOR-BIT IDENTICAL to Example 2.
--   191.830609900223     vs  191.830609900223
--   224.06199515156794   vs  224.06199515156794
--   256.2933804029129    vs  256.2933804029129
--   288.5247656542578    vs  288.5247656542578
--   320.75615090560274   vs  320.75615090560274
-- and every one of the ten interval bounds matches to the last digit as well.
--
-- So AI.CAUSAL_EFFECT's counterfactual IS ARIMA_PLUS + ML.FORECAST on default
-- options. Nothing proprietary, nothing tuned. The convenience is real -- one
-- call instead of two, and no model to manage -- but the counterfactual is not
-- the thing you cannot build yourself.
--
-- What the model gets you that the function does not:
--   ML.ARIMA_EVALUATE   -- the chosen (p,d,q), drift, detected seasonality
--   ML.EXPLAIN_FORECAST -- the trend/seasonal/holiday decomposition
--   ML.ARIMA_COEFFICIENTS
-- For a *causal* claim this matters: the function asks you to trust a
-- counterfactual you cannot inspect.


-- =============================================================================
-- Example 5: The p-value does NOT reproduce
-- =============================================================================
-- absolute_effect and relative_effect are sums (Example 3). p_value is the one
-- genuinely new quantity, and it is the one that resists reconstruction.
--
-- Six constructions tried against the observed 0.30481216822794477, using the
-- pointwise standard errors backed out of the intervals
-- (se_h = (upper_h - lower_h) / (2 * 1.959964) = 13.82, 30.91, 51.71, 75.70, 102.50):
--
--   construction                                        z         p
--   independent sum of pointwise variances           -1.9954   0.045997
--   random-walk cumulation  sigma^2*H(H+1)(2H+1)/6   -2.7571   0.005832
--   last step's se alone                             -2.7571   0.005832
--   H * last se                                      -0.5514   0.581349
--   sum of the se's (perfectly correlated errors)    -1.0290   0.303489  <-- closest
--   t-test on the 5 pointwise gaps                   -1.7404   0.081795
--
-- The closest is 0.303489 against 0.304812 -- 0.4% off, near but not equal.
-- Working backwards, the observed p implies a standard deviation of 275.40 on
-- the cumulative effect; the sum of the se's is 274.65. Fitting a t
-- distribution to close the gap needs df ~ 200, which is not a natural
-- quantity for 9 pre-period points, so that is coincidence rather than
-- mechanism.
--
-- Two further constraints on any explanation, both measured:
--   * p_value is INVARIANT to confidence_level. 0.80, 0.95 and 0.99 all return
--     0.30481216822794477. So the p-value is computed from the model's internal
--     variance, not from the rendered interval widths.
--   * p_value is DETERMINISTIC across runs, so it is a closed form rather than
--     a posterior sample -- unlike the R CausalImpact package, which obtains
--     its tail area by MCMC.
--
-- NO MECHANISM CLAIMED. What is established: the counterfactual is plain
-- ARIMA_PLUS, the two effect columns are plain sums, and the p-value is the
-- only part of AI.CAUSAL_EFFECT that is not reconstructible from documented
-- BigQuery pieces. That is the honest answer to "what does this function buy
-- me" -- the cumulative significance test, which is also the part that is
-- easiest to get wrong by hand.


-- =============================================================================
-- Example 6: Three estimators, one dataset, identical units
-- =============================================================================
-- The same Texas mask-mandate question, measured three structurally different
-- ways on the same weekly per-100k series:
--
--   method                       estimate (per post-period week)   identifies off
--   difference-in-differences    -19.29                            a control state (GA)
--   synthetic control            -19.28                            a weighted donor pool
--   AI.CAUSAL_EFFECT             -56.52  (= -282.61 / 5 weeks)     the unit's own past
--
-- All three agree on SIGN. They do not agree on magnitude: the univariate
-- counterfactual is about 2.9x larger.
--
-- This is not a defect in any of them -- it is what the different identifying
-- assumptions buy. AI.CAUSAL_EFFECT asks "how far did Texas fall below its own
-- prior trajectory," and answers with the whole gap, including the part caused
-- by the nationwide summer 2020 surge cresting everywhere at once. DiD and
-- synthetic control ask "how far did Texas fall below comparable states," and
-- so subtract that common shock out. Georgia and the 13-state donor pool lived
-- through the same surge; a straight-line extrapolation of Texas's own June
-- did not.
--
-- Significance: AI.CAUSAL_EFFECT reports p = 0.3048, well short of 0.05.
-- Whatever the magnitude disagreement, this estimator does not clear
-- conventional significance on this data, and the notebook says so rather than
-- leading with the point estimate.
--
-- The wider map of what each causal method in this project identifies off:
--   ../propensity_score_matching/  covariates (matched comparable units)
--   ../difference_in_differences/  a control group with parallel pre-trends
--   ../synthetic_control/          a weighted donor pool of control units
--   ../uplift_cate/                treatment assignment plus covariates
--   ../price_elasticity_dml/       covariates, via double machine learning
--   this notebook                  the treated unit's own pre-intervention history


-- =============================================================================
-- Example 7: The arguments in full
-- =============================================================================
-- Verified live against the function signature.
--
--   timestamp_col               STRING, required. Column holding the TIMESTAMP.
--   data_col                    STRING, required. The metric.
--   intervention_timestamp      TIMESTAMP LITERAL, required. Splits pre/post.
--   id_cols                     ARRAY<STRING>, optional. STRING/INT64 columns
--                               identifying separate series; each unique
--                               combination is analysed independently and
--                               returns its own row.
--   num_post_intervention_points INT64, optional. Cap on post-intervention
--                               points included. Defaults to everything from
--                               intervention_timestamp to the end of the series.
--   confidence_level            FLOAT64 in [0, 1), default 0.95. Affects
--                               lower_bound/upper_bound only -- NOT p_value.
--   output_time_series          BOOL, default FALSE. TRUE adds the pointwise
--                               columns shown in Example 2.
--
-- NOT accepted: `model` (see the header GOTCHA), `horizon`.
--
-- status is '' on success and carries the error string otherwise; the common
-- one is "The time series data is too short," which needs at least three
-- points. Note that three points is the hard floor, not a sensible minimum --
-- this notebook's 9 pre-period points already produce a counterfactual with no
-- seasonal structure and intervals that reach +/-200 by week five.


-- =============================================================================
-- Cleanup
-- =============================================================================
DROP MODEL IF EXISTS `PROJECT_ID.DATASET.causal_effect_arima`;
