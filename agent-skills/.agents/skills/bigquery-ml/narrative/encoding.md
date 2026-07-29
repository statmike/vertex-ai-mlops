# Encoding — BigQuery ML Model-Free Functions

Three categorical-encoding functions, all **analytic** (require `OVER()`): `ML.ONE_HOT_ENCODER` (scalar `STRING` → sparse one-hot/dummy vector), `ML.LABEL_ENCODER` (scalar `STRING` → ordinal `INT64`), and `ML.MULTI_HOT_ENCODER` (`ARRAY<STRING>` → sparse multi-hot vector). All three share the same `top_k`/`frequency_threshold` vocabulary-capping mechanism.

**When to use these:**
- `ML.ONE_HOT_ENCODER` — nominal categoricals for linear/logistic models that don't auto-encode the way you want.
- `ML.LABEL_ENCODER` — a compact ordinal integer, appropriate for tree models or where order genuinely doesn't matter to the algorithm.
- `ML.MULTI_HOT_ENCODER` — genuine array/multi-value columns (tags, multi-select fields) — not a substitute for splitting a string yourself.

**Data:** [`bigquery-public-data.ml_datasets.penguins`](https://console.cloud.google.com/marketplace/product/bigquery-public-datasets) — same dataset as `functions/scalers` (`functions/scalers/`) and `functions/feature_engineering` (`functions/feature_engineering/`).

**Featured in:** `models/boosted_tree_regressor` (`models/boosted_tree_regressor/`) (`ML.LABEL_ENCODER` inline in a `TRANSFORM` clause).

**References:** `RESOURCES.md` (Full reference) | [`ML.ONE_HOT_ENCODER` docs](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-one-hot-encoder) | [`ML.LABEL_ENCODER` docs](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-label-encoder) | [`ML.MULTI_HOT_ENCODER` docs](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-multi-hot-encoder) | `setup` (Setup guide)

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
## Step 1 — `ML.ONE_HOT_ENCODER`: default vs. dummy encoding (`drop`), and `top_k` capping

`drop='none'` (default) keeps every category; `drop='most_frequent'` drops the single most frequent category (dummy encoding — avoids the linear-model collinearity trap `RESOURCES.md` (documented for `DUMMY_ENCODING`) elsewhere in this project).

```python
query = """
SELECT DISTINCT x,
  ML.ONE_HOT_ENCODER(x) OVER() AS onehot_default,
  ML.ONE_HOT_ENCODER(x, 'most_frequent') OVER() AS onehot_dummy
FROM UNNEST(['a','a','a','a','a','a', 'b','b','b','b','b','b','b', 'c','c','c','c','c','c']) AS x
ORDER BY x
"""
client.query(query).to_dataframe()
```

Note `onehot_dummy`: `'b'` is the most frequent category (7 occurrences), so `drop='most_frequent'` keeps its slot in the sparse struct but zeroes it out (`value: 0.0`) — this is the "baseline" category every other category's coefficient gets compared against, avoiding the one-hot/intercept collinearity trap.

Now `top_k` — cap the vocabulary to only the N most frequent categories, regardless of `frequency_threshold`. With `'a'`(10x), `'b'`(8x), `'c'`(6x), `'d'`(6x) — all well above the default `frequency_threshold=5`, so that's not what's at play here — `top_k=2` keeps only the 2 most frequent:

```python
query = """
WITH data AS (
  SELECT x FROM UNNEST([
    'a','a','a','a','a','a','a','a','a','a',
    'b','b','b','b','b','b','b','b',
    'c','c','c','c','c','c',
    'd','d','d','d','d','d'
  ]) AS x
)
SELECT DISTINCT x,
  ML.ONE_HOT_ENCODER(x) OVER() AS no_topk_cap,
  ML.ONE_HOT_ENCODER(x, 'none', 2) OVER() AS topk2
FROM data
ORDER BY x
"""
client.query(query).to_dataframe()
```

**Verified:** `'c'` and `'d'` both collapse to bucket `0` under `top_k=2`, even though neither is anywhere close to the `frequency_threshold=5` cutoff (6 occurrences each) — `top_k` and `frequency_threshold` are two independent caps, and either one alone can push a category into the shared unknown bucket.

---
## Step 2 — MAJOR GOTCHA (verified live): the default `frequency_threshold=5` silently drops rare categories, in ALL THREE encoders

RESOURCES.md already flags a documentation discrepancy: older repo notebooks cite `top_k=1,000,000`/`frequency_threshold=0` (no threshold at all); current docs specify `top_k=32,000`/`frequency_threshold=5`. This isn't just a docs footnote — it changes real output.

With `'a'` appearing 6 times, `'b'` appearing 7 times, and `'c'` appearing only **3** times (below the default threshold of 5):

```python
query = """
SELECT DISTINCT x,
  ML.ONE_HOT_ENCODER(x) OVER() AS onehot_current_default_freq5,
  ML.ONE_HOT_ENCODER(x, 'none', 32000, 0) OVER() AS onehot_legacy_style_freq0,
  ML.LABEL_ENCODER(x) OVER() AS label_current_default_freq5,
  ML.LABEL_ENCODER(x, 32000, 0) OVER() AS label_legacy_style_freq0
FROM UNNEST(['a','a','a','a','a','a', 'b','b','b','b','b','b','b', 'c','c','c']) AS x
ORDER BY x
"""
client.query(query).to_dataframe()
```

**Verified:** under the current default, `'c'` (only 3 occurrences) collapses into bucket `0` for **both** `ML.ONE_HOT_ENCODER` and `ML.LABEL_ENCODER` — indistinguishable from `NULL`/unseen-at-predict. With `frequency_threshold=0` (the legacy behavior), `'c'` keeps its own index in both. On any real dataset with a rare-but-meaningful category (fewer than 5 total occurrences), **the current default silently discards it** unless you explicitly pass `frequency_threshold=0` or lower. This is easy to miss since it produces no error or warning — the category just quietly stops being distinguishable.

`ML.MULTI_HOT_ENCODER` shares the identical mechanism — same trap, on `ARRAY<STRING>` documents instead of scalar values. 6 tiny "documents," each containing `'common'` (appears in all 6, ≥5) plus one other word that appears in only 1 document:

```python
query = """
WITH docs AS (
  SELECT * FROM UNNEST([
    STRUCT(1 AS id, ['common', 'apple'] AS arr),
    STRUCT(2 AS id, ['common', 'banana'] AS arr),
    STRUCT(3 AS id, ['common', 'cherry'] AS arr),
    STRUCT(4 AS id, ['common', 'date'] AS arr),
    STRUCT(5 AS id, ['common', 'elderberry'] AS arr),
    STRUCT(6 AS id, ['common', 'fig'] AS arr)
  ])
)
SELECT id, arr,
  ML.MULTI_HOT_ENCODER(arr) OVER() AS multihot_default_freq5,
  ML.MULTI_HOT_ENCODER(arr, 32000, 0) OVER() AS multihot_legacy_style_freq0
FROM docs
ORDER BY id
"""
client.query(query).to_dataframe()
```

**Verified: bucket `0` is genuinely overloaded** — `NULL` and a below-threshold category land on the exact same index, so a downstream model can't tell them apart. Add a `NULL` document to the mix above:

```python
query = """
SELECT DISTINCT x, ML.ONE_HOT_ENCODER(x) OVER() AS onehot
FROM UNNEST([CAST(NULL AS STRING), 'a','a','a','a','a','a', 'b','b','b','b','b','b','b', 'c','c','c']) AS x
ORDER BY x IS NULL DESC, x
"""
client.query(query).to_dataframe()
```

---
## Step 3 — `ML.LABEL_ENCODER` and `ML.MULTI_HOT_ENCODER` on real data

`island` has plenty of rows per category (`Biscoe`/`Dream`/`Torgersen`), so none get dropped by the default threshold — unlike Step 2's tiny synthetic categories.

```python
query = """
SELECT DISTINCT island,
  ML.ONE_HOT_ENCODER(island) OVER() AS island_onehot,
  ML.LABEL_ENCODER(island) OVER() AS island_label
FROM `bigquery-public-data.ml_datasets.penguins`
ORDER BY island
"""
client.query(query).to_dataframe()
```

`ML.MULTI_HOT_ENCODER` on an `ARRAY<STRING>` column — one output feature per **unique element across all rows**, not per row:

```python
query = """
SELECT arr, ML.MULTI_HOT_ENCODER(arr, 100, 0) OVER() AS multi_hot
FROM UNNEST([
  STRUCT(['tag_a', 'tag_b'] AS arr),
  STRUCT(['tag_b', 'tag_c'] AS arr),
  STRUCT(['tag_a'] AS arr)
])
"""
client.query(query).to_dataframe()
```

---
## Step 4 — Embedded in a real `CREATE MODEL TRANSFORM`

Both encoders' vocabularies (and the `top_k`/`frequency_threshold`/`drop` choices) travel with the model and auto-apply at `ML.PREDICT` — no separate encoding step needed at inference time.

```python
query = """
CREATE OR REPLACE MODEL `{project}.{dataset}.encoding_downstream_logistic_regression`
TRANSFORM(
  species,
  ML.ONE_HOT_ENCODER(island) OVER() AS island_encoded,
  ML.LABEL_ENCODER(sex) OVER() AS sex_encoded
)
OPTIONS(model_type = 'LOGISTIC_REG', input_label_cols = ['species']) AS
SELECT species, island, sex
FROM `bigquery-public-data.ml_datasets.penguins`
""".format(project=PROJECT_ID, dataset=DATASET_ID)
client.query(query).result()
print('Model encoding_downstream_logistic_regression created')

query = f"SELECT * FROM ML.EVALUATE(MODEL `{PROJECT_ID}.{DATASET_ID}.encoding_downstream_logistic_regression`)"
client.query(query).to_dataframe()
```

`island`+`sex` alone are only modestly predictive of `species` (~0.71 accuracy) — that's expected and not the point here; the point is both encoders' fitted vocabularies are reused automatically, with no separate `ML.TRANSFORM` call needed.

---
## Examples — `%%bigquery` Magics

The same operations using IPython magic commands — write SQL directly in cells without Python string wrapping.

```sql
%%bigquery --project {PROJECT_ID}

SELECT DISTINCT island,
  ML.ONE_HOT_ENCODER(island) OVER() AS island_onehot,
  ML.LABEL_ENCODER(island) OVER() AS island_label
FROM `bigquery-public-data.ml_datasets.penguins`
ORDER BY island
```

---
## Examples — BigFrames

`bigframes.ml.preprocessing.OneHotEncoder` and `LabelEncoder` map to `ML.ONE_HOT_ENCODER`/`ML.LABEL_ENCODER`. There is **no** direct `MultiHotEncoder` class.

```python
import bigframes.pandas as bpd
from bigframes.ml.preprocessing import OneHotEncoder

bpd.close_session()  # Reset session to apply project/location settings
bpd.options.bigquery.project = PROJECT_ID
bpd.options.bigquery.location = LOCATION

df = bpd.read_gbq("SELECT island FROM `bigquery-public-data.ml_datasets.penguins`")
encoder = OneHotEncoder()
encoder.fit(df[['island']])
encoder.transform(df[['island']]).peek()
```
