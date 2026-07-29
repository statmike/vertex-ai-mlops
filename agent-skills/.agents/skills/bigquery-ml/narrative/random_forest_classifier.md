# Random Forest Classifier — BigQuery ML

Train a **binary classification** model with `CREATE MODEL` (model_type = `RANDOM_FOREST_CLASSIFIER`) — a bagged ensemble of decision trees powered by XGBoost — then walk the full model lifecycle: evaluate, predict, explain, inspect feature importance, visualize a tree, apply in-model preprocessing, and tune hyperparameters. No data leaves BigQuery, and no separate training infrastructure is needed.

**Lifecycle:** `CREATE MODEL` → `ML.EVALUATE` → `ML.CONFUSION_MATRIX` / `ML.ROC_CURVE` → `ML.PREDICT` → `ML.EXPLAIN_PREDICT` → `ML.GLOBAL_EXPLAIN` / `ML.FEATURE_IMPORTANCE` → `ML.FEATURE_INFO` / `ML.TRAINING_INFO` → `EXPORT MODEL` (tree visualization) → `TRANSFORM` clause → hyperparameter tuning (`ML.TRIAL_INFO`)

**When to use a random forest classifier:**
- A robust, low-tuning ensemble that resists overfitting via bagging (row + column subsampling per tree)
- Structured/tabular data — compare `roc_auc` directly against `models/logistic_regression` (Logistic Regression) and `models/boosted_tree_classifier` (Boosted Tree Classifier) on the same data
- You want built-in feature attributions plus split-based feature importance (`ML.FEATURE_IMPORTANCE`)
- As a variance-reduction alternative when boosting overfits

**Random forest vs. boosted tree:** both are XGBoost-based tree ensembles in BigQuery ML, but they train fundamentally differently. A random forest builds `num_parallel_tree` complete, independent trees in a **single pass** (bagging) and averages them — `max_iterations` is not even a valid option for this model type. A boosted tree sequentially fits many *shallow* trees to the residuals of the previous ones, shrinking each contribution (`learn_rate`). This shows up concretely in `ML.TRAINING_INFO` (Step 6): random forest always has exactly one iteration with `learning_rate = 1.0`.

**Data:** [`bigquery-public-data.ml_datasets.census_adult_income`](https://console.cloud.google.com/marketplace/product/bigquery-public-datasets) — predict whether income exceeds $50K/year from census attributes. **Same data + label as `models/logistic_regression` (Logistic Regression) and `models/boosted_tree_classifier` (Boosted Tree Classifier)** — compare `roc_auc` across all three techniques.

**References:** `RESOURCES.md` (Full reference) | [CREATE MODEL (random forest) docs](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-random-forest) | `setup` (Setup guide)

---
## Setup

Set your project and location, authenticate, and create a shared dataset for the model.

> Random forests train on data already in BigQuery — no connection or remote model required. The model is created with `CREATE MODEL` and stored in your dataset. See the `setup` (Setup Reference) for details.

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
- `num_parallel_tree = 50` — the number of trees in the forest, trained in parallel on row/column subsamples
- `auto_class_weights = TRUE` — balance the classes (the data is ~76% `<=50K`)
- `data_split_method = 'AUTO_SPLIT'` — automatically hold out rows for evaluation
- `enable_global_explain = TRUE` — **required** to use `ML.GLOBAL_EXPLAIN` later

> **Gotcha (verified):** `max_iterations` is **not a valid option for `RANDOM_FOREST_*` at all** — `CREATE MODEL` errors immediately with `Option(s) MAX_ITERATIONS are not supported for RANDOM_FOREST_CLASSIFIER model training` if you set it. Unlike `BOOSTED_TREE_*`, where `max_iterations` is a central hyperparameter, `num_parallel_tree` alone defines the forest — training is single-pass by API-level guarantee, not just convention.

```python
query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.random_forest_classifier_income`
OPTIONS(
  model_type = 'RANDOM_FOREST_CLASSIFIER',
  input_label_cols = ['income_bracket'],
  num_parallel_tree = 50,
  tree_method = 'HIST',
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
print('Model random_forest_classifier_income created')
```

---
## Step 2 — Evaluate with `ML.EVALUATE`

`ML.EVALUATE` returns standard classification metrics on the automatically held-out evaluation split: precision, recall, accuracy, F1, log loss, and ROC AUC. Compare `roc_auc` against `models/logistic_regression` (Logistic Regression) and `models/boosted_tree_classifier` (Boosted Tree Classifier), which train on the exact same data.

```python
query = f"""
SELECT *
FROM ML.EVALUATE(MODEL `{PROJECT_ID}.{DATASET_ID}.random_forest_classifier_income`)
"""
client.query(query).to_dataframe()
```

---
## Step 3 — Confusion matrix and ROC curve

`ML.CONFUSION_MATRIX` shows counts of predicted vs. actual classes. `ML.ROC_CURVE` returns the recall / false-positive-rate tradeoff across thresholds — useful for choosing an operating point.

```python
query = f"""
SELECT *
FROM ML.CONFUSION_MATRIX(MODEL `{PROJECT_ID}.{DATASET_ID}.random_forest_classifier_income`)
"""
client.query(query).to_dataframe()
```

```python
import matplotlib.pyplot as plt

query = f"""
SELECT threshold, recall, false_positive_rate
FROM ML.ROC_CURVE(MODEL `{PROJECT_ID}.{DATASET_ID}.random_forest_classifier_income`)
ORDER BY threshold
"""
roc = client.query(query).to_dataframe()

fig, ax = plt.subplots(figsize=(6, 6))
ax.plot(roc['false_positive_rate'], roc['recall'], color='#4285F4', linewidth=2, label='ROC curve')
ax.plot([0, 1], [0, 1], color='gray', linestyle='--', alpha=0.6, label='Random')
ax.set_xlabel('False Positive Rate')
ax.set_ylabel('True Positive Rate (Recall)')
ax.set_title('ROC Curve - Random Forest Classifier')
ax.legend(loc='lower right')
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()
```

---
## Step 4 — Predict with `ML.PREDICT`

`ML.PREDICT` scores new rows. It returns `predicted_income_bracket` (the chosen class) and `predicted_income_bracket_probs` (the probability of each class).

```python
query = f"""
SELECT
  predicted_income_bracket,
  predicted_income_bracket_probs
FROM ML.PREDICT(
  MODEL `{PROJECT_ID}.{DATASET_ID}.random_forest_classifier_income`,
  (SELECT * FROM `bigquery-public-data.ml_datasets.census_adult_income` LIMIT 10)
)
"""
client.query(query).to_dataframe()
```

---
## Step 5 — Explain predictions

- **`ML.EXPLAIN_PREDICT`** — per-row feature attributions
- **`ML.GLOBAL_EXPLAIN`** — overall feature importance across the model (Shapley-style; requires `enable_global_explain = TRUE`)
- **`ML.FEATURE_IMPORTANCE`** — tree-specific, split-based importance (`weight`/`gain`/`cover`). Neither this nor `ML.GLOBAL_EXPLAIN` applies to GLMs (see `models/logistic_regression` (Logistic Regression)) — use `ML.WEIGHTS` there instead.

`ML.GLOBAL_EXPLAIN` and `ML.FEATURE_IMPORTANCE` can rank features differently — expected, not a bug (attribution vs. split-based usage).

```python
query = f"""
SELECT
  predicted_income_bracket,
  top_feature_attributions
FROM ML.EXPLAIN_PREDICT(
  MODEL `{PROJECT_ID}.{DATASET_ID}.random_forest_classifier_income`,
  (SELECT * FROM `bigquery-public-data.ml_datasets.census_adult_income` LIMIT 5),
  STRUCT(5 AS top_k_features)
)
"""
client.query(query).to_dataframe()
```

```python
query = f"""
SELECT *
FROM ML.GLOBAL_EXPLAIN(MODEL `{PROJECT_ID}.{DATASET_ID}.random_forest_classifier_income`)
ORDER BY attribution DESC
"""
client.query(query).to_dataframe()
```

```python
query = f"""
SELECT *
FROM ML.FEATURE_IMPORTANCE(MODEL `{PROJECT_ID}.{DATASET_ID}.random_forest_classifier_income`)
ORDER BY importance_gain DESC
"""
client.query(query).to_dataframe()
```

---
## Step 6 — Introspect the model

`ML.FEATURE_INFO` reports the statistics each feature had during training. `ML.TRAINING_INFO` returns the training loss — for a random forest this is always **exactly one row** (`iteration = 1`) with `learning_rate = 1.0`, confirming the single-pass bagging behavior noted in Step 1 (contrast with the multi-iteration, shrinking-learning-rate curve in `models/boosted_tree_classifier` (Boosted Tree Classifier)).

```python
query = f"""
SELECT *
FROM ML.FEATURE_INFO(MODEL `{PROJECT_ID}.{DATASET_ID}.random_forest_classifier_income`)
"""
client.query(query).to_dataframe()
```

```python
query = f"""
SELECT iteration, loss, eval_loss, learning_rate, duration_ms
FROM ML.TRAINING_INFO(MODEL `{PROJECT_ID}.{DATASET_ID}.random_forest_classifier_income`)
ORDER BY iteration
"""
client.query(query).to_dataframe()
```

---
## Step 7 — Visualize a tree by exporting the model

`EXPORT MODEL` writes a trained ensemble to Cloud Storage as an XGBoost Booster file (`model.bst`). Downloading it and loading it with the `xgboost` Python library lets you plot an individual tree's structure — same mechanism as `models/boosted_tree_classifier` (Boosted Tree Classifier), with the same two gotchas (pin `xgboost==1.7.6`; reassign `feature_names` manually).

> **A third, random-forest-specific gotcha (verified):** the main model above (`num_parallel_tree=50`, default `max_tree_depth=6`) produces trees that are **too dense to render meaningfully** — unlike a boosted tree's shallow early-round tree (fit on residuals), *every* random forest tree is a complete, independently-trained tree. Its tree 0 has 2,435 dump lines and depth 15; `xgboost.plot_tree()` triggers a `graph is too large for cairo-renderer bitmaps` warning and produces an illegible image.
>
> **Fix:** train a small, separate **illustrative forest** just for the diagram — fewer, shallower trees. This mirrors real practice: nobody eyeballs a full-depth production random forest tree either; `ML.FEATURE_IMPORTANCE` (Step 5) is the right tool for that. The illustrative forest below (`num_parallel_tree=10`, `max_tree_depth=3`) renders a clean, legible diagram.

```python
# A small, shallow forest -- for visualization only, not for metrics.
query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.random_forest_classifier_income_viz`
OPTIONS(
  model_type = 'RANDOM_FOREST_CLASSIFIER',
  input_label_cols = ['income_bracket'],
  num_parallel_tree = 10,
  max_tree_depth = 3
) AS
SELECT
  age, workclass, education, education_num, marital_status, occupation,
  relationship, race, sex, hours_per_week, native_country, income_bracket
FROM `bigquery-public-data.ml_datasets.census_adult_income`
"""
client.query(query).result()
print('Illustrative forest created')
```

```python
query = f"""
EXPORT MODEL `{PROJECT_ID}.{DATASET_ID}.random_forest_classifier_income_viz`
OPTIONS (URI = 'gs://{BUCKET}/bq_ml/random_forest_classifier/model_viz')
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

local_dir = '/tmp/random_forest_classifier_export'
os.makedirs(local_dir, exist_ok=True)

storage_client = storage.Client(project=PROJECT_ID)
bucket = storage_client.bucket(BUCKET)
blob = bucket.blob('bq_ml/random_forest_classifier/model_viz/model.bst')
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
    'age', 'workclass', 'education', 'education_num', 'marital_status',
    'occupation', 'relationship', 'race', 'sex', 'hours_per_week', 'native_country',
]

fig, ax = plt.subplots(figsize=(20, 10))
xgb.plot_tree(booster, num_trees=0, ax=ax)
plt.title('Random Forest Classifier - Tree 0 (shallow illustrative forest)')
plt.tight_layout()
plt.show()
```

---
## Step 8 — In-model preprocessing with the `TRANSFORM` clause

The `TRANSFORM` clause bakes preprocessing into the model. Whatever you do in `TRANSFORM` is **saved with the model and reapplied automatically at predict time**. Here we quantile-bucketize `age` into 10 bins instead of using it as a raw numeric feature. `ML.QUANTILE_BUCKETIZE` is an analytic function, so it requires an empty `OVER()`.

```python
query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.random_forest_classifier_income_transform`
TRANSFORM(
  ML.QUANTILE_BUCKETIZE(age, 10) OVER() AS age_bucket,
  education, marital_status, occupation, relationship, hours_per_week, income_bracket
)
OPTIONS(
  model_type = 'RANDOM_FOREST_CLASSIFIER',
  input_label_cols = ['income_bracket'],
  num_parallel_tree = 50,
  auto_class_weights = TRUE
) AS
SELECT age, education, marital_status, occupation, relationship, hours_per_week, income_bracket
FROM `bigquery-public-data.ml_datasets.census_adult_income`
"""
client.query(query).result()
print('Model random_forest_classifier_income_transform created')
```

```python
# Predict on RAW rows - bucketizing is applied automatically inside the model
query = f"""
SELECT predicted_income_bracket, age
FROM ML.PREDICT(
  MODEL `{PROJECT_ID}.{DATASET_ID}.random_forest_classifier_income_transform`,
  (SELECT * FROM `bigquery-public-data.ml_datasets.census_adult_income` LIMIT 5)
)
"""
client.query(query).to_dataframe()
```

---
## Step 9 — Hyperparameter tuning

Tune the forest size (`num_parallel_tree`) and tree depth (`max_tree_depth`). BigQuery runs the trials and keeps the best model by `hparam_tuning_objectives`. Inspect every trial with `ML.TRIAL_INFO`.

> Individual trials can occasionally fail with a transient error (`ML.TRIAL_INFO.status = 'FAILED'`) — this shows up as a `NULL` objective metric for that trial without failing the overall job. Check `status`/`error_message` if a trial looks off.

```python
query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.random_forest_classifier_income_tuned`
OPTIONS(
  model_type = 'RANDOM_FOREST_CLASSIFIER',
  input_label_cols = ['income_bracket'],
  auto_class_weights = TRUE,
  num_trials = 6,
  max_parallel_trials = 3,
  hparam_tuning_objectives = ['roc_auc'],
  num_parallel_tree = HPARAM_RANGE(20, 100),
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
FROM ML.TRIAL_INFO(MODEL `{PROJECT_ID}.{DATASET_ID}.random_forest_classifier_income_tuned`)
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
FROM ML.EVALUATE(MODEL `statmike-mlops-349915.bq_ml.random_forest_classifier_income`)
```

---
## Examples — BigFrames

BigFrames provides a scikit-learn-style API (`bigframes.ml`) that trains BigQuery ML models under the hood. Here's the same random forest classifier with `bigframes.ml.ensemble.RandomForestClassifier`.

> **Not an apples-to-apples comparison with Step 2.** `bigframes.ml.ensemble.RandomForestClassifier` has **no `class_weight`/`auto_class_weights` parameter** (verified against the installed constructor signature) — the same gap found in `bigframes.ml.ensemble.XGBClassifier` (see `models/boosted_tree_classifier` (Boosted Tree Classifier)). This BigFrames model trains **without** the class balancing the SQL model in Step 1 uses, so expect different precision/recall on this imbalanced label — that's the missing class weighting, not a bug.

```python
import bigframes.pandas as bpd

bpd.close_session()  # Reset session to apply project/location settings
bpd.options.bigquery.project = PROJECT_ID
bpd.options.bigquery.location = LOCATION
```

```python
from bigframes.ml.ensemble import RandomForestClassifier

# Load data as a BigFrames DataFrame
df = bpd.read_gbq('bigquery-public-data.ml_datasets.census_adult_income')

feature_cols = ['age', 'workclass', 'education', 'education_num', 'marital_status',
                'occupation', 'relationship', 'race', 'sex', 'hours_per_week', 'native_country']
X = df[feature_cols]
y = df['income_bracket']

# Train (creates a BigQuery ML model behind the scenes)
model = RandomForestClassifier()
model.fit(X, y)

# Evaluate
model.score(X, y).to_pandas()
```
