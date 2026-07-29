# Price Elasticity via Double Machine Learning — BigQuery ML

**A naive regression here would lie to you.** Simply regressing quantity sold on price captures correlation, not the causal effect of price on demand — real confounders (how widely a product is distributed, its category, its brand) drive both price and volume at once, biasing a plain regression. **Double Machine Learning (DML)** — the current (2018+, Chernozhukov et al.) industry standard for causal effect estimation from observational data — fixes this: fit two ML models to strip out what the confounders explain, then estimate the effect from what's left over.

**Models used:** `LINEAR_REG`, `BOOSTED_TREE_REGRESSOR`
**Functions used:** `ML.WEIGHTS`, `ML.PREDICT`
**Data:** [`bigquery-public-data.iowa_liquor_sales.sales`](https://console.cloud.google.com/marketplace/product/bigquery-public-datasets) — real Iowa liquor wholesale/retail transactions, already used elsewhere in this project for `workflows/hierarchical_forecasting` (`workflows/hierarchical_forecasting/`).
**References:** `RESOURCES.md` (Full reference) | [CREATE MODEL (GLM) docs](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-glm) | `setup` (Setup guide)

---

## Why this, and why DML specifically

Price elasticity — how much demand changes when price changes — is one of the oldest questions in economics, and one of the easiest to get wrong with modern data. Naive regression-based elasticity estimates are now considered unreliable in industry precisely because real-world price variation is rarely random: prices differ across products for reasons (distribution reach, brand positioning, category) that *also* independently affect how much sells. A regression that ignores this bakes the confounding straight into the "elasticity" number.

**Double Machine Learning**, introduced by Chernozhukov et al. (2018) and now the standard approach at companies doing real pricing analytics, handles this cleanly:
1. Fit a flexible ML model predicting the **outcome** (quantity sold) from confounders — *excluding* price.
2. Fit a second flexible ML model predicting the **treatment** (price) from the *same* confounders.
3. Compute each model's **residuals** — the part of quantity and the part of price that the confounders *can't* explain.
4. Regress the residuals against each other. What's left over, by construction, isn't explained by the confounders — so this regression isolates price's own effect.

This is the Frisch-Waugh-Lovell theorem in action, done with ML models instead of linear ones, using genuine **cross-fitting** (each model predicts on data it never trained on) to avoid overfitting bias — the same real technique used in `workflows/cross_validation/`, repurposed here for causal inference rather than model evaluation. Every step below runs natively in BigQuery ML — no external package needed for this one.

### Where real elasticity varies across a category

Iowa's retail liquor prices are **state-set**, not market-driven — meaning any single product's price is fixed over time (already confirmed elsewhere in this project), which rules out a time-series design. But prices genuinely vary **across** different brands/products *within* the same category, driven by real cost and positioning differences — the same category-management approach real retailers use when they don't have a controlled price experiment to run.

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
## Step 1 — Build the SKU panel: one row per product, across 8 real liquor categories

One row per `item_number` (a real, distinct product SKU): average price, total bottles sold, and real confounders — `category_name`, `vendor_name`, `pack` (bottles per case), and `log_n_stores` (distribution breadth — how many distinct stores carried it). Restricted to 750ml bottles across 8 major categories, 2022-2023, with at least 50 bottles sold (filters out one-off/discontinued SKUs). A synthetic `row_id` is added since `item_number` alone isn't a safe join key here — a handful of SKUs appear under more than one category.

```python
query = f"""
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.price_elasticity_panel` AS
SELECT
  ROW_NUMBER() OVER() AS row_id,
  item_number,
  category_name,
  vendor_name,
  pack,
  log_price,
  log_qty,
  log_n_stores
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
)
"""
client.query(query).result()

query = f"""
SELECT COUNT(*) AS n_skus, COUNT(DISTINCT vendor_name) AS n_vendors,
  ROUND(CORR(log_price, log_qty), 4) AS corr_price_qty,
  ROUND(CORR(log_price, log_n_stores), 4) AS corr_price_n_stores
FROM `{PROJECT_ID}.{DATASET_ID}.price_elasticity_panel`
"""
client.query(query).to_dataframe()
```

**Verified finding:** 1,130 real SKUs across ~154 vendors (this count shifts by one or two on a rerun — `iowa_liquor_sales` is a still-updated public dataset). `log(price)` and `log(quantity)` are strongly negatively correlated (-0.52) — a real demand curve. But `log(price)` also correlates with `log(n_stores)` (-0.28): pricier SKUs are stocked in *fewer* stores, a genuine confounder. Any regression treating price as the only thing driving quantity will attribute some of distribution breadth's effect to price instead.

---
## Step 2 — Naive elasticity: what a plain regression says

A simple `LINEAR_REG` of `log(quantity)` on `log(price)` — no confounders at all. The coefficient is a naive point elasticity: the % change in quantity per 1% change in price.

```python
query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.price_elasticity_naive`
OPTIONS(model_type = 'LINEAR_REG', input_label_cols = ['log_qty'], optimize_strategy = 'NORMAL_EQUATION') AS
SELECT log_price, log_qty FROM `{PROJECT_ID}.{DATASET_ID}.price_elasticity_panel`
"""
client.query(query).result()

query = f"SELECT * FROM ML.WEIGHTS(MODEL `{PROJECT_ID}.{DATASET_ID}.price_elasticity_naive`)"
naive_weights = client.query(query).to_dataframe()
naive_elasticity = naive_weights.loc[naive_weights.processed_input == 'log_price', 'weight'].values[0]
print(f'Naive elasticity: {naive_elasticity:.4f}')

query = f"""
SELECT log_price, log_qty FROM `{PROJECT_ID}.{DATASET_ID}.price_elasticity_panel`
"""
panel_df = client.query(query).to_dataframe()

fig, ax = plt.subplots(figsize=(8, 5))
ax.scatter(panel_df['log_price'], panel_df['log_qty'], alpha=0.4, s=15)
x_range = [panel_df['log_price'].min(), panel_df['log_price'].max()]
intercept = naive_weights.loc[naive_weights.processed_input == '__INTERCEPT__', 'weight'].values[0]
ax.plot(x_range, [intercept + naive_elasticity*x for x in x_range], color='red', label=f'Naive fit (elasticity={naive_elasticity:.2f})')
ax.set_xlabel('log(price)')
ax.set_ylabel('log(quantity sold)')
ax.set_title('Naive price-quantity relationship (unadjusted)')
ax.legend()
plt.show()
```

**Verified finding:** naive elasticity ≈ **-1.4** — a 1% price increase associates with a ~1.4% drop in quantity (elastic demand, at face value). But Step 1 already showed a real confounder (distribution breadth) correlates with both variables — this number is contaminated by that, not a clean causal estimate.

---
## Step 3 — Why DML: explain before building

The naive coefficient above mixes two things together: the true effect of price on demand, *and* the effect of everything correlated with price that also drives volume — mainly distribution breadth (`log_n_stores`), but also category and vendor (broad brand recognition, category-level demand differences). A SKU stocked in 400 stores will sell more than one stocked in 80 stores **regardless of price** — and since pricier SKUs tend to reach fewer stores, that mechanically drags the naive price coefficient toward looking more negative than the true price effect. DML strips this out by construction rather than assuming it away.

---
## Step 4 — 5-fold cross-fitting: two ML models, out-of-fold residuals

Reuses `workflows/cross_validation/`'s exact deterministic fold-assignment pattern (`MOD(ABS(FARM_FINGERPRINT(TO_JSON_STRING(t))), 5)`). For each of 5 folds: train `Model_Y` (`BOOSTED_TREE_REGRESSOR`, predicting `log_qty` from confounders only) and `Model_T` (same confounders, predicting `log_price`) on the **other 4 folds**, then score the held-out fold — genuine **out-of-fold** predictions, never a model scoring its own training rows.

```python
query = f"""
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.price_elasticity_folds` AS
SELECT *, MOD(ABS(FARM_FINGERPRINT(TO_JSON_STRING(t))), 5) AS fold
FROM `{PROJECT_ID}.{DATASET_ID}.price_elasticity_panel` AS t
"""
client.query(query).result()

def train_fold_model(i, target_col, other_col):
    query = f"""
    CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.price_elasticity_fold{i}_{'y' if target_col == 'log_qty' else 't'}`
    OPTIONS(model_type = 'BOOSTED_TREE_REGRESSOR', input_label_cols = ['{target_col}'], data_split_method = 'NO_SPLIT') AS
    SELECT category_name, vendor_name, pack, log_n_stores, {target_col}
    FROM `{PROJECT_ID}.{DATASET_ID}.price_elasticity_folds`
    WHERE fold != {i}
    """
    return client.query(query)  # submitted asynchronously — caller awaits .result()

# Submit all 10 fold-model training jobs first, so they run concurrently server-side
jobs = {}
for i in range(5):
    jobs[f'fold{i}_y'] = train_fold_model(i, 'log_qty', 'log_price')
    jobs[f'fold{i}_t'] = train_fold_model(i, 'log_price', 'log_qty')
for name, job in jobs.items():
    job.result()
print(f'Trained {len(jobs)} fold models')
```

```python
union_parts = []
for i in range(5):
    union_parts.append(f"""
    SELECT f.row_id, f.log_price, f.log_qty,
      f.log_qty - py.predicted_log_qty AS residual_qty,
      f.log_price - pt.predicted_log_price AS residual_price
    FROM `{PROJECT_ID}.{DATASET_ID}.price_elasticity_folds` f
    JOIN ML.PREDICT(MODEL `{PROJECT_ID}.{DATASET_ID}.price_elasticity_fold{i}_y`,
      (SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.price_elasticity_folds` WHERE fold = {i})) py USING (row_id)
    JOIN ML.PREDICT(MODEL `{PROJECT_ID}.{DATASET_ID}.price_elasticity_fold{i}_t`,
      (SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.price_elasticity_folds` WHERE fold = {i})) pt USING (row_id)
    WHERE f.fold = {i}
    """)

query = f"""
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.price_elasticity_residuals` AS
{' UNION ALL '.join(f'SELECT * FROM ({p})' for p in union_parts)}
"""
client.query(query).result()

query = f"SELECT COUNT(*) AS n FROM `{PROJECT_ID}.{DATASET_ID}.price_elasticity_residuals`"
client.query(query).to_dataframe()
```

**Verified finding:** 1,130 rows — every SKU gets exactly one genuinely out-of-fold residual pair.

---
## Step 5 — Final regression on residuals: the DML-debiased elasticity

`LINEAR_REG` of `residual_qty` on `residual_price` — both stripped of whatever the confounders could explain. What's left, if anything, is price's own effect. **Gotcha found live**: on a small, collinear design, BigQuery ML's default `LINEAR_REG` optimizer (`optimize_strategy = 'AUTO_STRATEGY'`) can choose iterative gradient descent that stops early without reaching the true least-squares solution — verified separately in `difference_in_differences/`. This regression has 1,130 rows and a single predictor, well clear of that failure mode (confirmed: `AUTO_STRATEGY` and explicit `NORMAL_EQUATION` gave identical results here) — but `optimize_strategy='NORMAL_EQUATION'` is used anyway for a guaranteed exact fit, cheap at this scale.

```python
query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.price_elasticity_dml`
OPTIONS(model_type = 'LINEAR_REG', input_label_cols = ['residual_qty'], data_split_method = 'NO_SPLIT', optimize_strategy = 'NORMAL_EQUATION') AS
SELECT residual_price, residual_qty FROM `{PROJECT_ID}.{DATASET_ID}.price_elasticity_residuals`
"""
client.query(query).result()

query = f"SELECT * FROM ML.WEIGHTS(MODEL `{PROJECT_ID}.{DATASET_ID}.price_elasticity_dml`)"
dml_weights = client.query(query).to_dataframe()
dml_elasticity = dml_weights.loc[dml_weights.processed_input == 'residual_price', 'weight'].values[0]
print(f'DML-corrected elasticity: {dml_elasticity:.4f}')

query = f"SELECT residual_price, residual_qty FROM `{PROJECT_ID}.{DATASET_ID}.price_elasticity_residuals`"
resid_df = client.query(query).to_dataframe()

fig, ax = plt.subplots(figsize=(8, 5))
ax.scatter(resid_df['residual_price'], resid_df['residual_qty'], alpha=0.4, s=15, color='darkorange')
x_range = [resid_df['residual_price'].min(), resid_df['residual_price'].max()]
dml_intercept = dml_weights.loc[dml_weights.processed_input == '__INTERCEPT__', 'weight'].values[0]
ax.plot(x_range, [dml_intercept + dml_elasticity*x for x in x_range], color='red', label=f'DML fit (elasticity={dml_elasticity:.2f})')
ax.axhline(0, color='gray', linewidth=0.5)
ax.axvline(0, color='gray', linewidth=0.5)
ax.set_xlabel('residual log(price)  (unexplained by category/vendor/pack/distribution)')
ax.set_ylabel('residual log(quantity)  (unexplained by category/vendor/pack/distribution)')
ax.set_title('DML partial-regression plot: price\'s effect after removing confounders')
ax.legend()
plt.show()
```

**Verified finding:** DML-corrected elasticity ≈ **-0.7** — less than half the magnitude of the naive -1.4. This partial-regression plot (the classic Frisch-Waugh-Lovell visual) is the DML analogue of Step 2's raw scatter: same relationship, but only the part neither variable's confounders can explain. **Non-determinism note:** the exact value shifts slightly (observed -0.71 to -0.74 across reruns) since `BOOSTED_TREE_REGRESSOR`'s row/column subsampling makes each fold's `Model_Y`/`Model_T` — and therefore the residuals feeding this final regression — non-deterministic between retrains; the magnitude and direction relative to the naive estimate is the robust finding, not the exact decimal.

---
## Step 6 — Honest finding

**Naive vs. DML elasticity: roughly -1.4 vs. roughly -0.7.** Roughly half of the apparent price sensitivity in the naive regression was actually distribution breadth, category, and vendor effects masquerading as a price effect — not a true causal response to price itself. This is a real, substantial correction, not a rounding difference, and it's exactly the failure mode DML exists to catch: **naive regression-based price elasticity is now considered unreliable in industry precisely because of confounding like this.**

**What this estimates, stated plainly:** this is a **cross-sectional, cross-brand** elasticity — how quantity sold differs *across* SKUs at different price points within a category, holding distribution/vendor/category fixed. It is *not* a prediction of what would happen if one specific SKU's own price changed while everything else about it stayed fixed (a within-SKU, time-series elasticity) — Iowa's state-set retail pricing rules that design out entirely, since any single SKU's price barely moves over time. Real retail category-management teams run exactly this kind of cross-sectional study when a controlled price experiment isn't available.

---
## Related content

- `workflows/cross_validation` (`workflows/cross_validation/`) — the k-fold hash-based fold-assignment pattern reused here for cross-fitting instead of model evaluation.
- `workflows/propensity_score_matching` (`workflows/propensity_score_matching/`) — this project's other causal-inference (not prediction) workflow; correcting for confounders in a treatment-effect estimate is the same underlying idea as DML's residualization.
- `models/boosted_tree_regressor` (`models/boosted_tree_regressor/`) — `BOOSTED_TREE_REGRESSOR` mechanics in depth (used here as DML's flexible nuisance-model learner, not for its usual predictive role).

---
## Examples — `%%bigquery` Magics

The same SKU-panel summary using IPython magic commands.

```sql
%%bigquery --project {PROJECT_ID}

SELECT category_name, COUNT(*) AS n_skus, ROUND(AVG(EXP(log_price)), 2) AS avg_price
FROM `statmike-mlops-349915.bq_ml.price_elasticity_panel`
GROUP BY category_name
ORDER BY n_skus DESC
```

---
## Examples — BigFrames

`bigframes.ml.ensemble.XGBRegressor` is a valid drop-in for Step 4's `Model_Y`/`Model_T` nuisance models, and `bigframes.ml.linear_model.LinearRegression` for Steps 2 and 5's regressions (same patterns demonstrated in `models/boosted_tree_regressor` (`models/boosted_tree_regressor/`) and `models/linear_regression` (`models/linear_regression/`)) — the fold-assignment and residual-computation logic would still be plain SQL/pandas either way, same as this project's other multi-technique workflows (`workflows/propensity_score_matching` (`propensity_score_matching`)).
