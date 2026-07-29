# AutoML Regressor — BigQuery ML

Train a **regression** model with `CREATE MODEL` (model_type = `AUTOML_REGRESSOR`) — a BigQuery ML wrapper around Vertex AI AutoML Tables. AutoML searches architectures, engineers features, and tunes hyperparameters internally; you supply training data, a label column, and a time budget.

**Lifecycle:** `CREATE MODEL` → `ML.EVALUATE` → `ML.PREDICT` → `ML.GLOBAL_EXPLAIN` → `ML.FEATURE_INFO` / `ML.TRAINING_INFO` → `EXPORT MODEL` → confirm unsupported functions

**Tenth model type built in Phase 2 (core supervised models) — closes out Phase 2.**

**When to use AutoML instead of `LINEAR_REG`/`BOOSTED_TREE_REGRESSOR`/`DNN_REGRESSOR`/etc.:**
- You want the strongest tabular baseline without choosing or tuning an algorithm yourself.
- You can trade a longer, real-dollar-cost training job (1–72 hours of `budget_hours`) for accuracy.
- You want a model you can export and serve on Vertex AI endpoints.
- You do **not** need fast, iterative, in-BigQuery retraining — every other model type in this project trains in seconds to tens of minutes; AutoML's minimum is 1 hour of budget and, verified below, took much longer than that in wall-clock time.

> ### ⚠️ Cost and time — read before running
> **Real, substantial dollar cost**, same as `models/automl_classifier` (AutoML Classifier). `AUTOML_REGRESSOR` launches a Vertex AI AutoML Tables training job, billed at roughly **$21.25/node-hour** ([Vertex AI pricing](https://cloud.google.com/vertex-ai/pricing)). At `budget_hours = 1.0` (the minimum allowed):
> - **Cost:** roughly **$21–32** for this one `CREATE MODEL` call (compression/data-movement overhead below is not additional billed AutoML search time, per Google's own pricing model — not independently verified against an actual invoice).
> - **Wall-clock time, verified on this exact run:** `ML.TRAINING_INFO`'s `duration_ms` reported **8,103,600 ms ≈ 2.25 hours** for `budget_hours = 1.0` — a much larger overrun than the ~50% ceiling implied by Google's own documentation. `models/automl_classifier` (AutoML Classifier) on the same day took even longer (~2.63 hours) — budget at least 2-3 hours per AutoML run, not 1.5.
> - Do not re-run Step 1 casually, and do not raise `budget_hours` without deliberately deciding to spend more.
>
> This SQL was validated for syntax via `bq query --dry_run` before being placed in this notebook.

> ### ⚠️ GOTCHA (verified): AutoML Tables requires a minimum of 1,000 training rows
> Unlike the other five regressors in this project, this notebook does **not** use `penguins`/`body_mass_g`. A first attempt with `penguins` (~333 rows after filtering) failed immediately: `"Input data contains 333 rows. The minimum number of input rows for AutoML Tables models is 1000."` — this floor is not called out in the official `CREATE MODEL` (AutoML) reference and applies regardless of `budget_hours`. `models/automl_classifier` (AutoML Classifier) is unaffected (`census_adult_income` has ~32,000 rows).
>
> This notebook instead uses `bigquery-public-data.samples.natality` — Google's own canonical BQML regression tutorial dataset, predicting birth weight (`weight_pounds`) — filtered to Washington state, 2003 (~80,000 rows), comfortably clearing the minimum. This breaks direct row-for-row comparability with the other five regressors, but is required by the platform.

**Data:** [`bigquery-public-data.samples.natality`](https://console.cloud.google.com/marketplace/product/bigquery-public-datasets) — label `weight_pounds` (continuous, birth weight in pounds), filtered to `year = 2003` and `mother_residence_state = 'WA'` (79,993 rows after filtering out NULL label/`mother_age`/`gestation_weeks`/`plurality`). **Note (verified):** `cigarette_use` is NULL for 78,400 of those 79,993 rows (98%) — smoking status is essentially unrecorded for this state/year slice. This isn't a bug; it's consistent with `ML.GLOBAL_EXPLAIN` (Step 4) ranking `cigarette_use` as by far the least important feature (`attribution=0.0016`, next-lowest is `0.030`) — the model correctly learned to mostly ignore a near-constant/missing column.

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

`model_type` + `input_label_cols` are the essentials, same as any other model type. `budget_hours` is AutoML's one user-facing tuning knob — there is no `num_trials` / `HPARAM_RANGE` here; AutoML searches architectures and hyperparameters internally. `optimization_objective = 'MINIMIZE_RMSE'` is the regressor default, made explicit here.

**This cell trains for real on Vertex AI — verified on this run: ~2.25 hours wall-clock (see the warning above) and an estimated ~$21–32.**

```python
query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.automl_regressor_natality`
OPTIONS(
  model_type = 'AUTOML_REGRESSOR',
  input_label_cols = ['weight_pounds'],
  budget_hours = 1.0,
  optimization_objective = 'MINIMIZE_RMSE'
) AS
SELECT
  mother_age, gestation_weeks, plurality, is_male, mother_married, cigarette_use, weight_pounds
FROM `bigquery-public-data.samples.natality`
WHERE year = 2003
  AND mother_residence_state = 'WA'
  AND weight_pounds IS NOT NULL
  AND mother_age IS NOT NULL
  AND gestation_weeks IS NOT NULL
  AND plurality IS NOT NULL
"""
client.query(query).result()
print('Model automl_regressor_natality created')
```

---
## Step 2 — Evaluate with `ML.EVALUATE`

Same metric set as `LINEAR_REG`/`BOOSTED_TREE_REGRESSOR`/etc: mean absolute/squared error, mean squared log error, median absolute error, R^2, and explained variance — computed by AutoML on its own internal test split.

> **GOTCHA (verified): `median_absolute_error` and `explained_variance` both return exactly `0.0`, which does not look genuine.** `mean_absolute_error`, `mean_squared_error` (which matches `ML.TRAINING_INFO`'s `eval_loss` exactly — Step 5), `mean_squared_log_error`, and `r2_score=0.352` all look like real, internally-consistent values reflecting a model with genuine (if modest) predictive power — a `median_absolute_error` of exactly `0.0` (implying at least half the predictions are pixel-perfect on a continuous label) and an `explained_variance` of exactly `0.0` (which should track closely with a positive `r2_score`, not be zero) are implausible for this kind of regression. This parallels `models/automl_classifier` (AutoML Classifier)'s `ML.EVALUATE` aggregate-metric anomaly (Step 2 there) — some fields in the zero-argument evaluation aggregate for AutoML model types don't appear fully populated. **Unlike the classifier, this couldn't be root-caused further here**: by the time this was reviewed, Cleanup had already dropped the model, so `bq show --model`'s raw evaluation metadata (used to diagnose the classifier's anomaly) was no longer available. Treat `median_absolute_error`/`explained_variance` for `AUTOML_REGRESSOR` with the same skepticism as the classifier's `accuracy` — prefer `mean_squared_error`/`r2_score`/`mean_absolute_error`, which look trustworthy here.

```python
query = f"""
SELECT *
FROM ML.EVALUATE(MODEL `{PROJECT_ID}.{DATASET_ID}.automl_regressor_natality`)
"""
client.query(query).to_dataframe()
```

---
## Step 3 — Predict with `ML.PREDICT`

```python
query = f"""
SELECT
  predicted_weight_pounds,
  mother_age, gestation_weeks, plurality
FROM ML.PREDICT(
  MODEL `{PROJECT_ID}.{DATASET_ID}.automl_regressor_natality`,
  (SELECT mother_age, gestation_weeks, plurality, is_male, mother_married, cigarette_use, weight_pounds
   FROM `bigquery-public-data.samples.natality`
   WHERE year = 2003 AND mother_residence_state = 'WA'
     AND weight_pounds IS NOT NULL AND mother_age IS NOT NULL
     AND gestation_weeks IS NOT NULL AND plurality IS NOT NULL
   LIMIT 10)
)
"""
client.query(query).to_dataframe()
```

---
## Step 4 — Explain with `ML.GLOBAL_EXPLAIN`

Unlike `LINEAR_REG`/`BOOSTED_TREE_*`, no `enable_global_explain` option was needed at `CREATE MODEL` time — AutoML produces attributions automatically. Only model-level (not per-prediction) explanations are available for this model type: `ML.EXPLAIN_PREDICT` is **not supported** (confirmed in Step 7).

```python
query = f"""
SELECT *
FROM ML.GLOBAL_EXPLAIN(MODEL `{PROJECT_ID}.{DATASET_ID}.automl_regressor_natality`)
ORDER BY attribution DESC
"""
client.query(query).to_dataframe()
```

---
## Step 5 — Introspect the model

`ML.FEATURE_INFO` reports the statistics each feature had during training. `ML.TRAINING_INFO` returns per-iteration training info — for an AutoML model this reflects Vertex AI's internal training process rather than a simple iteration-by-iteration loss curve, since AutoML manages the search itself.

```python
query = f"""
SELECT *
FROM ML.FEATURE_INFO(MODEL `{PROJECT_ID}.{DATASET_ID}.automl_regressor_natality`)
"""
client.query(query).to_dataframe()
```

```python
query = f"""
SELECT *
FROM ML.TRAINING_INFO(MODEL `{PROJECT_ID}.{DATASET_ID}.automl_regressor_natality`)
"""
client.query(query).to_dataframe()
```

---
## Step 6 — Export with `EXPORT MODEL`

Writes the trained AutoML model to Cloud Storage for Vertex AI Model Registry / custom serving. Unlike `BOOSTED_TREE_*`/`RANDOM_FOREST_*`, AutoML's exported artifact is an opaque ensemble — there is no single tree/booster file to load and visualize with a local library, so this step just confirms the export lands in Cloud Storage.

```python
query = f"""
EXPORT MODEL `{PROJECT_ID}.{DATASET_ID}.automl_regressor_natality`
OPTIONS (URI = 'gs://{BUCKET}/bq_ml/automl_regressor/model')
"""
client.query(query).result()
print('Model exported')
```

```python
from google.cloud import storage

storage_client = storage.Client(project=PROJECT_ID)
bucket = storage_client.bucket(BUCKET)
blobs = list(bucket.list_blobs(prefix='bq_ml/automl_regressor/model'))
for blob in blobs:
    print(blob.name)
```

---
## Step 7 — Functions that do NOT apply to this model type

- **`TRANSFORM`** is not supported for AutoML model types — do any custom feature engineering in the training `SELECT` instead.
- **`ML.WEIGHTS` / `ML.ADVANCED_WEIGHTS`** do not apply — AutoML is not a single linear/tree model with an exposable weight vector.
- **`ML.EXPLAIN_PREDICT`** does not apply — use `ML.GLOBAL_EXPLAIN` (Step 4) for feature attributions instead.
- User-configurable hyperparameter tuning (`num_trials` / `HPARAM_RANGE` / `HPARAM_CANDIDATES`) is also not supported — `budget_hours` is the only lever.

Each cell below is expected to fail; the error text is captured live.

```python
# TRANSFORM — expected to fail
try:
    query = f"""
    CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.automl_regressor_natality_transform`
    TRANSFORM(gestation_weeks, weight_pounds)
    OPTIONS(
      model_type = 'AUTOML_REGRESSOR',
      input_label_cols = ['weight_pounds'],
      budget_hours = 1.0
    ) AS
    SELECT gestation_weeks, weight_pounds
    FROM `bigquery-public-data.samples.natality`
    WHERE year = 2003 AND mother_residence_state = 'WA'
      AND weight_pounds IS NOT NULL AND gestation_weeks IS NOT NULL
    """
    client.query(query).result()
except Exception as e:
    print(f'TRANSFORM failed as expected:\n{e}')
```

```python
# ML.WEIGHTS — expected to fail
try:
    query = f"""SELECT * FROM ML.WEIGHTS(MODEL `{PROJECT_ID}.{DATASET_ID}.automl_regressor_natality`)"""
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
      MODEL `{PROJECT_ID}.{DATASET_ID}.automl_regressor_natality`,
      (SELECT mother_age, gestation_weeks, plurality, is_male, mother_married, cigarette_use, weight_pounds
       FROM `bigquery-public-data.samples.natality`
       WHERE year = 2003 AND mother_residence_state = 'WA'
         AND weight_pounds IS NOT NULL AND mother_age IS NOT NULL
         AND gestation_weeks IS NOT NULL AND plurality IS NOT NULL
       LIMIT 5)
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
FROM ML.EVALUATE(MODEL `statmike-mlops-349915.bq_ml.automl_regressor_natality`)
```

---
## BigFrames

**No direct BigFrames AutoML estimator exists** (checked the live BigFrames API reference across `bigframes.ml.linear_model`, `.ensemble`, `.cluster`, `.decomposition`, `.forecasting`, `.imported`, `.llm` — no `AutoML*` class anywhere in the package, the same permanent gap as `DNN_REGRESSOR`/`WIDE_AND_DEEP_REGRESSOR`). Use the SQL `CREATE MODEL` interface shown above.
