# Semantic Search System — BigQuery AI Functions

Build a semantic search system in BigQuery, comparing two approaches:

1. **Manual approach**: `AI.EMBED` to create embeddings + `VECTOR_SEARCH` to query them
2. **Simplified approach**: `AI.SEARCH` with autonomous embedding generation

**What this demonstrates:**
- Creating and storing embeddings with `AI.EMBED`
- Searching with `VECTOR_SEARCH` (single query, batch, filtered)
- Setting up autonomous embeddings for `AI.SEARCH`
- Comparing the two approaches: flexibility vs simplicity

**Functions used:** `functions/ai_embed` (`AI.EMBED`) | `functions/vector_search` (`VECTOR_SEARCH`) | `functions/ai_search` (`AI.SEARCH`)

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

Create a sample knowledge base of technical documentation articles. We'll use this same data for both search approaches.

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
## Comparison: Manual vs Simplified

| Feature | Manual (EMBED + VECTOR_SEARCH) | Simplified (AI.SEARCH) |
|---------|-------------------------------|------------------------|
| **Setup** | Create embeddings yourself | Autonomous — BigQuery handles it |
| **Query embedding** | You call AI.EMBED on queries | Automatic |
| **Task types** | Full control (RETRIEVAL_DOCUMENT / RETRIEVAL_QUERY) | Managed by BigQuery |
| **Distance metrics** | Choose COSINE, EUCLIDEAN, DOT_PRODUCT | Managed |
| **Filtering** | Pre-filter base table with subquery | Not supported |
| **Batch queries** | Multiple queries in one call | One query at a time |
| **Vector indexes** | Supports IVF and TreeAH indexes | Managed |
| **Best for** | Production systems needing control | Quick prototyping, simple search |
