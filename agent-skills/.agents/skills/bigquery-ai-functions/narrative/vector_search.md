# VECTOR_SEARCH — BigQuery AI Functions

`VECTOR_SEARCH` is a table-valued function that finds the top-K nearest neighbors from a base table using pre-computed embeddings. Supports vector indexes for efficient approximate nearest neighbor (ANN) search.

**Status:** `VECTOR_SEARCH` is **GA**. The single-search syntax (`query_value =>`) is **Preview**, and it is also the hybrid search syntax — `lexical_search_columns` is only accepted alongside `query_value` (verified 2026-09-01). Batch search with a query table is the GA form.

**When to use it:**
- You need semantic search over a table with pre-computed embeddings
- You want top-K nearest neighbor search at scale
- You need batch search (multiple queries at once)
- You need hybrid search — semantic similarity fused with exact keyword matching
- You want to build a RAG (Retrieval Augmented Generation) pipeline

**Vector indexes:** By default, `VECTOR_SEARCH` uses brute-force KNN (exact nearest neighbor), which scans every row. For large tables, BigQuery supports vector indexes that enable approximate nearest neighbor (ANN) search for dramatically faster queries:

| Index Type | Best For | How It Works |
|------------|----------|--------------|
| `IVF` (Inverted File) | General-purpose ANN | Partitions vectors into clusters; searches only the nearest clusters |
| `TreeAH` (Tree Asymmetric Hashing) | Large-scale, high-throughput | Uses a tree structure with asymmetric hashing for efficient search |

Create a vector index with `CREATE VECTOR INDEX` — no changes to your `VECTOR_SEARCH` queries are needed. Adding `lexical_search_columns` (with those same columns repeated in a `STORING` clause) extends the index to accelerate the keyword half of a hybrid search. See the [Vector Index documentation](https://cloud.google.com/bigquery/docs/vector-index) for details.

**Alternatives:**
- `functions/ai_search` (`AI.SEARCH`) — Simplified semantic search with autonomous embedding generation
- `functions/ai_similarity` (`AI.SIMILARITY`) — Cosine similarity between two specific inputs
- `functions/ai_embed` (`AI.EMBED`) — Create embeddings for individual values

**Featured in:** `workflows/semantic_search` (Semantic Search System) | `workflows/rag_pipeline` (RAG Pipeline) | `workflows/document_rag` (Document RAG Pipeline) | `workflows/catalog_search` (Catalog Search) | `workflows/log_analysis` (Log Analysis) | `workflows/image_deduplication` (Image Deduplication)

**References:** `RESOURCES.md` (Full syntax reference) | [Official documentation](https://cloud.google.com/bigquery/docs/reference/standard-sql/search_functions#vector_search) | `setup` (Setup guide)

---
## Setup

Set your project and location, authenticate, and create a temporary dataset for this notebook.

> This function doesn't require a connection or model — it uses end-user credentials automatically. See the `setup` (Setup Reference) for details.

```python
PROJECT_ID = 'statmike-mlops-349915'  # <-- Replace with your project ID
LOCATION = 'US'  # BigQuery dataset location
DATASET_ID = 'bq_ai_functions'  # Shared dataset across all notebooks
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
## Examples — SQL

Progressive examples from simplest to most advanced. Each cell adds one new concept.

### Setup: Create sample data with embeddings

First, create a table with pre-computed embeddings to search against.

**Note on task_type:** This example uses the **asymmetric** embedding pattern — documents are embedded with `RETRIEVAL_DOCUMENT` (below), while search queries use `RETRIEVAL_QUERY` (in later examples). This is the recommended pattern for retrieval use cases. See the `functions/ai_embed` (`AI.EMBED`) notebook for the full list of task types.

```python
# Create a sample knowledge base with embeddings
query = f'''
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.vector_search_products` AS
SELECT id, product, category, description,
  (AI.EMBED(content => description, endpoint => 'text-embedding-005', task_type => 'RETRIEVAL_DOCUMENT')).result AS embedding
FROM UNNEST([
  STRUCT(1 AS id, 'Laptop' AS product, 'Computing' AS category, 'High-performance laptop with 16GB RAM and SSD storage for data science and programming.' AS description),
  STRUCT(2, 'Headphones', 'Audio', 'Wireless noise-cancelling headphones with 30-hour battery life and premium sound.'),
  STRUCT(3, 'Standing Desk', 'Furniture', 'Electric height-adjustable standing desk with memory presets and cable management.'),
  STRUCT(4, 'Monitor', 'Computing', '32-inch 4K monitor with USB-C connectivity and built-in KVM switch.'),
  STRUCT(5, 'Keyboard', 'Peripherals', 'Mechanical keyboard with programmable keys and RGB backlighting.'),
  STRUCT(6, 'Mouse', 'Peripherals', 'Ergonomic vertical mouse designed to reduce wrist strain.'),
  STRUCT(7, 'Webcam', 'Audio', '4K webcam with auto-framing and noise-cancelling microphone.'),
  STRUCT(8, 'Dock', 'Computing', 'Thunderbolt 4 docking station with dual 4K display support.')
])
'''
client.query(query).result()
print('Sample data created')
```

### 1. Single search (Preview)

Search for the nearest neighbors to a single query value. Use `query_value` for single searches.

```python
query = f'''
SELECT base.product, base.description, distance
FROM VECTOR_SEARCH(
  TABLE `{PROJECT_ID}.{DATASET_ID}.vector_search_products`,
  'embedding',
  query_value => (AI.EMBED(content => 'comfortable work setup for long hours',
                           endpoint => 'text-embedding-005',
                           task_type => 'RETRIEVAL_QUERY')).result,
  top_k => 3,
  distance_type => 'COSINE'
)
'''
client.query(query).to_dataframe()
```

### 2. Batch search

Search for multiple queries at once. Results include `query` and `base` STRUCTs plus `distance`.

**Batch and hybrid are mutually exclusive.** The keyword arguments shown in example 6 are only accepted alongside `query_value`, so a batch call can never be hybrid. The second cell below runs the combination and prints the error BigQuery returns.

```python
query = f'''
SELECT
  query.search_term,
  base.product,
  base.description,
  distance
FROM VECTOR_SEARCH(
  TABLE `{PROJECT_ID}.{DATASET_ID}.vector_search_products`,
  'embedding',
  (SELECT
     search_term,
     (AI.EMBED(content => search_term, endpoint => 'text-embedding-005',
               task_type => 'RETRIEVAL_QUERY')).result AS embedding
   FROM UNNEST(['audio equipment', 'computer display']) AS search_term),
  top_k => 2,
  distance_type => 'COSINE'
)
'''
client.query(query).to_dataframe()
```

```python
# Batch + hybrid: add the lexical arguments to the batch call above and it is rejected
batch_hybrid = f'''
SELECT query.search_term, base.product, distance
FROM VECTOR_SEARCH(
  TABLE `{PROJECT_ID}.{DATASET_ID}.vector_search_products`,
  'embedding',
  (SELECT
     search_term,
     (AI.EMBED(content => search_term, endpoint => 'text-embedding-005',
               task_type => 'RETRIEVAL_QUERY')).result AS embedding
   FROM UNNEST(['audio equipment', 'computer display']) AS search_term),
  lexical_search_columns => ['product', 'description'],
  lexical_search_query_value => 'noise-cancelling',
  top_k => 2,
  distance_type => 'COSINE'
)
'''

try:
    client.query(batch_hybrid).result()
    print('Batch + hybrid succeeded — the restriction has changed')
except Exception as e:
    print('Batch + hybrid ->', str(e).splitlines()[0])
```

### 3. Using EUCLIDEAN distance

Change the distance metric. Options: `COSINE`, `EUCLIDEAN` (default), `DOT_PRODUCT`.

```python
query = f'''
SELECT base.product, base.description, distance
FROM VECTOR_SEARCH(
  TABLE `{PROJECT_ID}.{DATASET_ID}.vector_search_products`,
  'embedding',
  query_value => (AI.EMBED(content => 'typing device', endpoint => 'text-embedding-005',
                           task_type => 'RETRIEVAL_QUERY')).result,
  top_k => 3,
  distance_type => 'EUCLIDEAN'
)
'''
client.query(query).to_dataframe()
```

### 4. Filtered search (pre-filtering)

Restrict the search to a subset of the base table by passing a subquery instead of `TABLE`. Only matching rows are considered for nearest neighbor search — useful for scoping results by category, region, status, etc.

```python
query = f'''
SELECT base.product, base.category, base.description, distance
FROM VECTOR_SEARCH(
  (SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.vector_search_products` WHERE category = 'Computing'),
  'embedding',
  query_value => (AI.EMBED(content => 'display for programming',
                           endpoint => 'text-embedding-005',
                           task_type => 'RETRIEVAL_QUERY')).result,
  top_k => 3,
  distance_type => 'COSINE'
)
'''
client.query(query).to_dataframe()
```

### 5. RAG pattern — search then generate

Retrieve relevant context with VECTOR_SEARCH, then pass it to AI.GENERATE for grounded answers.

```python
query = f'''
WITH context AS (
  SELECT
    STRING_AGG(base.product || ': ' || base.description, '; ') AS retrieved_docs
  FROM VECTOR_SEARCH(
    TABLE `{PROJECT_ID}.{DATASET_ID}.vector_search_products`,
    'embedding',
    query_value => (AI.EMBED(content => 'ergonomic office equipment',
                             endpoint => 'text-embedding-005',
                             task_type => 'RETRIEVAL_QUERY')).result,
    top_k => 3,
    distance_type => 'COSINE'
  )
)
SELECT (AI.GENERATE(
  CONCAT(
    'Based on these products: ', c.retrieved_docs,
    ' --- Recommend the best products for someone setting up an ergonomic home office. Explain why.'
  )
)).result AS recommendation
FROM context c
'''
df = client.query(query).to_dataframe()
print(df.iloc[0]['recommendation'])
```

### 6. Hybrid search (Preview) — semantic plus keyword

A hybrid search fuses the semantic result list with a lexical (keyword) result list. Two arguments turn it on:

- `lexical_search_columns` — an `ARRAY<STRING>` naming `STRING` columns in the base table. A **non-empty list is what makes the search hybrid**.
- `lexical_search_query_value` — the keyword text, matched against every column in that list. Required whenever `lexical_search_columns` is set.

Hybrid requires the **single-query syntax** (`query_value =>`) and cannot batch. The two legs are independent: the lexical columns need not be the column the embeddings came from, and `lexical_search_query_value` need not match `query_value`. Below, the vector leg searches on intent while the lexical leg pins an exact product token.

No vector index is needed — this runs brute force on an 8-row table. An index only speeds up the lexical leg (example 9).

```python
query = f'''
SELECT base.product, base.category, base.description, distance
FROM VECTOR_SEARCH(
  TABLE `{PROJECT_ID}.{DATASET_ID}.vector_search_products`,
  'embedding',
  query_value => (AI.EMBED(content => 'connect two external displays to a laptop',
                           endpoint => 'text-embedding-005',
                           task_type => 'RETRIEVAL_QUERY')).result,
  lexical_search_columns => ['product', 'description'],
  lexical_search_query_value => 'Thunderbolt 4 docking station',
  top_k => 3,
  distance_type => 'COSINE'
)
'''
client.query(query).to_dataframe()
```

### Setup: a larger catalog with part numbers

Examples 7 and 8 need a corpus where the semantic leg can plausibly be wrong. This catalog holds 24 products — a dense cluster of display-connectivity items among them — plus a `sku` column carrying manufacturer part codes.

The embedding is generated from `description` only, so **the part code never enters the embedding**. That is the realistic shape of the problem: a buyer who knows an exact part number, searching a catalog whose vectors know only prose.

```python
# A 24-row catalog: descriptions are embedded, part codes are not
query = f'''
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.vector_search_catalog` AS
SELECT id, sku, product, description,
  (AI.EMBED(content => description, endpoint => 'text-embedding-005', task_type => 'RETRIEVAL_DOCUMENT')).result AS embedding
FROM UNNEST([
  STRUCT(1 AS id, 'TBT-8841' AS sku, 'Thunderbolt Dock' AS product, 'Thunderbolt 4 docking station with dual 4K display support and 90W laptop charging.' AS description),
  STRUCT(2, 'DCK-2210', 'USB-C Hub', 'Seven-port USB-C hub with HDMI output, card reader, and gigabit ethernet.'),
  STRUCT(3, 'MON-3240', 'Ultrawide Monitor', '32-inch 4K monitor with USB-C connectivity and a built-in KVM switch.'),
  STRUCT(4, 'MON-2711', 'Portable Monitor', '15-inch portable travel monitor powered over a single USB-C cable.'),
  STRUCT(5, 'CBL-4417', 'DisplayPort Cable', 'DisplayPort 2.1 cable rated for 8K at 60Hz, two meters, braided jacket.'),
  STRUCT(6, 'CBL-9032', 'HDMI Splitter', 'One-in two-out HDMI 2.1 splitter that mirrors a source to two screens.'),
  STRUCT(7, 'ADP-5567', 'Display Adapter', 'USB-C to dual HDMI adapter using DisplayLink for extended desktops on any laptop.'),
  STRUCT(8, 'KVM-7788', 'KVM Switch', 'Two-computer KVM switch sharing one keyboard, mouse, and monitor.'),
  STRUCT(9, 'LAP-1120', 'Developer Laptop', 'High-performance laptop with 32GB RAM and NVMe storage for data science.'),
  STRUCT(10, 'KBD-6310', 'Mechanical Keyboard', 'Mechanical keyboard with programmable keys and RGB backlighting.'),
  STRUCT(11, 'MSE-4402', 'Vertical Mouse', 'Ergonomic vertical mouse designed to reduce wrist strain.'),
  STRUCT(12, 'HDS-2077', 'Wireless Headset', 'Wireless noise-cancelling headset with 30-hour battery life.'),
  STRUCT(13, 'CAM-9911', 'Conference Camera', '4K conference camera with auto-framing and beamforming microphones.'),
  STRUCT(14, 'DSK-1450', 'Standing Desk', 'Electric height-adjustable standing desk with memory presets.'),
  STRUCT(15, 'CHR-3390', 'Task Chair', 'Mesh task chair with adjustable lumbar support and 4D armrests.'),
  STRUCT(16, 'ARM-8123', 'Monitor Arm', 'Gas-spring dual monitor arm clamping to desks up to 90mm thick.'),
  STRUCT(17, 'HUB-5540', 'Travel Hub', 'Slim aluminum travel hub with pass-through power, HDMI, and gigabit ethernet.'),
  STRUCT(18, 'PWR-7702', 'GaN Charger', '100W GaN wall charger with two USB-C ports and one USB-A port.'),
  STRUCT(19, 'SSD-6604', 'Portable SSD', 'Two-terabyte portable NVMe SSD in a rugged USB-C enclosure.'),
  STRUCT(20, 'NAS-3318', 'Desktop NAS', 'Four-bay desktop NAS with 2.5 gigabit ethernet and hardware transcoding.'),
  STRUCT(21, 'RTR-2205', 'Mesh Router', 'Tri-band mesh router covering 5,000 square feet with wired backhaul.'),
  STRUCT(22, 'SWT-1180', 'Network Switch', 'Eight-port managed network switch with power over ethernet.'),
  STRUCT(23, 'UPS-4406', 'Battery Backup', 'Line-interactive UPS with 1500VA capacity and pure sine wave output.'),
  STRUCT(24, 'PRN-8890', 'Label Printer', 'Thermal label printer for shipping labels, no ink required.')
])
'''
client.query(query).result()
print('Catalog created — 24 rows, embeddings from description only')
```

### 7. Semantic-only vs hybrid, head to head

Same query text, same `top_k`, run twice. The first call is pure semantic. The second adds `lexical_search_columns => ['sku']` and puts an exact part code in `lexical_search_query_value` — a token the vector leg cannot see, because `sku` was never embedded.

`top_k => 5` against 24 rows is the setting that makes the comparison meaningful. A `top_k` equal to the row count returns the whole table on both legs, so the two rankings can only be reordered, never differ in membership. Retrieval can only miss something when top-K is smaller than the corpus.

The cell prints the two set differences instead of claiming an outcome, and reports each row's rank over the whole 24-row catalog so you can see where the vector leg alone puts the part-code row. Example 8 takes the fused score apart and derives the two gates that set how far a lexical match can reach: at `top_k => 5` it reaches down to semantic rank 10, and a row deeper than that stays out however exact the token.

```python
search_text = 'run two external monitors from one laptop port'
part_code = 'DCK-2210'
top_k = 5

query = f'''
WITH semantic AS (
  SELECT base.id, ROW_NUMBER() OVER (ORDER BY distance) AS semantic_rank
  FROM VECTOR_SEARCH(
    TABLE `{PROJECT_ID}.{DATASET_ID}.vector_search_catalog`,
    'embedding',
    query_value => (AI.EMBED(content => '{search_text}', endpoint => 'text-embedding-005',
                             task_type => 'RETRIEVAL_QUERY')).result,
    top_k => {top_k},
    distance_type => 'COSINE'
  )
),
hybrid AS (
  SELECT base.id, ROW_NUMBER() OVER (ORDER BY distance) AS hybrid_rank
  FROM VECTOR_SEARCH(
    TABLE `{PROJECT_ID}.{DATASET_ID}.vector_search_catalog`,
    'embedding',
    query_value => (AI.EMBED(content => '{search_text}', endpoint => 'text-embedding-005',
                             task_type => 'RETRIEVAL_QUERY')).result,
    lexical_search_columns => ['sku'],
    lexical_search_query_value => '{part_code}',
    top_k => {top_k},
    distance_type => 'COSINE'
  )
),
whole_catalog AS (
  SELECT base.id, base.sku, base.product,
         ROW_NUMBER() OVER (ORDER BY distance) AS vector_rank_overall
  FROM VECTOR_SEARCH(
    TABLE `{PROJECT_ID}.{DATASET_ID}.vector_search_catalog`,
    'embedding',
    query_value => (AI.EMBED(content => '{search_text}', endpoint => 'text-embedding-005',
                             task_type => 'RETRIEVAL_QUERY')).result,
    top_k => 24,
    distance_type => 'COSINE'
  )
)
SELECT c.sku, c.product, c.vector_rank_overall, s.semantic_rank, h.hybrid_rank
FROM whole_catalog c
LEFT JOIN semantic s USING (id)
LEFT JOIN hybrid h USING (id)
WHERE s.semantic_rank IS NOT NULL OR h.hybrid_rank IS NOT NULL
ORDER BY h.hybrid_rank NULLS LAST
'''
df = client.query(query).to_dataframe()

added = df.loc[df['semantic_rank'].isna(), 'sku'].tolist()
lost = df.loc[df['hybrid_rank'].isna(), 'sku'].tolist()
print(f'query text   : {search_text}')
print(f'lexical value: {part_code}   (matched against sku, which is not embedded)')
print(f'Rows hybrid added that the semantic-only top {top_k} missed: {added or "none"}')
print(f'Rows the semantic-only top {top_k} had that hybrid dropped : {lost or "none"}')
for s in added:
    overall = int(df.loc[df['sku'] == s, 'vector_rank_overall'].iloc[0])
    print(f'  {s} is at vector rank {overall} of 24 on the semantic leg alone')
df
```

### 8. Reading the hybrid score — reciprocal rank fusion

In hybrid mode `distance` is **not a distance**. Each leg ranks the rows independently and the two ranks are combined by reciprocal rank fusion, so the value depends only on positions — never on geometry. The cell below reproduces every returned value from integer ranks alone, to within 1e-12:

`distance = 1 - ( 1/(60 + rank_vector) + 1/(61 + rank_lexical) )`

Only one of those two ranks is ever read directly. `VECTOR_SEARCH` returns no rank column, so `rank_vector` comes from a separate semantic-only run over the same rows and the lexical term is whatever remains. What that pins is a set of *denominators*, not a pair of constants: the semantic leg's top row contributes `1/61`, and the lexical leg's top row contributes `1/62`. Two readings fit identically, because `1/(61 + rank_lexical)` and `1/(60 + (rank_lexical + 1))` are the same number.

| reading | semantic leg | lexical leg |
|---|---|---|
| A — two constants | k = 60, ranks `1..n` | k = 61, ranks `1..n` |
| **B — one constant, offset ranks** | k = 60, ranks `1..n` | k = 60, ranks `2..n+1` |

Nothing observable from outside BigQuery separates them, but **B is the likelier**. `k = 60` over 1-based ranks is canonical reciprocal rank fusion — Cormack, Clarke and Buettcher (2009) — and the default wherever the constant is exposed: Elasticsearch and OpenSearch both name it `rank_constant` and default it to 60, and Spanner and AlloyDB write 60 into their documented SQL. No published implementation uses 61 as the constant. The semantic leg here lands on the canonical `1/61` for its own top row, so the extra `+1` sits on the lexical side specifically.

**Why the lexical leg would start at 2 is a separate question, and it is open.** Reading B says *where* the `+1` sits, not *why*. Three mechanisms fit equally well: a **deliberate tie-break** (at equal ranks `1/(60 + r)` beats `1/(61 + r)`, so the semantic leg wins every tie by a hair — exactly what you would implement if hybrid should never reorder a tie against the embedding); a **reserved slot** (if lexical position 1 holds something that is not a result, real rows begin at 2 naturally); or an **off-by-one** (61 is universal as the rank-1 *denominator*, `1/(60 + 1)`, and transcribing that as the constant gives the observed `1/62`). Only the last is a defect, and it is the least charitable of the three. Nothing observable from outside distinguishes them, so none of them is presented here as the explanation.

One argument looks decisive and is not: decoding with 60 on both legs implies lexical ranks `2..n+1`, and no n-row list hands out rank n+1. That rules out a shared base with ordinary 1-based numbering, but it is exactly what reading B predicts — a contiguous block starting at 2 is evidence *for* an offset, not against a shared constant.

The 60/61 form is kept below because it is the shortest expression that reproduces every observed value. Read it as arithmetic that holds, not as two deliberate design decisions. Note that `1 - (1/61 + 1/62)` = `0.9674775251189847` is the score of a row first on *both* legs: the best attainable hybrid score, and not 0.

On the no-match run below both ranks are the same integer *r*, and `1/(60 + r) + 1/(61 + r)` reproduces all 24 returned values. Hybrid scores cluster just under 1, lower is still better, and they are not comparable to the distances a semantic-only search returns.

The query recovers the decomposition. It takes `rank_vector` from a semantic-only search over the same rows, subtracts that leg's contribution from `1 - distance`, and inverts what remains to reveal the lexical rank. `formula_holds` re-derives the returned score from the two integer ranks and compares — the ranks come back as exact integers, which is what pins the constants.

It runs the fusion twice: once with the exact part code, and once with `NOSUCHTOKEN`, a lexical value nothing in the catalog matches. **Compare those two columns — they are the whole lesson.**

- With the exact part code, that row solves to `rank_lexical` 1. Every row that outranked it on the vector leg shifts down exactly one lexical position; every row below it keeps the position it already had.
- With a value that matches nothing, `rank_lexical` equals `rank_vector` for every row. The lexical leg does not drop rows it cannot score — it ranks every candidate it is given, falling back to the vector ordering.

That second point is the one to carry away, together with the limit on which rows the lexical leg ever sees. BigQuery hands it the top `10 * top_k` rows by semantic rank — that **candidate pool** is BM25's whole world. Inside the pool the leg ranks everything: matches take lexical ranks 1..*m*, and every remaining pooled row falls back to its semantic order behind them. No pooled row forfeits a term, which is why a hybrid search whose lexical value matches nothing returns precisely the semantic ordering. The cell above runs at `top_k => 24` over 24 rows, so the pool of 240 covers the whole catalog and the fallback is visible on every row.

A matched row therefore has **two gates** to clear:

```
Gate 1 (candidate pool):  rank_vector <= 10 * top_k
Gate 2 (fusion score):    1/(60 + rank_vector) + 1/(61 + rank_lexical)
                            must beat the row holding the last slot
```

Gate 2 is the arithmetic of the score, and a match is worth a bounded amount. Promotion to lexical rank 1 contributes `1/62` ≈ `0.0161`, while the row holding the last returned slot sits at semantic rank `top_k` and — pushed down one by the match — lexical rank `top_k + 1`, scoring `1/(60 + top_k) + 1/(62 + top_k)`. Comparing those two gives the deepest semantic rank the score alone would allow.

Gate 1 is a hard ceiling over the top of that. A row deeper than `10 * top_k` on the semantic leg receives no lexical rank at all — BM25 never sees it, however exactly the token matches — so no score can rescue it. The **effective reach** of a lexical match is the smaller of the two, `min( score reach, 10 * top_k )`. The score gate binds below `top_k = 51`, the pool gate from 51 up.

| `top_k` | 2 | 3 | 5 | 10 | 20 | 30 | 40 | 50 | 51 | 64 | 100 | 208 | 300 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| deepest semantic rank retrievable | 3 | 6 | 10 | 23 | 56 | 110 | 212 | 468 | 510 | 640 | 1,000 | 2,080 | 3,000 |

So hybrid re-ranks *and* widens — it does pull rows in from outside the semantic top-`top_k` — but the widening is bounded by `top_k` twice over, and it grows only in proportion to `top_k`. At the `top_k => 5` example 7 uses, a part-code match rescues a row from as deep as semantic rank 10 and no deeper. At `top_k => 64` it reaches semantic rank 640 and no deeper: the pool ends there, and rank 641 is invisible to BM25.

The pool gate is sharp enough to predict. Plant a target at semantic rank 3,000 in a 3,000-row table and the flip is predicted at `top_k = 300` — 299 returns nothing, 300 returns the row. Plant it at rank 1,500 in a 1,500-row table and the flip lands at 150, again exactly. At rank 500 in a 500-row table the pool never binds and the score gate sets the flip at 51. All three probe tables sit below BigQuery's 5,000-row `CREATE VECTOR INDEX` floor, so they are brute-force scanned and no index exists to restrict anything. The 7,275-row product catalog is the opposite case — it carries a hybrid `TREE_AH` index with `lexical_search_columns`, `ACTIVE` at 100% coverage — and the pool gate shows up there identically. The gate is therefore neither an index artifact nor something an index can avoid.

**The diagnostic signature.** A target outside the pool looks exactly like a token that matches nothing: `rank_lexical` equals `rank_vector` across the whole result set, the shape the `rank_lexical_nomatch` column shows above. Every returned distance is then `1 - ( 1/(60 + r) + 1/(61 + r) )`, so the top of the page reads `0.967478`. A page whose best value is `0.967734` had a match fire. That one number tells you whether to raise `top_k` or fix the token.

The rule that follows sizes `top_k` from the depth you need to reach, and it is a floor rather than a recipe: **to retrieve a row at semantic rank *R* by exact token, `top_k` ≥ *R*/10 is necessary but not sufficient.** That ratio clears the pool gate only. Below *R* of about 500 the score gate is the binding one and *R*/10 falls short — a row at semantic rank 100 needs `top_k` 29 rather than 10, at rank 200 exactly 40 rather than 20, at rank 500 exactly 51 rather than 50. Size `top_k` to at least *R*/10, then read the real requirement off the reach table above; the two gates cross at `top_k` 51. With a small `top_k` (≤ ~30) an exact token only nudges rows already near the top, so do not expect recall from it. A 7,275-row product catalog makes the cost concrete: with the wanted row at semantic rank 2,072, `top_k => 64` returns nothing at all, because the pool reached only 640 rows deep — that row needs `top_k >= 208`. And when the identifier *is* the entire query and you want certainty rather than a good chance, use `WHERE sku = @sku` — a predicate cannot be outranked by a fusion score, and it has no pool.

**Reverse-engineered, not documented.** No Google reference page states the fusion algorithm, no rank or score column is returned, and the constants can change without notice — a Google Cloud blog post naming "Reciprocal Rank Fusion and BM25" is the only official mention of the algorithms. Production code should treat a hybrid `distance` as an opaque ordering. (verified 2026-09-02)

```python
query = f'''
WITH vector_leg AS (
  SELECT base.id, base.sku, base.product,
         ROW_NUMBER() OVER (ORDER BY distance) AS rank_vector
  FROM VECTOR_SEARCH(
    TABLE `{PROJECT_ID}.{DATASET_ID}.vector_search_catalog`,
    'embedding',
    query_value => (AI.EMBED(content => '{search_text}', endpoint => 'text-embedding-005',
                             task_type => 'RETRIEVAL_QUERY')).result,
    top_k => 24,
    distance_type => 'COSINE'
  )
),
hybrid_exact AS (
  SELECT base.id, distance AS hybrid_distance
  FROM VECTOR_SEARCH(
    TABLE `{PROJECT_ID}.{DATASET_ID}.vector_search_catalog`,
    'embedding',
    query_value => (AI.EMBED(content => '{search_text}', endpoint => 'text-embedding-005',
                             task_type => 'RETRIEVAL_QUERY')).result,
    lexical_search_columns => ['sku'],
    lexical_search_query_value => '{part_code}',
    top_k => 24,
    distance_type => 'COSINE'
  )
),
hybrid_nomatch AS (
  SELECT base.id, distance AS nomatch_distance
  FROM VECTOR_SEARCH(
    TABLE `{PROJECT_ID}.{DATASET_ID}.vector_search_catalog`,
    'embedding',
    query_value => (AI.EMBED(content => '{search_text}', endpoint => 'text-embedding-005',
                             task_type => 'RETRIEVAL_QUERY')).result,
    lexical_search_columns => ['sku'],
    lexical_search_query_value => 'NOSUCHTOKEN',
    top_k => 24,
    distance_type => 'COSINE'
  )
),
solved AS (
  SELECT v.sku, v.product, v.rank_vector, h.hybrid_distance,
    CAST(ROUND(1 / ((1 - h.hybrid_distance) - 1 / (60 + v.rank_vector)) - 61) AS INT64) AS rank_lexical,
    CAST(ROUND(1 / ((1 - n.nomatch_distance) - 1 / (60 + v.rank_vector)) - 61) AS INT64) AS rank_lexical_nomatch
  FROM vector_leg v
  JOIN hybrid_exact h USING (id)
  JOIN hybrid_nomatch n USING (id)
)
SELECT sku, product, rank_vector, rank_lexical, rank_lexical_nomatch, hybrid_distance,
       1 - (1 / (60 + rank_vector) + 1 / (61 + rank_lexical)) AS rebuilt_distance,
       ABS(hybrid_distance - (1 - (1 / (60 + rank_vector) + 1 / (61 + rank_lexical)))) < 1e-12 AS formula_holds
FROM solved
ORDER BY rank_vector
'''
client.query(query).to_dataframe()
```

### 9. CREATE VECTOR INDEX for hybrid — accelerating the lexical leg

Hybrid search needs no index. An index makes the lexical leg fast on large tables, and it is what lets `AI.SEARCH` choose hybrid on its own in `AUTO` mode. It is a speed optimization, not a prerequisite.

Two rules the DDL enforces:

- Every column in `lexical_search_columns` must also appear in the `STORING` clause. Leave it out and the statement fails with `Lexical search column product must be in the list of stored columns.`
- A lexical column cannot also be the index key — that fails with `Column product found multiple times in ...`. The key is the embedding column; the lexical columns ride along in `STORING`.

`lexical_search_columns` works with either index type — `IVF` or `TREE_AH`.

**An autonomous-embedding column cannot be indexed.** A generated `STRUCT<result ARRAY<FLOAT64>, status STRING>` column is rejected as an index key at creation time, and so is an expression key such as `embedding_col.result`. A table that generates its own embeddings therefore needs a second table holding the projected `ARRAY<FLOAT64>` before it can carry a hybrid index. A dry run does not catch this. (verified 2026-09-01)

**Nothing is created here.** BigQuery only populates a vector index once the base table reaches 5,000 rows and 10 MB, so this 8-row sample table can never carry one. The cell below validates the DDL with a dry run, which neither creates the index nor bills.

```python
ddl = f'''
CREATE VECTOR INDEX vector_search_products_hybrid_index
ON `{PROJECT_ID}.{DATASET_ID}.vector_search_products`(embedding)
STORING (product, description, category)
OPTIONS (
  index_type = 'TREE_AH',
  distance_type = 'COSINE',
  lexical_search_columns = ['product', 'description']
)
'''

# Dry run: validates the statement without creating the index and without billing
client.query(ddl, job_config=bigquery.QueryJobConfig(dry_run=True))
print('DDL validated — no index created')
```

### 10. Managing an index — coverage, drift, and rebuild

Creating an index is not managing one. Three signals describe an index's health, and they move **independently**:

| Signal | Where to read it | What it actually means |
|---|---|---|
| `coverage_percentage`, `unindexed_row_count` | `INFORMATION_SCHEMA.VECTOR_INDEXES` | how much of the base table the index currently covers |
| `tfdv_drift` | `VECTOR_INDEX.STATISTICS(TABLE t)` | how far the *vector distribution* has moved since the build |
| `last_model_build_time` | `INFORMATION_SCHEMA.VECTOR_INDEXES` | when the TreeAH model itself was built — **not** `last_refresh_time` |

**`VECTOR_INDEX.STATISTICS` takes exactly one argument, and it must be a relation.** Adding the index name as a second argument fails with `Signature accepts at most 1 argument, found 2 arguments`; passing a string instead of `TABLE t` fails with `argument 1 must be a relation (i.e. table subquery)`. It returns a single column, `tfdv_drift` — `null` until the index's first refresh, `"0.0"` at fresh 100% coverage. On a table with **no** index it returns zero rows rather than an error and scans 0 bytes, which is what the cell below shows against this notebook's sample table.

**A negative `tfdv_drift` is a sentinel, not a magnitude.** Two freshly built indexes at 100% coverage reported different things: `"0.0"` from an unpartitioned hybrid index, and `-1.0` from a `PARTITION BY` index with no `lexical_search_columns`. Those two differ in more than one way, so this does not isolate a cause. Read a negative value as *no drift figure available for this index yet* and corroborate with `coverage_percentage` and `last_refresh_time` before acting on it.

**Coverage and drift are not the same alarm.** Measured against a live 7,275-row `TREE_AH` hybrid index (the kind `workflows/catalog_search` (`workflows/catalog_search/`) runs at real scale), inserting 11,780 rows whose vectors duplicate ones already indexed — 7,275 → 19,055 rows — moved the three signals in completely different directions:

| | before | after |
|---|---|---|
| `coverage_percentage` | 100 | **38** |
| `unindexed_row_count` | 0 | **11,780** |
| `tfdv_drift` | `0.0` | `1.97e-5` (essentially unchanged) |
| `last_model_build_time` | 03:14:31 | 03:14:31 (unchanged, across six 90-second polls) |

A large volume of *new but distributionally identical* rows is a **coverage** problem, not a drift problem. Coverage recovers on the automatic refresh; drift is the signal that argues for a rebuild.

**`ALTER VECTOR INDEX ... REBUILD` requires a BACKGROUND reservation.** With no reservation on the project it is rejected outright:

```
Cannot alter vector index on table catalog_products because there is no BACKGROUND reservation.
```

The check fires *before* validation, so the statement cannot even be dry-run — `--dry_run` returns the same error rather than `Query successfully validated`, even when the named index does not exist. That is why there is no dry-run cell for it here, unlike section 9. Index **maintenance** runs as background work and background work needs slots assigned to it; creating an index, populating it, and querying through it all work with no reservation at all. Running the rebuild needs an Enterprise-edition reservation carrying a `BACKGROUND` job-type assignment — an autoscale reservation with baseline 0 is the cheap shape, billing only while the rebuild runs. The identical gate covers `ALTER SEARCH INDEX` (see `functions/ai_search` (`functions/ai_search/`)).

```sql
-- Requires a BACKGROUND reservation; not run here
ALTER VECTOR INDEX catalog_products_hybrid_index
ON `PROJECT_ID.DATASET.catalog_products`
REBUILD;
```

**`PARTITION BY` must match the base table's partitioning exactly.** The clause does not let you choose a different partitioning for the index. Against a table partitioned by `RANGE_BUCKET(id, GENERATE_ARRAY(0, 30000, 5000))`, repeating that expression validates; naming any other column fails with `Invalid Partition By expression` — as does naming a column on a table that is not partitioned at all.

One more field worth knowing: `last_index_alteration_info` stays `null` until an `ALTER` succeeds, and it is a `RECORD`, so `bq query --format=csv` refuses to print it (`Cannot print record field ... in CSV format`). Use `--format=prettyjson`, or read it through the client library as below.

```python
# Both queries below are safe on any table — including one with no index at all.

# (a) Coverage and freshness for every vector index in the dataset.
#     last_index_alteration_info is a RECORD and stays NULL until an ALTER succeeds.
inventory = f'''
SELECT
  table_name,
  index_name,
  index_status,
  coverage_percentage,
  unindexed_row_count,
  last_refresh_time,
  last_model_build_time,
  disable_reason
FROM `{PROJECT_ID}.{DATASET_ID}.INFORMATION_SCHEMA.VECTOR_INDEXES`
'''
df = client.query(inventory).to_dataframe()
print(f'vector indexes in {DATASET_ID}: {len(df)}')
display(df)

# (b) Drift. Zero rows here is the expected result — the sample table carries no
#     index, and STATISTICS reports per index, not per table.
stats = f'''
SELECT * FROM VECTOR_INDEX.STATISTICS(TABLE `{PROJECT_ID}.{DATASET_ID}.vector_search_products`)
'''
drift = client.query(stats).to_dataframe()
print(f'\nVECTOR_INDEX.STATISTICS rows: {len(drift)} (0 = no index on this table, not an error)')
display(drift)
```

---
## Examples — `%%bigquery` Magics

The same examples using IPython magic commands. Magics let you write SQL directly in notebook cells without Python string wrapping.

Key patterns:
- `%%bigquery` — run SQL, display results inline
- `%%bigquery df` — run SQL, capture results into a pandas DataFrame

### Single search with `%%bigquery`

```sql
%%bigquery --project {PROJECT_ID}

SELECT base.product, base.description, distance
FROM VECTOR_SEARCH(
  TABLE `statmike-mlops-349915.bq_ai_functions.vector_search_products`,
  'embedding',
  query_value => (AI.EMBED(content => 'productivity tools',
                           endpoint => 'text-embedding-005',
                           task_type => 'RETRIEVAL_QUERY')).result,
  top_k => 3,
  distance_type => 'COSINE'
)
```

---
## Examples — BigFrames

BigFrames wraps `VECTOR_SEARCH` via `bbq.vector_search()`. It takes a base table name, column, and a query DataFrame/Series.

```python
import bigframes.pandas as bpd
import bigframes.bigquery as bbq

bpd.options.bigquery.project = PROJECT_ID
bpd.options.bigquery.location = LOCATION
```

### Vector search

```python
# Create query embeddings
query_df = bpd.read_gbq_query("""
SELECT
  search_term,
  (AI.EMBED(content => search_term, endpoint => 'text-embedding-005',
            task_type => 'RETRIEVAL_QUERY')).result AS embedding
FROM UNNEST(['audio equipment']) AS search_term
""")

# Search
result = bbq.vector_search(
    f'{PROJECT_ID}.{DATASET_ID}.vector_search_products',
    'embedding',
    query_df,
    top_k=3,
    distance_type='COSINE'
)
result[['search_term', 'product', 'description', 'distance']].to_pandas()
```
