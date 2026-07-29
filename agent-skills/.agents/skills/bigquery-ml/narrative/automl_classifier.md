# AutoML Classifier — BigQuery ML

Train a **binary classification** model with `CREATE MODEL` (model_type = `AUTOML_CLASSIFIER`) — a BigQuery ML wrapper around Vertex AI AutoML Tables. AutoML searches architectures, engineers features, and tunes hyperparameters internally; you supply training data, a label column, and a time budget.

**Lifecycle:** `CREATE MODEL` → `ML.EVALUATE` → `ML.CONFUSION_MATRIX` / `ML.ROC_CURVE` → `ML.PREDICT` → `ML.GLOBAL_EXPLAIN` → `ML.FEATURE_INFO` / `ML.TRAINING_INFO` → `EXPORT MODEL` → confirm unsupported functions

**Ninth model type built in Phase 2 (core supervised models) — closes out the classifier/regressor pairs in this phase.**

**When to use AutoML instead of `LOGISTIC_REG`/`BOOSTED_TREE_CLASSIFIER`/`DNN_CLASSIFIER`/etc.:**
- You want the strongest tabular baseline without choosing or tuning an algorithm yourself.
- You can trade a longer, real-dollar-cost training job (1–72 hours of `budget_hours`) for accuracy.
- You want a model you can export and serve on Vertex AI endpoints.
- You do **not** need fast, iterative, in-BigQuery retraining — every other model type in this project trains in seconds to tens of minutes; AutoML's minimum is 1 hour of budget and, verified below, took much longer than that in wall-clock time.

> ### ⚠️ Cost and time — read before running
> **This is the first model type in this project with real, substantial dollar cost.** Every other notebook trains for free (or near-free) inside BigQuery's own compute. `AUTOML_CLASSIFIER` instead launches a Vertex AI AutoML Tables training job, billed at roughly **$21.25/node-hour** ([Vertex AI pricing](https://cloud.google.com/vertex-ai/pricing)). At `budget_hours = 1.0` (the minimum allowed):
> - **Cost:** roughly **$21–32** for this one `CREATE MODEL` call (the wall-clock overrun below is compression/data-movement overhead, not additional billed AutoML search time, per Google's own pricing model — not independently verified against an actual invoice).
> - **Wall-clock time, verified on this exact run:** `ML.TRAINING_INFO`'s `duration_ms` reported **9,475,200 ms ≈ 2.63 hours** for `budget_hours = 1.0` — a much larger overrun than the ~50% ceiling implied by Google's own documentation (which would cap this at ~1.5 hours). Budget accordingly; a "1-hour" AutoML job can plausibly take over 2.5 hours wall-clock.
> - Do not re-run Step 1 casually, and do not raise `budget_hours` without deliberately deciding to spend more.
>
> This SQL was validated for syntax only via `bq query --dry_run` (free, no training triggered) before being placed in this notebook.

**Data:** [`bigquery-public-data.ml_datasets.census_adult_income`](https://console.cloud.google.com/marketplace/product/bigquery-public-datasets) — same data and label (`income_bracket`) as `models/logistic_regression` (Logistic Regression), `models/boosted_tree_classifier` (Boosted Tree Classifier), `models/random_forest_classifier` (Random Forest Classifier), `models/dnn_classifier` (DNN Classifier), and `models/wide_and_deep_classifier` (Wide & Deep Classifier) — for direct comparison.

**References:** `RESOURCES.md` (Full reference) | [CREATE MODEL (AutoML) docs](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-automl) | [Vertex AI AutoML Tabular overview](https://cloud.google.com/vertex-ai/docs/tabular-data/classification-regression/overview) | `setup` (Setup guide)

---
## Setup

Set your project and location, authenticate, and create a shared dataset for the model.

> AutoML models train through a BigQuery `ML_EXTERNAL` job that invokes Vertex AI on your behalf -- no `CREATE CONNECTION` object is needed, but the Vertex AI API must be enabled in the project. See the `setup` (Setup Reference) for details.

```python
PROJECT_ID = 'statmike-mlops-349915'  # <-- Replace with your project ID
LOCATION = 'US'  # BigQuery dataset location
DATASET_ID = 'bq_ml'  # Shared dataset across all bq-ml notebooks
BUCKET = 'statmike-mlops-349915'  # <-- Replace with your GCS bucket (same location as DATASET_ID) -- used to EXPORT MODEL
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

`model_type` + `input_label_cols` are the essentials, same as any other model type. `budget_hours` is AutoML's one user-facing tuning knob — there is no `num_trials` / `HPARAM_RANGE` here; AutoML searches architectures and hyperparameters internally. `optimization_objective = 'MAXIMIZE_AU_ROC'` is the classifier default, made explicit here.

**This cell trains for real on Vertex AI — verified on this run: ~2.63 hours wall-clock (see the warning above) and an estimated ~$21–32.**

```python
query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.automl_classifier_income`
OPTIONS(
  model_type = 'AUTOML_CLASSIFIER',
  input_label_cols = ['income_bracket'],
  budget_hours = 1.0,
  optimization_objective = 'MAXIMIZE_AU_ROC'
) AS
SELECT
  age, workclass, education, education_num, marital_status, occupation,
  relationship, race, sex, hours_per_week, native_country, income_bracket
FROM `bigquery-public-data.ml_datasets.census_adult_income`
"""
client.query(query).result()
print('Model automl_classifier_income created')
```

---
## Step 2 — Evaluate with `ML.EVALUATE`

Same metric set as `LOGISTIC_REG`/`BOOSTED_TREE_CLASSIFIER`/etc: precision, recall, accuracy, F1, log loss, ROC AUC — computed by AutoML on its own internal test split.

> **GOTCHA (verified): the zero-argument `ML.EVALUATE`'s `accuracy` for this model type is not a literal, reconcilable confusion-matrix accuracy — treat it with caution.** The real run below reports `accuracy=0.5` exactly, alongside a strong `roc_auc=0.930`. Digging into the model's own metadata (`bq show --model`) confirms this evaluation ran against a **class-balanced ~6,416-row internal eval set (3,208 per class)**, not the natural ~76%/24% `income_bracket` split — expected, since AutoML manages its own splitting. But the reported `accuracy=0.5`/`precision=0.531`/`recall=0.509` don't match **any** of the model's own 203 confidence-threshold rows in `binaryConfusionMatrixList` (whose accuracy ranges from 0.5 at extreme thresholds up to ~0.845 at moderate ones — the literal threshold-0.5 row shows `accuracy=0.844`, not `0.5`). In other words, the aggregate metrics BigQuery surfaces here don't reduce to "the confusion matrix at threshold 0.5" the way they do for every native BQML classifier in this project — the exact Vertex AI methodology behind this aggregate isn't visible from BigQuery's side. **Passing an explicit data argument sidesteps the ambiguity entirely** — `ML.EVALUATE(MODEL ..., (SELECT ...))` against the model's own training table returns a standard, self-consistent `accuracy=0.8508`, matching a directly-computed confusion matrix over that same table exactly (confirmed: 27,703 correct / 32,561 total). Prefer `roc_auc`/`log_loss` (threshold-independent) or an explicit-data-argument call when evaluating this model type — don't take the zero-argument `accuracy` at face value.

```python
query = f"""
SELECT *
FROM ML.EVALUATE(MODEL `{PROJECT_ID}.{DATASET_ID}.automl_classifier_income`)
"""
client.query(query).to_dataframe()
```

---
## Step 3 — Confusion matrix and ROC curve

> **GOTCHA (verified):** the zero-argument form `ML.CONFUSION_MATRIX(MODEL ...)` — which relies on AutoML's own internal held-out eval split, and which works fine for `ML.EVALUATE`/`ML.ROC_CURVE` — fails immediately and consistently for this model type with a generic internal error (`Error: 21631273`, "This is usually caused by a transient issue"). It is **not actually transient**: it reproduces on every attempt. Worse, `google-cloud-bigquery`'s default client-side retry logic treats this error as retryable and keeps resubmitting with exponential backoff, so the cell appears to hang rather than fail fast. **Fix: pass an explicit data argument** — `ML.CONFUSION_MATRIX(MODEL ..., (SELECT ...))` — which works normally (confirmed against the same training table in a few seconds). This is specific to `ML.CONFUSION_MATRIX`; `ML.ROC_CURVE`'s zero-argument form works fine on the same model, confirmed below.

```python
query = f"""
SELECT *
FROM ML.CONFUSION_MATRIX(
  MODEL `{PROJECT_ID}.{DATASET_ID}.automl_classifier_income`,
  (SELECT age, workclass, education, education_num, marital_status, occupation,
          relationship, race, sex, hours_per_week, native_country, income_bracket
   FROM `bigquery-public-data.ml_datasets.census_adult_income`)
)
"""
client.query(query).to_dataframe()
```

```python
import matplotlib.pyplot as plt

query = f"""
SELECT threshold, recall, false_positive_rate
FROM ML.ROC_CURVE(MODEL `{PROJECT_ID}.{DATASET_ID}.automl_classifier_income`)
ORDER BY threshold
"""
roc = client.query(query).to_dataframe()

fig, ax = plt.subplots(figsize=(6, 6))
ax.plot(roc['false_positive_rate'], roc['recall'], color='#4285F4', linewidth=2, label='ROC curve')
ax.plot([0, 1], [0, 1], color='gray', linestyle='--', alpha=0.6, label='Random')
ax.set_xlabel('False Positive Rate')
ax.set_ylabel('True Positive Rate (Recall)')
ax.set_title('ROC Curve - AutoML Classifier')
ax.legend(loc='lower right')
plt.show()
```

---
## Step 4 — Predict with `ML.PREDICT`

```python
query = f"""
SELECT
  predicted_income_bracket,
  predicted_income_bracket_probs,
  age, occupation, education
FROM ML.PREDICT(
  MODEL `{PROJECT_ID}.{DATASET_ID}.automl_classifier_income`,
  (SELECT * FROM `bigquery-public-data.ml_datasets.census_adult_income` LIMIT 10)
)
"""
client.query(query).to_dataframe()
```

---
## Step 5 — Explain with `ML.GLOBAL_EXPLAIN`

Unlike `LOGISTIC_REG`/`BOOSTED_TREE_*`, no `enable_global_explain` option was needed at `CREATE MODEL` time — AutoML produces attributions automatically. Only model-level (not per-prediction) explanations are available for this model type: `ML.EXPLAIN_PREDICT` is **not supported** (confirmed in Step 8).

```python
query = f"""
SELECT *
FROM ML.GLOBAL_EXPLAIN(MODEL `{PROJECT_ID}.{DATASET_ID}.automl_classifier_income`)
ORDER BY attribution DESC
"""
client.query(query).to_dataframe()
```

---
## Step 6 — Introspect the model

`ML.FEATURE_INFO` reports the statistics each feature had during training. `ML.TRAINING_INFO` returns per-iteration training info — for an AutoML model this reflects Vertex AI's internal training process rather than a simple iteration-by-iteration loss curve, since AutoML manages the search itself.

```python
query = f"""
SELECT *
FROM ML.FEATURE_INFO(MODEL `{PROJECT_ID}.{DATASET_ID}.automl_classifier_income`)
"""
client.query(query).to_dataframe()
```

```python
query = f"""
SELECT *
FROM ML.TRAINING_INFO(MODEL `{PROJECT_ID}.{DATASET_ID}.automl_classifier_income`)
"""
client.query(query).to_dataframe()
```

---
## Step 7 — Export with `EXPORT MODEL`

Writes the trained AutoML model to Cloud Storage for Vertex AI Model Registry / custom serving. Unlike `BOOSTED_TREE_*`/`RANDOM_FOREST_*`, AutoML's exported artifact is an opaque ensemble — there is no single tree/booster file to load and visualize with a local library, so this step just confirms the export lands in Cloud Storage.

```python
query = f"""
EXPORT MODEL `{PROJECT_ID}.{DATASET_ID}.automl_classifier_income`
OPTIONS (URI = 'gs://{BUCKET}/bq_ml/automl_classifier/model')
"""
client.query(query).result()
print('Model exported')
```

```python
from google.cloud import storage

storage_client = storage.Client(project=PROJECT_ID)
bucket = storage_client.bucket(BUCKET)
blobs = list(bucket.list_blobs(prefix='bq_ml/automl_classifier/model'))
for blob in blobs:
    print(blob.name)
```

---
## Step 8 — Functions that do NOT apply to this model type

- **`TRANSFORM`** is not supported for AutoML model types — do any custom feature engineering in the training `SELECT` instead.
- **`ML.WEIGHTS` / `ML.ADVANCED_WEIGHTS`** do not apply — AutoML is not a single linear/tree model with an exposable weight vector.
- **`ML.EXPLAIN_PREDICT`** does not apply — use `ML.GLOBAL_EXPLAIN` (Step 5) for feature attributions instead.
- User-configurable hyperparameter tuning (`num_trials` / `HPARAM_RANGE` / `HPARAM_CANDIDATES`) is also not supported — `budget_hours` is the only lever.

Each cell below is expected to fail; the error text is captured live.

```python
# TRANSFORM — expected to fail
try:
    query = f"""
    CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.automl_classifier_income_transform`
    TRANSFORM(age, income_bracket)
    OPTIONS(
      model_type = 'AUTOML_CLASSIFIER',
      input_label_cols = ['income_bracket'],
      budget_hours = 1.0
    ) AS
    SELECT age, income_bracket
    FROM `bigquery-public-data.ml_datasets.census_adult_income`
    """
    client.query(query).result()
except Exception as e:
    print(f'TRANSFORM failed as expected:\n{e}')
```

```python
# ML.WEIGHTS — expected to fail
try:
    query = f"""SELECT * FROM ML.WEIGHTS(MODEL `{PROJECT_ID}.{DATASET_ID}.automl_classifier_income`)"""
    client.query(query).result()
except Exception as e:
    print(f'ML.WEIGHTS failed as expected:\n{e}')
```

```python
# ML.EXPLAIN_PREDICT — expected to fail
try:
    query = f"""
    SELECT *
    FROM ML.EXPLAIN_PREDICT(
      MODEL `{PROJECT_ID}.{DATASET_ID}.automl_classifier_income`,
      (SELECT * FROM `bigquery-public-data.ml_datasets.census_adult_income` LIMIT 5)
    )
    """
    client.query(query).result()
except Exception as e:
    print(f'ML.EXPLAIN_PREDICT failed as expected:\n{e}')
```

---
## Examples — `%%bigquery` Magics

The same operations using IPython magic commands — write SQL directly in cells without Python string wrapping.

### Evaluate with `%%bigquery`

```sql
%%bigquery --project {PROJECT_ID}

SELECT *
FROM ML.EVALUATE(MODEL `statmike-mlops-349915.bq_ml.automl_classifier_income`)
```

---
## BigFrames

**No direct BigFrames AutoML estimator exists** (checked the live BigFrames API reference across `bigframes.ml.linear_model`, `.ensemble`, `.cluster`, `.decomposition`, `.forecasting`, `.imported`, `.llm` — no `AutoML*` class anywhere in the package, the same permanent gap as `DNN_CLASSIFIER`/`WIDE_AND_DEEP_CLASSIFIER`). Use the SQL `CREATE MODEL` interface shown above.
