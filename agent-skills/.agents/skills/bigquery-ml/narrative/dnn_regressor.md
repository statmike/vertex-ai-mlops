# DNN Regressor — BigQuery ML

Train a **regression** model with `CREATE MODEL` (model_type = `DNN_REGRESSOR`) — a fully-connected feed-forward neural network trained with TensorFlow inside BigQuery — then walk the full model lifecycle: evaluate, predict, explain, inspect training, apply in-model preprocessing, and tune hyperparameters. No data leaves BigQuery, and no separate training infrastructure is needed.

**Lifecycle:** `CREATE MODEL` → `ML.EVALUATE` → `ML.PREDICT` → `ML.EXPLAIN_PREDICT` / `ML.GLOBAL_EXPLAIN` → `ML.FEATURE_INFO` / `ML.TRAINING_INFO` → `TRANSFORM` clause + higher `learn_rate` (the fix) → hyperparameter tuning (`ML.TRIAL_INFO`)

**This notebook tells an honest, verified debugging story** rather than jumping straight to a working config:
1. **Step 1** trains with default settings on unscaled features — the result is **badly broken** (`r2_score ~ -27.5`, far worse than predicting the mean). `early_stop` kicks in after only 2 iterations.
2. **Step 6** shows why: `ML.TRAINING_INFO` confirms training took just 2 gradient steps total before stopping.
3. **Step 7 finds the actual fix** — and it's not what you'd guess first. Scaling the numeric features (the usual DNN best practice) **alone does not fix it** (still `r2_score ~ -27.4`, verified). The binding constraint on this small (333-row) dataset is the default `learn_rate = 0.001`, which is far too conservative. Scaling **plus** a much higher `learn_rate` (0.05) together get `r2_score` to **0.86** — verified to reproduce bit-for-bit across separate full runs, not a lucky one-off.

**When to use a DNN regressor:**
- Non-linear feature/label relationships that linear or tree models underfit
- You specifically want a neural net rather than a tree ensemble
- Structured/tabular data — compare `r2_score` directly against `models/linear_regression` (Linear Regression), `models/boosted_tree_regressor` (Boosted Tree Regressor), and `models/random_forest_regressor` (Random Forest Regressor) on the same data
- For most tabular tasks, try Boosted Tree first — it trains far faster, needs less tuning, and reaches `r2_score ~ 0.97` on this same dataset vs. this notebook's best of ~0.87 (see Step 7)

**Data:** [`bigquery-public-data.ml_datasets.penguins`](https://console.cloud.google.com/marketplace/product/bigquery-public-datasets) — predict `body_mass_g` from physical measurements. **Same data + label as `models/linear_regression` (Linear Regression), `models/boosted_tree_regressor` (Boosted Tree Regressor), and `models/random_forest_regressor` (Random Forest Regressor)** — compare `r2_score` across all four techniques. Rows with a NULL label or an invalid `sex` value (`'.'`) are filtered out.

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

`CREATE MODEL` trains and stores the model in your dataset. Same options as `models/dnn_classifier` (DNN Classifier) minus `auto_class_weights` (classifier-only).

> **GOTCHA (verified, important):** on this small (333-row) dataset, with UNSCALED numeric features (`culmen_length_mm`, `culmen_depth_mm`, `flipper_length_mm`) and the default `learn_rate = 0.001`, this model is badly broken: `r2_score ~ -27.5` — far worse than just predicting the mean. `early_stop = TRUE` (the default) stops training after only 2 iterations. This is the real, reproducible output of this config — not a mistake. See Step 7 for the fix, and note up front: scaling the features **alone does not fix it** (verified) — the binding constraint here is `learn_rate`, not just feature scale.

```python
query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.dnn_regressor_penguins`
OPTIONS(
  model_type = 'DNN_REGRESSOR',
  input_label_cols = ['body_mass_g'],
  hidden_units = [64, 32],
  activation_fn = 'RELU',
  optimizer = 'ADAM',
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
print('Model dnn_regressor_penguins created')
```

---
## Step 2 — Evaluate with `ML.EVALUATE`

Expect a strongly negative `r2_score` here — see the Step 1 gotcha. This is the real output of the baseline config.

```python
query = f"""
SELECT *
FROM ML.EVALUATE(MODEL `{PROJECT_ID}.{DATASET_ID}.dnn_regressor_penguins`)
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
  MODEL `{PROJECT_ID}.{DATASET_ID}.dnn_regressor_penguins`,
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

No `ML.WEIGHTS`/`ML.ADVANCED_WEIGHTS` (GLM-only) or `ML.FEATURE_IMPORTANCE` (tree-only) for DNN models — same as `models/dnn_classifier` (DNN Classifier).

```python
query = f"""
SELECT
  predicted_body_mass_g,
  top_feature_attributions
FROM ML.EXPLAIN_PREDICT(
  MODEL `{PROJECT_ID}.{DATASET_ID}.dnn_regressor_penguins`,
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
FROM ML.GLOBAL_EXPLAIN(MODEL `{PROJECT_ID}.{DATASET_ID}.dnn_regressor_penguins`)
ORDER BY attribution DESC
"""
client.query(query).to_dataframe()
```

---
## Step 5 — Introspect the model

`ML.FEATURE_INFO` reports the statistics each feature had during training. `ML.TRAINING_INFO` returns the per-iteration loss curve — verified: only **2 iterations** run before `early_stop` kicks in, and `eval_loss` (in raw grams², so values in the tens of millions) is nearly flat between them. This is the training-side evidence for the Step 1/2 gotcha.

```python
query = f"""
SELECT *
FROM ML.FEATURE_INFO(MODEL `{PROJECT_ID}.{DATASET_ID}.dnn_regressor_penguins`)
"""
client.query(query).to_dataframe()
```

```python
query = f"""
SELECT iteration, loss, eval_loss, learning_rate, duration_ms
FROM ML.TRAINING_INFO(MODEL `{PROJECT_ID}.{DATASET_ID}.dnn_regressor_penguins`)
ORDER BY iteration
"""
client.query(query).to_dataframe()
```

---
## Step 6 — The fix: `TRANSFORM` (scaling) + a higher `learn_rate`

RESOURCES.md best practice says to normalize numeric features for DNN training — true in general, but **verified insufficient alone here**: scaling with the default `learn_rate = 0.001` still gives `r2_score ~ -27.4`, barely different from Step 1. The actual fix on this small dataset is a much higher `learn_rate` (0.05 vs. the 0.001 default) — with scaling, more headroom (`max_iterations = 30`), and the higher `learn_rate` together, `r2_score` reaches **0.86** — competitive with Linear Regression (~0.88), though still behind Boosted Tree Regressor (~0.97) on this dataset. Verified across two full Restart & Run All passes: this result (`r2_score = 0.861626`) reproduces bit-for-bit — training under a fixed model name is not a fresh random draw each time (see Step 7 for the same behavior in hyperparameter tuning).

**Takeaway:** for small datasets, the default `learn_rate` can be far too conservative — `early_stop` then locks the model in near its random initialization before it has taken enough meaningful gradient steps to converge.

```python
query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.dnn_regressor_penguins_transform`
TRANSFORM(
  ML.STANDARD_SCALER(culmen_length_mm) OVER() AS culmen_length_mm,
  ML.STANDARD_SCALER(culmen_depth_mm) OVER() AS culmen_depth_mm,
  ML.STANDARD_SCALER(flipper_length_mm) OVER() AS flipper_length_mm,
  species, island, sex, body_mass_g
)
OPTIONS(
  model_type = 'DNN_REGRESSOR',
  input_label_cols = ['body_mass_g'],
  hidden_units = [64, 32],
  activation_fn = 'RELU',
  optimizer = 'ADAM',
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
print('Model dnn_regressor_penguins_transform created')
```

```python
# Confirm the fix with ML.EVALUATE -- this is the number the markdown
# above promises. Verified across two full Restart & Run All passes:
# r2_score reproduces bit-for-bit (0.861626 both times) -- like Step 7's
# tuning search, DNN training under a fixed model name is fully
# reproducible here, not a fresh random draw each time.
query = f"""
SELECT *
FROM ML.EVALUATE(MODEL `{PROJECT_ID}.{DATASET_ID}.dnn_regressor_penguins_transform`)
"""
client.query(query).to_dataframe()
```

```python
# Predict on RAW rows - scaling is applied automatically inside the model
query = f"""
SELECT predicted_body_mass_g, species, flipper_length_mm
FROM ML.PREDICT(
  MODEL `{PROJECT_ID}.{DATASET_ID}.dnn_regressor_penguins_transform`,
  (SELECT * FROM `bigquery-public-data.ml_datasets.penguins`
   WHERE body_mass_g IS NOT NULL AND sex IN ('MALE', 'FEMALE') LIMIT 5)
)
"""
client.query(query).to_dataframe()
```

---
## Step 7 — Hyperparameter tuning

`hidden_units` is only tunable via `HPARAM_CANDIDATES`, and each candidate is a `STRUCT` wrapping the whole layer-sizes array (`ARRAY<STRUCT<ARRAY<INT64>>>`) — verified working syntax below. `learn_rate` is tunable via `HPARAM_RANGE` — given Step 6's finding, tuning `learn_rate` directly is exactly the right lever for this dataset.

> **Verified across two full runs of this exact model name — the search is reproducible, not random.** Retraining `dnn_regressor_penguins_tuned` twice (identical SQL, no explicit seed anywhere) produced **bit-for-bit identical trial hyperparameters** both times — the same 4 sampled `learn_rate` values to 17 significant digits, the same optimal trial (`learn_rate≈0.0275`, `r2_score≈0.87`). This suggests BigQuery ML's search order is tied to something about the model's identity (e.g. its resource name) rather than true run-time randomness. A separate ad-hoc validation model with a *different* name but the identical search-space config sampled a completely different, worse set of `learn_rate` values (0.001-0.008, stuck at `r2_score≈-27`) — so don't assume a hyperparameter search that worked (or failed) for one model name will transfer if you rename or duplicate the `CREATE MODEL` statement.

```python
query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.dnn_regressor_penguins_tuned`
TRANSFORM(
  ML.STANDARD_SCALER(culmen_length_mm) OVER() AS culmen_length_mm,
  ML.STANDARD_SCALER(culmen_depth_mm) OVER() AS culmen_depth_mm,
  ML.STANDARD_SCALER(flipper_length_mm) OVER() AS flipper_length_mm,
  species, island, sex, body_mass_g
)
OPTIONS(
  model_type = 'DNN_REGRESSOR',
  input_label_cols = ['body_mass_g'],
  num_trials = 4,
  max_parallel_trials = 2,
  hparam_tuning_objectives = ['r2_score'],
  hidden_units = HPARAM_CANDIDATES([STRUCT([64, 32]), STRUCT([32, 16])]),
  learn_rate = HPARAM_RANGE(0.001, 0.1)
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
FROM ML.TRIAL_INFO(MODEL `{PROJECT_ID}.{DATASET_ID}.dnn_regressor_penguins_tuned`)
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
FROM ML.EVALUATE(MODEL `statmike-mlops-349915.bq_ml.dnn_regressor_penguins`)
```

---
## BigFrames

**No first-class DNN wrapper exists in `bigframes.ml`** (verified against the installed BigFrames API reference: `bigframes.ml.linear_model`, `.ensemble`, `.cluster`, `.decomposition`, `.forecasting`, `.imported`, `.llm` — no `DNNClassifier`/`DNNRegressor`/neural-network class anywhere in the package). This is a permanent gap, not an omission on our part — there's no BigFrames comparison cell in this notebook because there's no BigFrames class to call. Use the SQL `CREATE MODEL` interface shown above, or fall back to `bigframes.ml.imported.TensorFlowModel` to *serve* an already-trained external model (not to train a BQML DNN).
