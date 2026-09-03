# Boosted Tree Regressor — BigQuery ML

Train a **regression** model with `CREATE MODEL` (model_type = `BOOSTED_TREE_REGRESSOR`) — a gradient-boosted decision tree ensemble powered by XGBoost — then walk the full model lifecycle: evaluate, predict, explain, inspect feature importance, visualize a tree, apply in-model preprocessing, and tune hyperparameters. No data leaves BigQuery, and no separate training infrastructure is needed.

**Lifecycle:** `CREATE MODEL` → `ML.EVALUATE` → `ML.PREDICT` → `ML.EXPLAIN_PREDICT` → `ML.GLOBAL_EXPLAIN` / `ML.FEATURE_IMPORTANCE` → `ML.FEATURE_INFO` / `ML.TRAINING_INFO` → `EXPORT MODEL` (tree visualization) → `TRANSFORM` clause → hyperparameter tuning (`ML.TRIAL_INFO`)

**When to use a boosted tree regressor:**
- Non-linear feature interactions that a linear model can't capture
- Structured/tabular data where accuracy matters more than a single interpretable equation — compare `r2_score` directly against `models/linear_regression` (Linear Regression) on the same data
- You want built-in per-prediction and per-model feature attributions for a tree model, plus split-based feature importance (`ML.FEATURE_IMPORTANCE`)
- You want to see an actual tree diagram, not just numbers — `EXPORT MODEL` + the `xgboost` Python library can render one
- A strong, fast-training baseline before reaching for a DNN

**Data:** [`bigquery-public-data.ml_datasets.penguins`](https://console.cloud.google.com/marketplace/product/bigquery-public-datasets) — predict a penguin's `body_mass_g` from species, island, and bill/flipper measurements. **Same data + label as `models/linear_regression` (Linear Regression)** — compare `r2_score` and feature attributions directly between the two techniques. Rows with a NULL label or an unrecorded `sex` are filtered out.

**Featured in:** `workflows/regression_based_forecasting` (Regression-Based Forecasting) — time/lag/lead feature engineering applied to `BOOSTED_TREE_REGRESSOR` for demand forecasting (also documents a real training-time GOTCHA for this model type there).

**References:** `RESOURCES.md` (Full reference) | [CREATE MODEL (boosted tree) docs](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-boosted-tree) | `setup` (Setup guide)

---
## Setup

Set your project and location, authenticate, and create a shared dataset for the model.

> Boosted trees train on data already in BigQuery — no connection or remote model required. The model is created with `CREATE MODEL` and stored in your dataset. See the `setup` (Setup Reference) for details.

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
- `data_split_method = 'AUTO_SPLIT'` — automatically hold out rows for evaluation
- `enable_global_explain = TRUE` — **required** to use `ML.GLOBAL_EXPLAIN` later
- `xgboost_version = '2.1'` — train with a current XGBoost library instead of the default

Unlike the classifier, there is no `auto_class_weights` option for regression.

> **The `xgboost_version` default is `0.9`** — a 2019 release — and omitting the option gets you that. `'2.1'` reached GA on 2026-08-27. It is set here for what it does to Step 6: the exported booster becomes a modern `model.ubj` that current `xgboost` reads with no pinned dependency, and the regressor's legacy `reg:linear` objective name goes away with it. Accepted values are `0.9`, `1.1`, and `2.1`. It also has one measured cost — `ML.TRAINING_INFO` comes back empty for this model — documented in full in Step 5.

```python
query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.boosted_tree_regressor_penguins`
OPTIONS(
  model_type = 'BOOSTED_TREE_REGRESSOR',
  xgboost_version = '2.1',
  input_label_cols = ['body_mass_g'],
  data_split_method = 'AUTO_SPLIT',
  enable_global_explain = TRUE
) AS
SELECT
  species, island, culmen_length_mm, culmen_depth_mm, flipper_length_mm, sex, body_mass_g
FROM `bigquery-public-data.ml_datasets.penguins`
WHERE body_mass_g IS NOT NULL AND sex IN ('MALE', 'FEMALE')
"""
client.query(query).result()
print('Model boosted_tree_regressor_penguins created')
```

---
## Step 2 — Evaluate with `ML.EVALUATE`

`ML.EVALUATE` returns standard regression metrics on the automatically held-out evaluation split: mean absolute error, mean squared error, R², and explained variance. Compare `r2_score` against the `models/linear_regression` (Linear Regression) notebook, which trains on the exact same data.

```python
query = f"""
SELECT *
FROM ML.EVALUATE(MODEL `{PROJECT_ID}.{DATASET_ID}.boosted_tree_regressor_penguins`)
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
  MODEL `{PROJECT_ID}.{DATASET_ID}.boosted_tree_regressor_penguins`,
  (SELECT * FROM `bigquery-public-data.ml_datasets.penguins`
   WHERE body_mass_g IS NOT NULL AND sex IN ('MALE', 'FEMALE') LIMIT 10)
)
"""
client.query(query).to_dataframe()
```

---
## Step 4 — Explain predictions

- **`ML.EXPLAIN_PREDICT`** — per-row feature attributions (which features pushed *this* prediction up or down)
- **`ML.GLOBAL_EXPLAIN`** — overall feature importance across the model (Shapley-style; requires `enable_global_explain = TRUE`)
- **`ML.FEATURE_IMPORTANCE`** — tree-specific, split-based importance (`weight`/`gain`/`cover`). This function only applies to tree ensembles — GLMs (like linear regression) don't have it; use `ML.WEIGHTS`/`ML.GLOBAL_EXPLAIN` instead.

`ML.GLOBAL_EXPLAIN` and `ML.FEATURE_IMPORTANCE` can rank features differently — that's expected, not a bug. They measure different things: attribution (contribution to predictions) vs. how often/effectively the trees actually split on a feature.

```python
query = f"""
SELECT
  predicted_body_mass_g,
  top_feature_attributions
FROM ML.EXPLAIN_PREDICT(
  MODEL `{PROJECT_ID}.{DATASET_ID}.boosted_tree_regressor_penguins`,
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
FROM ML.GLOBAL_EXPLAIN(MODEL `{PROJECT_ID}.{DATASET_ID}.boosted_tree_regressor_penguins`)
ORDER BY attribution DESC
"""
client.query(query).to_dataframe()
```

```python
query = f"""
SELECT *
FROM ML.FEATURE_IMPORTANCE(MODEL `{PROJECT_ID}.{DATASET_ID}.boosted_tree_regressor_penguins`)
ORDER BY importance_gain DESC
"""
client.query(query).to_dataframe()
```

---
## Step 5 — Introspect the model

`ML.FEATURE_INFO` reports the statistics each feature had during training.

`ML.TRAINING_INFO` normally returns the per-iteration loss curve, with iteration numbering starting at **1** for tree models (not 0, as in the GLM notebooks). Here it comes back **empty** — a direct consequence of `xgboost_version = '2.1'` in Step 1.

> **GOTCHA (measured, undocumented) — at `xgboost_version = '2.1'`, `ML.TRAINING_INFO` returns zero rows once training runs more than 10 iterations.** Nothing else about the model is affected: `CREATE MODEL` succeeds, and `ML.EVALUATE`, `ML.PREDICT`, `ML.EXPLAIN_PREDICT`, `ML.FEATURE_IMPORTANCE` and `ML.GLOBAL_EXPLAIN` all work on it — Steps 2–4 above are that proof. Only the training history is missing.
>
> The boundary is exactly 10, measured with single-variable probes: at `'0.9'` and at `'1.1'` a 20-iteration run returns all 20 rows, while at `'2.1'` 10 iterations returns 10 rows and 11 returns none. It isn't early stopping, `auto_class_weights` or `enable_global_explain` — the full sweep is in `models/boosted_tree_classifier` (Boosted Tree Classifier) Step 6. This model runs the default `max_iterations = 20`, so the curve is gone.
>
> **The trade-off on a boosted tree is one or the other:** a modern `model.ubj` export (Step 6) or a readable loss curve. To get the curve back, omit `xgboost_version` — returning to the `0.9` default, where this same model reports all 20 iterations, from `loss` 3022.1 down to 144.0 — or hold training to 10 iterations or fewer. This notebook keeps `'2.1'` and accepts the empty result as the documented cost.
>
> `RANDOM_FOREST_*` is unaffected: training there is single-pass, so it never reaches the boundary — `models/random_forest_regressor` (Random Forest Regressor) sets `'2.1'` and still reports its one `ML.TRAINING_INFO` row.

```python
query = f"""
SELECT *
FROM ML.FEATURE_INFO(MODEL `{PROJECT_ID}.{DATASET_ID}.boosted_tree_regressor_penguins`)
"""
client.query(query).to_dataframe()
```

```python
query = f"""
SELECT iteration, loss, eval_loss, learning_rate, duration_ms
FROM ML.TRAINING_INFO(MODEL `{PROJECT_ID}.{DATASET_ID}.boosted_tree_regressor_penguins`)
ORDER BY iteration
"""
client.query(query).to_dataframe()
```

---
## Step 6 — Visualize a tree by exporting the model

`EXPORT MODEL` writes the trained ensemble to Cloud Storage as an XGBoost Booster file. Downloading it and loading it with the `xgboost` Python library lets you plot an individual tree's structure.

**Two of the three things that used to make this step awkward are `xgboost_version` artifacts, not export limitations.** Verified both ways on the same model (see `models/boosted_tree_classifier` (Boosted Tree Classifier) for the side-by-side writeup):

| | default `'0.9'` | `'2.1'` (used here) |
|---|---|---|
| File written | `model.bst`, a legacy binary format | `model.ubj`, UBJSON |
| Current `xgboost` (3.x) can load it | **No** — `Check failed: str[0] == '{'` | **Yes** |
| Python dependency | pin `xgboost==1.7.6` | none |
| Objective name | `reg:linear`, with a deprecation warning on load | `reg:squarederror`, and the load is silent |

> **GOTCHA (verified) — feature names aren't preserved, and `'2.1'` does not fix this one.** The loaded booster's `feature_names` comes back `None` at either version. Set it manually to the training query's non-label column order.
> 
> Rendering also requires the system `graphviz` package (the `dot` binary) — pre-installed in Google Colab; elsewhere run `!apt-get install -y graphviz`.

```python
query = f"""
EXPORT MODEL `{PROJECT_ID}.{DATASET_ID}.boosted_tree_regressor_penguins`
OPTIONS (URI = 'gs://{BUCKET}/bq_ml/boosted_tree_regressor/model')
"""
client.query(query).result()
print('Model exported')
```

```python
# No version pin needed: the model was trained with xgboost_version = '2.1',
# so the export is model.ubj, which current xgboost reads directly. graphviz
# is the Python binding used by xgboost.plot_tree() to render; it shells out
# to the system 'dot' binary.
install('xgboost', 'graphviz')

from google.cloud import storage
import os

local_dir = '/tmp/boosted_tree_regressor_export'
os.makedirs(local_dir, exist_ok=True)

storage_client = storage.Client(project=PROJECT_ID)
bucket = storage_client.bucket(BUCKET)
blob = bucket.blob('bq_ml/boosted_tree_regressor/model/model.ubj')
local_path = os.path.join(local_dir, 'model.ubj')
blob.download_to_filename(local_path)
print(f'Downloaded to {local_path}')
```

```python
import xgboost as xgb
import matplotlib.pyplot as plt

booster = xgb.Booster()
booster.load_model(local_path)

# Feature names in the same order as the CREATE MODEL training SELECT
# (Step 1), excluding the label column. Not preserved by EXPORT MODEL --
# see the gotcha above.
booster.feature_names = [
    'species', 'island', 'culmen_length_mm', 'culmen_depth_mm', 'flipper_length_mm', 'sex',
]

fig, ax = plt.subplots(figsize=(28, 14))
xgb.plot_tree(booster, tree_idx=0, ax=ax)
plt.title('Boosted Tree Regressor - Tree 0 of the ensemble')
plt.tight_layout()
plt.show()
```

---
## Step 7 — In-model preprocessing with the `TRANSFORM` clause

The `TRANSFORM` clause bakes preprocessing into the model. Whatever you do in `TRANSFORM` is **saved with the model and reapplied automatically at predict time** — so `ML.PREDICT` takes raw data, with no need to repeat the preprocessing.

Here we label-encode the categorical features into ordinals instead of relying on the model's automatic categorical handling. `ML.LABEL_ENCODER` is an analytic function, so it requires an empty `OVER()`.

```python
query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.boosted_tree_regressor_penguins_transform`
TRANSFORM(
  ML.LABEL_ENCODER(species) OVER() AS species,
  ML.LABEL_ENCODER(island) OVER() AS island,
  ML.LABEL_ENCODER(sex) OVER() AS sex,
  culmen_length_mm, culmen_depth_mm, flipper_length_mm, body_mass_g
)
OPTIONS(
  model_type = 'BOOSTED_TREE_REGRESSOR',
  xgboost_version = '2.1',
  input_label_cols = ['body_mass_g']
) AS
SELECT species, island, culmen_length_mm, culmen_depth_mm, flipper_length_mm, sex, body_mass_g
FROM `bigquery-public-data.ml_datasets.penguins`
WHERE body_mass_g IS NOT NULL AND sex IN ('MALE', 'FEMALE')
"""
client.query(query).result()
print('Model boosted_tree_regressor_penguins_transform created')
```

```python
# Predict on RAW rows - label-encoding is applied automatically inside the model
query = f"""
SELECT predicted_body_mass_g, species, island, sex
FROM ML.PREDICT(
  MODEL `{PROJECT_ID}.{DATASET_ID}.boosted_tree_regressor_penguins_transform`,
  (SELECT * FROM `bigquery-public-data.ml_datasets.penguins`
   WHERE body_mass_g IS NOT NULL AND sex IN ('MALE', 'FEMALE') LIMIT 5)
)
"""
client.query(query).to_dataframe()
```

---
## Step 8 — Hyperparameter tuning

BigQuery ML has built-in hyperparameter tuning. Set `num_trials` and define a search space with `HPARAM_RANGE` / `HPARAM_CANDIDATES`; BigQuery runs the trials and keeps the best model by `hparam_tuning_objectives`. Inspect every trial with `ML.TRIAL_INFO`.

Here we tune the boosting shrinkage (`learn_rate`) and tree depth (`max_tree_depth`). Training multiple trials takes a while.

> Individual trials can occasionally fail with a transient error (`ML.TRIAL_INFO.status = 'FAILED'`) — this shows up as a `NULL` objective metric for that trial. It does not fail the overall job; BigQuery keeps the best-performing *successful* trial as `is_optimal`. Check `status`/`error_message` if a trial looks off.

```python
query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.boosted_tree_regressor_penguins_tuned`
OPTIONS(
  model_type = 'BOOSTED_TREE_REGRESSOR',
  xgboost_version = '2.1',
  input_label_cols = ['body_mass_g'],
  num_trials = 6,
  max_parallel_trials = 3,
  hparam_tuning_objectives = ['r2_score'],
  learn_rate = HPARAM_RANGE(0.05, 0.3),
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
FROM ML.TRIAL_INFO(MODEL `{PROJECT_ID}.{DATASET_ID}.boosted_tree_regressor_penguins_tuned`)
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
FROM ML.EVALUATE(MODEL `statmike-mlops-349915.bq_ml.boosted_tree_regressor_penguins`)
```

---
## Examples — BigFrames

BigFrames provides a scikit-learn-style API (`bigframes.ml`) that trains BigQuery ML models under the hood. Here's the same boosted tree regressor with `bigframes.ml.ensemble.XGBRegressor`.

```python
import bigframes.pandas as bpd

bpd.close_session()  # Reset session to apply project/location settings
bpd.options.bigquery.project = PROJECT_ID
bpd.options.bigquery.location = LOCATION
```

```python
from bigframes.ml.ensemble import XGBRegressor

# Load data as a BigFrames DataFrame
df = bpd.read_gbq('bigquery-public-data.ml_datasets.penguins')
df = df[df['body_mass_g'].notnull() & df['sex'].isin(['MALE', 'FEMALE'])]

feature_cols = ['species', 'island', 'culmen_length_mm', 'culmen_depth_mm', 'flipper_length_mm', 'sex']
X = df[feature_cols]
y = df['body_mass_g']

# Train (creates a BigQuery ML model behind the scenes)
model = XGBRegressor()
model.fit(X, y)

# Evaluate
model.score(X, y).to_pandas()
```
