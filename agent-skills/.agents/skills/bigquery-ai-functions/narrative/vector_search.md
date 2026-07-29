# VECTOR_SEARCH — BigQuery AI Functions

`VECTOR_SEARCH` is a table-valued function that finds the top-K nearest neighbors from a base table using pre-computed embeddings. Supports vector indexes for efficient approximate nearest neighbor (ANN) search.

**When to use it:**
- You need semantic search over a table with pre-computed embeddings
- You want top-K nearest neighbor search at scale
- You need batch search (multiple queries at once)
- You want to build a RAG (Retrieval Augmented Generation) pipeline

**Vector indexes:** By default, `VECTOR_SEARCH` uses brute-force KNN (exact nearest neighbor), which scans every row. For large tables, BigQuery supports vector indexes that enable approximate nearest neighbor (ANN) search for dramatically faster queries:

| Index Type | Best For | How It Works |
|------------|----------|--------------|
| `IVF` (Inverted File) | General-purpose ANN | Partitions vectors into clusters; searches only the nearest clusters |
| `TreeAH` (Tree Asymmetric Hashing) | Large-scale, high-throughput | Uses a tree structure with asymmetric hashing for efficient search |

Create a vector index with `CREATE VECTOR INDEX` — no changes to your `VECTOR_SEARCH` queries are needed. See the [Vector Index documentation](https://cloud.google.com/bigquery/docs/vector-index) for details.

**Alternatives:**
- `functions/ai_search` (`AI.SEARCH`) — Simplified semantic search with autonomous embedding generation
- `functions/ai_similarity` (`AI.SIMILARITY`) — Cosine similarity between two specific inputs
- `functions/ai_embed` (`AI.EMBED`) — Create embeddings for individual values

**Featured in:** `workflows/semantic_search` (Semantic Search System) | `workflows/rag_pipeline` (RAG Pipeline) | `workflows/document_rag` (Document RAG Pipeline)

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

### 3. Using EUCLIDEAN distance

Change the distance metric. Options: `COSINE` (default: `EUCLIDEAN`), `EUCLIDEAN`, `DOT_PRODUCT`.

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
