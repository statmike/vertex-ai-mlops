# Regression-Based Forecasting — BigQuery ML

Forecast daily bike-share demand using general-purpose regression models — `LINEAR_REG` and `BOOSTED_TREE_REGRESSOR`, both already built in this project's `models/` folder — instead of a native time-series model. Regression models have no built-in notion of time, so this workflow's real content is **feature engineering**: turning a single `(date, num_trips)` series into a training table via time-part extraction, lag features, and lead-based labels for direct multi-step forecasting.

**Models used:** `LINEAR_REG`, `BOOSTED_TREE_REGRESSOR`
**Functions used:** `ML.EVALUATE`, `ML.PREDICT`

**First workflow in the project** — composes model types from Phase 2 into an end-to-end forecasting technique, on the exact same station (Pershing Square North) and TEST window (last 28 days, held out after `2018-05-03`) as `models/arima_plus` (`models/arima_plus/`), so the two notebooks' forecast accuracy is directly comparable.

Four techniques, in increasing sophistication:
1. **Time features only** (`LINEAR_REG`) — day-of-week/month/year seasonality, no memory of recent demand.
2. **+ lag features** (`LINEAR_REG`) — adds 1-day/1-week/1-month/1-quarter/1-year lags of the target itself. Raises a real evaluation trap: a naive test-set evaluation *leaks* future information through those lags. Compares leaked vs. truncated vs. a properly recursive evaluation.
3. **Direct multi-step** (`LINEAR_REG`) — one model per horizon day (28 models), each trained to predict exactly *h* days ahead directly from lag/time features at the forecast origin. No recursion needed.
4. **Direct multi-step** (`BOOSTED_TREE_REGRESSOR`) — same 28-model structure, gradient-boosted trees instead of a linear model.

**A real, measured GOTCHA drives how Step 4 is built:** pre-validating this notebook found `BOOSTED_TREE_REGRESSOR` takes ~2.5–4.5 minutes to train per model in BigQuery ML — regardless of data size (this dataset has fewer than 1,000 training rows) and regardless of a BigQuery Editions slot reservation (tested directly: a reservation made no measurable difference, confirming the cost is inherent to this model type's training path, not slot-queueing). Training 28 of these sequentially would take 1.5–2 hours. Section 4 instead submits training jobs **concurrently** (confirmed live: BigQuery runs independently-named `CREATE MODEL` jobs from the same client in true parallel, not queued) in batches, cutting wall time from hours to tens of minutes.

---
## Setup

Set your project and location, authenticate, and create a shared dataset for the model.

> This workflow trains ordinary regression models on engineered features — no connection or remote model required, same as any other `LINEAR_REG`/`BOOSTED_TREE_REGRESSOR` notebook in this project. See the `setup` (Setup Reference) for details.

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

### Materialize the training data

Daily trip counts for a single station (Pershing Square North), with a `splits` column marking the last 28 days as `TEST` — the identical station and split point used in `models/arima_plus/`, so the two notebooks' accuracy is directly comparable.

```python
query = f"""
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.regression_forecasting_trips` AS
SELECT
  DATE(starttime) AS date,
  COUNT(*) AS num_trips
FROM `bigquery-public-data.new_york_citibike.citibike_trips`
WHERE start_station_name = 'Pershing Square North'
GROUP BY date
"""
client.query(query).result()

query = f"""
SELECT COUNT(*) AS n_rows, MIN(date) AS min_date, MAX(date) AS max_date
FROM `{PROJECT_ID}.{DATASET_ID}.regression_forecasting_trips`
"""
client.query(query).to_dataframe()
```

### GOTCHA (verified): `LAG`/`LEAD` operate on row position, not calendar time

This series has real gaps — the row count above is fewer than the number of calendar days between its min and max date. `models/arima_plus/` found (and documented) a genuine ~6-month gap (October 2016 – March 2017) in this same public dataset, which `ARIMA_PLUS` handles explicitly (interpolating or nulling across the gap by calendar date). Plain SQL window functions do **not** do this: `LAG(num_trips, 1) OVER (ORDER BY date)` returns the previous *row*, not the previous *calendar day* — during a gap, a "1-day lag" silently becomes a lag of however many calendar days the gap actually spans. Verified directly below: the single largest jump between consecutive rows in this table is exactly the same ~183-day gap.

```python
query = f"""
WITH gaps AS (
  SELECT date, DATE_DIFF(date, LAG(date) OVER (ORDER BY date), DAY) AS days_since_prior_row
  FROM `{PROJECT_ID}.{DATASET_ID}.regression_forecasting_trips`
)
SELECT date AS gap_end_date, days_since_prior_row
FROM gaps
ORDER BY days_since_prior_row DESC
LIMIT 3
"""
client.query(query).to_dataframe()
```

This TRAIN-region gap doesn't affect the TEST-period forecasts evaluated below (the 28-day TEST window itself has no gaps), but it's a real property of every lag feature built in Examples 2–4: a handful of TRAIN rows have lag values that are actually many months stale, not truly "1 day ago." Regression models have no visibility into this — unlike `ARIMA_PLUS`, nothing here flags or corrects for it.

---
## Example 1 — Time features only (`LINEAR_REG`)

Decompose the date into calendar parts (year, month, day-of-month, day-of-year, day-of-week, weekend flag) and let a linear regression learn seasonality from those alone — no memory of recent demand at all.

```python
EX1_CTE = f"""
WITH prepped AS (
  SELECT
    date,
    num_trips,
    IF(date > DATE('2018-05-03'), 'TEST', 'TRAIN') AS splits,
    EXTRACT(YEAR FROM date) AS year,
    EXTRACT(MONTH FROM date) AS month,
    EXTRACT(DAY FROM date) AS day_of_month,
    EXTRACT(DAYOFYEAR FROM date) AS day_of_year,
    EXTRACT(DAYOFWEEK FROM date) AS day_of_week,
    IF(EXTRACT(DAYOFWEEK FROM date) IN (1, 7), 1, 0) AS weekend
  FROM `{PROJECT_ID}.{DATASET_ID}.regression_forecasting_trips`
)
"""

query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.regression_forecast_ex1`
OPTIONS(
  model_type = 'LINEAR_REG',
  input_label_cols = ['num_trips']
) AS
{EX1_CTE}
SELECT year, month, day_of_month, day_of_year, day_of_week, weekend, num_trips
FROM prepped
WHERE splits = 'TRAIN'
"""
client.query(query).result()
print('Model regression_forecast_ex1 created')
```

```python
query = f"""
{EX1_CTE}
SELECT * FROM ML.EVALUATE(MODEL `{PROJECT_ID}.{DATASET_ID}.regression_forecast_ex1`,
  (SELECT year, month, day_of_month, day_of_year, day_of_week, weekend, num_trips
   FROM prepped WHERE splits = 'TEST'))
"""
client.query(query).to_dataframe()
```

### A custom metrics helper, reused for every technique below

BQML's `ML.EVALUATE` only applies cleanly to Example 1's simple train/test split. Examples 2–4 build their own actual-vs-predicted tables, so the same four metrics (MAE, RMSE, MAPE, pMAE) are computed directly in pandas here — applied identically to every technique for a fair final comparison.

```python
def compute_metrics(df, actual_col='actual', pred_col='predicted'):
    errors = df[actual_col] - df[pred_col]
    mae = errors.abs().mean()
    rmse = (errors ** 2).mean() ** 0.5
    mape = (errors.abs() / df[actual_col]).mean() * 100
    pmae = mae / df[actual_col].mean() * 100
    return pd.Series({'MAE': mae, 'RMSE': rmse, 'MAPE (%)': mape, 'pMAE (%)': pmae})

results = {}  # technique name -> metrics Series, filled in as each example runs

query = f"""
{EX1_CTE}
SELECT date, num_trips AS actual, predicted_num_trips AS predicted
FROM ML.PREDICT(MODEL `{PROJECT_ID}.{DATASET_ID}.regression_forecast_ex1`,
  (SELECT * FROM prepped WHERE splits = 'TEST'))
ORDER BY date
"""
ex1_predictions = client.query(query).to_dataframe()
results['Ex1: time features only (LINEAR_REG)'] = compute_metrics(ex1_predictions)

fig, ax = plt.subplots(figsize=(10, 4))
ax.plot(ex1_predictions['date'], ex1_predictions['actual'], label='actual', marker='o')
ax.plot(ex1_predictions['date'], ex1_predictions['predicted'], label='predicted', marker='o')
ax.set_title('Example 1: time features only — TEST period')
ax.legend()
plt.show()

results['Ex1: time features only (LINEAR_REG)']
```

---
## Example 2 — Add lag features (`LINEAR_REG`)

Add 1-day, 1-week, 1-month, 1-quarter, and 1-year lags of `num_trips` to the time features. This raises a real forecasting trap: at real forecast time, you only truly know the 1-day/1-week lags for the *first* day or week of a multi-day horizon — everything past that would have to come from your own prior forecasts, not ground truth. Evaluating naively against the TEST split lets those future lags leak in.

```python
EX2_CTE = f"""
WITH prepped AS (
  SELECT
    date,
    num_trips,
    IF(date > DATE('2018-05-03'), 'TEST', 'TRAIN') AS splits,
    EXTRACT(YEAR FROM date) AS year,
    EXTRACT(MONTH FROM date) AS month,
    EXTRACT(DAY FROM date) AS day_of_month,
    EXTRACT(DAYOFYEAR FROM date) AS day_of_year,
    EXTRACT(DAYOFWEEK FROM date) AS day_of_week,
    IF(EXTRACT(DAYOFWEEK FROM date) IN (1, 7), 1, 0) AS weekend,
    LAG(num_trips, 1) OVER (ORDER BY date) AS lag_1day,
    LAG(num_trips, 7) OVER (ORDER BY date) AS lag_1week,
    LAG(num_trips, 28) OVER (ORDER BY date) AS lag_1month,
    LAG(num_trips, 90) OVER (ORDER BY date) AS lag_1quarter,
    LAG(num_trips, 365) OVER (ORDER BY date) AS lag_1year
  FROM `{PROJECT_ID}.{DATASET_ID}.regression_forecasting_trips`
)
"""

query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.regression_forecast_ex2`
OPTIONS(
  model_type = 'LINEAR_REG',
  input_label_cols = ['num_trips']
) AS
{EX2_CTE}
SELECT year, month, day_of_month, day_of_year, day_of_week, weekend,
  lag_1day, lag_1week, lag_1month, lag_1quarter, lag_1year, num_trips
FROM prepped
WHERE splits = 'TRAIN'
"""
client.query(query).result()
print('Model regression_forecast_ex2 created (BQML mean-imputes the NULL lags in the earliest TRAIN rows)')
```

### Three ways to evaluate a lag-based model on the TEST horizon

- **LEAKED** — evaluate straight against the TEST split's real lag values. Every lag, even ones that would require knowing 20+ days into the future, is the true historical number. Optimistic and unrealistic beyond day 1.
- **TRUNCATED** — null out `lag_1day`/`lag_1week` wherever they'd fall inside the TEST horizon itself (not truly knowable yet). Honest about what's missing, but BQML's NULL-handling isn't the same as actually forecasting a lag — likely too pessimistic.
- **RECURSIVE** — the way this model would actually be used: forecast one day at a time, feeding each forecast back in as the next day's lag input.

```python
# LEAKED: straight prediction against the TEST split's real (future) lag values
query = f"""
{EX2_CTE}
SELECT date, num_trips AS actual, predicted_num_trips AS predicted
FROM ML.PREDICT(MODEL `{PROJECT_ID}.{DATASET_ID}.regression_forecast_ex2`,
  (SELECT * FROM prepped WHERE splits = 'TEST'))
ORDER BY date
"""
leaked_predictions = client.query(query).to_dataframe()
compute_metrics(leaked_predictions)
```

```python
# TRUNCATED: null out lag_1day/lag_1week wherever they'd require knowing the TEST horizon's own future
query = f"""
{EX2_CTE}
SELECT date, num_trips AS actual, predicted_num_trips AS predicted
FROM ML.PREDICT(MODEL `{PROJECT_ID}.{DATASET_ID}.regression_forecast_ex2`,
  (SELECT * EXCEPT(lag_1day, lag_1week),
    IF(date > DATE_ADD(DATE('2018-05-03'), INTERVAL 1 DAY), NULL, lag_1day) AS lag_1day,
    IF(date > DATE_ADD(DATE('2018-05-03'), INTERVAL 7 DAY), NULL, lag_1week) AS lag_1week
   FROM prepped WHERE splits = 'TEST'))
ORDER BY date
"""
truncated_predictions = client.query(query).to_dataframe()
compute_metrics(truncated_predictions)
```

### Recursive prediction

Predict the first TEST day using its true lag values (known at the forecast origin), then predict each subsequent day using the *previous day's own forecast* as its `lag_1day` (and, once the horizon passes 7 days, as its `lag_1week`). `lag_1month`/`lag_1quarter`/`lag_1year` always fall inside the 28-day horizon's TRAIN history, so they stay real throughout — a 28-day horizon never reaches far enough to need a forecasted `lag_1month` value.

```python
import datetime

history = client.query(f"""
SELECT date, num_trips FROM `{PROJECT_ID}.{DATASET_ID}.regression_forecasting_trips` ORDER BY date
""").to_dataframe()
history['date'] = pd.to_datetime(history['date'])
known_values = history.set_index('date')['num_trips'].to_dict()

test_start = datetime.date(2018, 5, 4)
horizon = 28
forecasts = {}

def value_on(d):
    d = pd.Timestamp(d)
    return forecasts.get(d, known_values.get(d))

recursive_rows = []
for h in range(horizon):
    d = test_start + datetime.timedelta(days=h)
    lag_1day = value_on(d - datetime.timedelta(days=1))
    lag_1week = value_on(d - datetime.timedelta(days=7))
    lag_1month = value_on(d - datetime.timedelta(days=28))
    lag_1quarter = value_on(d - datetime.timedelta(days=90))
    lag_1year = value_on(d - datetime.timedelta(days=365))
    day_of_week = d.isoweekday() % 7 + 1  # BigQuery DAYOFWEEK: Sunday=1 ... Saturday=7
    weekend = 1 if day_of_week in (1, 7) else 0

    query = f"""
    SELECT predicted_num_trips
    FROM ML.PREDICT(MODEL `{PROJECT_ID}.{DATASET_ID}.regression_forecast_ex2`, (
      SELECT {d.year} AS year, {d.month} AS month, {d.day} AS day_of_month,
        {d.timetuple().tm_yday} AS day_of_year, {day_of_week} AS day_of_week, {weekend} AS weekend,
        CAST({lag_1day} AS INT64) AS lag_1day, CAST({lag_1week} AS INT64) AS lag_1week,
        CAST({lag_1month} AS INT64) AS lag_1month, CAST({lag_1quarter} AS INT64) AS lag_1quarter,
        CAST({lag_1year} AS INT64) AS lag_1year
    ))
    """
    predicted = client.query(query).to_dataframe()['predicted_num_trips'].iloc[0]
    forecasts[pd.Timestamp(d)] = predicted
    recursive_rows.append({'date': d, 'actual': known_values.get(pd.Timestamp(d)), 'predicted': predicted})

recursive_predictions = pd.DataFrame(recursive_rows)
recursive_predictions
```

```python
comparison = pd.DataFrame({
    'LEAKED': compute_metrics(leaked_predictions),
    'TRUNCATED': compute_metrics(truncated_predictions),
    'RECURSIVE': compute_metrics(recursive_predictions),
}).T
comparison
```

LEAKED looks the most accurate (it's the only one allowed to peek at real future demand through its lags) and TRUNCATED the least — mean-imputing an unknown lag throws away real signal without replacing it with anything useful. RECURSIVE lands in between: a realistic, deployable evaluation that at least feeds the model *something* informative (its own prior forecast) instead of a mean-imputed placeholder. **RECURSIVE is the number carried into the final comparison below — it's the only one of the three that reflects how this model would actually be run.**

```python
results['Ex2: + lag features, recursive (LINEAR_REG)'] = compute_metrics(recursive_predictions)

fig, ax = plt.subplots(figsize=(10, 4))
ax.plot(recursive_predictions['date'], recursive_predictions['actual'], label='actual', marker='o')
ax.plot(recursive_predictions['date'], recursive_predictions['predicted'], label='predicted (recursive)', marker='o')
ax.set_title('Example 2: + lag features, recursive forecast — TEST period')
ax.legend()
plt.show()
```

---
## Example 3 — Direct multi-step (`LINEAR_REG`)

Train a separate model for each of the 28 horizon days: model *h*'s label is `LEAD(num_trips, h)`, so it directly predicts "the value *h* days from now" from lag/time features anchored at a single origin date — no recursion, and no dependence on a prior forecast's error compounding into the next step.

**Avoiding a subtle leak:** a naive `WHERE splits = 'TRAIN'` filter on the *anchor* date would still allow some anchors near the TRAIN/TEST boundary to have a label drawn from the TEST period itself (since the label is `h` days *after* the anchor). Each model instead requires `date + h <= '2018-05-03'`, so every training label comes from TRAIN, never TEST.

All 28 models are submitted to BigQuery concurrently (fast here regardless — `LINEAR_REG` trains in seconds — but this also validates the pattern used for the much slower boosted-tree version in Example 4 below).

```python
def make_direct_cte(h):
    return f"""
    WITH prepped AS (
      SELECT
        date,
        LEAD(num_trips, {h}) OVER (ORDER BY date) AS label,
        EXTRACT(YEAR FROM date) AS year,
        EXTRACT(MONTH FROM date) AS month,
        EXTRACT(DAY FROM date) AS day_of_month,
        EXTRACT(DAYOFYEAR FROM date) AS day_of_year,
        EXTRACT(DAYOFWEEK FROM date) AS day_of_week,
        IF(EXTRACT(DAYOFWEEK FROM date) IN (1, 7), 1, 0) AS weekend,
        LAG(num_trips, 1) OVER (ORDER BY date) AS lag_1day,
        LAG(num_trips, 7) OVER (ORDER BY date) AS lag_1week,
        LAG(num_trips, 28) OVER (ORDER BY date) AS lag_1month,
        LAG(num_trips, 90) OVER (ORDER BY date) AS lag_1quarter,
        LAG(num_trips, 365) OVER (ORDER BY date) AS lag_1year
      FROM `{PROJECT_ID}.{DATASET_ID}.regression_forecasting_trips`
    )
    """

TEST_ORIGIN = "DATE('2018-05-03')"  # last TRAIN date — the forecast anchor for every horizon day
HORIZON = 28

def train_direct_model(model_name, model_type, h):
    cte = make_direct_cte(h)
    query = f"""
    CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.{model_name}`
    OPTIONS(model_type = '{model_type}', input_label_cols = ['label']) AS
    {cte}
    SELECT year, month, day_of_month, day_of_year, day_of_week, weekend,
      lag_1day, lag_1week, lag_1month, lag_1quarter, lag_1year, label
    FROM prepped
    WHERE date + {h} <= {TEST_ORIGIN} AND label IS NOT NULL AND lag_1year IS NOT NULL
    """
    return client.query(query)  # submitted asynchronously — caller awaits .result()

def predict_direct_model(model_name, h):
    cte = make_direct_cte(h)
    query = f"""
    {cte}
    SELECT date + {h} AS date, label AS actual, predicted_label AS predicted
    FROM ML.PREDICT(MODEL `{PROJECT_ID}.{DATASET_ID}.{model_name}`,
      (SELECT * FROM prepped WHERE date = {TEST_ORIGIN}))
    """
    return client.query(query).to_dataframe()

def train_direct_models_in_batches(model_prefix, model_type, batch_size):
    """Submit CREATE MODEL jobs concurrently in batches of `batch_size`, waiting for each
    batch to finish before submitting the next (BigQuery runs distinctly-named CREATE MODEL
    jobs from one client in true parallel — verified live — so a batch of jobs finishes in
    roughly the time of its single slowest model, not the sum of all of them)."""
    horizon_days = list(range(1, HORIZON + 1))
    for batch_start in range(0, len(horizon_days), batch_size):
        batch = horizon_days[batch_start:batch_start + batch_size]
        jobs = {h: train_direct_model(f'{model_prefix}_h{h}', model_type, h) for h in batch}
        for h, job in jobs.items():
            job.result()
        print(f'{model_prefix}: trained horizon days {batch}')

train_direct_models_in_batches('regression_forecast_ex3', 'LINEAR_REG', batch_size=HORIZON)
```

```python
ex3_predictions = pd.concat(
    [predict_direct_model(f'regression_forecast_ex3_h{h}', h) for h in range(1, HORIZON + 1)],
    ignore_index=True
).sort_values('date')
results['Ex3: direct multi-step (LINEAR_REG)'] = compute_metrics(ex3_predictions)

fig, ax = plt.subplots(figsize=(10, 4))
ax.plot(ex3_predictions['date'], ex3_predictions['actual'], label='actual', marker='o')
ax.plot(ex3_predictions['date'], ex3_predictions['predicted'], label='predicted', marker='o')
ax.set_title('Example 3: direct multi-step (LINEAR_REG) — TEST period')
ax.legend()
plt.show()

results['Ex3: direct multi-step (LINEAR_REG)']
```

---
## Example 4 — Direct multi-step (`BOOSTED_TREE_REGRESSOR`)

Identical structure to Example 3 — one model per horizon day, same leak-free training filter — swapping in gradient-boosted trees.

**GOTCHA (verified):** a single `BOOSTED_TREE_REGRESSOR` model here takes ~2.5–4.5 minutes to train, versus ~15 seconds for the equivalent `LINEAR_REG` model — on the same, small (fewer than 1,000 row) training table. Pre-validating this notebook ruled out two obvious explanations directly: reducing `max_iterations` and disabling `early_stop` made a model take *longer*, not shorter (ruling out boosting-round count as the driver), and running the same model under a temporary BigQuery Editions autoscale reservation made no measurable difference either (ruling out on-demand slot queueing — the job's own query plan showed it actively burning slot-time the whole way through, not waiting for capacity). This appears to be a fixed cost of `BOOSTED_TREE_REGRESSOR` training in BigQuery ML, not something tunable away.

Training all 28 sequentially would take **1.5–2 hours**. This step instead reuses `train_direct_models_in_batches` from Example 3 with a smaller batch size — pre-validated directly: submitting several `BOOSTED_TREE_REGRESSOR` `CREATE MODEL` jobs (with distinct model names) at once lets BigQuery run them in true concurrent parallel, so a batch of ~10 finishes in minutes, not 10× the single-model time. Expect this cell to take **roughly 15–30 minutes** in total across all 3 batches — still a large improvement over fully sequential, but the longest-running cell in this notebook by far.

```python
train_direct_models_in_batches('regression_forecast_ex4', 'BOOSTED_TREE_REGRESSOR', batch_size=10)
```

```python
ex4_predictions = pd.concat(
    [predict_direct_model(f'regression_forecast_ex4_h{h}', h) for h in range(1, HORIZON + 1)],
    ignore_index=True
).sort_values('date')
results['Ex4: direct multi-step (BOOSTED_TREE_REGRESSOR)'] = compute_metrics(ex4_predictions)

fig, ax = plt.subplots(figsize=(10, 4))
ax.plot(ex4_predictions['date'], ex4_predictions['actual'], label='actual', marker='o')
ax.plot(ex4_predictions['date'], ex4_predictions['predicted'], label='predicted', marker='o')
ax.set_title('Example 4: direct multi-step (BOOSTED_TREE_REGRESSOR) — TEST period')
ax.legend()
plt.show()

results['Ex4: direct multi-step (BOOSTED_TREE_REGRESSOR)']
```

---
## Comparison

All four techniques, evaluated identically (MAE/RMSE/MAPE/pMAE over the same 28-day TEST window), plus a reference row pulled directly from `models/arima_plus/`'s own `ML.EVALUATE` output for Pershing Square North on this exact TEST window — the native time-series model this workflow is implicitly competing with.

```python
comparison_table = pd.DataFrame(results).T

# Reference row: ARIMA_PLUS's own measured accuracy for Pershing Square North on the identical
# TEST window, taken directly from models/arima_plus/'s ML.EVALUATE output (Step 5 there).
test_avg_actual = client.query(f"""
SELECT AVG(num_trips) AS avg_actual
FROM `{PROJECT_ID}.{DATASET_ID}.regression_forecasting_trips`
WHERE date > DATE('2018-05-03')
""").to_dataframe()['avg_actual'].iloc[0]
arima_mae = 135.461280
comparison_table.loc['Reference: ARIMA_PLUS (models/arima_plus/)'] = {
    'MAE': arima_mae,
    'RMSE': 162.790009,
    'MAPE (%)': 56.792525,
    'pMAE (%)': arima_mae / test_avg_actual * 100,
}
comparison_table
```

**Read this table for the ranking, not as a verdict on regression vs. ARIMA_PLUS in general** — it reflects one station, one 28-day window, and untuned default hyperparameters throughout. `ARIMA_PLUS` gets automatic seasonal/trend decomposition, holiday effects, and anomaly-robust fitting for free; every regression technique here only has whatever's explicit in its feature list.

Two results are worth calling out specifically, since they run against the naive expectation that "more principled" or "more sophisticated" automatically means "more accurate":

- **Direct multi-step `LINEAR_REG` (Example 3) is the *worst* performer here on every metric** — worse than even the plain time-features-only model (Example 1). Avoiding recursion and evaluation leakage doesn't help if it comes at the cost of splitting one already-small training table (~1,150 TRAIN rows) into 28 separate per-horizon models, each fit on fewer effective examples than Example 1 or 2 ever had to work with.
- **Direct multi-step `BOOSTED_TREE_REGRESSOR` (Example 4) gets the best MAPE of *any* technique in this table, including the `ARIMA_PLUS` reference** (45.68% vs. ARIMA_PLUS's 56.79%) — despite a worse MAE/RMSE than ARIMA_PLUS. MAE/RMSE are dominated by the largest absolute misses (weekday demand spikes); MAPE weights every day equally in relative terms. A model can be the better *percentage-error* forecaster while still losing on absolute error, and this table has a genuine example of exactly that.

`ARIMA_PLUS` still wins on MAE, RMSE, and pMAE, and Example 2's recursive `LINEAR_REG` remains the strongest of the regression techniques on those same three metrics — the takeaway isn't "boosted trees beat ARIMA_PLUS," it's that **which metric you optimize for changes which technique looks best**, even on identical data.
