# Transform-Only Models — BigQuery ML

Train a model that contains **only a `TRANSFORM` clause and no learning algorithm** with `CREATE MODEL` (model_type = `TRANSFORM_ONLY`) — a reusable, exportable preprocessing pipeline, decoupled from any estimator. There's no label, no training/evaluation of a predictor: the "output" of this model is the preprocessed data itself, produced by `ML.TRANSFORM`.

**Lifecycle:** `CREATE MODEL` (with `TRANSFORM`, no estimator) → `ML.TRANSFORM` → `ML.FEATURE_INFO` → `EXPORT MODEL` → feed the pipeline's output into a downstream `CREATE MODEL`

**Why this is its own model category:** every other model type in this project embeds an *optional* `TRANSFORM` clause directly on a predictive model (see `models/pca` (PCA) Step 10, or `models/kmeans` (K-Means)) — that embedded transform auto-applies at `ML.PREDICT`/`ML.EVALUATE` time, but it isn't reusable outside that one model. A `TRANSFORM_ONLY` model flips that: the pipeline is a first-class, reusable object with no estimator attached, at the cost of having to explicitly re-apply it (`ML.TRANSFORM`) before feeding new data into whatever downstream model consumes it.

**When to use a transform-only model:**
- Decouple feature engineering from model training so the same preprocessing (with its frozen train-time statistics — means, stddevs, vocabularies) can be reused across many downstream models.
- Build modular, feature-store-style transforms and chain them with CTEs or a view.
- Guarantee training/serving consistency without embedding the same `TRANSFORM` clause repeatedly across model definitions.

**A gotcha this notebook demonstrates directly, not just describes:** a downstream model trained on a `TRANSFORM_ONLY` pipeline's output has **no embedded `TRANSFORM` of its own**. If you call `ML.PREDICT` on that downstream model with *raw*, untransformed data, BigQuery ML does **not** error — it silently predicts using values on the wrong scale, giving confidently wrong answers. You must re-wrap new data in `ML.TRANSFORM` (using the same pipeline model) before every `ML.PREDICT`/`ML.EVALUATE` call.

**Data:** [`bigquery-public-data.ml_datasets.penguins`](https://console.cloud.google.com/marketplace/product/bigquery-public-datasets) — same dataset as `models/kmeans` (K-Means), `models/pca` (PCA), and `models/autoencoder` (Autoencoder). The pipeline imputes missing `body_mass_g`, standard-scales two measurements, robust-scales a third, and one-hot encodes `sex`; a downstream `LOGISTIC_REG` model then predicts `species` from the pipeline's output.

**Bridges into:** Phase 6 (model-free `ML.*` functions) documents each preprocessing function (`ML.IMPUTER`, the scalers, the encoders) individually and in standalone SQL — this notebook shows several of them **composed into one reusable pipeline object**, which is the more realistic way they get used in practice.

**References:** `RESOURCES.md` (Full reference) | [CREATE MODEL (transform-only) docs](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-transform) | `setup` (Setup guide)

---
## Setup

Set your project and location, authenticate, and create a shared dataset for the model.

> A transform-only model trains on data already in BigQuery — no connection or remote model required. See the `setup` (Setup Reference) for details.

```python
PROJECT_ID = 'statmike-mlops-349915'  # <-- Replace with your project ID
LOCATION = 'US'  # BigQuery dataset location
DATASET_ID = 'bq_ml'  # Shared dataset across all bq-ml notebooks
BUCKET = 'statmike-mlops-349915'  # <-- Replace with your GCS bucket (same location as DATASET_ID) -- used in Step 4 to export the pipeline
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
## Step 1 — Create the pipeline with `CREATE MODEL`

`model_type = 'TRANSFORM_ONLY'` is the only option that applies here — no `input_label_cols`, no learning options (any would error, since there's no estimator to configure). Every transformed column needs an explicit alias; `species` and `island` pass through untransformed.

- `ML.IMPUTER(body_mass_g, 'mean')` fills the 2 rows with a missing `body_mass_g`.
- `ML.STANDARD_SCALER` z-scores `culmen_length_mm`/`culmen_depth_mm`.
- `ML.ROBUST_SCALER` scales `flipper_length_mm` by median/IQR instead (outlier-robust).
- `ML.ONE_HOT_ENCODER(sex)` turns the 3-category (`MALE`/`FEMALE`/`NULL`) string into a sparse vector.

All four are **analytic** functions and require the empty `OVER()` — `ML.IMPUTER` additionally requires a `strategy` argument (`'mean'`/`'median'`/`'most_frequent'`), unlike the scalers, which take only the column.

```python
query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.transform_only_penguins`
TRANSFORM(
  species,
  island,
  ML.IMPUTER(body_mass_g, 'mean') OVER() AS body_mass_g,
  ML.STANDARD_SCALER(culmen_length_mm) OVER() AS culmen_length_mm,
  ML.STANDARD_SCALER(culmen_depth_mm) OVER() AS culmen_depth_mm,
  ML.ROBUST_SCALER(flipper_length_mm) OVER() AS flipper_length_mm,
  ML.ONE_HOT_ENCODER(sex) OVER() AS sex_encoded
)
OPTIONS(
  model_type = 'TRANSFORM_ONLY'
) AS
SELECT species, island, sex, body_mass_g, culmen_length_mm, culmen_depth_mm, flipper_length_mm
FROM `bigquery-public-data.ml_datasets.penguins`
"""
client.query(query).result()
print('Model transform_only_penguins created')
```

---
## Step 2 — Apply the pipeline with `ML.TRANSFORM`

Returns the columns the `TRANSFORM` clause produces for the inputs it consumes.

> **GOTCHA (verified):** any input column whose name isn't reused as an output alias in the `TRANSFORM` clause passes straight through **untouched**, appended after the transform outputs — here that's raw `sex`, which the pipeline consumes (`ML.ONE_HOT_ENCODER(sex) OVER() AS sex_encoded`) but never re-emits under its own name, so it comes through a second time as-is right alongside `sex_encoded`. Useful for carrying an id/label column through without re-listing it in the pipeline, but easy to mistake for the pipeline itself re-emitting a raw column — it's really just unused-by-name input passed through.

```python
query = f"""
SELECT *
FROM ML.TRANSFORM(
  MODEL `{PROJECT_ID}.{DATASET_ID}.transform_only_penguins`,
  (SELECT species, island, sex, body_mass_g, culmen_length_mm, culmen_depth_mm, flipper_length_mm
   FROM `bigquery-public-data.ml_datasets.penguins`
   LIMIT 5)
)
"""
client.query(query).to_dataframe()
```

---
## Step 3 — Introspect the raw inputs with `ML.FEATURE_INFO`

Reports statistics on the **raw** input columns (not the transformed outputs) — e.g. `sex` shows `null_count=10`, confirming why `ML.ONE_HOT_ENCODER` needs to handle nulls, and `body_mass_g` shows `null_count=2`, confirming why `ML.IMPUTER` is in the pipeline at all.

```python
query = f"""
SELECT *
FROM ML.FEATURE_INFO(MODEL `{PROJECT_ID}.{DATASET_ID}.transform_only_penguins`)
"""
client.query(query).to_dataframe()
```

---
## Step 4 — Export the pipeline with `EXPORT MODEL`

A transform-only export contains no predictive weights — there's no estimator — just the preprocessing graph and the frozen statistics (means, stddevs, one-hot vocabulary) computed at creation time. It exports as a `transform/saved_model.pb` (plus `assets`/`variables`), a distinct layout from a trained estimator's export.

```python
query = f"""
EXPORT MODEL `{PROJECT_ID}.{DATASET_ID}.transform_only_penguins`
OPTIONS (URI = 'gs://{BUCKET}/bq_ml/transform_only/model')
"""
client.query(query).result()
print('Model exported')

from google.cloud import storage
storage_client = storage.Client(project=PROJECT_ID)
bucket = storage_client.bucket(BUCKET)
for blob in bucket.list_blobs(prefix='bq_ml/transform_only/model'):
    print(blob.name)
```

---
## Step 5 — Feed the pipeline's output into a downstream `CREATE MODEL`

The downstream model has **no embedded `TRANSFORM` of its own** — it trains directly on the already-transformed columns coming out of `ML.TRANSFORM`. This is the feature-store-style pattern: one shared pipeline, reused across as many downstream models as you like, each choosing which transformed columns to consume.

```python
query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.transform_only_downstream`
OPTIONS(
  model_type = 'LOGISTIC_REG',
  input_label_cols = ['species']
) AS
SELECT species, island, body_mass_g, culmen_length_mm, culmen_depth_mm, flipper_length_mm
FROM ML.TRANSFORM(
  MODEL `{PROJECT_ID}.{DATASET_ID}.transform_only_penguins`,
  (SELECT species, island, sex, body_mass_g, culmen_length_mm, culmen_depth_mm, flipper_length_mm
   FROM `bigquery-public-data.ml_datasets.penguins`
   WHERE body_mass_g IS NOT NULL)
)
"""
client.query(query).result()
print('Model transform_only_downstream created')
```

---
## Step 6 — Evaluate the downstream model with `ML.EVALUATE`

```python
query = f"""
SELECT *
FROM ML.EVALUATE(MODEL `{PROJECT_ID}.{DATASET_ID}.transform_only_downstream`)
"""
client.query(query).to_dataframe()
```

---
## Step 7 — The gotcha: predicting on raw data silently gives garbage

Because the downstream model has no embedded `TRANSFORM`, `ML.PREDICT` does **not** know to re-apply the pipeline. Feeding it raw (untransformed) feature values doesn't error — BigQuery ML happily predicts using values on the wrong scale, it just gives **wrong** answers.

> **Verified live:** every row below predicts `Gentoo penguin` (the largest species) regardless of its true species, because raw `body_mass_g`/`culmen_*` values are far outside the z-score-scaled range the model was actually trained on.

```python
query = f"""
SELECT species, predicted_species
FROM ML.PREDICT(
  MODEL `{PROJECT_ID}.{DATASET_ID}.transform_only_downstream`,
  (SELECT species, island, body_mass_g, culmen_length_mm, culmen_depth_mm, flipper_length_mm
   FROM `bigquery-public-data.ml_datasets.penguins`
   WHERE body_mass_g IS NOT NULL LIMIT 5)
)
"""
client.query(query).to_dataframe()
```

---
## Step 8 — The fix: re-apply `ML.TRANSFORM` before `ML.PREDICT`

Wrapping the same raw rows in `ML.TRANSFORM` first reproduces the exact preprocessing used at training time, and predictions become correct again. This re-application is the price of a transform-only model's reusability — contrast with an **embedded** `TRANSFORM` clause on a predictive model (e.g. `models/pca` (PCA) Step 10), which auto-applies at predict time with no re-application needed, but isn't reusable across other models the way a standalone `TRANSFORM_ONLY` model is.

```python
query = f"""
SELECT species, predicted_species
FROM ML.PREDICT(
  MODEL `{PROJECT_ID}.{DATASET_ID}.transform_only_downstream`,
  (SELECT species, island, body_mass_g, culmen_length_mm, culmen_depth_mm, flipper_length_mm
   FROM ML.TRANSFORM(
     MODEL `{PROJECT_ID}.{DATASET_ID}.transform_only_penguins`,
     (SELECT species, island, sex, body_mass_g, culmen_length_mm, culmen_depth_mm, flipper_length_mm
      FROM `bigquery-public-data.ml_datasets.penguins`
      WHERE body_mass_g IS NOT NULL LIMIT 5)
   )
  )
)
"""
client.query(query).to_dataframe()
```

---
## Examples — `%%bigquery` Magics

The same operations using IPython magic commands — write SQL directly in cells without Python string wrapping.

- `%%bigquery` — run SQL, display results inline
- `%%bigquery df` — run SQL, capture results into a pandas DataFrame

### `ML.FEATURE_INFO` with `%%bigquery`

```sql
%%bigquery --project {PROJECT_ID}

SELECT *
FROM ML.FEATURE_INFO(MODEL `statmike-mlops-349915.bq_ml.transform_only_penguins`)
```

---
## Examples — BigFrames

There is **no single direct `TRANSFORM_ONLY` class** in BigFrames — the equivalent functionality is the `bigframes.ml.preprocessing` transformers (`StandardScaler`, `MaxAbsScaler`, `OneHotEncoder`, etc.) composed with `bigframes.ml.pipeline.Pipeline`, which compile down to the same BQML preprocessing functions under the hood. This shows the closest equivalent: a two-step `Pipeline` (impute, then scale) — but note it does not produce a queryable `TRANSFORM_ONLY` model object the way the SQL path does; it's a Python-side pipeline that gets applied at `.fit()`/`.predict()` time.

```python
import bigframes.pandas as bpd

bpd.close_session()  # Reset session to apply project/location settings
bpd.options.bigquery.project = PROJECT_ID
bpd.options.bigquery.location = LOCATION
```

```python
from bigframes.ml.preprocessing import StandardScaler
from bigframes.ml.impute import SimpleImputer
from bigframes.ml.compose import ColumnTransformer

df = bpd.read_gbq('bigquery-public-data.ml_datasets.penguins')
df = df[df['body_mass_g'].notnull()]

# Impute then scale, composed as a ColumnTransformer (closest BigFrames equivalent
# to a reusable TRANSFORM_ONLY pipeline)
preprocessor = ColumnTransformer([
    ('scale_length', StandardScaler(), 'culmen_length_mm'),
    ('scale_depth', StandardScaler(), 'culmen_depth_mm'),
])
preprocessor.fit(df[['culmen_length_mm', 'culmen_depth_mm']])
preprocessor.transform(df[['culmen_length_mm', 'culmen_depth_mm']]).peek()
```
