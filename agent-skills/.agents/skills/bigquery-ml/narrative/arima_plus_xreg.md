# ARIMA_PLUS_XREG — BigQuery ML

Train a **multivariate time series forecasting** model with `CREATE MODEL` (model_type = `ARIMA_PLUS_XREG`) — `ARIMA_PLUS` plus linear external regressors (covariates). Internally it fits a linear regression on the supplied covariates and models the residuals with the full `ARIMA_PLUS` pipeline. Every selected column that is NOT the timestamp/data/id column becomes a covariate implicitly.

**Lifecycle:** `CREATE MODEL` → `ML.ARIMA_EVALUATE` → `ML.FEATURE_INFO` / `ML.TRAINING_INFO` → `ML.EVALUATE` → `ML.FORECAST` (covariates required) → `ML.EXPLAIN_FORECAST` (+ per-regressor attribution) → `ML.ARIMA_COEFFICIENTS` (+ regression weights) → `ML.HOLIDAY_INFO` → `ML.DETECT_ANOMALIES` → additional options

**Twelfth model type in the project, second in Phase 4 (time series).**

**When to use ARIMA_PLUS_XREG instead of plain `models/arima_plus` (`ARIMA_PLUS`):**
- You have a target series **and** time-varying covariates (promotions, weather, ridership mix) that improve forecast accuracy.
- Covariate values are known/available for the forecast horizon (required at forecast time — see Step 6).
- You want ARIMA_PLUS automation (holidays, seasonality, anomaly handling) but with explanatory regressors and per-regressor attribution.

**Modernized from the old repo notebook:** it predates GA multi-series support for this model type and works around it with an `EXECUTE IMMEDIATE` loop / async Python jobs. This notebook uses native `time_series_id_col` directly (Step 2) — the same approach as `models/arima_plus` (`models/arima_plus/`).

**Data:** Same 5 Citi Bike stations and TEST window (last 28 days, `horizon = 28`) as `models/arima_plus` (`models/arima_plus/`), for direct forecast-accuracy comparison — plus 3 covariates computed per station/day: `avg_tripduration`, `pct_subscriber` (fraction `usertype='Subscriber'`), `ratio_gender` (fraction `gender='female'` among known genders). `capacity` (used by the old repo notebook) is deliberately dropped — it needs a join to a separate, current-only stations table and was NULL for some stations there too.

**References:** `RESOURCES.md` (Full reference) | [CREATE MODEL (multivariate time series) docs](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-multivariate-time-series) | `setup` (Setup guide)

---
## Setup

Set your project and location, authenticate, and create a shared dataset for the model.

> ARIMA_PLUS_XREG trains on data already in BigQuery — no connection or remote model required. See the `setup` (Setup Reference) for details.

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

Same 5 stations and TRAIN/TEST split as `models/arima_plus/`, plus 3 covariates.

> **GOTCHA (verified):** 4 rows (`E 17 St & Broadway`) have a NULL `ratio_gender` — days where every trip had an unknown gender, so the ratio is `0/0`. `CREATE MODEL` does not error on this; it emits a warning and trains successfully (confirmed below in Step 2 and `ML.FEATURE_INFO`).

```python
query = f"""
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.arima_xreg_trips` AS
WITH daily AS (
  SELECT
    start_station_name,
    DATE(starttime) AS date,
    COUNT(*) AS num_trips,
    AVG(tripduration) AS avg_tripduration,
    SAFE_DIVIDE(COUNTIF(usertype = 'Subscriber'), COUNT(*)) AS pct_subscriber,
    SAFE_DIVIDE(COUNTIF(gender = 'female'), COUNTIF(gender IN ('male','female'))) AS ratio_gender
  FROM `bigquery-public-data.new_york_citibike.citibike_trips`
  WHERE start_station_name IN (
    'Pershing Square North', 'E 17 St & Broadway', 'W 21 St & 6 Ave',
    'Lafayette St & E 8 St', 'West St & Chambers St'
  )
  GROUP BY start_station_name, date
)
SELECT *, IF(date > DATE('2018-05-03'), 'TEST', 'TRAIN') AS splits
FROM daily
"""
client.query(query).result()
print('Table arima_xreg_trips created')
```

---
## Step 1 — Create a single-series model with `CREATE MODEL`

Same essentials as `ARIMA_PLUS`, plus the 3 covariate columns in the training `SELECT` — no `time_series_id_col` yet, so this fits one station.

```python
query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.arima_xreg_pershing`
OPTIONS(
  model_type = 'ARIMA_PLUS_XREG',
  time_series_timestamp_col = 'date',
  time_series_data_col = 'num_trips',
  holiday_region = ['GLOBAL', 'US'],
  horizon = 28
) AS
SELECT date, num_trips, avg_tripduration, pct_subscriber, ratio_gender
FROM `{PROJECT_ID}.{DATASET_ID}.arima_xreg_trips`
WHERE start_station_name = 'Pershing Square North' AND splits = 'TRAIN'
"""
client.query(query).result()
print('Model arima_xreg_pershing created')
```

---
## Step 2 — Create a multi-series model (all 5 stations in one `CREATE MODEL`)

`time_series_id_col` fits and forecasts all 5 series in a single model — this is the model used for the rest of this notebook, and the direct replacement for the old repo notebook's `EXECUTE IMMEDIATE` loop workaround.

```python
query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.arima_xreg_multi`
OPTIONS(
  model_type = 'ARIMA_PLUS_XREG',
  time_series_timestamp_col = 'date',
  time_series_data_col = 'num_trips',
  time_series_id_col = 'start_station_name',
  holiday_region = ['GLOBAL', 'US'],
  horizon = 28
) AS
SELECT start_station_name, date, num_trips, avg_tripduration, pct_subscriber, ratio_gender
FROM `{PROJECT_ID}.{DATASET_ID}.arima_xreg_trips`
WHERE splits = 'TRAIN'
"""
client.query(query).result()
print('Model arima_xreg_multi created')
```

---
## Step 3 — Per-series diagnostics with `ML.ARIMA_EVALUATE`

```python
query = f"""
SELECT *
FROM ML.ARIMA_EVALUATE(MODEL `{PROJECT_ID}.{DATASET_ID}.arima_xreg_multi`)
"""
client.query(query).to_dataframe()
```

---
## Step 4 — Introspect the model

`ML.FEATURE_INFO` shows `null_count=4` for `ratio_gender`, confirming the NULL-covariate gotcha from Setup.

```python
query = f"""
SELECT *
FROM ML.FEATURE_INFO(MODEL `{PROJECT_ID}.{DATASET_ID}.arima_xreg_multi`)
"""
client.query(query).to_dataframe()
```

```python
query = f"""
SELECT *
FROM ML.TRAINING_INFO(MODEL `{PROJECT_ID}.{DATASET_ID}.arima_xreg_multi`)
"""
client.query(query).to_dataframe()
```

---
## Step 5 — Evaluate forecast accuracy on the held-out TEST period

> **GOTCHA (verified): unlike `ARIMA_PLUS`, this model type's `ML.EVALUATE` does NOT include `mean_absolute_scaled_error`** — confirmed by comparing the actual output columns of both model types side by side.

Plotted below by station for a quick at-a-glance comparison.

```python
query = f"""
SELECT *
FROM ML.EVALUATE(MODEL `{PROJECT_ID}.{DATASET_ID}.arima_xreg_multi`,
  (SELECT start_station_name, date, num_trips, avg_tripduration, pct_subscriber, ratio_gender
   FROM `{PROJECT_ID}.{DATASET_ID}.arima_xreg_trips` WHERE splits = 'TEST'),
  STRUCT(TRUE AS perform_aggregation))
"""
eval_metrics = client.query(query).to_dataframe()
eval_metrics
```

```python
import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(8, 4))
ax.bar(eval_metrics['start_station_name'], eval_metrics['mean_absolute_percentage_error'], color='#4285F4')
ax.set_ylabel('MAPE (%)')
ax.set_title('Forecast accuracy (MAPE) by station')
plt.xticks(rotation=30, ha='right')
plt.tight_layout()
plt.show()
```

---
## Step 6 — Forecast with `ML.FORECAST` (covariates required)

> **GOTCHA (verified): the 2-argument form fails immediately** — `ML.FORECAST(MODEL ..., STRUCT(...))` errors with `"Model type ARIMA_PLUS_XREG requires three parameters in ML.FORECAST."` Covariates must be supplied for the entire forecast horizon. This notebook uses the `TEST` split's actual (already-known) covariate values — the same honest framing the old repo notebook used, since it never had genuinely-unknown future covariates either.

```python
query = f"""
SELECT start_station_name, forecast_timestamp, forecast_value,
       prediction_interval_lower_bound, prediction_interval_upper_bound
FROM ML.FORECAST(MODEL `{PROJECT_ID}.{DATASET_ID}.arima_xreg_multi`,
  STRUCT(28 AS horizon, 0.9 AS confidence_level),
  (SELECT start_station_name, date, avg_tripduration, pct_subscriber, ratio_gender
   FROM `{PROJECT_ID}.{DATASET_ID}.arima_xreg_trips` WHERE splits = 'TEST'))
ORDER BY start_station_name, forecast_timestamp
"""
forecast = client.query(query).to_dataframe()
forecast.head()
```

```python
import matplotlib.pyplot as plt

query = f"""
SELECT start_station_name, date AS timestamp, num_trips AS value
FROM `{PROJECT_ID}.{DATASET_ID}.arima_xreg_trips`
WHERE date > DATE_SUB(DATE('2018-05-03'), INTERVAL 90 DAY)
ORDER BY start_station_name, date
"""
history = client.query(query).to_dataframe()

stations = sorted(forecast['start_station_name'].unique())
fig, axes = plt.subplots(len(stations), 1, figsize=(10, 3 * len(stations)), sharex=True)
for ax, station in zip(axes, stations):
    h = history[history['start_station_name'] == station]
    f = forecast[forecast['start_station_name'] == station]
    ax.plot(h['timestamp'], h['value'], color='#4285F4', label='history')
    ax.plot(f['forecast_timestamp'], f['forecast_value'], color='#EA4335', label='forecast')
    ax.fill_between(f['forecast_timestamp'], f['prediction_interval_lower_bound'], f['prediction_interval_upper_bound'], color='#EA4335', alpha=0.15)
    ax.set_title(station)
    ax.legend(loc='upper left', fontsize=8)
plt.tight_layout()
plt.show()
```

---
## Step 7 — Decompose with `ML.EXPLAIN_FORECAST` (+ per-regressor attribution)

Same decomposition columns as `ARIMA_PLUS`, plus `attribution_<covariate>` for each regressor.

```python
query = f"""
SELECT time_series_timestamp, time_series_type, trend,
       attribution_avg_tripduration, attribution_pct_subscriber, attribution_ratio_gender
FROM ML.EXPLAIN_FORECAST(MODEL `{PROJECT_ID}.{DATASET_ID}.arima_xreg_multi`,
  STRUCT(28 AS horizon),
  (SELECT start_station_name, date, avg_tripduration, pct_subscriber, ratio_gender
   FROM `{PROJECT_ID}.{DATASET_ID}.arima_xreg_trips` WHERE splits = 'TEST'))
WHERE start_station_name = 'Pershing Square North'
ORDER BY time_series_timestamp
"""
explain = client.query(query).to_dataframe()
explain.tail()
```

```python
fig, axes = plt.subplots(3, 1, figsize=(10, 7), sharex=True)
axes[0].plot(explain['time_series_timestamp'], explain['attribution_avg_tripduration'], color='#4285F4')
axes[0].set_title('Attribution: avg_tripduration')
axes[1].plot(explain['time_series_timestamp'], explain['attribution_pct_subscriber'], color='#34A853')
axes[1].set_title('Attribution: pct_subscriber')
axes[2].plot(explain['time_series_timestamp'], explain['attribution_ratio_gender'], color='#FBBC04')
axes[2].set_title('Attribution: ratio_gender')
plt.tight_layout()
plt.show()
```

---
## Step 8 — Inspect coefficients with `ML.ARIMA_COEFFICIENTS` (+ regression weights)

Same AR/MA/drift columns as `ARIMA_PLUS`, plus one row per regressor (`processed_input`) with its regression `weight`, and a `__INTERCEPT__` row.

```python
query = f"""
SELECT *
FROM ML.ARIMA_COEFFICIENTS(MODEL `{PROJECT_ID}.{DATASET_ID}.arima_xreg_multi`)
"""
client.query(query).to_dataframe()
```

---
## Step 9 — Modeled holidays with `ML.HOLIDAY_INFO`

```python
query = f"""
SELECT *
FROM ML.HOLIDAY_INFO(MODEL `{PROJECT_ID}.{DATASET_ID}.arima_xreg_multi`)
WHERE region = 'US' AND primary_date BETWEEN '2016-01-01' AND '2018-12-31'
ORDER BY primary_date
"""
client.query(query).to_dataframe()
```

---
## Step 10 — Anomaly detection with `ML.DETECT_ANOMALIES`

The table below shows the top 10 flagged points by `anomaly_probability`. The plot after it shows every station's full history alongside every flagged anomaly marked directly on the time series — much easier to interpret in context than the table alone.

> **GOTCHA (verified): the full-history plot reveals the same real ~6-month gap found in `models/arima_plus` (`models/arima_plus/`) — but this model type handles it differently.** `bigquery-public-data.new_york_citibike.citibike_trips` has zero rows for **October 2016 through March 2017**, across all 5 stations. Plain `ARIMA_PLUS` linearly interpolates a real numeric value across the *entire* 6-month span (see that notebook's Step 11). **`ARIMA_PLUS_XREG` does not** — `ML.DETECT_ANOMALIES` returns `NULL` for `num_trips`/`is_anomaly`/`anomaly_probability` on every day within the gap (verified directly), which correctly renders as a genuine break in the plotted line below rather than a misleading straight-line "bridge." A real, verified difference between the two model types' gap handling — don't assume the two behave identically just because they share most of the same lifecycle functions.

```python
query = f"""
SELECT start_station_name, date, num_trips, is_anomaly, anomaly_probability
FROM ML.DETECT_ANOMALIES(MODEL `{PROJECT_ID}.{DATASET_ID}.arima_xreg_multi`, STRUCT(0.95 AS anomaly_prob_threshold))
WHERE is_anomaly
ORDER BY anomaly_probability DESC
LIMIT 10
"""
client.query(query).to_dataframe()
```

```python
query = f"""
SELECT start_station_name, date AS timestamp, num_trips AS value, is_anomaly
FROM ML.DETECT_ANOMALIES(MODEL `{PROJECT_ID}.{DATASET_ID}.arima_xreg_multi`, STRUCT(0.95 AS anomaly_prob_threshold))
ORDER BY start_station_name, timestamp
"""
anomaly_series = client.query(query).to_dataframe()

stations = sorted(anomaly_series['start_station_name'].unique())
fig, axes = plt.subplots(len(stations), 1, figsize=(12, 3 * len(stations)))
for ax, station in zip(axes, stations):
    a = anomaly_series[anomaly_series['start_station_name'] == station]
    f = forecast[forecast['start_station_name'] == station]
    ax.plot(a['timestamp'], a['value'], color='#4285F4', linewidth=0.6, label='history')
    ax.plot(f['forecast_timestamp'], f['forecast_value'], color='#34A853', linewidth=1.2, label='forecast')
    flagged = a[a['is_anomaly']]
    ax.scatter(flagged['timestamp'], flagged['value'], color='#EA4335', s=20, zorder=5, label='anomaly')
    ax.set_title(station)
    ax.legend(loc='upper left', fontsize=8)
plt.tight_layout()
plt.show()
```

---
## Step 11 — Additional options: same as ARIMA_PLUS, with one real difference

Custom holidays and manual ARIMA order both work identically to `models/arima_plus` (`models/arima_plus/`) — same two-block `AS ( training_data AS (...), custom_holiday AS (...) )` syntax, same `auto_arima = FALSE` + `non_seasonal_order = STRUCT(p, d, q)`.

> **GOTCHA (verified): forecast bounds behave differently here.** For `ARIMA_PLUS`, `forecast_limit_lower_bound` is *accepted* at `CREATE MODEL` time but breaks `ML.EXPLAIN_FORECAST`. For `ARIMA_PLUS_XREG`, the option is **rejected outright at training time**: `"Option(s) FORECAST_LIMIT_LOWER_BOUND are not supported for ARIMA_PLUS_XREG model training."` A real, different limitation between the two model types — confirmed live below.

```python
query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.arima_xreg_custom_holiday`
OPTIONS(
  model_type = 'ARIMA_PLUS_XREG',
  holiday_region = 'US',
  time_series_timestamp_col = 'date',
  time_series_data_col = 'num_trips',
  horizon = 7
) AS (
  training_data AS (
    SELECT date, num_trips, avg_tripduration, pct_subscriber, ratio_gender
    FROM `{PROJECT_ID}.{DATASET_ID}.arima_xreg_trips`
    WHERE start_station_name = 'Pershing Square North' AND splits = 'TRAIN'
  ),
  custom_holiday AS (
    SELECT 'US' AS region, 'NYCMarathon' AS holiday_name, primary_date, 1 AS preholiday_days, 1 AS postholiday_days
    FROM UNNEST([DATE('2014-11-02'), DATE('2015-11-01'), DATE('2016-11-06'), DATE('2017-11-05')]) AS primary_date
  )
)
"""
client.query(query).result()
print('Model arima_xreg_custom_holiday created')

query = f"""
SELECT * FROM ML.HOLIDAY_INFO(MODEL `{PROJECT_ID}.{DATASET_ID}.arima_xreg_custom_holiday`)
WHERE holiday_name = 'NYCMarathon'
"""
client.query(query).to_dataframe()
```

```python
query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.arima_xreg_manual_order`
OPTIONS(
  model_type = 'ARIMA_PLUS_XREG',
  time_series_timestamp_col = 'date',
  time_series_data_col = 'num_trips',
  auto_arima = FALSE,
  non_seasonal_order = STRUCT(2 AS p, 1 AS d, 1 AS q),
  horizon = 7
) AS
SELECT date, num_trips, avg_tripduration, pct_subscriber, ratio_gender
FROM `{PROJECT_ID}.{DATASET_ID}.arima_xreg_trips`
WHERE start_station_name = 'Pershing Square North' AND splits = 'TRAIN'
"""
client.query(query).result()
print('Model arima_xreg_manual_order created')

query = f"""
SELECT non_seasonal_p, non_seasonal_d, non_seasonal_q
FROM ML.ARIMA_EVALUATE(MODEL `{PROJECT_ID}.{DATASET_ID}.arima_xreg_manual_order`)
"""
client.query(query).to_dataframe()
```

```python
# forecast_limit_lower_bound -- expected to fail outright for this model type
try:
    query = f"""
    CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.arima_xreg_bound_error`
    OPTIONS(
      model_type = 'ARIMA_PLUS_XREG',
      time_series_timestamp_col = 'date',
      time_series_data_col = 'num_trips',
      forecast_limit_lower_bound = 0,
      horizon = 7
    ) AS
    SELECT date, num_trips, avg_tripduration, pct_subscriber, ratio_gender
    FROM `{PROJECT_ID}.{DATASET_ID}.arima_xreg_trips`
    WHERE start_station_name = 'Pershing Square North' AND splits = 'TRAIN'
    """
    client.query(query).result()
except Exception as e:
    print(f'forecast_limit_lower_bound failed as expected for ARIMA_PLUS_XREG:\n{e}')
```

---
## Examples — `%%bigquery` Magics

The same operations using IPython magic commands — write SQL directly in cells without Python string wrapping.

### Forecast with `%%bigquery`

```sql
%%bigquery --project {PROJECT_ID}

SELECT start_station_name, forecast_timestamp, forecast_value
FROM ML.FORECAST(MODEL `statmike-mlops-349915.bq_ml.arima_xreg_multi`,
  STRUCT(28 AS horizon),
  (SELECT start_station_name, date, avg_tripduration, pct_subscriber, ratio_gender
   FROM `statmike-mlops-349915.bq_ml.arima_xreg_trips` WHERE splits = 'TEST'))
ORDER BY start_station_name, forecast_timestamp
LIMIT 10
```

---
## BigFrames

**No dedicated `ARIMAPlusXReg` class exists** (checked the live BigFrames API reference: `bigframes.ml.forecasting` exposes only `ARIMAPlus`, which is univariate). Use the SQL `CREATE MODEL` interface shown above for multivariate/external-regressor forecasting.
