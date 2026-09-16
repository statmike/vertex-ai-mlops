-- Causal Effect — AI.CAUSAL_EFFECT, and what it is actually doing
-- =============================================================
-- AI.CAUSAL_EFFECT (Preview) is a CausalImpact-style intervention analysis:
-- it fits a counterfactual on the pre-intervention series and reports the gap
-- afterward. It takes NO control series and NO covariates -- the docs give the
-- reason, preventing bias from experiment spillover effects.
--
-- This file measures what the function does rather than restating the docs.
-- The headline: the counterfactual is reproducible BIT-FOR-BIT with a plain
-- ARIMA_PLUS model and ML.FORECAST, and the p-value is reproducible EXACTLY
-- from two measured quantities. Every column of the output row can be rebuilt
-- from documented BigQuery pieces. What the function sells is the packaging
-- and one defensible modelling choice, not a capability you were missing.
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
--
-- Those two formulas make four predictions about transformed inputs. Run the
-- same call on `rate * 10`, `rate + 100` and `-rate` and every one holds:
--
--   transform        absolute_effect   relative_effect   p_value
--   rate              -282.606186      -0.220533         0.304812
--   rate * 10        -2826.061858      -0.220533         0.304812
--   rate + 100        -282.606186      -0.158637         0.304812
--   -rate              282.606186      -0.220533         0.304812
--
-- Reading the table: scaling moves absolute_effect and leaves relative_effect
-- alone, because the scale cancels in the ratio. A constant SHIFT does not
-- cancel -- it inflates the denominator SUM(expected) and drags
-- relative_effect toward zero (-0.2205 -> -0.1586), so relative_effect is only
-- interpretable on a ratio scale with a meaningful zero. Negation flips
-- absolute_effect but NOT relative_effect, since numerator and denominator flip
-- together. And p_value never moves under any of them: the test statistic is
-- scale- and location-free, exactly as a z on a standardized gap should be.


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
-- Example 5: Rebuilding the p-value from two measured quantities
-- =============================================================================
-- absolute_effect and relative_effect are sums (Example 3). p_value is the one
-- genuinely new quantity, so it is the one worth reconstructing. It takes two
-- ingredients, and neither is the one a textbook reaches for first.
--
-- FIRST, GET THE STANDARD ERRORS RIGHT. AI.CAUSAL_EFFECT renders interval
-- bounds and no standard error, so the tempting move is to divide the width by
-- 2 * 1.959964. Do not: ML.FORECAST on the Example 4 model reports the quantity
-- directly, and the rendered bounds are NOT forecast +/- z * standard_error.
SELECT standard_error,
       (prediction_interval_upper_bound - prediction_interval_lower_bound)
         / (2 * standard_error) AS multiplier_actually_used
FROM ML.FORECAST(MODEL `PROJECT_ID.DATASET.causal_effect_arima`,
                 STRUCT(5 AS horizon, 0.95 AS confidence_level))
ORDER BY forecast_timestamp;
-- Verified: multiplier_actually_used = 1.9564581 at all five horizons, against
-- a normal 97.5th percentile of 1.9599640. The bounds are 0.18% narrower than
-- the textbook interval, so back-solved standard errors come out 0.18% small
-- (13.82 / 30.91 / 51.71 / 75.70 / 102.50 instead of the true
-- 13.85 / 30.96 / 51.81 / 75.84 / 102.69).
--
-- Sweeping confidence_level IDENTIFIES the multiplier rather than merely
-- bounding it. It is the inverse of Abramowitz & Stegun 26.2.18, the Hastings
-- quartic approximation to the normal CDF:
--
--   P(x) = 1 - 0.5*(1 + 0.196854x + 0.115194x^2 + 0.000344x^3 + 0.019527x^4)^-4
--
-- with |error| < 2.5e-4. Inverting it reproduces every multiplier to about a
-- millionth, which is the precision at which they print:
--
--   conf_level  multiplier used  A&S inverse  A&S err    normal    normal err
--   0.80        1.282287         1.282284     -0.000002  1.281552  -0.000735
--   0.90        1.643071         1.643074     +0.000003  1.644854  +0.001782
--   0.95        1.956458         1.956457     -0.000001  1.959964  +0.003506
--   0.98        2.327237         2.327236     -0.000001  2.326348  -0.000889
--   0.99        2.587695         2.587694     -0.000002  2.575829  -0.011866
--
--   (errors are candidate minus multiplier used)
--
-- Not a Student t -- t is always WIDER than normal (2.3646 at df=7, cl=0.95).
-- Not a constant scale factor -- the normal error changes sign. Non-monotone
-- error that grows in the tail is what a fixed-degree polynomial approximation
-- does, not what a different distribution does. Say this carefully: the
-- rendered multipliers are numerically INDISTINGUISHABLE from that published
-- approximation at every level tested. That is a claim about arithmetic, not
-- about what BigQuery's source code contains.
--
-- NOW THE P-VALUE. Seven constructions tried against the observed
-- 0.30481216822794477, using the reported standard errors above:
--
--   construction                                       sd         z         p
--   independent sum of pointwise variances         141.881   -1.9919   0.046387
--   random-walk cumulation sigma^2*H(H+1)(2H+1)/6  102.686   -2.7521   0.005921
--   last step's se alone                           102.686   -2.7521   0.005921
--   H * last se                                    513.429   -0.5504   0.582025
--   psi-weight cumulation (the textbook answer)    266.696   -1.0597   0.289301
--   sum of the se's (perfectly correlated errors)  275.139   -1.0271   0.304355  <-- the one used
--   t-test on the 5 pointwise gaps                       -   -1.7404   0.156772
--
-- The psi weights are recovered from the standard errors themselves, not
-- assumed: se_h^2 = sigma^2 * sum(psi_0..psi_{h-1})^2 gives psi = [1,2,3,4,5]
-- exactly, which is what an ARIMA(0,2,0) must produce. So the psi row IS the
-- correct standard deviation of the sum of five forecast errors -- and it is
-- not the one the function uses. The function uses the sum of the se's, the
-- variance you get only if those errors are PERFECTLY correlated: the ceiling
-- of the family rather than a member of it. That is deliberate and it is
-- conservative -- the widest interval and the largest p-value any correlation
-- structure among these errors can justify. The function is built not to
-- overstate significance.
--
-- PUT THE TWO TOGETHER AND THE P-VALUE IS EXACT:
--
--   Z = absolute_effect / sum(se) = -282.606186 / 275.139104 = -1.027139297
--
--   reported by AI.CAUSAL_EFFECT          0.304812168   difference  0
--   2 * (1 - A&S_CDF(|Z|))                0.304812168   difference  0
--   2 * (1 - exact normal CDF(|Z|))       0.304354877   difference -4.57e-04
--   exact normal on the psi cumulation    0.289300596   difference -1.55e-02
--
-- No fitted constant and no free parameter: both ingredients were measured
-- before the comparison. Sizes matter here. The conservative variance choice is
-- worth 0.015054 of p-value (it inflates the sd by 3.17%); the CDF
-- approximation is worth 0.000457, 33x smaller. The MODELLING decision does the
-- work; the numerics are a rounding convention.
--
-- IT HOLDS AT THREE HORIZONS. num_post_intervention_points shortens the post
-- window without touching the pre window, so the counterfactual is unchanged
-- and only the number of points summed moves:
--
--   post points  p_value   Z = effect/sum(se)  2*(1-A&S(|Z|))  exact normal  A&S err
--   2            0.511079  +0.656775           0.511079        0.511325      0
--   3            0.735735  -0.337194           0.735735        0.735970      4.4e-16
--   5            0.304812  -1.027139           0.304812        0.304355      0
--
-- Z is POSITIVE at two post weeks: Texas ran above its counterfactual before it
-- ran below, so the cumulative gap changes sign as the window lengthens and the
-- reconstruction tracks it through the turn.
--
-- WHY THE EXACT-NORMAL RESIDUAL STRADDLES. Measured against the EXACT normal, the
-- implied sd lands at 0.999418 / 0.999073 / 1.000946 times the ceiling -- below
-- it twice, above it once. That sign change looks like evidence about the
-- variance and is not: the variance is exactly the ceiling at every horizon.
-- The straddle is the quartic's own error against the function it approximates,
-- which changes sign as |Z| moves -- the same oscillation the normal-error
-- column shows for the interval multiplier, seen through a second lens. The
-- transferable lesson: when a reproduction misses by a margin far smaller than
-- the quantity being reproduced, suspect the EVALUATION of the formula before
-- concluding the formula is wrong. A 0.09% residual on a standard deviation is
-- the size of a rounding convention, not of a missing variance component.
--
-- Two further measured facts, both consistent with the closed form:
--   * p_value is INVARIANT to confidence_level. 0.80, 0.95 and 0.99 all return
--     0.30481216822794477. So the p-value is computed from the model's internal
--     variance, not from the rendered interval widths.
--   * p_value is DETERMINISTIC across runs, so it is a closed form rather than
--     a posterior sample -- unlike the R CausalImpact package, which obtains
--     its tail area by MCMC.
--
-- THE INTERVAL THE FUNCTION DOES NOT RETURN. lower_bound and upper_bound bound
-- the COUNTERFACTUAL at each timestamp, not the cumulative gap, so the summary
-- row hands you a threshold verdict and no range. The same two ingredients
-- build the missing one:
--
--   absolute_effect +/- A&S_inverse((1+cl)/2) * sum(se)
--
--   cl     on the function's terms   textbook normal        half-width diff
--   0.80   [-635.413,   70.200]      [-635.211,   69.999]   +0.202
--   0.95   [-820.904,  255.692]      [-821.869,  256.657]   -0.965
--   0.99   [-994.582,  429.369]      [-991.318,  426.105]   +3.264
--
-- Use the ceiling variance, because that is what the reported p-value uses; a
-- psi-based interval would be narrower and would quietly contradict the p-value
-- printed beside it. Then report the interval, not the threshold verdict alone.
-- A five-week cumulative effect of -282.6 per 100k that is consistent with
-- anything from -821 to +256 says far more than "p > 0.05": that range holds a
-- large reduction, no change, and a moderate increase. The interval straddling
-- zero IS p > 1 - cl, so the p-value is recoverable from the interval and the
-- interval is not recoverable from the p-value.


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
-- The trade runs BOTH ways, and this data makes only one direction visible. A
-- control unit removes the common shock, but it also imports whatever else is
-- happening in the control. If the control is itself touched by the
-- intervention -- a neighbouring state whose residents change behaviour because
-- Texas did, a holdout market the same campaign reaches -- that spillover lands
-- in the counterfactual and biases the estimate toward zero. If the control's
-- own trajectory diverges for unrelated reasons, the divergence is charged to
-- the treatment. A univariate counterfactual cannot be contaminated either way,
-- because no other unit is in it. Here the common shock is large and the
-- spillover plausibly small, so the control-based estimates are the better
-- ones; reverse those two magnitudes and the ranking reverses with them. The
-- choice is which bias you would rather carry, not which method is correct.
--
-- Significance: AI.CAUSAL_EFFECT reports p = 0.3048, well short of 0.05, and
-- the 95% interval built in Example 5 runs from -820.9 to +255.7 cumulative.
-- Whatever the magnitude disagreement, this estimator cannot separate a mandate
-- effect from a cresting epidemic wave on 9 pre-period weeks -- and the
-- interval says that far more usefully than the threshold does.
--
-- The wider map of what each causal method in this project identifies off:
--   ../propensity_score_matching/  covariates (matched comparable units)
--   ../difference_in_differences/  a control group with parallel pre-trends
--   ../synthetic_control/          a weighted donor pool of control units
--   ../uplift_cate/                treatment assignment plus covariates
--   ../price_elasticity_dml/       covariates, via double machine learning
--   this notebook                  the treated unit's own pre-intervention history


-- =============================================================================
-- Example 7: id_cols -- many series in one call
-- =============================================================================
-- id_cols analyses each unique combination independently and returns one row
-- per series. The panel already holds 14 states, so three of them cost one call.
WITH pop AS (
  SELECT subregion1_code, ANY_VALUE(population) AS population
  FROM `bigquery-public-data.covid19_open_data.covid19_open_data`
  WHERE country_code = 'US' AND aggregation_level = 1
    AND subregion1_code IN ('TX', 'CO', 'GA')
  GROUP BY subregion1_code
),
base AS (
  SELECT subregion1_code, DATE_TRUNC(date, WEEK(MONDAY)) AS wk,
         SUM(new_confirmed) AS wk_cases, COUNT(*) AS n_days
  FROM `bigquery-public-data.covid19_open_data.covid19_open_data`
  WHERE country_code = 'US' AND aggregation_level = 1
    AND subregion1_code IN ('TX', 'CO', 'GA')
    AND date BETWEEN '2020-05-04' AND '2020-08-09'
  GROUP BY subregion1_code, wk
),
panel AS (
  SELECT b.subregion1_code, TIMESTAMP(b.wk) AS wk_ts,
         b.wk_cases / p.population * 100000 AS rate
  FROM base b JOIN pop p USING (subregion1_code)
  WHERE b.n_days = 7
)
SELECT subregion1_code, absolute_effect, relative_effect, p_value
FROM AI.CAUSAL_EFFECT(
  (SELECT * FROM panel),
  timestamp_col => 'wk_ts', data_col => 'rate',
  intervention_timestamp => TIMESTAMP '2020-07-03',
  id_cols => ['subregion1_code'])
ORDER BY subregion1_code;
-- Verified:
--   CO   133.603549    0.868572   0.093329
--   GA  -535.898927   -0.321624   0.141167
--   TX  -282.606186   -0.220533   0.304812
--
-- FINDING: id_cols FANS OUT, it does not pool. Every one of these nine numbers
-- is bit-identical to the value from a call on that state alone -- largest
-- disagreement across all nine is exactly 0.0. Nothing is shared between
-- series: no common trend, no pooled variance, no multiple-comparison
-- adjustment. It is N independent analyses with one job's overhead, which is
-- the cost saving and also the caveat. Three states here, three p-values, and
-- nothing in the output warns that testing more series raises the chance one of
-- them clears 0.05 by accident.
--
-- Note Colorado's +0.87 relative_effect. A positive "effect" in a state whose
-- mask mandate this analysis is not about is the univariate counterfactual's
-- weakness stated in one number: it charges the nationwide summer 2020 surge to
-- whatever happened at the intervention timestamp. See Example 6.


-- =============================================================================
-- Example 8: The arguments in full
-- =============================================================================
-- Verified live against the function signature.
--
--   timestamp_col               STRING, required. Column holding the TIMESTAMP.
--   data_col                    STRING, required. The metric.
--   intervention_timestamp      TIMESTAMP LITERAL, required. Splits pre/post.
--   id_cols                     ARRAY<STRING>, optional. STRING/INT64 columns
--                               identifying separate series; each unique
--                               combination is analysed independently and
--                               returns its own row -- demonstrated, and shown
--                               to be bit-identical to separate calls, in
--                               Example 7.
--   num_post_intervention_points INT64, optional. Cap on post-intervention
--                               points included. Defaults to everything from
--                               intervention_timestamp to the end of the series.
--   confidence_level            FLOAT64 in [0, 1), default 0.95. Affects the
--                               pointwise lower_bound/upper_bound only -- NOT
--                               p_value.
--   output_time_series          BOOL, default FALSE. TRUE adds the pointwise
--                               columns shown in Example 2.
--
-- NOT accepted: `model` (see the header GOTCHA), `horizon`.
--
-- NOT RETURNED: an interval on the effect itself. lower_bound/upper_bound bound
-- the COUNTERFACTUAL at each timestamp, not the cumulative gap. Example 5 builds
-- the missing one.
--
-- NOT PRODUCED: a model artifact. The function fits its counterfactual and
-- discards it, so there is nothing to inspect, re-use, grant access to, or
-- apply to later data, and ML.EXPLAIN_FORECAST has nothing to point at.
-- Example 4's rebuild is the only way to get one.
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
