# Random Forest Regressor — BigQuery ML

Train a **regression** model with `CREATE MODEL` (model_type = `RANDOM_FOREST_REGRESSOR`) — a bagged ensemble of decision trees powered by XGBoost — then walk the full model lifecycle: evaluate, predict, explain, inspect feature importance, visualize a tree, apply in-model preprocessing, and tune hyperparameters. No data leaves BigQuery, and no separate training infrastructure is needed.

**Lifecycle:** `CREATE MODEL` → `ML.EVALUATE` → `ML.PREDICT` → `ML.EXPLAIN_PREDICT` → `ML.GLOBAL_EXPLAIN` / `ML.FEATURE_IMPORTANCE` → `ML.FEATURE_INFO` / `ML.TRAINING_INFO` → `EXPORT MODEL` (tree visualization) → `TRANSFORM` clause → hyperparameter tuning (`ML.TRIAL_INFO`)

**When to use a random forest regressor:**
- A robust, low-tuning ensemble that resists overfitting via bagging (row + column subsampling per tree)
- Structured/tabular data — compare `r2_score` directly against `models/linear_regression` (Linear Regression) and `models/boosted_tree_regressor` (Boosted Tree Regressor) on the same data
- You want built-in feature attributions plus split-based feature importance (`ML.FEATURE_IMPORTANCE`)

**Random forest vs. boosted tree:** both are XGBoost-based tree ensembles in BigQuery ML, but they train fundamentally differently. A random forest builds `num_parallel_tree` complete, independent trees in a **single pass** (bagging) and averages them — `max_iterations` is not even a valid option for this model type. A boosted tree sequentially fits many *shallow* trees to the residuals of the previous ones. **On this small (333-row) dataset, that difference matters**: random forest's bagging underperforms both boosting and even plain linear regression here (`r2_score` ≈ 0.74 vs. ≈ 0.97 for boosted trees and ≈ 0.88 for linear regression — verified, and it persists even after hyperparameter tuning, see Step 8). A real, honest comparison point, not a misconfiguration.

**Data:** [`bigquery-public-data.ml_datasets.penguins`](https://console.cloud.google.com/marketplace/product/bigquery-public-datasets) — predict a penguin's `body_mass_g` from species, island, and bill/flipper measurements. **Same data + label as `models/linear_regression` (Linear Regression) and `models/boosted_tree_regressor` (Boosted Tree Regressor)** — compare `r2_score` across all three techniques. Rows with a NULL label or an unrecorded `sex` are filtered out.

**References:** `RESOURCES.md` (Full reference) | [CREATE MODEL (random forest) docs](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-random-forest) | `setup` (Setup guide)

---
## Setup

Set your project and location, authenticate, and create a shared dataset for the model.

> Random forests train on data already in BigQuery — no connection or remote model required. The model is created with `CREATE MODEL` and stored in your dataset. See the `setup` (Setup Reference) for details.

```python
PROJECT_ID = 'statmike-mlops-349915'  # <-- Replace with your project ID
LOCATION = 'US'  # BigQuery dataset location
DATASET_ID = 'bq_ml'  # Shared dataset across all bq-ml notebooks
BUCKET = 'statmike-mlops-349915'  # <-- Replace with your GCS bucket (same location as DATASET_ID) -- used in Step 6 to export/visualize a tree
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
- `num_parallel_tree = 50` — the number of trees in the forest, trained in parallel on row/column subsamples
- `data_split_method = 'AUTO_SPLIT'` — automatically hold out rows for evaluation
- `enable_global_explain = TRUE` — **required** to use `ML.GLOBAL_EXPLAIN` later

> **Gotcha (verified):** `max_iterations` is **not a valid option for `RANDOM_FOREST_*` at all** — `CREATE MODEL` errors immediately if you set it. `num_parallel_tree` alone defines the forest; training is single-pass by API-level guarantee.

```python
query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.random_forest_regressor_penguins`
OPTIONS(
  model_type = 'RANDOM_FOREST_REGRESSOR',
  input_label_cols = ['body_mass_g'],
  num_parallel_tree = 50,
  tree_method = 'HIST',
  data_split_method = 'AUTO_SPLIT',
  enable_global_explain = TRUE
) AS
SELECT
  species, island, culmen_length_mm, culmen_depth_mm, flipper_length_mm, sex, body_mass_g
FROM `bigquery-public-data.ml_datasets.penguins`
WHERE body_mass_g IS NOT NULL AND sex IN ('MALE', 'FEMALE')
"""
client.query(query).result()
print('Model random_forest_regressor_penguins created')
```

---
## Step 2 — Evaluate with `ML.EVALUATE`

`ML.EVALUATE` returns standard regression metrics on the automatically held-out evaluation split: mean absolute error, mean squared error, R², and explained variance. Compare `r2_score` against `models/linear_regression` (Linear Regression) and `models/boosted_tree_regressor` (Boosted Tree Regressor), which train on the exact same data — see the overview note above on why random forest underperforms both here.

```python
query = f"""
SELECT *
FROM ML.EVALUATE(MODEL `{PROJECT_ID}.{DATASET_ID}.random_forest_regressor_penguins`)
"""
client.query(query).to_dataframe()
```

---
## Step 3 — Predict with `ML.PREDICT`

`ML.PREDICT` scores new rows. It returns `predicted_body_mass_g` — a single continuous value, no probability array like a classifier.

```python
query = f"""
SELECT
  predicted_body_mass_g,
  species,
  flipper_length_mm
FROM ML.PREDICT(
  MODEL `{PROJECT_ID}.{DATASET_ID}.random_forest_regressor_penguins`,
  (SELECT * FROM `bigquery-public-data.ml_datasets.penguins`
   WHERE body_mass_g IS NOT NULL AND sex IN ('MALE', 'FEMALE') LIMIT 10)
)
"""
client.query(query).to_dataframe()
```

---
## Step 4 — Explain predictions

- **`ML.EXPLAIN_PREDICT`** — per-row feature attributions
- **`ML.GLOBAL_EXPLAIN`** — overall feature importance across the model (Shapley-style; requires `enable_global_explain = TRUE`)
- **`ML.FEATURE_IMPORTANCE`** — tree-specific, split-based importance (`weight`/`gain`/`cover`). Neither applies to GLMs (see `models/linear_regression` (Linear Regression)) — use `ML.WEIGHTS` there instead.

> On this small dataset with heavy column subsampling (`colsample_bynode` default 0.8 over just 6 features), some features can end up with **zero** importance/attribution — verified: `island` and `culmen_length_mm` both showed `importance_weight = 0` / `attribution = 0.0` in testing. A real effect of bagging variance on a small feature set, not a bug.

```python
query = f"""
SELECT
  predicted_body_mass_g,
  top_feature_attributions
FROM ML.EXPLAIN_PREDICT(
  MODEL `{PROJECT_ID}.{DATASET_ID}.random_forest_regressor_penguins`,
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
FROM ML.GLOBAL_EXPLAIN(MODEL `{PROJECT_ID}.{DATASET_ID}.random_forest_regressor_penguins`)
ORDER BY attribution DESC
"""
client.query(query).to_dataframe()
```

```python
query = f"""
SELECT *
FROM ML.FEATURE_IMPORTANCE(MODEL `{PROJECT_ID}.{DATASET_ID}.random_forest_regressor_penguins`)
ORDER BY importance_gain DESC
"""
client.query(query).to_dataframe()
```

---
## Step 5 — Introspect the model

`ML.FEATURE_INFO` reports the statistics each feature had during training. `ML.TRAINING_INFO` returns the training loss — for a random forest this is always **exactly one row** (`iteration = 1`) with `learning_rate = 1.0` (contrast with the multi-iteration, shrinking-learning-rate curve in `models/boosted_tree_regressor` (Boosted Tree Regressor)).

```python
query = f"""
SELECT *
FROM ML.FEATURE_INFO(MODEL `{PROJECT_ID}.{DATASET_ID}.random_forest_regressor_penguins`)
"""
client.query(query).to_dataframe()
```

```python
query = f"""
SELECT iteration, loss, eval_loss, learning_rate, duration_ms
FROM ML.TRAINING_INFO(MODEL `{PROJECT_ID}.{DATASET_ID}.random_forest_regressor_penguins`)
ORDER BY iteration
"""
client.query(query).to_dataframe()
```

---
## Step 6 — Visualize a tree by exporting the model

`EXPORT MODEL` writes a trained ensemble to Cloud Storage as an XGBoost Booster file (`model.bst`). Downloading it and loading it with the `xgboost` Python library lets you plot an individual tree's structure — same mechanism as `models/boosted_tree_regressor` (Boosted Tree Regressor), with the same gotchas (pin `xgboost==1.7.6`; reassign `feature_names` manually; expect an extra `reg:linear is now deprecated` warning on load).

> **A random-forest-specific gotcha (verified, see `models/random_forest_classifier` (Random Forest Classifier) for the original writeup):** the main model above produces trees that are **too dense to render meaningfully** — every random forest tree is a complete, independently-trained tree, unlike a boosted tree's shallow early-round tree. **Fix:** train a small, separate **illustrative forest** just for the diagram (`num_parallel_tree=10`, `max_tree_depth=3`).

```python
# A small, shallow forest -- for visualization only, not for metrics.
query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.random_forest_regressor_penguins_viz`
OPTIONS(
  model_type = 'RANDOM_FOREST_REGRESSOR',
  input_label_cols = ['body_mass_g'],
  num_parallel_tree = 10,
  max_tree_depth = 3
) AS
SELECT
  species, island, culmen_length_mm, culmen_depth_mm, flipper_length_mm, sex, body_mass_g
FROM `bigquery-public-data.ml_datasets.penguins`
WHERE body_mass_g IS NOT NULL AND sex IN ('MALE', 'FEMALE')
"""
client.query(query).result()
print('Illustrative forest created')
```

```python
query = f"""
EXPORT MODEL `{PROJECT_ID}.{DATASET_ID}.random_forest_regressor_penguins_viz`
OPTIONS (URI = 'gs://{BUCKET}/bq_ml/random_forest_regressor/model_viz')
"""
client.query(query).result()
print('Model exported')
```

```python
# Pin xgboost<2.0 -- newer versions cannot load BQML's exported XGBoost 0.82
# binary format. graphviz is the Python binding used by xgboost.plot_tree()
# to render; it shells out to the system 'dot' binary.
install('xgboost==1.7.6', 'graphviz')

from google.cloud import storage
import os

local_dir = '/tmp/random_forest_regressor_export'
os.makedirs(local_dir, exist_ok=True)

storage_client = storage.Client(project=PROJECT_ID)
bucket = storage_client.bucket(BUCKET)
blob = bucket.blob('bq_ml/random_forest_regressor/model_viz/model.bst')
local_path = os.path.join(local_dir, 'model.bst')
blob.download_to_filename(local_path)
print(f'Downloaded to {local_path}')
```

```python
import xgboost as xgb
import matplotlib.pyplot as plt

booster = xgb.Booster()
booster.load_model(local_path)

# Feature names in the same order as the illustrative forest's training
# SELECT, excluding the label column. Not preserved by EXPORT MODEL.
booster.feature_names = [
    'species', 'island', 'culmen_length_mm', 'culmen_depth_mm', 'flipper_length_mm', 'sex',
]

fig, ax = plt.subplots(figsize=(20, 10))
xgb.plot_tree(booster, num_trees=0, ax=ax)
plt.title('Random Forest Regressor - Tree 0 (shallow illustrative forest)')
plt.tight_layout()
plt.show()
```

---
## Step 7 — In-model preprocessing with the `TRANSFORM` clause

The `TRANSFORM` clause bakes preprocessing into the model. Here we label-encode the categorical features into ordinals instead of relying on the model's automatic categorical handling. `ML.LABEL_ENCODER` is an analytic function, so it requires an empty `OVER()`.

```python
query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.random_forest_regressor_penguins_transform`
TRANSFORM(
  ML.LABEL_ENCODER(species) OVER() AS species,
  ML.LABEL_ENCODER(island) OVER() AS island,
  ML.LABEL_ENCODER(sex) OVER() AS sex,
  culmen_length_mm, culmen_depth_mm, flipper_length_mm, body_mass_g
)
OPTIONS(
  model_type = 'RANDOM_FOREST_REGRESSOR',
  input_label_cols = ['body_mass_g'],
  num_parallel_tree = 50
) AS
SELECT species, island, culmen_length_mm, culmen_depth_mm, flipper_length_mm, sex, body_mass_g
FROM `bigquery-public-data.ml_datasets.penguins`
WHERE body_mass_g IS NOT NULL AND sex IN ('MALE', 'FEMALE')
"""
client.query(query).result()
print('Model random_forest_regressor_penguins_transform created')
```

```python
# Predict on RAW rows - label-encoding is applied automatically inside the model
query = f"""
SELECT predicted_body_mass_g, species, island, sex
FROM ML.PREDICT(
  MODEL `{PROJECT_ID}.{DATASET_ID}.random_forest_regressor_penguins_transform`,
  (SELECT * FROM `bigquery-public-data.ml_datasets.penguins`
   WHERE body_mass_g IS NOT NULL AND sex IN ('MALE', 'FEMALE') LIMIT 5)
)
"""
client.query(query).to_dataframe()
```

---
## Step 8 — Hyperparameter tuning

Tune the forest size (`num_parallel_tree`) and tree depth (`max_tree_depth`). Inspect trials with `ML.TRIAL_INFO`.

> Verified: even the best-tuned trial only reaches `r2_score` ≈ 0.76 on this dataset — still well below `models/boosted_tree_regressor` (Boosted Tree Regressor)'s ≈ 0.97. This reinforces the overview note that bagging underperforms boosting here — not a tuning shortfall. Individual trials can also occasionally fail with a transient error (`status = 'FAILED'`, `NULL` metric) without failing the overall job.

```python
query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.random_forest_regressor_penguins_tuned`
OPTIONS(
  model_type = 'RANDOM_FOREST_REGRESSOR',
  input_label_cols = ['body_mass_g'],
  num_trials = 6,
  max_parallel_trials = 3,
  hparam_tuning_objectives = ['r2_score'],
  num_parallel_tree = HPARAM_RANGE(20, 100),
  max_tree_depth = HPARAM_RANGE(4, 8)
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
FROM ML.TRIAL_INFO(MODEL `{PROJECT_ID}.{DATASET_ID}.random_forest_regressor_penguins_tuned`)
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
FROM ML.EVALUATE(MODEL `statmike-mlops-349915.bq_ml.random_forest_regressor_penguins`)
```

---
## Examples — BigFrames

BigFrames provides a scikit-learn-style API (`bigframes.ml`) that trains BigQuery ML models under the hood. Here's the same random forest regressor with `bigframes.ml.ensemble.RandomForestRegressor`.

```python
import bigframes.pandas as bpd

bpd.close_session()  # Reset session to apply project/location settings
bpd.options.bigquery.project = PROJECT_ID
bpd.options.bigquery.location = LOCATION
```

```python
from bigframes.ml.ensemble import RandomForestRegressor

# Load data as a BigFrames DataFrame
df = bpd.read_gbq('bigquery-public-data.ml_datasets.penguins')
df = df[df['body_mass_g'].notnull() & df['sex'].isin(['MALE', 'FEMALE'])]

feature_cols = ['species', 'island', 'culmen_length_mm', 'culmen_depth_mm', 'flipper_length_mm', 'sex']
X = df[feature_cols]
y = df['body_mass_g']

# Train (creates a BigQuery ML model behind the scenes)
model = RandomForestRegressor()
model.fit(X, y)

# Evaluate
model.score(X, y).to_pandas()
```
