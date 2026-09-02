# AI.EVALUATE — BigQuery AI Functions

`AI.EVALUATE` is a table-valued function with two branches. Given `data_col` and `timestamp_col`, it evaluates a **TimesFM forecast** against actual observed values and returns MAE, MSE, RMSE, MAPE, sMAPE, and MASE. Given `label_col`, it evaluates **TabFM tabular predictions** against ground-truth labels — from the same training and prediction relations `AI.PREDICT` takes — and returns regression or classification metrics depending on the label column's type.

**When to use it:**
- You want to measure how accurate a forecast is before deploying it
- You need standard forecasting metrics (MAE, RMSE, MAPE, MASE, etc.)
- You want to compare different model configurations or context windows
- You can control how much history the model sees with `context_window` (64–15,360 depending on model)
- You want to score a zero-shot TabFM regression or classification setup before rolling it out

**Alternatives:**
- `functions/ai_forecast` (`AI.FORECAST`) — Generate forecasts (no evaluation)
- `functions/ai_detect_anomalies` (`AI.DETECT_ANOMALIES`) — Detect anomalies instead of evaluating accuracy
- `functions/ai_predict` (`AI.PREDICT`) — Generate the TabFM predictions themselves; `AI.EVALUATE` returns aggregate metrics only, never per-row predictions

**Launch stage:** the TimesFM branch is GA. The TabFM branch is Preview per the 2026-08-31 BigQuery release note, though the reference page carries no Preview banner.

**Featured in:** `workflows/time_series_intelligence` (Time Series Intelligence) | `workflows/tabular_prediction` (Zero-Shot Tabular Prediction)

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

### Two syntaxes, one function

The arguments you pass select the branch:

| Arguments | Branch | What gets evaluated |
|---|---|---|
| `data_col` + `timestamp_col` | **TimesFM** | a forecast generated from the history relation, scored against the actuals relation |
| `label_col` | **TabFM** | tabular predictions scored against ground-truth labels, from the same two relations `AI.PREDICT` takes |

The branches are mutually exclusive. Supplying arguments from both raises `AI.EVALUATE expects either timestamp_col and data_col to be provided for TimesFM forecasting tasks, or label_col for tabular classification/regression tasks.`

Examples 1–4 use the TimesFM branch; examples 5–6 use the TabFM branch. Neither branch needs a connection, a `CREATE MODEL`, or an endpoint.

### Setup: Split data into history and actuals

For the TimesFM branch, `AI.EVALUATE` needs two inputs:
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

Every TimesFM example in this notebook pins `model => 'TimesFM 2.5'`. The argument is optional, and the default is TimesFM 2.5 today — it was TimesFM 2.0 and moved with no release note. An unpinned call therefore evaluates whatever version is current, so any metric you record from one can shift without your query changing. Pin the version whenever the number matters.

```python
query = f'''
SELECT *
FROM AI.EVALUATE(
  (SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.ai_evaluate_full` WHERE date < '2024-11-01'),
  (SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.ai_evaluate_full` WHERE date >= '2024-11-01'),
  data_col => 'daily_sales',
  timestamp_col => 'date',
  model => 'TimesFM 2.5'
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
  horizon => 14,  -- evaluate only first 14 days
  model => 'TimesFM 2.5'
)
'''
client.query(query).to_dataframe()
```

### 3. Comparing TimesFM model versions

Evaluate the same data with different TimesFM versions. The newer version is not automatically the more accurate one on a given series, and the base table here is `RAND()`-generated, so the gap and even its direction move between runs — the cell computes and prints which version wins rather than stating it.

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

comparison = pd.concat([df_20, df_25]).reset_index(drop=True)
best = comparison.loc[comparison['mae'].idxmin()]
other = comparison.loc[comparison['mae'].idxmax()]
gap = (other['mae'] - best['mae']) / other['mae']
print(f"Lower MAE on this series: {best['model']} "
      f"({best['mae']} vs {other['mae']} — {gap:.1%} lower)")
comparison
```

### 4. Setting the context window

The `context_window` controls how many historical time points the model uses. Compare evaluation metrics across different context sizes to find the best fit for your data.

Supported values:
- **TimesFM 2.0:** 64, 128, 256, 512, 1024, 2048
- **TimesFM 2.5:** 64, 128, 256, 512, 1024, 2048, 4096, 8192, 15360

The legal set depends on the model, so `context_window` and `model` belong together — the sweep below pins `model => 'TimesFM 2.5'`. The four windows it uses are legal on both versions, but the three largest windows are 2.5-only: `context_window => 4096` with `model => 'TimesFM 2.0'` is rejected before the query runs, with `context_window of AI.EVALUATE is expected to be a Int64 literal with value in {64, 128, 256, 512, 1024, 2048} for model TimesFM 2.0`. A window larger than the history you pass in is not an error — the model simply sees all of it, and the metrics stop changing once the window covers the whole relation.

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
      horizon => 30, context_window => {cw}, model => 'TimesFM 2.5'
    )
    '''
    results.append(client.query(query).to_dataframe())

pd.concat(results).reset_index(drop=True)
```

### 5. TabFM: evaluating a regression prediction

Passing `label_col` instead of `data_col` and `timestamp_col` switches to the TabFM branch. The two positional relations become a **training** relation and a **prediction** relation — exactly the pair `AI.PREDICT` takes — and TabFM learns the task in-context, with no `CREATE MODEL` and no connection.

The label column's type picks the task. `body_mass_g` is `FLOAT64`, so this is regression and six metrics come back: `mean_absolute_error`, `mean_squared_error`, `mean_squared_log_error`, `median_absolute_error`, `r2_score`, and `explained_variance`.

- `label_col` is **required** on `AI.EVALUATE`, while `AI.PREDICT` defaults it to `'label'` — the same call that works there fails here if you drop it
- The prediction relation must carry the ground-truth label column; that is what the metrics are computed against
- Hand this identical relation pair and the identical `label_col` to `AI.PREDICT` and these metrics describe that run
- The split uses `FARM_FINGERPRINT`, not `RAND()`, so the same rows land in the same partition on every run — 239 training rows and 94 held-out rows
- Keep the training relation small: TabFM re-reads it on every call, and a 10,000-row training relation fails with `Resources exceeded during query execution` on on-demand slots, while a few thousand rows run in about a minute (verified 2026-09-01 against `AI.PREDICT`, which takes the same inputs and runs the same model)

```python
query = """
WITH penguins AS (
  SELECT
    species, island, culmen_length_mm, culmen_depth_mm, flipper_length_mm, sex, body_mass_g,
    IF(ABS(MOD(FARM_FINGERPRINT(FORMAT('%t', t)), 10)) < 7, 'TRAIN', 'TEST') AS split
  FROM `bigquery-public-data.ml_datasets.penguins` AS t
  WHERE body_mass_g IS NOT NULL AND sex IN ('MALE', 'FEMALE')
)
SELECT *
FROM AI.EVALUATE(
  (SELECT * EXCEPT(split) FROM penguins WHERE split = 'TRAIN'),
  (SELECT * EXCEPT(split) FROM penguins WHERE split = 'TEST'),
  label_col => 'body_mass_g'
)
"""
df = client.query(query).to_dataframe()
print(f'Metrics returned: {list(df.columns)}')
df
```

### 6. TabFM: evaluating a classification prediction

Same two relations, same call — only `label_col` changes. `sex` is a `STRING`, so TabFM evaluates classification and returns four metrics instead of six.

`precision`, `recall`, and `f1_score` are **macro-averaged across classes**: the metric is computed per class and then averaged with equal weight, so a rare class counts exactly as much as a common one. `accuracy` is the plain fraction of correct predictions across all rows. There is no `log_loss` and no `roc_auc` here — `ML.EVALUATE` on a trained classification model returns those two, the TabFM branch does not.

**Limits:** at most 20 feature columns and at most 10 classes. Both are documented on the `AI.PREDICT` reference page and are not restated on the `AI.EVALUATE` page, but the TabFM branch runs the same model on the same inputs. Penguins has 6 feature columns, and `sex` has 2 classes.

```python
query = """
WITH penguins AS (
  SELECT
    species, island, culmen_length_mm, culmen_depth_mm, flipper_length_mm, sex, body_mass_g,
    IF(ABS(MOD(FARM_FINGERPRINT(FORMAT('%t', t)), 10)) < 7, 'TRAIN', 'TEST') AS split
  FROM `bigquery-public-data.ml_datasets.penguins` AS t
  WHERE body_mass_g IS NOT NULL AND sex IN ('MALE', 'FEMALE')
)
SELECT *
FROM AI.EVALUATE(
  (SELECT * EXCEPT(split) FROM penguins WHERE split = 'TRAIN'),
  (SELECT * EXCEPT(split) FROM penguins WHERE split = 'TEST'),
  label_col => 'sex'
)
"""
df = client.query(query).to_dataframe()
print(f'Metrics returned: {list(df.columns)}')
df
```

### Two branches, two output shapes

| | TimesFM branch | TabFM branch |
|---|---|---|
| Selected by | `data_col` + `timestamp_col` | `label_col` |
| Rows returned | one per `id_cols` combination, one when `id_cols` is omitted | always one |
| Numeric metrics | `mean_absolute_error`, `mean_squared_error`, `root_mean_squared_error`, `mean_absolute_percentage_error`, `symmetric_mean_absolute_percentage_error`, `mean_absolute_scaled_error` | `mean_absolute_error`, `mean_squared_error`, `mean_squared_log_error`, `median_absolute_error`, `r2_score`, `explained_variance` |
| Categorical metrics | — | `precision`, `recall`, `accuracy`, `f1_score` |
| Status column | `ai_evaluate_status` — NULL on success | none |

Only the TimesFM branch returns `ai_evaluate_status`. On success it is **NULL**, not an empty string; on failure it carries the error string for that series, such as `The time series data is too short.` for a series with fewer than 3 data points. Per-series failures are therefore reported in the output rather than failing the query.

Select the failures with `WHERE ai_evaluate_status IS NOT NULL`. `= ''` matches nothing and `<> ''` silently drops every successful series, because a comparison against NULL evaluates to NULL rather than TRUE. The sibling functions are not consistent here: `ai_forecast_status` comes back as a zero-length empty string on success, so a predicate written for one function does not port to the other.

The TabFM branch has no status column at all: the query either returns its single row of metrics or fails outright. The two branches also share only two metric names (`mean_absolute_error` and `mean_squared_error`), so a query written against one branch's output cannot be pointed at the other.

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
  horizon => 30,
  model => 'TimesFM 2.5'
)
```

---
## Examples — BigFrames

`AI.EVALUATE` has no direct BigFrames equivalent — neither branch is wrapped, and there is no `bbq.ai.predict` either. Use `session.read_gbq_query()` to execute the SQL from BigFrames. The same query text works for the TabFM branch.

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
  horizon => 30,
  model => 'TimesFM 2.5'
)
"""
df = bpd.read_gbq_query(query)
df.to_pandas()
```
