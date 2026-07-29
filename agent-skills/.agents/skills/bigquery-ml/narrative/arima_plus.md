# ARIMA_PLUS — BigQuery ML

Train a **univariate time series forecasting** model with `CREATE MODEL` (model_type = `ARIMA_PLUS`) — an automated pipeline around auto.ARIMA that handles frequency detection, missing-value interpolation, spike/dip cleaning, step-change adjustment, seasonal + trend decomposition, and holiday effects automatically. No data leaves BigQuery, and no separate training infrastructure is needed.

**Lifecycle:** `CREATE MODEL` → `ML.ARIMA_EVALUATE` → `ML.FEATURE_INFO` / `ML.TRAINING_INFO` → `ML.EVALUATE` → `ML.FORECAST` → `ML.EXPLAIN_FORECAST` → `ML.ARIMA_COEFFICIENTS` → `ML.HOLIDAY_INFO` (built-in + custom holidays, manual ARIMA order, hierarchical forecasting) → `ML.DETECT_ANOMALIES` → granularity/missing-data gotchas

**Eleventh model type in the project, first in Phase 4 (time series).**

**When to use ARIMA_PLUS:**
- You have a single demand signal over time (one timestamp + one value column) and want a forecast plus prediction intervals.
- You want to forecast many independent series in one query (one model per `time_series_id_col` group).
- You want interpretable decomposition (trend, seasonality, holiday effects, spikes/dips, step changes) via `ML.EXPLAIN_FORECAST`.
- You want in-database time series anomaly detection via `ML.DETECT_ANOMALIES`.
- You have a natural hierarchy (e.g. store → city → region) and want reconciled forecasts at every level in one model — see `hierarchical_time_series_cols` in Step 10. For a custom top-down alternative to BQML's built-in bottom-up reconciliation, see `workflows/hierarchical_forecasting` (`workflows/hierarchical_forecasting/`).
- You have known future covariates that should improve accuracy — use `models/arima_plus_xreg` (`ARIMA_PLUS_XREG`) instead.
- For zero-config foundation-model forecasting with no `CREATE MODEL` step at all, see the sibling `bq-ai-functions` project's `AI.FORECAST` (TimesFM).

**Data:** [`bigquery-public-data.new_york_citibike.citibike_trips`](https://console.cloud.google.com/marketplace/product/bigquery-public-datasets), aggregated to one row per (station, day) = daily trip count, for 5 stations: Pershing Square North, E 17 St & Broadway, W 21 St & 6 Ave, Lafayette St & E 8 St, West St & Chambers St. Pershing Square North has a shorter history (starts 2014-09-01, others start 2013-07-01) — real-world messiness multi-series ARIMA_PLUS handles natively. TEST = the last 28 days of data (after 2018-05-03); `horizon = 28`. Step 10's hierarchical-forecasting demo uses a separate small set of 6 stations grouped into 2 real Manhattan neighborhoods (Midtown, Downtown) — a genuine geographic hierarchy this 5-station set doesn't have (all 5 sit in the same neighborhood).

**References:** `RESOURCES.md` (Full reference) | [CREATE MODEL (time series) docs](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-time-series) | [ML.FORECAST docs](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-forecast) | `setup` (Setup guide)

---
## Setup

Set your project and location, authenticate, and create a shared dataset for the model.

> ARIMA_PLUS trains on data already in BigQuery — no connection or remote model required. The model is created with `CREATE MODEL` and stored in your dataset. See the `setup` (Setup Reference) for details.

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

Daily trip counts per station, with a `splits` column marking the last 28 days as `TEST` (held out for evaluation) and everything before as `TRAIN`.

```python
query = f"""
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.arima_plus_trips` AS
WITH daily AS (
  SELECT
    start_station_name,
    DATE(starttime) AS date,
    COUNT(*) AS num_trips
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
print('Table arima_plus_trips created')
```

---
## Step 1 — Create a single-series model with `CREATE MODEL`

The essentials are `time_series_timestamp_col` and `time_series_data_col` — no `time_series_id_col` yet, so this fits one station. ARIMA_PLUS ignores a validation split — train on `TRAIN` alone, hold out `TEST` for evaluation below.

```python
query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.arima_plus_pershing`
OPTIONS(
  model_type = 'ARIMA_PLUS',
  time_series_timestamp_col = 'date',
  time_series_data_col = 'num_trips',
  holiday_region = ['GLOBAL', 'US'],
  horizon = 28
) AS
SELECT date, num_trips
FROM `{PROJECT_ID}.{DATASET_ID}.arima_plus_trips`
WHERE start_station_name = 'Pershing Square North' AND splits = 'TRAIN'
"""
client.query(query).result()
print('Model arima_plus_pershing created')
```

```python
query = f"""
SELECT *
FROM ML.EVALUATE(MODEL `{PROJECT_ID}.{DATASET_ID}.arima_plus_pershing`,
  (SELECT date, num_trips FROM `{PROJECT_ID}.{DATASET_ID}.arima_plus_trips`
   WHERE start_station_name = 'Pershing Square North' AND splits = 'TEST'))
"""
client.query(query).to_dataframe()
```

---
## Step 2 — Create a multi-series model (all 5 stations in one `CREATE MODEL`)

`time_series_id_col` fits and forecasts all 5 series in a single model — this is the model used for the rest of this notebook. Pershing Square North's shorter history (Step 1's data starts later than the other four stations) demonstrates that multi-series ARIMA_PLUS handles series of different lengths within one model.

```python
query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.arima_plus_multi`
OPTIONS(
  model_type = 'ARIMA_PLUS',
  time_series_timestamp_col = 'date',
  time_series_data_col = 'num_trips',
  time_series_id_col = 'start_station_name',
  holiday_region = ['GLOBAL', 'US'],
  horizon = 28
) AS
SELECT start_station_name, date, num_trips
FROM `{PROJECT_ID}.{DATASET_ID}.arima_plus_trips`
WHERE splits = 'TRAIN'
"""
client.query(query).result()
print('Model arima_plus_multi created')
```

---
## Step 3 — Per-series diagnostics with `ML.ARIMA_EVALUATE`

Returns the selected `(p,d,q)` order, AIC, and which components (holiday effects, spikes/dips, step changes, seasonality) were detected — one row per series.

```python
query = f"""
SELECT *
FROM ML.ARIMA_EVALUATE(MODEL `{PROJECT_ID}.{DATASET_ID}.arima_plus_multi`)
"""
client.query(query).to_dataframe()
```

---
## Step 4 — Introspect the model

```python
query = f"""
SELECT *
FROM ML.FEATURE_INFO(MODEL `{PROJECT_ID}.{DATASET_ID}.arima_plus_multi`)
"""
client.query(query).to_dataframe()
```

```python
query = f"""
SELECT *
FROM ML.TRAINING_INFO(MODEL `{PROJECT_ID}.{DATASET_ID}.arima_plus_multi`)
"""
client.query(query).to_dataframe()
```

---
## Step 5 — Evaluate forecast accuracy on the held-out TEST period

Without eval data, `ML.EVALUATE` falls back to the same ARIMA-fit stats as `ML.ARIMA_EVALUATE`. Passing the `TEST` split explicitly with `perform_aggregation=TRUE` instead returns forecast-accuracy metrics per series — plotted below by station for a quick at-a-glance comparison.

```python
query = f"""
SELECT *
FROM ML.EVALUATE(MODEL `{PROJECT_ID}.{DATASET_ID}.arima_plus_multi`,
  (SELECT start_station_name, date, num_trips FROM `{PROJECT_ID}.{DATASET_ID}.arima_plus_trips` WHERE splits = 'TEST'),
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
## Step 6 — Forecast with `ML.FORECAST`

```python
query = f"""
SELECT start_station_name, forecast_timestamp, forecast_value,
       prediction_interval_lower_bound, prediction_interval_upper_bound
FROM ML.FORECAST(MODEL `{PROJECT_ID}.{DATASET_ID}.arima_plus_multi`, STRUCT(28 AS horizon, 0.9 AS confidence_level))
ORDER BY start_station_name, forecast_timestamp
"""
forecast = client.query(query).to_dataframe()
forecast.head()
```

```python
import matplotlib.pyplot as plt

query = f"""
SELECT start_station_name, date AS timestamp, num_trips AS value
FROM `{PROJECT_ID}.{DATASET_ID}.arima_plus_trips`
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
## Step 7 — Decompose with `ML.EXPLAIN_FORECAST`

Adds trend, seasonal, holiday, spike/dip, and step-change components to every history and forecast point — requires `decompose_time_series=TRUE` (the default).

```python
query = f"""
SELECT time_series_timestamp, time_series_type, time_series_data, time_series_adjusted_data,
       trend, seasonal_period_weekly, seasonal_period_yearly, holiday_effect
FROM ML.EXPLAIN_FORECAST(MODEL `{PROJECT_ID}.{DATASET_ID}.arima_plus_multi`, STRUCT(28 AS horizon))
WHERE start_station_name = 'Pershing Square North'
ORDER BY time_series_timestamp
"""
explain = client.query(query).to_dataframe()
explain.tail()
```

```python
fig, axes = plt.subplots(4, 1, figsize=(10, 9), sharex=True)
axes[0].plot(explain['time_series_timestamp'], explain['time_series_data'], color='#4285F4')
axes[0].set_title('Observed / Forecast (time_series_data)')
axes[1].plot(explain['time_series_timestamp'], explain['trend'], color='#34A853')
axes[1].set_title('Trend')
axes[2].plot(explain['time_series_timestamp'], explain['seasonal_period_weekly'], color='#FBBC04')
axes[2].set_title('Weekly seasonality')
axes[3].plot(explain['time_series_timestamp'], explain['holiday_effect'], color='#EA4335')
axes[3].set_title('Holiday effect')
plt.tight_layout()
plt.show()
```

---
## Step 8 — Inspect coefficients with `ML.ARIMA_COEFFICIENTS`

```python
query = f"""
SELECT *
FROM ML.ARIMA_COEFFICIENTS(MODEL `{PROJECT_ID}.{DATASET_ID}.arima_plus_multi`)
"""
client.query(query).to_dataframe()
```

---
## Step 9 — Modeled holidays with `ML.HOLIDAY_INFO`

```python
query = f"""
SELECT *
FROM ML.HOLIDAY_INFO(MODEL `{PROJECT_ID}.{DATASET_ID}.arima_plus_multi`)
WHERE region = 'US' AND primary_date BETWEEN '2016-01-01' AND '2018-12-31'
ORDER BY primary_date
"""
client.query(query).to_dataframe()
```

---
## Step 10 — Additional options: custom holidays, manual ARIMA order, forecast bounds, and hierarchical forecasting

`holiday_region` only covers built-in regional holidays. To model an event that matters for *this* series but isn't a public holiday — a marathon, a local festival, a store's own promotion calendar — supply a **custom holiday** table using the special two-block `AS ( training_data AS (...), custom_holiday AS (...) )` syntax (no `WITH` keyword; `training_data` and `custom_holiday` are the two required block names, not ordinary CTEs). `custom_holiday` needs `region`, `holiday_name` (must be a valid column-name string — no spaces), `primary_date`, `preholiday_days`, `postholiday_days`. The custom holiday's effect then shows up in `ML.EXPLAIN_FORECAST` as `holiday_effect_<holiday_name>`, alongside the built-in `holiday_effect_*` columns.

Separately, `auto_arima` is `TRUE` by default (the search used everywhere else in this notebook). Setting `auto_arima = FALSE` with `non_seasonal_order = STRUCT(p, d, q)` disables the search and pins an exact order — single-series only.

All three demonstrated on Pershing Square North alone, as small standalone models (not the main `arima_plus_multi` model).

> **GOTCHA (verified): `forecast_limit_lower_bound`/`forecast_limit_upper_bound` are incompatible with `ML.EXPLAIN_FORECAST`.** A bound on the forecast is a genuinely useful option — trip counts, for example, can never be negative — but a model trained with either bound set fails `ML.EXPLAIN_FORECAST` with `"This model was trained with either 'forecast_limit_lower_bound' or 'forecast_limit_upper_bound' being specified. In this case, EXPLAIN_FORECAST is not supported."` `ML.FORECAST` and every other lifecycle function are unaffected — only `ML.EXPLAIN_FORECAST` is blocked. This is why `arima_plus_multi` (Step 2) does **not** set a bound — decomposition (Step 7) is used throughout this notebook. Demonstrated below as its own small model instead.

### Hierarchical forecasting with `hierarchical_time_series_cols`

`time_series_id_col` (Step 2) forecasts each series independently — a station's forecast has no relationship to its neighborhood's forecast. `hierarchical_time_series_cols` changes this: given an ordered list of grouping columns (finest-grained last), BigQuery ML trains the base-level series as usual, then **automatically reconciles forecasts at every rollup level plus an overall total** — all in one `CREATE MODEL` call, no extra models or manual aggregation needed.

Demonstrated below on a small, separate 6-station table (3 stations in each of 2 real Manhattan neighborhoods — Midtown, Downtown), since the main 5-station table doesn't have a real hierarchy (all 5 are effectively the same neighborhood). Verified directly below that the reconciliation is **bottom-up**: station-level forecasts sum exactly to their neighborhood's forecast, and neighborhood forecasts sum exactly to the overall total. BigQuery ML has no built-in *top-down* alternative (disaggregating a top-level forecast down through the hierarchy) — see `workflows/hierarchical_forecasting` (`workflows/hierarchical_forecasting/`) for a from-scratch implementation of that approach, compared head-to-head against this bottom-up method.

```python
query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.arima_plus_custom_holiday`
OPTIONS(
  model_type = 'ARIMA_PLUS',
  holiday_region = 'US',
  time_series_timestamp_col = 'date',
  time_series_data_col = 'num_trips',
  horizon = 7
) AS (
  training_data AS (
    SELECT date, num_trips
    FROM `{PROJECT_ID}.{DATASET_ID}.arima_plus_trips`
    WHERE start_station_name = 'Pershing Square North' AND splits = 'TRAIN'
  ),
  custom_holiday AS (
    SELECT 'US' AS region, 'NYCMarathon' AS holiday_name, primary_date, 1 AS preholiday_days, 1 AS postholiday_days
    FROM UNNEST([DATE('2014-11-02'), DATE('2015-11-01'), DATE('2016-11-06'), DATE('2017-11-05')]) AS primary_date
  )
)
"""
client.query(query).result()
print('Model arima_plus_custom_holiday created')

query = f"""
SELECT *
FROM ML.HOLIDAY_INFO(MODEL `{PROJECT_ID}.{DATASET_ID}.arima_plus_custom_holiday`)
WHERE holiday_name = 'NYCMarathon'
"""
client.query(query).to_dataframe()
```

```python
# The custom holiday's effect appears in ML.EXPLAIN_FORECAST as
# holiday_effect_<holiday_name> -- confirming the column exists, not that the
# effect is large: with only 4 marathon dates in the training history, the
# estimated effect for this station comes out at 0.0 (statistically
# indistinguishable from no effect) -- a real, honest result, not a bug.
query = f"""
SELECT time_series_timestamp, holiday_effect_NYCMarathon
FROM ML.EXPLAIN_FORECAST(MODEL `{PROJECT_ID}.{DATASET_ID}.arima_plus_custom_holiday`, STRUCT(7 AS horizon))
WHERE DATE(time_series_timestamp) BETWEEN '2016-11-04' AND '2016-11-08'
ORDER BY time_series_timestamp
"""
client.query(query).to_dataframe()
```

```python
query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.arima_plus_manual_order`
OPTIONS(
  model_type = 'ARIMA_PLUS',
  time_series_timestamp_col = 'date',
  time_series_data_col = 'num_trips',
  auto_arima = FALSE,
  non_seasonal_order = STRUCT(2 AS p, 1 AS d, 1 AS q),
  horizon = 7
) AS
SELECT date, num_trips
FROM `{PROJECT_ID}.{DATASET_ID}.arima_plus_trips`
WHERE start_station_name = 'Pershing Square North' AND splits = 'TRAIN'
"""
client.query(query).result()
print('Model arima_plus_manual_order created')

query = f"""
SELECT non_seasonal_p, non_seasonal_d, non_seasonal_q
FROM ML.ARIMA_EVALUATE(MODEL `{PROJECT_ID}.{DATASET_ID}.arima_plus_manual_order`)
"""
client.query(query).to_dataframe()
```

```python
query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.arima_plus_bounded`
OPTIONS(
  model_type = 'ARIMA_PLUS',
  time_series_timestamp_col = 'date',
  time_series_data_col = 'num_trips',
  forecast_limit_lower_bound = 0,
  horizon = 7
) AS
SELECT date, num_trips
FROM `{PROJECT_ID}.{DATASET_ID}.arima_plus_trips`
WHERE start_station_name = 'Pershing Square North' AND splits = 'TRAIN'
"""
client.query(query).result()
print('Model arima_plus_bounded created')

# ML.FORECAST still works fine with a bound in place
query = f"""
SELECT forecast_timestamp, forecast_value
FROM ML.FORECAST(MODEL `{PROJECT_ID}.{DATASET_ID}.arima_plus_bounded`)
ORDER BY forecast_timestamp
LIMIT 5
"""
client.query(query).to_dataframe()
```

```python
# ML.EXPLAIN_FORECAST -- expected to fail on a bounded model
try:
    query = f"""SELECT * FROM ML.EXPLAIN_FORECAST(MODEL `{PROJECT_ID}.{DATASET_ID}.arima_plus_bounded`)"""
    client.query(query).result()
except Exception as e:
    print(f'ML.EXPLAIN_FORECAST failed as expected on a bounded model:\n{e}')
```

```python
query = f"""
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.arima_plus_hierarchy_trips` AS
SELECT
  CASE start_station_name
    WHEN 'Pershing Square North' THEN 'Midtown'
    WHEN '8 Ave & W 31 St' THEN 'Midtown'
    WHEN 'W 41 St & 8 Ave' THEN 'Midtown'
    WHEN 'Lafayette St & E 8 St' THEN 'Downtown'
    WHEN 'West St & Chambers St' THEN 'Downtown'
    WHEN 'Christopher St & Greenwich St' THEN 'Downtown'
  END AS neighborhood,
  start_station_name,
  DATE(starttime) AS date,
  COUNT(*) AS num_trips
FROM `bigquery-public-data.new_york_citibike.citibike_trips`
WHERE start_station_name IN (
  'Pershing Square North', '8 Ave & W 31 St', 'W 41 St & 8 Ave',
  'Lafayette St & E 8 St', 'West St & Chambers St', 'Christopher St & Greenwich St'
)
GROUP BY neighborhood, start_station_name, date
"""
client.query(query).result()
print('Table arima_plus_hierarchy_trips created')

query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.arima_plus_hierarchy`
OPTIONS(
  model_type = 'ARIMA_PLUS',
  time_series_timestamp_col = 'date',
  time_series_data_col = 'num_trips',
  time_series_id_col = ['neighborhood', 'start_station_name'],
  hierarchical_time_series_cols = ['neighborhood', 'start_station_name'],
  holiday_region = ['GLOBAL', 'US'],
  horizon = 7
) AS
SELECT neighborhood, start_station_name, date, num_trips
FROM `{PROJECT_ID}.{DATASET_ID}.arima_plus_hierarchy_trips`
WHERE date <= DATE('2018-05-03')
"""
client.query(query).result()
print('Model arima_plus_hierarchy created')
```

```python
# One CREATE MODEL, three levels of forecasts: station-level rows (neighborhood + start_station_name
# both set), neighborhood-level rows (start_station_name NULL), and one overall-total row (both NULL).
query = f"""
SELECT DISTINCT neighborhood, start_station_name
FROM ML.FORECAST(MODEL `{PROJECT_ID}.{DATASET_ID}.arima_plus_hierarchy`, STRUCT(7 AS horizon))
ORDER BY neighborhood, start_station_name
"""
client.query(query).to_dataframe()
```

```python
# Verify the reconciliation is bottom-up: neighborhood forecast == sum of its stations' forecasts,
# and the overall total == sum of the neighborhood forecasts.
query = f"""
WITH f AS (
  SELECT neighborhood, start_station_name, forecast_timestamp, forecast_value
  FROM ML.FORECAST(MODEL `{PROJECT_ID}.{DATASET_ID}.arima_plus_hierarchy`, STRUCT(7 AS horizon))
)
SELECT
  forecast_timestamp,
  (SELECT forecast_value FROM f WHERE neighborhood = 'Midtown' AND start_station_name IS NULL
     AND forecast_timestamp = t.forecast_timestamp) AS midtown_direct,
  (SELECT SUM(forecast_value) FROM f WHERE neighborhood = 'Midtown' AND start_station_name IS NOT NULL
     AND forecast_timestamp = t.forecast_timestamp) AS midtown_summed_from_stations,
  (SELECT forecast_value FROM f WHERE neighborhood IS NULL AND start_station_name IS NULL
     AND forecast_timestamp = t.forecast_timestamp) AS overall_direct,
  (SELECT SUM(forecast_value) FROM f WHERE neighborhood IS NOT NULL AND start_station_name IS NULL
     AND forecast_timestamp = t.forecast_timestamp) AS overall_summed_from_neighborhoods
FROM (SELECT DISTINCT forecast_timestamp FROM f) t
ORDER BY forecast_timestamp
"""
client.query(query).to_dataframe()
```

`midtown_direct` matches `midtown_summed_from_stations` exactly, and `overall_direct` matches `overall_summed_from_neighborhoods` exactly, at every forecast day — confirming `hierarchical_time_series_cols` reconciles **bottom-up**: it does not adjust the base-level station forecasts at all, it just sums them upward through the hierarchy. There's no option here to reconcile the other direction (top-down, disaggregating a higher-level forecast down to the base level) — that requires a custom implementation, covered end-to-end in `workflows/hierarchical_forecasting` (`workflows/hierarchical_forecasting/`).

---
## Step 11 — Anomaly detection with `ML.DETECT_ANOMALIES`

The table below shows the top 10 flagged points by `anomaly_probability`. The plot after it shows every station's full history with `forecast` (from Step 6) alongside it, and every flagged anomaly marked directly on the time series — much easier to interpret in context than the table alone.

> **GOTCHA (verified): the full-history plot reveals a genuinely important, previously-unnoticed characteristic of `ARIMA_PLUS`'s gap handling.** `bigquery-public-data.new_york_citibike.citibike_trips` has zero rows for **October 2016 through March 2017** — a real ~6-month gap in the public dataset, across all 5 stations simultaneously (confirmed directly against the source table, not station-specific). The near-straight, gently-sloped line visible in every station's plot during this window is **not missing data or a plotting artifact** — `ML.DETECT_ANOMALIES` returns exactly one row per calendar day with no gaps at all, and inspecting the actual values confirms BQML **linearly interpolates the entire 6-month span** between the last real value before the gap and the first real value after it (verified directly: Pershing Square North goes `194.0` → a smooth, constant `~-0.415`/day decline → `118.0`, day by day, for all ~183 missing days). This is the same linear-interpolation mechanism documented for short 1-2 day gaps (Step 12) applied without limit to a much longer span — a straight 6-month line necessarily ignores all the weekly/seasonal structure that would have occurred in between, so treat any value in this window as a crude placeholder, not a real observation.

```python
query = f"""
SELECT start_station_name, date, num_trips, is_anomaly, anomaly_probability
FROM ML.DETECT_ANOMALIES(MODEL `{PROJECT_ID}.{DATASET_ID}.arima_plus_multi`, STRUCT(0.95 AS anomaly_prob_threshold))
WHERE is_anomaly
ORDER BY anomaly_probability DESC
LIMIT 10
"""
client.query(query).to_dataframe()
```

```python
query = f"""
SELECT start_station_name, date AS timestamp, num_trips AS value, is_anomaly
FROM ML.DETECT_ANOMALIES(MODEL `{PROJECT_ID}.{DATASET_ID}.arima_plus_multi`, STRUCT(0.95 AS anomaly_prob_threshold))
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
## Step 12 — GOTCHA: granularity and missing-data handling

> **GOTCHA (verified):** requesting a **coarser** granularity than the data errors immediately — `data_frequency='WEEKLY'` on daily data fails with `"Invalid time series: All input time intervals must be no less than the interval unit specified by data_frequency (WEEKLY)"`. Requesting a *finer* granularity than the data (e.g. `HOURLY` on daily data) is allowed and interpolates the gaps instead.
>
> **GOTCHA (verified): missing/absent days are linearly interpolated.** Pershing Square North has no row at all for `2015-10-20` in the source data (a genuine gap, not a zero-trip day) — `ML.EXPLAIN_FORECAST`'s `time_series_data` for that date is `252.0`, exactly the average of the neighboring days `2015-10-19` (141) and `2015-10-21` (363): `(141+363)/2=252`.

```python
# WEEKLY on daily data -- expected to fail
try:
    query = f"""
    CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.arima_plus_weekly_error`
    OPTIONS(
      model_type = 'ARIMA_PLUS',
      time_series_timestamp_col = 'date',
      time_series_data_col = 'num_trips',
      data_frequency = 'WEEKLY',
      horizon = 4
    ) AS
    SELECT date, num_trips
    FROM `{PROJECT_ID}.{DATASET_ID}.arima_plus_trips`
    WHERE start_station_name = 'Pershing Square North' AND splits = 'TRAIN'
    """
    client.query(query).result()
except Exception as e:
    print(f'WEEKLY on daily data failed as expected:\n{e}')
```

```python
# Confirm 2015-10-20 has no row in the source data for this station
query = f"""
SELECT COUNT(*) AS n
FROM `{PROJECT_ID}.{DATASET_ID}.arima_plus_trips`
WHERE start_station_name = 'Pershing Square North' AND date = '2015-10-20'
"""
print('Rows for 2015-10-20:', client.query(query).to_dataframe()['n'].iloc[0])

# The interpolated value in ML.EXPLAIN_FORECAST's history
query = f"""
SELECT time_series_timestamp, time_series_data
FROM ML.EXPLAIN_FORECAST(MODEL `{PROJECT_ID}.{DATASET_ID}.arima_plus_multi`, STRUCT(28 AS horizon))
WHERE start_station_name = 'Pershing Square North'
  AND DATE(time_series_timestamp) BETWEEN '2015-10-18' AND '2015-10-23'
ORDER BY time_series_timestamp
"""
client.query(query).to_dataframe()
```

---
## Examples — `%%bigquery` Magics

The same operations using IPython magic commands — write SQL directly in cells without Python string wrapping.

### Forecast with `%%bigquery`

```sql
%%bigquery --project {PROJECT_ID}

SELECT start_station_name, forecast_timestamp, forecast_value
FROM ML.FORECAST(MODEL `statmike-mlops-349915.bq_ml.arima_plus_multi`, STRUCT(28 AS horizon))
ORDER BY start_station_name, forecast_timestamp
LIMIT 10
```

---
## Examples — BigFrames

`bigframes.ml.forecasting.ARIMAPlus` mirrors the SQL interface, including multi-series via `id_col`.

```python
import bigframes.pandas as bpd

bpd.close_session()  # Reset session to apply project/location settings
bpd.options.bigquery.project = PROJECT_ID
bpd.options.bigquery.location = LOCATION
```

```python
from bigframes.ml.forecasting import ARIMAPlus

df = bpd.read_gbq(f'{PROJECT_ID}.{DATASET_ID}.arima_plus_trips')
df = df[df['splits'] == 'TRAIN']

model = ARIMAPlus(horizon=28, holiday_region='US')
model.fit(df[['date']], df[['num_trips']], id_col=df[['start_station_name']])

model.predict(horizon=28, confidence_level=0.9)
```
