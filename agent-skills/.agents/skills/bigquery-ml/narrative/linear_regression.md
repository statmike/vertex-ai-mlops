# Linear Regression — BigQuery ML

Train a **regression** model entirely in SQL with `CREATE MODEL`, then walk the full model lifecycle: evaluate, predict, explain, inspect coefficients, apply in-model preprocessing, and tune hyperparameters. No data leaves BigQuery, and no separate training infrastructure is needed.

**Lifecycle:** `CREATE MODEL` → `ML.EVALUATE` → `ML.PREDICT` → `ML.EXPLAIN_PREDICT` → `ML.GLOBAL_EXPLAIN` → `ML.WEIGHTS` → `ML.FEATURE_INFO` / `ML.TRAINING_INFO` → `TRANSFORM` clause → hyperparameter tuning (`ML.TRIAL_INFO`)

**When to use linear regression:**
- Predicting a continuous numeric value (price, weight, demand) from features
- A fast, explainable baseline before trying boosted trees or DNNs
- You want directly interpretable coefficients (`ML.WEIGHTS`) plus per-prediction and global feature attributions
- The workhorse behind regression-based forecasting (lagged-feature design matrices)

**Data:** [`bigquery-public-data.ml_datasets.penguins`](https://console.cloud.google.com/marketplace/product/bigquery-public-datasets) — predict a penguin's `body_mass_g` from species, island, and bill/flipper measurements. Rows with a NULL label or an unrecorded `sex` are filtered out.

**Featured in:** `workflows/regression_based_forecasting` (Regression-Based Forecasting) — time/lag/lead feature engineering applied to `LINEAR_REG` for demand forecasting.

**References:** `RESOURCES.md` (Full reference) | [CREATE MODEL (GLM) docs](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-glm) | `setup` (Setup guide)

---
## Setup

Set your project and location, authenticate, and create a shared dataset for the model.

> Linear regression trains on data already in BigQuery — no connection or remote model required. The model is created with `CREATE MODEL` and stored in your dataset. See the `setup` (Setup Reference) for details.

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

---
## Step 1 — Create the model with `CREATE MODEL`

`CREATE MODEL` trains and stores the model in your dataset. The essentials are `model_type` and `input_label_cols`. We also:
- `data_split_method = 'AUTO_SPLIT'` — automatically hold out rows for evaluation
- `category_encoding_method = 'DUMMY_ENCODING'` — drop one baseline category per categorical feature instead of one-hot-encoding all of them. This matters for `ML.WEIGHTS` in Step 5: with the default `ONE_HOT_ENCODING`, categorical dummies plus the intercept are collinear, so individual `category_weights` are **not uniquely identified** — re-running `CREATE MODEL` with a different random split can swing a category's weight by thousands of grams, even though predictions stay stable. `DUMMY_ENCODING` fixes this.
- `enable_global_explain = TRUE` — **required** to use `ML.GLOBAL_EXPLAIN` later

Training runs synchronously — the cell completes when the model is ready.

> For a small, unregularized problem like this one, BigQuery ML auto-selects the `NORMAL_EQUATION` solver (a single closed-form pass) instead of iterative gradient descent — see the `ML.TRAINING_INFO` note in Step 6.

```python
query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.linear_regression_penguins`
OPTIONS(
  model_type = 'LINEAR_REG',
  input_label_cols = ['body_mass_g'],
  data_split_method = 'AUTO_SPLIT',
  category_encoding_method = 'DUMMY_ENCODING',
  enable_global_explain = TRUE
) AS
SELECT
  species, island, culmen_length_mm, culmen_depth_mm, flipper_length_mm, sex, body_mass_g
FROM `bigquery-public-data.ml_datasets.penguins`
WHERE body_mass_g IS NOT NULL AND sex IN ('MALE', 'FEMALE')
"""
client.query(query).result()
print('Model linear_regression_penguins created')
```

---
## Step 2 — Evaluate with `ML.EVALUATE`

`ML.EVALUATE` returns standard regression metrics on the automatically held-out evaluation split: mean absolute error, mean squared error, R², and explained variance.

```python
query = f"""
SELECT *
FROM ML.EVALUATE(MODEL `{PROJECT_ID}.{DATASET_ID}.linear_regression_penguins`)
"""
client.query(query).to_dataframe()
```

---
## Step 3 — Predict with `ML.PREDICT`

`ML.PREDICT` scores new rows. It returns `predicted_body_mass_g` — a single continuous value, no probability array like a classifier. You pass any query with the same feature columns.

```python
query = f"""
SELECT
  predicted_body_mass_g,
  species,
  flipper_length_mm
FROM ML.PREDICT(
  MODEL `{PROJECT_ID}.{DATASET_ID}.linear_regression_penguins`,
  (SELECT * FROM `bigquery-public-data.ml_datasets.penguins`
   WHERE body_mass_g IS NOT NULL AND sex IN ('MALE', 'FEMALE') LIMIT 10)
)
"""
client.query(query).to_dataframe()
```

---
## Step 4 — Explain predictions

BigQuery ML provides explainability out of the box:
- **`ML.EXPLAIN_PREDICT`** — per-row feature attributions (which features pushed *this* prediction up or down)
- **`ML.GLOBAL_EXPLAIN`** — overall feature importance across the model (requires `enable_global_explain = TRUE`)

```python
query = f"""
SELECT
  predicted_body_mass_g,
  top_feature_attributions
FROM ML.EXPLAIN_PREDICT(
  MODEL `{PROJECT_ID}.{DATASET_ID}.linear_regression_penguins`,
  (SELECT * FROM `bigquery-public-data.ml_datasets.penguins`
   WHERE body_mass_g IS NOT NULL AND sex IN ('MALE', 'FEMALE') LIMIT 5),
  STRUCT(5 AS top_k_features)
)
"""
client.query(query).to_dataframe()
```

```python
query = f"""
SELECT *
FROM ML.GLOBAL_EXPLAIN(MODEL `{PROJECT_ID}.{DATASET_ID}.linear_regression_penguins`)
ORDER BY attribution DESC
"""
client.query(query).to_dataframe()
```

---
## Step 5 — Inspect coefficients with `ML.WEIGHTS`

Unlike a classifier, a `LINEAR_REG` model's weights are directly interpretable in the label's own units — e.g. "each additional mm of flipper length adds N grams of predicted body mass." Numeric features get a single `weight`; categorical features (like `species`, `island`, `sex`) expand into a `category_weights` array. Because the model was trained with `category_encoding_method = 'DUMMY_ENCODING'`, one category per feature is the pinned baseline (`weight: 0.0`) and every other category's weight is a stable, well-defined delta from it. This function only applies to `LINEAR_REG` / `LOGISTIC_REG` / `MATRIX_FACTORIZATION` models.

```python
query = f"""
SELECT *
FROM ML.WEIGHTS(MODEL `{PROJECT_ID}.{DATASET_ID}.linear_regression_penguins`)
"""
client.query(query).to_dataframe()
```

---
## Step 6 — Introspect the model

`ML.FEATURE_INFO` reports the statistics each feature had during training. `ML.TRAINING_INFO` returns the per-iteration loss curve — for this model, BigQuery ML auto-selects the `NORMAL_EQUATION` solver, which trains in a single closed-form pass, so expect exactly one row with no `eval_loss`.

```python
query = f"""
SELECT *
FROM ML.FEATURE_INFO(MODEL `{PROJECT_ID}.{DATASET_ID}.linear_regression_penguins`)
"""
client.query(query).to_dataframe()
```

```python
query = f"""
SELECT iteration, loss, eval_loss, learning_rate, duration_ms
FROM ML.TRAINING_INFO(MODEL `{PROJECT_ID}.{DATASET_ID}.linear_regression_penguins`)
ORDER BY iteration
"""
client.query(query).to_dataframe()
```

---
## Step 7 — In-model preprocessing with the `TRANSFORM` clause

The `TRANSFORM` clause bakes preprocessing into the model. Whatever you do in `TRANSFORM` (scaling, bucketizing, feature crosses) is **saved with the model and reapplied automatically at predict time** — so `ML.PREDICT` takes raw data, with no need to repeat the preprocessing.

Here we standard-scale the numeric bill/flipper measurements. Notice the prediction query passes raw, unscaled rows.

```python
query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.linear_regression_penguins_transform`
TRANSFORM(
  ML.STANDARD_SCALER(culmen_length_mm) OVER() AS culmen_length_mm,
  ML.STANDARD_SCALER(flipper_length_mm) OVER() AS flipper_length_mm,
  species, island, sex, body_mass_g
)
OPTIONS(
  model_type = 'LINEAR_REG',
  input_label_cols = ['body_mass_g']
) AS
SELECT species, island, culmen_length_mm, flipper_length_mm, sex, body_mass_g
FROM `bigquery-public-data.ml_datasets.penguins`
WHERE body_mass_g IS NOT NULL AND sex IN ('MALE', 'FEMALE')
"""
client.query(query).result()
print('Model linear_regression_penguins_transform created')
```

```python
# Predict on RAW rows - scaling is applied automatically inside the model
query = f"""
SELECT predicted_body_mass_g, culmen_length_mm, flipper_length_mm
FROM ML.PREDICT(
  MODEL `{PROJECT_ID}.{DATASET_ID}.linear_regression_penguins_transform`,
  (SELECT * FROM `bigquery-public-data.ml_datasets.penguins`
   WHERE body_mass_g IS NOT NULL AND sex IN ('MALE', 'FEMALE') LIMIT 5)
)
"""
client.query(query).to_dataframe()
```

---
## Step 8 — Hyperparameter tuning

BigQuery ML has built-in hyperparameter tuning. Set `num_trials` and define a search space with `HPARAM_RANGE` / `HPARAM_CANDIDATES`; BigQuery runs the trials and keeps the best model by `hparam_tuning_objectives`. Inspect every trial with `ML.TRIAL_INFO`.

Training multiple trials takes a few minutes.

```python
query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.linear_regression_penguins_tuned`
OPTIONS(
  model_type = 'LINEAR_REG',
  input_label_cols = ['body_mass_g'],
  num_trials = 10,
  max_parallel_trials = 2,
  hparam_tuning_objectives = ['r2_score'],
  l1_reg = HPARAM_RANGE(0, 10),
  l2_reg = HPARAM_RANGE(0, 10)
) AS
SELECT
  species, island, culmen_length_mm, culmen_depth_mm, flipper_length_mm, sex, body_mass_g
FROM `bigquery-public-data.ml_datasets.penguins`
WHERE body_mass_g IS NOT NULL AND sex IN ('MALE', 'FEMALE')
"""
client.query(query).result()
print('Tuned model created')
```

```python
query = f"""
SELECT
  trial_id,
  hyperparameters,
  hparam_tuning_evaluation_metrics.r2_score AS r2_score,
  is_optimal
FROM ML.TRIAL_INFO(MODEL `{PROJECT_ID}.{DATASET_ID}.linear_regression_penguins_tuned`)
ORDER BY r2_score DESC
"""
client.query(query).to_dataframe()
```

---
## Examples — `%%bigquery` Magics

The same operations using IPython magic commands — write SQL directly in cells without Python string wrapping.

- `%%bigquery` — run SQL, display results inline
- `%%bigquery df` — run SQL, capture results into a pandas DataFrame

### Evaluate with `%%bigquery`

```sql
%%bigquery --project {PROJECT_ID}

SELECT *
FROM ML.EVALUATE(MODEL `statmike-mlops-349915.bq_ml.linear_regression_penguins`)
```

---
## Examples — BigFrames

BigFrames provides a scikit-learn-style API (`bigframes.ml`) that trains BigQuery ML models under the hood. Here's the same linear regression with `bigframes.ml.linear_model.LinearRegression`.

```python
import bigframes.pandas as bpd

bpd.close_session()  # Reset session to apply project/location settings
bpd.options.bigquery.project = PROJECT_ID
bpd.options.bigquery.location = LOCATION
```

```python
from bigframes.ml.linear_model import LinearRegression

# Load data as a BigFrames DataFrame
df = bpd.read_gbq('bigquery-public-data.ml_datasets.penguins')
df = df[df['body_mass_g'].notnull() & df['sex'].isin(['MALE', 'FEMALE'])]

feature_cols = ['species', 'island', 'culmen_length_mm', 'culmen_depth_mm', 'flipper_length_mm', 'sex']
X = df[feature_cols]
y = df['body_mass_g']

# Train (creates a BigQuery ML model behind the scenes)
model = LinearRegression()
model.fit(X, y)

# Evaluate
model.score(X, y).to_pandas()
```
