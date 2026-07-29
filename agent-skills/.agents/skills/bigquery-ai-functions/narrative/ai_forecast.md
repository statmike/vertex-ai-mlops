# AI.FORECAST — BigQuery AI Functions

`AI.FORECAST` is a table-valued function that forecasts future time series values using BigQuery ML's built-in TimesFM model. No model creation or training required.

**When to use it:**
- You want to forecast future values from historical time series data
- You need prediction intervals (confidence bounds) for forecasts
- You want to forecast multiple independent time series at once
- You need a zero-setup forecasting solution (no CREATE MODEL)
- You can specify a target date with `forecast_end_timestamp` instead of a numeric `horizon`
- You can control how much history the model sees with `context_window` (64–15,360 depending on model)

**Alternatives:**
- `functions/ai_detect_anomalies` (`AI.DETECT_ANOMALIES`) — Detect anomalies by comparing data against a forecast baseline
- `functions/ai_evaluate` (`AI.EVALUATE`) — Evaluate forecast accuracy against actual values
- `bq-ml/models/arima_plus` (`ARIMA_PLUS`) — the trainable, in-BigQuery classical statistical alternative: supports custom holiday effects, external regressors (`ARIMA_PLUS_XREG`), hierarchical reconciliation across a real dimension hierarchy, and forecast bounds — none of which this zero-setup TimesFM model exposes. Use `AI.FORECAST` for a fast, no-training baseline; reach for `ARIMA_PLUS` when you need that level of control.

**Featured in:** `workflows/time_series_intelligence` (Time Series Intelligence)

**References:** `RESOURCES.md` (Full syntax reference) | [Official documentation](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-forecast) | `setup` (Setup guide)

---
## Setup

Set your project and location, authenticate, and create a temporary dataset for this notebook.

> This function doesn't require a connection or model — it uses end-user credentials automatically. See the `setup` (Setup Reference) for details.

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
## Examples — SQL

Progressive examples from simplest to most advanced. Each cell adds one new concept.

### Setup: Create sample time series data

Generate synthetic daily sales data with realistic patterns using SQL.

```python
# Create synthetic daily sales data with trend and weekly seasonality
query = f'''
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.ai_forecast_sales` AS
WITH dates AS (
  SELECT date
  FROM UNNEST(GENERATE_DATE_ARRAY('2024-01-01', '2024-12-31')) AS date
)
SELECT
  date,
  -- Base sales + trend + weekly seasonality + noise
  GREATEST(0,
    1000
    + EXTRACT(DAYOFYEAR FROM date) * 2  -- upward trend
    + CASE EXTRACT(DAYOFWEEK FROM date)
        WHEN 1 THEN -200  -- Sunday dip
        WHEN 7 THEN 300   -- Saturday peak
        WHEN 6 THEN 200   -- Friday boost
        ELSE 0
      END
    + CAST(200 * (RAND() - 0.5) AS INT64)  -- random noise
  ) AS daily_sales
FROM dates
'''
client.query(query).result()

# Preview the data
df = client.query(f'SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.ai_forecast_sales` ORDER BY date LIMIT 10').to_dataframe()
print(f'Rows: {client.query(f"SELECT COUNT(*) AS n FROM `{PROJECT_ID}.{DATASET_ID}.ai_forecast_sales`").to_dataframe().iloc[0]["n"]}')
df
```

### 1. Basic forecast

`AI.FORECAST` requires `data_col` and `timestamp_col`. Default horizon is 10 time steps.

```python
query = f'''
SELECT *
FROM AI.FORECAST(
  TABLE `{PROJECT_ID}.{DATASET_ID}.ai_forecast_sales`,
  data_col => 'daily_sales',
  timestamp_col => 'date'
)
'''
client.query(query).to_dataframe()
```

### 2. Custom horizon

Forecast more time steps into the future.

```python
query = f'''
SELECT *
FROM AI.FORECAST(
  TABLE `{PROJECT_ID}.{DATASET_ID}.ai_forecast_sales`,
  data_col => 'daily_sales',
  timestamp_col => 'date',
  horizon => 30
)
'''
client.query(query).to_dataframe()
```

### 3. Include historical data

Set `output_historical_time_series => TRUE` to get historical + forecasted data in one result for comparison.

```python
query = f'''
SELECT *
FROM AI.FORECAST(
  (SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.ai_forecast_sales`
   WHERE date >= '2024-11-01'),  -- last 2 months for context
  data_col => 'daily_sales',
  timestamp_col => 'date',
  horizon => 14,
  output_historical_time_series => TRUE
)
ORDER BY time_series_timestamp
'''
df = client.query(query).to_dataframe()
print(f'Historical rows: {(df["time_series_type"] == "history").sum()}')
print(f'Forecast rows: {(df["time_series_type"] == "forecast").sum()}')
df.tail(20)
```

### 4. Multi-series forecasting with id_cols

Forecast multiple independent time series at once by specifying `id_cols`.

```python
# Create multi-series data
query = f'''
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.ai_forecast_multi_series` AS
WITH dates AS (
  SELECT date
  FROM UNNEST(GENERATE_DATE_ARRAY('2024-01-01', '2024-12-31')) AS date
),
stores AS (
  SELECT * FROM UNNEST([
    STRUCT('downtown' AS store_id, 1500 AS base_sales),
    STRUCT('suburban', 800),
    STRUCT('airport', 2000)
  ])
)
SELECT
  s.store_id,
  d.date,
  GREATEST(0, s.base_sales + EXTRACT(DAYOFYEAR FROM d.date) * 1 + CAST(100 * (RAND() - 0.5) AS INT64)) AS daily_sales
FROM dates d CROSS JOIN stores s
'''
client.query(query).result()
print('Multi-series data created')
```

```python
# Forecast each store independently
query = f'''
SELECT *
FROM AI.FORECAST(
  TABLE `{PROJECT_ID}.{DATASET_ID}.ai_forecast_multi_series`,
  data_col => 'daily_sales',
  timestamp_col => 'date',
  id_cols => ['store_id'],
  horizon => 14
)
ORDER BY store_id, forecast_timestamp
'''
client.query(query).to_dataframe()
```

### 5. Confidence level and TimesFM model version

Control prediction interval width and model version.

```python
query = f'''
SELECT *
FROM AI.FORECAST(
  TABLE `{PROJECT_ID}.{DATASET_ID}.ai_forecast_sales`,
  data_col => 'daily_sales',
  timestamp_col => 'date',
  horizon => 14,
  confidence_level => 0.99,
  model => 'TimesFM 2.0'
)
'''
client.query(query).to_dataframe()
```

### 6. Forecast to a specific date

Use `forecast_end_timestamp` instead of `horizon` to forecast up to a target date. The horizon is calculated automatically from the data's frequency. Mutually exclusive with `horizon`.

```python
query = f'''
SELECT *
FROM AI.FORECAST(
  TABLE `{PROJECT_ID}.{DATASET_ID}.ai_forecast_sales`,
  data_col => 'daily_sales',
  timestamp_col => 'date',
  forecast_end_timestamp => '2025-01-15'
)
'''
df = client.query(query).to_dataframe()
print(f'Forecasted {len(df)} days (through {df["forecast_timestamp"].max().strftime("%Y-%m-%d")})')
df
```

### 7. Setting the context window

The `context_window` controls how many historical time points the model uses to learn patterns. By default, the smallest window covering your data is auto-selected.

Supported values:
- **TimesFM 2.0:** 64, 128, 256, 512, 1024, 2048
- **TimesFM 2.5:** 64, 128, 256, 512, 1024, 2048, 4096, 8192, 15360

```python
query = f'''
SELECT
  forecast_timestamp,
  ROUND(forecast_value, 0) AS forecast,
  ROUND(prediction_interval_lower_bound, 0) AS lower,
  ROUND(prediction_interval_upper_bound, 0) AS upper
FROM AI.FORECAST(
  TABLE `{PROJECT_ID}.{DATASET_ID}.ai_forecast_sales`,
  data_col => 'daily_sales',
  timestamp_col => 'date',
  horizon => 7,
  context_window => 128
)
'''
client.query(query).to_dataframe()
```

---
## Examples — `%%bigquery` Magics

The same examples using IPython magic commands. Magics let you write SQL directly in notebook cells without Python string wrapping.

Key patterns:
- `%%bigquery` — run SQL, display results inline
- `%%bigquery df` — run SQL, capture results into a pandas DataFrame

### Basic forecast with `%%bigquery`

```sql
%%bigquery --project {PROJECT_ID}

SELECT *
FROM AI.FORECAST(
  TABLE `statmike-mlops-349915.bq_ai_functions.ai_forecast_sales`,
  data_col => 'daily_sales',
  timestamp_col => 'date',
  horizon => 7
)
```

---
## Examples — BigFrames

BigFrames wraps `AI.FORECAST` via `bbq.ai.forecast()`. No model object needed.

```python
import bigframes.pandas as bpd
import bigframes.bigquery as bbq

bpd.options.bigquery.project = PROJECT_ID
bpd.options.bigquery.location = LOCATION
```

### Basic forecast

```python
# Load the time series data
df = bpd.read_gbq(f'{PROJECT_ID}.{DATASET_ID}.ai_forecast_sales')

# Forecast
forecast = bbq.ai.forecast(
    df,
    data_col='daily_sales',
    timestamp_col='date',
    horizon=14
)
forecast.to_pandas()
```
