# K-Means — BigQuery ML

Train an **unsupervised clustering** model with `CREATE MODEL` (model_type = `KMEANS`) — no label column, just `k` groups discovered from the data itself — then walk the full model lifecycle: evaluate, predict, visualize, inspect centroids, detect anomalies, apply in-model preprocessing, and tune hyperparameters. No data leaves BigQuery, and no separate training infrastructure is needed.

**Lifecycle:** `CREATE MODEL` → `ML.EVALUATE` → `ML.PREDICT` → visualize → `ML.CENTROIDS` → `ML.FEATURE_INFO` → `ML.DETECT_ANOMALIES` → `TRANSFORM` clause → hyperparameter tuning (`ML.TRIAL_INFO`)

**This is the first unsupervised model in this project — a few things are genuinely different from every classifier/regressor notebook so far:**
- No `input_label_cols` — the model has no target to predict, only groups to discover.
- `ML.EVALUATE`'s metrics (`davies_bouldin_index`, `mean_squared_distance`) measure internal cluster quality, **not** agreement with any ground truth — there is no `roc_auc`/`r2_score` equivalent.
- To sanity-check whether the clusters mean anything, this notebook carries the real `species` column through `ML.PREDICT` purely as an **external check** — it's never used to train the model.
- **Verified: K-means retraining is genuinely non-deterministic here**, even with `kmeans_init_method = 'KMEANS++'` — `davies_bouldin_index` and the specific cluster-to-species alignment both vary across separate `CREATE OR REPLACE MODEL` calls on identical SQL (see Step 8 for the full story).

**When to use K-means:**
- Customer/market segmentation and grouping unlabeled records
- Exploratory analysis to discover natural structure in data
- Unsupervised anomaly/outlier detection (distance-to-centroid based, via `ML.DETECT_ANOMALIES`)
- Fast, in-SQL clustering at BigQuery scale with no labels required

**Data:** [`bigquery-public-data.ml_datasets.penguins`](https://console.cloud.google.com/marketplace/product/bigquery-public-datasets) — cluster on four physical measurements (`culmen_length_mm`, `culmen_depth_mm`, `flipper_length_mm`, `body_mass_g`). Same dataset as `models/linear_regression` (Linear Regression), `models/boosted_tree_regressor` (Boosted Tree Regressor), `models/random_forest_regressor` (Random Forest Regressor), `models/dnn_regressor` (DNN Regressor), and `models/wide_and_deep_regressor` (Wide & Deep Regressor), but used completely differently here — no label, and `species`/`island`/`sex` are not training features (only `species` is used afterward, as an external check). 342 of 344 rows remain after filtering `body_mass_g IS NOT NULL` — a different row count than the regression notebooks, which also filter on `sex`.

**References:** `RESOURCES.md` (Full reference) | [CREATE MODEL (K-means) docs](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-kmeans) | `setup` (Setup guide)

---
## Setup

Set your project and location, authenticate, and create a shared dataset for the model.

> K-means trains on data already in BigQuery — no connection or remote model required. The model is created with `CREATE MODEL` and stored in your dataset. See the `setup` (Setup Reference) for details.

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

`CREATE MODEL` trains and stores the model in your dataset. There's no `input_label_cols` — every selected column is a clustering feature. `num_clusters = 3` is a deliberate, informed choice (there are 3 penguin species in this data), not a default guess. `kmeans_init_method = 'KMEANS++'` gives more stable, generally better convergence than the `RANDOM` default — though see Step 9: even with `KMEANS++`, retraining is not fully deterministic. `standardize_features` defaults to `TRUE` — important here since `body_mass_g` (thousands of grams) and `culmen_depth_mm` (tens of mm) are on very different scales.

```python
query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.kmeans_penguins`
OPTIONS(
  model_type = 'KMEANS',
  num_clusters = 3,
  kmeans_init_method = 'KMEANS++',
  distance_type = 'EUCLIDEAN'
) AS
SELECT culmen_length_mm, culmen_depth_mm, flipper_length_mm, body_mass_g
FROM `bigquery-public-data.ml_datasets.penguins`
WHERE body_mass_g IS NOT NULL
"""
client.query(query).result()
print('Model kmeans_penguins created')
```

---
## Step 2 — Evaluate with `ML.EVALUATE`

`davies_bouldin_index` (lower is better — more separated clusters) and `mean_squared_distance` (lower is better — tighter clusters). Neither metric uses or needs a label — this is intrinsic cluster quality, not agreement with any ground truth.

```python
query = f"""
SELECT *
FROM ML.EVALUATE(MODEL `{PROJECT_ID}.{DATASET_ID}.kmeans_penguins`)
"""
client.query(query).to_dataframe()
```

---
## Step 3 — Predict with `ML.PREDICT`

`ML.PREDICT` returns `CENTROID_ID` (the assigned cluster) and `NEAREST_CENTROIDS_DISTANCE` (distance to every centroid). `species` is passed through untouched — it was never a training feature — purely so we can check, as an external validation, how well the unsupervised clusters line up with the real species labels.

> **Result below, honestly reported as-is:** one cluster recovers Gentoo penguins almost perfectly, while the other two mix Adelie and Chinstrap — those two species overlap more in body measurements than either does with Gentoo. Unsupervised clustering finds real structure here, but not a perfect species partition. **Caveat (see Step 8): K-means retraining is non-deterministic**, so re-running this exact notebook can shift which species end up cleanly separated and which overlap — don't treat this specific split as guaranteed to reproduce bit-for-bit.

```python
query = f"""
SELECT species, CENTROID_ID, COUNT(*) AS n
FROM ML.PREDICT(
  MODEL `{PROJECT_ID}.{DATASET_ID}.kmeans_penguins`,
  (SELECT species, culmen_length_mm, culmen_depth_mm, flipper_length_mm, body_mass_g
   FROM `bigquery-public-data.ml_datasets.penguins`
   WHERE body_mass_g IS NOT NULL)
)
GROUP BY species, CENTROID_ID
ORDER BY species, CENTROID_ID
"""
client.query(query).to_dataframe()
```

---
## Step 4 — Visualize the clusters

Plot two of the clustering features against each other, colored by the *predicted* cluster and shaped by the *actual* species — a quick visual read on where the clusters agree and disagree with species.

```python
import matplotlib.pyplot as plt

query = f"""
SELECT species, CENTROID_ID, flipper_length_mm, body_mass_g
FROM ML.PREDICT(
  MODEL `{PROJECT_ID}.{DATASET_ID}.kmeans_penguins`,
  (SELECT species, culmen_length_mm, culmen_depth_mm, flipper_length_mm, body_mass_g
   FROM `bigquery-public-data.ml_datasets.penguins`
   WHERE body_mass_g IS NOT NULL)
)
"""
df = client.query(query).to_dataframe()

cluster_colors = {1: '#4285F4', 2: '#EA4335', 3: '#34A853'}
species_markers = dict(zip(sorted(df['species'].unique()), ['o', '^', 's']))

fig, ax = plt.subplots(figsize=(7, 6))
for species, marker in species_markers.items():
    subset = df[df['species'] == species]
    ax.scatter(
        subset['flipper_length_mm'], subset['body_mass_g'],
        c=[cluster_colors[c] for c in subset['CENTROID_ID']],
        marker=marker, label=species, edgecolors='k', linewidths=0.3, s=50
    )
ax.set_xlabel('Flipper Length (mm)')
ax.set_ylabel('Body Mass (g)')
ax.set_title('K-Means Clusters (color) vs Actual Species (marker shape)')
ax.legend(loc='upper left', fontsize=8)
plt.tight_layout()
plt.show()
```

---
## Step 5 — Inspect cluster centers with `ML.CENTROIDS`

One row per (`centroid_id`, `feature`) with the centroid's coordinate on that feature — this is how you interpret what each cluster "means" (e.g. the cluster with the highest `body_mass_g` and `flipper_length_mm` is consistent with it being the Gentoo cluster, the largest of the three species).

```python
query = f"""
SELECT *
FROM ML.CENTROIDS(MODEL `{PROJECT_ID}.{DATASET_ID}.kmeans_penguins`)
ORDER BY centroid_id, feature
"""
client.query(query).to_dataframe()
```

---
## Step 6 — Introspect the training features with `ML.FEATURE_INFO`

```python
query = f"""
SELECT *
FROM ML.FEATURE_INFO(MODEL `{PROJECT_ID}.{DATASET_ID}.kmeans_penguins`)
"""
client.query(query).to_dataframe()
```

---
## Step 7 — Detect outliers with `ML.DETECT_ANOMALIES`

`contamination = 0.05` flags the 5% of rows with the largest `normalized_distance` from their nearest centroid as anomalies — no labels required.

> **GOTCHA (verified):** for `KMEANS`, the input-data argument is **required** — calling this with only `(MODEL, STRUCT(contamination))` errors immediately: `"DETECT_ANOMALIES expects 3 arguments for KMEANS models but 2 were passed."` Always pass the scoring data as the 3rd argument.

```python
query = f"""
SELECT *
FROM ML.DETECT_ANOMALIES(
  MODEL `{PROJECT_ID}.{DATASET_ID}.kmeans_penguins`,
  STRUCT(0.05 AS contamination),
  (SELECT culmen_length_mm, culmen_depth_mm, flipper_length_mm, body_mass_g
   FROM `bigquery-public-data.ml_datasets.penguins`
   WHERE body_mass_g IS NOT NULL)
)
WHERE is_anomaly
ORDER BY normalized_distance DESC
"""
client.query(query).to_dataframe()
```

---
## Step 8 — In-model preprocessing with the `TRANSFORM` clause

Adds `island` as a categorical feature alongside the four (explicitly scaled) numeric measurements. `ML.STANDARD_SCALER` here is redundant with the model's own `standardize_features = TRUE` default, but shown for clarity.

> **GOTCHA (verified):** K-means retraining is genuinely non-deterministic here, even with `kmeans_init_method = 'KMEANS++'`. Retraining both the baseline (Step 1) and this model multiple times on identical SQL shows `davies_bouldin_index` and the specific cluster-to-species alignment both vary meaningfully across separate `CREATE OR REPLACE MODEL` calls on the exact same SQL — sometimes the baseline's `davies_bouldin_index` is lower, sometimes this transform's is; sometimes Gentoo ends up in one clean cluster, sometimes it's split, regardless of whether `island` was included (the BigFrames section below independently confirms this too — same config, a third different `davies_bouldin_index`). **This means a single before/after comparison is not reliable evidence that a specific feature change causes a specific effect** on either the intrinsic metric or external alignment — you'd need to retrain each config multiple times and look at the range, not one sample. Separately: `davies_bouldin_index` measures internal cluster separation in whatever feature space you give it — it says nothing about whether clusters line up with any domain-meaningful grouping, so don't treat a lower value alone as proof of a "better" or "more useful" clustering.

```python
query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.kmeans_penguins_transform`
TRANSFORM(
  ML.STANDARD_SCALER(culmen_length_mm) OVER() AS culmen_length_mm,
  ML.STANDARD_SCALER(culmen_depth_mm) OVER() AS culmen_depth_mm,
  ML.STANDARD_SCALER(flipper_length_mm) OVER() AS flipper_length_mm,
  ML.STANDARD_SCALER(body_mass_g) OVER() AS body_mass_g,
  island
)
OPTIONS(
  model_type = 'KMEANS',
  num_clusters = 3,
  kmeans_init_method = 'KMEANS++',
  distance_type = 'EUCLIDEAN'
) AS
SELECT culmen_length_mm, culmen_depth_mm, flipper_length_mm, body_mass_g, island
FROM `bigquery-public-data.ml_datasets.penguins`
WHERE body_mass_g IS NOT NULL
"""
client.query(query).result()
print('Model kmeans_penguins_transform created')
```

```python
# Confirm with ML.EVALUATE -- see the markdown above for why comparing
# this number to Step 2's isn't as simple as "higher/lower is the effect
# of adding island."
query = f"""
SELECT *
FROM ML.EVALUATE(MODEL `{PROJECT_ID}.{DATASET_ID}.kmeans_penguins_transform`)
"""
client.query(query).to_dataframe()
```

```python
query = f"""
SELECT species, CENTROID_ID, COUNT(*) AS n
FROM ML.PREDICT(
  MODEL `{PROJECT_ID}.{DATASET_ID}.kmeans_penguins_transform`,
  (SELECT species, culmen_length_mm, culmen_depth_mm, flipper_length_mm, body_mass_g, island
   FROM `bigquery-public-data.ml_datasets.penguins`
   WHERE body_mass_g IS NOT NULL)
)
GROUP BY species, CENTROID_ID
ORDER BY species, CENTROID_ID
"""
client.query(query).to_dataframe()
```

---
## Step 9 — Hyperparameter tuning

`num_clusters` is the primary tunable option, searched via `HPARAM_RANGE` with the default `davies_bouldin_index` objective (minimize).

> **Result below, honestly reported as-is — and another instance of the non-determinism from Step 8:** this run's tuning selected `num_clusters=2` as optimal, not 3. A separate pre-validation run of this exact same search space selected `num_clusters=3` (matching the true species count) instead. Both are real, both are "correct" outputs of the identical tuning configuration — they just landed on different local optima. This reinforces the same lesson: don't treat a single HP-tuning run's chosen value as the definitive answer for `num_clusters` on this kind of data; if the choice matters, run the search more than once (or with more trials) and look for a value that keeps winning, not just whichever won once.

```python
query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.kmeans_penguins_tuned`
OPTIONS(
  model_type = 'KMEANS',
  num_clusters = HPARAM_RANGE(2, 10),
  kmeans_init_method = 'KMEANS++',
  distance_type = 'EUCLIDEAN',
  num_trials = 6,
  max_parallel_trials = 3,
  hparam_tuning_objectives = ['davies_bouldin_index']
) AS
SELECT culmen_length_mm, culmen_depth_mm, flipper_length_mm, body_mass_g
FROM `bigquery-public-data.ml_datasets.penguins`
WHERE body_mass_g IS NOT NULL
"""
client.query(query).result()
print('Tuned model created')
```

```python
query = f"""
SELECT
  trial_id,
  hyperparameters,
  hparam_tuning_evaluation_metrics.davies_bouldin_index AS davies_bouldin_index,
  is_optimal
FROM ML.TRIAL_INFO(MODEL `{PROJECT_ID}.{DATASET_ID}.kmeans_penguins_tuned`)
ORDER BY davies_bouldin_index ASC
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
FROM ML.EVALUATE(MODEL `statmike-mlops-349915.bq_ml.kmeans_penguins`)
```

---
## Examples — BigFrames

BigFrames provides a scikit-learn-style API (`bigframes.ml`) that trains BigQuery ML models under the hood. Unlike DNN/wide-and-deep, **K-means has a genuine first-class wrapper**: `bigframes.ml.cluster.KMeans`.

```python
import bigframes.pandas as bpd

bpd.close_session()  # Reset session to apply project/location settings
bpd.options.bigquery.project = PROJECT_ID
bpd.options.bigquery.location = LOCATION
```

```python
from bigframes.ml.cluster import KMeans

# Load data as a BigFrames DataFrame
df = bpd.read_gbq('bigquery-public-data.ml_datasets.penguins')
df = df[df['body_mass_g'].notnull()]

feature_cols = ['culmen_length_mm', 'culmen_depth_mm', 'flipper_length_mm', 'body_mass_g']
X = df[feature_cols]

# Train (creates a BigQuery ML model behind the scenes)
model = KMeans(n_clusters=3)
model.fit(X)

# Evaluate
model.score(X).to_pandas()
```
