# Export Models — BigQuery ML

Write a trained BQML model to Cloud Storage in a portable format with `EXPORT MODEL`, so it can be served **outside** BigQuery — with TF Serving, a custom container, or a Vertex AI Endpoint. No connection is needed for the export itself (just GCS write IAM).

**Lifecycle:** `CREATE MODEL` → `EXPORT MODEL` → load locally to prove portability → (optionally) `model_registry='VERTEX_AI'` for direct registry registration

**Two export formats, chosen by model type — not by an option you set:**
- **TensorFlow SavedModel** — the default for most types (GLMs, DNNs, `KMEANS`, `PCA`, `AUTOENCODER`, `TRANSFORM_ONLY`, ...).
- **XGBoost Booster** (`model.bst`) — `BOOSTED_TREE_*`/`RANDOM_FOREST_*` only.

This notebook trains one of each to export both formats and proves each is genuinely portable by loading it back **outside BigQuery**, with no BigQuery client involved at that point.

**When to use `EXPORT MODEL` (vs. an `models/imported` (imported) round trip, vs. `models/remote` (remote models)):**
- You trained in BQML but need to serve somewhere BigQuery ML itself can't reach (a mobile app via TF Lite conversion, an on-prem server, a custom Vertex AI Endpoint with GPU serving).
- Contrast with `models/remote` (`models/remote/`), which goes the other direction: **exports** a BQML model, uploads it to a **Vertex AI Endpoint**, and calls it back from BigQuery with `REMOTE WITH CONNECTION` — the natural next step after this notebook.
- Contrast with `models/imported` (`models/imported/`), which imports models trained **outside** BigQuery *into* BigQuery — the reverse direction from this notebook.

**Data:** [`bigquery-public-data.ml_datasets.census_adult_income`](https://console.cloud.google.com/marketplace/product/bigquery-public-datasets) — same feature/label set as `models/logistic_regression` (Logistic Regression) and `models/boosted_tree_classifier` (Boosted Tree Classifier).

**References:** `RESOURCES.md` (Full reference) | [EXPORT MODEL docs](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-export-model) | [Exporting models](https://cloud.google.com/bigquery/docs/exporting-models) | `setup` (Setup guide)

---
## Setup

Set your project and location, authenticate, and create a shared dataset for the model.

> `EXPORT MODEL` needs **no BigQuery connection** — only GCS write IAM for the destination bucket. `model_registry='VERTEX_AI'` (Step 5) needs the usual Vertex AI Model Registry permissions, also not a BigQuery connection. This notebook additionally installs `tensorflow` and a pinned `xgboost` **locally** to prove each export loads and runs outside BigQuery entirely.

```python
PROJECT_ID = 'statmike-mlops-349915'  # <-- Replace with your project ID
LOCATION = 'US'  # BigQuery dataset location
REGION = 'us-central1'  # Vertex AI region for model_registry='VERTEX_AI' (Step 5)
DATASET_ID = 'bq_ml'  # Shared dataset across all bq-ml notebooks
BUCKET = 'statmike-mlops-349915'  # <-- Replace with your GCS bucket (same location as DATASET_ID) -- used to stage each export
```

### Environment

> **Already set up the project environment?** The cell below is a no-op — packages are already in your kernel. See the `setup` (Setup Reference) for details.
>
> **Running standalone** (Colab, Colab Enterprise, Vertex AI Workbench)? The cell below installs required packages into your current kernel.
>
> **Verified pin:** loading a BQML-exported XGBoost Booster locally needs `xgboost<2.0` — modern xgboost (2.0+) cannot read BQML's exported legacy binary format (the same gotcha documented in `models/boosted_tree_classifier` (`models/boosted_tree_classifier/`) Step 7).

```python
from google.cloud import bigquery, storage
import pandas as pd

client = bigquery.Client(project=PROJECT_ID)
gcs_client = storage.Client(project=PROJECT_ID)
gcs_bucket = gcs_client.bucket(BUCKET)
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
## Step 1 — Train a `LOGISTIC_REG` model to export

A small, fast-training classifier — the point of this notebook is the export mechanics, not the model quality.

```python
query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.export_logistic_regression_income`
OPTIONS(
  model_type = 'LOGISTIC_REG',
  input_label_cols = ['income_bracket'],
  auto_class_weights = TRUE
) AS
SELECT
  age, workclass, education, education_num, marital_status, occupation,
  relationship, race, sex, hours_per_week, native_country, income_bracket
FROM `bigquery-public-data.ml_datasets.census_adult_income`
"""
client.query(query).result()
print('Model export_logistic_regression_income created')
```

---
## Step 2 — `EXPORT MODEL`: TensorFlow SavedModel

`LOGISTIC_REG` (like GLMs, DNNs, `KMEANS`, `PCA`, `AUTOENCODER`, `TRANSFORM_ONLY`) exports as a TensorFlow SavedModel by default — no format option needed in SQL.

```python
query = f"""
EXPORT MODEL `{PROJECT_ID}.{DATASET_ID}.export_logistic_regression_income`
OPTIONS (URI = 'gs://{BUCKET}/bq_ml/export/logistic_regression/model')
"""
client.query(query).result()
print('Model exported')

for blob in gcs_bucket.list_blobs(prefix='bq_ml/export/logistic_regression/model'):
    print(blob.name)
```

Download the export and inspect its signature — this is now a plain TensorFlow artifact, no BigQuery involved.

```python
import os

local_dir = '/tmp/export_logistic_regression'
os.makedirs(local_dir, exist_ok=True)
for blob in gcs_bucket.list_blobs(prefix='bq_ml/export/logistic_regression/model'):
    rel_path = blob.name.split('bq_ml/export/logistic_regression/model/')[-1]
    if not rel_path or blob.name.endswith('/'):
        continue  # skip the GCS directory-placeholder objects
    local_path = os.path.join(local_dir, rel_path)
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    blob.download_to_filename(local_path)
print(f'Downloaded to {local_dir}')

import tensorflow as tf

tf_model = tf.saved_model.load(local_dir)
infer = tf_model.signatures['serving_default']
print('Inputs:', list(infer.structured_input_signature[1].keys()))
print('Outputs:', list(infer.structured_outputs.keys()))
```

**Verified:** the exported signature exposes **one named input tensor per feature column** (not a single packed array, unlike the imported-model examples in `models/imported` (`models/imported/`)) and three named outputs (`{label}_probs`, `{label}_values`, `predicted_{label}`). Categorical vocabularies (`education.txt`, `workclass.txt`, ...) ship as separate asset files alongside the graph. Run a real prediction, entirely outside BigQuery:

```python
result = infer(
    age=tf.constant([39.0], dtype=tf.float64),
    workclass=tf.constant(['Private']),
    education=tf.constant(['Bachelors']),
    education_num=tf.constant([13.0], dtype=tf.float64),
    marital_status=tf.constant(['Never-married']),
    occupation=tf.constant(['Tech-support']),
    relationship=tf.constant(['Not-in-family']),
    race=tf.constant(['White']),
    sex=tf.constant(['Male']),
    hours_per_week=tf.constant([40.0], dtype=tf.float64),
    native_country=tf.constant(['United-States']),
)
{k: v.numpy() for k, v in result.items()}
```

---
## Step 3 — Train a `BOOSTED_TREE_CLASSIFIER` to export

Tree ensembles export to a different format (Step 4), so this notebook trains one alongside the `LOGISTIC_REG` above. `max_iterations=20` keeps this reasonably quick — but boosted-tree training on this ~32K-row table still takes several minutes (verified ~6 minutes here), consistent with `models/boosted_tree_classifier` (`models/boosted_tree_classifier/`)'s own timing notes.

```python
query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.export_boosted_tree_income`
OPTIONS(
  model_type = 'BOOSTED_TREE_CLASSIFIER',
  input_label_cols = ['income_bracket'],
  max_iterations = 20
) AS
SELECT
  age, workclass, education, education_num, marital_status, occupation,
  relationship, race, sex, hours_per_week, native_country, income_bracket
FROM `bigquery-public-data.ml_datasets.census_adult_income`
"""
client.query(query).result()
print('Model export_boosted_tree_income created')
```

---
## Step 4 — `EXPORT MODEL`: XGBoost Booster

`BOOSTED_TREE_*`/`RANDOM_FOREST_*` export as an XGBoost Booster (`model.bst`) instead — the format is determined by model type, not an option you set in SQL.

> **GOTCHA (verified, same as `models/boosted_tree_classifier` (`models/boosted_tree_classifier/`) Step 7):** loading this file locally needs `xgboost<2.0` pinned — BQML exports using an old XGBoost binary format that modern xgboost (2.0+) cannot read — and `feature_names` must be reassigned manually after loading (the export does not preserve them).

```python
query = f"""
EXPORT MODEL `{PROJECT_ID}.{DATASET_ID}.export_boosted_tree_income`
OPTIONS (URI = 'gs://{BUCKET}/bq_ml/export/boosted_tree/model')
"""
client.query(query).result()
print('Model exported')
```

```python
import os

local_dir = '/tmp/export_boosted_tree'
os.makedirs(local_dir, exist_ok=True)
blob = gcs_bucket.blob('bq_ml/export/boosted_tree/model/model.bst')
local_path = os.path.join(local_dir, 'model.bst')
blob.download_to_filename(local_path)
print(f'Downloaded to {local_path}')

import xgboost as xgb
print('xgboost version:', xgb.__version__)  # must be < 2.0 -- see the gotcha above

booster = xgb.Booster()
booster.load_model(local_path)
booster.feature_names = [
    'age', 'workclass', 'education', 'education_num', 'marital_status',
    'occupation', 'relationship', 'race', 'sex', 'hours_per_week', 'native_country',
]
print('Loaded outside BigQuery. Feature count:', booster.num_features())
```

Prove the artifact is fully self-contained by computing feature importance **locally** with the `xgboost` library — no BigQuery client, no `ML.FEATURE_IMPORTANCE` call involved.

```python
booster.get_score(importance_type='gain')
```

---
## Step 5 — `model_registry='VERTEX_AI'`: register at training time

An alternative to `EXPORT MODEL` + manual upload: register the trained model directly to Vertex AI Model Registry as a side effect of `CREATE MODEL`. No live serving cost yet — this only creates a Model Registry entry (registry storage), not a deployed Endpoint. `models/remote` (`models/remote/`) picks up from here and deploys.

```python
query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.export_logistic_regression_registry`
OPTIONS(
  model_type = 'LOGISTIC_REG',
  input_label_cols = ['income_bracket'],
  model_registry = 'VERTEX_AI',
  vertex_ai_model_id = 'bq_ml_export_demo_logreg'
) AS
SELECT
  age, workclass, education, education_num, marital_status, occupation,
  relationship, race, sex, hours_per_week, native_country, income_bracket
FROM `bigquery-public-data.ml_datasets.census_adult_income`
"""
client.query(query).result()
print('Model export_logistic_regression_registry created and registered to Vertex AI')
```

Verify the registration with the Vertex AI SDK — a completely separate API surface from BigQuery, confirming the model genuinely landed in Vertex AI Model Registry.

```python
from google.cloud import aiplatform

aiplatform.init(project=PROJECT_ID, location=REGION)
vertex_models = aiplatform.Model.list(filter='display_name="bq_ml_export_demo_logreg"')
for m in vertex_models:
    print(m.display_name, m.resource_name, m.create_time)
```

---
## Step 6 — `bq extract --model`: the CLI equivalent

Same result as Step 2, run from the shell instead of SQL — useful for scripting exports outside a notebook/BigQuery client session. `--destination_format` lets you choose explicitly (`ML_TF_SAVED_MODEL` is the default; `ML_XGBOOST_BOOSTER` is the only other option, for tree ensembles):

```bash
bq extract --model \
  --destination_format=ML_TF_SAVED_MODEL \
  PROJECT_ID:DATASET.export_logistic_regression_income \
  gs://BUCKET/bq_ml/export/cli_extract/model
```

Not run here — it's the exact same export as Step 2's `EXPORT MODEL` statement, just from a different interface.

---
## Related production content

This notebook stays focused on `EXPORT MODEL` mechanics and proving portability with a minimal local load. For deploying an exported model to a real serving platform, see:
- `MLOps/Serving/Platforms/Vertex%20AI%20Pre-built%20Serving%20Containers.ipynb` (`MLOps/Serving/Platforms/Vertex AI Pre-built Serving Containers.ipynb`) — upload an exported model to Vertex AI Model Registry with a pre-built serving container (no Dockerfile), the same mechanism `models/remote` (`models/remote/`) uses to deploy an Endpoint.
- `models/remote` (`models/remote/`) — the natural next step: deploy an exported model to a Vertex AI Endpoint and call it back from BigQuery with `REMOTE WITH CONNECTION`.

---
## Examples — `%%bigquery` Magics

The same operations using IPython magic commands — write SQL directly in cells without Python string wrapping.

- `%%bigquery` — run SQL, display results inline
- `%%bigquery df` — run SQL, capture results into a pandas DataFrame

```sql
%%bigquery --project {PROJECT_ID}

EXPORT MODEL `statmike-mlops-349915.bq_ml.export_logistic_regression_income`
OPTIONS (URI = 'gs://statmike-mlops-349915/bq_ml/export/logistic_regression_magics/model')
```

---
## Examples — BigFrames

`EXPORT MODEL` has no dedicated one-call BigFrames helper — `bigframes.ml` estimators persist to BigQuery via `model.to_gbq(...)`, but GCS export is still done through the SQL `EXPORT MODEL` statement (or `bq extract --model`). This trains the same `LOGISTIC_REG` via BigFrames, then exports it with plain SQL.

```python
import bigframes.pandas as bpd
from bigframes.ml.linear_model import LogisticRegression

bpd.close_session()  # Reset session to apply project/location settings
bpd.options.bigquery.project = PROJECT_ID
bpd.options.bigquery.location = LOCATION

df = bpd.read_gbq('bigquery-public-data.ml_datasets.census_adult_income')
feature_cols = ['age', 'workclass', 'education', 'education_num', 'marital_status',
                'occupation', 'relationship', 'race', 'sex', 'hours_per_week', 'native_country']
X = df[feature_cols]
y = df['income_bracket']

bf_model = LogisticRegression()
bf_model.fit(X, y)
bf_model.to_gbq(f'{PROJECT_ID}.{DATASET_ID}.export_logistic_regression_bigframes', replace=True)

query = f"""
EXPORT MODEL `{PROJECT_ID}.{DATASET_ID}.export_logistic_regression_bigframes`
OPTIONS (URI = 'gs://{BUCKET}/bq_ml/export/logistic_regression_bigframes/model')
"""
client.query(query).result()
print('BigFrames-trained model exported via plain SQL EXPORT MODEL')
```
