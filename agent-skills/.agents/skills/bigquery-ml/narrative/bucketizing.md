# Bucketizing — BigQuery ML Model-Free Functions

Three functions that convert a continuous or string value into a discrete bucket: `ML.BUCKETIZE` (manual split points, scalar), `ML.QUANTILE_BUCKETIZE` (equal-frequency bins, **analytic** — requires `OVER()`), and `ML.HASH_BUCKETIZE` (deterministic string hashing into N buckets, scalar). All three are exportable when used inside a `CREATE MODEL ... TRANSFORM(...)` clause.

**When to use these:**
- `ML.BUCKETIZE` — encode domain knowledge as explicit boundaries (e.g. age brackets, price tiers) for linear/logistic models.
- `ML.QUANTILE_BUCKETIZE` — equal-frequency binning of a skewed numeric feature without hand-picking boundaries.
- `ML.HASH_BUCKETIZE` — the "hashing trick" for high-cardinality strings: stable, deterministic, no vocabulary fitting required (contrast with `functions/encoding` (`functions/encoding/`), which fits a real vocabulary).

**Data:** [`bigquery-public-data.ml_datasets.penguins`](https://console.cloud.google.com/marketplace/product/bigquery-public-datasets) — same dataset as `functions/scalers` (`functions/scalers/`), `functions/feature_engineering` (`functions/feature_engineering/`), and `functions/encoding` (`functions/encoding/`).

**References:** `RESOURCES.md` (Full reference) | [`ML.BUCKETIZE` docs](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-bucketize) | [`ML.QUANTILE_BUCKETIZE` docs](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-quantile-bucketize) | [`ML.HASH_BUCKETIZE` docs](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-hash-bucketize) | `setup` (Setup guide)

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
## Step 1 — `ML.BUCKETIZE`: manual split points, 3 output formats

Scalar function (no `OVER()`). `output_format` controls the label: `'bucket_names'` (default, `bin_<i>`), `'bucket_ranges'` (interval notation), or `'bucket_ranges_json'`.

```python
query = """
SELECT
  body_mass_g,
  ML.BUCKETIZE(body_mass_g, [3000, 4000, 5000]) AS bucket_names,
  ML.BUCKETIZE(body_mass_g, [3000, 4000, 5000], FALSE, 'bucket_ranges') AS bucket_ranges,
  ML.BUCKETIZE(body_mass_g, [3000, 4000, 5000], FALSE, 'bucket_ranges_json') AS bucket_ranges_json
FROM `bigquery-public-data.ml_datasets.penguins`
WHERE body_mass_g IS NOT NULL
ORDER BY body_mass_g
LIMIT 5
"""
client.query(query).to_dataframe()
```

---
## Step 2 — GOTCHA (verified live): what `exclude_boundaries=TRUE` actually does

RESOURCES.md's docs-derived description says `exclude_boundaries` "drops the implicit lower (`-inf`) and upper (`+inf`) overflow buckets so only interior bins remain." That phrasing is easy to misread as "out-of-range values become `NULL`."

**Verified: they do NOT become `NULL`.** Instead, the **outermost split points are dropped entirely**, merging the overflow bucket into its nearest interior neighbor. With split points `[10, 20, 30]`:
- Default (4 bins): `(-inf,10)` `[10,20)` `[20,30)` `[30,+inf)`
- Excluded (2 bins): `(-inf,20)` `[20,+inf)`

The first and last split points (`10` and `30`) disappear entirely, leaving only the middle one (`20`) as the sole effective boundary — not "values outside `[10,30]` become `NULL`."

```python
query = """
SELECT
  x,
  ML.BUCKETIZE(x, [10, 20, 30], FALSE, 'bucket_ranges') AS default_ranges,
  ML.BUCKETIZE(x, [10, 20, 30], TRUE, 'bucket_ranges') AS excluded_ranges
FROM UNNEST([0.0, 10.0, 15.0, 20.0, 25.0, 30.0, 40.0]) AS x
"""
client.query(query).to_dataframe()
```

---
## Step 3 — `ML.QUANTILE_BUCKETIZE`: equal-frequency bins (analytic — requires `OVER()`)

Unlike `ML.BUCKETIZE`'s fixed, hand-picked split points, this computes boundaries from the data itself so each bucket holds roughly the same number of rows.

```python
query = """
SELECT
  culmen_length_mm,
  ML.QUANTILE_BUCKETIZE(culmen_length_mm, 4) OVER() AS quantile_bucket,
  ML.QUANTILE_BUCKETIZE(culmen_length_mm, 4, 'bucket_ranges') OVER() AS quantile_ranges,
  ML.QUANTILE_BUCKETIZE(culmen_length_mm, 4, 'bucket_ranges_json') OVER() AS quantile_ranges_json
FROM `bigquery-public-data.ml_datasets.penguins`
WHERE culmen_length_mm IS NOT NULL
ORDER BY culmen_length_mm
LIMIT 5
"""
client.query(query).to_dataframe()
```

---
## Step 4 — `ML.HASH_BUCKETIZE`: deterministic string hashing (scalar)

The "hashing trick" — no vocabulary fitting, no training-time statistics, just a deterministic `hash(string) mod hash_bucket_size`. `hash_bucket_size=0` returns the raw hash with no modulo applied. Unlike `ML.QUANTILE_BUCKETIZE` above (which computes and stores real quantile boundaries from the training data), `ML.HASH_BUCKETIZE` has no state to fit or store at all — the same string always hashes to the same bucket, with no dependency on what else is in the dataset.

```python
query = """
SELECT DISTINCT island,
  ML.HASH_BUCKETIZE(island, 0) AS raw_hash,
  ML.HASH_BUCKETIZE(island, 3) AS bucket_mod3
FROM `bigquery-public-data.ml_datasets.penguins`
ORDER BY island
"""
client.query(query).to_dataframe()
```

**Collisions are unavoidable when distinct values exceed `hash_bucket_size`** — with only 3 islands and `hash_bucket_size=2`, two different islands land in the same bucket:

```python
query = """
SELECT DISTINCT island, ML.HASH_BUCKETIZE(island, 2) AS bucket_mod2
FROM `bigquery-public-data.ml_datasets.penguins`
ORDER BY island
"""
client.query(query).to_dataframe()
```

---
## Step 5 — Embedded in a real `CREATE MODEL TRANSFORM`

BQML auto-encodes the `STRING` bucket labels and `INT64` hash buckets just like any other categorical/numeric feature — no extra handling needed downstream.

```python
query = """
CREATE OR REPLACE MODEL `{project}.{dataset}.bucketizing_downstream_logistic_regression`
TRANSFORM(
  species,
  ML.QUANTILE_BUCKETIZE(body_mass_g, 4) OVER() AS body_mass_bucket,
  ML.HASH_BUCKETIZE(island, 10) AS island_hashed
)
OPTIONS(model_type = 'LOGISTIC_REG', input_label_cols = ['species']) AS
SELECT species, body_mass_g, island
FROM `bigquery-public-data.ml_datasets.penguins`
WHERE body_mass_g IS NOT NULL
""".format(project=PROJECT_ID, dataset=DATASET_ID)
client.query(query).result()
print('Model bucketizing_downstream_logistic_regression created')

query = f"SELECT * FROM ML.EVALUATE(MODEL `{PROJECT_ID}.{DATASET_ID}.bucketizing_downstream_logistic_regression`)"
client.query(query).to_dataframe()
```

---
## Examples — `%%bigquery` Magics

The same operations using IPython magic commands — write SQL directly in cells without Python string wrapping.

```sql
%%bigquery --project {PROJECT_ID}

SELECT
  culmen_length_mm,
  ML.QUANTILE_BUCKETIZE(culmen_length_mm, 4) OVER() AS quantile_bucket
FROM `bigquery-public-data.ml_datasets.penguins`
WHERE culmen_length_mm IS NOT NULL
ORDER BY culmen_length_mm
LIMIT 5
```

---
## Examples — BigFrames

`bigframes.ml.preprocessing.KBinsDiscretizer` covers both `ML.BUCKETIZE` (`strategy='uniform'`-like manual behavior isn't a 1:1 match) and `ML.QUANTILE_BUCKETIZE` (`strategy='quantile'`). There is **no** direct equivalent for `ML.HASH_BUCKETIZE`.

```python
import bigframes.pandas as bpd
from bigframes.ml.preprocessing import KBinsDiscretizer

bpd.close_session()  # Reset session to apply project/location settings
bpd.options.bigquery.project = PROJECT_ID
bpd.options.bigquery.location = LOCATION

df = bpd.read_gbq(
    "SELECT culmen_length_mm FROM `bigquery-public-data.ml_datasets.penguins` WHERE culmen_length_mm IS NOT NULL"
)
discretizer = KBinsDiscretizer(n_bins=4, strategy='quantile')
discretizer.fit(df[['culmen_length_mm']])
discretizer.transform(df[['culmen_length_mm']]).peek()
```
