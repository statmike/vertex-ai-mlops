-- Survival Analysis (Time-to-Event) — BigQuery ML Workflow
-- =============================================================
-- Time-to-event modeling with censoring: when will a user purchase, and
-- what do you do about the majority who haven't purchased yet by the time
-- you have to stop watching? Cox Proportional Hazards -- the standard
-- survival model -- is NOT possible natively in BigQuery ML (see the
-- "Read this first" note below). What IS possible natively: Kaplan-Meier
-- curves (pure SQL) and a discrete-time hazard model (LOGISTIC_REG on a
-- reshaped person-period table). Cox itself is shown too, via `lifelines`
-- in Python, to prove the escape hatch actually works.
--
-- READ THIS FIRST: Cox Proportional Hazards' partial-likelihood estimation
-- (comparing each event against everyone else still "at risk" at that exact
-- moment) is row-DEPENDENT -- it does not map onto any BQML model type,
-- all of which fit row-INDEPENDENT likelihoods. If you need Cox PH
-- specifically, the data has to leave BigQuery for Python. Real options:
-- lifelines (used here), scikit-survival, statsmodels.duration.hazard_regression.PHReg.
--
-- Data: bigquery-public-data.ga4_obfuscated_sample_ecommerce, reusing
--       ../ga4_churn_prediction/'s exact cohort (first-time visitors,
--       2020-11-01 to 2020-12-24), asking a different question of the
--       same real users (time-to-purchase instead of 30-day churn).
--
-- GOTCHA: thelook_ecommerce was checked first (repeat-purchase rate /
-- time-to-second-order by traffic_source, gender/age_band, first-order
-- size) and showed flat ~42-46% rates / ~460-490 avg days across every
-- segment -- no real covariate-hazard signal baked into that synthetic
-- data (the same lesson found twice already in propensity_score_matching's
-- dataset search). Pivoted to the GA4 dataset instead, which is already
-- proven in this project (ga4_churn_prediction) to carry real behavioral
-- signal, and does here too.
--
-- GOTCHA: naming a CTE `hazard` while also selecting a column named
-- `hazard` from it caused an outer ROUND(hazard, 5) to resolve to the
-- CTE/table alias (a STRUCT) instead of the column --
-- "Unable to coerce type STRUCT<...> to expected type FLOAT64". Fixed by
-- renaming the CTE to `hazard_calc` (shown below).
--
-- GOTCHA (Python/lifelines side, not BigQuery): fitting CoxPHFitter on
-- device_category + n_events + n_active_days + n_sessions together failed
-- with "ConvergenceError: ... high collinearity ... singular matrix" --
-- these activity features are highly mutually correlated. Dropping to just
-- n_events hit a different error, "ConvergenceError: delta contains nan
-- value(s)" -- traced to n_events' extreme right-skew (median ~5, max
-- ~1,298). Fixed by log-transforming (log1p(n_events)) before fitting.
--
-- Full reference: ../../RESOURCES.md
-- Official docs:
--   CREATE MODEL (GLM): https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-glm
--   lifelines:          https://lifelines.readthedocs.io/


-- =============================================================================
-- Step 1: Build the cohort -- first-week features, 35-day time-to-purchase
-- =============================================================================
CREATE OR REPLACE TABLE `PROJECT_ID.DATASET.survival_cohort` AS
WITH events AS (
  SELECT
    user_pseudo_id,
    PARSE_DATE('%Y%m%d', event_date) AS event_date,
    event_name,
    device.category AS device_category
  FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
),
first_visit AS (
  SELECT user_pseudo_id, MIN(event_date) AS first_date
  FROM events
  GROUP BY user_pseudo_id
  HAVING first_date BETWEEN '2020-11-01' AND '2020-12-24'
),
feature_window AS (
  SELECT e.*, f.first_date
  FROM events e
  JOIN first_visit f USING (user_pseudo_id)
  WHERE e.event_date BETWEEN f.first_date AND DATE_ADD(f.first_date, INTERVAL 6 DAY)
),
first_week_features AS (
  SELECT
    fw.user_pseudo_id,
    ANY_VALUE(fw.device_category) AS device_category,
    COUNT(*) AS n_events,
    COUNT(DISTINCT fw.event_date) AS n_active_days,
    COUNTIF(fw.event_name = 'session_start') AS n_sessions
  FROM feature_window fw
  GROUP BY fw.user_pseudo_id
),
purchase_day AS (
  SELECT
    e.user_pseudo_id,
    MIN(DATE_DIFF(e.event_date, f.first_date, DAY)) AS days_to_purchase
  FROM events e
  JOIN first_visit f USING (user_pseudo_id)
  WHERE e.event_name = 'purchase'
    AND e.event_date BETWEEN f.first_date AND DATE_ADD(f.first_date, INTERVAL 35 DAY)
  GROUP BY e.user_pseudo_id
)
SELECT
  ff.user_pseudo_id,
  ff.device_category,
  ff.n_events,
  ff.n_active_days,
  ff.n_sessions,
  IF(pd.days_to_purchase IS NOT NULL, 1, 0) AS event_indicator,
  IFNULL(pd.days_to_purchase, 35) AS duration_days
FROM first_week_features ff
LEFT JOIN purchase_day pd USING (user_pseudo_id);
-- Verified: 162,339 cohort users, 3,343 (2.06%) purchase within 35 days --
-- the other 97.94% are censored, not "non-buyers forever."


-- =============================================================================
-- Step 2: Kaplan-Meier survival curves, segmented by first-week activity band
-- =============================================================================
WITH bands AS (
  SELECT
    user_pseudo_id,
    CASE
      WHEN n_events BETWEEN 1 AND 5 THEN '1-5'
      WHEN n_events BETWEEN 6 AND 20 THEN '6-20'
      WHEN n_events BETWEEN 21 AND 50 THEN '21-50'
      ELSE '50+'
    END AS activity_band,
    event_indicator,
    LEAST(CAST(FLOOR(duration_days / 7) AS INT64) + 1, 5) AS period
  FROM `PROJECT_ID.DATASET.survival_cohort`
),
period_stats AS (
  SELECT activity_band, period,
    COUNT(*) AS n_ending_this_period,
    SUM(event_indicator) AS n_events_this_period
  FROM bands
  GROUP BY 1, 2
),
at_risk AS (
  SELECT activity_band, period, n_events_this_period,
    SUM(n_ending_this_period) OVER (PARTITION BY activity_band ORDER BY period DESC) AS n_at_risk
  FROM period_stats
),
hazard_calc AS (  -- renamed from `hazard` -- see gotcha above
  SELECT activity_band, period, n_at_risk, n_events_this_period,
    SAFE_DIVIDE(n_events_this_period, n_at_risk) AS hazard
  FROM at_risk
)
SELECT
  activity_band, period, n_at_risk, n_events_this_period,
  ROUND(hazard, 5) AS hazard,
  ROUND(EXP(SUM(LN(1 - hazard)) OVER (PARTITION BY activity_band ORDER BY period)), 5) AS survival_prob
FROM hazard_calc
ORDER BY activity_band, period;
-- Verified: survival probability at week 5 ranges from ~99.9% (1-5 events)
-- down to ~70.2% (50+ events) -- a nearly 30-point gap, dramatic and
-- monotonic separation by activity level.


-- =============================================================================
-- Step 3: Discrete-time hazard model -- person-period reshape + LOGISTIC_REG
-- =============================================================================
CREATE OR REPLACE TABLE `PROJECT_ID.DATASET.survival_person_period` AS
SELECT
  c.user_pseudo_id,
  period AS week,
  c.device_category,
  c.n_events,
  c.n_active_days,
  c.n_sessions,
  IF(c.event_indicator = 1 AND period = LEAST(CAST(FLOOR(c.duration_days / 7) AS INT64) + 1, 5), 1, 0) AS period_event
FROM `PROJECT_ID.DATASET.survival_cohort` c
CROSS JOIN UNNEST(GENERATE_ARRAY(1, LEAST(CAST(FLOOR(c.duration_days / 7) AS INT64) + 1, 5))) AS period;
-- Verified: 799,737 person-period rows from 162,339 users; the 3,343 real
-- purchases land in their exact purchase week (period_event = 1).

CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.survival_discrete_hazard`
OPTIONS(
  model_type = 'LOGISTIC_REG',
  input_label_cols = ['period_event'],
  auto_class_weights = TRUE,
  data_split_method = 'AUTO_SPLIT'
) AS
SELECT week, device_category, n_events, n_active_days, n_sessions, period_event
FROM `PROJECT_ID.DATASET.survival_person_period`;

SELECT * FROM ML.EVALUATE(MODEL `PROJECT_ID.DATASET.survival_discrete_hazard`);
-- Verified: roc_auc ~0.901 -- strong real signal.

SELECT * FROM ML.WEIGHTS(MODEL `PROJECT_ID.DATASET.survival_discrete_hazard`);
-- Verified: n_events/n_active_days/n_sessions all carry POSITIVE weights
-- (higher activity -> higher per-period purchase hazard -> faster
-- time-to-purchase); week carries a small negative weight (hazard drifts
-- slightly lower in later weeks once activity is controlled for).


-- =============================================================================
-- Step 4: Cox Proportional Hazards via lifelines (Python, not SQL)
-- =============================================================================
-- # Pull the PERSON-LEVEL cohort (not person-period) into a DataFrame:
-- query = f"SELECT device_category, n_events, event_indicator, duration_days FROM `PROJECT_ID.DATASET.survival_cohort`"
-- cohort_df = client.query(query).to_dataframe()
--
-- import numpy as np
-- from lifelines import CoxPHFitter
--
-- cohort_df['log_n_events'] = np.log1p(cohort_df['n_events'].astype(float))  -- fixes the NaN-delta convergence error, see gotcha above
-- cohort_df['event_indicator'] = cohort_df['event_indicator'].astype(int)
-- cohort_df['duration_days'] = cohort_df['duration_days'].astype(float).clip(lower=0.01)  -- Cox requires strictly positive durations
--
-- cox_df = pd.get_dummies(cohort_df[['log_n_events', 'device_category', 'event_indicator', 'duration_days']],
--                          columns=['device_category'], drop_first=True)
-- for c in cox_df.columns:
--     if cox_df[c].dtype == bool:
--         cox_df[c] = cox_df[c].astype(int)
--
-- cph = CoxPHFitter()
-- cph.fit(cox_df, duration_col='duration_days', event_col='event_indicator')
-- cph.print_summary()
-- Verified: hazard ratio for log_n_events ~4.3 (p < 0.001), concordance
-- ~0.95 -- same direction as Step 3's positive n_events weight and Step 2's
-- KM separation. Three different techniques, one converging answer.
--
-- Two lifelines built-in plots, essentially free off the already-fitted cph:
-- cph.plot(hazard_ratios=True) -- the standard Cox forest plot (HR + 95% CI
-- per covariate, reference line at HR=1); log_n_events' entire CI sits far
-- right of 1, both device_category CIs straddle it.
-- cph.plot_partial_effects_on_outcome(covariates='log_n_events', values=[...])
-- -- holds every other covariate at its average and plots the MODEL's
-- predicted survival curve at a few representative activity levels -- the
-- model-based counterpart to Step 2's empirical KM-by-band chart. Built from
-- completely different math (fitted proportional-hazards curve vs.
-- nonparametric product-limit estimator) and lands on the same shape -- a
-- second, visual confirmation the relationship is real.


-- =============================================================================
-- Honest finding: first-week activity level is a strong, robust
-- accelerating factor for time-to-purchase, confirmed three independent
-- ways (KM curves, discrete-time hazard model, Cox PH). Cox PH required
-- leaving BigQuery -- a real, structural gap, disclosed up front, not a
-- late discovery. The discrete-time hazard model approximates but is not
-- identical to continuous-time Cox: weekly granularity coarsens exact
-- event timing, a real precision tradeoff for use cases where it matters.
-- =============================================================================
