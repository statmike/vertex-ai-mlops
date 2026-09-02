# Catalog Search — BigQuery AI Functions

Semantic search understands *meaning*. Full-text search matches *tokens*. A product catalog needs both — the same shopper types `a warm layer for a chilly hike` and a 32-character SKU in the same session, and each query breaks the other kind of search:

1. **Build** a 7,275-product catalog with autonomous embedding generation
2. **Prove** where each signal fails alone — an exact SKU lookup and a paraphrased need
3. **Compare** `AI.SEARCH` in `VECTOR`, `HYBRID`, and `AUTO` mode
4. **Materialize** the vectors into a second table and build a hybrid `CREATE VECTOR INDEX`
5. **Sweep** `top_k` on a `VECTOR_SEARCH` with a separate lexical query value and measure how deep a lexical match can reach
6. **Hit** the batch-vs-hybrid constraint on purpose

**What this demonstrates:**
- Where pure semantic search fails: an exact SKU lookup, where the token was never embedded
- Where pure lexical search fails: a paraphrased need that shares no token with any product
- Why an exact-token lookup succeeds or fails on `top_k` alone: the lexical leg is only shown the top `10 * top_k` rows by semantic rank, and inside that pool a match is worth a fixed `1/62` of fused score — enough to reach ten rows deep at `top_k => 5`, 640 at `top_k => 64`, and no further
- The configuration that gives a row both signals at once: a semantic `query_value` describing the product plus the SKU as `lexical_search_query_value` — the notebook prints how far up the page the target is promoted, and separately, on a paraphrased query, which rows hybrid adds and drops
- `lexical_search_columns` / `lexical_search_query_value` — cross-column hybrid retrieval on `VECTOR_SEARCH`
- `CREATE VECTOR INDEX ... STORING(...)` with `lexical_search_columns`, and why `STORING` is mandatory
- Hybrid returns a fused rank score, not a distance — `1 - (1/(60 + rank_vector) + 1/(61 + rank_lexical))`, on a scale that is not comparable across modes
- A vector index cannot be created on an autonomous-embedding column, which forces a two-table design

**Functions used:** `functions/ai_embed` (`AI.EMBED`) | `functions/ai_search` (`AI.SEARCH`) | `functions/vector_search` (`VECTOR_SEARCH`)

**Related:** `workflows/semantic_search` (Semantic Search System) compares manual embedding management against autonomous generation. This notebook is about *retrieval quality* — which signal wins for which query.

**Prerequisites:** `setup` (Setup guide) | `RESOURCES.md` (Function reference)

---
## Setup

Set your project and location, authenticate, and create shared resources.

> Autonomous embedding generation calls `AI.EMBED` on your behalf, so it needs a BigQuery cloud resource connection holding the Vertex AI User role. `VECTOR_SEARCH` and the query-side `AI.EMBED` calls run on end-user credentials. See the `setup` (Setup Reference) for details.

```python
PROJECT_ID = 'statmike-mlops-349915'  # <-- Replace with your project ID
LOCATION = 'US'  # BigQuery dataset location
DATASET_ID = 'bq_ai_functions'  # Shared dataset across all notebooks
CONNECTION_ID = 'bq_ai_functions'  # Shared connection (needed for autonomous embedding generation)
```

### Environment

> **Already set up the project environment?** The cell below is a no-op — packages are already in your kernel. See the `setup` (Setup Reference) for details.
>
> **Running standalone** (Colab, Colab Enterprise, Vertex AI Workbench)? The cell below installs required packages into your current kernel.

```python
from google.cloud import bigquery
from IPython.display import display
import pandas as pd
import time

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

```python
import subprocess as _sp, json as _json

# Create connection (idempotent) — needed for AI.SEARCH autonomous embeddings
_sp.run(['bq', 'mk', '--connection', '--location', LOCATION,
         '--connection_type', 'CLOUD_RESOURCE',
         '--project_id', PROJECT_ID, CONNECTION_ID],
        capture_output=True, text=True)

# Get service account and grant Vertex AI User role
r = _sp.run(['bq', 'show', '--connection', '--format=json',
             '--project_id', PROJECT_ID, '--location', LOCATION, CONNECTION_ID],
            capture_output=True, text=True, check=True)
sa = _json.loads(r.stdout)['cloudResource']['serviceAccountId']
_sp.run(['gcloud', 'projects', 'add-iam-policy-binding', PROJECT_ID,
         f'--member=serviceAccount:{sa}', '--role=roles/aiplatform.user', '--quiet'],
        capture_output=True, text=True)
print(f'Connection {CONNECTION_ID} ready (SA: {sa})')
```

---
## Step 1 — Build the catalog

This workflow uses a real catalog instead of generated data for a hard reason: **a vector index needs at least 5,000 rows in the base table, and the table has to exceed 10 MB before the index is populated.** A hand-built catalog of a few dozen products makes `CREATE VECTOR INDEX` fail outright, and the index demo in Step 6 would be theater.

`bigquery-public-data.thelook_ecommerce.products` has 29,120 rows with unique 32-character hex SKUs — exactly the kind of token that defeats an embedding model. Taking every fourth row yields 7,275 products spanning all 26 categories and 1,593 brands: over the row floor, and roughly 45 MB once 768-dimension vectors land next to them.

The source table has no model number, so this step synthesizes a deterministic one from the brand initials and the product id.

**The design choice that makes the rest of the notebook a proof rather than a coincidence:** `search_text` holds the product name, brand, department, and category — **and deliberately not the SKU or the model number.** Those two live in their own columns and are reachable only lexically. Pure vector search therefore *cannot* retrieve by SKU, because the SKU was never embedded.

```python
query = f'''
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.workflow_catalog_auto` (
  id INT64,
  sku STRING,
  model_number STRING,
  brand STRING,
  name STRING,
  category STRING,
  department STRING,
  retail_price FLOAT64,
  search_text STRING,
  search_text_embedding STRUCT<result ARRAY<FLOAT64>, status STRING>
    GENERATED ALWAYS AS (
      AI.EMBED(search_text,
        connection_id => '{PROJECT_ID}.{LOCATION}.{CONNECTION_ID}',
        endpoint => 'text-embedding-005')
    ) STORED OPTIONS (asynchronous = TRUE)
)
'''
client.query(query).result()

query = f'''
INSERT INTO `{PROJECT_ID}.{DATASET_ID}.workflow_catalog_auto`
  (id, sku, model_number, brand, name, category, department, retail_price, search_text)
SELECT
  id,
  sku,
  CONCAT(
    IFNULL(NULLIF(UPPER(SUBSTR(REGEXP_REPLACE(brand, r'[^A-Za-z]', ''), 1, 3)), ''), 'GEN'),
    '-', FORMAT('%05d', id)
  ) AS model_number,
  brand,
  name,
  category,
  department,
  retail_price,
  CONCAT(name, '. ', brand, ' ', department, ' ', category, '.') AS search_text
FROM `bigquery-public-data.thelook_ecommerce.products`
WHERE MOD(id, 4) = 0
  AND brand IS NOT NULL
  AND name IS NOT NULL
  AND sku IS NOT NULL
'''
job = client.query(query)
job.result()
print(f'{job.num_dml_affected_rows:,} products inserted — embeddings are generating in the background')
```

### Wait for the embeddings — this cell is the long pole

`STORED OPTIONS (asynchronous = TRUE)` is mandatory on a generated embedding column: BigQuery runs the `AI.EMBED` calls as background jobs after the rows land. Searching before they finish silently returns partial results, because rows with a missing embedding are skipped.

A row is done when `search_text_embedding IS NOT NULL AND search_text_embedding.status = ''` — an empty status string means success, a non-empty one carries the per-row error. Rows that fail permanently never become ready, so the loop below stops when `ready + failed = total`, not when `ready = total`.

**Expect this cell to dominate the runtime of the notebook.** Throughput at 7,275 rows is not something this notebook can promise — it depends on your embedding quota, slot availability, and how many background jobs BigQuery schedules. So the loop prints elapsed minutes on every poll, checks `INFORMATION_SCHEMA.COLUMNS.async_generation_status` for blocking errors such as a missing `roles/aiplatform.user` grant, and raises after the deadline instead of spinning forever. If it raises, the table is fine — re-run this cell and it picks up where the background jobs are.

```python
POLL_SECONDS = 30
DEADLINE_MINUTES = 90

progress_sql = f'''
  SELECT
    COUNT(*) AS total,
    COUNTIF(search_text_embedding IS NOT NULL AND search_text_embedding.status = '') AS ready,
    COUNTIF(search_text_embedding IS NOT NULL AND search_text_embedding.status != '') AS failed
  FROM `{PROJECT_ID}.{DATASET_ID}.workflow_catalog_auto`
'''

blocking_sql = f'''
  SELECT
    async_generation_status.blocking_error.reason AS reason,
    async_generation_status.blocking_error.message AS message
  FROM `{PROJECT_ID}.{DATASET_ID}`.INFORMATION_SCHEMA.COLUMNS
  WHERE table_name = 'workflow_catalog_auto' AND is_generated = 'ALWAYS'
'''

start = time.time()
while True:
    row = client.query(progress_sql).to_dataframe().iloc[0]
    total, ready, failed = int(row['total']), int(row['ready']), int(row['failed'])
    elapsed = time.time() - start
    print(f'  {elapsed / 60:6.1f} min elapsed — {ready:,}/{total:,} ready, {failed:,} failed')

    if ready + failed == total:
        break

    blocked = client.query(blocking_sql).to_dataframe()
    blocked = blocked[blocked['reason'].notna()]
    if len(blocked):
        raise RuntimeError(
            'Autonomous embedding generation is BLOCKED and will never finish: '
            f'{blocked.iloc[0]["reason"]} — {blocked.iloc[0]["message"]}. '
            'Most often the connection service account is missing roles/aiplatform.user, '
            'or the Vertex AI API is not enabled. Fix it, then re-run this cell.'
        )

    if elapsed > DEADLINE_MINUTES * 60:
        raise RuntimeError(
            f'Embedding generation did not finish within {DEADLINE_MINUTES} minutes '
            f'({ready:,}/{total:,} ready, {failed:,} failed). Nothing is broken — the '
            'background jobs are simply still running or throttled. Re-run this cell to '
            'keep waiting, or raise DEADLINE_MINUTES.'
        )

    time.sleep(POLL_SECONDS)

print(f'\nFinished in {(time.time() - start) / 60:.1f} minutes: {ready:,} ready, {failed:,} failed')

client.query(f'''
  SELECT
    COUNT(*) AS products,
    COUNT(DISTINCT sku) AS distinct_skus,
    COUNT(DISTINCT brand) AS brands,
    COUNT(DISTINCT category) AS categories,
    ROUND(AVG(LENGTH(search_text)), 1) AS avg_search_text_chars,
    COUNTIF(search_text_embedding.status = '') AS rows_with_embeddings
  FROM `{PROJECT_ID}.{DATASET_ID}.workflow_catalog_auto`
''').to_dataframe()
```

---
## Step 2 — Choose the two head-to-head queries

Everything that follows is judged against two queries that pull in opposite directions:

- an **exact-token lookup** — a single SKU, a string with no meaning for an embedding model
- a **paraphrased need** — `a warm layer for a chilly hike`, which shares no token with any product name in the catalog

The SKU is read out of the table at run time and printed, never pasted in from a previous run. `thelook_ecommerce` is a public dataset that is regenerated periodically, so a hardcoded SKU would rot. The paraphrase is a fixed literal because it is deliberately made of words the catalog does not use.

```python
target = client.query(f'''
  SELECT id, sku, model_number, brand, name, category, department
  FROM `{PROJECT_ID}.{DATASET_ID}.workflow_catalog_auto`
  WHERE category = 'Jeans'
  ORDER BY id
  LIMIT 1
''').to_dataframe().iloc[0]

SKU_QUERY = target['sku']
NEED_QUERY = 'a warm layer for a chilly hike'

print(f'Exact-token query : {SKU_QUERY}')
print(f'  target product  : {target["brand"]} | {target["name"]} | {target["category"]}')
print(f'  model_number    : {target["model_number"]}  (also absent from search_text)')
print(f'Paraphrased query : {NEED_QUERY}')
```

---
## Step 3 — Where each signal fails on its own

Two one-line proofs, before any hybrid appears.

BigQuery's built-in `SEARCH()` is pure full-text matching. It tokenizes both sides and returns `TRUE` only when every query token is present, so it is the cleanest available stand-in for the lexical half of a hybrid search. Point it at the exact-token columns — the same four that `lexical_search_columns` will use later.

```python
lexical = client.query(f'''
  SELECT
    COUNTIF(SEARCH(STRUCT(sku, model_number, brand, name), @sku_q)) AS hits_for_sku,
    COUNTIF(SEARCH(STRUCT(sku, model_number, brand, name), @need_q)) AS hits_for_need
  FROM `{PROJECT_ID}.{DATASET_ID}.workflow_catalog_auto`
''', job_config=bigquery.QueryJobConfig(query_parameters=[
    bigquery.ScalarQueryParameter('sku_q', 'STRING', SKU_QUERY),
    bigquery.ScalarQueryParameter('need_q', 'STRING', NEED_QUERY),
])).to_dataframe()

print(f'Lexical hits for the SKU        : {int(lexical.iloc[0]["hits_for_sku"])}')
print(f'Lexical hits for the paraphrase : {int(lexical.iloc[0]["hits_for_need"])}')
lexical
```

### Pure semantic — AI.SEARCH in VECTOR mode

`AI.SEARCH` with `mode => 'VECTOR'` is the mirror image: it embeds the query text with the same connection and endpoint the base table's generated column uses, then returns nearest neighbours by distance. It always returns `top_k` rows, whether or not any of them are relevant — a distance is not a relevance threshold.

Watch the SKU query. The catalog contains that SKU, but `search_text` does not, so there is nothing in the embedded text for the query to be close to. What comes back is whatever the embedding model thinks a hex string resembles.

```python
for label, q in [('exact SKU', SKU_QUERY), ('paraphrased need', NEED_QUERY)]:
    print(f'--- AI.SEARCH mode VECTOR — {label}: {q}')
    df = client.query(f'''
      SELECT base.sku, base.brand, base.name, base.category, distance
      FROM AI.SEARCH(
        TABLE `{PROJECT_ID}.{DATASET_ID}.workflow_catalog_auto`,
        'search_text',
        @q,
        top_k => 5,
        mode => 'VECTOR'
      )
      ORDER BY distance
    ''', job_config=bigquery.QueryJobConfig(query_parameters=[
        bigquery.ScalarQueryParameter('q', 'STRING', q)])).to_dataframe()
    print(f'    target SKU returned: {(df["sku"] == SKU_QUERY).any()}')
    display(df)
```

---
## Step 4 — AI.SEARCH modes: VECTOR, HYBRID, AUTO

The scoreboard after Step 3: lexical finds the SKU and nothing for the paraphrase; semantic finds the paraphrase and misses the SKU entirely. Neither signal is usable alone for a real catalog.

`AI.SEARCH` takes a `mode` argument to fuse them:

| `mode` | Behavior |
|---|---|
| `'VECTOR'` | pure semantic |
| `'HYBRID'` | fuse the semantic and lexical result lists |
| `'AUTO'` (default) | hybrid **if a hybrid vector index exists**, otherwise semantic |

Anything else is rejected: `mode argument of AI.SEARCH should be one of: VECTOR, HYBRID, AUTO.`

The three calls below are identical except for `mode`.

```python
mode_results = {}

for mode in ['VECTOR', 'HYBRID', 'AUTO']:
    mode_results[mode] = client.query(f'''
      SELECT base.sku, base.brand, base.name, base.category, distance
      FROM AI.SEARCH(
        TABLE `{PROJECT_ID}.{DATASET_ID}.workflow_catalog_auto`,
        'search_text',
        @q,
        top_k => 20,
        mode => '{mode}'
      )
      ORDER BY distance
    ''', job_config=bigquery.QueryJobConfig(query_parameters=[
        bigquery.ScalarQueryParameter('q', 'STRING', SKU_QUERY)])).to_dataframe()
    print(f"--- mode => '{mode}'  (top 5 of 20)")
    display(mode_results[mode].head(5))
```

### What HYBRID can and cannot reach

Three things are visible in the summary below.

**`distance` changes meaning between modes.** Under `VECTOR` it is a genuine distance and small is good. Under `HYBRID` the values collapse into a narrow band just under 1 — that is a fused rank score, not geometry, and `0.967478` at the top of the page is the smallest value the fusion can produce. Step 7 takes the arithmetic apart.

**`AUTO` resolves to `VECTOR` here.** `AUTO` upgrades to hybrid only when a *hybrid vector index* — a vector index created with `lexical_search_columns` — exists on the table. One cannot exist on this table, and Step 5 explains why.

**`HYBRID` does not surface the target SKU.** `AI.SEARCH` has no `lexical_search_columns` argument: its lexical half searches only `column_to_search`, which is `search_text`, which by construction excludes the SKU. No row in the catalog matches the token, so the lexical ranking falls back onto the vector ranking row for row and `HYBRID` returns the same products in the same order as `VECTOR`. Only the score scale changes.

Step 7 moves to `VECTOR_SEARCH` for the two capabilities `AI.SEARCH` does not have — lexical matching on columns that were never embedded, and a lexical query value independent of the vector query. Whether either one is enough to retrieve this row is a question Step 7 measures rather than assumes.

```python
summary = []
for mode, df in mode_results.items():
    hit = df.index[df['sku'] == SKU_QUERY]
    summary.append({
        'mode': mode,
        'rows_returned': len(df),
        'target_sku_returned': bool(len(hit)),
        'target_rank': int(hit[0]) + 1 if len(hit) else None,
        'distance_min': round(float(df['distance'].min()), 6),
        'distance_max': round(float(df['distance'].max()), 6),
    })

print(f'Target SKU: {SKU_QUERY}')
pd.DataFrame(summary)
```

---
## Step 5 — Materialize the vectors so they can be indexed

A vector index cannot be built on an autonomous-embedding column. The generated column has to be a `STRUCT<result ARRAY<FLOAT64>, status STRING>`, and that shape is not indexable:

    CREATE VECTOR INDEX ... ON tbl(search_text_embedding)
    -->  Vector index is not supported on column: 'search_text_embedding'

Reaching inside it does not help either, because an index key must be a bare column name:

    CREATE VECTOR INDEX ... ON tbl(search_text_embedding.result)
    -->  CREATE VECTOR INDEX does not yet support expressions to define index keys,
         only column name is supported

And the `STRUCT` is not optional — declaring the generated column as a plain array fails at `CREATE TABLE` time with `Unsupported generated column expression.`

So the notebook keeps two tables. `workflow_catalog_auto` owns autonomous generation and serves `AI.SEARCH`; `workflow_catalog_products` projects `search_text_embedding.result` into a plain `ARRAY<FLOAT64>` column, carries the hybrid index, and serves `VECTOR_SEARCH`. Nothing is re-embedded — the second table reuses the vectors the first one produced, so the catalog is embedded exactly once.

The trade is symmetric and worth stating plainly: the table that can run `AI.SEARCH` cannot carry a vector index, and the table that carries the index cannot run `AI.SEARCH` (`No generation expression found for the column_to_search`).

```python
query = f'''
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.workflow_catalog_products` AS
SELECT
  id, sku, model_number, brand, name, category, department, retail_price, search_text,
  search_text_embedding.result AS embedding
FROM `{PROJECT_ID}.{DATASET_ID}.workflow_catalog_auto`
WHERE search_text_embedding IS NOT NULL
  AND search_text_embedding.status = ''
'''
client.query(query).result()

client.query(f'''
  SELECT
    COUNT(*) AS products,
    ARRAY_LENGTH(ANY_VALUE(embedding)) AS dimensions,
    ROUND(SUM(ARRAY_LENGTH(embedding)) * 8 / 1048576, 1) AS approx_vector_mb
  FROM `{PROJECT_ID}.{DATASET_ID}.workflow_catalog_products`
''').to_dataframe()
```

---
## Step 6 — A hybrid vector index

`lexical_search_columns` is what turns an ordinary vector index into a **hybrid** index. It works on either index type — `IVF` or `TREE_AH` — and it comes with one hard rule, stated once in the documentation:

> Any column added to the `lexical_search_columns` list must also be added as a stored column in the `STORING` clause.

Skip `STORING` and the statement is rejected before anything is built:

    OPTIONS (index_type = 'TREE_AH', lexical_search_columns = ['sku'])
    -->  Lexical search column sku must be in the list of stored columns.

There is a second collision to know about. The index key and the stored columns are one namespace, so a column can be the key **or** a stored column, never both:

    ON workflow_catalog_products(embedding) STORING (embedding, sku)
    -->  Column embedding found multiple times in workflow_catalog_hybrid_index

Which means a lexical column can never be the index key: lexical columns must be stored, the key must not be stored, and in any case the key has to be the embedding column rather than a `STRING`.

The index below stores everything the search results need and marks the four exact-token columns as lexical. `sku` and `model_number` appear in no embedding anywhere in this notebook, so this index is the only structure that can reach them quickly.

Two operational notes. `CREATE OR REPLACE VECTOR INDEX` is deliberately not used here — the cell drops the index explicitly and creates it with `IF NOT EXISTS`, which makes the re-run behavior obvious. And BigQuery allows only **10 vector-index DDL statements per table per day** (creates and drops combined). A full Restart & Run All issues three of them — the `DROP` and the `CREATE` in the next cell, plus the `DROP` in the cleanup cell at the end — so the quota allows about three complete runs per day.

```python
INDEX_NAME = 'workflow_catalog_hybrid_index'

client.query(f'''
  DROP VECTOR INDEX IF EXISTS {INDEX_NAME}
  ON `{PROJECT_ID}.{DATASET_ID}.workflow_catalog_products`
''').result()

client.query(f'''
  CREATE VECTOR INDEX IF NOT EXISTS {INDEX_NAME}
  ON `{PROJECT_ID}.{DATASET_ID}.workflow_catalog_products`(embedding)
  STORING (id, sku, model_number, brand, name, category, department, retail_price)
  OPTIONS (
    index_type = 'TREE_AH',
    distance_type = 'COSINE',
    lexical_search_columns = ['sku', 'model_number', 'brand', 'name']
  )
''').result()
print(f'{INDEX_NAME} submitted — population runs asynchronously')

index_sql = f'''
  SELECT index_name, index_status, coverage_percentage, last_refresh_time, disable_reason
  FROM `{PROJECT_ID}.{DATASET_ID}`.INFORMATION_SCHEMA.VECTOR_INDEXES
  WHERE table_name = 'workflow_catalog_products'
'''

start = time.time()
while True:
    idx = client.query(index_sql).to_dataframe()
    cov_raw = idx.iloc[0]['coverage_percentage'] if len(idx) else None
    coverage = 0 if cov_raw is None or pd.isna(cov_raw) else int(cov_raw)
    elapsed = time.time() - start
    print(f'  {elapsed / 60:6.1f} min elapsed — coverage {coverage}%')
    if coverage >= 100:
        break
    if elapsed > 45 * 60:
        print('\nStill not fully populated. The searches below remain correct — BigQuery '
              'falls back to brute force for the unindexed rows — they are just slower.')
        break
    time.sleep(30)

display(idx)

client.query(f'''
  SELECT index_name, option_name, option_type, option_value
  FROM `{PROJECT_ID}.{DATASET_ID}`.INFORMATION_SCHEMA.VECTOR_INDEX_OPTIONS
  WHERE table_name = 'workflow_catalog_products'
  ORDER BY option_name
''').to_dataframe()
```

---
## Step 7 — VECTOR_SEARCH with an explicit lexical query

`AI.SEARCH` fuses two lists derived from one piece of text against one column. `VECTOR_SEARCH` exposes the real control surface — two independent query values against two independent sets of columns:

| Argument | What it searches |
|---|---|
| `query_value` | the `ARRAY<FLOAT64>` compared against `column_to_search` |
| `lexical_search_columns` | any `STRING` columns in the base table, and they need not be the embedded one |
| `lexical_search_query_value` | the text matched against those columns, and it need not equal the vector query |

From the documentation: *"The `lexical_search_columns` value doesn't have to correspond to the column from which embeddings were generated. This allows hybrid search to perform a cross-column search on the base table. Similarly, the `lexical_search_query_value` doesn't have to correspond to `query_value`."*

The query vector is produced by calling `AI.EMBED` on the search text with the same endpoint the catalog column used, so both sides of the comparison live in the same embedding space. The calls below are byte-identical apart from `top_k` and the two lexical arguments.

**One scale change before reading the numbers.** `AI.SEARCH` in Step 3 used its default distance type, which is Euclidean; every `VECTOR_SEARCH` call in this step pins `distance_type => 'COSINE'`. On unit-norm embeddings the two are monotonically related — Euclidean distance is `SQRT(2 * cosine_distance)` — so the same neighbours come back in the same order and only the unit changes. Check any row against its Step 3 counterpart and the identity holds to rounding.

```python
import math

sku_params = [bigquery.ScalarQueryParameter('q', 'STRING', SKU_QUERY)]

def sku_search(top_k, with_lexical):
    """Same vector query every time — only top_k and the lexical arguments change."""
    lexical_args = '''
    lexical_search_columns => ['sku', 'model_number', 'brand', 'name'],
    lexical_search_query_value => @q,''' if with_lexical else ''
    return client.query(f'''
      SELECT base.sku AS sku, base.brand AS brand, base.name AS name, base.category AS category,
             distance, ROW_NUMBER() OVER (ORDER BY distance) AS position
      FROM VECTOR_SEARCH(
        TABLE `{PROJECT_ID}.{DATASET_ID}.workflow_catalog_products`,
        'embedding',
        query_value => (AI.EMBED(content => @q, endpoint => 'text-embedding-005')).result,{lexical_args}
        top_k => {top_k},
        distance_type => 'COSINE'
      )
      ORDER BY distance
    ''', job_config=bigquery.QueryJobConfig(query_parameters=sku_params)).to_dataframe()

def pool(top_k):
    """Rows the lexical leg is allowed to see: the top 10 * top_k of the semantic ranking."""
    return 10 * top_k

def score_reach(top_k):
    """Deepest semantic rank that clears the *scoring* gate at this page size.

    A matched row at semantic rank R takes lexical rank 1 and scores 1/(60 + R) + 1/62.
    It has to beat the row holding the last slot, which sits at semantic rank top_k and,
    pushed down one place by the match, lexical rank top_k + 1.
    """
    margin = 1 / (60 + top_k) + 1 / (62 + top_k) - 1 / 62
    if margin <= 0:
        return math.inf  # 1/62 alone outscores the last slot: the scoring gate stops binding
    return math.ceil(1 / margin - 60) - 1

def reach(top_k):
    """Effective reach: a row has to clear the pool gate *and* the scoring gate."""
    return min(score_reach(top_k), pool(top_k))

SHALLOW_TOP_K = 5   # a first page
DEEP_TOP_K = 64     # deep enough to retire the scoring gate, and nothing else

# Where does the target actually sit in the vector ranking of the whole catalog?
sku_vector_rank = client.query(f'''
  SELECT rank_vector, total
  FROM (
    SELECT base.sku AS sku,
           ROW_NUMBER() OVER (ORDER BY distance) AS rank_vector,
           COUNT(*) OVER () AS total
    FROM VECTOR_SEARCH(
      TABLE `{PROJECT_ID}.{DATASET_ID}.workflow_catalog_products`,
      'embedding',
      query_value => (AI.EMBED(content => @q, endpoint => 'text-embedding-005')).result,
      top_k => -1,
      distance_type => 'COSINE'
    )
  )
  WHERE sku = @q
''', job_config=bigquery.QueryJobConfig(query_parameters=sku_params)).to_dataframe().iloc[0]
R = int(sku_vector_rank['rank_vector'])
TOTAL = int(sku_vector_rank['total'])

# The smallest page whose pool reaches the target — and the one right below it.
POOL_TOP_K = max(2, math.ceil(R / 10))  # max(2, ...) keeps top_k >= 1 if the data regenerates

vector_only_sku = sku_search(SHALLOW_TOP_K, with_lexical=False)
sweep_k = sorted({SHALLOW_TOP_K, DEEP_TOP_K, POOL_TOP_K - 1, POOL_TOP_K})
sweep = {k: sku_search(k, with_lexical=True) for k in sweep_k}

def target_row(df):
    hit = df.loc[df['sku'] == SKU_QUERY]
    return hit.iloc[0] if len(hit) else None

print(f'query_value and lexical_search_query_value : {SKU_QUERY}')
print(f'Target semantic rank                       : {R:,} of {TOTAL:,}')
print(f'Target in the vector-only top-{SHALLOW_TOP_K}             : '
      f'{(vector_only_sku["sku"] == SKU_QUERY).any()}')
print(f'Smallest page whose pool holds the target  : ceil({R:,} / 10) = {POOL_TOP_K}')

print(f'\n{"top_k":>6}  {"pool":>7}  {"score gate":>10}  {"reach":>7}  '
      f'{"returned":>8}  {"position":>8}  distance')
for k in sweep_k:
    t = target_row(sweep[k])
    sg = score_reach(k)
    sg_s = '-' if sg == math.inf else f'{sg:,}'
    pos_s = str(int(t['position'])) if t is not None else '-'
    dist_s = f'{t["distance"]:.12f}' if t is not None else '-'
    print(f'{k:>6}  {pool(k):>7,}  {sg_s:>10}  {reach(k):>7,}  '
          f'{str(t is not None):>8}  {pos_s:>8}  {dist_s}')

found = target_row(sweep[POOL_TOP_K])
if found is not None:
    predicted = 1 - (1 / (60 + R) + 1 / 62)
    print(f'\nFused score of the target at semantic rank {R:,}, lexical rank 1:')
    print(f'  1 - (1/(60 + {R}) + 1/62) = {predicted:.15f}')
    print(f'  distance returned         = {found["distance"]:.15f}')
    print(f'  difference                = {abs(predicted - found["distance"]):.3e}')

# With nothing in the pool matching, every row scores 1 - (1/(60 + r) + 1/(61 + r)) for its
# semantic rank r: rank_lexical == rank_vector straight down the page. That is the signature
# of a target that never entered the pool.
missed = sweep[POOL_TOP_K - 1]
zero_match = 1 - (1 / 61 + 1 / 62)
print(f'\nAt top_k => {POOL_TOP_K - 1} the pool holds {pool(POOL_TOP_K - 1):,} rows and stops '
      f'{R - pool(POOL_TOP_K - 1):,} short of the target.')
print(f'  best distance returned                = {missed["distance"].iloc[0]:.12f}')
print(f'  1 - (1/61 + 1/62), i.e. no match      = {zero_match:.12f}')

print('\nReach by top_k — both gates, and the one that binds:')
display(pd.DataFrame(
    [{'top_k': k,
      'lexical pool (10 x top_k)': f'{pool(k):,}',
      'scoring gate': '-' if score_reach(k) == math.inf else f'{score_reach(k):,}',
      'deepest semantic rank retrievable': f'{reach(k):,}',
      'binding gate': 'pool' if pool(k) <= score_reach(k) else 'score'}
     for k in sorted({2, 3, 5, 10, 20, 30, 40, 50, 51, 64, 100, POOL_TOP_K})]).set_index('top_k').T)

print(f'\n--- vector only, top_k => {SHALLOW_TOP_K}')
display(vector_only_sku)
print(f'--- hybrid, top_k => {SHALLOW_TOP_K}')
display(sweep[SHALLOW_TOP_K])
print(f'--- hybrid, top_k => {POOL_TOP_K - 1} (first 5 rows — every one a pool miss)')
display(sweep[POOL_TOP_K - 1].head(5))
print(f'--- hybrid, top_k => {POOL_TOP_K} (first 5 rows)')
display(sweep[POOL_TOP_K].head(5))
if found is not None and int(found['position']) > 5:
    print(f'--- hybrid, top_k => {POOL_TOP_K} (the target row)')
    display(sweep[POOL_TOP_K][sweep[POOL_TOP_K]['sku'] == SKU_QUERY])
```

### Why `top_k` decides whether the token finds the row

`SEARCH()` found this SKU in Step 3 and `lexical_search_columns` now includes `sku`, so the token is present and reachable. What decides whether the row comes back is the page size, and the sweep above runs the identical query at four of them.

**The lexical leg is not shown the whole catalog.** BigQuery hands it the top `10 * top_k` rows by semantic rank and nothing else. That candidate pool is the first gate: a row deeper than `10 * top_k` never reaches BM25 at all and receives no lexical rank, however perfectly the token matches. This SKU sits at semantic rank 2,072 of 7,275 — the cell prints exactly how far down it is — so `top_k => 5` pools 50 rows and `top_k => 64` pools 640, and the row is thousands of places outside both.

The sweep brackets the boundary rather than asserting it. `ceil(2,072 / 10) = 208` is the smallest page whose pool reaches this row, and the two sizes either side of it are the whole argument: at `top_k => 207` the pool stops two rows short and the target is absent; at `top_k => 208` it comes back. One row of page size, nothing else about the query touched.

The returned scores say so directly. *Inside* the pool the lexical leg ranks every candidate: BM25 matches take lexical ranks 1, 2, 3 …, and the pooled rows it does not match fall in behind them in vector order, so no pooled row forfeits a term. When nothing matches, lexical rank equals vector rank the whole way down and the page comes back as `1 - (1/(60 + r) + 1/(61 + r))` — `0.967478`, `0.967998`, `0.968502`, `0.968990`, `0.969464`. That is the zero-match signature, and it is what the `top_k => 5`, `=> 64` and `=> 207` pages all print, in the same order as the vector-only page. The cell sets the best distance from the 207-row page beside `1 - (1/61 + 1/62)` so the two can be read against each other.

Clearing the pool is necessary, not sufficient. A pooled match still has to outscore the row holding the last slot. What the match buys is the move to lexical rank 1, worth a flat `1/62 = 0.0161` of fused score however emphatic the match, and the row it has to displace sits at semantic rank `top_k` and, pushed down one place by the match, lexical rank `top_k + 1`. So the second gate is the deepest `R` satisfying

    1/(60 + R) + 1/62  >  1/(60 + top_k) + 1/(62 + top_k)

**Effective reach is the smaller of the two gates.** The score gate binds on short pages, where a fixed `0.0161` can only displace so much. From `top_k = 51` upward the pool gate takes over and pins reach to exactly `10 * top_k`:

| `top_k` | 2 | 3 | 5 | 10 | 20 | 30 | 40 | 50 | 51 | 64 | 100 | 208 | 300 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| deepest semantic rank retrievable | 3 | 6 | 10 | 23 | 56 | 110 | 212 | 468 | 510 | 640 | 1,000 | 2,080 | 3,000 |

Read the table as a sizing rule, and read it in that order. **`R/10` is a floor, not a recipe.** `top_k` has to be at least `R/10` to put a target at semantic rank `R` into the pool at all, and on short pages it has to be larger still to clear the score gate — a row at semantic rank 100 is already inside the pool at `top_k => 10`, but needs `top_k => 29` to survive the scoring comparison. Only above `top_k = 51`, where the pool gate binds alone, does `R/10` become the answer as well as the floor. A five-row page reaches semantic rank 10 and a 64-row page reaches 640, while a 32-character hex string used as a `query_value` puts its own row 2,072 deep in this 7,275-row catalog — which is why it takes exactly `top_k => 208` to pull back by token alone.

**That makes reach a diagnostic, not a design.** With the SKU as the `query_value` the vector leg contributes nothing but an arbitrary rank, so the row's only route onto the page is `1/62` carrying it across two thousand positions — and ranking a 2,080-row pool to find one known identifier is work a predicate would not do at all. The case worth engineering for is the one a shopper actually types: words *and* an identifier.

So give the row **both** signals — a `query_value` that describes what the product *is*, so the vector leg ranks it on its own merits and lands it inside the pool, and the opaque SKU as `lexical_search_query_value`, so the lexical leg puts it at rank 1. The next cell holds `top_k` at 64. The description alone places the target at semantic rank 49, well inside both the 640-row pool and the 640-deep reach, so the `1/62` has a short distance to carry it instead of thousands of ranks; what changes is how far up the page it lands and whether anything is pushed off the end of it.

The description below is built from the target's own `department` and `category` at run time rather than typed in, so it stays correct when `thelook_ecommerce` is regenerated and a different product becomes the target. It contains no SKU and no brand — it is what a shopper would type from memory. The SKU stays in the lexical argument, untouched.

The comparison the cell prints is the point: same `top_k`, same vector query, one call with the lexical arguments and one without, the target's true rank in the full vector ranking, and where it lands on each page.

```python
TYPE_QUERY = f"{target['department']} {target['category']}"  # e.g. 'Women Jeans' — no SKU, no brand
HYBRID_TOP_K = 64                                            # pools 10 * 64 = 640 rows; the target sits well inside

pair_params = [
    bigquery.ScalarQueryParameter('vq', 'STRING', TYPE_QUERY),
    bigquery.ScalarQueryParameter('lq', 'STRING', SKU_QUERY),
]

def search_page(with_lexical: bool):
    """Same vector query and top_k both times — only the lexical arguments differ."""
    lexical_args = '''
    lexical_search_columns => ['sku', 'model_number', 'brand', 'name'],
    lexical_search_query_value => @lq,''' if with_lexical else ''
    return client.query(f'''
      SELECT base.sku AS sku, base.brand AS brand, base.name AS name, distance,
             ROW_NUMBER() OVER (ORDER BY distance) AS position
      FROM VECTOR_SEARCH(
        TABLE `{PROJECT_ID}.{DATASET_ID}.workflow_catalog_products`,
        'embedding',
        query_value => (AI.EMBED(content => @vq, endpoint => 'text-embedding-005')).result,{lexical_args}
        top_k => {HYBRID_TOP_K},
        distance_type => 'COSINE'
      )
      ORDER BY distance
    ''', job_config=bigquery.QueryJobConfig(query_parameters=pair_params)).to_dataframe()

semantic_page = search_page(with_lexical=False)
hybrid_page = search_page(with_lexical=True)

target_rank = client.query(f'''
  SELECT rank_vector, total
  FROM (
    SELECT base.sku AS sku,
           ROW_NUMBER() OVER (ORDER BY distance) AS rank_vector,
           COUNT(*) OVER () AS total
    FROM VECTOR_SEARCH(
      TABLE `{PROJECT_ID}.{DATASET_ID}.workflow_catalog_products`,
      'embedding',
      query_value => (AI.EMBED(content => @vq, endpoint => 'text-embedding-005')).result,
      top_k => -1,
      distance_type => 'COSINE'
    )
  )
  WHERE sku = @lq
''', job_config=bigquery.QueryJobConfig(query_parameters=pair_params)).to_dataframe().iloc[0]

added = [s for s in hybrid_page['sku'] if s not in set(semantic_page['sku'])]
dropped = [s for s in semantic_page['sku'] if s not in set(hybrid_page['sku'])]
target_position = hybrid_page.loc[hybrid_page['sku'] == SKU_QUERY, 'position']
semantic_position = semantic_page.loc[semantic_page['sku'] == SKU_QUERY, 'position']

print(f'query_value                 : {TYPE_QUERY}')
print(f'lexical_search_query_value  : {SKU_QUERY}')
print(f'target product              : {target["brand"]} | {target["name"]}')
print(f'\nTarget rank in the full vector ranking : '
      f'{int(target_rank["rank_vector"]):,} of {int(target_rank["total"]):,}')
print(f'Target in the semantic-only top-{HYBRID_TOP_K}     : {(semantic_page["sku"] == SKU_QUERY).any()}'
      + (f'  (position {int(semantic_position.iloc[0])})' if len(semantic_position) else ''))
print(f'Target in the hybrid top-{HYBRID_TOP_K}            : {(hybrid_page["sku"] == SKU_QUERY).any()}'
      + (f'  (position {int(target_position.iloc[0])})' if len(target_position) else ''))
print(f'\nRows hybrid added that semantic-only missed : {len(added)}'
      + ('  (the target is one of them)' if SKU_QUERY in added else ''))
print(f'Rows semantic-only had that hybrid dropped  : {len(dropped)}')

hybrid_page['also_in_semantic_top_k'] = hybrid_page['sku'].isin(set(semantic_page['sku']))
display(hybrid_page.head(10))
if len(target_position) and int(target_position.iloc[0]) > 10:
    print(f'--- the target row, at position {int(target_position.iloc[0])} of {HYBRID_TOP_K}')
    display(hybrid_page[hybrid_page['sku'] == SKU_QUERY])
```

### Does the lexical leg damage a query it cannot help?

The exact token is worth exactly one thing: lexical rank 1, a flat `1/62` of fused score, and only for a row the candidate pool already holds. How far that carries a row is set by `top_k` and nothing else — ten ranks deep on a five-row page, 640 on a 64-row one. Both results above are the same arithmetic at two depths: at semantic rank 2,072 the row never enters a 640-row pool and nothing happens, while at semantic rank 49 it is pooled comfortably and the `1/62` lifts it thirty places.

The remaining question is the cost. `SEARCH()` returned zero rows for the paraphrase in Step 3, so it is tempting to assume the lexical half contributes nothing here. It does not work out that way: `SEARCH()` requires *every* query token to be present, while BM25 scores *partial* overlap, so a product named `... Two-Layer Thermal` still matches on `layer`. Run the same pair of calls and let the code print what actually moved.

```python
need_params = [bigquery.ScalarQueryParameter('q', 'STRING', NEED_QUERY)]

vector_only_need = client.query(f'''
  SELECT base.sku, base.brand, base.name, base.category, distance
  FROM VECTOR_SEARCH(
    TABLE `{PROJECT_ID}.{DATASET_ID}.workflow_catalog_products`,
    'embedding',
    query_value => (AI.EMBED(content => @q, endpoint => 'text-embedding-005')).result,
    top_k => 5,
    distance_type => 'COSINE'
  )
  ORDER BY distance
''', job_config=bigquery.QueryJobConfig(query_parameters=need_params)).to_dataframe()

hybrid_need = client.query(f'''
  SELECT base.sku, base.brand, base.name, base.category, distance
  FROM VECTOR_SEARCH(
    TABLE `{PROJECT_ID}.{DATASET_ID}.workflow_catalog_products`,
    'embedding',
    query_value => (AI.EMBED(content => @q, endpoint => 'text-embedding-005')).result,
    top_k => 5,
    distance_type => 'COSINE',
    lexical_search_columns => ['sku', 'model_number', 'brand', 'name'],
    lexical_search_query_value => @q
  )
  ORDER BY distance
''', job_config=bigquery.QueryJobConfig(query_parameters=need_params)).to_dataframe()

v_pos = {s: i + 1 for i, s in enumerate(vector_only_need['sku'])}
h_pos = {s: i + 1 for i, s in enumerate(hybrid_need['sku'])}
shared = [s for s in h_pos if s in v_pos]

print(f'Query: {NEED_QUERY}')
print(f'Products in common between the two top-5 lists : {len(shared)}/5')
print(f'Rows hybrid added   : {[s for s in h_pos if s not in v_pos] or "none"}')
print(f'Rows hybrid dropped : {[s for s in v_pos if s not in h_pos] or "none"}')
print(f'Shared rows that changed position              : '
      f'{sum(1 for s in shared if v_pos[s] != h_pos[s])}/{len(shared)}')
print('\n--- vector only')
display(vector_only_need)
print('\n--- hybrid')
display(hybrid_need)
```

### Reading the hybrid score — reciprocal rank fusion

Compare the `distance` columns above. Vector-only distances spread across a wide range and a perfect match sits near 0. Hybrid values cluster in a narrow band just below 1, and the best row is not close to 0 at all. **Under hybrid retrieval `distance` is not a distance.** It is a fused rank score, it is not comparable to a vector-mode distance, and it must never be called a cosine distance.

Google does not document the fusion. The only public statement of the algorithm is a Google Cloud blog post that says hybrid search uses *"algorithms such as Reciprocal Rank Fusion and BM25"*, with no formula and no constants.

> **Reverse-engineered, not documented.** Everything in the rest of this section was recovered by arithmetic on observed outputs. Google publishes no formula for the hybrid score, so this behavior is not part of any contract and can change without notice. Consume the *ordering*, never the number.

What the observed values fit, exactly, is reciprocal rank fusion over two 1-based ranked lists:

```
distance = 1 - ( 1/(60 + rank_vector) + 1/(61 + rank_lexical) )
```

Only one of those ranks is read directly, though. `VECTOR_SEARCH` returns no rank column, so `rank_vector` comes from a separate semantic-only run and the lexical term is the remainder. That pins *denominators*, not constants: the semantic leg's top row contributes `1/61` and the lexical leg's top row contributes `1/62`. Two readings fit identically, since `1/(61 + rank_lexical)` and `1/(60 + (rank_lexical + 1))` are the same number:

| Reading | Semantic leg | Lexical leg |
|---|---|---|
| A — two constants | k = 60, ranks `1..n` | k = 61, ranks `1..n` |
| **B — one constant, offset ranks** | k = 60, ranks `1..n` | k = 60, ranks `2..n+1` |

Nothing observable separates them, but **B is the likelier**. `k = 60` over 1-based ranks is canonical RRF (Cormack, Clarke and Buettcher, 2009) and the default wherever the constant is exposed — Elasticsearch and OpenSearch name it `rank_constant` and default it to 60, Spanner and AlloyDB write 60 into their documented SQL. No published implementation uses 61 as the constant; 61 appears everywhere instead as the rank-1 denominator `1/(60 + 1)`, which is the transcription slip that would produce the observed `1/62` on a top row. The semantic leg lands on the canonical `1/61` here, so the extra `+1` is on the lexical side.

The 60/61 form is used throughout this notebook because it is the shortest expression that reproduces every observed value — arithmetic that holds, not two design decisions.

Worked against the two rows Google prints in its own `VECTOR_SEARCH` hybrid example:

| Row | Published `distance` | `1 - distance` | Decomposition | Implied ranks |
|---|---|---|---|---|
| `tiger` | 0.967741935483871 | 0.032258064516129 | `1/62 + 1/62` | vector 2, lexical 1 |
| `lion` | 0.96798155737704916 | 0.03201844262295082 | `1/61 + 1/64` | vector 1, lexical 3 |

Longhand for the `tiger` row: the vector term is `1/(60 + 2) = 0.016129032258064516` and the lexical term is `1/(61 + 1) = 0.016129032258064516`; they sum to `0.032258064516129032`, and `1 - 0.032258064516129032 = 0.967741935483871`. Every hybrid value published in the `AI.SEARCH` and `VECTOR_SEARCH` reference pages decomposes the same way, to the last digit.

Four consequences follow directly from the formula:

- **Both legs rank the entire candidate pool, so no returned row ever forfeits a term.** BM25 matches take lexical ranks 1 through *m*, and every remaining pooled row falls in behind them in vector order. There is no single-list state and no penalty for being found by one signal only. The decomposition below recovers a whole-number lexical rank for *every* returned row, including rows that contain none of the query's tokens.
- **The lowest score the fusion can produce is `1 - (1/61 + 1/62) = 0.9674775251189847`**, from rank 1 in both legs. Nothing scores lower. Step 4's `HYBRID` page is the degenerate case that shows the fallback at work: no row in the catalog matched the SKU token, so lexical rank equalled vector rank everywhere, and the five returned scores are exactly `1 - (1/61 + 1/62)`, `1 - (1/62 + 1/63)`, `1 - (1/63 + 1/64)` and so on down the page.
- **The whole scale is squeezed into roughly 0.967 to 1.** Two rows separated by one rank differ in the fourth decimal place, so score gaps carry almost no information.
- **A lexical match is worth a fixed amount, not a proportional one.** Promotion to lexical rank 1 is worth `1/62 = 0.0161` however emphatic the match, which is why hybrid retrieval widens the page by a bounded amount, and why `top_k` sets that bound twice over — the candidate pool and the reach table in Step 7.

The cell below tests all of this against this notebook's own data, using the page from the search that carries both signals. It re-runs the vector-only search with `top_k => -1` to obtain a true rank for every product, then inverts the formula on each returned hybrid row to recover the lexical rank BigQuery never reports:

```
rank_lexical = 1 / ( (1 - distance) - 1/(60 + rank_vector) ) - 61
```

If the arithmetic is right, those recovered ranks come out as whole numbers; if it is wrong they come out as arbitrary fractions, so the rounding-error column is the actual test. Under reading B the engine's own lexical ranks would be one higher than the `implied_rank_lexical` recovered here — the same integers, shifted. The recovered ranks carry a second signature of pool-wide ranking, in the `rank_lexical - rank_vector` offsets the cell tallies: the one row that matched the SKU token holds lexical rank 1, and every row above it in vector order is pushed down exactly one place. Rows below it should keep their positions, and the tally shows most of them do — read the `+0` bucket against the `±1` and `±2` strays, which are distance ties re-broken between the two `ROW_NUMBER` passes rather than fusion effects.

```python
K_VECTOR = 60   # canonical RRF constant, 1-based ranks — reproduces the vector leg exactly
K_LEXICAL = 61  # shorthand: equivalently k=60 with lexical ranks offset by one (see above)

ranks = client.query(f'''
  SELECT base.sku AS sku, distance,
         ROW_NUMBER() OVER (ORDER BY distance) AS rank_vector
  FROM VECTOR_SEARCH(
    TABLE `{PROJECT_ID}.{DATASET_ID}.workflow_catalog_products`,
    'embedding',
    query_value => (AI.EMBED(content => @vq, endpoint => 'text-embedding-005')).result,
    top_k => -1,
    distance_type => 'COSINE'
  )
''', job_config=bigquery.QueryJobConfig(query_parameters=pair_params)).to_dataframe()

decomp = hybrid_page[['sku', 'name', 'distance']].rename(columns={'distance': 'hybrid_distance'})
decomp = decomp.merge(ranks[['sku', 'rank_vector']], on='sku', how='left')
decomp['is_target'] = decomp['sku'] == SKU_QUERY

decomp['fused_total'] = 1 - decomp['hybrid_distance']
decomp['vector_term'] = 1 / (K_VECTOR + decomp['rank_vector'])
decomp['lexical_term'] = decomp['fused_total'] - decomp['vector_term']
decomp['implied_rank_lexical'] = 1 / decomp['lexical_term'] - K_LEXICAL
decomp['rank_rounding_error'] = (
    decomp['implied_rank_lexical'] - decomp['implied_rank_lexical'].round()).abs()
decomp['reconstructed_distance'] = 1 - (
    decomp['vector_term'] + 1 / (K_LEXICAL + decomp['implied_rank_lexical'].round()))
decomp['abs_error'] = (decomp['reconstructed_distance'] - decomp['hybrid_distance']).abs()
decomp['lexical_minus_vector'] = decomp['implied_rank_lexical'].round() - decomp['rank_vector']

print(f'query_value: {TYPE_QUERY}   |   lexical_search_query_value: {SKU_QUERY}')
print(f'Products ranked by the vector signal: {len(ranks):,}')
print(f'Hybrid rows decomposed: {len(decomp)}')
print(f'Largest gap between an implied lexical rank and a whole number: '
      f'{decomp["rank_rounding_error"].max():.3e}')
print(f'Largest gap between the reconstructed and returned score: '
      f'{decomp["abs_error"].max():.3e}')

print('\nrank_lexical - rank_vector, across the returned rows:')
for offset, n in decomp['lexical_minus_vector'].value_counts().sort_index().items():
    print(f'  {offset:+.0f}: {n} row(s)')

tgt = decomp[decomp['is_target']]
if len(tgt):
    t = tgt.iloc[0]
    rv = int(t['rank_vector'])
    print(f'\nTarget row: vector rank {rv:,}, lexical rank {t["implied_rank_lexical"]:.0f}')
    print(f'  fused score returned  = {t["hybrid_distance"]:.15f}')
    print(f'  1 - (1/({K_VECTOR} + {rv}) + 1/{K_LEXICAL + 1}) = '
          f'{1 - (1 / (K_VECTOR + rv) + 1 / (K_LEXICAL + 1)):.15f}')

decomp
```

### The batch constraint

`VECTOR_SEARCH` normally accepts a whole *table* of queries and answers them in one pass — that is the batch form, and it is what `workflows/semantic_search/` uses. Hybrid retrieval cannot do it. Passing the queries as a relation makes `query_value` absent, and the lexical arguments only exist on the single-query form:

> `lexical_search_columns` can be used only when `query_value` is specified with single search. Hybrid search doesn't support batch queries.

Run it anyway, so the error message is on the record rather than a surprise in production. Because this is caught at query-analysis time it costs nothing — the query never executes.

```python
query = f'''
SELECT query.q, base.sku, base.name, distance
FROM VECTOR_SEARCH(
  TABLE `{PROJECT_ID}.{DATASET_ID}.workflow_catalog_products`,
  'embedding',
  (SELECT q, (AI.EMBED(content => q, endpoint => 'text-embedding-005')).result AS emb
   FROM UNNEST([@sku_q, @need_q]) AS q),
  'emb',
  top_k => 3,
  lexical_search_columns => ['sku', 'model_number', 'brand', 'name'],
  lexical_search_query_value => @sku_q
)
'''

try:
    display(client.query(query, job_config=bigquery.QueryJobConfig(query_parameters=[
        bigquery.ScalarQueryParameter('sku_q', 'STRING', SKU_QUERY),
        bigquery.ScalarQueryParameter('need_q', 'STRING', NEED_QUERY),
    ])).to_dataframe())
    print('Unexpected: the batch + hybrid combination was accepted.')
except Exception as e:
    print('Expected failure:')
    print(e)
```

---
## Which retrieval signal, and when

What each approach did with the queries this notebook ran:

| Query | `SEARCH()` full text | `AI.SEARCH mode => 'VECTOR'` | `AI.SEARCH mode => 'HYBRID'` | `VECTOR_SEARCH` + `lexical_search_columns` |
|---|---|---|---|---|
| Exact SKU and nothing else | finds the single row | **fails** — the SKU was never embedded | **fails** — the lexical half sees only `column_to_search` | **decided by `top_k`** — out of reach at `top_k => 5`, `=> 64` and `=> 207`, returned at `=> 208`, because the lexical leg only sees the top `10 * top_k` rows and this SKU sits at semantic rank 2,072 |
| A description of the product, SKU passed separately as the lexical query | cannot express — one query string | cannot express — no separate lexical query | cannot express — no separate lexical query | **the configuration to reach for** — the row earns a vector rank *and* lexical rank 1, and is promoted from vector rank 49 to position 19 of 64 rather than scraping onto the end of the page |
| Paraphrased need | **fails — 0 rows** | best | not run in this notebook | no damage — four of the five rows are retained and reordered, and BM25 partial overlap on `layer` swaps in a fifth |

Read the first two rows together. The exact token is worth lexical rank 1 and nothing else, a flat `1/62` of fused score, so how deep it reaches is a property of the page size rather than of the query: ten rows at `top_k => 5`, 110 at `top_k => 30`, and a flat `10 * top_k` from `top_k => 51` up — 640 rows at `top_k => 64`. For a target at semantic rank `R`, size `top_k` to at least `R/10`, and to whatever more the reach table demands on short pages. Adding a semantic `query_value` that describes the product is what lets a short page work at all, because the vector leg then does most of the carrying instead of leaving `1/62` to cross thousands of ranks.

And how the two search functions compare as tools:

| Feature | `AI.SEARCH` | `VECTOR_SEARCH` |
|---------|-------------|-----------------|
| **Setup** | Autonomous embedding column required | You supply an `ARRAY<FLOAT64>` column |
| **Query embedding** | Automatic | You call `AI.EMBED` yourself |
| **Lexical columns** | Only `column_to_search` | Any `STRING` columns, via `lexical_search_columns` |
| **Separate lexical query text** | No | Yes, `lexical_search_query_value` |
| **Vector index** | Impossible on the generated column | Full `IVF` and `TREE_AH` support, including hybrid |
| **Batch queries** | One query per call | Supported — but never together with hybrid |
| **Score under hybrid** | Fused rank score, roughly 0.967–1.0 | Fused rank score, roughly 0.967–1.0 |
| **Best for** | Semantic search with zero plumbing | Catalogs and support corpora where users type identifiers *alongside* words |

Reach for `AI.SEARCH` when you want semantic search and no infrastructure. Reach for `VECTOR_SEARCH` with `lexical_search_columns` when your users type SKUs, part numbers, error codes or ticket IDs **together with** words describing what they want — that is the shape hybrid retrieval is built for, and the middle row of the table above is it.

When the identifier is *all* the user typed, do not reach for retrieval at all. Hybrid search can find the row, but only from inside a `10 * top_k` pool and only if the page was sized for the depth the row happens to sit at, whereas `WHERE sku = @sku` is exact, instant, reads one row instead of ranking a pool of them, has no pool of its own, and cannot be outranked by a fusion score. Hybrid search widens and re-ranks an ambiguous query; it is not a substitute for a predicate.
