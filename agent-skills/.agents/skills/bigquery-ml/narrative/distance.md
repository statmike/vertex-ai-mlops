# Distance / Vectors — BigQuery ML Model-Free Functions

Two model-free scalar functions with **no example anywhere in this repo** before this notebook: `ML.DISTANCE` (pairwise distance between two equal-length vectors) and `ML.LP_NORM` (the magnitude of a single vector). Neither needs a model — they operate on plain `ARRAY<FLOAT64>`/`ARRAY<INT64>` data, standalone in any `SELECT`.

**When to use these:**
- `ML.DISTANCE` — similarity scoring between embedding vectors, pairwise distance for lookalike/dedup/recommendation ranking, or ad-hoc custom KNN logic without `ML.PREDICT`.
- `ML.LP_NORM` — vector magnitude for normalization, or deriving a metric `ML.DISTANCE` doesn't support directly (e.g. Jaccard similarity).
- For scalable nearest-neighbor search over many rows, use `VECTOR_SEARCH` with an index instead — these two functions are brute-force, row-by-row.

**Data:** Literal arrays for core mechanics, plus real `models/pca` (PCA) embeddings on [`bigquery-public-data.ml_datasets.penguins`](https://console.cloud.google.com/marketplace/product/bigquery-public-datasets) (same dataset as every other `functions/` notebook in this project).

**References:** `RESOURCES.md` (Full reference) | [`ML.DISTANCE` docs](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-distance) | [`ML.LP_NORM` docs](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-lp-norm) | `setup` (Setup guide)

---
## Setup

Set your project and location, authenticate, and create a shared dataset. No connection needed.

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
## Step 1 — `ML.DISTANCE`: all three metrics, and cosine distance vs similarity

Scalar function, no model needed. `type` defaults to `'EUCLIDEAN'` when omitted.

> **Note:** `ML.DISTANCE` returns cosine **distance**, not similarity — compute `1 - ML.DISTANCE(v1, v2, 'COSINE')` for similarity. Same pattern already used in `bq-ai-functions/functions/ai_embed` (`bq-ai-functions/functions/ai_embed/`).

```python
query = """
SELECT
  ML.DISTANCE([1.0, 2.0, 3.0], [4.0, 5.0, 6.0], 'EUCLIDEAN') AS euclidean,
  ML.DISTANCE([1.0, 2.0, 3.0], [4.0, 5.0, 6.0], 'MANHATTAN') AS manhattan,
  ML.DISTANCE([1.0, 2.0, 3.0], [4.0, 5.0, 6.0], 'COSINE') AS cosine_distance,
  1 - ML.DISTANCE([1.0, 2.0, 3.0], [4.0, 5.0, 6.0], 'COSINE') AS cosine_similarity,
  ML.DISTANCE([1.0, 2.0, 3.0], [4.0, 5.0, 6.0]) AS default_metric
"""
client.query(query).to_dataframe()
```

---
## Step 2 — `ML.LP_NORM`, and a live cross-check against `ML.NORMALIZER`

The "Lp norm" is a single number summarizing a vector's overall magnitude — `degree` (the "p" in Lp) controls how it's computed:
- **L2** (`degree=2.0`) — the everyday "length" of a vector: `sqrt(x₁² + x₂² + ...)` (Euclidean distance from the origin).
- **L1** (`degree=1.0`) — the sum of absolute values: `|x₁| + |x₂| + ...` (Manhattan/"taxicab" distance from the origin).
- **L0** (`degree=0.0`) — a count, not a magnitude: the number of **non-zero** elements in the vector.

**Verified:** `ML.NORMALIZER(v, p)` from `functions/scalers` (`functions/scalers/`) equals `v / ML.LP_NORM(v, p)`, element-wise — `ML.LP_NORM` computes exactly the denominator `ML.NORMALIZER` uses internally.

```python
query = """
SELECT
  ML.LP_NORM([3.0, 4.0], 2.0) AS l2_norm,
  ML.LP_NORM([3.0, 4.0], 1.0) AS l1_norm,
  ML.LP_NORM([3.0, 4.0], 0.0) AS l0_norm,
  ML.NORMALIZER([3.0, 4.0], 2) AS normalizer_p2,
  [3.0 / ML.LP_NORM([3.0, 4.0], 2.0), 4.0 / ML.LP_NORM([3.0, 4.0], 2.0)] AS manual_normalized
"""
client.query(query).to_dataframe()
```

---
## Step 3 — Deriving Jaccard similarity: a metric `ML.DISTANCE` doesn't support directly

`ML.DISTANCE` only supports `EUCLIDEAN`/`MANHATTAN`/`COSINE`. Jaccard similarity (intersection / union) for binary vectors is derivable via a dot product (intersection count) and `ML.LP_NORM`'s L1 norm (set sizes).

```python
query = """
WITH data AS (
  SELECT [1.0, 1.0, 0.0, 1.0, 0.0] AS a, [1.0, 0.0, 0.0, 1.0, 1.0] AS b
),
computed AS (
  SELECT a, b,
    (SELECT SUM(x * y) FROM UNNEST(a) AS x WITH OFFSET i JOIN UNNEST(b) AS y WITH OFFSET j ON i = j) AS intersection,
    ML.LP_NORM(a, 1.0) AS norm_a,
    ML.LP_NORM(b, 1.0) AS norm_b
  FROM data
)
SELECT *, intersection / (norm_a + norm_b - intersection) AS jaccard_similarity
FROM computed
"""
client.query(query).to_dataframe()
```

Jaccard = `2 / (3 + 3 - 2) = 0.5` — matches manual set-based Jaccard exactly (both vectors have 3 ones each, sharing 2 positions).

---
## Step 4 — Real embedding similarity: distance between two penguins' PCA projections

`ML.DISTANCE` is the natural fit for a one-off pairwise comparison between real embeddings — the same technique `models/pca` (`models/pca/`) pairs with `VECTOR_SEARCH` for scalable lookup, but without building a vector index. Train a small scratch `PCA` model (same mechanism as `models/pca/`), then compute the distance between two penguins from **different** species.

```python
query = """
CREATE OR REPLACE MODEL `{project}.{dataset}.scratch_distance_pca_demo`
OPTIONS(model_type = 'PCA', num_principal_components = 2) AS
SELECT culmen_length_mm, culmen_depth_mm, flipper_length_mm, body_mass_g
FROM `bigquery-public-data.ml_datasets.penguins`
WHERE culmen_length_mm IS NOT NULL AND culmen_depth_mm IS NOT NULL
  AND flipper_length_mm IS NOT NULL AND body_mass_g IS NOT NULL
""".format(project=PROJECT_ID, dataset=DATASET_ID)
client.query(query).result()
print('Scratch PCA model created')
```

```python
query = """
WITH sample_penguins AS (
  (SELECT species, culmen_length_mm, culmen_depth_mm, flipper_length_mm, body_mass_g
   FROM `bigquery-public-data.ml_datasets.penguins`
   WHERE culmen_length_mm IS NOT NULL AND culmen_depth_mm IS NOT NULL AND flipper_length_mm IS NOT NULL AND body_mass_g IS NOT NULL
   ORDER BY species LIMIT 1)
  UNION ALL
  (SELECT species, culmen_length_mm, culmen_depth_mm, flipper_length_mm, body_mass_g
   FROM `bigquery-public-data.ml_datasets.penguins`
   WHERE culmen_length_mm IS NOT NULL AND culmen_depth_mm IS NOT NULL AND flipper_length_mm IS NOT NULL AND body_mass_g IS NOT NULL
   ORDER BY species DESC LIMIT 1)
),
embeddings AS (
  SELECT species, [principal_component_1, principal_component_2] AS embedding
  FROM ML.PREDICT(MODEL `{project}.{dataset}.scratch_distance_pca_demo`, (SELECT * FROM sample_penguins))
)
SELECT
  a.species AS species_a, b.species AS species_b,
  ML.DISTANCE(a.embedding, b.embedding, 'EUCLIDEAN') AS euclidean_distance,
  1 - ML.DISTANCE(a.embedding, b.embedding, 'COSINE') AS cosine_similarity
FROM embeddings a, embeddings b
WHERE a.species < b.species
""".format(project=PROJECT_ID, dataset=DATASET_ID)
client.query(query).to_dataframe()
```

Notice `cosine_similarity` comes out **negative** (`-0.45`) — a beginner expecting a `0`-`1` "similarity score" might read this as a bug. It isn't: cosine similarity ranges `[-1, 1]`, and a negative value means the two vectors point in substantially different directions in PC-space (not just "far apart," but on opposite sides of the origin along some dimension). This is exactly the payoff of the example — the Adelie and Gentoo penguins, two visibly different species, land far enough apart in the PCA projection that even their *direction* from the origin disagrees, not just their distance.

---
## Examples — `%%bigquery` Magics

The same operations using IPython magic commands — write SQL directly in cells without Python string wrapping.

```sql
%%bigquery --project {PROJECT_ID}

SELECT
  ML.DISTANCE([1.0, 2.0, 3.0], [4.0, 5.0, 6.0], 'COSINE') AS cosine_distance,
  ML.LP_NORM([3.0, 4.0], 2.0) AS l2_norm
```

---
## Examples — BigFrames

There is **no** direct BigFrames equivalent for either function — use array math on a local/pandas array, or `VECTOR_SEARCH` for scalable nearest-neighbor lookup at the BigFrames level.

```python
import bigframes.pandas as bpd

bpd.close_session()  # Reset session to apply project/location settings
bpd.options.bigquery.project = PROJECT_ID
bpd.options.bigquery.location = LOCATION

bf_query = """
SELECT
  ML.DISTANCE([1.0, 2.0, 3.0], [4.0, 5.0, 6.0], 'COSINE') AS cosine_distance,
  ML.LP_NORM([3.0, 4.0], 2.0) AS l2_norm
"""
bpd.read_gbq(bf_query).peek()
```
