# Imported Models — BigQuery ML

Bring a model trained **outside** BigQuery — TensorFlow, TensorFlow Lite, ONNX, or XGBoost — into BigQuery ML from Cloud Storage with `CREATE MODEL` (`model_type` = one of `TENSORFLOW` / `TENSORFLOW_LITE` / `ONNX` / `XGBOOST`) and run inference with `ML.PREDICT` **inside BigQuery compute**. This is the BigQuery ML Inference Engine: same SQL API, no Vertex AI endpoint to deploy, manage, or pay for.

**Lifecycle:** `CREATE MODEL` (with `MODEL_PATH` pointing at a GCS artifact) → `ML.PREDICT` → (`ML.FEATURE_IMPORTANCE`, XGBoost only)

**All four share one shape:**
```sql
CREATE MODEL `PROJECT.DATASET.NAME`
OPTIONS(MODEL_TYPE = '...', MODEL_PATH = 'gs://bucket/path/*')
```
— but they differ sharply in what's supported afterward. There's **no training, no `TRANSFORM`, no hyperparameter tuning, no `ML.EVALUATE`** for any of them: the model is frozen at import, and you supply inputs already in the format the model expects.

**When to use an imported model (vs. a `models/remote` (remote model)):**
- The model is small enough to fit BigQuery's size limits (250-450 MB depending on format) and needs no GPU.
- You want zero serving infrastructure — no endpoint to deploy or keep warm.
- Contrast with `models/remote` (`models/remote/`), where the model runs on an external Vertex AI endpoint of any size/framework, at the cost of needing that endpoint deployed and a connection configured.

**Data:** [`bigquery-public-data.ml_datasets.penguins`](https://console.cloud.google.com/marketplace/product/bigquery-public-datasets) — same 4 physical measurements used by `models/kmeans` (K-Means)/`models/pca` (PCA)/`models/transform_only` (Transform-Only), trained **locally** (outside BigQuery — that's the entire premise of "imported") with scikit-learn, XGBoost, and Keras, then imported and scored with `ML.PREDICT`.

**A verified, undocumented gotcha driving a chunk of this notebook's Setup:** BigQuery ML's `XGBOOST` importer only accepts Booster files saved by **XGBoost ≤ 1.5.1** — a booster saved with a modern (2.x/3.x) xgboost fails to import outright ("XGBoost model version newer than 1.5.1 is not supported"). Training with that old a release, in turn, needs `numpy<2` in the same Python environment. Both pins are scoped to this notebook's own kernel session.

**References:** `RESOURCES.md` (Full reference) | [Imported models journey](https://cloud.google.com/bigquery/docs/e2e-journey-import) | `setup` (Setup guide)

---
## Setup

Set your project and location, authenticate, and create a shared dataset for the model.

> Imported models need **no BigQuery connection** to read the GCS model file — BigQuery uses the credentials of whoever runs `CREATE MODEL` (a connection is only required for the unrelated case of serving against an *object table* under reservation pricing). But this notebook also does real **local training** (scikit-learn, XGBoost, Keras) to produce the artifacts to import, which is why Setup installs far more than the usual `google-cloud-bigquery`.

```python
PROJECT_ID = 'statmike-mlops-349915'  # <-- Replace with your project ID
LOCATION = 'US'  # BigQuery dataset location
DATASET_ID = 'bq_ml'  # Shared dataset across all bq-ml notebooks
BUCKET = 'statmike-mlops-349915'  # <-- Replace with your GCS bucket (same location as DATASET_ID) -- used to stage each imported model's artifact
```

### Environment

> **Already set up the project environment?** The cell below is a no-op — packages are already in your kernel. See the `setup` (Setup Reference) for details.
>
> **Running standalone** (Colab, Colab Enterprise, Vertex AI Workbench)? The cell below installs required packages into your current kernel.
>
> **Verified pins (see the gotcha above):** `xgboost==1.5.1` is the newest release whose Booster files BigQuery ML's `XGBOOST` importer will load, and that release needs `numpy<2` to run correctly on this environment's Python. It also imports the now-deprecated `pkg_resources` from `setuptools`, which was dropped from very recent `setuptools` releases — hence the `setuptools<81` pin too. All three pins apply for the rest of this notebook's kernel session.

> **This notebook shares a virtual environment with every other bq-ml notebook.** If another notebook's own `install()` cell runs at the same moment (e.g. `models/export` (`models/export/`), which pins a *different* xgboost version), the two concurrent writes to `site-packages` can corrupt `scipy` mid-install. That surfaces later as a confusing `"No module named 'numpy.strings'"` (or `'numpy.rec'`) error buried deep inside an unrelated `sklearn`/`xgboost` import — not a real version incompatibility (this exact `numpy`/`scipy`/`xgboost` combination is verified to work together correctly when installed without a race). The cell below catches that immediately, with an actionable message, instead of failing several cells later. **Avoid running this notebook's Setup at the same time as another bq-ml notebook's Setup** — if you hit the error below, wait for the other notebook's install to finish, then re-run this cell (and the one above it).

```python
import numpy, scipy, sklearn, xgboost
from sklearn.linear_model import LogisticRegression  # exercises the exact scipy import chain Step 2 needs

assert numpy.__version__.startswith('1.'), (
    f"numpy is {numpy.__version__}, expected 1.x (<2). Likely a concurrent install race "
    "with another bq-ml notebook -- re-run the install cell above once it's finished."
)
assert xgboost.__version__ == '1.5.1', (
    f"xgboost is {xgboost.__version__}, expected 1.5.1. Likely a concurrent install race "
    "with another bq-ml notebook -- re-run the install cell above once it's finished."
)
print(f'Environment OK -- numpy {numpy.__version__}, scipy {scipy.__version__}, xgboost {xgboost.__version__}')
```

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
## Step 1 — Pull the training data locally

Every format in this notebook is trained **outside** BigQuery, so the data has to leave BigQuery once, into a local pandas DataFrame — the opposite direction from every other notebook in this project.

```python
import numpy as np

query = """
SELECT species, culmen_length_mm, culmen_depth_mm, flipper_length_mm, body_mass_g
FROM `bigquery-public-data.ml_datasets.penguins`
WHERE body_mass_g IS NOT NULL
  AND culmen_length_mm IS NOT NULL
  AND culmen_depth_mm IS NOT NULL
  AND flipper_length_mm IS NOT NULL
"""
df = client.query(query).to_dataframe()

feature_cols = ['culmen_length_mm', 'culmen_depth_mm', 'flipper_length_mm', 'body_mass_g']
X = df[feature_cols].values.astype('float32')
species_classes = sorted(df['species'].unique())
y_multi = np.array([species_classes.index(s) for s in df['species']])
y_binary = (df['species'] == 'Adelie Penguin (Pygoscelis adeliae)').astype('float32').values

print(df.shape, dict(enumerate(species_classes)))
```

---
## Step 2 — `ONNX`: import a scikit-learn model

Train a scikit-learn `LogisticRegression`, convert it to ONNX with `skl2onnx`, and fix the two version gotchas verified above (`ir_version=8`, `target_opset=13`) before uploading.

```python
from sklearn.linear_model import LogisticRegression
from skl2onnx import convert_sklearn
from skl2onnx.common.data_types import FloatTensorType

clf = LogisticRegression(max_iter=1000)
clf.fit(X, y_multi)
print('sklearn train accuracy:', clf.score(X, y_multi))

# zipmap=False: without it, sklearn-onnx emits a "sequence of map" for
# probabilities that BigQuery ML's importer rejects outright.
onnx_model = convert_sklearn(
    clf,
    initial_types=[('input', FloatTensorType([None, 4]))],
    options={id(clf): {'zipmap': False}},
    target_opset=13,   # ONNX Runtime 1.12 (BQML's engine) only guarantees support through opset 17
)
onnx_model.ir_version = 8  # ONNX Runtime 1.12 max supported IR version

with open('sklearn_logreg.onnx', 'wb') as f:
    f.write(onnx_model.SerializeToString())
print('ONNX model written')
```

```python
blob = gcs_bucket.blob('bq_ml/imported/onnx/model.onnx')
blob.upload_from_filename('sklearn_logreg.onnx')
print(f'Uploaded to gs://{BUCKET}/bq_ml/imported/onnx/model.onnx')

query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.imported_onnx_penguins`
OPTIONS(
  model_type = 'ONNX',
  model_path = 'gs://{BUCKET}/bq_ml/imported/onnx/*'
)
"""
client.query(query).result()
print('Model imported_onnx_penguins created')
```

`ML.FEATURE_INFO` is **not** supported for ONNX (or any imported type) — verified: `"Model type ONNX is not supported by FEATURE_INFO."` Use the Python client (`client.get_model(...)`) to confirm the import succeeded instead.

```python
query = f"""
SELECT species, label, probabilities
FROM ML.PREDICT(
  MODEL `{PROJECT_ID}.{DATASET_ID}.imported_onnx_penguins`,
  (SELECT species,
     [CAST(culmen_length_mm AS FLOAT64), CAST(culmen_depth_mm AS FLOAT64),
      CAST(flipper_length_mm AS FLOAT64), CAST(body_mass_g AS FLOAT64)] AS input
   FROM `bigquery-public-data.ml_datasets.penguins`
   WHERE body_mass_g IS NOT NULL LIMIT 5)
)
"""
client.query(query).to_dataframe()
```

---
## Step 3 — `XGBOOST`: import a native XGBoost Booster

XGBoost is BigQuery ML's **native** import format for this library — no conversion step, just `booster.save_model(...)`. Trained here as a **binary** classifier (predict "is this an Adelie penguin?") rather than the multiclass model used elsewhere in this notebook — verified live that a `multi:softprob` objective still predicts fine, but BigQuery ML silently returns an ARRAY of per-class probabilities even though `OUTPUT` declares a single `FLOAT64` field, which reads confusingly. A binary objective keeps the declared output type honest.

> **GOTCHA (verified, undocumented as of this writing):** BigQuery ML's XGBoost importer only accepts Booster files saved by **XGBoost ≤ 1.5.1** — training with a modern xgboost (2.x/3.x, whatever `pip install xgboost` gives you today) produces a file that fails to import: `"XGBoost model version newer than 1.5.1 is not supported."` This is why Setup pins `xgboost==1.5.1` (and, transitively, `numpy<2`).

```python
import xgboost as xgb
print('xgboost version:', xgb.__version__)  # should be 1.5.1 -- see the gotcha above

dtrain = xgb.DMatrix(X, label=y_binary, feature_names=feature_cols)
params = {'objective': 'binary:logistic', 'max_depth': 3, 'eta': 0.3}
booster = xgb.train(params, dtrain, num_boost_round=50)

preds = booster.predict(dtrain)
train_acc = ((preds > 0.5).astype(int) == y_binary).mean()
print('xgboost train accuracy:', train_acc)

booster.save_model('xgb_penguins.json')
print('XGBoost model written')
```

```python
blob = gcs_bucket.blob('bq_ml/imported/xgboost/model.json')
blob.upload_from_filename('xgb_penguins.json')
print(f'Uploaded to gs://{BUCKET}/bq_ml/imported/xgboost/model.json')

# INPUT/OUTPUT is required here (the Booster file has feature_names but not
# feature_types) -- unlike ONNX/TensorFlow, which need neither.
query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.imported_xgboost_penguins`
INPUT(culmen_length_mm FLOAT64, culmen_depth_mm FLOAT64, flipper_length_mm FLOAT64, body_mass_g FLOAT64)
OUTPUT(is_adelie_prob FLOAT64)
OPTIONS(
  model_type = 'XGBOOST',
  model_path = 'gs://{BUCKET}/bq_ml/imported/xgboost/*'
)
"""
client.query(query).result()
print('Model imported_xgboost_penguins created')
```

```python
query = f"""
SELECT species, is_adelie_prob
FROM ML.PREDICT(
  MODEL `{PROJECT_ID}.{DATASET_ID}.imported_xgboost_penguins`,
  (SELECT species, culmen_length_mm, culmen_depth_mm, flipper_length_mm, body_mass_g
   FROM `bigquery-public-data.ml_datasets.penguins`
   WHERE body_mass_g IS NOT NULL LIMIT 5)
)
"""
client.query(query).to_dataframe()
```

`XGBOOST` is the **only** imported type that supports `ML.FEATURE_IMPORTANCE` — unlike ONNX/TensorFlow/TensorFlow Lite, which support none of the introspection functions.

```python
query = f"""
SELECT *
FROM ML.FEATURE_IMPORTANCE(MODEL `{PROJECT_ID}.{DATASET_ID}.imported_xgboost_penguins`)
"""
client.query(query).to_dataframe()
```

---
## Step 4 — `TENSORFLOW`: import a Keras SavedModel

A small Keras `Sequential` model with a `tf.keras.layers.Normalization` layer **baked in** (`.adapt()`-ed on the training data). Imported models support no `TRANSFORM`/preprocessing of their own, so any feature scaling the model needs must live inside the exported graph itself — this lets raw column values be fed directly at predict time, same as the trained data.

```python
import tensorflow as tf

norm = tf.keras.layers.Normalization(axis=-1)
norm.adapt(X)

model = tf.keras.Sequential([
    tf.keras.layers.Input(shape=(4,), name='input'),
    norm,
    tf.keras.layers.Dense(8, activation='relu'),
    tf.keras.layers.Dense(3, activation='softmax'),
])
model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])
model.fit(X, y_multi, epochs=60, verbose=0)
loss, acc = model.evaluate(X, y_multi, verbose=0)
print('keras train accuracy (raw, unscaled features -- Normalization is baked in):', acc)

model.export('tf_savedmodel')
```

```python
import os

for root, _, files in os.walk('tf_savedmodel'):
    for fname in files:
        local_path = os.path.join(root, fname)
        rel_path = os.path.relpath(local_path, 'tf_savedmodel')
        blob = gcs_bucket.blob(f'bq_ml/imported/tensorflow/{rel_path}')
        blob.upload_from_filename(local_path)
print(f'Uploaded SavedModel to gs://{BUCKET}/bq_ml/imported/tensorflow/')

query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.imported_tensorflow_penguins`
OPTIONS(
  model_type = 'TENSORFLOW',
  model_path = 'gs://{BUCKET}/bq_ml/imported/tensorflow/*'
)
"""
client.query(query).result()
print('Model imported_tensorflow_penguins created')
```

Input is a single `ARRAY<FLOAT64>` column matching the SavedModel's named input signature (`"input"`, shape `(-1, 4)`) — BigQuery maps it by name. The output column is auto-named `output_0` (the model's output tensor has no name).

```python
query = f"""
SELECT species, output_0
FROM ML.PREDICT(
  MODEL `{PROJECT_ID}.{DATASET_ID}.imported_tensorflow_penguins`,
  (SELECT species,
     [CAST(culmen_length_mm AS FLOAT64), CAST(culmen_depth_mm AS FLOAT64),
      CAST(flipper_length_mm AS FLOAT64), CAST(body_mass_g AS FLOAT64)] AS input
   FROM `bigquery-public-data.ml_datasets.penguins`
   WHERE body_mass_g IS NOT NULL LIMIT 5)
)
"""
client.query(query).to_dataframe()
```

> **Correction to the docs (verified live):** the capability table cited in `RESOURCES.md` (sourced from official BigQuery ML documentation) lists `ML.EXPLAIN_PREDICT` as supported for `TENSORFLOW` imports. Calling it on this model returns `"TENSORFLOW model is unsupported in ml.explain_predict."` Not reproduced here — treat that specific cell as unverified/stale until confirmed against a model that does support it.

---
## Step 5 — `TENSORFLOW_LITE`: the same model, converted to `.tflite`

`tf.lite.TFLiteConverter.from_saved_model(...)` on the exact SavedModel from Step 4 — same graph, same baked-in `Normalization` layer, just a more compact serialized format.

```python
converter = tf.lite.TFLiteConverter.from_saved_model('tf_savedmodel')
tflite_model = converter.convert()
with open('model.tflite', 'wb') as f:
    f.write(tflite_model)
print(f'TFLite model written ({len(tflite_model)} bytes)')
```

```python
blob = gcs_bucket.blob('bq_ml/imported/tflite/model.tflite')
blob.upload_from_filename('model.tflite')
print(f'Uploaded to gs://{BUCKET}/bq_ml/imported/tflite/model.tflite')

query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.imported_tflite_penguins`
OPTIONS(
  model_type = 'TENSORFLOW_LITE',
  model_path = 'gs://{BUCKET}/bq_ml/imported/tflite/*'
)
"""
client.query(query).result()
print('Model imported_tflite_penguins created')
```

**Verified:** predictions match the `TENSORFLOW` import in Step 4 to about 7 significant figures — not bit-for-bit identical (they differ at the 7th-8th decimal place, ordinary float32 kernel differences between the TensorFlow runtime and the TFLite interpreter, since no quantization was applied during conversion) — same input contract (`ARRAY<FLOAT64>` named `"input"`), same `output_0` naming convention. Only `ML.PREDICT` is supported for this type — narrower than `TENSORFLOW`, which at least nominally lists `ML.EXPLAIN_PREDICT` (see the correction above).

```python
query = f"""
SELECT species, output_0
FROM ML.PREDICT(
  MODEL `{PROJECT_ID}.{DATASET_ID}.imported_tflite_penguins`,
  (SELECT species,
     [CAST(culmen_length_mm AS FLOAT64), CAST(culmen_depth_mm AS FLOAT64),
      CAST(flipper_length_mm AS FLOAT64), CAST(body_mass_g AS FLOAT64)] AS input
   FROM `bigquery-public-data.ml_datasets.penguins`
   WHERE body_mass_g IS NOT NULL LIMIT 5)
)
"""
client.query(query).to_dataframe()
```

---
## Step 6 — Comparing the four formats

| | `ONNX` | `XGBOOST` | `TENSORFLOW` | `TENSORFLOW_LITE` |
|---|---|---|---|---|
| Trained with | scikit-learn → skl2onnx | xgboost (native) | Keras | Keras → TFLiteConverter |
| Size limit | 450 MB | 250 MB | 450 MB | 450 MB |
| `INPUT`/`OUTPUT` clause | Not needed | Required (unless `feature_names`+`feature_types` in file) | Not needed | Not needed |
| `ML.FEATURE_INFO` | No | No | No | No |
| `ML.FEATURE_IMPORTANCE` | No | **Yes (only one)** | No | No |
| `ML.EXPLAIN_PREDICT` | No | No | Documented, **not actually supported** (verified) | No |
| `ML.EVALUATE` / HP tuning / `TRANSFORM` | No | No | No | No |
| Version gotcha | IR version ≤ 8, opset ≤ ~17 | Booster version ≤ XGBoost 1.5.1 | 450 MB / ~250 MB RAM limit | Only TF core + TF Text ops |

Every format shares the same bottom line: **no training-time BigQuery cost, no serving infrastructure, but a frozen model** with almost no introspection beyond `ML.PREDICT`.

---
## Related production content

This notebook stays focused on the `CREATE MODEL`/`ML.PREDICT` mechanics of each import format. For the full production picture — real-world model sizes, tokenization contracts, container-free serving tradeoffs — see:
- `MLOps/Serving/SQL%20Inference/BQML%20Import%20Model%20via%20ONNX.ipynb` (`MLOps/Serving/SQL Inference/BQML Import Model via ONNX.ipynb`) — a HuggingFace PyTorch sentiment model converted to ONNX, with the 250 MB practical limit and pre-tokenized `ARRAY` inputs.
- `MLOps/Serving/SQL%20Inference/Serve%20TensorFlow%20SavedModel%20Format%20With%20BigQuery.ipynb` (`MLOps/Serving/SQL Inference/Serve TensorFlow SavedModel Format With BigQuery.ipynb`) — importing a TensorFlow SavedModel at production scale.

---
## Examples — `%%bigquery` Magics

The same operations using IPython magic commands — write SQL directly in cells without Python string wrapping.

- `%%bigquery` — run SQL, display results inline
- `%%bigquery df` — run SQL, capture results into a pandas DataFrame

```sql
%%bigquery --project {PROJECT_ID}

SELECT *
FROM ML.FEATURE_IMPORTANCE(MODEL `statmike-mlops-349915.bq_ml.imported_xgboost_penguins`)
```

---
## Examples — BigFrames

`bigframes.ml.imported` has a dedicated wrapper class per format — `ONNXModel`, `TensorFlowModel`, `XGBoostModel` (no separate class for TensorFlow Lite). Each wraps the exact same `CREATE MODEL ... MODEL_PATH=...` mechanics shown above; `.predict()` maps to `ML.PREDICT`.

```python
import bigframes.pandas as bpd
from bigframes.ml.imported import ONNXModel

bpd.close_session()  # Reset session to apply project/location settings
bpd.options.bigquery.project = PROJECT_ID
bpd.options.bigquery.location = LOCATION
```

```python
bf_onnx_model = ONNXModel(model_path=f'gs://{BUCKET}/bq_ml/imported/onnx/*')

# Build the ARRAY<FLOAT64> input column in the SQL itself -- BigFrames'
# DataFrame.apply(axis=1) requires a registered BigQuery function for
# row-wise Python callables, so the array literal is constructed server-side.
bf_query = f"""
SELECT species,
  [CAST(culmen_length_mm AS FLOAT64), CAST(culmen_depth_mm AS FLOAT64),
   CAST(flipper_length_mm AS FLOAT64), CAST(body_mass_g AS FLOAT64)] AS input
FROM `bigquery-public-data.ml_datasets.penguins`
WHERE body_mass_g IS NOT NULL
LIMIT 5
"""
bf_df = bpd.read_gbq(bf_query)

bf_onnx_model.predict(bf_df[['input']]).peek()
```
