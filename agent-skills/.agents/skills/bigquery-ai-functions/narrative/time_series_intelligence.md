# Time Series Intelligence — BigQuery AI Functions

An end-to-end time series analysis pipeline:

1. **Generate** realistic time series data with SQL
2. **Forecast** future values with `AI.FORECAST` (by horizon or target date)
3. **Detect anomalies** by comparing actuals against a forecast baseline with `AI.DETECT_ANOMALIES`
4. **Evaluate** forecast accuracy with `AI.EVALUATE` (compare models and context windows)
5. **Explain** a metric change by segment with `AI.KEY_DRIVERS`

**What this demonstrates:**
- Using TimesFM (Google's foundation model for time series) — no training required
- Forecasting with confidence intervals, using `horizon` or `forecast_end_timestamp`
- Anomaly detection by comparing target data against a forecast baseline
- Quantitative evaluation of forecast quality (MAE, RMSE, MAPE, MASE)
- Tuning `context_window` to control how much history the model uses
- Explaining *why* a metric changed between two periods with key driver analysis

**Functions used:** `functions/ai_forecast` (`AI.FORECAST`) | `functions/ai_detect_anomalies` (`AI.DETECT_ANOMALIES`) | `functions/ai_evaluate` (`AI.EVALUATE`) | `functions/ai_key_drivers` (`AI.KEY_DRIVERS`)

**Prerequisites:** `setup` (Setup guide) | `RESOURCES.md` (Function reference)

---
## Setup

Set your project and location, authenticate, and create a shared dataset.

> Time series functions (`AI.FORECAST`, `AI.DETECT_ANOMALIES`, `AI.EVALUATE`) use TimesFM and don't require a connection or model — they use end-user credentials automatically. See the `setup` (Setup Reference) for details.

```python
PROJECT_ID = 'statmike-mlops-349915'  # <-- Replace with your project ID
LOCATION = 'US'  # BigQuery dataset location
DATASET_ID = 'bq_ai_functions'  # Shared dataset across all notebooks
```

### Environment

> **Already set up the project environment?** The cell below is a no-op — packages are already in your kernel. See the `setup` (Setup Reference) for details.
>
> **Running standalone** (Colab, Colab Enterprise, Vertex AI Workbench)? The cell below installs required packages into your current kernel.

```python
from google.cloud import bigquery
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

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
## Step 1 — Generate sample time series data

Create a year of daily sales data with realistic patterns: upward trend, weekly seasonality (weekends higher), and random noise. We also inject a few anomalies in December to detect later.

```python
query = f'''
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.workflow_ts_sales` AS
WITH base_data AS (
  SELECT
    date,
    GREATEST(0,
      1000
      + EXTRACT(DAYOFYEAR FROM date) * 2                         -- upward trend
      + CASE EXTRACT(DAYOFWEEK FROM date)
          WHEN 1 THEN -200 WHEN 7 THEN 300 WHEN 6 THEN 200
          ELSE 0
        END                                                       -- weekly seasonality
      + CAST(200 * (RAND() - 0.5) AS INT64)                      -- random noise
    ) AS daily_sales
  FROM UNNEST(GENERATE_DATE_ARRAY('2024-01-01', '2024-12-31')) AS date
)
SELECT
  date,
  CASE
    WHEN date = '2024-12-10' THEN daily_sales + 1500  -- spike anomaly
    WHEN date = '2024-12-20' THEN daily_sales - 1200  -- dip anomaly
    WHEN date = '2024-12-25' THEN 0                   -- holiday shutdown
    ELSE daily_sales
  END AS daily_sales
FROM base_data
'''
client.query(query).result()

sales = client.query(f'''
  SELECT date, daily_sales
  FROM `{PROJECT_ID}.{DATASET_ID}.workflow_ts_sales`
  ORDER BY date
''').to_dataframe()
print(f'{len(sales)} days of data ({sales.date.min()} to {sales.date.max()})')
print(f'Sales range: {sales.daily_sales.min()} to {sales.daily_sales.max()}')

# Plot full year with training/test split and injected anomalies
fig, ax = plt.subplots(figsize=(14, 4))
train = sales[sales.date < pd.Timestamp('2024-12-01')]
test = sales[sales.date >= pd.Timestamp('2024-12-01')]
ax.plot(train.date, train.daily_sales, color='steelblue', linewidth=0.8, label='Training (Jan-Nov)')
ax.plot(test.date, test.daily_sales, color='darkorange', linewidth=0.8, label='Test (Dec)')

# Mark injected anomalies
for d, label in [('2024-12-10', 'Spike'), ('2024-12-20', 'Dip'), ('2024-12-25', 'Shutdown')]:
    row = sales[sales.date == pd.Timestamp(d)]
    if not row.empty:
        ax.scatter(row.date, row.daily_sales, color='red', s=60, zorder=5)
        ax.annotate(label, (row.date.values[0], row.daily_sales.values[0]),
                    textcoords='offset points', xytext=(8, 8), fontsize=8, color='red')

ax.axvline(pd.Timestamp('2024-12-01'), color='gray', linestyle='--', alpha=0.5, label='Train/Test split')
ax.set_xlabel('Date')
ax.set_ylabel('Daily Sales')
ax.set_title('Daily Sales Data — Full Year 2024')
ax.legend(loc='upper left', fontsize=8)
ax.xaxis.set_major_locator(mdates.MonthLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
plt.tight_layout()
plt.show()
```

---
## Step 2 — Forecast future values with AI.FORECAST

Use `AI.FORECAST` with TimesFM to predict the next 30 days of sales. TimesFM is a foundation model for time series — no training or tuning required.

We use the first 11 months as history and forecast into January 2025.

```python
query = f'''
SELECT *
FROM AI.FORECAST(
  (SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.workflow_ts_sales` WHERE date < '2024-12-01'),
  data_col => 'daily_sales',
  timestamp_col => 'date',
  horizon => 30,
  confidence_level => 0.95
)
ORDER BY forecast_timestamp
'''
forecast = client.query(query).to_dataframe()
print(f'Forecast: {len(forecast)} days ({forecast.forecast_timestamp.min().date()} to {forecast.forecast_timestamp.max().date()})')

# Plot: last 2 months of actuals + forecast with confidence interval
fig, ax = plt.subplots(figsize=(14, 4))
recent = sales[sales.date >= pd.Timestamp('2024-10-01')]
ax.plot(recent.date, recent.daily_sales, color='steelblue', linewidth=1, label='Actuals')
ax.plot(forecast.forecast_timestamp, forecast.forecast_value, color='darkgreen', linewidth=1.5, label='Forecast')
ax.fill_between(forecast.forecast_timestamp,
                forecast.prediction_interval_lower_bound,
                forecast.prediction_interval_upper_bound,
                color='green', alpha=0.15, label='95% confidence interval')
ax.axvline(pd.Timestamp('2024-12-01'), color='gray', linestyle='--', alpha=0.5, label='Forecast start')
ax.set_xlabel('Date')
ax.set_ylabel('Daily Sales')
ax.set_title('AI.FORECAST — 30-Day Sales Forecast from Training Data (Jan-Nov)')
ax.legend(loc='upper left', fontsize=8)
ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
plt.tight_layout()
plt.show()
```

### Forecast to a target date with forecast_end_timestamp

Instead of specifying `horizon` (number of points), you can use `forecast_end_timestamp` to forecast up to a specific date. This is useful when you need coverage through a known deadline — the function calculates the required horizon from the input data frequency automatically.

```python
query = f'''
SELECT
  forecast_timestamp,
  ROUND(forecast_value, 0) AS forecast_value,
  ROUND(prediction_interval_lower_bound, 0) AS lower_bound,
  ROUND(prediction_interval_upper_bound, 0) AS upper_bound
FROM AI.FORECAST(
  (SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.workflow_ts_sales` WHERE date < '2024-12-01'),
  data_col => 'daily_sales',
  timestamp_col => 'date',
  forecast_end_timestamp => '2025-01-15',
  confidence_level => 0.95
)
ORDER BY forecast_timestamp
'''
forecast_by_date = client.query(query).to_dataframe()
print(f'Forecast: {len(forecast_by_date)} days (through {forecast_by_date.forecast_timestamp.max().date()})')
print(f'  horizon=30 produced {len(forecast)} days, forecast_end_timestamp auto-calculated {len(forecast_by_date)} days')
forecast_by_date.tail(5)
```

### Forecast vs December actuals

Overlay the forecast on top of the actual December data (which contains our injected anomalies). This shows how the forecast represents "expected" behavior, making anomalies visually obvious.

```python
# Overlay forecast on actual December data
fig, ax = plt.subplots(figsize=(14, 4))
dec_actuals = sales[sales.date >= pd.Timestamp('2024-12-01')]

# Normalize forecast timestamps to timezone-naive dates for comparison
forecast['forecast_date'] = forecast.forecast_timestamp.dt.tz_localize(None).dt.normalize()
dec_forecast = forecast[forecast.forecast_date <= pd.Timestamp('2024-12-31')]

ax.plot(dec_actuals.date, dec_actuals.daily_sales, color='steelblue', linewidth=1, marker='o', markersize=3, label='Actuals (Dec)')
ax.plot(dec_forecast.forecast_date, dec_forecast.forecast_value, color='darkgreen', linewidth=1.5, label='Forecast')
ax.fill_between(dec_forecast.forecast_date,
                dec_forecast.prediction_interval_lower_bound,
                dec_forecast.prediction_interval_upper_bound,
                color='green', alpha=0.15, label='95% confidence interval')

# Highlight anomaly points
for d, label in [('2024-12-10', 'Spike'), ('2024-12-20', 'Dip'), ('2024-12-25', 'Shutdown')]:
    row = dec_actuals[dec_actuals.date == pd.Timestamp(d)]
    if not row.empty:
        ax.scatter(row.date, row.daily_sales, color='red', s=80, zorder=5)
        ax.annotate(label, (row.date.values[0], row.daily_sales.values[0]),
                    textcoords='offset points', xytext=(8, 8), fontsize=9, color='red', fontweight='bold')

ax.set_xlabel('Date')
ax.set_ylabel('Daily Sales')
ax.set_title('Forecast vs Actuals — December 2024 (anomalies visible)')
ax.legend(loc='upper left', fontsize=8)
ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
plt.tight_layout()
plt.show()
```

---
## Step 3 — Detect anomalies with AI.DETECT_ANOMALIES

Use `AI.DETECT_ANOMALIES` to find unusual data points in December. The function forecasts a baseline from the history (Jan–Nov) and flags points in the target (December) that fall outside the prediction interval.

We injected three anomalies: a spike on Dec 10, a dip on Dec 20, and a holiday shutdown on Dec 25.

```python
query = f'''
SELECT
  time_series_timestamp,
  time_series_data,
  is_anomaly,
  ROUND(anomaly_probability, 4) AS anomaly_prob,
  ROUND(lower_bound, 0) AS lower_bound,
  ROUND(upper_bound, 0) AS upper_bound
FROM AI.DETECT_ANOMALIES(
  (SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.workflow_ts_sales` WHERE date < '2024-12-01'),
  (SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.workflow_ts_sales` WHERE date >= '2024-12-01'),
  data_col => 'daily_sales',
  timestamp_col => 'date'
)
ORDER BY time_series_timestamp
'''
anomalies = client.query(query).to_dataframe()
print(f'December data: {len(anomalies)} days, Anomalies detected: {anomalies.is_anomaly.sum()}')

# Plot anomaly detection results
fig, ax = plt.subplots(figsize=(14, 4))
normal = anomalies[~anomalies.is_anomaly]
flagged = anomalies[anomalies.is_anomaly]

ax.fill_between(anomalies.time_series_timestamp, anomalies.lower_bound, anomalies.upper_bound,
                color='green', alpha=0.12, label='Expected range')
ax.plot(anomalies.time_series_timestamp, anomalies.time_series_data,
        color='steelblue', linewidth=1, marker='o', markersize=3, label='Actuals')
ax.scatter(flagged.time_series_timestamp, flagged.time_series_data,
           color='red', s=100, zorder=5, label=f'Anomalies ({len(flagged)} detected)')

for _, row in flagged.iterrows():
    atype = 'SPIKE' if row.time_series_data > row.upper_bound else 'DIP'
    ax.annotate(f'{atype}\np={row.anomaly_prob:.2f}',
                (row.time_series_timestamp, row.time_series_data),
                textcoords='offset points', xytext=(10, 10), fontsize=8, color='red',
                fontweight='bold', ha='left')

ax.set_xlabel('Date')
ax.set_ylabel('Daily Sales')
ax.set_title('AI.DETECT_ANOMALIES — December 2024')
ax.legend(loc='upper left', fontsize=8)
ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
plt.tight_layout()
plt.show()
```

### Anomaly details

Summary of each detected anomaly: what happened, how far outside the expected range, and the model's confidence.

```python
# Detailed anomaly summary
for _, row in flagged.iterrows():
    atype = 'SPIKE' if row.time_series_data > row.upper_bound else 'DIP'
    deviation = abs(row.time_series_data - (row.upper_bound if atype == 'SPIKE' else row.lower_bound))
    print(f'{row.time_series_timestamp.strftime("%b %d")} — {atype} (probability: {row.anomaly_prob:.2%})')
    print(f'  Actual: {row.time_series_data:.0f}, Expected range: {row.lower_bound:.0f} – {row.upper_bound:.0f}')
    print(f'  Deviation: {deviation:.0f} units outside expected range')
    print()
```

---
## Step 4 — Evaluate forecast accuracy with AI.EVALUATE

Use `AI.EVALUATE` to quantify how well the forecast matches actual December data. It computes standard metrics: MAE, MSE, RMSE, MAPE, and sMAPE.

Note: the anomalies in December will impact these metrics — in a real scenario, you might evaluate on clean data.

```python
query = f'''
SELECT
  ROUND(mean_absolute_error, 2) AS mae,
  ROUND(root_mean_squared_error, 2) AS rmse,
  ROUND(mean_absolute_percentage_error, 4) AS mape,
  ROUND(symmetric_mean_absolute_percentage_error, 4) AS smape
FROM AI.EVALUATE(
  (SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.workflow_ts_sales` WHERE date < '2024-12-01'),
  (SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.workflow_ts_sales` WHERE date >= '2024-12-01'),
  data_col => 'daily_sales',
  timestamp_col => 'date'
)
'''
metrics = client.query(query).to_dataframe()
print('Forecast accuracy metrics (Dec 2024):')
metrics
```

### Compare TimesFM model versions

Evaluate both TimesFM 2.0 and 2.5 to see which performs better on this data.

```python
results = []
for model_version in ['TimesFM 2.0', 'TimesFM 2.5']:
    query = f'''
    SELECT
      '{model_version}' AS model,
      ROUND(mean_absolute_error, 2) AS mae,
      ROUND(root_mean_squared_error, 2) AS rmse,
      ROUND(mean_absolute_percentage_error, 4) AS mape
    FROM AI.EVALUATE(
      (SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.workflow_ts_sales` WHERE date < '2024-12-01'),
      (SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.workflow_ts_sales` WHERE date >= '2024-12-01'),
      data_col => 'daily_sales',
      timestamp_col => 'date',
      model => '{model_version}'
    )
    '''
    results.append(client.query(query).to_dataframe())

comparison = pd.concat(results, ignore_index=True)
print('Model comparison:')
print(comparison.to_string(index=False))

# Visual comparison
fig, axes = plt.subplots(1, 3, figsize=(12, 3))
metrics = ['mae', 'rmse', 'mape']
titles = ['Mean Absolute Error', 'Root Mean Squared Error', 'Mean Abs % Error']
for ax, metric, title in zip(axes, metrics, titles):
    bars = ax.bar(comparison['model'], comparison[metric], color=['steelblue', 'darkorange'], width=0.5)
    ax.set_title(title, fontsize=10)
    ax.set_ylabel(metric.upper())
    for bar, val in zip(bars, comparison[metric]):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                f'{val:.2f}', ha='center', va='bottom', fontsize=9)
plt.suptitle('AI.EVALUATE — TimesFM Model Comparison', fontsize=12, y=1.02)
plt.tight_layout()
plt.show()
```

### Tune context_window

`context_window` controls how many historical data points the TimesFM model uses. The model auto-selects the smallest window that covers the input, but you can override this — a larger window gives the model more history to learn patterns from, while a smaller window focuses on recent trends.

Supported values for TimesFM 2.0: 64, 128, 256, 512, 1024, 2048. TimesFM 2.5 adds: 4096, 8192, 15360.

```python
results = []
for cw in [128, 256, 512]:
    query = f'''
    SELECT
      {cw} AS context_window,
      ROUND(mean_absolute_error, 2) AS mae,
      ROUND(root_mean_squared_error, 2) AS rmse,
      ROUND(mean_absolute_percentage_error, 4) AS mape
    FROM AI.EVALUATE(
      (SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.workflow_ts_sales` WHERE date < '2024-12-01'),
      (SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.workflow_ts_sales` WHERE date >= '2024-12-01'),
      data_col => 'daily_sales',
      timestamp_col => 'date',
      context_window => {cw}
    )
    '''
    results.append(client.query(query).to_dataframe())

cw_comparison = pd.concat(results, ignore_index=True)
print('Context window comparison (TimesFM 2.0, default):')
print(cw_comparison.to_string(index=False))

fig, axes = plt.subplots(1, 3, figsize=(12, 3))
for ax, metric, title in zip(axes, ['mae', 'rmse', 'mape'],
                              ['Mean Absolute Error', 'Root Mean Squared Error', 'Mean Abs % Error']):
    bars = ax.bar([str(v) for v in cw_comparison['context_window']],
                  cw_comparison[metric], color=['#4e79a7', '#59a14f', '#e15759'], width=0.5)
    ax.set_title(title, fontsize=10)
    ax.set_xlabel('context_window')
    for bar, val in zip(bars, cw_comparison[metric]):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                f'{val:.2f}', ha='center', va='bottom', fontsize=9)
plt.suptitle('AI.EVALUATE — Context Window Comparison', fontsize=12, y=1.02)
plt.tight_layout()
plt.show()
```

---
## Step 5 — Explain a change with AI.KEY_DRIVERS

Forecasting and anomaly detection tell you *what* happened to a metric over time. `AI.KEY_DRIVERS` answers a different question: when a metric shifts between two periods, **which segments drove the change?**

The daily series above is a single aggregate. To analyze drivers we need segmented data, so we generate a companion table broken out by `region` and `product_line`, then compare the **second half of the year (interest)** against the **first half (reference)**.

```python
query = f'''
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.workflow_ts_segmented` AS
WITH gen AS (
  SELECT
    region,
    product_line,
    d,
    GREATEST(0,
      300
      + CASE region WHEN 'West' THEN 120 WHEN 'East' THEN 80 ELSE 40 END
      + CASE product_line WHEN 'Accessories' THEN 60 WHEN 'Apparel' THEN 30 ELSE 10 END
      + CASE WHEN d >= '2024-07-01' AND region = 'West' AND product_line = 'Accessories'
             THEN 400 ELSE 0 END                                   -- injected H2 surge
      + CAST(60 * (RAND() - 0.5) AS INT64)                         -- random noise
    ) AS revenue
  FROM UNNEST(['West', 'East', 'Central']) AS region,
       UNNEST(['Accessories', 'Apparel', 'Hardware']) AS product_line,
       UNNEST(GENERATE_DATE_ARRAY('2024-01-01', '2024-12-31', INTERVAL 1 DAY)) AS d
)
SELECT region, product_line, revenue, (d >= '2024-07-01') AS is_interest
FROM gen
'''
client.query(query).result()

# Confirm the headline shift between the two halves
client.query(f'''
  SELECT
    IF(is_interest, 'H2 (interest)', 'H1 (reference)') AS period,
    SUM(revenue) AS total_revenue
  FROM `{PROJECT_ID}.{DATASET_ID}.workflow_ts_segmented`
  GROUP BY is_interest
  ORDER BY is_interest
''').to_dataframe()
```

### Which segments drove the change?

`AI.KEY_DRIVERS` decomposes the H1→H2 revenue change by `region` and `product_line`. Sort by `contribution` for the biggest absolute movers, and watch `unexpected_difference` for the segment that moved most against the overall trend — that's the injected **West / Accessories** surge.

```python
query = f'''
SELECT
  ARRAY_TO_STRING(drivers, ', ') AS segment,
  difference,
  unexpected_difference,
  ROUND(apriori_support, 3) AS apriori_support,
  contribution
FROM AI.KEY_DRIVERS(
  TABLE `{PROJECT_ID}.{DATASET_ID}.workflow_ts_segmented`,
  metric_col => 'revenue',
  dimension_cols => ['region', 'product_line'],
  interest_label_col => 'is_interest',
  top_k => 12
)
ORDER BY contribution DESC
'''
client.query(query).to_dataframe()
```
