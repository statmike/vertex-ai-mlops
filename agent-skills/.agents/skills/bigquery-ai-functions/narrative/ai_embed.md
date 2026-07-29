# AI.EMBED — BigQuery AI Functions

`AI.EMBED` is a scalar function that creates text or image embeddings. Specify an endpoint directly, or use the built-in `embeddinggemma-300m` model with no Vertex AI charges — no model creation required either way.

**When to use it:**
- You need embeddings for individual values in SELECT, WHERE, or JOIN
- You want to create embeddings without CREATE MODEL
- You need to embed a small number of values inline
- You want zero-cost text embedding using the built-in model (`embeddinggemma-300m`)

**Alternatives:**
- `functions/ai_generate_embedding` (`AI.GENERATE_EMBEDDING`) — TVF for batch embedding, requires CREATE MODEL
- `functions/ai_similarity` (`AI.SIMILARITY`) — Cosine similarity between two inputs (uses embeddings internally)
- `functions/vector_search` (`VECTOR_SEARCH`) — Top-K nearest neighbor search on pre-computed embeddings

**Featured in:** `workflows/semantic_search` (Semantic Search System) | `workflows/rag_pipeline` (RAG Pipeline) | `workflows/multimodal_analysis` (Multimodal Analysis) | `workflows/document_rag` (Document RAG Pipeline)

**Multimodal:** Supports image input via `RESOURCES.md#objectref-and-objectrefruntime-schema-reference` (ObjectRef) with `multimodalembedding@001`. For PDFs, use `gemini-embedding-2-preview` (Preview) which embeds PDFs directly without rendering to images.

**References:** `RESOURCES.md` (Full syntax reference) | [Official documentation](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-embed) | `setup` (Setup guide)

---
## Setup

Set your project and location, authenticate, and create a temporary dataset for this notebook.

> Text embedding uses end-user credentials automatically — no connection needed. **Multimodal** embedding (images) requires a connection. See the `setup` (Setup Reference) for details.

```python
PROJECT_ID = 'statmike-mlops-349915'  # <-- Replace with your project ID
LOCATION = 'US'  # BigQuery dataset location
DATASET_ID = 'bq_ai_functions'  # Shared dataset across all notebooks
CONNECTION_ID = 'bq_ai_functions'  # Shared connection
BUCKET = PROJECT_ID  # GCS bucket (same name as project)
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

### Connection Setup

Multimodal embedding (images) requires a connection with `aiplatform.user` and `storage.objectViewer` roles. The connection is shared across notebooks.

```python
import subprocess as _sp, json as _json

# Create connection (idempotent)
_sp.run(['bq', 'mk', '--connection', '--location', LOCATION,
         '--connection_type', 'CLOUD_RESOURCE',
         '--project_id', PROJECT_ID, CONNECTION_ID],
        capture_output=True, text=True)

# Get service account and grant required roles
r = _sp.run(['bq', 'show', '--connection', '--format=json',
             '--project_id', PROJECT_ID, '--location', LOCATION, CONNECTION_ID],
            capture_output=True, text=True, check=True)
sa = _json.loads(r.stdout)['cloudResource']['serviceAccountId']
for role in ['roles/aiplatform.user', 'roles/storage.objectViewer']:
    _sp.run(['gcloud', 'projects', 'add-iam-policy-binding', PROJECT_ID,
             f'--member=serviceAccount:{sa}', f'--role={role}', '--quiet'],
            capture_output=True, text=True)
print(f'Connection {CONNECTION_ID} ready (SA: {sa})')
```

---
## Examples — SQL

Progressive examples from simplest to most advanced. Each cell adds one new concept.

### 1. Basic text embedding

`AI.EMBED` takes content and an endpoint, returns a STRUCT with `result` (the embedding vector) and `status`.

**Note:** Either `endpoint` or `model` is required. When using Vertex AI models, `endpoint` must include the model version. When using the built-in model, use `model` instead (see Example 6).

```python
query = """
SELECT
  text,
  ARRAY_LENGTH((AI.EMBED(
    content => text,
    endpoint => 'text-embedding-005'
  )).result) AS embedding_dimensions
FROM UNNEST(['BigQuery is a data warehouse.', 'Cloud computing scales on demand.']) AS text
"""
client.query(query).to_dataframe()
```

### 2. Viewing the embedding vector

The embedding is an `ARRAY<FLOAT64>` — a dense vector of floating-point numbers.

```python
query = """
SELECT
  (AI.EMBED(
    content => 'What is machine learning?',
    endpoint => 'text-embedding-005'
  )).result AS embedding
"""
df = client.query(query).to_dataframe()
embedding = df.iloc[0]['embedding']
print(f'Dimensions: {len(embedding)}')
print(f'First 5 values: {embedding[:5]}')
```

### 3. Using task_type for retrieval

`task_type` tells the embedding model the intended use of the text, which changes how the embedding is generated. This is a critical configuration choice.

**Asymmetric task types** — documents and queries use *different* task types. Use this pattern for retrieval, where what you index differs in intent from what you search with:

| Use Case | Document Task Type | Query Task Type |
|----------|-------------------|-----------------|
| Search | `RETRIEVAL_DOCUMENT` | `RETRIEVAL_QUERY` |
| Question Answering | `RETRIEVAL_DOCUMENT` | `QUESTION_ANSWERING` |
| Fact Checking | `RETRIEVAL_DOCUMENT` | `FACT_VERIFICATION` |
| Code Retrieval | `RETRIEVAL_DOCUMENT` | `CODE_RETRIEVAL_QUERY` |

**Symmetric task types** — both sides use the *same* task type:
- `SEMANTIC_SIMILARITY` — comparing how similar two texts are
- `CLASSIFICATION` — grouping texts by category
- `CLUSTERING` — organizing texts into clusters

> **Key point:** If your use case doesn't align with a specific task type, use `RETRIEVAL_DOCUMENT` when indexing and `RETRIEVAL_QUERY` when searching.

```python
query = """
SELECT
  text,
  (AI.EMBED(
    content => text,
    endpoint => 'text-embedding-005',
    task_type => 'RETRIEVAL_DOCUMENT'
  )).result AS embedding
FROM UNNEST([
  'BigQuery is a serverless data warehouse.',
  'Cloud Functions runs event-driven code.',
  'Cloud Storage stores objects in buckets.'
]) AS text
"""
df = client.query(query).to_dataframe()
for _, row in df.iterrows():
    print(f'{row["text"][:40]}... -> {len(row["embedding"])} dims')
```

### 4. Computing cosine similarity manually

Embed two texts and compute cosine similarity using the ML.DISTANCE function.

```python
query = """
WITH embeddings AS (
  SELECT
    text,
    (AI.EMBED(content => text, endpoint => 'text-embedding-005')).result AS vec
  FROM UNNEST([
    'BigQuery is a data warehouse',
    'BigQuery stores and analyzes large datasets',
    'I enjoy hiking in the mountains'
  ]) AS text
)
SELECT
  a.text AS text_a,
  b.text AS text_b,
  1 - ML.DISTANCE(a.vec, b.vec, 'COSINE') AS cosine_similarity
FROM embeddings a
CROSS JOIN embeddings b
WHERE a.text < b.text
ORDER BY cosine_similarity DESC
"""
client.query(query).to_dataframe()
```

### 5. Saving embeddings to a table

For reuse across queries, materialize embeddings into a table.

```python
query = f'''
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.ai_embed_documents` AS
SELECT
  id,
  text,
  (AI.EMBED(content => text, endpoint => 'text-embedding-005', task_type => 'RETRIEVAL_DOCUMENT')).result AS embedding
FROM UNNEST([
  STRUCT(1 AS id, 'BigQuery is a serverless data warehouse for analytics.' AS text),
  STRUCT(2, 'Cloud Functions lets you run code in response to events.'),
  STRUCT(3, 'Cloud Storage provides object storage for any amount of data.'),
  STRUCT(4, 'Kubernetes Engine runs containerized applications at scale.'),
  STRUCT(5, 'Pub/Sub is a messaging service for event-driven systems.')
])
'''
client.query(query).result()

# Verify
client.query(f'SELECT id, text, ARRAY_LENGTH(embedding) AS dims FROM `{PROJECT_ID}.{DATASET_ID}.ai_embed_documents` ORDER BY id').to_dataframe()
```

### 6. Built-in model (no Vertex AI charges)

Use `model => 'embeddinggemma-300m'` for zero-cost text embedding. Data stays in BigQuery and uses BQ compute slots — no Vertex AI endpoint call, no connection needed, no per-token billing. Returns 768-dimension vectors.

This is ideal for cost-sensitive workloads or when you want to avoid Vertex AI dependencies entirely.

> **Note:** `embeddinggemma-300m` is in Preview. When using `model`, you cannot specify `endpoint`, `title`, `model_params`, or `connection_id`.

```python
query = """
SELECT
  text,
  ARRAY_LENGTH((AI.EMBED(
    content => text,
    model => 'embeddinggemma-300m'
  )).result) AS embedding_dimensions
FROM UNNEST(['BigQuery is a data warehouse.', 'Cloud computing scales on demand.']) AS text
"""
client.query(query).to_dataframe()
```

### 7. Comparing embedding models

`AI.EMBED` supports multiple embedding models with different dimensions, capabilities, and pricing. Here's a side-by-side comparison:

| Model | Param | Type | Max Dims | Cost |
|-------|-------|------|----------|------|
| `embeddinggemma-300m` | `model` | Built-in text | 768 | BQ slots only |
| `text-embedding-005` | `endpoint` | Vertex AI text | 768 | Vertex AI per-token |
| `gemini-embedding-001` | `endpoint` | Vertex AI text | 3072 | Vertex AI per-token |

```python
query = """
SELECT 'embeddinggemma-300m (built-in)' AS model,
  ARRAY_LENGTH((AI.EMBED(content => 'BigQuery is a data warehouse', model => 'embeddinggemma-300m')).result) AS dims
UNION ALL
SELECT 'text-embedding-005',
  ARRAY_LENGTH((AI.EMBED(content => 'BigQuery is a data warehouse', endpoint => 'text-embedding-005')).result)
UNION ALL
SELECT 'gemini-embedding-001',
  ARRAY_LENGTH((AI.EMBED(content => 'BigQuery is a data warehouse', endpoint => 'gemini-embedding-001')).result)
"""
client.query(query).to_dataframe()
```

---
## Multimodal — Document Embedding

`AI.EMBED` supports image input via ObjectRef with `multimodalembedding@001`. A `connection_id` is required for multimodal. Returns 1408-dimension vectors by default (configurable: 128, 256, 512, 1408).

> **New:** `gemini-embedding-2-preview` (Preview) can embed PDFs directly — no rendering to PNG needed. It also supports audio and video. See `RESOURCES.md` (RESOURCES.md) for details. The examples below use the GA `multimodalembedding@001` approach with rendered PNGs.

Below we render invoice and receipt PDFs from this project's `data/documents` (document set) to PNG images, upload them to GCS, then embed and compare them. The embeddings should show that documents of the same type cluster together.

The ObjectRef pattern: `OBJ.MAKE_REF` → `OBJ.FETCH_METADATA` → `OBJ.GET_ACCESS_URL` creates a signed reference inline — no object table needed.

```python
import shutil, subprocess

if not shutil.which('pdftoppm'):
    subprocess.check_call(['sudo', 'apt-get', 'install', '-y', '-qq', 'poppler-utils'])
    print('Installed poppler-utils (provides pdftoppm)')
else:
    print('pdftoppm already available')
```

```python
import subprocess, io
from pathlib import Path
from google.cloud import storage

# Locate the document directory
data_dir = Path('../../data/documents')
if not data_dir.exists():
    data_dir = Path('data/documents')

# Pick 3 invoices and 3 receipts
docs = [
    ('invoice_1.png', data_dir / 'invoices' / 'invoice_001.pdf'),
    ('invoice_2.png', data_dir / 'invoices' / 'invoice_002.pdf'),
    ('invoice_3.png', data_dir / 'invoices' / 'invoice_003.pdf'),
    ('receipt_1.png', data_dir / 'receipts' / 'receipt_001.pdf'),
    ('receipt_2.png', data_dir / 'receipts' / 'receipt_002.pdf'),
    ('receipt_3.png', data_dir / 'receipts' / 'receipt_003.pdf'),
]

gcs = storage.Client(project=PROJECT_ID)
bucket = gcs.bucket(BUCKET)
prefix = 'bq_ai_functions/ai_embed'

for name, pdf_path in docs:
    # Render first page of PDF to PNG using pdftoppm (poppler)
    result = subprocess.run(
        ['pdftoppm', '-png', '-f', '1', '-l', '1', '-r', '150', str(pdf_path)],
        capture_output=True
    )
    blob = bucket.blob(f'{prefix}/{name}')
    blob.upload_from_string(result.stdout, content_type='image/png')

print(f'Rendered and uploaded {len(docs)} document images to gs://{BUCKET}/{prefix}/')
```

### 8. Embed a document image

Use the inline ObjectRef pipeline to embed an invoice image with `multimodalembedding@001`. The `connection_id` parameter authorizes GCS access.

```python
query = f"""
SELECT
  'invoice_1.png' AS document,
  ARRAY_LENGTH((AI.EMBED(
    content => OBJ.GET_ACCESS_URL(
      OBJ.FETCH_METADATA(
        OBJ.MAKE_REF('gs://{BUCKET}/bq_ai_functions/ai_embed/invoice_1.png', '{PROJECT_ID}.{LOCATION}.{CONNECTION_ID}')
      ), 'r'),
    endpoint => 'multimodalembedding@001',
    connection_id => '{PROJECT_ID}.{LOCATION}.{CONNECTION_ID}'
  )).result) AS embedding_dimensions
"""
client.query(query).to_dataframe()
```

### 9. Compare document embeddings

Embed all 6 documents and compute pairwise cosine similarity using `ML.DISTANCE`. Documents of the same type (invoices vs receipts) should cluster together with higher similarity scores.

```python
query = f"""
WITH doc_embeddings AS (
  SELECT
    doc_name,
    (AI.EMBED(
      content => OBJ.GET_ACCESS_URL(
        OBJ.FETCH_METADATA(
          OBJ.MAKE_REF(
            CONCAT('gs://{BUCKET}/bq_ai_functions/ai_embed/', doc_name),
            '{PROJECT_ID}.{LOCATION}.{CONNECTION_ID}'
          )
        ), 'r'),
      endpoint => 'multimodalembedding@001',
      connection_id => '{PROJECT_ID}.{LOCATION}.{CONNECTION_ID}'
    )).result AS vec
  FROM UNNEST([
    'invoice_1.png', 'invoice_2.png', 'invoice_3.png',
    'receipt_1.png', 'receipt_2.png', 'receipt_3.png'
  ]) AS doc_name
)
SELECT
  a.doc_name AS doc_a,
  b.doc_name AS doc_b,
  ROUND(1 - ML.DISTANCE(a.vec, b.vec, 'COSINE'), 4) AS cosine_similarity
FROM doc_embeddings a
CROSS JOIN doc_embeddings b
WHERE a.doc_name < b.doc_name
ORDER BY cosine_similarity DESC
"""
client.query(query).to_dataframe()
```

---
## Examples — `%%bigquery` Magics

The same examples using IPython magic commands. Magics let you write SQL directly in notebook cells without Python string wrapping.

Key patterns:
- `%%bigquery` — run SQL, display results inline
- `%%bigquery df` — run SQL, capture results into a pandas DataFrame

### Basic embedding with `%%bigquery`

```sql
%%bigquery --project {PROJECT_ID}

SELECT
  text,
  ARRAY_LENGTH((AI.EMBED(
    content => text,
    endpoint => 'text-embedding-005'
  )).result) AS embedding_dimensions
FROM UNNEST(['Machine learning', 'Deep learning', 'Natural language processing']) AS text
```

---
## Examples — BigFrames

`AI.EMBED` has no direct BigFrames equivalent. Use `session.read_gbq_query()` to execute AI.EMBED SQL from BigFrames.

```python
import bigframes.pandas as bpd

bpd.options.bigquery.project = PROJECT_ID
bpd.options.bigquery.location = LOCATION
```

### Running AI.EMBED via read_gbq_query

```python
query = """
SELECT
  text,
  ARRAY_LENGTH((AI.EMBED(content => text, endpoint => 'text-embedding-005')).result) AS embedding_dims
FROM UNNEST(['BigQuery', 'Cloud Functions', 'Cloud Storage']) AS text
"""
df = bpd.read_gbq_query(query)
df.to_pandas()
```
