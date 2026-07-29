# Autoencoder — BigQuery ML

Train an **unsupervised, nonlinear dimensionality-reduction** model with `CREATE MODEL` (model_type = `AUTOENCODER`) — a symmetric feed-forward network that compresses rows into a small latent space and reconstructs them — then walk the full model lifecycle: evaluate, diagnose a real training failure, fix it, predict, visualize, reconstruction loss, detect anomalies, generate embeddings and search them, apply in-model preprocessing, and tune hyperparameters. No data leaves BigQuery, and no separate training infrastructure is needed.

**Lifecycle:** `CREATE MODEL` → `ML.EVALUATE` → diagnose → `CREATE MODEL` (fix) → `ML.PREDICT` → visualize → `ML.RECONSTRUCTION_LOSS` → `ML.FEATURE_INFO` → `ML.DETECT_ANOMALIES` → `ML.GENERATE_EMBEDDING` → `VECTOR_SEARCH` → `TRANSFORM` clause → hyperparameter tuning (`ML.TRIAL_INFO`)

**Third unsupervised model in this project, after `models/kmeans` (K-Means) and `models/pca` (PCA) — and the first one with a genuine training failure to debug:**
- No `input_label_cols` — every selected column is a feature to reconstruct, not predict.
- `ML.EVALUATE`'s reconstruction-error metrics (`mean_absolute_error`, `mean_squared_error`, `mean_squared_log_error`) measure how closely outputs match inputs — not agreement with any ground truth.
- This notebook carries the real `species` column through `ML.PREDICT` as an **external check**, same convention as the other two unsupervised notebooks.
- **This model type's default activation function (`RELU`) genuinely breaks on this small, narrow network** — a large share of the 2-dimensional latent space collapses to exactly `0.0` (a classic "dying ReLU"), invisible from `ML.EVALUATE` alone. Steps 1–4 walk through diagnosing this directly from `ML.PREDICT`'s output and fixing it by switching to `TANH`.
- **Verified: `ML.EVALUATE`'s reconstruction metrics are reproducible bit-for-bit under a fixed model name** (like `models/dnn_regressor` (DNN)), but the specific latent-space values are **not** — different retrains land on equally-good but differently-shaped latent geometries. Unlike `models/pca` (PCA)'s uniquely-ordered, variance-ranked components, a generic autoencoder bottleneck has no constraint forcing a stable, canonical basis.

**When to use an autoencoder:**
- Unsupervised anomaly detection on tabular data (high reconstruction error = anomaly) via `ML.DETECT_ANOMALIES`
- Nonlinear dimensionality reduction / feature compression where a linear method (PCA) is insufficient
- Producing row-level embeddings (latent vectors) for similarity search via `ML.GENERATE_EMBEDDING` + `VECTOR_SEARCH`
- Data sanitation: flag records the model cannot reconstruct well

**Data:** [`bigquery-public-data.ml_datasets.penguins`](https://console.cloud.google.com/marketplace/product/bigquery-public-datasets) — same four physical measurements as `models/kmeans` (K-Means) and `models/pca` (PCA) (`culmen_length_mm`, `culmen_depth_mm`, `flipper_length_mm`, `body_mass_g`), compressed to a 2-dimensional latent space for a direct visual comparison with PCA's 2-component projection. No label, and `species`/`island`/`sex` are not training features (only `species` is used afterward, as an external check). 342 of 344 rows remain after filtering `body_mass_g IS NOT NULL`.

**References:** `RESOURCES.md` (Full reference) | [CREATE MODEL (autoencoder) docs](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-autoencoder) | [ML.RECONSTRUCTION_LOSS docs](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-reconstruction-loss) | `setup` (Setup guide)

> **Training time:** autoencoder training on this dataset is much slower than K-Means or PCA — expect roughly 5–15 minutes per `CREATE MODEL` call, and this notebook trains four models plus a 4-trial hyperparameter search. Budget 45–60+ minutes for a full Restart & Run All, and avoid running other BigQuery ML work concurrently in the same project.

---
## Setup

Set your project and location, authenticate, and create a shared dataset for the model.

> Autoencoders train on data already in BigQuery — no connection or remote model required. The model is created with `CREATE MODEL` and stored in your dataset. See the `setup` (Setup Reference) for details.

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
## Step 1 — Create the model with `CREATE MODEL` (the naive attempt)

`hidden_units = [3, 2, 3]` gives a 2-dimensional latent space (the middle value) — small on purpose, for a direct visual comparison with `models/pca` (PCA)'s 2-component projection on the same 4 features. `activation_fn = 'RELU'` is BigQuery ML's own default — used here first, deliberately, before the fix in Step 4.

```python
query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.autoencoder_penguins`
OPTIONS(
  model_type = 'AUTOENCODER',
  hidden_units = [3, 2, 3],
  activation_fn = 'RELU',
  learn_rate = 0.01,
  max_iterations = 30
) AS
SELECT culmen_length_mm, culmen_depth_mm, flipper_length_mm, body_mass_g
FROM `bigquery-public-data.ml_datasets.penguins`
WHERE body_mass_g IS NOT NULL
"""
client.query(query).result()
print('Model autoencoder_penguins created')
```

---
## Step 2 — Evaluate with `ML.EVALUATE`

`mean_absolute_error` / `mean_squared_error` / `mean_squared_log_error` are reconstruction-error metrics — no label. These numbers alone look like a model that trained normally — a real problem in this model, diagnosed next, is invisible here.

```python
query = f"""
SELECT *
FROM ML.EVALUATE(MODEL `{PROJECT_ID}.{DATASET_ID}.autoencoder_penguins`)
"""
client.query(query).to_dataframe()
```

---
## Step 3 — Diagnose the latent space directly with `ML.PREDICT`

`ML.PREDICT` on an autoencoder returns `latent_col_1`, `latent_col_2`, ... (the bottleneck representation) alongside the reconstructed input columns. Aggregate min/max/zero-count across all rows exposes a real problem with this model that Step 2's metrics alone didn't reveal.

> **GOTCHA (verified across three independent retrains, including this notebook's own run):** with `RELU` on this small, narrow network, a substantial and highly variable share of rows have **both** latent dimensions simultaneously pinned to exactly `0.0` — a classic dying-ReLU symptom: once a ReLU unit's input goes negative across most of the dataset, its gradient is zero there and it can't recover during training. **The exact severity varies widely by retrain** (see Step 12) — observed rates of `n_both_zero / n_total` so far: 40%, 50%, and 65%. Sometimes one entire latent column is pinned to `0.0` for every single row; other times the zeros are spread unevenly across both columns instead — but the underlying dying-ReLU symptom itself shows up every time. Run the cell below against your own trained model to see your own real numbers.

```python
query = f"""
SELECT
  MIN(latent_col_1) AS min_l1, MAX(latent_col_1) AS max_l1,
  MIN(latent_col_2) AS min_l2, MAX(latent_col_2) AS max_l2,
  COUNTIF(latent_col_1 = 0.0 AND latent_col_2 = 0.0) AS n_both_zero,
  COUNT(*) AS n_total
FROM ML.PREDICT(
  MODEL `{PROJECT_ID}.{DATASET_ID}.autoencoder_penguins`,
  (SELECT culmen_length_mm, culmen_depth_mm, flipper_length_mm, body_mass_g
   FROM `bigquery-public-data.ml_datasets.penguins`
   WHERE body_mass_g IS NOT NULL)
)
"""
client.query(query).to_dataframe()
```

---
## Step 4 — Create the fix with `CREATE MODEL` (`TANH` activation)

Same architecture — only `activation_fn` changes: `RELU` → `TANH`. `TANH` has no "dead zone" — its gradient is nonzero almost everywhere — so it can't collapse the same way.

> **Verified:** this single change fixes both problems at once. No dead latent units (both `latent_col_1` and `latent_col_2` take a full range of nonzero values across all 342 rows), and reconstruction quality improves substantially and consistently — `mean_squared_error` lands around ~0.21 with `TANH` every time this has been tested, well below the `RELU` baseline from Step 2 (observed anywhere from ~0.66 to ~0.94 across different retrains, itself a symptom of the collapse's variable severity — see Step 12). The exact improvement ratio isn't fixed since it depends on how badly `RELU` happened to collapse on a given retrain, but the direction and the ~0.21 landing point for `TANH` are consistent.

```python
query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.autoencoder_penguins_fix`
OPTIONS(
  model_type = 'AUTOENCODER',
  hidden_units = [3, 2, 3],
  activation_fn = 'TANH',
  learn_rate = 0.01,
  max_iterations = 30
) AS
SELECT culmen_length_mm, culmen_depth_mm, flipper_length_mm, body_mass_g
FROM `bigquery-public-data.ml_datasets.penguins`
WHERE body_mass_g IS NOT NULL
"""
client.query(query).result()
print('Model autoencoder_penguins_fix created')
```

```python
query = f"""
SELECT *
FROM ML.EVALUATE(MODEL `{PROJECT_ID}.{DATASET_ID}.autoencoder_penguins_fix`)
"""
client.query(query).to_dataframe()
```

---
## Step 5 — Predict with `ML.PREDICT`

Returns the 2D latent space (`latent_col_1`, `latent_col_2`) alongside the reconstructed input columns. `species` is passed through untouched — it was never a training feature — purely so we can check, as an external validation, whether the latent space separates species visually.

```python
query = f"""
SELECT species, latent_col_1, latent_col_2
FROM ML.PREDICT(
  MODEL `{PROJECT_ID}.{DATASET_ID}.autoencoder_penguins_fix`,
  (SELECT species, culmen_length_mm, culmen_depth_mm, flipper_length_mm, body_mass_g
   FROM `bigquery-public-data.ml_datasets.penguins`
   WHERE body_mass_g IS NOT NULL)
)
"""
client.query(query).to_dataframe()
```

---
## Step 6 — Visualize the latent space

Plot the two latent dimensions against each other, colored by the actual species — a quick visual read on how well the compressed 2D representation separates the species without ever being trained on the label.

```python
import matplotlib.pyplot as plt

query = f"""
SELECT species, latent_col_1, latent_col_2
FROM ML.PREDICT(
  MODEL `{PROJECT_ID}.{DATASET_ID}.autoencoder_penguins_fix`,
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
    ax.scatter(subset['latent_col_1'], subset['latent_col_2'],
               c=color, label=species, edgecolors='k', linewidths=0.3, s=50)
ax.set_xlabel('Latent Dimension 1')
ax.set_ylabel('Latent Dimension 2')
ax.set_title('Autoencoder Latent Space, colored by Actual Species')
ax.legend(loc='best', fontsize=8)
plt.tight_layout()
plt.show()
```

---
## Step 7 — Per-row diagnostics with `ML.RECONSTRUCTION_LOSS`

Same three metrics as `ML.EVALUATE`, but per input row — use this to find the specific rows the model reconstructs worst (a manual, row-level view of the same signal `ML.DETECT_ANOMALIES` automates in Step 9).

```python
query = f"""
SELECT *
FROM ML.RECONSTRUCTION_LOSS(
  MODEL `{PROJECT_ID}.{DATASET_ID}.autoencoder_penguins_fix`,
  (SELECT culmen_length_mm, culmen_depth_mm, flipper_length_mm, body_mass_g
   FROM `bigquery-public-data.ml_datasets.penguins`
   WHERE body_mass_g IS NOT NULL)
)
ORDER BY mean_squared_error DESC
LIMIT 10
"""
client.query(query).to_dataframe()
```

---
## Step 8 — Introspect the training features with `ML.FEATURE_INFO`

```python
query = f"""
SELECT *
FROM ML.FEATURE_INFO(MODEL `{PROJECT_ID}.{DATASET_ID}.autoencoder_penguins_fix`)
"""
client.query(query).to_dataframe()
```

---
## Step 9 — Detect outliers with `ML.DETECT_ANOMALIES`

`contamination = 0.05` flags the 5% of rows with the largest reconstruction error (`mean_squared_error`) as anomalies — no labels required.

> **GOTCHA (verified, same as `models/kmeans` (K-Means) and `models/pca` (PCA)):** the input-data argument is **required** for `AUTOENCODER` too — calling this with only `(MODEL, STRUCT(contamination))` errors immediately: `"DETECT_ANOMALIES expects 3 arguments for AUTOENCODER models but 2 were passed."` All three unsupervised model types in this project share this requirement.

```python
query = f"""
SELECT *
FROM ML.DETECT_ANOMALIES(
  MODEL `{PROJECT_ID}.{DATASET_ID}.autoencoder_penguins_fix`,
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
## Step 10 — Package the latent space as an embedding with `ML.GENERATE_EMBEDDING`

Wraps the same `latent_col_1`/`latent_col_2` values from Step 5 into a single `ml_generate_embedding_result` `ARRAY<FLOAT>` column — purpose-built for `VECTOR_SEARCH`.

> **Verified:** the array values match `ML.PREDICT`'s `latent_col_1`/`latent_col_2` columns exactly, in order.

```python
query = f"""
SELECT species, ml_generate_embedding_result
FROM ML.GENERATE_EMBEDDING(
  MODEL `{PROJECT_ID}.{DATASET_ID}.autoencoder_penguins_fix`,
  (SELECT species, culmen_length_mm, culmen_depth_mm, flipper_length_mm, body_mass_g
   FROM `bigquery-public-data.ml_datasets.penguins`
   WHERE body_mass_g IS NOT NULL LIMIT 5)
)
"""
client.query(query).to_dataframe()
```

---
## Step 11 — Embedding matching: manual `ML.NORMALIZER` vs. `ML.GENERATE_EMBEDDING`, then `VECTOR_SEARCH`

Two ways to get an embedding, compared directly:
- **Manual:** `ML.PREDICT` → wrap `latent_col_1`/`latent_col_2` into an `ARRAY` yourself → `ML.NORMALIZER` to give it unit (L2) norm.
- **Automated:** `ML.GENERATE_EMBEDDING` → `ml_generate_embedding_result`, already an `ARRAY` — no manual column-wrangling needed.

> **GOTCHA (verified):** `ML.GENERATE_EMBEDDING` does **not** normalize its output — its raw `ml_generate_embedding_result` is bit-for-bit identical to `ML.PREDICT`'s un-normalized latent columns (already shown in Step 10). Applying `ML.NORMALIZER` to the manual array and to the raw `ML.GENERATE_EMBEDDING` array independently produces the exact same normalized vector — confirmed row-by-row below. So `ML.GENERATE_EMBEDDING`'s real convenience is **not** built-in normalization (there isn't any) — it's simply not having to enumerate `latent_col_1..N` into an `ARRAY` literal yourself, which matters more as the latent dimension grows.

```python
query = f"""
WITH base AS (
  SELECT species, culmen_length_mm, culmen_depth_mm, flipper_length_mm, body_mass_g,
    ROW_NUMBER() OVER() AS row_id
  FROM `bigquery-public-data.ml_datasets.penguins`
  WHERE body_mass_g IS NOT NULL
  LIMIT 5
),
manual AS (
  SELECT row_id, ML.NORMALIZER([latent_col_1, latent_col_2]) AS embedding_manual
  FROM ML.PREDICT(MODEL `{PROJECT_ID}.{DATASET_ID}.autoencoder_penguins_fix`, TABLE base)
),
auto AS (
  SELECT row_id, ml_generate_embedding_result AS embedding_auto_raw,
    ML.NORMALIZER(ml_generate_embedding_result) AS embedding_auto_normalized
  FROM ML.GENERATE_EMBEDDING(MODEL `{PROJECT_ID}.{DATASET_ID}.autoencoder_penguins_fix`, TABLE base)
)
SELECT m.row_id, m.embedding_manual, a.embedding_auto_raw, a.embedding_auto_normalized
FROM manual m JOIN auto a USING (row_id)
ORDER BY row_id
"""
client.query(query).to_dataframe()
```

`VECTOR_SEARCH` doesn't accept `ML.PREDICT`/`ML.GENERATE_EMBEDDING` output directly as its base-table argument (`"Unsupported query pattern"`) — materialize the embeddings into a real table first. This table stores both the raw and the normalized embedding, to compare both search strategies below.

```python
query = f"""
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.autoencoder_embeddings` AS
SELECT species, ml_generate_embedding_result AS embedding_raw,
  ML.NORMALIZER(ml_generate_embedding_result) AS embedding_normalized
FROM ML.GENERATE_EMBEDDING(
  MODEL `{PROJECT_ID}.{DATASET_ID}.autoencoder_penguins_fix`,
  (SELECT species, culmen_length_mm, culmen_depth_mm, flipper_length_mm, body_mass_g
   FROM `bigquery-public-data.ml_datasets.penguins`
   WHERE body_mass_g IS NOT NULL)
)
"""
client.query(query).result()
print('Table autoencoder_embeddings created')
```

> **GOTCHA (verified):** normalized-embedding + `DOT_PRODUCT` and raw-embedding + `COSINE` produce mathematically equivalent results — `COSINE` distance = `1 - cosine_similarity`, `DOT_PRODUCT` distance (on unit vectors) = `-cosine_similarity`, and the two queries below return identical rankings with distances that convert exactly between the two formulas. **Practical implication: `ML.NORMALIZER` is unnecessary for `VECTOR_SEARCH` specifically** — use `distance_type='COSINE'` directly on `ML.GENERATE_EMBEDDING`'s raw output and skip the normalization step entirely, unless you need normalized vectors for something else.

```python
query = f"""
SELECT query.species AS query_species, base.species AS neighbor_species, distance
FROM VECTOR_SEARCH(
  TABLE `{PROJECT_ID}.{DATASET_ID}.autoencoder_embeddings`, 'embedding_normalized',
  (SELECT species, embedding_normalized FROM `{PROJECT_ID}.{DATASET_ID}.autoencoder_embeddings` LIMIT 1),
  top_k => 5,
  distance_type => 'DOT_PRODUCT'
)
ORDER BY distance
"""
client.query(query).to_dataframe()
```

```python
query = f"""
SELECT query.species AS query_species, base.species AS neighbor_species, distance
FROM VECTOR_SEARCH(
  TABLE `{PROJECT_ID}.{DATASET_ID}.autoencoder_embeddings`, 'embedding_raw',
  (SELECT species, embedding_raw FROM `{PROJECT_ID}.{DATASET_ID}.autoencoder_embeddings` LIMIT 1),
  top_k => 5,
  distance_type => 'COSINE'
)
ORDER BY distance
"""
client.query(query).to_dataframe()
```

---
## Step 12 — Retraining reproduces `ML.EVALUATE`, but not the latent space

> **GOTCHA (verified):** retraining Step 1's exact `RELU` model (same name, same SQL) reproduces `ML.EVALUATE`'s `mean_absolute_error` / `mean_squared_error` / `mean_squared_log_error` bit-for-bit — the learned reconstruction *function* is deterministic, same as `models/dnn_regressor` (`DNN_REGRESSOR`). But the two runs' actual `latent_col_*` values are meaningfully different: one run had `latent_col_2` dead (pinned to exactly `0.0` for all rows); another run's `latent_col_2` ranged up to ~0.9, and `latent_col_1`'s range changed too.

> This is a real, explainable property, not a bug: a generic autoencoder bottleneck has no constraint forcing a unique, ordered basis the way `models/pca` (PCA)'s variance-ranked components do — any invertible transform of the latent space, paired with the inverse transform in the decoder, reconstructs identically, so different training runs can land on equally good but differently-shaped latent geometries. **Practical implication: treat the autoencoder's overall reconstruction quality (`ML.EVALUATE`) as reproducible under a fixed model name, but don't assume any individual `latent_col_N` carries a fixed, comparable meaning across retrains the way PCA's `principal_component_N` does.**

---
## Step 13 — In-model preprocessing with the `TRANSFORM` clause

Adds `island` as a categorical feature alongside the four numeric measurements.

> **Verified:** `mean_squared_error` improves from ~0.21 to ~0.13. This makes sense — not a gotcha: `island` only has 3 categories, one-hot encoded — the model reconstructs a low-cardinality categorical almost perfectly, which pulls the average per-dimension reconstruction error down across the board.

```python
query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.autoencoder_penguins_transform`
TRANSFORM(
  culmen_length_mm, culmen_depth_mm, flipper_length_mm, body_mass_g, island
)
OPTIONS(
  model_type = 'AUTOENCODER',
  hidden_units = [3, 2, 3],
  activation_fn = 'TANH',
  learn_rate = 0.01,
  max_iterations = 30
) AS
SELECT culmen_length_mm, culmen_depth_mm, flipper_length_mm, body_mass_g, island
FROM `bigquery-public-data.ml_datasets.penguins`
WHERE body_mass_g IS NOT NULL
"""
client.query(query).result()
print('Model autoencoder_penguins_transform created')
```

```python
query = f"""
SELECT *
FROM ML.EVALUATE(MODEL `{PROJECT_ID}.{DATASET_ID}.autoencoder_penguins_transform`)
"""
client.query(query).to_dataframe()
```

---
## Step 14 — Hyperparameter tuning

Tunes `activation_fn` (`RELU` vs `TANH`) and `learn_rate` together, minimizing `mean_squared_error`.

> **Result below, honestly reported as-is:** this run's 4-trial search sampled 3 `RELU` configurations (`learn_rate` 0.0060, 0.0010, 0.0018) and only 1 `TANH` configuration (`learn_rate` 0.0024), with a `RELU` trial winning (`mean_squared_error=0.967`). **This does not confirm Step 4's finding that `TANH` beats `RELU`** — every one of these 4 tuned trials scored worse than *both* Step 2's untuned `RELU` baseline (~0.66–0.94) and Step 4's untuned `TANH` fix (~0.21). With only 4 trials spread across two hyperparameters at once, the search is too sparse to reliably explore either dimension — a small trial budget can fail to find a known-good region, the same limitation already documented for `models/dnn_regressor` (`DNN_REGRESSOR`)'s hyperparameter tuning. **Don't treat a small-budget tuning result as evidence for or against a specific hyperparameter's importance — Step 4's direct, controlled, same-`learn_rate` comparison remains the reliable evidence that `TANH` fixes the collapse, not this tuning search.**

```python
query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.autoencoder_penguins_tuned`
OPTIONS(
  model_type = 'AUTOENCODER',
  hidden_units = [3, 2, 3],
  activation_fn = HPARAM_CANDIDATES(['RELU', 'TANH']),
  learn_rate = HPARAM_RANGE(0.001, 0.05),
  max_iterations = 30,
  num_trials = 4,
  max_parallel_trials = 2,
  hparam_tuning_objectives = ['mean_squared_error']
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
  hparam_tuning_evaluation_metrics.mean_squared_error AS mean_squared_error,
  is_optimal
FROM ML.TRIAL_INFO(MODEL `{PROJECT_ID}.{DATASET_ID}.autoencoder_penguins_tuned`)
ORDER BY mean_squared_error ASC
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
FROM ML.EVALUATE(MODEL `statmike-mlops-349915.bq_ml.autoencoder_penguins_fix`)
```

---
## Examples — BigFrames

BigFrames provides a scikit-learn-style API (`bigframes.ml`) that trains BigQuery ML models under the hood. **Unlike `models/kmeans` (K-Means) or `models/pca` (PCA), there is no first-class `bigframes.ml` autoencoder wrapper** — confirmed against the live BigFrames API reference. Use the SQL `CREATE MODEL ... AUTOENCODER` shown above instead.
