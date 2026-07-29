# AI.SEARCH — BigQuery AI Functions

`AI.SEARCH` is a simplified semantic search function for tables with autonomous embedding generation enabled. It embeds the query at runtime and searches the table — no manual embedding step needed.

**When to use it:**
- You want the simplest possible semantic search (no embedding management)
- Your base table has autonomous embedding generation enabled
- You need single-query semantic search with a string literal

**Alternatives:**
- `functions/vector_search` (`VECTOR_SEARCH`) — More control: batch search, custom embeddings, manual embedding management
- `functions/ai_embed` (`AI.EMBED`) — Create individual embeddings for custom search logic
- `functions/ai_similarity` (`AI.SIMILARITY`) — Compare two specific inputs directly

**Featured in:** `workflows/semantic_search` (Semantic Search System)

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
This is configured at table creation — you add a `GENERATED ALWAYS AS` column that calls `AI.EMBED`, with `OPTIONS(asynchronous = TRUE)`. BigQuery then automatically generates and maintains embeddings when data is inserted or updated.

**Note on task_type:** When you configure autonomous embedding generation, BigQuery handles the `task_type` automatically — it uses `RETRIEVAL_DOCUMENT` when indexing your table data and `RETRIEVAL_QUERY` when embedding search queries at runtime. This is the correct **asymmetric** pattern for retrieval. See the `functions/ai_embed` (`AI.EMBED`) notebook for the full list of task types.

**Limitations:** You can't add a generated embedding column to an existing table with ALTER TABLE — it must be defined at CREATE TABLE time.

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
