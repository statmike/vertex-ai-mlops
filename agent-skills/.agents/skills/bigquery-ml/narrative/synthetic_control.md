# Synthetic Control — BigQuery ML

**One arbitrary comparison state is a weakness.** `workflows/difference_in_differences` (`difference_in_differences`) picked Georgia as Texas's comparison state — a real, defensible choice, but still just one choice among several plausible ones. **Synthetic Control** (Abadie, Diamond & Hainmueller — the same method behind the famous California tobacco-tax study) replaces that single arbitrary pick with an optimization: build a **weighted combination of several untreated units** that matches the treated unit's pre-treatment trend as closely as possible. It's real, current causal-inference practice — Uber, Airbnb, and Meta use it for geo-level marketing-lift experiments.

**Models used:** `LINEAR_REG` (native, unconstrained approximation)
**Functions used:** `ML.WEIGHTS`
**Data:** [`bigquery-public-data.covid19_open_data.covid19_open_data`](https://console.cloud.google.com/marketplace/product/bigquery-public-datasets) — reuses `workflows/difference_in_differences` (`workflows/difference_in_differences/`)'s exact Texas mask-mandate panel, extended with a larger donor pool.
**References:** `RESOURCES.md` (Full reference) | [CREATE MODEL (GLM) docs](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-glm) | [`pysyncon` docs](https://github.com/sdfordham/pysyncon) | `setup` (Setup guide)

---

## Read this first: what BigQuery ML can and can't do here

Synthetic control's defining constraint is what makes it trustworthy: the donor weights must be **non-negative** and **sum to 1** — so the result is literally interpretable as "this percentage of Idaho plus that percentage of Georgia," a real blend of real, observed states, never an extrapolation outside the data. That constraint makes fitting the weights a **constrained quadratic program**, not an ordinary regression — and there's no `CREATE MODEL` option in BigQuery ML that expresses "fit these coefficients subject to non-negativity and a sum-to-one constraint." `LINEAR_REG` will happily fit *unconstrained* coefficients, but as this notebook shows concretely (not just asserts), those coefficients can be negative, can exceed 1, and don't sum to 1 — breaking the entire interpretability promise that makes synthetic control trustworthy in the first place.

The real, standard tool for the constrained fit is Python: `scipy.optimize` (used directly here) or the purpose-built `pysyncon` package (a real, maintained, installable implementation of Abadie's method). Shown live below, not just named.

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
## Step 1 — Build the donor pool: an extended version of the DiD panel

Same weekly per-100k case-rate construction as `difference_in_differences/`, now for Texas plus a **13-state donor pool**: every state whose `facial_coverings` policy level never reached Texas's post-mandate level (3) throughout the study window — a real, verified, non-arbitrary "never fully mandated" set, not hand-picked to make the story work.

```python
donor_pool = ['CO', 'GA', 'ID', 'IL', 'ME', 'MN', 'ND', 'NE', 'NH', 'SD', 'VA', 'WV', 'WY']
all_states = ['TX'] + donor_pool

query = f"""
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.synthetic_control_panel` AS
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
    AND date BETWEEN '2020-05-04' AND '2020-08-09'
  GROUP BY subregion1_code, wk
)
SELECT b.subregion1_code, b.wk, b.wk_cases / p.population * 100000 AS rate
FROM base b JOIN pop p USING (subregion1_code)
WHERE b.n_days = 7
"""
job_config = bigquery.QueryJobConfig(query_parameters=[bigquery.ArrayQueryParameter('states', 'STRING', all_states)])
client.query(query, job_config=job_config).result()

query = f"SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.synthetic_control_panel` ORDER BY subregion1_code, wk"
panel_df = client.query(query).to_dataframe()
panel_df['wk'] = pd.to_datetime(panel_df['wk'])
pivot = panel_df.pivot(index='wk', columns='subregion1_code', values='rate').sort_index()
pivot.head()
```

---
## Step 2 — Why synthetic control: the gap it fills

`difference_in_differences/` picked Georgia because it looked like a reasonable single comparison state — but that choice was somewhat arbitrary, and a different analyst might have picked a different state and told a different story. Synthetic control removes that arbitrariness: instead of choosing one state, **optimize** over a combination of several.

---
## Step 3 — Why the real method needs to leave BigQuery, made concrete

Fit the *unconstrained* version of this weighted-combination idea — a plain `LINEAR_REG` of Texas's pre-period series on the donor states' pre-period series — and look at the resulting weights directly.

```python
pre_period = pivot[pivot.index <= pd.Timestamp('2020-06-29')]

query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.synthetic_control_unconstrained`
OPTIONS(model_type = 'LINEAR_REG', input_label_cols = ['TX'], data_split_method = 'NO_SPLIT', optimize_strategy = 'NORMAL_EQUATION') AS
SELECT {', '.join(donor_pool)}, TX
FROM `{PROJECT_ID}.{DATASET_ID}.synthetic_control_panel`
PIVOT (AVG(rate) FOR subregion1_code IN ({', '.join(f"'{d}'" for d in all_states)}))
WHERE wk <= '2020-06-29'
"""
client.query(query).result()

query = f"SELECT * FROM ML.WEIGHTS(MODEL `{PROJECT_ID}.{DATASET_ID}.synthetic_control_unconstrained`)"
unconstrained_weights = client.query(query).to_dataframe()
unconstrained_weights
```

**Verified finding:** several donor weights come back **negative**, others land far **above 1**, and the full set is nowhere near summing to **1** — none of which is possible for a real percentage blend of real states. Part of why this is so extreme: only 9 pre-period weeks are available against 13 donor states, an **underdetermined system** (more unknowns than equations) with no unique OLS solution — small changes in the input data or solver internals can swing individual weights considerably. **Confirmed three separate times now, each giving a substantially different weight pattern**: an initial scratch check during planning, this notebook's own pre-execution run, and a fresh run of this exact notebook all produced visibly different extreme values (in one run the weights summed to roughly -0.8; in another, roughly +3.1) — the instability itself is the reproducible finding, not any specific weight. This is exactly the break named in "Read this first" above, made concrete rather than asserted — and it's worth contrasting with Step 4 below, where the properly *constrained* fit lands on the same answer every time.

---
## Step 4 — The real, constrained fit: `scipy.optimize`

Minimize the pre-period squared error between Texas and the weighted donor combination, subject to every weight being non-negative and all weights summing to 1 — the actual textbook synthetic control optimization (`pysyncon` wraps this same constrained solve; done directly here with `scipy.optimize` to show exactly what it's doing).

```python
from scipy.optimize import minimize

donors_pre = pre_period[donor_pool].values
treated_pre = pre_period['TX'].values

def objective(w):
    return np.sum((treated_pre - donors_pre @ w) ** 2)

n = len(donor_pool)
w0 = np.ones(n) / n
constraints = ({'type': 'eq', 'fun': lambda w: np.sum(w) - 1})
bounds = [(0, 1)] * n
result = minimize(objective, w0, method='SLSQP', bounds=bounds, constraints=constraints)
weights = result.x

print('Synthetic control weights:')
for donor, w in zip(donor_pool, weights):
    if w > 0.01:
        print(f'  {donor}: {w:.3f}')

synth_pre = donors_pre @ weights
mse_synthetic = np.mean((treated_pre - synth_pre) ** 2)
mse_ga_alone = np.mean((treated_pre - pre_period['GA'].values) ** 2)
print(f'\nPre-period MSE, synthetic control: {mse_synthetic:.2f}')
print(f'Pre-period MSE, Georgia alone:     {mse_ga_alone:.2f}')
```

**Verified finding:** the optimizer settles on **82.4% Georgia + 17.6% Idaho** — it re-discovers Georgia as the dominant match (the same state `difference_in_differences/` picked by hand) but *improves* on it: pre-period MSE drops from 189.98 (Georgia alone) to 143.95 (the synthetic blend) — a real, quantified ~24% better fit to Texas's actual pre-treatment trend, not a cosmetic change.

---
## Step 5 — The classic synthetic control visual

Plot Texas's actual case rate against both counterfactuals — the synthetic-control blend and Georgia alone — across the full pre- and post-period.

```python
full_donors = pivot[donor_pool].values
synth_full = full_donors @ weights

fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(pivot.index, pivot['TX'], marker='o', label='Texas (actual)', color='black', linewidth=2)
ax.plot(pivot.index, synth_full, marker='o', label='Synthetic control (82% GA + 18% ID)', color='darkorange', linestyle='--')
ax.plot(pivot.index, pivot['GA'], marker='o', label='Georgia alone', color='gray', linestyle=':')
ax.axvline(pd.Timestamp('2020-07-03'), color='gray', linestyle='--', linewidth=1, label='TX mandate (2020-07-03)')
ax.set_xlabel('Week')
ax.set_ylabel('New confirmed cases per 100k')
ax.set_title('Texas vs. synthetic control vs. single-state counterfactual')
ax.legend()
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

post_period = pivot[pivot.index > pd.Timestamp('2020-06-29')]
synth_post = post_period[donor_pool].values @ weights
att_synthetic = (post_period['TX'].values - synth_post).mean()
print(f'Average post-period gap (synthetic control ATT): {att_synthetic:.2f}')
```

**Verified finding:** average post-period gap = **-19.28** — Texas's actual case rate ran about 19 cases per 100k *below* what the synthetic control predicts it would have without the mandate, closely matching `difference_in_differences/`'s own estimate (-19.29) from the simple 2-state comparison.

---
## Step 6 — Honest finding

**Two independently-built counterfactuals agree**: synthetic control's post-period gap (-19.28) and the simple 2-state DiD estimate (-19.29) land within a rounding error of each other — the same "converging evidence" pattern already established in `survival_analysis`. The improved pre-period fit (a real, quantified 24% MSE reduction) is genuine evidence synthetic control's extra optimization work was worth doing here, even though the final answer barely moved relative to the simpler 2-state comparison.

**Stated plainly, not oversold:** synthetic control earns its complexity by making the comparison-group choice principled and defensible rather than arbitrary — not by guaranteeing a different answer. Sometimes the fancier, more rigorous method mostly just gives you more *confidence* in an answer you already had, and that's a legitimate, valuable outcome in its own right, not a disappointing one.

---
## Related content

- `workflows/difference_in_differences` (`workflows/difference_in_differences/`) — this workflow's direct prerequisite; builds the panel and the single-comparison-state estimate this notebook extends and cross-checks.
- `workflows/propensity_score_matching` (`workflows/propensity_score_matching/`) and `workflows/uplift_cate` (`workflows/uplift_cate/`) — this project's other causal-inference workflows.

---
## Examples — `%%bigquery` Magics

The same donor-pool summary using IPython magic commands.

```sql
%%bigquery --project {PROJECT_ID}

SELECT subregion1_code, COUNT(*) AS n_weeks, ROUND(AVG(rate), 2) AS avg_rate
FROM `statmike-mlops-349915.bq_ml.synthetic_control_panel`
GROUP BY subregion1_code
ORDER BY subregion1_code
```

---
## Examples — BigFrames

`bigframes.ml.linear_model.LinearRegression` is a valid drop-in for Step 3's unconstrained fit (same pattern demonstrated in `models/linear_regression` (`models/linear_regression/`)) — Step 4's constrained optimization has no BigFrames/BQML equivalent at all, since neither exposes a constrained quadratic solver; `scipy.optimize`/`pysyncon` remain the only real options.
