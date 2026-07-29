# DNN Classifier — BigQuery ML

Train a **binary classification** model with `CREATE MODEL` (model_type = `DNN_CLASSIFIER`) — a fully-connected feed-forward neural network trained with TensorFlow inside BigQuery — then walk the full model lifecycle: evaluate, predict, explain, inspect training, apply in-model preprocessing, and tune hyperparameters. No data leaves BigQuery, and no separate training infrastructure is needed.

**Lifecycle:** `CREATE MODEL` → `ML.EVALUATE` → `ML.CONFUSION_MATRIX` / `ML.ROC_CURVE` → `ML.PREDICT` → `ML.EXPLAIN_PREDICT` / `ML.GLOBAL_EXPLAIN` → `ML.FEATURE_INFO` / `ML.TRAINING_INFO` → `TRANSFORM` clause → hyperparameter tuning (`ML.TRIAL_INFO`)

**When to use a DNN classifier:**
- Non-linear feature/label relationships that linear or tree models underfit
- You specifically want a neural net (e.g. for TensorFlow export via `EXPORT MODEL`) rather than a tree ensemble
- Structured/tabular data — compare `roc_auc` directly against `models/logistic_regression` (Logistic Regression), `models/boosted_tree_classifier` (Boosted Tree Classifier), and `models/random_forest_classifier` (Random Forest Classifier) on the same data
- For most tabular tasks, try Boosted Tree or Random Forest first — they train far faster and need less tuning; reach for DNN when you specifically want a neural net

**A genuine gotcha, verified below:** DNN training in BigQuery ML is dramatically slower than the tree models — this notebook's Step 1 `CREATE MODEL` took **12-46 minutes** in testing (wall time varies a lot with concurrent BigQuery load — see `RESOURCES.md` (RESOURCES.md)) for a training set of only ~32K rows, versus a few minutes for the equivalent boosted tree / random forest models. Budget accordingly before running this notebook.

**Data:** [`bigquery-public-data.ml_datasets.census_adult_income`](https://console.cloud.google.com/marketplace/product/bigquery-public-datasets) — predict whether income exceeds $50K/year from census attributes. **Same data + label as `models/logistic_regression` (Logistic Regression), `models/boosted_tree_classifier` (Boosted Tree Classifier), and `models/random_forest_classifier` (Random Forest Classifier)** — compare `roc_auc` across all four techniques.

**References:** `RESOURCES.md` (Full reference) | [CREATE MODEL (DNN) docs](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-dnn-models) | `setup` (Setup guide)

---
## Setup

Set your project and location, authenticate, and create a shared dataset for the model.

> DNNs train on data already in BigQuery — no connection or remote model required. The model is created with `CREATE MODEL` and stored in your dataset. See the `setup` (Setup Reference) for details.

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
- `hidden_units = [64, 32]` — two fully-connected hidden layers
- `dropout = 0.15` — regularization to reduce overfitting
- `auto_class_weights = TRUE` — balance the classes (the data is ~76% `<=50K`)
- `enable_global_explain = TRUE` — **required** to use `ML.GLOBAL_EXPLAIN` later

> **This takes a while — genuinely, not just "first iteration overhead" like the tree models.** Training ran 12-46 minutes in testing. With the default `learn_rate = 0.001` and `early_stop = TRUE`, training here stopped after only **2 iterations** (see `ML.TRAINING_INFO` in Step 6) — despite that short run, `roc_auc` still lands competitively with the other techniques on this dataset (~0.89). Contrast with `models/dnn_regressor` (DNN Regressor), where the same default settings produce a badly broken model — classification tolerates unscaled inputs far better than regression does here.

```python
query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.dnn_classifier_income`
OPTIONS(
  model_type = 'DNN_CLASSIFIER',
  input_label_cols = ['income_bracket'],
  hidden_units = [64, 32],
  activation_fn = 'RELU',
  optimizer = 'ADAM',
  dropout = 0.15,
  max_iterations = 20,
  early_stop = TRUE,
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
print('Model dnn_classifier_income created')
```

---
## Step 2 — Evaluate with `ML.EVALUATE`

`ML.EVALUATE` returns standard classification metrics on the automatically held-out evaluation split: precision, recall, accuracy, F1, log loss, and ROC AUC. Compare `roc_auc` against `models/logistic_regression` (Logistic Regression), `models/boosted_tree_classifier` (Boosted Tree Classifier), and `models/random_forest_classifier` (Random Forest Classifier), which all train on the exact same data.

```python
query = f"""
SELECT *
FROM ML.EVALUATE(MODEL `{PROJECT_ID}.{DATASET_ID}.dnn_classifier_income`)
"""
client.query(query).to_dataframe()
```

---
## Step 3 — Confusion matrix and ROC curve

`ML.CONFUSION_MATRIX` shows counts of predicted vs. actual classes. `ML.ROC_CURVE` returns the recall / false-positive-rate tradeoff across thresholds — useful for choosing an operating point.

```python
query = f"""
SELECT *
FROM ML.CONFUSION_MATRIX(MODEL `{PROJECT_ID}.{DATASET_ID}.dnn_classifier_income`)
"""
client.query(query).to_dataframe()
```

```python
import matplotlib.pyplot as plt

query = f"""
SELECT threshold, recall, false_positive_rate
FROM ML.ROC_CURVE(MODEL `{PROJECT_ID}.{DATASET_ID}.dnn_classifier_income`)
ORDER BY threshold
"""
roc = client.query(query).to_dataframe()

fig, ax = plt.subplots(figsize=(6, 6))
ax.plot(roc['false_positive_rate'], roc['recall'], color='#4285F4', linewidth=2, label='ROC curve')
ax.plot([0, 1], [0, 1], color='gray', linestyle='--', alpha=0.6, label='Random')
ax.set_xlabel('False Positive Rate')
ax.set_ylabel('True Positive Rate (Recall)')
ax.set_title('ROC Curve - DNN Classifier')
ax.legend(loc='lower right')
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()
```

---
## Step 4 — Predict with `ML.PREDICT`

`ML.PREDICT` scores new rows. It returns `predicted_income_bracket` (the chosen class) and `predicted_income_bracket_probs` (the probability of each class) — the same output shape as the other classifier notebooks.

```python
query = f"""
SELECT
  predicted_income_bracket,
  predicted_income_bracket_probs
FROM ML.PREDICT(
  MODEL `{PROJECT_ID}.{DATASET_ID}.dnn_classifier_income`,
  (SELECT * FROM `bigquery-public-data.ml_datasets.census_adult_income` LIMIT 10)
)
"""
client.query(query).to_dataframe()
```

---
## Step 5 — Explain predictions

- **`ML.EXPLAIN_PREDICT`** — per-row feature attributions (Integrated Gradients)
- **`ML.GLOBAL_EXPLAIN`** — overall feature importance across the model (requires `enable_global_explain = TRUE`)

DNNs have no coefficients and no split-based importance, so there is no `ML.WEIGHTS`/`ML.ADVANCED_WEIGHTS` (GLM-only) or `ML.FEATURE_IMPORTANCE` (tree-only) here — Integrated Gradients is the only explainability mechanism for this model type.

```python
query = f"""
SELECT
  predicted_income_bracket,
  top_feature_attributions
FROM ML.EXPLAIN_PREDICT(
  MODEL `{PROJECT_ID}.{DATASET_ID}.dnn_classifier_income`,
  (SELECT * FROM `bigquery-public-data.ml_datasets.census_adult_income` LIMIT 5),
  STRUCT(5 AS top_k_features)
)
"""
client.query(query).to_dataframe()
```

```python
query = f"""
SELECT *
FROM ML.GLOBAL_EXPLAIN(MODEL `{PROJECT_ID}.{DATASET_ID}.dnn_classifier_income`)
ORDER BY attribution DESC
"""
client.query(query).to_dataframe()
```

---
## Step 6 — Introspect the model

`ML.FEATURE_INFO` reports the statistics each feature had during training. `ML.TRAINING_INFO` returns the per-iteration loss curve — verified: with the default `learn_rate = 0.001`, `early_stop = TRUE` (the default) stopped training after only **2 iterations** here, well short of `max_iterations = 20`, with eval loss barely moving between them. See Step 7 for what changes when the numeric features are scaled.

```python
query = f"""
SELECT *
FROM ML.FEATURE_INFO(MODEL `{PROJECT_ID}.{DATASET_ID}.dnn_classifier_income`)
"""
client.query(query).to_dataframe()
```

```python
query = f"""
SELECT iteration, loss, eval_loss, learning_rate, duration_ms
FROM ML.TRAINING_INFO(MODEL `{PROJECT_ID}.{DATASET_ID}.dnn_classifier_income`)
ORDER BY iteration
"""
client.query(query).to_dataframe()
```

---
## Step 7 — In-model preprocessing with the `TRANSFORM` clause

RESOURCES.md best practice: normalize numeric inputs before training a DNN — gradient-based training is sensitive to feature scale. `TRANSFORM` bakes this preprocessing into the model, so `ML.PREDICT` still takes raw data.

**Verified effect:** final `roc_auc` comes out about the same as Step 1 (~0.89), but the training dynamics change — this run took **8 iterations** to hit the same early-stopping rule (vs. 2 unscaled), with a properly declining loss curve instead of an almost-flat one. See `models/dnn_regressor` (DNN Regressor) for a case where scaling — plus a higher `learn_rate` — is the difference between a broken model and a good one.

```python
query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.dnn_classifier_income_transform`
TRANSFORM(
  ML.STANDARD_SCALER(age) OVER() AS age,
  ML.STANDARD_SCALER(education_num) OVER() AS education_num,
  ML.STANDARD_SCALER(hours_per_week) OVER() AS hours_per_week,
  workclass, education, marital_status, occupation, relationship, race, sex,
  native_country, income_bracket
)
OPTIONS(
  model_type = 'DNN_CLASSIFIER',
  input_label_cols = ['income_bracket'],
  hidden_units = [64, 32],
  activation_fn = 'RELU',
  optimizer = 'ADAM',
  dropout = 0.15,
  max_iterations = 20,
  early_stop = TRUE,
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
print('Model dnn_classifier_income_transform created')
```

```python
# Predict on RAW rows - scaling is applied automatically inside the model
query = f"""
SELECT predicted_income_bracket, age
FROM ML.PREDICT(
  MODEL `{PROJECT_ID}.{DATASET_ID}.dnn_classifier_income_transform`,
  (SELECT * FROM `bigquery-public-data.ml_datasets.census_adult_income` LIMIT 5)
)
"""
client.query(query).to_dataframe()
```

---
## Step 8 — Hyperparameter tuning

BigQuery ML has built-in hyperparameter tuning. Set `num_trials` and define a search space with `HPARAM_RANGE` / `HPARAM_CANDIDATES`; BigQuery runs the trials and keeps the best model by `hparam_tuning_objectives`. Inspect every trial with `ML.TRIAL_INFO`.

`hidden_units` is only tunable via `HPARAM_CANDIDATES`, and each candidate is a `STRUCT` wrapping the whole layer-sizes array (`ARRAY<STRUCT<ARRAY<INT64>>>`) — verified working syntax below. `learn_rate` is tunable via `HPARAM_RANGE`. Given how expensive DNN training is (see Step 1), this keeps `num_trials` small.

```python
query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.dnn_classifier_income_tuned`
OPTIONS(
  model_type = 'DNN_CLASSIFIER',
  input_label_cols = ['income_bracket'],
  auto_class_weights = TRUE,
  num_trials = 4,
  max_parallel_trials = 2,
  hparam_tuning_objectives = ['roc_auc'],
  hidden_units = HPARAM_CANDIDATES([STRUCT([64, 32]), STRUCT([32, 16])]),
  learn_rate = HPARAM_RANGE(0.001, 0.05)
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
FROM ML.TRIAL_INFO(MODEL `{PROJECT_ID}.{DATASET_ID}.dnn_classifier_income_tuned`)
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
FROM ML.EVALUATE(MODEL `statmike-mlops-349915.bq_ml.dnn_classifier_income`)
```

---
## BigFrames

**No first-class DNN wrapper exists in `bigframes.ml`** (verified against the installed BigFrames API reference: `bigframes.ml.linear_model`, `.ensemble`, `.cluster`, `.decomposition`, `.forecasting`, `.imported`, `.llm` — no `DNNClassifier`/`DNNRegressor`/neural-network class anywhere in the package). This is a permanent gap, not an omission on our part — there's no BigFrames comparison cell in this notebook because there's no BigFrames class to call. Use the SQL `CREATE MODEL` interface shown above, or fall back to `bigframes.ml.imported.TensorFlowModel` to *serve* an already-trained external model (not to train a BQML DNN).
