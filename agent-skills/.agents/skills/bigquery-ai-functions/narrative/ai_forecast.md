# AI.FORECAST — BigQuery AI Functions

`AI.FORECAST` is a table-valued function that forecasts future time series values using BigQuery ML's built-in TimesFM model. No model creation or training required. Univariate forecasting is GA; multivariate forecasting and the TimesFM 3.0 model are Preview.

**When to use it:**
- You want to forecast future values from historical time series data
- You need prediction intervals (confidence bounds) for forecasts
- You want to forecast multiple independent time series at once
- You need a zero-setup forecasting solution (no CREATE MODEL)
- You can specify a target date with `forecast_end_timestamp` instead of a numeric `horizon`
- You can control how much history the model sees with `context_window` (64–15,360 on TimesFM 2.5; 64–2,048 on TimesFM 3.0)
- You have related series to forecast together, or covariates that should shape the forecast — TimesFM 3.0 (Preview) adds multivariate forecasting with `target_cols`, `past_covariate_cols` and `future_covariate_cols`

**Alternatives:**
- `functions/ai_detect_anomalies` (`AI.DETECT_ANOMALIES`) — Detect anomalies by comparing data against a forecast baseline
- `functions/ai_evaluate` (`AI.EVALUATE`) — Evaluate forecast accuracy against actual values
- `bq-ml/models/arima_plus` (`ARIMA_PLUS`) — the trainable, in-BigQuery classical statistical alternative: custom holiday effects, hierarchical reconciliation across a real dimension hierarchy, decomposable and explainable components (`ML.EXPLAIN_FORECAST`), and forecast bounds — none of which the TimesFM functions expose. External regressors are no longer the dividing line: `bq-ml/models/arima_plus_xreg` (`ARIMA_PLUS_XREG`) and TimesFM 3.0's covariates (section 9 below) both take them. Use `AI.FORECAST` for a fast, no-training baseline — with 3.0, a covariate-aware one; reach for `ARIMA_PLUS` when you need that level of control and explanation.
- `bq-ml/functions/time_series` (`ML.TREND` / `ML.SEASONALITY` / `ML.DETECT_CHANGE_POINTS`) — model-free decomposition rather than forecasting: trend, seasonal components, and sustained structural change points, with no `CREATE MODEL` and no foundation model. Reach for these when the question is *what has this series been doing* rather than *what will it do next*.
- `bq-ml/workflows/causal_effect` (`AI.CAUSAL_EFFECT`) — **the same forecasting idea aimed backwards.** It is not TimesFM: it wraps `ARIMA_PLUS`, and the sibling notebook reproduces its counterfactual bit-for-bit with a plain `CREATE MODEL ... ARIMA_PLUS`. Instead of forecasting past the end of the data, it forecasts past a point *inside* the data — the intervention date — and reports how far the observed values ran from that counterfactual. Reach for it when the question is *what would have happened without the change*, and for `AI.FORECAST` when the question is *what happens next*.

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

Control prediction interval width with `confidence_level`, and pin the model version with `model`.

**The default is TimesFM 2.5.** The other accepted value is `'TimesFM 3.0'` (Preview) — section 8 covers what it adds. Pin `model` whenever the numbers have to be reproducible: an unpinned call follows the default, and the default moves when Google advances it.

```python
query = f'''
SELECT *
FROM AI.FORECAST(
  TABLE `{PROJECT_ID}.{DATASET_ID}.ai_forecast_sales`,
  data_col => 'daily_sales',
  timestamp_col => 'date',
  horizon => 14,
  confidence_level => 0.99,
  model => 'TimesFM 2.5'
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

The `context_window` controls how many of the most recent historical points the model sees. The two model versions handle it differently:

- **TimesFM 2.5** (default): 64, 128, 256, 512, 1024, 2048, 4096, 8192 or 15360. When unspecified, the smallest window covering your data is auto-selected. Any other value is rejected.
- **TimesFM 3.0**: a multiple of 32 from 64 to 2048. When unspecified, the **maximum** (2048) is used, and points older than that are ignored. A value above 2048 is rejected; a value that is not a multiple of 32 is accepted rather than rejected, so stay on the documented grid if you want to know what the model saw.

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

### 8. TimesFM 3.0 (Preview): multivariate forecasting with `target_cols`

TimesFM 3.0 is selected with `model => 'TimesFM 3.0'`. On a single series it is a drop-in alternative to 2.5 with the same output columns, and a shorter reach: `horizon` is capped at 1,024 and the context window at 2,048 points.

What it adds is **multivariate forecasting**: pass `target_cols` (an array of column names) instead of `data_col`, and the model forecasts the series jointly. This syntax requires `model => 'TimesFM 3.0'` — with any other model, or with no `model` at all, the call fails with the generic `Invalid table-valued function AI.FORECAST`.

The output is restructured for multiple targets:
- the timestamp column **keeps its input name** (`date` here, not `forecast_timestamp`) and comes back as a `TIMESTAMP`
- each target becomes a `STRUCT<value, prediction_interval_lower_bound, prediction_interval_upper_bound>` under its own name
- `time_series_type` (`forecast`, or `history` when `output_historical_time_series => TRUE`), `confidence_level` and `ai_forecast_status` complete the row

`forecast_end_timestamp` is accepted in this form too, although the documented multivariate syntax lists only `horizon`.

First, a second table with two related daily series — sales and web visits — plus two columns that will serve as covariates in section 9. It covers 2024 as history and includes **14 future dates with the targets left NULL**; section 9 explains why.

```python
# Two related daily series (sales, web visits) plus two covariates (promo flag, weekend flag).
# History: 2024. Future: 14 days with the targets NULL and the future covariates populated.
query = f'''
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.ai_forecast_sales_mv` AS
WITH days AS (
  SELECT date,
    EXTRACT(DAYOFWEEK FROM date) AS dow,
    DATE_DIFF(date, DATE '2024-01-01', DAY) AS t
  FROM UNNEST(GENERATE_DATE_ARRAY('2024-01-01', '2025-01-14')) AS date
)
SELECT
  date,
  IF(date <= '2024-12-31', GREATEST(0,
    1000 + t * 2
    + CASE dow WHEN 1 THEN -200 WHEN 7 THEN 300 WHEN 6 THEN 200 ELSE 0 END
    + IF(MOD(t + 20, 30) < 3, 400, 0)            -- promotion lift
    + CAST(200 * (RAND() - 0.5) AS INT64)), NULL) AS daily_sales,
  IF(date <= '2024-12-31', GREATEST(0,
    5000 + t * 5
    + CASE dow WHEN 1 THEN -800 WHEN 7 THEN 1200 WHEN 6 THEN 800 ELSE 0 END
    + CAST(600 * (RAND() - 0.5) AS INT64)), NULL) AS web_visits,
  IF(MOD(t + 20, 30) < 3, 1, 0) AS promo_flag,   -- known in advance: the promotion calendar
  IF(dow IN (1, 7), 1, 0) AS is_weekend          -- known in advance: the calendar
FROM days
'''
client.query(query).result()

# The seam between history and future: targets stop, future covariates continue
df = client.query(f'''
SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.ai_forecast_sales_mv`
WHERE date BETWEEN '2024-12-29' AND '2025-01-03' ORDER BY date''').to_dataframe()
df
```

Forecast both series jointly from the history rows. Each target comes back as its own `STRUCT`; the query below flattens the fields it wants.

```python
query = f'''
SELECT
  date,
  ROUND(daily_sales.value) AS sales_forecast,
  ROUND(daily_sales.prediction_interval_lower_bound) AS sales_lower,
  ROUND(daily_sales.prediction_interval_upper_bound) AS sales_upper,
  ROUND(web_visits.value) AS visits_forecast,
  time_series_type,
  ai_forecast_status
FROM AI.FORECAST(
  (SELECT date, daily_sales, web_visits
   FROM `{PROJECT_ID}.{DATASET_ID}.ai_forecast_sales_mv`
   WHERE date <= '2024-12-31'),
  target_cols => ['daily_sales', 'web_visits'],
  timestamp_col => 'date',
  model => 'TimesFM 3.0',
  horizon => 7
)
ORDER BY date
'''
client.query(query).to_dataframe()
```

### 9. Past and future covariates

Covariates are extra columns the model may use to shape the forecast. TimesFM 3.0 distinguishes two kinds by *when they are known*:

- **`past_covariate_cols`** — known only historically. Web visits influence sales, but tomorrow's visits are not known today: populated for history rows, NULL for the future rows.
- **`future_covariate_cols`** — known for the past *and* the future. The promotion calendar and the day of the week are fixed in advance: populated on every row, including the 14 future dates.

That is why the input table carries future rows with NULL targets: the future covariates have to be supplied for every timestamp you want forecast. Covariates require the `target_cols` form — `data_col` plus a covariate argument is rejected. Three things measured here that the syntax does not say:

- `horizon` is **capped by the future rows you supply** — ask for 30 with 14 future rows and you get 14, silently.
- Without `horizon`, the default of 10 applies even when more future rows are available.
- A past covariate alone, with no future rows at all, also works — it simply conditions the forecast on the history.

```python
query = f'''
WITH forecast AS (
  SELECT
    date,
    ROUND(daily_sales.value) AS sales_forecast,
    ROUND(daily_sales.prediction_interval_lower_bound) AS lower,
    ROUND(daily_sales.prediction_interval_upper_bound) AS upper
  FROM AI.FORECAST(
    TABLE `{PROJECT_ID}.{DATASET_ID}.ai_forecast_sales_mv`,
    target_cols => ['daily_sales'],
    timestamp_col => 'date',
    model => 'TimesFM 3.0',
    horizon => 14,
    past_covariate_cols => ['web_visits'],
    future_covariate_cols => ['promo_flag', 'is_weekend']
  )
)
SELECT f.date, f.sales_forecast, f.lower, f.upper, c.promo_flag, c.is_weekend
FROM forecast f
JOIN `{PROJECT_ID}.{DATASET_ID}.ai_forecast_sales_mv` c ON DATE(f.date) = c.date
ORDER BY f.date
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

BigFrames wraps `AI.FORECAST` via `bbq.ai.forecast()`. No model object needed. Pass `model` explicitly: the wrapper's own default is `'TimesFM 2.0'`, a version the SQL reference page no longer lists, so an unpinned wrapper call and an unpinned SQL call run different models.

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
    horizon=14,
    model='TimesFM 2.5'
)
forecast.to_pandas()
```
