# Boosted Tree Classifier — BigQuery ML

Train a **binary classification** model with `CREATE MODEL` (model_type = `BOOSTED_TREE_CLASSIFIER`) — a gradient-boosted decision tree ensemble powered by XGBoost — then walk the full model lifecycle: evaluate, predict, explain, inspect feature importance, visualize a tree, apply in-model preprocessing, and tune hyperparameters. No data leaves BigQuery, and no separate training infrastructure is needed.

**Lifecycle:** `CREATE MODEL` → `ML.EVALUATE` → `ML.CONFUSION_MATRIX` / `ML.ROC_CURVE` → `ML.PREDICT` → `ML.EXPLAIN_PREDICT` → `ML.GLOBAL_EXPLAIN` / `ML.FEATURE_IMPORTANCE` → `ML.FEATURE_INFO` / `ML.TRAINING_INFO` → `EXPORT MODEL` (tree visualization) → `TRANSFORM` clause → hyperparameter tuning (`ML.TRIAL_INFO`)

**When to use a boosted tree classifier:**
- Non-linear feature interactions that a linear/logistic model can't capture
- Structured/tabular data where accuracy matters more than a single interpretable equation
- You want built-in per-prediction and per-model feature attributions for a tree model, plus split-based feature importance (`ML.FEATURE_IMPORTANCE`)
- You want to see an actual tree diagram, not just numbers — `EXPORT MODEL` + the `xgboost` Python library can render one
- A strong, fast-training baseline before reaching for a DNN

**Data:** [`bigquery-public-data.ml_datasets.census_adult_income`](https://console.cloud.google.com/marketplace/product/bigquery-public-datasets) — predict whether income exceeds $50K/year from census attributes. **Same data + label as `models/logistic_regression` (Logistic Regression)** — compare `roc_auc` and feature attributions directly between the two techniques.

**Featured in:** `workflows/embeddings_classification` (Embeddings As Features For Hierarchical Classification) — embedding vectors passed directly as `ARRAY<FLOAT64>` feature columns to classify products into a retail hierarchy.

**References:** `RESOURCES.md` (Full reference) | [CREATE MODEL (boosted tree) docs](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-boosted-tree) | `setup` (Setup guide)

---
## Setup

Set your project and location, authenticate, and create a shared dataset for the model.

> Boosted trees train on data already in BigQuery — no connection or remote model required. The model is created with `CREATE MODEL` and stored in your dataset. See the `setup` (Setup Reference) for details.

```python
PROJECT_ID = 'statmike-mlops-349915'  # <-- Replace with your project ID
LOCATION = 'US'  # BigQuery dataset location
DATASET_ID = 'bq_ml'  # Shared dataset across all bq-ml notebooks
BUCKET = 'statmike-mlops-349915'  # <-- Replace with your GCS bucket (same location as DATASET_ID) -- used in Step 7 to export/visualize a tree
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
- `xgboost_version = '2.1'` — train with a current XGBoost library instead of the default

> **The `xgboost_version` default is `0.9`** — a 2019 release — and omitting the option gets you that, on every boosted-tree and random-forest model type. `'2.1'` reached GA on 2026-08-27. It is set here because it changes what `EXPORT MODEL` writes in Step 7: a modern `model.ubj` that current `xgboost` can read directly, instead of a legacy `model.bst` that needs a pinned old library. Accepted values are `0.9`, `1.1`, and `2.1`. It also has one measured cost — `ML.TRAINING_INFO` comes back empty for this model — documented in full in Step 6.

> Training takes several minutes: the first boosting iteration pays a large one-time data-loading/indexing cost, then each subsequent iteration is fast. Don't be alarmed by a slow first iteration in `ML.TRAINING_INFO` (Step 6) — that's expected, not a stall.

```python
query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.boosted_tree_classifier_income`
OPTIONS(
  model_type = 'BOOSTED_TREE_CLASSIFIER',
  xgboost_version = '2.1',
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
print('Model boosted_tree_classifier_income created')
```

---
## Step 2 — Evaluate with `ML.EVALUATE`

`ML.EVALUATE` returns standard classification metrics on the automatically held-out evaluation split: precision, recall, accuracy, F1, log loss, and ROC AUC. Compare `roc_auc` against the `models/logistic_regression` (Logistic Regression) notebook, which trains on the exact same data.

```python
query = f"""
SELECT *
FROM ML.EVALUATE(MODEL `{PROJECT_ID}.{DATASET_ID}.boosted_tree_classifier_income`)
"""
client.query(query).to_dataframe()
```

---
## Step 3 — Confusion matrix and ROC curve

`ML.CONFUSION_MATRIX` shows counts of predicted vs. actual classes. `ML.ROC_CURVE` returns the recall / false-positive-rate tradeoff across thresholds — useful for choosing an operating point.

```python
query = f"""
SELECT *
FROM ML.CONFUSION_MATRIX(MODEL `{PROJECT_ID}.{DATASET_ID}.boosted_tree_classifier_income`)
"""
client.query(query).to_dataframe()
```

```python
import matplotlib.pyplot as plt

query = f"""
SELECT threshold, recall, false_positive_rate
FROM ML.ROC_CURVE(MODEL `{PROJECT_ID}.{DATASET_ID}.boosted_tree_classifier_income`)
ORDER BY threshold
"""
roc = client.query(query).to_dataframe()

fig, ax = plt.subplots(figsize=(6, 6))
ax.plot(roc['false_positive_rate'], roc['recall'], color='#4285F4', linewidth=2, label='ROC curve')
ax.plot([0, 1], [0, 1], color='gray', linestyle='--', alpha=0.6, label='Random')
ax.set_xlabel('False Positive Rate')
ax.set_ylabel('True Positive Rate (Recall)')
ax.set_title('ROC Curve - Boosted Tree Classifier')
ax.legend(loc='lower right')
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()
```

---
## Step 4 — Predict with `ML.PREDICT`

`ML.PREDICT` scores new rows. It returns `predicted_income_bracket` (the chosen class) and `predicted_income_bracket_probs` (the probability of each class) — the same output shape as the logistic regression notebook.

```python
query = f"""
SELECT
  predicted_income_bracket,
  predicted_income_bracket_probs,
  age, occupation, education
FROM ML.PREDICT(
  MODEL `{PROJECT_ID}.{DATASET_ID}.boosted_tree_classifier_income`,
  (SELECT * FROM `bigquery-public-data.ml_datasets.census_adult_income` LIMIT 10)
)
"""
client.query(query).to_dataframe()
```

---
## Step 5 — Explain predictions

- **`ML.EXPLAIN_PREDICT`** — per-row feature attributions (which features pushed *this* prediction up or down)
- **`ML.GLOBAL_EXPLAIN`** — overall feature importance across the model (Shapley-style; requires `enable_global_explain = TRUE`)
- **`ML.FEATURE_IMPORTANCE`** — tree-specific, split-based importance (`weight`/`gain`/`cover`). This function only applies to tree ensembles (boosted tree, random forest) — GLMs (like logistic regression) don't have it; use `ML.WEIGHTS`/`ML.GLOBAL_EXPLAIN` instead.

`ML.GLOBAL_EXPLAIN` and `ML.FEATURE_IMPORTANCE` can rank features differently — that's expected, not a bug. They measure different things: attribution (contribution to predictions) vs. how often/effectively the trees actually split on a feature.

```python
query = f"""
SELECT
  predicted_income_bracket,
  top_feature_attributions
FROM ML.EXPLAIN_PREDICT(
  MODEL `{PROJECT_ID}.{DATASET_ID}.boosted_tree_classifier_income`,
  (SELECT * FROM `bigquery-public-data.ml_datasets.census_adult_income` LIMIT 5),
  STRUCT(5 AS top_k_features)
)
"""
client.query(query).to_dataframe()
```

```python
query = f"""
SELECT *
FROM ML.GLOBAL_EXPLAIN(MODEL `{PROJECT_ID}.{DATASET_ID}.boosted_tree_classifier_income`)
ORDER BY attribution DESC
"""
client.query(query).to_dataframe()
```

```python
query = f"""
SELECT *
FROM ML.FEATURE_IMPORTANCE(MODEL `{PROJECT_ID}.{DATASET_ID}.boosted_tree_classifier_income`)
ORDER BY importance_gain DESC
"""
client.query(query).to_dataframe()
```

---
## Step 6 — Introspect the model

`ML.FEATURE_INFO` reports the statistics each feature had during training.

`ML.TRAINING_INFO` normally returns the per-iteration loss curve, with iteration numbering starting at **1** for tree models (not 0, as in the GLM notebooks). Here it comes back **empty** — a direct consequence of `xgboost_version = '2.1'` in Step 1.

> **GOTCHA (measured, undocumented) — at `xgboost_version = '2.1'`, `ML.TRAINING_INFO` returns zero rows once training runs more than 10 iterations.** Nothing else about the model is affected: `CREATE MODEL` succeeds, and `ML.EVALUATE`, `ML.PREDICT`, `ML.EXPLAIN_PREDICT`, `ML.FEATURE_IMPORTANCE` and `ML.GLOBAL_EXPLAIN` all work on it — Steps 2–5 above are that proof. Only the training history is missing.
>
> Isolated with single-variable probes on the same data, `early_stop = FALSE`, everything else held constant:
>
> | `xgboost_version` | `max_iterations` | rows returned |
> |---|---|---|
> | `0.9` (the default) | 20 | 20 |
> | `1.1` | 20 | 20 |
> | `2.1` | 5 | 5 |
> | `2.1` | 10 | 10 |
> | `2.1` | 11 | **0** |
> | `2.1` | 20 | **0** |
>
> The boundary is exactly 10. It isn't early stopping — the probes above disable it, and the default `early_stop = TRUE` behaves the same way — and it isn't `auto_class_weights` or `enable_global_explain`, both of which return rows normally at `'2.1'` with `max_iterations = 5`. This model uses the default `max_iterations = 20` and trains past 10, so the curve is gone.
>
> **The trade-off on a boosted tree is one or the other:** a modern `model.ubj` export (Step 7) or a readable loss curve. To get the curve back, omit `xgboost_version` — returning to the `0.9` default, where this same model reports 9 iterations before early stopping — or hold training to 10 iterations or fewer. This notebook keeps `'2.1'` and accepts the empty result as the documented cost.
>
> `RANDOM_FOREST_*` is unaffected: training there is single-pass, so it never reaches the boundary — `models/random_forest_classifier` (Random Forest Classifier) sets `'2.1'` and still reports its one `ML.TRAINING_INFO` row.

```python
query = f"""
SELECT *
FROM ML.FEATURE_INFO(MODEL `{PROJECT_ID}.{DATASET_ID}.boosted_tree_classifier_income`)
"""
client.query(query).to_dataframe()
```

```python
query = f"""
SELECT iteration, loss, eval_loss, learning_rate, duration_ms
FROM ML.TRAINING_INFO(MODEL `{PROJECT_ID}.{DATASET_ID}.boosted_tree_classifier_income`)
ORDER BY iteration
"""
client.query(query).to_dataframe()
```

---
## Step 7 — Visualize a tree by exporting the model

`EXPORT MODEL` writes the trained ensemble to Cloud Storage as an XGBoost Booster file. Downloading it and loading it with the `xgboost` Python library lets you plot an individual tree's structure.

**The filename depends on `xgboost_version`, and so does how much trouble this step is.** Verified both ways on the same model:

| | default `'0.9'` | `'2.1'` (used here) |
|---|---|---|
| File written | `model.bst`, a legacy binary format | `model.ubj`, UBJSON |
| Current `xgboost` (3.x) can load it | **No** — `load_model()` raises `Check failed: str[0] == '{'` | **Yes** |
| Python dependency | pin `xgboost==1.7.6` | none — whatever `pip install xgboost` gives you |
| Warnings on load | an `XGBoost < 1.0.0` compatibility warning | none |

So Step 1's one extra option is what lets the cell below install a plain, unpinned `xgboost`. If you train without it, download `model.bst` instead and pin the old library.

> **GOTCHA (verified) — feature names aren't preserved, and `'2.1'` does not fix this one.** The loaded booster's `feature_names` comes back `None` at either version. Set it manually to the training query's non-label column order — this assumes a 1:1 mapping between `SELECT` column order and the booster's internal feature index, which held up when checked against the actual split thresholds below.
> 
> Rendering also requires the system `graphviz` package (the `dot` binary) — pre-installed in Google Colab; elsewhere run `!apt-get install -y graphviz`.

```python
query = f"""
EXPORT MODEL `{PROJECT_ID}.{DATASET_ID}.boosted_tree_classifier_income`
OPTIONS (URI = 'gs://{BUCKET}/bq_ml/boosted_tree_classifier/model')
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

local_dir = '/tmp/boosted_tree_classifier_export'
os.makedirs(local_dir, exist_ok=True)

storage_client = storage.Client(project=PROJECT_ID)
bucket = storage_client.bucket(BUCKET)
blob = bucket.blob('bq_ml/boosted_tree_classifier/model/model.ubj')
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
    'age', 'workclass', 'education', 'education_num', 'marital_status',
    'occupation', 'relationship', 'race', 'sex', 'hours_per_week', 'native_country',
]

fig, ax = plt.subplots(figsize=(28, 14))
xgb.plot_tree(booster, tree_idx=0, ax=ax)
plt.title('Boosted Tree Classifier - Tree 0 of the ensemble')
plt.tight_layout()
plt.show()
```

---
## Step 8 — In-model preprocessing with the `TRANSFORM` clause

The `TRANSFORM` clause bakes preprocessing into the model. Whatever you do in `TRANSFORM` is **saved with the model and reapplied automatically at predict time** — so `ML.PREDICT` takes raw data, with no need to repeat the preprocessing.

Here we quantile-bucketize `age` into 10 bins instead of using it as a raw numeric feature. `ML.QUANTILE_BUCKETIZE` is an analytic function, so it requires an empty `OVER()`. Notice the prediction query passes the raw, un-bucketized `age` column.

```python
query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.boosted_tree_classifier_income_transform`
TRANSFORM(
  ML.QUANTILE_BUCKETIZE(age, 10) OVER() AS age_bucket,
  education, marital_status, occupation, relationship, hours_per_week, income_bracket
)
OPTIONS(
  model_type = 'BOOSTED_TREE_CLASSIFIER',
  xgboost_version = '2.1',
  input_label_cols = ['income_bracket'],
  auto_class_weights = TRUE
) AS
SELECT age, education, marital_status, occupation, relationship, hours_per_week, income_bracket
FROM `bigquery-public-data.ml_datasets.census_adult_income`
"""
client.query(query).result()
print('Model boosted_tree_classifier_income_transform created')
```

```python
# Predict on RAW rows - bucketizing is applied automatically inside the model
query = f"""
SELECT predicted_income_bracket, age
FROM ML.PREDICT(
  MODEL `{PROJECT_ID}.{DATASET_ID}.boosted_tree_classifier_income_transform`,
  (SELECT * FROM `bigquery-public-data.ml_datasets.census_adult_income` LIMIT 5)
)
"""
client.query(query).to_dataframe()
```

---
## Step 9 — Hyperparameter tuning

BigQuery ML has built-in hyperparameter tuning. Set `num_trials` and define a search space with `HPARAM_RANGE` / `HPARAM_CANDIDATES`; BigQuery runs the trials and keeps the best model by `hparam_tuning_objectives`. Inspect every trial with `ML.TRIAL_INFO`.

Here we tune the boosting shrinkage (`learn_rate`) and tree depth (`max_tree_depth`). Training multiple trials takes a while.

> Individual trials can occasionally fail with a transient error (`ML.TRIAL_INFO.status = 'FAILED'`, e.g. "An internal error happened during trial training") — this shows up as a `NULL` objective metric for that trial. It does not fail the overall job; BigQuery keeps the best-performing *successful* trial as `is_optimal`. Check `status`/`error_message` if a trial looks off.

```python
query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.boosted_tree_classifier_income_tuned`
OPTIONS(
  model_type = 'BOOSTED_TREE_CLASSIFIER',
  xgboost_version = '2.1',
  input_label_cols = ['income_bracket'],
  auto_class_weights = TRUE,
  num_trials = 6,
  max_parallel_trials = 3,
  hparam_tuning_objectives = ['roc_auc'],
  learn_rate = HPARAM_RANGE(0.05, 0.3),
  max_tree_depth = HPARAM_RANGE(4, 8)
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
FROM ML.TRIAL_INFO(MODEL `{PROJECT_ID}.{DATASET_ID}.boosted_tree_classifier_income_tuned`)
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
FROM ML.EVALUATE(MODEL `statmike-mlops-349915.bq_ml.boosted_tree_classifier_income`)
```

---
## Examples — BigFrames

BigFrames provides a scikit-learn-style API (`bigframes.ml`) that trains BigQuery ML models under the hood. Here's the same boosted tree classifier with `bigframes.ml.ensemble.XGBClassifier`.

> **Not an apples-to-apples comparison with Step 2.** `bigframes.ml.ensemble.XGBClassifier` has **no `class_weight`/`auto_class_weights` parameter** (verified against the installed constructor signature) — unlike `bigframes.ml.linear_model.LogisticRegression`, which does expose sklearn-style `class_weight`. So this BigFrames model trains **without** the class balancing the SQL model in Step 1 uses, and its metrics will look different (typically higher precision, lower recall, on this ~76/24 imbalanced label) — that's the missing class weighting, not a bug.

```python
import bigframes.pandas as bpd

bpd.close_session()  # Reset session to apply project/location settings
bpd.options.bigquery.project = PROJECT_ID
bpd.options.bigquery.location = LOCATION
```

```python
from bigframes.ml.ensemble import XGBClassifier

# Load data as a BigFrames DataFrame
df = bpd.read_gbq('bigquery-public-data.ml_datasets.census_adult_income')

feature_cols = ['age', 'workclass', 'education', 'education_num', 'marital_status',
                'occupation', 'relationship', 'race', 'sex', 'hours_per_week', 'native_country']
X = df[feature_cols]
y = df['income_bracket']

# Train (creates a BigQuery ML model behind the scenes)
model = XGBClassifier()
model.fit(X, y)

# Evaluate
model.score(X, y).to_pandas()
```
