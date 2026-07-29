# Wide & Deep Classifier — BigQuery ML

Train a **binary classification** model with `CREATE MODEL` (model_type = `DNN_LINEAR_COMBINED_CLASSIFIER`) — a jointly-trained combination of a **wide** linear model (memorizes feature interactions) and a **deep** neural network (generalizes), trained with TensorFlow inside BigQuery — then walk the full model lifecycle: evaluate, predict, explain, inspect training, apply in-model preprocessing, and tune hyperparameters. No data leaves BigQuery, and no separate training infrastructure is needed.

**Lifecycle:** `CREATE MODEL` → `ML.EVALUATE` → `ML.CONFUSION_MATRIX` / `ML.ROC_CURVE` → `ML.PREDICT` → `ML.EXPLAIN_PREDICT` / `ML.GLOBAL_EXPLAIN` → `ML.FEATURE_INFO` / `ML.TRAINING_INFO` → `TRANSFORM` clause → hyperparameter tuning (`ML.TRIAL_INFO`)

**When to use wide & deep:**
- Large, sparse categorical features (high-cardinality IDs) common in ranking/recommendation problems
- You want both memorization of specific feature combinations (wide) and generalization to unseen ones (deep)
- A plain DNN underfits sparse signals but a linear-only model underfits interactions
- Structured/tabular data — compare `roc_auc` directly against `models/logistic_regression` (Logistic Regression), `models/boosted_tree_classifier` (Boosted Tree Classifier), `models/random_forest_classifier` (Random Forest Classifier), and `models/dnn_classifier` (DNN Classifier) on the same data

**Same training-cost profile as `models/dnn_classifier` (DNN Classifier)** — this is TensorFlow training inside BigQuery, so expect multi-minute `CREATE MODEL` calls even on modest data, well beyond the tree models.

**Data:** [`bigquery-public-data.ml_datasets.census_adult_income`](https://console.cloud.google.com/marketplace/product/bigquery-public-datasets) — predict whether income exceeds $50K/year from census attributes. **Same data + label as `models/logistic_regression` (Logistic Regression), `models/boosted_tree_classifier` (Boosted Tree Classifier), `models/random_forest_classifier` (Random Forest Classifier), and `models/dnn_classifier` (DNN Classifier)** — compare `roc_auc` across all five techniques.

**References:** `RESOURCES.md` (Full reference) | [CREATE MODEL (wide-and-deep) docs](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-wnd-models) | `setup` (Setup guide)

---
## Setup

Set your project and location, authenticate, and create a shared dataset for the model.

> Wide & deep models train on data already in BigQuery — no connection or remote model required. The model is created with `CREATE MODEL` and stored in your dataset. See the `setup` (Setup Reference) for details.

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

`CREATE MODEL` trains and stores the model in your dataset. `hidden_units` define the **deep** side's fully-connected layers; the **wide** (linear) side is implicit and uses the same input features. `auto_class_weights` balances the classes; `enable_global_explain` is **required** to use `ML.GLOBAL_EXPLAIN` later.

> **Verified:** like `DNN_CLASSIFIER`, this tolerates unscaled numeric inputs reasonably well on this dataset — `early_stop` still cuts training to 2 iterations, but `roc_auc` lands competitively (~0.89). Contrast with `models/wide_and_deep_regressor` (Wide & Deep Regressor), where the same default settings on the small penguins dataset produce a badly broken model (same finding as `models/dnn_regressor` (DNN Regressor)).

```python
query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.wide_deep_classifier_income`
OPTIONS(
  model_type = 'DNN_LINEAR_COMBINED_CLASSIFIER',
  input_label_cols = ['income_bracket'],
  hidden_units = [64, 32],
  activation_fn = 'RELU',
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
print('Model wide_deep_classifier_income created')
```

---
## Step 2 — Evaluate with `ML.EVALUATE`

`ML.EVALUATE` returns standard classification metrics on the automatically held-out evaluation split. Compare `roc_auc` against `models/logistic_regression` (Logistic Regression), `models/boosted_tree_classifier` (Boosted Tree Classifier), `models/random_forest_classifier` (Random Forest Classifier), and `models/dnn_classifier` (DNN Classifier), which all train on the exact same data.

```python
query = f"""
SELECT *
FROM ML.EVALUATE(MODEL `{PROJECT_ID}.{DATASET_ID}.wide_deep_classifier_income`)
"""
client.query(query).to_dataframe()
```

---
## Step 3 — Confusion matrix and ROC curve

`ML.CONFUSION_MATRIX` shows counts of predicted vs. actual classes. `ML.ROC_CURVE` returns the recall / false-positive-rate tradeoff across thresholds.

```python
query = f"""
SELECT *
FROM ML.CONFUSION_MATRIX(MODEL `{PROJECT_ID}.{DATASET_ID}.wide_deep_classifier_income`)
"""
client.query(query).to_dataframe()
```

```python
import matplotlib.pyplot as plt

query = f"""
SELECT threshold, recall, false_positive_rate
FROM ML.ROC_CURVE(MODEL `{PROJECT_ID}.{DATASET_ID}.wide_deep_classifier_income`)
ORDER BY threshold
"""
roc = client.query(query).to_dataframe()

fig, ax = plt.subplots(figsize=(6, 6))
ax.plot(roc['false_positive_rate'], roc['recall'], color='#4285F4', linewidth=2, label='ROC curve')
ax.plot([0, 1], [0, 1], color='gray', linestyle='--', alpha=0.6, label='Random')
ax.set_xlabel('False Positive Rate')
ax.set_ylabel('True Positive Rate (Recall)')
ax.set_title('ROC Curve - Wide & Deep Classifier')
ax.legend(loc='lower right')
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()
```

---
## Step 4 — Predict with `ML.PREDICT`

```python
query = f"""
SELECT
  predicted_income_bracket,
  predicted_income_bracket_probs
FROM ML.PREDICT(
  MODEL `{PROJECT_ID}.{DATASET_ID}.wide_deep_classifier_income`,
  (SELECT * FROM `bigquery-public-data.ml_datasets.census_adult_income` LIMIT 10)
)
"""
client.query(query).to_dataframe()
```

---
## Step 5 — Explain predictions

- **`ML.EXPLAIN_PREDICT`** — per-row feature attributions (Integrated Gradients)
- **`ML.GLOBAL_EXPLAIN`** — overall feature importance across the model (requires `enable_global_explain = TRUE`)

No coefficients and no split-based importance for this model type, so there is no `ML.WEIGHTS`/`ML.ADVANCED_WEIGHTS` (GLM-only) or `ML.FEATURE_IMPORTANCE` (tree-only) here — same as `models/dnn_classifier` (DNN Classifier).

```python
query = f"""
SELECT
  predicted_income_bracket,
  top_feature_attributions
FROM ML.EXPLAIN_PREDICT(
  MODEL `{PROJECT_ID}.{DATASET_ID}.wide_deep_classifier_income`,
  (SELECT * FROM `bigquery-public-data.ml_datasets.census_adult_income` LIMIT 5),
  STRUCT(5 AS top_k_features)
)
"""
client.query(query).to_dataframe()
```

```python
query = f"""
SELECT *
FROM ML.GLOBAL_EXPLAIN(MODEL `{PROJECT_ID}.{DATASET_ID}.wide_deep_classifier_income`)
ORDER BY attribution DESC
"""
client.query(query).to_dataframe()
```

---
## Step 6 — Introspect the model

`ML.FEATURE_INFO` reports the statistics each feature had during training. `ML.TRAINING_INFO` returns the per-iteration loss curve — verified: `early_stop = TRUE` (the default) stopped training after only 2 iterations here, same pattern as `models/dnn_classifier` (DNN Classifier).

```python
query = f"""
SELECT *
FROM ML.FEATURE_INFO(MODEL `{PROJECT_ID}.{DATASET_ID}.wide_deep_classifier_income`)
"""
client.query(query).to_dataframe()
```

```python
query = f"""
SELECT iteration, loss, eval_loss, learning_rate, duration_ms
FROM ML.TRAINING_INFO(MODEL `{PROJECT_ID}.{DATASET_ID}.wide_deep_classifier_income`)
ORDER BY iteration
"""
client.query(query).to_dataframe()
```

---
## Step 7 — In-model preprocessing with the `TRANSFORM` clause

Same best practice as DNN: normalize numeric inputs before gradient-based training. **Verified effect:** final `roc_auc` comes out about the same as Step 1 (~0.89), but this run took 8 iterations to hit the same early-stopping rule (vs. 2 unscaled), with a properly declining loss curve instead of an almost-flat one.

```python
query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.wide_deep_classifier_income_transform`
TRANSFORM(
  ML.STANDARD_SCALER(age) OVER() AS age,
  ML.STANDARD_SCALER(education_num) OVER() AS education_num,
  ML.STANDARD_SCALER(hours_per_week) OVER() AS hours_per_week,
  workclass, education, marital_status, occupation, relationship, race, sex,
  native_country, income_bracket
)
OPTIONS(
  model_type = 'DNN_LINEAR_COMBINED_CLASSIFIER',
  input_label_cols = ['income_bracket'],
  hidden_units = [64, 32],
  activation_fn = 'RELU',
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
print('Model wide_deep_classifier_income_transform created')
```

```python
# Predict on RAW rows - scaling is applied automatically inside the model
query = f"""
SELECT predicted_income_bracket, age
FROM ML.PREDICT(
  MODEL `{PROJECT_ID}.{DATASET_ID}.wide_deep_classifier_income_transform`,
  (SELECT * FROM `bigquery-public-data.ml_datasets.census_adult_income` LIMIT 5)
)
"""
client.query(query).to_dataframe()
```

---
## Step 8 — Hyperparameter tuning

`hidden_units` is only tunable via `HPARAM_CANDIDATES` (same STRUCT-wrapped array syntax as DNN). `dropout` is tunable via `HPARAM_RANGE`.

> **GOTCHA (verified, differs from `DNN_CLASSIFIER`/`DNN_REGRESSOR`):** `learn_rate` and `optimizer` are **NOT** tunable for `DNN_LINEAR_COMBINED_*` — both fail immediately with `"Unsupported hyperparameter <name> for model_type DNN_LINEAR_COMBINED_CLASSIFIER"`, even though the general docs summary for DNN-family models lists them as tunable (that applies to plain `DNN_*`, not this type). Confirmed tunable instead: `hidden_units`, `dropout`, `batch_size`, `l1_reg`, `l2_reg`.

```python
query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.wide_deep_classifier_income_tuned`
OPTIONS(
  model_type = 'DNN_LINEAR_COMBINED_CLASSIFIER',
  input_label_cols = ['income_bracket'],
  auto_class_weights = TRUE,
  num_trials = 4,
  max_parallel_trials = 2,
  hparam_tuning_objectives = ['roc_auc'],
  hidden_units = HPARAM_CANDIDATES([STRUCT([64, 32]), STRUCT([32, 16])]),
  dropout = HPARAM_RANGE(0.0, 0.3)
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
FROM ML.TRIAL_INFO(MODEL `{PROJECT_ID}.{DATASET_ID}.wide_deep_classifier_income_tuned`)
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
FROM ML.EVALUATE(MODEL `statmike-mlops-349915.bq_ml.wide_deep_classifier_income`)
```

---
## BigFrames

**No first-class wide-and-deep wrapper exists in `bigframes.ml`** (verified against the installed BigFrames API reference: `bigframes.ml.linear_model`, `.ensemble`, `.cluster`, `.decomposition`, `.forecasting`, `.imported`, `.llm` — no `DNNLinearCombinedClassifier`/`Regressor` or equivalent anywhere in the package, same gap as `models/dnn_classifier` (DNN Classifier)/`models/dnn_regressor` (DNN Regressor)). Use the SQL `CREATE MODEL` interface shown above.
