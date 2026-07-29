# Logistic Regression — BigQuery ML

Train a **binary classification** model entirely in SQL with `CREATE MODEL`, then walk the full model lifecycle: evaluate, inspect, predict, and explain — plus hyperparameter tuning. No data leaves BigQuery, and no separate training infrastructure is needed.

**Lifecycle:** `CREATE MODEL` → `ML.EVALUATE` → `ML.CONFUSION_MATRIX` / `ML.ROC_CURVE` → `ML.PREDICT` → `ML.EXPLAIN_PREDICT` → `ML.GLOBAL_EXPLAIN` → `ML.FEATURE_INFO` / `ML.TRAINING_INFO` → hyperparameter tuning (`ML.TRIAL_INFO`)

**When to use logistic regression:**
- Binary (or multiclass) classification with interpretable feature weights
- A fast, explainable baseline before trying boosted trees or DNNs
- You want per-prediction and global feature attributions out of the box

**Data:** [`bigquery-public-data.ml_datasets.census_adult_income`](https://console.cloud.google.com/marketplace/product/bigquery-public-datasets) — predict whether income exceeds $50K/year from census attributes.

**References:** `RESOURCES.md` (Full reference) | [CREATE MODEL (GLM) docs](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-glm) | `setup` (Setup guide)

---
## Setup

Set your project and location, authenticate, and create a shared dataset for the model.

> Logistic regression trains on data already in BigQuery — no connection or remote model required. The model is created with `CREATE MODEL` and stored in your dataset. See the `setup` (Setup Reference) for details.

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
- `auto_class_weights = TRUE` — balance the classes (the data is ~76% `<=50K`)
- `data_split_method = 'AUTO_SPLIT'` — automatically hold out rows for evaluation
- `enable_global_explain = TRUE` — **required** to use `ML.GLOBAL_EXPLAIN` later

Training runs synchronously — the cell completes when the model is ready (about a minute).

```python
query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.logistic_regression_income`
OPTIONS(
  model_type = 'LOGISTIC_REG',
  input_label_cols = ['income_bracket'],
  auto_class_weights = TRUE,
  data_split_method = 'AUTO_SPLIT',
  enable_global_explain = TRUE
) AS
SELECT
  age, workclass, education, education_num, marital_status, occupation,
  relationship, race, sex, hours_per_week, native_country, income_bracket
FROM `bigquery-public-data.ml_datasets.census_adult_income`
"""
client.query(query).result()
print('Model logistic_regression_income created')
```

---
## Step 2 — Evaluate with `ML.EVALUATE`

`ML.EVALUATE` returns standard classification metrics on the automatically held-out evaluation split: precision, recall, accuracy, F1, log loss, and ROC AUC.

```python
query = f"""
SELECT *
FROM ML.EVALUATE(MODEL `{PROJECT_ID}.{DATASET_ID}.logistic_regression_income`)
"""
client.query(query).to_dataframe()
```

---
## Step 3 — Confusion matrix and ROC curve

`ML.CONFUSION_MATRIX` shows counts of predicted vs. actual classes. `ML.ROC_CURVE` returns the recall / false-positive-rate tradeoff across thresholds — useful for choosing an operating point.

```python
query = f"""
SELECT *
FROM ML.CONFUSION_MATRIX(MODEL `{PROJECT_ID}.{DATASET_ID}.logistic_regression_income`)
"""
client.query(query).to_dataframe()
```

```python
import matplotlib.pyplot as plt

query = f"""
SELECT threshold, recall, false_positive_rate
FROM ML.ROC_CURVE(MODEL `{PROJECT_ID}.{DATASET_ID}.logistic_regression_income`)
ORDER BY threshold
"""
roc = client.query(query).to_dataframe()

fig, ax = plt.subplots(figsize=(6, 6))
ax.plot(roc['false_positive_rate'], roc['recall'], color='#4285F4', linewidth=2, label='ROC curve')
ax.plot([0, 1], [0, 1], color='gray', linestyle='--', alpha=0.6, label='Random')
ax.set_xlabel('False Positive Rate')
ax.set_ylabel('True Positive Rate (Recall)')
ax.set_title('ROC Curve - Logistic Regression')
ax.legend(loc='lower right')
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()
```

---
## Step 4 — Predict with `ML.PREDICT`

`ML.PREDICT` scores new rows. It returns `predicted_income_bracket` (the chosen class) and `predicted_income_bracket_probs` (the probability of each class). You pass any query with the same feature columns.

```python
query = f"""
SELECT
  predicted_income_bracket,
  predicted_income_bracket_probs,
  age, occupation, education
FROM ML.PREDICT(
  MODEL `{PROJECT_ID}.{DATASET_ID}.logistic_regression_income`,
  (SELECT * FROM `bigquery-public-data.ml_datasets.census_adult_income` LIMIT 10)
)
"""
client.query(query).to_dataframe()
```

---
## Step 5 — Explain predictions

BigQuery ML provides explainability out of the box:
- **`ML.EXPLAIN_PREDICT`** — per-row feature attributions (which features pushed *this* prediction up or down)
- **`ML.GLOBAL_EXPLAIN`** — overall feature importance across the model (requires `enable_global_explain = TRUE`)

```python
query = f"""
SELECT
  predicted_income_bracket,
  top_feature_attributions
FROM ML.EXPLAIN_PREDICT(
  MODEL `{PROJECT_ID}.{DATASET_ID}.logistic_regression_income`,
  (SELECT * FROM `bigquery-public-data.ml_datasets.census_adult_income` LIMIT 5),
  STRUCT(5 AS top_k_features)
)
"""
client.query(query).to_dataframe()
```

```python
query = f"""
SELECT *
FROM ML.GLOBAL_EXPLAIN(MODEL `{PROJECT_ID}.{DATASET_ID}.logistic_regression_income`)
ORDER BY attribution DESC
"""
client.query(query).to_dataframe()
```

---
## Step 6 — Introspect the model

`ML.FEATURE_INFO` reports the statistics each feature had during training. `ML.TRAINING_INFO` returns the per-iteration loss curve, useful for confirming the model converged.

```python
query = f"""
SELECT *
FROM ML.FEATURE_INFO(MODEL `{PROJECT_ID}.{DATASET_ID}.logistic_regression_income`)
"""
client.query(query).to_dataframe()
```

```python
query = f"""
SELECT iteration, loss, eval_loss, learning_rate, duration_ms
FROM ML.TRAINING_INFO(MODEL `{PROJECT_ID}.{DATASET_ID}.logistic_regression_income`)
ORDER BY iteration
"""
client.query(query).to_dataframe()
```

---
## Step 7 — In-model preprocessing with the `TRANSFORM` clause

The `TRANSFORM` clause bakes preprocessing into the model. Whatever you do in `TRANSFORM` (scaling, bucketizing, feature crosses) is **saved with the model and reapplied automatically at predict time** — so `ML.PREDICT` takes raw data, with no need to repeat the preprocessing.

Here we standard-scale the numeric features. Notice the prediction query passes raw, unscaled rows.

```python
query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.logistic_regression_income_transform`
TRANSFORM(
  ML.STANDARD_SCALER(age) OVER() AS age,
  ML.STANDARD_SCALER(hours_per_week) OVER() AS hours_per_week,
  education, marital_status, occupation, relationship, income_bracket
)
OPTIONS(
  model_type = 'LOGISTIC_REG',
  input_label_cols = ['income_bracket'],
  auto_class_weights = TRUE
) AS
SELECT
  age, hours_per_week, education, marital_status, occupation,
  relationship, income_bracket
FROM `bigquery-public-data.ml_datasets.census_adult_income`
"""
client.query(query).result()
print('Model logistic_regression_income_transform created')
```

```python
# Predict on RAW rows - scaling is applied automatically inside the model
query = f"""
SELECT predicted_income_bracket, age, hours_per_week, occupation
FROM ML.PREDICT(
  MODEL `{PROJECT_ID}.{DATASET_ID}.logistic_regression_income_transform`,
  (SELECT * FROM `bigquery-public-data.ml_datasets.census_adult_income` LIMIT 5)
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
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.logistic_regression_income_tuned`
OPTIONS(
  model_type = 'LOGISTIC_REG',
  input_label_cols = ['income_bracket'],
  num_trials = 10,
  max_parallel_trials = 2,
  hparam_tuning_objectives = ['roc_auc'],
  l1_reg = HPARAM_RANGE(0, 1),
  l2_reg = HPARAM_RANGE(0, 1)
) AS
SELECT
  age, workclass, education, education_num, marital_status, occupation,
  relationship, race, sex, hours_per_week, native_country, income_bracket
FROM `bigquery-public-data.ml_datasets.census_adult_income`
"""
client.query(query).result()
print('Tuned model created')
```

```python
query = f"""
SELECT
  trial_id,
  hyperparameters,
  hparam_tuning_evaluation_metrics.roc_auc AS roc_auc,
  is_optimal
FROM ML.TRIAL_INFO(MODEL `{PROJECT_ID}.{DATASET_ID}.logistic_regression_income_tuned`)
ORDER BY roc_auc DESC
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
FROM ML.EVALUATE(MODEL `statmike-mlops-349915.bq_ml.logistic_regression_income`)
```

---
## Examples — BigFrames

BigFrames provides a scikit-learn-style API (`bigframes.ml`) that trains BigQuery ML models under the hood. Here's the same logistic regression with `bigframes.ml.linear_model.LogisticRegression`.

```python
import bigframes.pandas as bpd

bpd.close_session()  # Reset session to apply project/location settings
bpd.options.bigquery.project = PROJECT_ID
bpd.options.bigquery.location = LOCATION
```

```python
from bigframes.ml.linear_model import LogisticRegression

# Load data as a BigFrames DataFrame
df = bpd.read_gbq('bigquery-public-data.ml_datasets.census_adult_income')

feature_cols = ['age', 'workclass', 'education', 'education_num', 'marital_status',
                'occupation', 'relationship', 'race', 'sex', 'hours_per_week', 'native_country']
X = df[feature_cols]
y = df['income_bracket']

# Train (creates a BigQuery ML model behind the scenes)
model = LogisticRegression(class_weight="balanced")  # BigFrames uses sklearn-style class_weight
model.fit(X, y)

# Evaluate
model.score(X, y).to_pandas()
```
