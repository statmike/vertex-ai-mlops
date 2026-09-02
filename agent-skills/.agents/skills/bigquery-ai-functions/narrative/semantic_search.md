# Semantic Search System — BigQuery AI Functions

Build a semantic search system in BigQuery, comparing three approaches:

1. **Manual approach**: `AI.EMBED` to create embeddings + `VECTOR_SEARCH` to query them
2. **Simplified approach**: `AI.SEARCH` with autonomous embedding generation
3. **Hybrid approach**: semantic + lexical keyword matching in one call

**What this demonstrates:**
- Creating and storing embeddings with `AI.EMBED`
- Searching with `VECTOR_SEARCH` (single query, batch, filtered)
- Setting up autonomous embeddings for `AI.SEARCH`
- Adding a keyword leg with `VECTOR_SEARCH` lexical columns and `AI.SEARCH` `mode => 'HYBRID'`
- Comparing the three approaches: flexibility vs simplicity vs exact-term recall

**Functions used:** `functions/ai_embed` (`AI.EMBED`) | `functions/vector_search` (`VECTOR_SEARCH`) (semantic + hybrid) | `functions/ai_search` (`AI.SEARCH`) (semantic + hybrid)

**Prerequisites:** `setup` (Setup guide) | `RESOURCES.md` (Function reference)

---
## Setup

Set your project and location, authenticate, and create shared resources.

> `AI.EMBED` and `VECTOR_SEARCH` use end-user credentials — no connection needed. `AI.SEARCH` requires a connection for autonomous embedding generation. See the `setup` (Setup Reference) for details.

```python
PROJECT_ID = 'statmike-mlops-349915'  # <-- Replace with your project ID
LOCATION = 'US'  # BigQuery dataset location
DATASET_ID = 'bq_ai_functions'  # Shared dataset across all notebooks
CONNECTION_ID = 'bq_ai_functions'  # Shared connection (needed for AI.SEARCH)
```

### Environment

> **Already set up the project environment?** The cell below is a no-op — packages are already in your kernel. See the `setup` (Setup Reference) for details.
>
> **Running standalone** (Colab, Colab Enterprise, Vertex AI Workbench)? The cell below installs required packages into your current kernel.

```python
from google.cloud import bigquery
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
## Step 1 — Create a knowledge base

Create a sample knowledge base of technical documentation articles. We'll use this same data for all three search approaches.

```python
# Source data — technical documentation articles
articles_query = f'''
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.workflow_search_articles` AS
SELECT * FROM UNNEST([
  STRUCT(1 AS id, 'BigQuery' AS product, 'Querying Data' AS title,
    'BigQuery supports standard SQL for querying data. Use SELECT statements to retrieve data from tables. BigQuery processes queries using a distributed architecture that can scan terabytes in seconds.' AS content),
  STRUCT(2, 'BigQuery', 'Loading Data',
    'Load data into BigQuery from Cloud Storage, local files, or streaming inserts. Supported formats include CSV, JSON, Avro, Parquet, and ORC. Use batch loading for large datasets and streaming for real-time data.'),
  STRUCT(3, 'BigQuery', 'Access Control',
    'BigQuery uses IAM for access control. Grant roles at the project, dataset, or table level. Key roles include BigQuery Data Viewer, Data Editor, and Admin. Use authorized views for row-level security.'),
  STRUCT(4, 'Cloud Storage', 'Creating Buckets',
    'Create Cloud Storage buckets to store objects. Choose a storage class based on access frequency: Standard for hot data, Nearline for monthly, Coldline for quarterly, and Archive for yearly access.'),
  STRUCT(5, 'Cloud Storage', 'Object Lifecycle',
    'Configure lifecycle rules to automatically manage objects. Rules can delete objects after a specified age, transition to cheaper storage classes, or abort incomplete multipart uploads.'),
  STRUCT(6, 'Cloud Functions', 'Writing Functions',
    'Cloud Functions lets you write single-purpose functions that respond to events. Supported runtimes include Python, Node.js, Go, Java, and .NET. Functions automatically scale based on incoming request volume.'),
  STRUCT(7, 'Cloud Functions', 'Triggers',
    'Functions can be triggered by HTTP requests, Pub/Sub messages, Cloud Storage events, Firestore changes, or scheduled by Cloud Scheduler. Each trigger type provides different event data to your function.'),
  STRUCT(8, 'Cloud Run', 'Deploying Services',
    'Deploy containerized applications to Cloud Run. Build your container image, push to Artifact Registry, and deploy. Cloud Run automatically scales from zero to handle traffic and scales back down when idle.'),
  STRUCT(9, 'Cloud Run', 'Custom Domains',
    'Map custom domains to Cloud Run services. Verify domain ownership, create a DNS mapping, and update your DNS records. Cloud Run automatically provisions and renews TLS certificates.'),
  STRUCT(10, 'Pub/Sub', 'Publishing Messages',
    'Publish messages to Pub/Sub topics for asynchronous communication. Messages can be up to 10MB. Use batch publishing for higher throughput. Messages are stored for up to 31 days until acknowledged.')
])
'''
client.query(articles_query).result()

articles = client.query(
    f'SELECT id, product, title FROM `{PROJECT_ID}.{DATASET_ID}.workflow_search_articles` ORDER BY id'
).to_dataframe()
print(f'{len(articles)} articles created')
articles
```

---
## Approach 1: Manual — AI.EMBED + VECTOR_SEARCH

The manual approach gives you full control: you choose the embedding model, task type, distance metric, and can pre-filter the search space.

### Step 2a — Embed the knowledge base

Create embeddings for all articles using `AI.EMBED` with `RETRIEVAL_DOCUMENT` task type (the document side of asymmetric retrieval).

```python
query = f'''
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.workflow_search_embedded` AS
SELECT
  id, product, title, content,
  (AI.EMBED(
    content => content,
    endpoint => 'text-embedding-005',
    task_type => 'RETRIEVAL_DOCUMENT'
  )).result AS embedding
FROM `{PROJECT_ID}.{DATASET_ID}.workflow_search_articles`
'''
client.query(query).result()

# Verify embeddings
verify = client.query(f'''
  SELECT id, title, ARRAY_LENGTH(embedding) AS dims
  FROM `{PROJECT_ID}.{DATASET_ID}.workflow_search_embedded`
  ORDER BY id
''').to_dataframe()
print(f'All {len(verify)} articles embedded ({verify.iloc[0]["dims"]} dimensions)')
verify
```

### Step 3a — Search with VECTOR_SEARCH

Search the embedded knowledge base. Note the asymmetric pattern: queries use `RETRIEVAL_QUERY` task type to match the `RETRIEVAL_DOCUMENT` embeddings.

```python
# Single query search
query = f'''
SELECT base.product, base.title, base.content, distance
FROM VECTOR_SEARCH(
  TABLE `{PROJECT_ID}.{DATASET_ID}.workflow_search_embedded`,
  'embedding',
  query_value => (AI.EMBED(
    content => 'How do I load CSV files into a data warehouse?',
    endpoint => 'text-embedding-005',
    task_type => 'RETRIEVAL_QUERY'
  )).result,
  top_k => 3,
  distance_type => 'COSINE'
)
'''
client.query(query).to_dataframe()
```

### Step 4a — Filtered search

One advantage of the manual approach: you can pre-filter the search space. Here we restrict search to only BigQuery articles.

```python
query = f'''
SELECT base.product, base.title, base.content, distance
FROM VECTOR_SEARCH(
  (SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.workflow_search_embedded` WHERE product = 'BigQuery'),
  'embedding',
  query_value => (AI.EMBED(
    content => 'security and permissions',
    endpoint => 'text-embedding-005',
    task_type => 'RETRIEVAL_QUERY'
  )).result,
  top_k => 3,
  distance_type => 'COSINE'
)
'''
client.query(query).to_dataframe()
```

### Step 5a — Batch search

Search for multiple queries at once — efficient for processing many questions in a single pass.

```python
query = f'''
SELECT
  query.question,
  base.product,
  base.title,
  distance
FROM VECTOR_SEARCH(
  TABLE `{PROJECT_ID}.{DATASET_ID}.workflow_search_embedded`,
  'embedding',
  (SELECT
     question,
     (AI.EMBED(content => question, endpoint => 'text-embedding-005',
               task_type => 'RETRIEVAL_QUERY')).result AS embedding
   FROM UNNEST([
     'How do I set up event-driven processing?',
     'What are the storage tiers available?',
     'How do I deploy a container?'
   ]) AS question),
  top_k => 2,
  distance_type => 'COSINE'
)
ORDER BY question, distance
'''
client.query(query).to_dataframe()
```

---
## Approach 2: Simplified — AI.SEARCH

`AI.SEARCH` handles embedding generation automatically. You create a table with a `GENERATED ALWAYS AS` column that uses `AI.EMBED`, and BigQuery generates embeddings in the background.

### Step 2b — Create table with autonomous embeddings

The key syntax: define an embedding column as `GENERATED ALWAYS AS (AI.EMBED(...)) STORED OPTIONS (asynchronous = TRUE)`. BigQuery populates embeddings automatically after data is inserted.

```python
# Create table with autonomous embedding column
query = f'''
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.workflow_search_auto` (
  id INT64,
  product STRING,
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

# Insert the same articles
query = f'''
INSERT INTO `{PROJECT_ID}.{DATASET_ID}.workflow_search_auto` (id, product, title, content)
SELECT id, product, title, content
FROM `{PROJECT_ID}.{DATASET_ID}.workflow_search_articles`
'''
client.query(query).result()
print('Data inserted — embeddings generating in background...')

# Wait for embeddings to be ready
# Successful embeddings have status = '' (empty string) and a non-null embedding
for i in range(30):
    result = client.query(f'''
        SELECT
          COUNT(*) AS total,
          COUNTIF(content_embedding IS NOT NULL AND content_embedding.status = '') AS ready
        FROM `{PROJECT_ID}.{DATASET_ID}.workflow_search_auto`
    ''').to_dataframe()
    total = int(result.iloc[0]['total'])
    ready = int(result.iloc[0]['ready'])
    if ready == total:
        print(f'All {total} embeddings ready!')
        break
    print(f'  Waiting... {ready}/{total} embeddings ready')
    time.sleep(10)
else:
    print(f'Warning: only {ready}/{total} embeddings ready after 5 minutes')
```

### Step 3b — Search with AI.SEARCH

`AI.SEARCH` is much simpler — just pass the table, column, and search text. No manual embedding of queries, no distance type selection.

It picks the distance metric too: the default is `EUCLIDEAN`, where Step 3a asked for `COSINE`. The same question therefore comes back on a different scale here. Approach 3 adds a third scale — a fused rank score that is not a distance at all. Compare *ranks* across the three approaches; never compare the `distance` values.

```python
query = f'''
SELECT base.product, base.title, base.content, distance
FROM AI.SEARCH(
  TABLE `{PROJECT_ID}.{DATASET_ID}.workflow_search_auto`,
  'content',
  'How do I load CSV files into a data warehouse?',
  top_k => 3
)
'''
client.query(query).to_dataframe()
```

---
## Approach 3: Hybrid — semantic + lexical

Semantic search matches meaning, which is what you want right up until the answer hinges on a term the question never spells out — a product name, an error code, a SKU. Embeddings blur those tokens into their neighborhood. Lexical (keyword) search matches them literally.

Hybrid search runs both legs and fuses the two rankings into one result set. BigQuery exposes it two ways, and both run on the tables already built above:

- `VECTOR_SEARCH` with `lexical_search_columns` + `lexical_search_query_value` — any table with an embedding column (Approach 1's table)
- `AI.SEARCH` with `mode => 'HYBRID'` — tables with autonomous embedding generation (Approach 2's table)

Neither one needs a vector index here. An index only accelerates the lexical leg, and BigQuery does not populate one until the base table reaches 5,000 rows and 10 MB, so this 10-row knowledge base never gets one.

### Step 2c — VECTOR_SEARCH with lexical columns

The question below is phrased entirely in storage vocabulary: a nightly job that moves files between tiers. The operator running it already knows the exact term the answer turns on — `Cloud Scheduler` — but that term appears in exactly one article, and that article files under Cloud Functions rather than Cloud Storage. This is the shape hybrid exists for: fuzzy intent on one leg, an exact token on the other.

Start with the semantic-only ranking. Ranking all ten articles, instead of only the top 3 a user would be shown, makes it visible where the exact-term article actually sits before any fusion happens.

```python
# Semantic-only baseline — rank every article, then take the top 3 a user would see
TOP_K = 3

query = f'''
SELECT
  ROW_NUMBER() OVER (ORDER BY distance) AS semantic_rank,
  base.id, base.product, base.title,
  CONTAINS_SUBSTR(base.content, 'Cloud Scheduler') AS names_the_term,
  distance
FROM VECTOR_SEARCH(
  TABLE `{PROJECT_ID}.{DATASET_ID}.workflow_search_embedded`,
  'embedding',
  query_value => (AI.EMBED(
    content => 'How do I schedule a nightly job that moves files between storage tiers?',
    endpoint => 'text-embedding-005',
    task_type => 'RETRIEVAL_QUERY'
  )).result,
  top_k => 10,
  distance_type => 'COSINE'
)
ORDER BY distance
'''
semantic_all = client.query(query).to_dataframe()
semantic_top = semantic_all.head(TOP_K)

term_rank = semantic_all.loc[semantic_all['names_the_term'], 'semantic_rank']
print(f'Semantic-only top {TOP_K}: {[int(i) for i in semantic_top["id"]]}')
print('Semantic rank of the article naming "Cloud Scheduler": '
      f'{int(term_rank.iloc[0]) if len(term_rank) else "not returned"}')
semantic_all
```

```python
# Hybrid — same semantic question, plus a literal keyword leg carrying the exact term
query = f'''
SELECT
  base.id, base.product, base.title,
  CONTAINS_SUBSTR(base.content, 'Cloud Scheduler') AS names_the_term,
  distance
FROM VECTOR_SEARCH(
  TABLE `{PROJECT_ID}.{DATASET_ID}.workflow_search_embedded`,
  'embedding',
  query_value => (AI.EMBED(
    content => 'How do I schedule a nightly job that moves files between storage tiers?',
    endpoint => 'text-embedding-005',
    task_type => 'RETRIEVAL_QUERY'
  )).result,
  lexical_search_columns => ['title', 'content'],
  lexical_search_query_value => 'Cloud Scheduler',
  top_k => {TOP_K},
  distance_type => 'COSINE'
)
ORDER BY distance
'''
hybrid = client.query(query).to_dataframe()

semantic_ids = [int(i) for i in semantic_top['id']]
hybrid_ids = [int(i) for i in hybrid['id']]
rank_of = {int(i): int(r) for i, r in zip(semantic_all['id'], semantic_all['semantic_rank'])}
added = [i for i in hybrid_ids if i not in semantic_ids]
dropped = [i for i in semantic_ids if i not in hybrid_ids]

print(f'Semantic-only top {TOP_K}: {semantic_ids}')
print(f'Hybrid top {TOP_K}:        {hybrid_ids}')
print('Article ids the lexical leg added: '
      f'{[f"id {i} (semantic rank {rank_of[i]})" for i in added] if added else "none"}')
print(f'Article ids pushed out to make room: {dropped if dropped else "none"}')
hybrid
```

`lexical_search_columns` lists the `STRING` columns to match literally and `lexical_search_query_value` is the text to match them against. The two legs take **separate** inputs: the semantic leg gets the user's question, the lexical leg gets the exact term worth pinning.

The cell above prints what that bought — the ids each ranking returned, any id the lexical leg pulled into the top 3, the semantic rank that id held beforehand, and whatever was pushed out to make room. The fused list is the same length as the semantic one, so every promotion is a swap, not an append. How far down the semantic list a lexical match can reach is set by `top_k`, and the bound is arithmetic rather than luck: *Reading the hybrid `distance`* below works it out.

Two constraints to know before reaching for it:

- Hybrid is **single-query only**. The lexical arguments cannot be combined with the batch (query-table) form from Step 5a — BigQuery rejects it with `lexical_search_columns is not supported when query_value is not specified.`
- The `distance` column is no longer a cosine distance, even though `distance_type => 'COSINE'` is still accepted. See *Reading the hybrid `distance`* below.

### Step 3c — AI.SEARCH with mode => 'HYBRID'

`AI.SEARCH` has no lexical column arguments at all. It has a single `mode`:

- `'VECTOR'` — semantic only
- `'HYBRID'` — semantic + lexical
- `'AUTO'` (default) — hybrid *if the table has a vector index configured with lexical search columns*, otherwise semantic only

Step 3b omitted `mode`, so it ran as `AUTO` and resolved to a semantic-only search — and on this table it always will. `AI.SEARCH` requires autonomous embedding generation, and Step 2b's `content_embedding` is a generated `STRUCT<result ARRAY<FLOAT64>, status STRING>` column. A vector index cannot be built on a generated `STRUCT` column, or on a field of one, so `workflow_search_auto` can never carry the index `AUTO` looks for. On an autonomous-embedding table, `'HYBRID'` has to be asked for by name. An *indexed* hybrid search means projecting `content_embedding.result` into a second table as a plain `ARRAY<FLOAT64>` column and querying that with `VECTOR_SEARCH` — the `workflows/catalog_search` (Catalog Search) workflow builds that two-table design end to end.

The price of the simplicity: one string feeds both legs, so the query text has to carry the intent *and* the keyword. And the lexical leg matches only `column_to_search` — `'content'` here, the same column the embedding is generated from. When the keyword belongs to a *different* column, that is `VECTOR_SEARCH`'s job.

The cell below runs one identical string through `'VECTOR'` and `'HYBRID'` so the fusion effect is measured against its own baseline rather than against a differently-worded query.

```python
# One query text, both modes — the only difference is the fusion
query = f'''
WITH both_modes AS (
  SELECT
    'VECTOR' AS search_mode, base.id, base.title,
    CONTAINS_SUBSTR(base.content, 'Cloud Scheduler') AS names_the_term, distance
  FROM AI.SEARCH(
    TABLE `{PROJECT_ID}.{DATASET_ID}.workflow_search_auto`,
    'content',
    'nightly job to move files between storage tiers using Cloud Scheduler',
    top_k => {TOP_K},
    mode => 'VECTOR'
  )
  UNION ALL
  SELECT
    'HYBRID', base.id, base.title,
    CONTAINS_SUBSTR(base.content, 'Cloud Scheduler'), distance
  FROM AI.SEARCH(
    TABLE `{PROJECT_ID}.{DATASET_ID}.workflow_search_auto`,
    'content',
    'nightly job to move files between storage tiers using Cloud Scheduler',
    top_k => {TOP_K},
    mode => 'HYBRID'
  )
)
SELECT
  search_mode,
  RANK() OVER (PARTITION BY search_mode ORDER BY distance) AS result_rank,
  id, title, names_the_term, distance
FROM both_modes
ORDER BY search_mode DESC, distance
'''
modes = client.query(query).to_dataframe()

for mode in ['VECTOR', 'HYBRID']:
    leg = modes[modes['search_mode'] == mode]
    hit = leg[leg['names_the_term']]
    where = f'rank {int(hit["result_rank"].iloc[0])}' if len(hit) else f'not in the top {TOP_K}'
    print(f'{mode:6} top {TOP_K}: {[int(i) for i in leg["id"]]}   '
          f'article naming "Cloud Scheduler": {where}')
modes
```

### Reading the hybrid `distance`

Both hybrid calls return a `distance` column, and in neither case is it a distance. Hybrid fuses the two legs by **rank**, not by score, using reciprocal rank fusion with 1-based ranks. The two legs do not count from the same base:

```
distance = 1 - ( 1/(60 + rank_vector) + 1/(61 + rank_lexical) )
```

The semantic leg uses 60, the standard fusion constant; the lexical leg uses 61. That asymmetry is measured, not cosmetic. A row sitting at semantic rank 1 and lexical rank 2 comes back as `1 - (1/61 + 1/63) = 0.9677335415040333`, and that value lands *between* the two readings a shared base would give for the same pair of ranks — 60 on both legs predicts `1 - (1/61 + 1/62) = 0.9674775251189847`, 61 on both legs predicts `1 - (1/62 + 1/63) = 0.9679979518689196`. Falling between them is the signature of two different bases.

Lower still sorts first. Three consequences follow directly from the arithmetic:

- **Values cluster just below 1** — the fused results above sit within a few thousandths of `0.97`. A document that matches the query perfectly does *not* score 0; the best score available, rank 1 on both legs, is `1 - (1/61 + 1/62) = 0.96748`. That is the same expression the shared-base-60 reading produces at ranks 1 and 2 above, which is arithmetic coincidence and not shared meaning: here it is the measured law evaluated at the best ranks a row can hold.
- **The numbers are not comparable to Approach 1's `COSINE` distances or Approach 2's `EUCLIDEAN` ones.** Different scale, different meaning. Compare *ranks* across approaches, never the values.
- **Every pooled row collects both terms.** BigQuery hands the lexical leg only the top `10 * top_k` rows by semantic rank, and inside that candidate pool it ranks *all* of them, not just the rows BM25 matched: the matches take lexical ranks `1..m` and every remaining candidate falls in behind them in its semantic order. No pooled row is ever missing from a list, so no pooled row ever forfeits a term — an article that never mentions `Cloud Scheduler` still earns a lexical rank, namely its semantic rank pushed down one place for each matching article ranked below it. Only where nothing matches at all does that reduce to `1 - ( 1/(60 + r) + 1/(61 + r) )` at semantic rank `r`. A row deeper than `10 * top_k` never enters the pool and gets no lexical rank at all.

What the keyword actually buys, then, is a promotion to lexical rank 1, worth `1/62 ≈ 0.0161`. That is real money on this scale, and it does pull rows in from outside the semantic top `top_k` — but only so deep, and `top_k` bounds the depth twice over. A matched row has to be inside the `10 * top_k` candidate pool, *and* its fused score has to beat the row holding the last slot. The reach is whichever bound is tighter:

| `top_k` | 2 | 3 | 5 | 10 | 20 | 30 | 40 | 50 | 51 | 64 | 100 | 208 | 300 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| deepest semantic rank retrievable | 3 | 6 | 10 | 23 | 56 | 110 | 212 | 468 | 510 | 640 | 1,000 | 2,080 | 3,000 |

The score half of that is one comparison. A matched row at semantic rank `R` scores `1/(60 + R) + 1/62`. To make the page it has to beat the row holding the last slot, which keeps its semantic rank `top_k` and — pushed down one place by the match — takes lexical rank `top_k + 1`, scoring `1/(60 + top_k) + 1/(61 + top_k + 1)`. That comparison relaxes fast, and from `top_k = 51` up it stops binding at all: the pool is the tighter of the two from there on, and reach is exactly `10 * top_k`.

This notebook runs at `top_k = 3`, a reach of 6, which is why the comparison above shows a promotion of a few positions rather than a rescue from the bottom of a ten-article list. That is the rule to carry away: hybrid does widen recall, but in proportion to `top_k` rather than without limit — to reach an exact-token match sitting at semantic rank `R`, `top_k` has to be at least `R / 10`, and usually more. That ratio is the pool bound alone; below a few hundred ranks deep the score bound is the tighter of the two, so read the requirement off the reach table above rather than from the ratio — a target at semantic rank 100 needs `top_k = 29`, not 10. The two gates cross at `top_k = 51`, and only above that does `R / 10` become the answer rather than the floor. And when the term *is* the whole question and you want certainty rather than arithmetic, filter on it — a `WHERE CONTAINS_SUBSTR(content, @term)` predicate cannot be outranked by a fusion score, and it has no pool to fall outside of.

This formula is reverse-engineered from observed results and reproduces them exactly, but Google documents no fusion formula and no score column, so it can change without notice. Treat a hybrid `distance` as an opaque ordering in production code. The full decomposition, with the underlying ranks solved out of live results, is in `functions/vector_search` (`VECTOR_SEARCH`).

---
## Comparison: Manual vs Simplified vs Hybrid

| Feature | Manual (EMBED + VECTOR_SEARCH) | Simplified (AI.SEARCH) | Hybrid (semantic + lexical) |
|---------|-------------------------------|------------------------|-----------------------------|
| **Setup** | Create embeddings yourself | Autonomous — BigQuery handles it | None — runs on either table as-is |
| **Query embedding** | You call AI.EMBED on queries | Automatic | Follows the function it runs on |
| **Task types** | Full control (RETRIEVAL_DOCUMENT / RETRIEVAL_QUERY) | Managed by BigQuery | Follows the function it runs on |
| **Distance metrics** | Choose COSINE, EUCLIDEAN, DOT_PRODUCT | Choose COSINE, EUCLIDEAN, DOT_PRODUCT (EUCLIDEAN default) | Accepted, but `distance` comes back as a fused rank score |
| **Keyword input** | None — semantic only | None — semantic only until `mode => 'HYBRID'` is named | `VECTOR_SEARCH`: a separate `lexical_search_query_value` over chosen `lexical_search_columns`. `AI.SEARCH`: the one query string, matched only against `column_to_search` |
| **Filtering** | Pre-filter base table with subquery | Pre-filter with a base table query | Pre-filter works on both |
| **Batch queries** | Multiple queries in one call | One query at a time | Not supported — single query only |
| **Vector indexes** | Supports IVF and TreeAH indexes | Impossible — the generated `STRUCT` embedding column cannot be an index key | Optional accelerator for the lexical leg; `AUTO` needs an index with `lexical_search_columns`, so `AI.SEARCH` must name `'HYBRID'` |
| **Best for** | Production systems needing control | Quick prototyping, simple search | Exact terms — product names, error codes, SKUs — reachable at most `10 * top_k` deep in the semantic ranking, so `top_k` >= `R / 10` is a floor for a target at rank `R`, not a recipe: below `top_k` = 51 the scoring gate binds first and needs more |
