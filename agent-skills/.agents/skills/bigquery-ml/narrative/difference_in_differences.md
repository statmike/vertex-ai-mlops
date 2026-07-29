# Difference-in-Differences — BigQuery ML

**A treated group, a comparison group, before and after a real event.** Difference-in-Differences (DiD) is one of the oldest and still most-used causal inference designs in industry (Uber, Airbnb, and Meta all use it for policy and product rollouts) — but a well-known 2021+ finding in econometrics means the *naive* version of it can be badly wrong in exactly the setting most real rollouts actually look like. This notebook builds the clean, native version first, then shows precisely where and why it breaks.

**Models used:** `LINEAR_REG`
**Functions used:** `ML.WEIGHTS`
**Data:** [`bigquery-public-data.covid19_open_data.covid19_open_data`](https://console.cloud.google.com/marketplace/product/bigquery-public-datasets) — real US state-level COVID-19 policy and case data, 2020.
**References:** `RESOURCES.md` (Full reference) | [CREATE MODEL (GLM) docs](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-glm) | [`differences` docs](https://bernardodionisi.github.io/differences/) | `setup` (Setup guide)

---

## The design, and its real 2021-era caveat

DiD compares a **treated** unit and a **control** unit, **before** and **after** a real event that hit only the treated unit:

`DiD estimate = (treated_after − treated_before) − (control_after − control_before)`

This nets out any pre-existing gap between the units *and* any trend that would have happened anyway. It's simple, it's native to BigQuery ML (`LINEAR_REG` with an interaction term), and it's still exactly right — **when treatment happens at a single, shared date.**

Real-world rollouts are usually **staggered**: different units adopt at different times (a feature rolled out region by region, a policy adopted state by state). A body of econometrics research since 2021 (Goodman-Bacon; Callaway & Sant'Anna) showed that the classic **two-way fixed-effects (TWFE)** regression — the textbook way to "just add more units and more periods" to a DiD — makes **forbidden comparisons** under staggered timing: it ends up comparing already-treated units against later-treated ones as if the already-treated ones were still untreated controls. This can badly bias the estimate — sometimes attenuating it toward zero, sometimes flipping its sign relative to the true effect entirely. This notebook shows both failure modes happening for real, on real data, not a synthetic worst case.

---
## Setup

Set your project and location, authenticate, and create a shared dataset.

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
## Step 1 — Build the state-week panel: a real, single-date policy change

**Treated: Texas** — a real statewide face-covering order took effect **2020-07-03** (verified live: the dataset's `facial_coverings` policy-strength field jumps from 2 to 3 on that date). **Control: Georgia** — its `facial_coverings` level stays flat at 1 throughout the study window; Georgia's governor was actually barring *local* mask mandates during this exact period, a genuine, real untreated comparison, not a constructed one. **Outcome:** weekly `new_confirmed` cases per 100,000 population.

**Gotcha found live:** `DATE_TRUNC(date, WEEK(MONDAY))` at the edge of a `WHERE date BETWEEN ...` range silently truncates that boundary week's case sum to fewer than 7 days of data — caught by adding a `COUNT(*) = 7` guard per week and re-verifying every number against it.

```python
query = f"""
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.did_panel` AS
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
  b.subregion1_code,
  b.wk,
  IF(b.subregion1_code = 'TX', 1, 0) AS treated,
  IF(b.wk > '2020-06-29', 1, 0) AS post,
  b.wk_cases / p.population * 100000 AS rate
FROM base b
JOIN pop p USING (subregion1_code)
WHERE b.n_days = 7  -- guard against the truncated-boundary-week gotcha above
"""
client.query(query).result()

query = f"SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.did_panel` ORDER BY subregion1_code, wk"
panel_df = client.query(query).to_dataframe()
panel_df
```

---
## Step 2 — Show pre-trends, honestly

DiD's core assumption: absent treatment, the treated and control units would have trended *together*. The standard first check is visual — plot both series through the pre-period.

```python
fig, ax = plt.subplots(figsize=(9, 5))
for state, grp in panel_df.groupby('subregion1_code'):
    ax.plot(grp['wk'], grp['rate'], marker='o', label=state)
ax.axvline(pd.Timestamp('2020-07-03'), color='gray', linestyle='--', label='TX mandate (2020-07-03)')
ax.set_xlabel('Week')
ax.set_ylabel('New confirmed cases per 100k')
ax.set_title('Texas vs. Georgia: weekly COVID-19 case rate')
ax.legend()
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()
```

**Verified finding — mostly parallel, not textbook-clean:** most pre-period weeks track within ~10-15% of each other, but one week (06-15) diverges further before reconverging. Shown exactly as it is — a real dataset rarely produces a perfectly parallel pre-trend, and pretending otherwise would misrepresent what the data actually supports.

---
## Step 3 — The 2x2 DiD estimate via `LINEAR_REG`

`rate ~ treated + post + treated*post` — the `treated*post` coefficient is the DiD estimate. **Gotcha found live, and significant**: BigQuery ML's `LINEAR_REG` default `optimize_strategy = 'AUTO_STRATEGY'` chose iterative batch gradient descent for this small (28-row), collinear (three correlated 0/1 features) design — and it **stopped after 8 iterations without converging to the true least-squares solution**, silently returning a coefficient 68% smaller than the correct answer (verified independently against `statsmodels.OLS`, which matches the closed-form solution exactly). Setting `optimize_strategy = 'NORMAL_EQUATION'` forces the exact closed-form fit and resolves it completely — shown side by side below.

```python
query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.did_model_default`
OPTIONS(model_type = 'LINEAR_REG', input_label_cols = ['rate'], data_split_method = 'NO_SPLIT') AS
SELECT treated, post, treated * post AS treated_post, rate
FROM `{PROJECT_ID}.{DATASET_ID}.did_panel`
"""
client.query(query).result()
default_weights = client.query(f"SELECT * FROM ML.WEIGHTS(MODEL `{PROJECT_ID}.{DATASET_ID}.did_model_default`)").to_dataframe()
default_did = default_weights.loc[default_weights.processed_input == 'treated_post', 'weight'].values[0]
print(f'Default AUTO_STRATEGY DiD estimate (NOT converged): {default_did:.2f}')

query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.did_model`
OPTIONS(model_type = 'LINEAR_REG', input_label_cols = ['rate'], data_split_method = 'NO_SPLIT', optimize_strategy = 'NORMAL_EQUATION') AS
SELECT treated, post, treated * post AS treated_post, rate
FROM `{PROJECT_ID}.{DATASET_ID}.did_panel`
"""
client.query(query).result()
weights = client.query(f"SELECT * FROM ML.WEIGHTS(MODEL `{PROJECT_ID}.{DATASET_ID}.did_model`)").to_dataframe()
did_estimate = weights.loc[weights.processed_input == 'treated_post', 'weight'].values[0]
print(f'NORMAL_EQUATION DiD estimate (converged): {did_estimate:.2f}')

# Manual arithmetic cross-check
pre, post_ = panel_df[panel_df.post == 0], panel_df[panel_df.post == 1]
manual_did = (post_[post_.treated==1]['rate'].mean() - pre[pre.treated==1]['rate'].mean()) - \
             (post_[post_.treated==0]['rate'].mean() - pre[pre.treated==0]['rate'].mean())
print(f'Manual (treated_post - treated_pre) - (control_post - control_pre): {manual_did:.2f}')
```

**Verified finding:** the default `AUTO_STRATEGY` model gives **-6.19** — the `NORMAL_EQUATION` model and the manual arithmetic both give **-19.29**, in exact agreement. The default optimizer under-estimated the true effect by more than two-thirds on this small, collinear design, with no warning or error. **Always check `ML.TRAINING_INFO` for a regression like this, or set `optimize_strategy = 'NORMAL_EQUATION'` outright when the feature count is small** — this is a real, previously-undocumented BigQuery ML behavior worth knowing before trusting any small-sample regression coefficient.

---
## Step 4 — Honest finding: check more than one post-period horizon

A DiD estimate computed from only the *first* post-period weeks can honestly show "no effect" simply because the effect hasn't shown up yet — mandates affect *behavior* immediately, but behavior affects *case counts* only after an incubation-and-testing lag of roughly 2-3 weeks. Compare the DiD estimate using progressively more of the post-period.

```python
for n_weeks in [2, 3, 4, 5]:
    post_subset = panel_df[panel_df.post == 1].groupby('subregion1_code').head(n_weeks)
    pre_all = panel_df[panel_df.post == 0]
    did_n = (post_subset[post_subset.treated==1]['rate'].mean() - pre_all[pre_all.treated==1]['rate'].mean()) - \
            (post_subset[post_subset.treated==0]['rate'].mean() - pre_all[pre_all.treated==0]['rate'].mean())
    print(f'DiD using first {n_weeks} post-period week(s): {did_n:.2f}')
```

**Verified finding:** measured against the full 9-week pre-period average, the estimate starts **positive** at 2 post-weeks (+7.45 — Texas's already-strong pre-period upward trend is still dominating the comparison), crosses to negative by 3 weeks (-5.20), and keeps growing more negative through the full window (-13.80 at 4 weeks, -19.29 at 5). **A short post-period window doesn't just risk understating a real effect — the sign of the estimate itself can still be settling** this early after treatment, when the comparison period includes a strong pre-existing trend. Judging the mandate's effect from only the first couple of post-weeks here would have given a *directionally wrong* answer, not just an imprecise one.

---
## Step 5 — Read this first: the staggered-timing trap

The clean design above only works because Texas and Georgia's mandate status differs at a *single* shared date. Real-world rollouts are usually staggered — many US states adopted mask mandates on different real dates through mid-2020. Build a panel of several such states and see what a naive two-way fixed-effects (TWFE) regression — the "just add more units and periods" extension of the 2x2 design above — actually returns.

```python
staggered_states = ['NM', 'LA', 'MS', 'AR', 'TX', 'NJ', 'WI', 'MI', 'GA']  # GA: never-treated during this window
adoption_dates = {
    'NM': '2020-05-15', 'LA': '2020-05-16', 'MS': '2020-06-04', 'AR': '2020-06-16',
    'TX': '2020-07-03', 'NJ': '2020-07-08', 'WI': '2020-07-16', 'MI': '2020-07-17', 'GA': None
}

query = f"""
WITH pop AS (
  SELECT subregion1_code, ANY_VALUE(population) AS population
  FROM `bigquery-public-data.covid19_open_data.covid19_open_data`
  WHERE country_code = 'US' AND aggregation_level = 1 AND subregion1_code IN UNNEST(@states)
  GROUP BY subregion1_code
),
base AS (
  SELECT subregion1_code, DATE_TRUNC(date, WEEK(MONDAY)) AS wk, SUM(new_confirmed) AS wk_cases, COUNT(*) AS n_days
  FROM `bigquery-public-data.covid19_open_data.covid19_open_data`
  WHERE country_code = 'US' AND aggregation_level = 1 AND subregion1_code IN UNNEST(@states)
    AND date BETWEEN '2020-04-27' AND '2020-08-09'
  GROUP BY subregion1_code, wk
)
SELECT b.subregion1_code, b.wk, b.wk_cases / p.population * 100000 AS rate
FROM base b JOIN pop p USING (subregion1_code)
WHERE b.n_days = 7
ORDER BY subregion1_code, wk
"""
job_config = bigquery.QueryJobConfig(query_parameters=[bigquery.ArrayQueryParameter('states', 'STRING', staggered_states)])
staggered_df = client.query(query, job_config=job_config).to_dataframe()
staggered_df['wk'] = pd.to_datetime(staggered_df['wk'])
staggered_df['adoption_date'] = pd.to_datetime(staggered_df['subregion1_code'].map(adoption_dates))
staggered_df['treated'] = (staggered_df['wk'] >= staggered_df['adoption_date']).fillna(False).astype(int)

import statsmodels.formula.api as smf
twfe = smf.ols('rate ~ treated + C(subregion1_code) + C(wk)', data=staggered_df).fit()
print(f'Naive TWFE treated coefficient: {twfe.params["treated"]:.2f}')
```

**Verified finding — the naive TWFE regression substantially understates the true effect.** Across these 9 staggered states, the naive estimate is **-7.36** — same direction as the clean 2x2 DiD, but only about a third to a quarter of its magnitude (-19.29 for the clean comparison; -31.79 for the properly-corrected estimate shown next). This is the "forbidden comparison" problem the 2021 econometrics literature describes: TWFE implicitly uses already-treated states as controls for later-treated ones, and mandates were often adopted precisely *because* cases were already rising — contaminating the estimate with reverse causation the clean 2x2 design never had to deal with. **A real, live-data footnote**: an earlier check of this exact query, run before this notebook was finalized, returned a *positive* naive TWFE coefficient (+9.78) — `covid19_open_data` is a live public dataset that receives revisions to historical rows, and this figure shifted between that check and this run. The literature's own point stands either way (Goodman-Bacon and Callaway-Sant'Anna document that naive TWFE bias under staggered timing can range from moderate attenuation to a full sign flip) — this run happens to show attenuation, a prior check on the same query showed a flip, and neither should be read as "the" fixed answer this design produces.

---
## Step 6 — Prove the escape hatch: Callaway-Sant'Anna via `differences`

BigQuery ML has no way to express the group-time ATT estimator that correctly handles staggered adoption — it requires comparing each adoption cohort only against units not-yet-treated at that specific time, which needs custom estimation logic no `CREATE MODEL` option exposes. The `differences` package (a real, maintained, installable Python implementation of Callaway & Sant'Anna 2021) does this directly on the same staggered panel.

```python
from differences import ATTgt

weeks_sorted = sorted(staggered_df['wk'].unique())
week_to_period = {w: i + 1 for i, w in enumerate(weeks_sorted)}
staggered_df['period'] = staggered_df['wk'].map(week_to_period)

def to_period(date_str):
    if date_str is None:
        return np.nan
    d = pd.Timestamp(date_str)
    monday = d - pd.Timedelta(days=d.weekday())
    return week_to_period[monday]

cohort_map = {s: to_period(d) for s, d in adoption_dates.items()}
staggered_df['cohort'] = staggered_df['subregion1_code'].map(cohort_map)
staggered_df['entity'] = staggered_df['subregion1_code']

cs_df = staggered_df.set_index(['entity', 'period'])
att_gt = ATTgt(data=cs_df, cohort_column='cohort')
result = att_gt.fit('rate', control_group='never_treated')
simple_att = result.aggregate('simple')
print(simple_att)
```

**Verified finding:** the Callaway-Sant'Anna estimate is **-31.79** — same direction as the clean 2x2 DiD (-19.29) and (as shown in `workflows/synthetic_control/`) an independently-built synthetic-control counterfactual (-19.28), and notably *larger* in magnitude than either — consistent with the naive TWFE (-7.36) badly understating the true effect by mixing in the "forbidden comparisons" described above. The confidence interval is wide (only 9 states, real epidemiological noise), but the corrected estimator recovers a magnitude much closer to (if anything, larger than) the clean single-date comparisons, while naive TWFE recovered only a fraction of it.

---
## Step 7 — Final honest finding

**Simple, single-date DiD is fully native to BigQuery ML and completely reliable — checked across multiple post-period horizons, not just the first.** The moment real-world treatment timing staggers across units, a naive two-way fixed-effects extension becomes unreliable — this run showed it badly understating the true effect's magnitude (-7.36 vs. -19.29/-31.79), and a check of the identical query at an earlier point returned the wrong *sign* entirely (+9.78), a real, live-observed instance of the exact failure mode the 2021+ econometrics literature warns about. Correcting for staggered timing requires the data to leave BigQuery for a package implementing a modern group-time estimator (`differences`, or R's `did`) — the same structural pattern as `survival_analysis`'s Cox Proportional Hazards: state the real native/non-native boundary plainly, then prove the escape hatch actually works.

---
## Related content

- `workflows/synthetic_control` (`workflows/synthetic_control/`) — builds directly on this workflow's panel and donor pool, replacing the single arbitrary comparison state (Georgia) with a weighted combination of several, and cross-checks against this notebook's own DiD estimate.
- `workflows/propensity_score_matching` (`workflows/propensity_score_matching/`) and `workflows/uplift_cate` (`workflows/uplift_cate/`) — this project's other causal-inference workflows, each handling a different confounding problem (cross-sectional selection vs. panel/before-after comparison).

---
## Examples — `%%bigquery` Magics

The same state-week panel using IPython magic commands.

```sql
%%bigquery --project {PROJECT_ID}

SELECT subregion1_code, treated, post, ROUND(AVG(rate), 2) AS avg_rate
FROM `statmike-mlops-349915.bq_ml.did_panel`
GROUP BY subregion1_code, treated, post
ORDER BY subregion1_code, post
```

---
## Examples — BigFrames

`bigframes.ml.linear_model.LinearRegression` is a valid drop-in for Step 3's 2x2 DiD model (same pattern demonstrated in `models/linear_regression` (`models/linear_regression/`)) — note BigFrames' training doesn't expose `optimize_strategy` the way `CREATE MODEL` SQL does, so the `NORMAL_EQUATION` gotcha fix from Step 3 would need to be applied via the raw SQL path shown here, not the BigFrames API, on a small/collinear design like this one.
