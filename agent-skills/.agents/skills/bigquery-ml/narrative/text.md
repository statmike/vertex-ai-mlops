# Text — BigQuery ML Model-Free Functions

Three functions that turn tokenized text (`ARRAY<STRING>`) into ML features: `ML.NGRAMS` (scalar — builds n-grams from tokens), `ML.TF_IDF`, and `ML.BAG_OF_WORDS` (both **analytic** — require `OVER()`, build a dictionary across the whole document window). `ML.TF_IDF` and `ML.BAG_OF_WORDS` had **no example anywhere in this repo** before this notebook.

> **GOTCHA:** GoogleSQL also has same-named non-`ML.*` [text-analysis functions](https://cloud.google.com/bigquery/docs/reference/standard-sql/text-analysis-functions) (`TF_IDF`, `BAG_OF_WORDS`) with **different** semantics (term-string dictionary index, frequency-ordered). The `ML.*` versions documented here use integer dictionary indices, order the dictionary alphabetically, and reserve index `0` for the unknown term. Always call them as `ML.TF_IDF` / `ML.BAG_OF_WORDS`.

**When to use these:**
- `ML.NGRAMS` — capture local token order (bigrams, trigrams) that single tokens lose, before bag-of-words or TF-IDF.
- `ML.BAG_OF_WORDS` — raw per-document term counts, a quick baseline text feature.
- `ML.TF_IDF` — weight terms by importance (frequent-in-doc but rare-across-corpus), better than raw counts for sparse text features feeding a linear model.

**Data:** [`bigquery-public-data.thelook_ecommerce.products`](https://console.cloud.google.com/marketplace/product/bigquery-public-datasets)`.name` — short, real product-name strings, already used in `workflows/embeddings_classification` (`workflows/embeddings_classification/`).

**References:** `RESOURCES.md` (Full reference) | [`ML.NGRAMS` docs](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ngrams) | [`ML.TF_IDF` docs](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-tf-idf) | [`ML.BAG_OF_WORDS` docs](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-bag-of-words) | `setup` (Setup guide)

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
## Step 1 — Tokenize first: all three functions operate on `ARRAY<STRING>`

None of these functions take raw text directly — split it into tokens first (here, a simple lowercase + space split; a real pipeline might use GoogleSQL's `TEXT_ANALYZE`). This step exists because `ML.NGRAMS`/`ML.TF_IDF`/`ML.BAG_OF_WORDS` all work by counting or concatenating **discrete units** — there's no way to count "how many times does a word appear" or "merge adjacent words" on a single undivided string; the string has to be broken into a list of individual tokens first.

```python
query = """
SELECT name, SPLIT(LOWER(name), ' ') AS tokens
FROM `bigquery-public-data.thelook_ecommerce.products`
LIMIT 3
"""
client.query(query).to_dataframe()
```

---
## Step 2 — `ML.NGRAMS`: scalar, builds n-grams within a size range

`range=[2,3]` returns every bigram and trigram, each `separator`-joined (default: a single space).

> **GOTCHA (verified live, corrects RESOURCES.md):** the docs describe `range` as accepting "a single integer `x`" to mean `[x, x]` — **this is not actually true.** Passing a bare `INT64` (e.g. `ML.NGRAMS(tokens, 2)`) fails outright: `"No matching signature for function ML.NGRAMS... Unable to coerce type INT64 to expected type ARRAY<INT64>"`. `range` must always be an `ARRAY<INT64>`, even for a single size — use `[2, 2]`, not `2`.

```python
query = """
SELECT
  ML.NGRAMS(tokens, [2, 3]) AS default_separator,
  ML.NGRAMS(tokens, [2, 3], '_') AS underscore_separator,
  ML.NGRAMS(tokens, [2, 2]) AS bigrams_only
FROM (SELECT SPLIT(LOWER('Low Profile Dyed Cotton Cap'), ' ') AS tokens)
"""
client.query(query).to_dataframe()
```

---
## Step 3 — `ML.BAG_OF_WORDS` and `ML.TF_IDF` on real product-name tokens

Both are analytic — the dictionary is fit across every document in the `OVER()` window, not per-row. `BAG_OF_WORDS` returns raw counts; `TF_IDF` weights them by cross-document rarity.

```python
query = """
WITH docs AS (
  SELECT id, SPLIT(LOWER(REGEXP_REPLACE(name, r'[^a-zA-Z0-9 ]', ' ')), ' ') AS tokens
  FROM `bigquery-public-data.thelook_ecommerce.products`
  WHERE category = 'Accessories'
  LIMIT 500
)
SELECT id, tokens,
  ML.BAG_OF_WORDS(tokens) OVER() AS bow_default,
  ML.TF_IDF(tokens) OVER() AS tfidf_default
FROM docs
LIMIT 5
"""
client.query(query).to_dataframe()
```

**The concrete difference between the two, isolated:** 4 tiny documents, each containing `'common_word'` (in all 4) plus one other word (`'apple'`/`'banana'`/`'rare_word'`/`'rare_word'` — appearing in 1-2 docs). Lower the threshold so nothing gets dropped to bucket 0 (`top_k=100, frequency_threshold=1`), isolating the weighting behavior itself:

```python
query = """
WITH docs AS (
  SELECT * FROM UNNEST([
    STRUCT(1 AS doc_id, ['common_word', 'apple'] AS tokens),
    STRUCT(2 AS doc_id, ['common_word', 'banana'] AS tokens),
    STRUCT(3 AS doc_id, ['common_word', 'rare_word'] AS tokens),
    STRUCT(4 AS doc_id, ['common_word', 'rare_word'] AS tokens)
  ])
)
SELECT doc_id, tokens,
  ML.BAG_OF_WORDS(tokens, 100, 1) OVER() AS bow_counts,
  ML.TF_IDF(tokens, 100, 1) OVER() AS tfidf_weights
FROM docs
ORDER BY doc_id
"""
client.query(query).to_dataframe()
```

**Verified:** `bow_counts` gives `'common_word'` (appears in all 4 docs) the exact same weight (`1.0`) as `'apple'`/`'banana'`/`'rare_word'` (rarer) — raw counts don't distinguish importance. `tfidf_weights` gives `'common_word'` a **lower** weight (`0.294`) than `'apple'`/`'banana'` (`0.549`, appearing in only 1 doc each) or `'rare_word'` (`0.424`, appearing in 2 docs) — TF-IDF genuinely down-weights terms that show up everywhere and up-weights rarer, more distinguishing ones.

---
## Step 4 — MAJOR GOTCHA (verified live, first time tested anywhere in this repo)

`ML.TF_IDF`/`ML.BAG_OF_WORDS` share the exact same `top_k=32000`/`frequency_threshold=5` defaults as the encoders in `functions/encoding` (`functions/encoding/`) — and the **same practical consequence, verified for both functions, not just asserted by analogy**. Six tiny "documents," each containing `'common_word'` (appears in all 6, ≥5) plus one other word that appears in only 1-2 documents (below the default threshold of 5):

```python
query = """
WITH docs AS (
  SELECT * FROM UNNEST([
    STRUCT(1 AS doc_id, ['common_word', 'apple'] AS tokens),
    STRUCT(2 AS doc_id, ['common_word', 'banana'] AS tokens),
    STRUCT(3 AS doc_id, ['common_word', 'rare_word'] AS tokens),
    STRUCT(4 AS doc_id, ['common_word', 'cherry'] AS tokens),
    STRUCT(5 AS doc_id, ['common_word', 'date'] AS tokens),
    STRUCT(6 AS doc_id, ['common_word', 'rare_word'] AS tokens)
  ])
)
SELECT doc_id, tokens,
  ML.BAG_OF_WORDS(tokens) OVER() AS bow_default_freq5,
  ML.BAG_OF_WORDS(tokens, 100, 1) OVER() AS bow_freqthresh1,
  ML.TF_IDF(tokens) OVER() AS tfidf_default_freq5,
  ML.TF_IDF(tokens, 100, 1) OVER() AS tfidf_freqthresh1
FROM docs
ORDER BY doc_id
"""
client.query(query).to_dataframe()
```

**Verified for both functions:** under the default `frequency_threshold=5`, **every** word except `'common_word'` collapses to index `0` in both `ML.BAG_OF_WORDS` AND `ML.TF_IDF` — even `'rare_word'`, which appears in **2 different documents**, is indistinguishable from `'apple'` (1 occurrence) or a truly unseen term. With `frequency_threshold=1`, all 6 distinct words get their own index in both. Same practical consequence as the encoder gotcha in `functions/encoding/`: on a small corpus, almost everything except the most common terms silently disappears under current defaults.

---
## Step 5 — Embedded in a real `CREATE MODEL TRANSFORM`: text classification

`ML.BAG_OF_WORDS` features derived directly from the product name, feeding a `LOGISTIC_REG` that distinguishes two categories.

```python
query = """
CREATE OR REPLACE MODEL `{project}.{dataset}.text_downstream_logistic_regression`
TRANSFORM(
  category,
  ML.BAG_OF_WORDS(SPLIT(LOWER(REGEXP_REPLACE(name, r'[^a-zA-Z0-9 ]', ' ')), ' '), 200, 3) OVER() AS name_bow
)
OPTIONS(model_type = 'LOGISTIC_REG', input_label_cols = ['category']) AS
SELECT category, name
FROM `bigquery-public-data.thelook_ecommerce.products`
WHERE category IN ('Accessories', 'Jeans')
""".format(project=PROJECT_ID, dataset=DATASET_ID)
client.query(query).result()
print('Model text_downstream_logistic_regression created')

query = f"SELECT * FROM ML.EVALUATE(MODEL `{PROJECT_ID}.{DATASET_ID}.text_downstream_logistic_regression`)"
client.query(query).to_dataframe()
```

~0.95 accuracy — bag-of-words features from the product name alone strongly separate `Accessories` from `Jeans`, with no manual feature engineering beyond tokenizing.

---
## Examples — `%%bigquery` Magics

The same operations using IPython magic commands — write SQL directly in cells without Python string wrapping.

```sql
%%bigquery --project {PROJECT_ID}

SELECT tokens, ML.NGRAMS(tokens, [2, 3]) AS bigrams_trigrams
FROM (SELECT SPLIT(LOWER('Low Profile Dyed Cotton Cap'), ' ') AS tokens)
```

---
## Examples — BigFrames

There is **no** direct BigFrames equivalent for any of these three — use the SQL `TRANSFORM` path, or BigFrames' own SQL passthrough (`bpd.read_gbq`) as shown below.

```python
import bigframes.pandas as bpd

bpd.close_session()  # Reset session to apply project/location settings
bpd.options.bigquery.project = PROJECT_ID
bpd.options.bigquery.location = LOCATION

bf_query = """
SELECT tokens, ML.NGRAMS(tokens, [2, 3]) AS bigrams_trigrams
FROM (SELECT SPLIT(LOWER('Low Profile Dyed Cotton Cap'), ' ') AS tokens)
"""
bpd.read_gbq(bf_query).peek()
```
