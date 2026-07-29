# PCA — BigQuery ML

Train an **unsupervised dimensionality-reduction** model with `CREATE MODEL` (model_type = `PCA`) — no label column, just a smaller set of orthogonal principal components that capture as much of the original variance as possible — then walk the full model lifecycle: evaluate, predict, visualize, inspect components, detect anomalies, generate embeddings, apply in-model preprocessing, and try an alternative to a fixed component count. No data leaves BigQuery, and no separate training infrastructure is needed.

**Lifecycle:** `CREATE MODEL` → `ML.EVALUATE` → `ML.PREDICT` → visualize → `ML.PRINCIPAL_COMPONENTS` → `ML.PRINCIPAL_COMPONENT_INFO` → `ML.FEATURE_INFO` → `ML.DETECT_ANOMALIES` → `ML.GENERATE_EMBEDDING` → `TRANSFORM` clause → `pca_explained_variance_ratio` (no hyperparameter tuning exists for PCA)

**Same unsupervised pattern as `models/kmeans` (K-Means), with one reassuring difference:**
- No `input_label_cols` — every selected column is a feature to project, not predict.
- `ML.EVALUATE`'s `total_explained_variance_ratio` measures how much of the original variance survives the projection — not agreement with any ground truth.
- This notebook carries the real `species` column through `ML.PREDICT` as an **external check**, same convention as K-Means.
- **Verified: unlike K-Means, PCA is fully deterministic.** Retraining the identical model produced a bit-for-bit identical `total_explained_variance_ratio` every time — PCA is a closed-form eigendecomposition, not an iterative algorithm with random initialization, so there's no retraining variance to guard against here.

**When to use PCA:**
- Reduce dimensionality before training another model, or for visualization of high-dimensional data
- Unsupervised anomaly detection via `ML.DETECT_ANOMALIES` (reconstruction-error based)
- Generate compact embeddings of structured rows for downstream similarity search (`ML.GENERATE_EMBEDDING` + `VECTOR_SEARCH`)
- Inspect feature loadings to understand which features drive the most variance

**Data:** [`bigquery-public-data.ml_datasets.penguins`](https://console.cloud.google.com/marketplace/product/bigquery-public-datasets) — reduce four physical measurements (`culmen_length_mm`, `culmen_depth_mm`, `flipper_length_mm`, `body_mass_g`) to 2 principal components. Same dataset as `models/kmeans` (K-Means) and the regression notebooks, but used the same unsupervised way as K-Means — no label, and `species`/`island`/`sex` are not training features (only `species` is used afterward, as an external check). 342 of 344 rows remain after filtering `body_mass_g IS NOT NULL`.

**References:** `RESOURCES.md` (Full reference) | [CREATE MODEL (PCA) docs](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-pca) | `setup` (Setup guide)

---
## Setup

Set your project and location, authenticate, and create a shared dataset for the model.

> PCA trains on data already in BigQuery — no connection or remote model required. The model is created with `CREATE MODEL` and stored in your dataset. See the `setup` (Setup Reference) for details.

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

`CREATE MODEL` trains and stores the model in your dataset. There's no `input_label_cols` — every selected column is a feature to project. Exactly one of `num_principal_components` / `pca_explained_variance_ratio` is required — `num_principal_components = 2` is used here for a clean 2D visualization (Step 9 demonstrates the `pca_explained_variance_ratio` alternative). `scale_features` defaults to `TRUE` — important here since `body_mass_g` (thousands of grams) and `culmen_depth_mm` (tens of mm) are on very different scales.

> **Verified:** retraining this exact model reproduces `total_explained_variance_ratio` bit-for-bit every time — PCA has no random initialization to introduce retraining variance, unlike `models/kmeans` (K-Means).

```python
query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.pca_penguins`
OPTIONS(
  model_type = 'PCA',
  num_principal_components = 2,
  scale_features = TRUE,
  pca_solver = 'AUTO'
) AS
SELECT culmen_length_mm, culmen_depth_mm, flipper_length_mm, body_mass_g
FROM `bigquery-public-data.ml_datasets.penguins`
WHERE body_mass_g IS NOT NULL
"""
client.query(query).result()
print('Model pca_penguins created')
```

---
## Step 2 — Evaluate with `ML.EVALUATE`

`total_explained_variance_ratio` — the fraction of total variance captured by the retained components. No label, no agreement-with-ground-truth metric — this is intrinsic to the projection itself.

```python
query = f"""
SELECT *
FROM ML.EVALUATE(MODEL `{PROJECT_ID}.{DATASET_ID}.pca_penguins`)
"""
client.query(query).to_dataframe()
```

---
## Step 3 — Predict with `ML.PREDICT`

`ML.PREDICT` projects each row onto the components, returning `principal_component_1`, `principal_component_2`, etc. `species` is passed through untouched — it was never a training feature — purely so we can check, as an external validation, whether the projection separates species visually.

```python
query = f"""
SELECT species, principal_component_1, principal_component_2
FROM ML.PREDICT(
  MODEL `{PROJECT_ID}.{DATASET_ID}.pca_penguins`,
  (SELECT species, culmen_length_mm, culmen_depth_mm, flipper_length_mm, body_mass_g
   FROM `bigquery-public-data.ml_datasets.penguins`
   WHERE body_mass_g IS NOT NULL)
)
"""
client.query(query).to_dataframe()
```

---
## Step 4 — Visualize the projection

Plot the two principal components against each other, colored by the actual species — a quick visual read on how well 2 components separate the species without ever being trained on the label.

```python
import matplotlib.pyplot as plt

query = f"""
SELECT species, principal_component_1, principal_component_2
FROM ML.PREDICT(
  MODEL `{PROJECT_ID}.{DATASET_ID}.pca_penguins`,
  (SELECT species, culmen_length_mm, culmen_depth_mm, flipper_length_mm, body_mass_g
   FROM `bigquery-public-data.ml_datasets.penguins`
   WHERE body_mass_g IS NOT NULL)
)
"""
df = client.query(query).to_dataframe()

species_colors = dict(zip(sorted(df['species'].unique()), ['#4285F4', '#EA4335', '#34A853']))

fig, ax = plt.subplots(figsize=(7, 6))
for species, color in species_colors.items():
    subset = df[df['species'] == species]
    ax.scatter(subset['principal_component_1'], subset['principal_component_2'],
               c=color, label=species, edgecolors='k', linewidths=0.3, s=50)
ax.set_xlabel('Principal Component 1')
ax.set_ylabel('Principal Component 2')
ax.set_title('PCA Projection, colored by Actual Species')
ax.legend(loc='best', fontsize=8)
plt.tight_layout()
plt.show()
```

---
## Step 5 — Inspect the component loadings with `ML.PRINCIPAL_COMPONENTS`

One row per (`principal_component_id`, `feature`) with that feature's loading (eigenvector coefficient) on that component.

> **GOTCHA (verified):** `principal_component_id` is **0-indexed** (0, 1, ...) — unlike `models/kmeans` (K-Means)'s `centroid_id`, which is 1-indexed (1, 2, 3, ...). Don't assume consistent indexing conventions across unsupervised model types.

```python
query = f"""
SELECT *
FROM ML.PRINCIPAL_COMPONENTS(MODEL `{PROJECT_ID}.{DATASET_ID}.pca_penguins`)
ORDER BY principal_component_id, feature
"""
client.query(query).to_dataframe()
```

---
## Step 6 — Variance per component with `ML.PRINCIPAL_COMPONENT_INFO`

`eigenvalue`, `explained_variance_ratio`, and `cumulative_explained_variance_ratio` per component — use this to pick a sensible component count via the "elbow" in cumulative variance.

```python
query = f"""
SELECT *
FROM ML.PRINCIPAL_COMPONENT_INFO(MODEL `{PROJECT_ID}.{DATASET_ID}.pca_penguins`)
"""
client.query(query).to_dataframe()
```

---
## Step 7 — Introspect the training features with `ML.FEATURE_INFO`

```python
query = f"""
SELECT *
FROM ML.FEATURE_INFO(MODEL `{PROJECT_ID}.{DATASET_ID}.pca_penguins`)
"""
client.query(query).to_dataframe()
```

---
## Step 8 — Detect outliers with `ML.DETECT_ANOMALIES`

`contamination = 0.05` flags the 5% of rows with the largest reconstruction error (`mean_squared_error`) as anomalies — no labels required.

> **GOTCHA (verified, same as `models/kmeans` (K-Means)):** the input-data argument is **required** for PCA too — calling this with only `(MODEL, STRUCT(contamination))` errors immediately: `"DETECT_ANOMALIES expects 3 arguments for PCA models but 2 were passed."` Always pass the scoring data as the 3rd argument. This resolves a question the K-Means notebook left open (whether the requirement was K-Means-specific) — it is not; PCA shares it.

```python
query = f"""
SELECT *
FROM ML.DETECT_ANOMALIES(
  MODEL `{PROJECT_ID}.{DATASET_ID}.pca_penguins`,
  STRUCT(0.05 AS contamination),
  (SELECT culmen_length_mm, culmen_depth_mm, flipper_length_mm, body_mass_g
   FROM `bigquery-public-data.ml_datasets.penguins`
   WHERE body_mass_g IS NOT NULL)
)
WHERE is_anomaly
ORDER BY mean_squared_error DESC
"""
client.query(query).to_dataframe()
```

---
## Step 9 — Package the projection as an embedding with `ML.GENERATE_EMBEDDING`

Wraps the same PC1/PC2 projection from Step 3 into a single `ml_generate_embedding_result` `ARRAY<FLOAT>` column — purpose-built for `VECTOR_SEARCH`.

> **Verified:** the array values match `ML.PREDICT`'s `principal_component_1`/`principal_component_2` columns exactly, in order.

```python
query = f"""
SELECT species, ml_generate_embedding_result
FROM ML.GENERATE_EMBEDDING(
  MODEL `{PROJECT_ID}.{DATASET_ID}.pca_penguins`,
  (SELECT species, culmen_length_mm, culmen_depth_mm, flipper_length_mm, body_mass_g
   FROM `bigquery-public-data.ml_datasets.penguins`
   WHERE body_mass_g IS NOT NULL LIMIT 5)
)
"""
client.query(query).to_dataframe()
```

---
## Step 10 — In-model preprocessing with the `TRANSFORM` clause

Adds `island` as a categorical feature alongside the four numeric measurements.

> **Verified (and reproduced on a second retrain, since PCA is deterministic):** `total_explained_variance_ratio` drops from ~0.88 to ~0.76 with the same 2 components. This makes sense and isn't a gotcha the way the analogous change was for K-Means: `island` gets one-hot encoded into extra dimensions, so the same 2 components must now spread their explanatory power across more total variance — with more features contributing variance, 2 components capture a smaller fraction of a larger whole.

```python
query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.pca_penguins_transform`
TRANSFORM(
  culmen_length_mm, culmen_depth_mm, flipper_length_mm, body_mass_g, island
)
OPTIONS(
  model_type = 'PCA',
  num_principal_components = 2,
  scale_features = TRUE
) AS
SELECT culmen_length_mm, culmen_depth_mm, flipper_length_mm, body_mass_g, island
FROM `bigquery-public-data.ml_datasets.penguins`
WHERE body_mass_g IS NOT NULL
"""
client.query(query).result()
print('Model pca_penguins_transform created')
```

```python
query = f"""
SELECT *
FROM ML.EVALUATE(MODEL `{PROJECT_ID}.{DATASET_ID}.pca_penguins_transform`)
"""
client.query(query).to_dataframe()
```

---
## Step 11 — `pca_explained_variance_ratio`: an alternative to a fixed component count

PCA has **no hyperparameter tuning** (`num_trials`/`HPARAM_RANGE` don't apply), so unlike every supervised/K-Means notebook in this project, there's no `ML.TRIAL_INFO` step here. Instead, `pca_explained_variance_ratio` lets you target a retained-information level and let BigQuery ML pick the component count automatically.

> **Verified:** targeting 0.90 selects **3** components (2 components only reach ~0.88, just short of the 0.90 target — the 3rd is needed to cross it), reaching a cumulative ratio of ~0.97.

```python
query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.pca_penguins_variance`
OPTIONS(
  model_type = 'PCA',
  pca_explained_variance_ratio = 0.90,
  scale_features = TRUE
) AS
SELECT culmen_length_mm, culmen_depth_mm, flipper_length_mm, body_mass_g
FROM `bigquery-public-data.ml_datasets.penguins`
WHERE body_mass_g IS NOT NULL
"""
client.query(query).result()
print('Model pca_penguins_variance created')
```

```python
query = f"""
SELECT *
FROM ML.EVALUATE(MODEL `{PROJECT_ID}.{DATASET_ID}.pca_penguins_variance`)
"""
client.query(query).to_dataframe()
```

```python
query = f"""
SELECT *
FROM ML.PRINCIPAL_COMPONENT_INFO(MODEL `{PROJECT_ID}.{DATASET_ID}.pca_penguins_variance`)
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
FROM ML.EVALUATE(MODEL `statmike-mlops-349915.bq_ml.pca_penguins`)
```

---
## Examples — BigFrames

BigFrames provides a scikit-learn-style API (`bigframes.ml`) that trains BigQuery ML models under the hood. PCA has a genuine first-class wrapper: `bigframes.ml.decomposition.PCA`.

> Unlike scikit-learn, BigFrames' `PCA` has no `.transform()`/`.fit_transform()` — call `.predict()` after `.fit()` to get the projected components, matching BigQuery ML's `ML.PREDICT` convention rather than scikit-learn's `transform` API.

> **Verified:** training a fresh, independently-named PCA model here through BigFrames reproduces the exact same `total_explained_variance_ratio` as Step 2's manually-named model above — a third independent confirmation that PCA training is fully deterministic, and a contrast to `models/kmeans` (K-Means), where BigFrames' independently-trained model produced yet a different value each time.

```python
import bigframes.pandas as bpd

bpd.close_session()  # Reset session to apply project/location settings
bpd.options.bigquery.project = PROJECT_ID
bpd.options.bigquery.location = LOCATION
```

```python
from bigframes.ml.decomposition import PCA

# Load data as a BigFrames DataFrame
df = bpd.read_gbq('bigquery-public-data.ml_datasets.penguins')
df = df[df['body_mass_g'].notnull()]

feature_cols = ['culmen_length_mm', 'culmen_depth_mm', 'flipper_length_mm', 'body_mass_g']
X = df[feature_cols]

# Train (creates a BigQuery ML model behind the scenes)
model = PCA(n_components=2)
model.fit(X)

# Evaluate
model.score(X).to_pandas()
```
