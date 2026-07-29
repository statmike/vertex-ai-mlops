# AI.DETECT_ANOMALIES — BigQuery AI Functions

`AI.DETECT_ANOMALIES` is a GA table-valued function that detects anomalies in time series data using TimesFM. It forecasts expected values from historical data, then flags data points that deviate significantly.

**When to use it:**
- You want to detect unusual spikes or drops in time series data
- You need anomaly probability scores for each data point
- You want to detect anomalies across multiple time series simultaneously
- You can choose between TimesFM 2.0 (default) and TimesFM 2.5 via the `model` parameter
- You can control how much history the model sees with `context_window` (64–15,360 depending on model)

**Alternatives:**
- `functions/ai_forecast` (`AI.FORECAST`) — Generate forecasts without anomaly detection
- `functions/ai_evaluate` (`AI.EVALUATE`) — Evaluate forecast accuracy instead of detecting anomalies

**Featured in:** `workflows/time_series_intelligence` (Time Series Intelligence)

**References:** `RESOURCES.md` (Full syntax reference) | [Official documentation](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-detect-anomalies) | `setup` (Setup guide)

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

### Setup: Create historical and target data

Anomaly detection needs two inputs:
1. **Historical data** — used to build a forecast baseline
2. **Target data** — checked for anomalies against the baseline

We create data with a realistic pattern (upward trend + weekly seasonality), then inject two clear anomalies into the target period: a spike on Dec 15 and a drop on Dec 25.

```python
# Create historical data (Jan-Nov 2024): upward trend + weekly seasonality + noise
query = f'''
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.ai_detect_anomalies_history` AS
WITH dates AS (
  SELECT date FROM UNNEST(GENERATE_DATE_ARRAY('2024-01-01', '2024-11-30')) AS date
)
SELECT date,
  GREATEST(0,
    1000
    + EXTRACT(DAYOFYEAR FROM date) * 2  -- upward trend (~2/day)
    + CASE EXTRACT(DAYOFWEEK FROM date)
        WHEN 1 THEN -200  -- Sunday dip
        WHEN 7 THEN 300   -- Saturday peak
        ELSE 0
      END
    + CAST(100 * (RAND() - 0.5) AS INT64)  -- noise
  ) AS daily_sales
FROM dates
'''
client.query(query).result()

# Create target data (Dec 2024): same pattern but with 2 injected anomalies
# IMPORTANT: target must follow the same pattern as history, otherwise
# the model flags every deviation from the learned seasonality.
query = f'''
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.ai_detect_anomalies_target` AS
WITH dates AS (
  SELECT date FROM UNNEST(GENERATE_DATE_ARRAY('2024-12-01', '2024-12-31')) AS date
)
SELECT date,
  CASE
    WHEN date = '2024-12-15' THEN 5000  -- injected spike anomaly (Sunday)
    WHEN date = '2024-12-25' THEN 50    -- injected drop anomaly (Wednesday)
    ELSE GREATEST(0,
      1000
      + EXTRACT(DAYOFYEAR FROM date) * 2  -- same trend
      + CASE EXTRACT(DAYOFWEEK FROM date)
          WHEN 1 THEN -200  -- same weekly seasonality
          WHEN 7 THEN 300
          ELSE 0
        END
      + CAST(100 * (RAND() - 0.5) AS INT64)  -- same noise
    )
  END AS daily_sales
FROM dates
'''
client.query(query).result()
print('Historical and target data created')
```

### 1. Basic anomaly detection

Pass historical and target tables. Returns each target point with `is_anomaly`, bounds, and probability.

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
  TABLE `{PROJECT_ID}.{DATASET_ID}.ai_detect_anomalies_history`,
  TABLE `{PROJECT_ID}.{DATASET_ID}.ai_detect_anomalies_target`,
  data_col => 'daily_sales',
  timestamp_col => 'date'
)
ORDER BY time_series_timestamp
'''
df = client.query(query).to_dataframe()

anomalies = df[df['is_anomaly'] == True]
print(f'Total points: {len(df)}, Anomalies detected: {len(anomalies)}')
print(f'\nAnomalous points:')
print(anomalies[['time_series_timestamp', 'time_series_data', 'anomaly_prob', 'lower_bound', 'upper_bound']].to_string(index=False))
```

### 2. Adjusting the anomaly threshold

The `anomaly_prob_threshold` controls sensitivity (default: 0.95). A data point is flagged as anomalous if its anomaly probability exceeds this threshold.

- **Higher threshold** (e.g., 0.99) → fewer, more extreme anomalies only
- **Lower threshold** (e.g., 0.8) → more anomalies, catches subtler deviations

Here we show all points sorted by anomaly probability to see the full distribution.

```python
query = f'''
SELECT
  time_series_timestamp,
  time_series_data,
  is_anomaly,
  ROUND(anomaly_probability, 4) AS anomaly_prob,
  ROUND(lower_bound, 0) AS lower,
  ROUND(upper_bound, 0) AS upper
FROM AI.DETECT_ANOMALIES(
  TABLE `{PROJECT_ID}.{DATASET_ID}.ai_detect_anomalies_history`,
  TABLE `{PROJECT_ID}.{DATASET_ID}.ai_detect_anomalies_target`,
  data_col => 'daily_sales',
  timestamp_col => 'date',
  anomaly_prob_threshold => 0.99  -- stricter: only the most extreme anomalies
)
ORDER BY anomaly_prob DESC
'''
df = client.query(query).to_dataframe()

anomalies = df[df['is_anomaly'] == True]
print(f'With threshold=0.99: {len(anomalies)} anomalies (vs default 0.95)')
df.head(10)
```

### 3. Using a query for history (subset)

Pass a query instead of a table reference to filter historical data.

```python
query = f'''
SELECT
  time_series_timestamp,
  time_series_data,
  is_anomaly,
  ROUND(anomaly_probability, 4) AS anomaly_prob
FROM AI.DETECT_ANOMALIES(
  (SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.ai_detect_anomalies_history`
   WHERE date >= '2024-09-01'),  -- use only recent history
  TABLE `{PROJECT_ID}.{DATASET_ID}.ai_detect_anomalies_target`,
  data_col => 'daily_sales',
  timestamp_col => 'date'
)
WHERE is_anomaly = TRUE
ORDER BY anomaly_prob DESC
'''
client.query(query).to_dataframe()
```

### 4. Setting the context window

The `context_window` controls how many historical time points the model uses to learn patterns. Supported values depend on the model:
- **TimesFM 2.0:** 64, 128, 256, 512, 1024, 2048
- **TimesFM 2.5:** 64, 128, 256, 512, 1024, 2048, 4096, 8192, 15360

By default, the smallest window covering your input data is auto-selected. A larger window can capture longer-term patterns but uses more resources.

```python
query = f'''
SELECT
  time_series_timestamp,
  time_series_data,
  is_anomaly,
  ROUND(anomaly_probability, 4) AS anomaly_prob
FROM AI.DETECT_ANOMALIES(
  TABLE `{PROJECT_ID}.{DATASET_ID}.ai_detect_anomalies_history`,
  TABLE `{PROJECT_ID}.{DATASET_ID}.ai_detect_anomalies_target`,
  data_col => 'daily_sales',
  timestamp_col => 'date',
  context_window => 128
)
WHERE is_anomaly = TRUE
ORDER BY anomaly_prob DESC
'''
client.query(query).to_dataframe()
```

### 5. Using TimesFM 2.5

The `model` parameter selects which TimesFM version to use. TimesFM 2.5 supports larger context windows (up to 15,360) and may produce different anomaly probabilities.

```python
query = f'''
SELECT
  time_series_timestamp,
  time_series_data,
  is_anomaly,
  ROUND(anomaly_probability, 4) AS anomaly_prob
FROM AI.DETECT_ANOMALIES(
  TABLE `{PROJECT_ID}.{DATASET_ID}.ai_detect_anomalies_history`,
  TABLE `{PROJECT_ID}.{DATASET_ID}.ai_detect_anomalies_target`,
  data_col => 'daily_sales',
  timestamp_col => 'date',
  model => 'TimesFM 2.5'
)
WHERE is_anomaly = TRUE
ORDER BY anomaly_prob DESC
'''
client.query(query).to_dataframe()
```

---
## Examples — `%%bigquery` Magics

The same examples using IPython magic commands. Magics let you write SQL directly in notebook cells without Python string wrapping.

Key patterns:
- `%%bigquery` — run SQL, display results inline
- `%%bigquery df` — run SQL, capture results into a pandas DataFrame

### Anomaly detection with `%%bigquery`

```sql
%%bigquery --project {PROJECT_ID}

SELECT time_series_timestamp, time_series_data, is_anomaly,
  ROUND(anomaly_probability, 4) AS anomaly_prob
FROM AI.DETECT_ANOMALIES(
  TABLE `statmike-mlops-349915.bq_ai_functions.ai_detect_anomalies_history`,
  TABLE `statmike-mlops-349915.bq_ai_functions.ai_detect_anomalies_target`,
  data_col => 'daily_sales',
  timestamp_col => 'date'
)
WHERE is_anomaly = TRUE
ORDER BY anomaly_probability DESC
```

---
## Examples — BigFrames

`AI.DETECT_ANOMALIES` has no direct BigFrames equivalent for TimesFM. Use `session.read_gbq_query()` to execute the SQL from BigFrames.

**Note:** `bigframes.ml.forecasting.ARIMAPlus.detect_anomalies()` exists but uses ARIMA_PLUS, not TimesFM.

```python
import bigframes.pandas as bpd

bpd.options.bigquery.project = PROJECT_ID
bpd.options.bigquery.location = LOCATION
```

### Running AI.DETECT_ANOMALIES via read_gbq_query

```python
query = f"""
SELECT time_series_timestamp, time_series_data, is_anomaly, anomaly_probability
FROM AI.DETECT_ANOMALIES(
  TABLE `{PROJECT_ID}.{DATASET_ID}.ai_detect_anomalies_history`,
  TABLE `{PROJECT_ID}.{DATASET_ID}.ai_detect_anomalies_target`,
  data_col => 'daily_sales',
  timestamp_col => 'date'
)
ORDER BY time_series_timestamp
"""
df = bpd.read_gbq_query(query)
df.to_pandas()
```
