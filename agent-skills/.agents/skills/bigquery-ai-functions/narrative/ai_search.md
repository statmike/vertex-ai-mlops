# AI.SEARCH — BigQuery AI Functions

`AI.SEARCH` is a simplified search function for tables with autonomous embedding generation enabled. It embeds the query at runtime and searches the table — no manual embedding step needed. The `mode` argument picks the retrieval strategy: semantic (vector) search, lexical (keyword) search fused with semantic search, or an automatic choice.

**Status:** `AI.SEARCH` is **GA**. Only the `mode` argument is **Preview** — hybrid search shipped 2026-06-25, was temporarily disabled 2026-07-09, and was restored 2026-08-03 (verified 2026-09-01). There is no separate `HYBRID_SEARCH` function; hybrid retrieval ships as `mode` here and as `lexical_search_columns` on `functions/vector_search` (`VECTOR_SEARCH`).

**When to use it:**
- You want the simplest possible semantic search (no embedding management)
- Your base table has autonomous embedding generation enabled
- You need single-query semantic search with a string literal
- You want hybrid (semantic + keyword) retrieval without assembling the lexical half yourself

**Alternatives:**
- `functions/vector_search` (`VECTOR_SEARCH`) — More control: batch search, custom embeddings, manual embedding management, and hybrid search over lexical columns you name explicitly
- `functions/ai_embed` (`AI.EMBED`) — Create individual embeddings for custom search logic
- `functions/ai_similarity` (`AI.SIMILARITY`) — Compare two specific inputs directly

**Featured in:** `workflows/semantic_search` (Semantic Search System) | `workflows/catalog_search` (Catalog Search)

**References:** `RESOURCES.md` (Full syntax reference) | [Official documentation](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-search) | `setup` (Setup guide)

---
## Setup

Set your project and location, authenticate, and create a temporary dataset for this notebook.

> This function requires a connection. The cells below create them if they don't exist. See the `setup` (Setup Reference) for details.

```python
PROJECT_ID = 'statmike-mlops-349915'  # <-- Replace with your project ID
LOCATION = 'US'  # BigQuery dataset location
DATASET_ID = 'bq_ai_functions'  # Shared dataset across all notebooks
CONNECTION_ID = 'bq_ai_functions'  # Shared connection
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

```python
import subprocess as _sp, json as _json

# Create connection (idempotent)
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
## Examples — SQL

Progressive examples from simplest to most advanced. Each cell adds one new concept.

### Setup: Create a table with autonomous embedding generation

AI.SEARCH requires a base table with autonomous embedding generation enabled.
This is configured with a `GENERATED ALWAYS AS` column that calls `AI.EMBED`, with `OPTIONS(asynchronous = TRUE)`. BigQuery then automatically generates and maintains embeddings when data is inserted or updated. The same column definition works in `ALTER TABLE ... ADD COLUMN`, so an existing table can be upgraded in place.

**Note on task_type:** When you configure autonomous embedding generation, BigQuery handles the `task_type` automatically — it uses `RETRIEVAL_DOCUMENT` when indexing your table data and `RETRIEVAL_QUERY` when embedding search queries at runtime. This is the correct **asymmetric** pattern for retrieval. See the `functions/ai_embed` (`AI.EMBED`) notebook for the full list of task types.

**Limitations:**
- One automatically generated embedding column per table.
- The column must be `STRUCT<result ARRAY<FLOAT64>, status STRING>`; declaring it as a plain `ARRAY<FLOAT64>` fails with `Unsupported generated column expression`.
- `OPTIONS (asynchronous = TRUE)` is required — without it both `CREATE TABLE` and `ALTER TABLE ... ADD COLUMN` fail with `Generated embedding column requires asynchronous option to be true`.
- No column-level security policies (policy tags) on such tables, and no partitioned vector index.
- A vector index on the generated column is not supported at all — see example 6.

```python
# Create table with autonomous embedding generation
query = f'''
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.ai_search_knowledge_base` (
  id INT64,
  title STRING,
  content STRING,
  content_embedding STRUCT<result ARRAY<FLOAT64>, status STRING>
    GENERATED ALWAYS AS (
      AI.EMBED(content,
        connection_id => '{PROJECT_ID}.{LOCATION}.{CONNECTION_ID}',
        endpoint => 'text-embedding-005')
    ) STORED OPTIONS (asynchronous = TRUE)
)
'''
client.query(query).result()
print('Table created with autonomous embedding generation')

# Insert data — embeddings are generated automatically in the background
query = f'''
INSERT INTO `{PROJECT_ID}.{DATASET_ID}.ai_search_knowledge_base` (id, title, content)
VALUES
  (1, 'BigQuery', 'BigQuery is a serverless enterprise data warehouse for analytics at any scale.'),
  (2, 'Cloud Functions', 'Cloud Functions is a serverless execution environment for building event-driven applications.'),
  (3, 'Cloud Storage', 'Cloud Storage is a managed service for storing unstructured data of any size.'),
  (4, 'Kubernetes Engine', 'Google Kubernetes Engine provides a managed environment for deploying containerized applications.'),
  (5, 'Pub/Sub', 'Pub/Sub is an asynchronous messaging service that decouples services that produce events from services that process events.')
'''
client.query(query).result()
print('Data inserted — embeddings generating asynchronously')

# Wait for embeddings to be generated
import time
for attempt in range(30):
    df = client.query(f'''
        SELECT
          COUNT(*) AS total,
          COUNTIF(content_embedding IS NOT NULL AND content_embedding.status = '') AS ready
        FROM `{PROJECT_ID}.{DATASET_ID}.ai_search_knowledge_base`
    ''').to_dataframe()
    total, ready = int(df.iloc[0]['total']), int(df.iloc[0]['ready'])
    if ready == total:
        print(f'All {total} embeddings ready')
        break
    print(f'  Waiting... {ready}/{total} embeddings ready')
    time.sleep(10)
else:
    print(f'Warning: only {ready}/{total} embeddings ready after 5 minutes')
```

### 1. Basic semantic search

AI.SEARCH takes the table, the column to search, and a query string. It embeds the query automatically and returns nearest matches.

```python
query = f'''
SELECT base.title, base.content, distance
FROM AI.SEARCH(
  TABLE `{PROJECT_ID}.{DATASET_ID}.ai_search_knowledge_base`,
  'content',
  'serverless compute for running code'
)
'''
client.query(query).to_dataframe()
```

### 2. Limiting results with top_k

```python
query = f'''
SELECT base.title, base.content, distance
FROM AI.SEARCH(
  TABLE `{PROJECT_ID}.{DATASET_ID}.ai_search_knowledge_base`,
  'content',
  'data storage and analytics',
  top_k => 2
)
'''
client.query(query).to_dataframe()
```

### 3. Changing distance type

```python
query = f'''
SELECT base.title, base.content, distance
FROM AI.SEARCH(
  TABLE `{PROJECT_ID}.{DATASET_ID}.ai_search_knowledge_base`,
  'content',
  'messaging and events',
  top_k => 3,
  distance_type => 'COSINE'
)
'''
client.query(query).to_dataframe()
```

### 4. Hybrid search — `mode => 'HYBRID'` (Preview)

`mode` selects the retrieval strategy: `'VECTOR'` (semantic only), `'HYBRID'` (semantic fused with a lexical keyword search), or `'AUTO'` (the default). Hybrid aims at the exact tokens embeddings blur — SKUs, error codes, proper nouns — but it does not reach them by overriding the semantic leg. It fuses two ranked lists, so it changes *which* rows come back only when the two lists disagree, and how far down the corpus a keyword hit can reach is bounded by `top_k` twice over — once by the pool of rows the lexical leg is given, once by the fused score. Example 6 derives both gates and the reach they buy.

- `AI.SEARCH` takes **no** lexical arguments. The lexical half searches `column_to_search` with the same query string — there is no way to hand it an exact token of its own. Reach for `functions/vector_search` (`VECTOR_SEARCH`) when the keyword query has to run against *other* columns or carry its own text — it accepts explicit `lexical_search_columns` and `lexical_search_query_value`.
- No vector index is required. `mode => 'HYBRID'` runs on this five-row table with no index of any kind.
- `distance` changes meaning in hybrid mode. It stops being a distance — example 6 takes that apart.

```python
query = f'''
SELECT base.title, base.content, distance
FROM AI.SEARCH(
  TABLE `{PROJECT_ID}.{DATASET_ID}.ai_search_knowledge_base`,
  'content',
  'serverless messaging between services',
  top_k => 3,
  mode => 'HYBRID'
)
'''
client.query(query).to_dataframe()
```

**Did the lexical half change the answer?** That is a claim about output, so measure it rather than assert it. The cell below runs the same query text in both modes and prints the set difference.

```python
# Semantic-only vs hybrid on the same query text — compare the returned rows, not the scores
search_text = 'serverless messaging between services'

def top_titles(mode):
    query = f'''
    SELECT base.title
    FROM AI.SEARCH(
      TABLE `{PROJECT_ID}.{DATASET_ID}.ai_search_knowledge_base`,
      'content',
      '{search_text}',
      top_k => 3,
      mode => '{mode}'
    )
    ORDER BY distance
    '''
    return client.query(query).to_dataframe()['title'].tolist()

semantic, hybrid = top_titles('VECTOR'), top_titles('HYBRID')
print(f'semantic-only (VECTOR): {semantic}')
print(f'hybrid (HYBRID)       : {hybrid}')
print(f'Rows hybrid added that semantic-only missed: {[t for t in hybrid if t not in semantic] or "none"}')
print(f'Same rows, same order: {semantic == hybrid}')
```

**This corpus is too small to show a recall win, and that is worth understanding.** Five rows with `top_k => 3` means the semantic leg alone already returns 60% of the table, and every row here is an ordinary product description — there is no opaque token for the lexical leg to contribute that the embedding has not already found. Fusion has nothing to add, so it reorders at most.

Salting the corpus with error codes does not rescue the demo either: on documents this short a unique alphanumeric token dominates the embedding, so the semantic leg returns the row carrying the code first and hybrid has nothing left to recover (measured on a copy of this table, 2026-09-02).

Membership changes when two things line up: a token the embedding does not resolve, and a `top_k` deep enough for the fused score to reach the row carrying it. A rank-1 lexical match is worth `1/62` ≈ `0.0161`, which at `top_k => 3` reaches no further than semantic rank 6 — and the lexical leg is only handed the top `10 * top_k` rows to score, so even at `top_k => 64` nothing below semantic rank 640 can be recovered. Example 6 has the full reach table. For `VECTOR_SEARCH` there is a third lever: the exact token can be passed separately as `lexical_search_query_value` instead of being folded into the semantic query text.

See the `workflows/catalog_search` (Catalog Search) workflow for that head-to-head over a real product catalog, and the `functions/vector_search` (`VECTOR_SEARCH`) notebook for the same comparison with the underlying vector and lexical ranks printed side by side.

### 5. The default — `mode => 'AUTO'`, and the trap inside it

`AUTO` is the default, so examples 1-3 all ran in `AUTO` mode. The documented rule: `AUTO` performs a hybrid search **only if a hybrid index exists** — a vector index created with the `lexical_search_columns` option — and otherwise performs a semantic-only search.

**This is the failure mode worth memorizing.** `AUTO` never errors and never warns when it falls back. Ask for `AUTO` expecting hybrid, get a clean, plausible result set, and nothing in the output announces that the lexical half never ran. The only tell is the `distance` column: semantic distances spread out, fused hybrid scores cluster just under `0.97`.

This table cannot have a vector index at all (example 6 shows why), so `AUTO` resolves to semantic-only here and always will. The distances below are ordinary vector distances, identical to the `'VECTOR'` rows in example 6 and nothing like the fused scores in example 4. Set `mode` explicitly whenever hybrid behavior matters.

```python
query = f'''
SELECT base.title, base.content, distance
FROM AI.SEARCH(
  TABLE `{PROJECT_ID}.{DATASET_ID}.ai_search_knowledge_base`,
  'content',
  'serverless messaging between services',
  top_k => 3,
  mode => 'AUTO'
)
'''
client.query(query).to_dataframe()
```

### 6. `mode => 'VECTOR'` — and what `distance` means in each mode

`'VECTOR'` forces a semantic-only search: the same work `AUTO` falls back to, but stated explicitly so the query never rides on `AUTO`'s index-sensitive default. On this table that default can never resolve to anything else — the reason is below the results. Running all three modes over one query text puts the difference on screen in a single result set.

Read the two scales separately:
- **`VECTOR`** returns a real distance in the space named by `distance_type` (`EUCLIDEAN` by default). Smaller is closer and an exact self-match is `0`.
- **`HYBRID`** returns a fused rank score. Smaller is still better, but it is not a distance: an exact self-match scores about `0.967`, not `0`, and the values are not comparable to `VECTOR` distances. Never put them on one axis or threshold them with one cutoff. `distance_type` has no effect in this mode: the fused score is built from the two rank lists, not from a metric space.

```python
query = f'''
SELECT 'VECTOR' AS search_mode, base.title, distance
FROM AI.SEARCH(
  TABLE `{PROJECT_ID}.{DATASET_ID}.ai_search_knowledge_base`,
  'content', 'serverless messaging between services', top_k => 3, mode => 'VECTOR'
)
UNION ALL
SELECT 'AUTO', base.title, distance
FROM AI.SEARCH(
  TABLE `{PROJECT_ID}.{DATASET_ID}.ai_search_knowledge_base`,
  'content', 'serverless messaging between services', top_k => 3, mode => 'AUTO'
)
UNION ALL
SELECT 'HYBRID', base.title, distance
FROM AI.SEARCH(
  TABLE `{PROJECT_ID}.{DATASET_ID}.ai_search_knowledge_base`,
  'content', 'serverless messaging between services', top_k => 3, mode => 'HYBRID'
)
ORDER BY search_mode, distance
'''
client.query(query).to_dataframe()
```

**What the hybrid score actually is.** BigQuery documents no fusion algorithm and returns no rank or score column. Reconstructed from observed output, hybrid `distance` is one minus a Reciprocal Rank Fusion score over the two ranked lists, with 1-based ranks:

```
distance = 1 - ( 1/(60 + rank_vector) + 1/(61 + rank_lexical) )
```

Read the two denominators carefully — and read what they do and do not establish. Only the semantic rank is ever observed: the function returns no rank column, so `rank_vector` comes from a separate semantic-only run and the lexical term is whatever remains. That pins *denominators*, not constants. Since `1/(61 + r)` and `1/(60 + (r + 1))` are the same number, two readings fit the measurements identically:

| Reading | Semantic leg | Lexical leg |
|---|---|---|
| A — two constants | k = 60, ranks `1..n` | k = 61, ranks `1..n` |
| B — one constant, offset ranks | k = 60, ranks `1..n` | k = 60, ranks `2..n+1` |

**B is the likelier.** k = 60 over 1-based ranks is canonical reciprocal rank fusion (Cormack, Clarke and Buettcher, 2009) and the default wherever the constant is exposed — Elasticsearch and OpenSearch name it `rank_constant` and default it to 60, Spanner and AlloyDB write 60 into their documented SQL — while 61 appears as the constant in no published implementation. The 60/61 form is used here because it is the shortest expression that reproduces every observed value, not because two bases were deliberately chosen. Either way the best attainable score is `1 - (1/61 + 1/62)` = `0.9674775251189847`, a row at rank 1 in *both* legs — which is why hybrid scores sit just under `0.97` and a self-match is never `0`.

**The lexical leg ranks the entire candidate pool.** BigQuery hands the lexical half only the top `10 * top_k` rows by semantic rank, and that pool is the whole universe it sees. Inside it, true BM25 matches take lexical ranks 1 through *m*, and every remaining pooled row falls back to its semantic order behind them. Search with a lexical value that matches nothing and every returned row still carries a lexical term, with `rank_lexical` equal to `rank_vector`; promote one row to lexical rank 1 and the row that held rank 1 slides to 2 while everything below the promoted row is untouched. No pooled row is ever missing a term. Hybrid re-orders a single candidate set — it does not merge two lists in which a row can be present or absent. A row *outside* the pool is a different case entirely: it receives no lexical rank at all, however perfectly the token matches.

**How deep a keyword hit reaches.** Two gates decide it, and `top_k` sets both. The *pool* gate is the one above: only rows with `rank_vector <= 10 * top_k` are scored lexically. The *score* gate is the arithmetic — a rank-1 lexical match is worth `1/62` ≈ `0.0161`, so a matched row at semantic rank *R* scores `1/(60 + R) + 1/62`, and it has to beat the row holding the last slot, which sits at semantic rank `top_k` and, pushed down one position by the match, lexical rank `top_k + 1`. Effective reach is the smaller of the two, `min(score gate, 10 * top_k)`:

| `top_k` | 2 | 3 | 5 | 10 | 20 | 30 | 40 | 50 | 51 | 64 | 100 | 208 | 300 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| deepest semantic rank retrievable | 3 | 6 | 10 | 23 | 56 | 110 | 212 | 468 | 510 | 640 | 1,000 | 2,080 | 3,000 |
| binding gate | score | score | score | score | score | score | score | score | pool | pool | pool | pool | pool |

The score gate binds below `top_k = 51`; from 51 up the pool binds and reach is simply `10 * top_k`. The sizing rule that falls out is a floor, not a recipe: **`top_k` of at least `R/10` is necessary to retrieve a row at semantic rank *R*, and sufficient only once the pool gate is the binding one.** While the score gate binds — below `top_k = 51`, so for targets less than a few hundred ranks deep — `R/10` is not enough: a target at semantic rank 100 needs `top_k = 29`, not 10, and one at rank 200 needs `top_k = 40`, not 20. Read the real requirement off the reach table above. The crossover is sharp, and it lands where the pool gate says it will — on a 3,000-row corpus a target at semantic rank 3,000 is absent at `top_k => 299` and returned at `top_k => 300`; on a 1,500-row corpus a target at rank 1,500 flips at `top_k => 150`. Those synthetic corpora sit below BigQuery's 5,000-row `CREATE VECTOR INDEX` floor and are brute-force scanned, but the gate is not an artifact of running unindexed: on a 7,275-row product catalog carrying an `ACTIVE`, fully covered hybrid `TREE_AH` index with `lexical_search_columns`, a target at semantic rank 2,072 still needs `top_k >= 208`, and `top_k => 64` returns nothing. An index neither causes the pool gate nor avoids it. Below roughly `top_k => 30` a keyword only nudges rows that were already near the top, which is exactly what example 4 shows at `top_k => 3`. Hybrid widens recall in proportion to `top_k`, never unboundedly. And when the identifier *is* the whole query and the answer has to be certain, a `WHERE` predicate cannot be outranked by a fusion score at all — and it has no pool.

This decomposition is reverse-engineered from observation, not documented by Google, and can change without notice — read it as an explanation of the shape of the numbers, never as an API contract. The `functions/vector_search` (`VECTOR_SEARCH`) notebook carries the full derivation with the underlying ranks visible.

**Why `AUTO` can never upgrade an `AI.SEARCH` base table.** A hybrid index is a vector index created with `lexical_search_columns`, where every lexical column also appears in a `STORING` clause and none of them is the index key:

```sql
CREATE VECTOR INDEX kb_hybrid_index
ON `PROJECT_ID.DATASET.some_table`(embedding)
STORING (content)
OPTIONS (index_type = 'IVF', distance_type = 'COSINE',
         lexical_search_columns = ['content']);
```

That index cannot exist on an `AI.SEARCH` base table. `AI.SEARCH` requires autonomous embedding generation, whose embedding column is a generated `STRUCT<result ARRAY<FLOAT64>, status STRING>`, and a vector index cannot be built on it:

```
CREATE VECTOR INDEX ... ON tbl(content_embedding)
-->  Vector index is not supported on column: 'content_embedding'
```

Nor on a field of it — `ON tbl(content_embedding.result)` returns `CREATE VECTOR INDEX does not yet support expressions to define index keys, only column name is supported` — and the generated column cannot be declared as a plain `ARRAY<FLOAT64>` to dodge the restriction. The DDL passes a dry run and fails at execution (verified 2026-09-01). Separately, a vector index only populates at 5,000+ rows and 10 MB, so this five-row demo table could not carry one in any case.

**The practical consequence:** on an `AI.SEARCH` base table today, `AUTO` is always semantic-only and `HYBRID` must be asked for by name. To get an *indexed* hybrid search, project `content_embedding.result` into a second table as a plain `ARRAY<FLOAT64>` column, build the hybrid index there, and query it with `VECTOR_SEARCH` — the `workflows/catalog_search` (Catalog Search) workflow builds that two-table design end to end.

### 7. `CREATE SEARCH INDEX` and `ALTER SEARCH INDEX` — the other index type

A **search index** is a different object from the vector index discussed above: it powers the `SEARCH()` function over text, not `VECTOR_SEARCH`. This project creates none, and the reason is a measured size gate worth knowing before you plan around one.

**`CREATE SEARCH INDEX` succeeds on a small table — and then the index never populates.** `INFORMATION_SCHEMA.SEARCH_INDEXES` reports `index_status` `TEMPORARILY DISABLED`, `coverage_percentage` 0, `disable_time` equal to `creation_time`, and this `disable_reason` (measured on a 19,055-row table):

> The base table size is below the threshold of 10737418240 bytes for indexing. The index does not provide noticeable search performance gains when the base table is too small.

10,737,418,240 bytes is exactly **10 GiB** — against the vector index's 5,000-row hard reject and ~10 MB population gate. Nothing at teaching scale clears it, which is why hybrid search here rides on `lexical_search_columns` on a vector index instead.

```sql
CREATE SEARCH INDEX ai_search_kb_index
ON `PROJECT_ID.DATASET.some_large_table`(name, brand, category)
OPTIONS (analyzer = 'LOG_ANALYZER');
```

**The recorded `ddl` is normalized, not a verbatim echo.** The statement above comes back from `SEARCH_INDEXES.ddl` as `OPTIONS (data_types = ['STRING'])`, with the analyzer surfaced in the separate `analyzer` column.

**Both `ALTER` forms require a BACKGROUND reservation.** With no reservation on the project each is rejected outright:

```
Cannot alter search index on table some_large_table because there is no BACKGROUND reservation.
```

This is the same gate that blocks `ALTER VECTOR INDEX ... REBUILD` — see `functions/vector_search` (`functions/vector_search/`) section 10. Index **maintenance** runs as background work, and background work needs slots assigned to it. The check fires *before* validation, so neither statement can even be dry-run: `--dry_run` returns the same reservation error rather than `Query successfully validated`, even when the named index does not exist. Creating an index is not gated — only altering one. Running these needs an Enterprise-edition reservation with a `BACKGROUND` job-type assignment; an autoscale reservation with baseline 0 bills only while the alteration runs.

```sql
-- Both require a BACKGROUND reservation; not run here
ALTER SEARCH INDEX ai_search_kb_index
ON `PROJECT_ID.DATASET.some_large_table`
SET OPTIONS (analyzer = 'NO_OP_ANALYZER');

ALTER SEARCH INDEX ai_search_kb_index
ON `PROJECT_ID.DATASET.some_large_table`
ADD COLUMN sku;
```

Reading what an index covers is not gated at all — the cell below runs cleanly with no reservation, and returns zero rows here because this dataset carries no search index.

```python
# Inspecting search indexes needs no reservation. Zero rows is the expected
# result in this dataset — nothing here clears the 10 GiB threshold.
indexes = f'''
SELECT index_name, table_name, index_status, coverage_percentage,
       analyzer, disable_reason, last_refresh_time
FROM `{PROJECT_ID}.{DATASET_ID}.INFORMATION_SCHEMA.SEARCH_INDEXES`
'''
df = client.query(indexes).to_dataframe()
print(f'search indexes in {DATASET_ID}: {len(df)}')
display(df)

columns = f'''
SELECT index_name, table_name, index_column_name, index_field_path
FROM `{PROJECT_ID}.{DATASET_ID}.INFORMATION_SCHEMA.SEARCH_INDEX_COLUMNS`
'''
display(client.query(columns).to_dataframe())
```

---
## Examples — `%%bigquery` Magics

The same examples using IPython magic commands. Magics let you write SQL directly in notebook cells without Python string wrapping.

Key patterns:
- `%%bigquery` — run SQL, display results inline
- `%%bigquery df` — run SQL, capture results into a pandas DataFrame

### Semantic search with `%%bigquery`

```sql
%%bigquery --project {PROJECT_ID}

SELECT base.title, base.content, distance
FROM AI.SEARCH(
  TABLE `statmike-mlops-349915.bq_ai_functions.ai_search_knowledge_base`,
  'content',
  'container orchestration',
  top_k => 3
)
```

---
## Examples — BigFrames

`AI.SEARCH` has no direct BigFrames equivalent. Use `session.read_gbq_query()` to execute AI.SEARCH SQL from BigFrames.

```python
import bigframes.pandas as bpd

bpd.options.bigquery.project = PROJECT_ID
bpd.options.bigquery.location = LOCATION
```

### Running AI.SEARCH via read_gbq_query

```python
query = f"""
SELECT base.title, base.content, distance
FROM AI.SEARCH(
  TABLE `{PROJECT_ID}.{DATASET_ID}.ai_search_knowledge_base`,
  'content',
  'serverless compute',
  top_k => 3
)
"""
df = bpd.read_gbq_query(query)
df.to_pandas()
```
