# AI.EVALUATE — BigQuery AI Functions

`AI.EVALUATE` is a table-valued function that evaluates TimesFM forecast accuracy by comparing forecasted values against actual observed data. Returns standard metrics: MAE, MSE, RMSE, MAPE, sMAPE, and MASE.

**When to use it:**
- You want to measure how accurate a forecast is before deploying it
- You need standard forecasting metrics (MAE, RMSE, MAPE, MASE, etc.)
- You want to compare different model configurations or context windows
- You can control how much history the model sees with `context_window` (64–15,360 depending on model)

**Alternatives:**
- `functions/ai_forecast` (`AI.FORECAST`) — Generate forecasts (no evaluation)
- `functions/ai_detect_anomalies` (`AI.DETECT_ANOMALIES`) — Detect anomalies instead of evaluating accuracy

**Featured in:** `workflows/time_series_intelligence` (Time Series Intelligence)

**References:** `RESOURCES.md` (Full syntax reference) | [Official documentation](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-evaluate) | `setup` (Setup guide)

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

### Setup: Split data into history and actuals

AI.EVALUATE needs two inputs:
1. **History** — used to generate a forecast
2. **Actuals** — the real values to compare the forecast against

We split existing time series data at a cutoff date.

```python
# Create full time series
query = f'''
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.ai_evaluate_full` AS
WITH dates AS (
  SELECT date FROM UNNEST(GENERATE_DATE_ARRAY('2024-01-01', '2024-12-31')) AS date
)
SELECT date,
  GREATEST(0, 1000 + EXTRACT(DAYOFYEAR FROM date) * 2
    + CASE EXTRACT(DAYOFWEEK FROM date) WHEN 1 THEN -200 WHEN 7 THEN 300 ELSE 0 END
    + CAST(100 * (RAND() - 0.5) AS INT64)
  ) AS daily_sales
FROM dates
'''
client.query(query).result()
print('Full time series created (365 days)')
```

### 1. Basic evaluation

Split at November 1 — use Jan-Oct as history, Nov-Dec as actuals.

```python
query = f'''
SELECT *
FROM AI.EVALUATE(
  (SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.ai_evaluate_full` WHERE date < '2024-11-01'),
  (SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.ai_evaluate_full` WHERE date >= '2024-11-01'),
  data_col => 'daily_sales',
  timestamp_col => 'date'
)
'''
df = client.query(query).to_dataframe()
for col in ['mean_absolute_error', 'root_mean_squared_error', 'mean_absolute_percentage_error']:
    print(f'{col}: {df.iloc[0][col]:.2f}')
df
```

### 2. Limiting the forecast horizon

Evaluate only the first N forecasted time steps.

```python
query = f'''
SELECT *
FROM AI.EVALUATE(
  (SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.ai_evaluate_full` WHERE date < '2024-11-01'),
  (SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.ai_evaluate_full` WHERE date >= '2024-11-01'),
  data_col => 'daily_sales',
  timestamp_col => 'date',
  horizon => 14  -- evaluate only first 14 days
)
'''
client.query(query).to_dataframe()
```

### 3. Comparing TimesFM model versions

Evaluate the same data with different TimesFM versions.

```python
# TimesFM 2.0
query_20 = f'''
SELECT 'TimesFM 2.0' AS model,
  ROUND(mean_absolute_error, 2) AS mae,
  ROUND(root_mean_squared_error, 2) AS rmse,
  ROUND(mean_absolute_percentage_error, 4) AS mape
FROM AI.EVALUATE(
  (SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.ai_evaluate_full` WHERE date < '2024-11-01'),
  (SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.ai_evaluate_full` WHERE date >= '2024-11-01'),
  data_col => 'daily_sales', timestamp_col => 'date',
  horizon => 30, model => 'TimesFM 2.0'
)
'''

# TimesFM 2.5
query_25 = f'''
SELECT 'TimesFM 2.5' AS model,
  ROUND(mean_absolute_error, 2) AS mae,
  ROUND(root_mean_squared_error, 2) AS rmse,
  ROUND(mean_absolute_percentage_error, 4) AS mape
FROM AI.EVALUATE(
  (SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.ai_evaluate_full` WHERE date < '2024-11-01'),
  (SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.ai_evaluate_full` WHERE date >= '2024-11-01'),
  data_col => 'daily_sales', timestamp_col => 'date',
  horizon => 30, model => 'TimesFM 2.5'
)
'''

df_20 = client.query(query_20).to_dataframe()
df_25 = client.query(query_25).to_dataframe()
import pandas as pd
pd.concat([df_20, df_25]).reset_index(drop=True)
```

### 4. Setting the context window

The `context_window` controls how many historical time points the model uses. Compare evaluation metrics across different context sizes to find the best fit for your data.

Supported values:
- **TimesFM 2.0:** 64, 128, 256, 512, 1024, 2048
- **TimesFM 2.5:** 64, 128, 256, 512, 1024, 2048, 4096, 8192, 15360

```python
import pandas as pd

results = []
for cw in [64, 128, 256, 512]:
    query = f'''
    SELECT {cw} AS context_window,
      ROUND(mean_absolute_error, 2) AS mae,
      ROUND(root_mean_squared_error, 2) AS rmse,
      ROUND(mean_absolute_percentage_error, 4) AS mape
    FROM AI.EVALUATE(
      (SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.ai_evaluate_full` WHERE date < '2024-11-01'),
      (SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.ai_evaluate_full` WHERE date >= '2024-11-01'),
      data_col => 'daily_sales', timestamp_col => 'date',
      horizon => 30, context_window => {cw}
    )
    '''
    results.append(client.query(query).to_dataframe())

pd.concat(results).reset_index(drop=True)
```

---
## Examples — `%%bigquery` Magics

The same examples using IPython magic commands. Magics let you write SQL directly in notebook cells without Python string wrapping.

Key patterns:
- `%%bigquery` — run SQL, display results inline
- `%%bigquery df` — run SQL, capture results into a pandas DataFrame

### Evaluation with `%%bigquery`

```sql
%%bigquery --project {PROJECT_ID}

SELECT
  ROUND(mean_absolute_error, 2) AS mae,
  ROUND(root_mean_squared_error, 2) AS rmse,
  ROUND(mean_absolute_percentage_error, 4) AS mape,
  ROUND(symmetric_mean_absolute_percentage_error, 4) AS smape
FROM AI.EVALUATE(
  (SELECT * FROM `statmike-mlops-349915.bq_ai_functions.ai_evaluate_full` WHERE date < '2024-11-01'),
  (SELECT * FROM `statmike-mlops-349915.bq_ai_functions.ai_evaluate_full` WHERE date >= '2024-11-01'),
  data_col => 'daily_sales',
  timestamp_col => 'date',
  horizon => 30
)
```

---
## Examples — BigFrames

`AI.EVALUATE` has no direct BigFrames equivalent for TimesFM. Use `session.read_gbq_query()` to execute the SQL from BigFrames.

**Note:** `bigframes.ml.forecasting.ARIMAPlus.evaluate()` exists but uses ARIMA_PLUS, not TimesFM.

```python
import bigframes.pandas as bpd

bpd.options.bigquery.project = PROJECT_ID
bpd.options.bigquery.location = LOCATION
```

### Running AI.EVALUATE via read_gbq_query

```python
query = f"""
SELECT *
FROM AI.EVALUATE(
  (SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.ai_evaluate_full` WHERE date < '2024-11-01'),
  (SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.ai_evaluate_full` WHERE date >= '2024-11-01'),
  data_col => 'daily_sales',
  timestamp_col => 'date',
  horizon => 30
)
"""
df = bpd.read_gbq_query(query)
df.to_pandas()
```
