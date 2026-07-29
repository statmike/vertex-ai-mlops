# Wide & Deep Regressor — BigQuery ML

Train a **regression** model with `CREATE MODEL` (model_type = `DNN_LINEAR_COMBINED_REGRESSOR`) — a jointly-trained combination of a **wide** linear model and a **deep** neural network, trained with TensorFlow inside BigQuery — then walk the full model lifecycle: evaluate, predict, explain, inspect training, apply in-model preprocessing, and tune hyperparameters. No data leaves BigQuery, and no separate training infrastructure is needed.

**Lifecycle:** `CREATE MODEL` → `ML.EVALUATE` → `ML.PREDICT` → `ML.EXPLAIN_PREDICT` / `ML.GLOBAL_EXPLAIN` → `ML.FEATURE_INFO` / `ML.TRAINING_INFO` → `TRANSFORM` clause + higher `learn_rate` (the fix) → hyperparameter tuning (`ML.TRIAL_INFO`)

**This is the same debugging story as `models/dnn_regressor` (DNN Regressor), verified again for this model type:** with default settings on unscaled features, this model is **badly broken** (`r2_score ~ -27.4`, far worse than predicting the mean) — `early_stop` cuts training to just 2 iterations. Scaling the numeric features alone is known (from the DNN Regressor notebook's detailed walkthrough) to be insufficient; the fix applied directly here is scaling **plus** a much higher `learn_rate` (0.05 vs. the 0.001 default), which reaches `r2_score = 0.79` untuned — and **0.87** after hyperparameter tuning (Step 7), which found `hidden_units=[32,16]` works better than the `[64,32]` default on this small dataset. See `models/dnn_regressor` (DNN Regressor) for the step-by-step diagnosis of *why* scaling alone doesn't work — this notebook applies that lesson rather than re-deriving it.

**When to use wide & deep:**
- Large, sparse categorical features (high-cardinality IDs) common in ranking/recommendation problems
- You want both memorization of specific feature combinations (wide) and generalization to unseen ones (deep)
- Structured/tabular data — compare `r2_score` directly against `models/linear_regression` (Linear Regression), `models/boosted_tree_regressor` (Boosted Tree Regressor), `models/random_forest_regressor` (Random Forest Regressor), and `models/dnn_regressor` (DNN Regressor) on the same data
- For most tabular tasks, try Boosted Tree first — it trains far faster, needs less tuning, and reaches `r2_score ~ 0.97` on this same dataset vs. this notebook's best of ~0.87

**Data:** [`bigquery-public-data.ml_datasets.penguins`](https://console.cloud.google.com/marketplace/product/bigquery-public-datasets) — predict `body_mass_g` from physical measurements. **Same data + label as `models/linear_regression` (Linear Regression), `models/boosted_tree_regressor` (Boosted Tree Regressor), `models/random_forest_regressor` (Random Forest Regressor), and `models/dnn_regressor` (DNN Regressor)** — compare `r2_score` across all five techniques. Rows with a NULL label or an invalid `sex` value (`'.'`) are filtered out.

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

`CREATE MODEL` trains and stores the model in your dataset. Same options as `models/wide_and_deep_classifier` (Wide & Deep Classifier) minus `auto_class_weights` (classifier-only).

> **GOTCHA (verified — same finding as `models/dnn_regressor` (DNN Regressor), now confirmed for this model type too):** on this small (333-row) dataset, with UNSCALED numeric features and the default `learn_rate = 0.001`, this model is badly broken: `r2_score ~ -27.4` — far worse than just predicting the mean. `early_stop = TRUE` (the default) stops training after only 2 iterations. See Step 6 for the fix (same recipe as DNN Regressor: scale the numeric features AND raise `learn_rate` well above default) — see `models/dnn_regressor` (DNN Regressor) for the detailed diagnostic walkthrough of why scaling alone is not enough; this notebook applies that lesson directly.

```python
query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.wide_deep_regressor_penguins`
OPTIONS(
  model_type = 'DNN_LINEAR_COMBINED_REGRESSOR',
  input_label_cols = ['body_mass_g'],
  hidden_units = [64, 32],
  activation_fn = 'RELU',
  dropout = 0.15,
  max_iterations = 20,
  early_stop = TRUE,
  data_split_method = 'AUTO_SPLIT',
  enable_global_explain = TRUE
) AS
SELECT
  species, island, culmen_length_mm, culmen_depth_mm, flipper_length_mm, sex, body_mass_g
FROM `bigquery-public-data.ml_datasets.penguins`
WHERE body_mass_g IS NOT NULL AND sex IN ('MALE', 'FEMALE')
"""
client.query(query).result()
print('Model wide_deep_regressor_penguins created')
```

---
## Step 2 — Evaluate with `ML.EVALUATE`

Expect a strongly negative `r2_score` here — see the Step 1 gotcha. This is the real output of the baseline config.

```python
query = f"""
SELECT *
FROM ML.EVALUATE(MODEL `{PROJECT_ID}.{DATASET_ID}.wide_deep_regressor_penguins`)
"""
client.query(query).to_dataframe()
```

---
## Step 3 — Predict with `ML.PREDICT`

```python
query = f"""
SELECT
  predicted_body_mass_g,
  species,
  flipper_length_mm
FROM ML.PREDICT(
  MODEL `{PROJECT_ID}.{DATASET_ID}.wide_deep_regressor_penguins`,
  (SELECT * FROM `bigquery-public-data.ml_datasets.penguins`
   WHERE body_mass_g IS NOT NULL AND sex IN ('MALE', 'FEMALE') LIMIT 10)
)
"""
client.query(query).to_dataframe()
```

---
## Step 4 — Explain predictions

- **`ML.EXPLAIN_PREDICT`** — per-row feature attributions (Integrated Gradients)
- **`ML.GLOBAL_EXPLAIN`** — overall feature importance across the model (requires `enable_global_explain = TRUE`)

No `ML.WEIGHTS`/`ML.ADVANCED_WEIGHTS` (GLM-only) or `ML.FEATURE_IMPORTANCE` (tree-only) for this model type — same as `models/dnn_regressor` (DNN Regressor).

```python
query = f"""
SELECT
  predicted_body_mass_g,
  top_feature_attributions
FROM ML.EXPLAIN_PREDICT(
  MODEL `{PROJECT_ID}.{DATASET_ID}.wide_deep_regressor_penguins`,
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
FROM ML.GLOBAL_EXPLAIN(MODEL `{PROJECT_ID}.{DATASET_ID}.wide_deep_regressor_penguins`)
ORDER BY attribution DESC
"""
client.query(query).to_dataframe()
```

---
## Step 5 — Introspect the model

`ML.FEATURE_INFO` reports the statistics each feature had during training. `ML.TRAINING_INFO` returns the per-iteration loss curve — verified: only 2 iterations run before `early_stop` kicks in, same pattern as `models/dnn_regressor` (DNN Regressor).

```python
query = f"""
SELECT *
FROM ML.FEATURE_INFO(MODEL `{PROJECT_ID}.{DATASET_ID}.wide_deep_regressor_penguins`)
"""
client.query(query).to_dataframe()
```

```python
query = f"""
SELECT iteration, loss, eval_loss, learning_rate, duration_ms
FROM ML.TRAINING_INFO(MODEL `{PROJECT_ID}.{DATASET_ID}.wide_deep_regressor_penguins`)
ORDER BY iteration
"""
client.query(query).to_dataframe()
```

---
## Step 6 — The fix: `TRANSFORM` (scaling) + a higher `learn_rate`

Same fix as `models/dnn_regressor` (DNN Regressor): scale the numeric features AND raise `learn_rate` to 0.05 (50x the 0.001 default), with more `max_iterations` headroom. Verified: `r2_score` reaches **0.79** with the default `hidden_units=[64,32]` — a real fix (up from -27.4), though notably lower than DNN Regressor's ~0.86 with the equivalent fix on the same data. Step 7's hyperparameter tuning closes most of that gap by finding a better `hidden_units` value for this small dataset.

```python
query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.wide_deep_regressor_penguins_transform`
TRANSFORM(
  ML.STANDARD_SCALER(culmen_length_mm) OVER() AS culmen_length_mm,
  ML.STANDARD_SCALER(culmen_depth_mm) OVER() AS culmen_depth_mm,
  ML.STANDARD_SCALER(flipper_length_mm) OVER() AS flipper_length_mm,
  species, island, sex, body_mass_g
)
OPTIONS(
  model_type = 'DNN_LINEAR_COMBINED_REGRESSOR',
  input_label_cols = ['body_mass_g'],
  hidden_units = [64, 32],
  activation_fn = 'RELU',
  learn_rate = 0.05,
  dropout = 0.15,
  max_iterations = 30,
  early_stop = TRUE,
  data_split_method = 'AUTO_SPLIT',
  enable_global_explain = TRUE
) AS
SELECT
  species, island, culmen_length_mm, culmen_depth_mm, flipper_length_mm, sex, body_mass_g
FROM `bigquery-public-data.ml_datasets.penguins`
WHERE body_mass_g IS NOT NULL AND sex IN ('MALE', 'FEMALE')
"""
client.query(query).result()
print('Model wide_deep_regressor_penguins_transform created')
```

```python
# Confirm the fix with ML.EVALUATE
query = f"""
SELECT *
FROM ML.EVALUATE(MODEL `{PROJECT_ID}.{DATASET_ID}.wide_deep_regressor_penguins_transform`)
"""
client.query(query).to_dataframe()
```

```python
# Predict on RAW rows - scaling is applied automatically inside the model
query = f"""
SELECT predicted_body_mass_g, species, flipper_length_mm
FROM ML.PREDICT(
  MODEL `{PROJECT_ID}.{DATASET_ID}.wide_deep_regressor_penguins_transform`,
  (SELECT * FROM `bigquery-public-data.ml_datasets.penguins`
   WHERE body_mass_g IS NOT NULL AND sex IN ('MALE', 'FEMALE') LIMIT 5)
)
"""
client.query(query).to_dataframe()
```

---
## Step 7 — Hyperparameter tuning

`learn_rate` and `optimizer` are **NOT** tunable for this model type (verified — see `models/wide_and_deep_classifier` (Wide & Deep Classifier) Step 8 gotcha), so `learn_rate` stays fixed at the known-good 0.05 from Step 6 while tuning `hidden_units` (`HPARAM_CANDIDATES`) and `dropout` (`HPARAM_RANGE`) instead.

> **Verified:** all 4 trials succeeded (no failures), and all landed in the good region already — since `learn_rate` is fixed rather than searched, there's no risk here of trials getting stuck in the catastrophic unscaled/low-`learn_rate` region the way `models/dnn_regressor` (DNN Regressor)'s tuning step can.

```python
query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.wide_deep_regressor_penguins_tuned`
TRANSFORM(
  ML.STANDARD_SCALER(culmen_length_mm) OVER() AS culmen_length_mm,
  ML.STANDARD_SCALER(culmen_depth_mm) OVER() AS culmen_depth_mm,
  ML.STANDARD_SCALER(flipper_length_mm) OVER() AS flipper_length_mm,
  species, island, sex, body_mass_g
)
OPTIONS(
  model_type = 'DNN_LINEAR_COMBINED_REGRESSOR',
  input_label_cols = ['body_mass_g'],
  learn_rate = 0.05,
  num_trials = 4,
  max_parallel_trials = 2,
  hparam_tuning_objectives = ['r2_score'],
  hidden_units = HPARAM_CANDIDATES([STRUCT([64, 32]), STRUCT([32, 16])]),
  dropout = HPARAM_RANGE(0.0, 0.3)
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
FROM ML.TRIAL_INFO(MODEL `{PROJECT_ID}.{DATASET_ID}.wide_deep_regressor_penguins_tuned`)
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
FROM ML.EVALUATE(MODEL `statmike-mlops-349915.bq_ml.wide_deep_regressor_penguins`)
```

---
## BigFrames

**No first-class wide-and-deep wrapper exists in `bigframes.ml`** (verified against the installed BigFrames API reference: `bigframes.ml.linear_model`, `.ensemble`, `.cluster`, `.decomposition`, `.forecasting`, `.imported`, `.llm` — no `DNNLinearCombinedClassifier`/`Regressor` or equivalent anywhere in the package, same gap as `models/dnn_classifier` (DNN Classifier)/`models/dnn_regressor` (DNN Regressor)). Use the SQL `CREATE MODEL` interface shown above.
