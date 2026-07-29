# Survival Analysis (Time-to-Event) — BigQuery ML

**A third kind of question.** Every other workflow in this project either predicts an outcome or estimates a causal effect. This one asks *when* something will happen, and what to do about the people it hasn't happened to yet. **Survival analysis** (time-to-event analysis) models the time until an event — a purchase, a churn, a machine failure, a death — while correctly handling **censoring**: subjects who haven't experienced the event by the time you have to stop watching aren't "no event," they're "not yet observed," and treating them as either extreme (drop them, or count them as "no event forever") biases the answer.

**Models used:** `LOGISTIC_REG` (as a discrete-time hazard model) — plus, outside BigQuery entirely, `lifelines.CoxPHFitter` (see "Read this first" below).
**Functions used:** `ML.EVALUATE`, `ML.PREDICT`, `ML.WEIGHTS`
**Data:** [`bigquery-public-data.ga4_obfuscated_sample_ecommerce`](https://console.cloud.google.com/marketplace/product/bigquery-public-datasets) — a real Google Merchandise Store GA4 export. Reuses `workflows/ga4_churn_prediction` (`workflows/ga4_churn_prediction/`)'s exact cohort definition (first-time visitors, 2020-11-01 to 2020-12-24), asking a different question of the same real users.
**References:** `RESOURCES.md` (Full reference) | [CREATE MODEL (GLM) docs](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-glm) | [`lifelines` docs](https://lifelines.readthedocs.io/) | `setup` (Setup guide)

---

## Read this first: what BigQuery ML can and can't do here

**Cox Proportional Hazards — the most widely used survival model in statistics — is not possible directly in BigQuery ML, and no amount of clever SQL changes that.** Cox's defining trick is *partial likelihood*: at every observed event time, it compares the subject who just had the event against everyone else still "at risk" at that exact moment (the *risk set*), and estimates coefficients from that comparison — without ever needing to specify a baseline hazard shape. That's a fundamentally different estimation procedure from anything BQML offers. Every BQML model type (`LOGISTIC_REG`, `BOOSTED_TREE_*`, `LINEAR_REG`, ...) fits **row-independent** likelihoods — each row contributes to the loss on its own, independent of every other row. Cox's row-*dependent*, risk-set-based partial likelihood simply doesn't map onto that paradigm. There's no `CREATE MODEL` incantation that gets you there.

If you need Cox PH specifically, the honest answer is: **the data has to leave BigQuery and be fit in Python with a real survival-analysis package.** Real options, roughly in order of how often they're reached for:
- **[`lifelines`](https://lifelines.readthedocs.io/)** — the most accessible pure-Python implementation. Used in Step 4 below to prove this bridge actually works, not just to name-drop it.
- **[`scikit-survival`](https://scikit-survival.readthedocs.io/)** — scikit-learn-compatible, more ML-oriented (random survival forests, gradient-boosted Cox models).
- **[`statsmodels.duration.hazard_regression.PHReg`](https://www.statsmodels.org/stable/generated/statsmodels.duration.hazard_regression.PHReg.html)** — Cox regression inside the broader `statsmodels` ecosystem.

This is a real, non-trivial tradeoff worth stating plainly: every other model type in this project keeps your data and compute entirely inside BigQuery. Cox PH breaks that story — the data has to be pulled into a Python runtime's memory and re-fit outside the warehouse. That's slower, adds a data-movement step, and forfeits BigQuery's scale for whatever your Python environment can hold in memory.

**What genuinely *is* possible natively in BigQuery ML** — and is built for real below:
1. **Kaplan-Meier survival curves** (Step 2) — no model at all, just SQL implementing the standard product-limit estimator.
2. **A discrete-time hazard model** (Step 3) — reshape the data so each subject contributes one row per time period they were at risk, then fit an ordinary `LOGISTIC_REG` predicting the per-period event probability. This is a real, standard technique — not an invented workaround — that approximates Cox's hazard-based framing using a model type BQML already has.

Step 4 then fits the real Cox model too, via `lifelines`, so you can see all three approaches converge on the same underlying finding — and judge the tradeoff for yourself rather than take it on faith.

---
## Setup

Set your project and location, authenticate, and create a shared dataset. No connection needed — this workflow only uses `LOGISTIC_REG`, plain SQL, and (in Step 4) a local Python package.

```python
PROJECT_ID = 'statmike-mlops-349915'  # <-- Replace with your project ID
LOCATION = 'US'  # BigQuery dataset location
DATASET_ID = 'bq_ml'  # Shared dataset across all bq-ml notebooks
```

### Environment

> **Already set up the project environment?** The cell below is a no-op — packages are already in your kernel. See the `setup` (Setup Reference) for details.
>
> **Running standalone** (Colab, Colab Enterprise, Vertex AI Workbench)? The cell below installs required packages into your current kernel.

```python
from google.cloud import bigquery
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

client = bigquery.Client(project=PROJECT_ID)
pd.set_option('display.max_colwidth', None)

# Create the shared dataset (idempotent)
dataset_ref = bigquery.DatasetReference(PROJECT_ID, DATASET_ID)
dataset = bigquery.Dataset(dataset_ref)
dataset.location = LOCATION
client.create_dataset(dataset, exists_ok=True)
print(f'Dataset {PROJECT_ID}.{DATASET_ID} ready')

# Register %%bigquery cell magic (auto-loaded in Colab, needed elsewhere)
%load_ext bigquery_magics
```

---
## Step 1 — Build the cohort: real users, real censoring

Reuses `workflows/ga4_churn_prediction` (`ga4_churn_prediction`)'s exact cohort (users whose first-ever event falls between 2020-11-01 and 2020-12-24) and first-week engagement features (`n_events`, `n_active_days`, `n_sessions`, `device_category`) — already proven informative in this dataset. New here: a **35-day follow-up window** from each user's entry date, chosen so even the latest entrant (2020-12-24) reaches 2021-01-28 — still inside the dataset's actual range (through 2021-01-31) — giving every cohort member a uniform, non-staggered follow-up length.

- `event_indicator` = 1 if the user purchased within 35 days of their first visit, else 0 (**censored** — they simply hadn't purchased by the time observation stopped, not "never will").
- `duration_days` = days from first visit to purchase if observed, else 35 (the censoring time).

```python
query = f"""
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.survival_cohort` AS
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
LEFT JOIN purchase_day pd USING (user_pseudo_id)
"""
client.query(query).result()

query = f"""
SELECT COUNT(*) AS n_users, SUM(event_indicator) AS n_purchased, ROUND(AVG(event_indicator), 4) AS purchase_rate
FROM `{PROJECT_ID}.{DATASET_ID}.survival_cohort`
"""
client.query(query).to_dataframe()
```

**Verified finding:** 162,339 cohort users, only 3,343 (2.06%) purchase within 35 days — the other 97.94% are censored, not "non-buyers forever." Survival analysis is the right tool precisely because that majority can't just be dropped or relabeled without biasing every estimate that follows.

---
## Step 2 — Kaplan-Meier survival curves, by activity level (pure SQL, no model)

The Kaplan-Meier estimator needs no model — just the standard product-limit formula: within each weekly period, `hazard = events_this_period / at_risk_at_start_of_period`, and `survival = running product of (1 - hazard)` across periods. Segmenting by **first-week activity level** (`n_events`, bucketed) shows whether the curves separate — the direct visual evidence for Step 3's covariate. (Device category alone showed only mild variation in earlier exploration — activity volume is this dataset's real signal, consistent with `ga4_churn_prediction`'s own finding.)

```python
query = f"""
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
  FROM `{PROJECT_ID}.{DATASET_ID}.survival_cohort`
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
hazard_calc AS (
  SELECT activity_band, period, n_at_risk, n_events_this_period,
    SAFE_DIVIDE(n_events_this_period, n_at_risk) AS hazard
  FROM at_risk
)
SELECT
  activity_band, period, n_at_risk, n_events_this_period,
  ROUND(hazard, 5) AS hazard,
  ROUND(EXP(SUM(LN(1 - hazard)) OVER (PARTITION BY activity_band ORDER BY period)), 5) AS survival_prob
FROM hazard_calc
ORDER BY activity_band, period
"""
km = client.query(query).to_dataframe()

band_order = ['1-5', '6-20', '21-50', '50+']
fig, ax = plt.subplots(figsize=(10, 5))
for band in band_order:
    grp = km[km['activity_band'] == band]
    ax.plot(grp['period'], grp['survival_prob'], label=f'{band} events', marker='o', drawstyle='steps-post')
ax.set_xlabel('Week')
ax.set_ylabel('Survival probability (has not purchased)')
ax.set_title('Kaplan-Meier: time to first purchase, by first-week activity level')
ax.legend(title='First-week events')
plt.show()

km
```

**Verified finding — dramatic, monotonic separation:** by the end of week 5, survival probability (the share who *haven't* purchased) is ~99.9% for the lightest-activity band (1-5 events) but only ~70.2% for the heaviest (50+ events) — a nearly 30-point gap driven entirely by first-week activity volume. This is real, strong evidence that activity level is a genuine hazard covariate, not a flat/uninformative one — exactly what Step 3's discrete-time model and Step 4's Cox model both go on to quantify.

---
## Step 3 — Discrete-time hazard model: `LOGISTIC_REG` approximating Cox

Reshape the cohort into **person-period format**: one row per user per week they were still at risk (period 1 through their event/censoring week), with a binary `period_event` flag set only in the exact week of an observed purchase. Fitting an ordinary `LOGISTIC_REG` on this reshaped table — with the period number itself as a feature — lets a row-independent classifier approximate a non-constant baseline hazard, which is exactly what makes this a genuine discrete-time survival model rather than just "a classifier on some columns."

**Gotcha found live:** naming a CTE `hazard` while also selecting a column named `hazard` from it caused an outer `ROUND(hazard, 5)` to resolve to the CTE/table alias (a `STRUCT`) instead of the column — `"Unable to coerce type STRUCT<...> to expected type FLOAT64"`. Fixed by renaming the CTE (`hazard_calc`, used above already).

```python
query = f"""
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.survival_person_period` AS
SELECT
  c.user_pseudo_id,
  period AS week,
  c.device_category,
  c.n_events,
  c.n_active_days,
  c.n_sessions,
  IF(c.event_indicator = 1 AND period = LEAST(CAST(FLOOR(c.duration_days / 7) AS INT64) + 1, 5), 1, 0) AS period_event
FROM `{PROJECT_ID}.{DATASET_ID}.survival_cohort` c
CROSS JOIN UNNEST(GENERATE_ARRAY(1, LEAST(CAST(FLOOR(c.duration_days / 7) AS INT64) + 1, 5))) AS period
"""
client.query(query).result()

query = f"""
SELECT week, COUNT(*) AS n_at_risk, SUM(period_event) AS n_events
FROM `{PROJECT_ID}.{DATASET_ID}.survival_person_period`
GROUP BY 1 ORDER BY 1
"""
client.query(query).to_dataframe()
```

One row per user per at-risk week — 799,737 person-period rows from 162,339 users, with the 3,343 real purchases distributed across their exact purchase week (`period_event = 1`). Now fit `LOGISTIC_REG` on this reshaped table, predicting the per-period purchase probability from the period number plus the same activity/device covariates used in the KM curves. `auto_class_weights = TRUE` — purchases are a small minority of person-period rows, same imbalance-handling reasoning as `ga4_churn_prediction`.

```python
query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.survival_discrete_hazard`
OPTIONS(
  model_type = 'LOGISTIC_REG',
  input_label_cols = ['period_event'],
  auto_class_weights = TRUE,
  data_split_method = 'AUTO_SPLIT'
) AS
SELECT week, device_category, n_events, n_active_days, n_sessions, period_event
FROM `{PROJECT_ID}.{DATASET_ID}.survival_person_period`
"""
client.query(query).result()
print('Model survival_discrete_hazard created')

query = f"SELECT * FROM ML.EVALUATE(MODEL `{PROJECT_ID}.{DATASET_ID}.survival_discrete_hazard`)"
client.query(query).to_dataframe()
```

**Verified finding:** `roc_auc` ~0.901 — strong real signal, consistent with the dramatic KM separation above. (`precision` is low by construction, same `ML.EVALUATE`-default-threshold-under-imbalance artifact seen in `propensity_score_matching` — irrelevant here since the coefficients, not the classification decision, are what this step is after.)

```python
query = f"SELECT * FROM ML.WEIGHTS(MODEL `{PROJECT_ID}.{DATASET_ID}.survival_discrete_hazard`)"
client.query(query).to_dataframe()
```

**Verified finding:** `n_events`, `n_active_days`, and `n_sessions` all carry **positive** weights — higher first-week activity means a *higher* per-period hazard of purchasing, i.e. a *faster* time-to-purchase. `week` carries a small negative weight — once activity level is controlled for, the per-period hazard drifts slightly lower in later weeks (most purchases that are going to happen, happen early). Both directions agree with the KM curves above, and (as shown next) with the Cox model fit entirely outside BigQuery.

---
## Step 4 — Cox Proportional Hazards via `lifelines`: the Python bridge, proven working

This is the escape hatch named in "Read this first" above, shown live rather than just described. Pull the **person-level** (not person-period) cohort into a DataFrame and fit `lifelines.CoxPHFitter` directly.

**Two real convergence errors hit along the way, both instructive:**
- Fitting on `device_category` + `n_events` + `n_active_days` + `n_sessions` together failed outright: `ConvergenceError: ... Suspicion is high collinearity. ... A singular matrix detected`. These three activity features are highly mutually correlated (someone with many events almost always also has many active days and sessions) — Cox's Newton-Raphson optimizer can't invert a near-singular covariance matrix built from redundant predictors.
- Dropping to just `n_events` (+ `device_category`) removed the collinearity but hit a *different* error: `ConvergenceError: delta contains nan value(s)`. `n_events` turned out to be extremely right-skewed (median ~5, but max ~1,298 — a ~250x spread) — exactly the kind of unstandardized, skewed covariate that destabilizes Cox's optimizer. Log-transforming it (`log1p(n_events)`) resolved this cleanly.

Neither error was a BigQuery ML problem — both are ordinary `lifelines`/Cox numerical-stability issues, the same ones you'd hit fitting Cox PH on this data in any Python environment.

```python
from lifelines import CoxPHFitter

query = f"""
SELECT device_category, n_events, event_indicator, duration_days
FROM `{PROJECT_ID}.{DATASET_ID}.survival_cohort`
"""
cohort_df = client.query(query).to_dataframe()

cohort_df['log_n_events'] = np.log1p(cohort_df['n_events'].astype(float))
cohort_df['event_indicator'] = cohort_df['event_indicator'].astype(int)
cohort_df['duration_days'] = cohort_df['duration_days'].astype(float).clip(lower=0.01)  # Cox requires strictly positive durations

cox_df = pd.get_dummies(
    cohort_df[['log_n_events', 'device_category', 'event_indicator', 'duration_days']],
    columns=['device_category'], drop_first=True
)
for c in cox_df.columns:
    if cox_df[c].dtype == bool:
        cox_df[c] = cox_df[c].astype(int)

cph = CoxPHFitter()
cph.fit(cox_df, duration_col='duration_days', event_col='event_indicator')
cph.print_summary()
print(f'Concordance index: {cph.concordance_index_:.4f}')
```

```python
fig, ax = plt.subplots(figsize=(7, 3))
cph.plot(hazard_ratios=True, ax=ax)
ax.set_title('Cox hazard ratios (log scale) with 95% CI')
plt.tight_layout()
plt.show()
```

This is the standard **forest plot** for a Cox model — every covariate's hazard ratio and 95% CI, with a reference line at `HR = 1` (no effect). `log_n_events`'s point estimate and entire CI sit far to the right of 1 (a large, unambiguous *increase* in hazard); `device_category`'s two CIs both straddle 1 — device alone isn't a reliable hazard signal here, the same conclusion `ga4_churn_prediction` reached about device for churn.

```python
n_events_values = [1, 10, 50, 200]
log_values = [np.log1p(v) for v in n_events_values]

fig, ax = plt.subplots(figsize=(9, 5))
cph.plot_partial_effects_on_outcome(covariates='log_n_events', values=log_values, cmap='viridis', ax=ax)
ax.set_xlabel('Days since first visit')
ax.set_ylabel('Predicted survival probability (has not purchased)')
ax.legend([f'{v} first-week events' for v in n_events_values], title='Held at representative activity level')
ax.set_title('Cox-predicted survival curves at representative activity levels')
plt.tight_layout()
plt.show()
```

This is `plot_partial_effects_on_outcome` — it holds every other covariate at its observed average and asks the fitted Cox model "what survival curve would this population show if everyone had exactly this many first-week events?" It's the model-based counterpart to Step 2's empirical KM-by-band chart, not a re-plot of the same data: Step 2 groups real users into bands and computes their actual observed survival; this asks the fitted equation what it predicts at a few representative points. The two are built from completely different math (nonparametric product-limit vs. a fitted proportional-hazards curve) and land on the same shape — a second, visual confirmation that the relationship is real and not an artifact of one particular estimator.

**Verified finding — three independent techniques, one converging answer:** the Cox model's hazard ratio for `log_n_events` is **~4.3** (95% CI 4.21-4.43, p < 0.001) — a large, highly significant *increase* in hazard (faster time-to-purchase) with higher first-week activity, with a concordance index of ~0.95. The direction matches both the KM curves (heavier-activity bands cross into purchase far sooner) and the discrete-time hazard model's positive `n_events` weight. Same real relationship, found three different ways — via pure SQL, via `LOGISTIC_REG` inside BigQuery, and via Cox outside it.

---
## Step 5 — Honest finding

**First-week activity level is a strong, robust accelerating factor for time-to-purchase**, confirmed three independent ways: Kaplan-Meier curves separate dramatically by activity band (Step 2), a discrete-time hazard model fit entirely inside BigQuery ML shows a strong positive coefficient and `roc_auc` ~0.901 (Step 3), and a true Cox Proportional Hazards model fit outside BigQuery shows a hazard ratio of ~4.3 for the same signal with concordance ~0.95 (Step 4). Three genuinely different estimation procedures landing on the same direction and the same rough magnitude of effect is real, converging evidence — not a coincidence of how each technique happens to be built.

**What this workflow cannot avoid, stated plainly:**
- **Cox PH required leaving BigQuery.** That's not a limitation of this notebook's design — it's a real, structural gap in BigQuery ML, honestly disclosed up front rather than discovered halfway through. If your workflow needs to stay entirely inside BigQuery, the discrete-time hazard model (Step 3) is the native answer, not a compromise dressed up as one.
- **The discrete-time hazard model approximates, but isn't identical to, continuous-time Cox.** Weekly-period granularity coarsens exact event timing — a purchase on day 8 and a purchase on day 13 look identical to the model (both "period 2"). For many business questions this coarsening is irrelevant; for use cases needing precise timing (e.g. clinical time-to-event with day-level resolution mattering), that's a real precision tradeoff worth knowing about before choosing this technique.

---
## Related content

- `workflows/ga4_churn_prediction` (`workflows/ga4_churn_prediction/`) — the same cohort and dataset, asking a related but distinct question (will this user churn in a fixed window, vs. when will they purchase).
- `models/logistic_regression` (`models/logistic_regression/`) — `LOGISTIC_REG` mechanics in depth (used here for its discrete-time hazard role, not its usual predictive role).
- `workflows/propensity_score_matching` (`workflows/propensity_score_matching/`) — the other workflow in this project built around a technique BigQuery ML doesn't fully cover natively, handled with the same "state the limitation honestly, then show what is possible" approach.

---
## Examples — `%%bigquery` Magics

The same cohort summary using IPython magic commands — write SQL directly in cells without Python string wrapping.

```sql
%%bigquery --project {PROJECT_ID}

SELECT event_indicator, COUNT(*) AS n_users, ROUND(AVG(duration_days), 2) AS avg_duration_days
FROM `statmike-mlops-349915.bq_ml.survival_cohort`
GROUP BY event_indicator
ORDER BY event_indicator
```

---
## Examples — BigFrames

No direct BigFrames equivalent for the Kaplan-Meier SQL, the person-period reshape, or the `lifelines` Cox bridge — those are hand-rolled SQL/Python here, same as this project's other multi-technique workflows (`workflows/propensity_score_matching` (`propensity_score_matching`), `workflows/ensembling` (`ensembling`)). `bigframes.ml.linear_model.LogisticRegression` is a valid drop-in for Step 3's discrete-time hazard model itself (same pattern demonstrated in `models/logistic_regression` (`models/logistic_regression/`)) — the reshaping and Cox steps would still be plain SQL/Python either way.
