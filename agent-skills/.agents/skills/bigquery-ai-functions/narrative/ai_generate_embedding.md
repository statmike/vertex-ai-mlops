# AI.GENERATE_EMBEDDING — BigQuery AI Functions

`AI.GENERATE_EMBEDDING` is a table-valued function that creates embeddings from text, images, or video via a remote model. It supports multiple embedding models and returns statistics alongside the embedding vector.

**When to use it:**
- You need to embed an entire table of text or images in batch
- You want embedding statistics (token counts, truncation info)
- You need multimodal embeddings (images, video, audio, PDFs)
- You have an existing CREATE MODEL workflow for embeddings

**Alternatives:**
- `functions/ai_embed` (`AI.EMBED`) — Scalar function, no model required, for inline embedding. Supports a built-in model (`embeddinggemma-300m`) with no Vertex AI charges.
- `functions/ml_generate_embedding` (`ML.GENERATE_EMBEDDING`) — Legacy predecessor with ml_generate_embedding_ column prefixes

**Multimodal:** Supports image and video input via `RESOURCES.md#objectref-and-objectrefruntime-schema-reference` (ObjectRef). Pass ObjectRef or ObjectRefRuntime values in the `content` column. `gemini-embedding-2-preview` (Preview) extends this to audio and PDFs.

**References:** `RESOURCES.md` (Full syntax reference) | [Official documentation](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-generate-embedding) | `setup` (Setup guide)

---
## Setup

Set your project and location, authenticate, and create a temporary dataset for this notebook.

> This function requires a connection and a remote model. The cells below create them if they don't exist. See the `setup` (Setup Reference) for details.

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
for role in ['roles/aiplatform.user', 'roles/storage.objectViewer']:
    _sp.run(['gcloud', 'projects', 'add-iam-policy-binding', PROJECT_ID,
             f'--member=serviceAccount:{sa}', f'--role={role}', '--quiet'],
            capture_output=True, text=True)
print(f'Connection {CONNECTION_ID} ready (SA: {sa})')
```

```python
# Create remote embedding model (idempotent)
client.query(f'''
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.embedding_text`
  REMOTE WITH CONNECTION `{PROJECT_ID}.{LOCATION}.{CONNECTION_ID}`
  OPTIONS (endpoint = \'text-embedding-005\')
''').result()
print('Model embedding_text ready')
```

---
## Examples — SQL

Progressive examples from simplest to most advanced. Each cell adds one new concept.

### 1. Basic text embedding

Input must have a `content` column (STRING). Returns the input columns plus `embedding`, `statistics`, and `status`.

```python
query = f'''
SELECT content, ARRAY_LENGTH(embedding) AS dims
FROM AI.GENERATE_EMBEDDING(
  MODEL `{PROJECT_ID}.{DATASET_ID}.embedding_text`,
  (SELECT text AS content
   FROM UNNEST(['BigQuery is a data warehouse.', 'Cloud computing scales on demand.']) AS text)
)
'''
client.query(query).to_dataframe()
```

### 2. Viewing embedding statistics

The `statistics` column contains token count and truncation information.

```python
import json

query = f'''
SELECT content, embedding, statistics
FROM AI.GENERATE_EMBEDDING(
  MODEL `{PROJECT_ID}.{DATASET_ID}.embedding_text`,
  (SELECT 'What is machine learning and how does it work?' AS content)
)
'''
df = client.query(query).to_dataframe()
print(f'Dimensions: {len(df.iloc[0]["embedding"])}')
print(f'Statistics: {json.loads(df.iloc[0]["statistics"])}')
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
query = f'''
SELECT content, ARRAY_LENGTH(embedding) AS dims, statistics
FROM AI.GENERATE_EMBEDDING(
  MODEL `{PROJECT_ID}.{DATASET_ID}.embedding_text`,
  (SELECT text AS content
   FROM UNNEST([
     'BigQuery is a serverless data warehouse.',
     'Cloud Functions runs event-driven code.',
     'Cloud Storage stores objects in buckets.'
   ]) AS text),
  STRUCT('RETRIEVAL_DOCUMENT' AS task_type)
)
'''
client.query(query).to_dataframe()
```

### 4. Materializing embeddings for VECTOR_SEARCH

Save embeddings to a table so they can be searched with `VECTOR_SEARCH`.

```python
query = f'''
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.ai_generate_embedding_docs` AS
SELECT content, embedding
FROM AI.GENERATE_EMBEDDING(
  MODEL `{PROJECT_ID}.{DATASET_ID}.embedding_text`,
  (SELECT text AS content
   FROM UNNEST([
     'BigQuery is a serverless data warehouse for analytics.',
     'Cloud Functions lets you run code in response to events.',
     'Cloud Storage provides object storage for any amount of data.',
     'Kubernetes Engine runs containerized applications at scale.',
     'Pub/Sub is a messaging service for event-driven systems.'
   ]) AS text),
  STRUCT('RETRIEVAL_DOCUMENT' AS task_type)
)
'''
client.query(query).result()

client.query(f'SELECT content, ARRAY_LENGTH(embedding) AS dims FROM `{PROJECT_ID}.{DATASET_ID}.ai_generate_embedding_docs`').to_dataframe()
```

### 5. Using gemini-embedding-001 (higher dimensions)

`gemini-embedding-001` is a multilingual text embedding model that defaults to 3072 dimensions (vs 768 for `text-embedding-005`). Create a separate remote model for it, then compare.

```python
# Create remote model for gemini-embedding-001 (idempotent)
client.query(f'''
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.embedding_gemini`
  REMOTE WITH CONNECTION `{PROJECT_ID}.{LOCATION}.{CONNECTION_ID}`
  OPTIONS (endpoint = \'gemini-embedding-001\')
''').result()
print('Model embedding_gemini ready')

# Compare dimensions: text-embedding-005 (768) vs gemini-embedding-001 (3072)
query = f'''
SELECT
  'text-embedding-005' AS model,
  ARRAY_LENGTH(embedding) AS dims,
  statistics
FROM AI.GENERATE_EMBEDDING(
  MODEL `{PROJECT_ID}.{DATASET_ID}.embedding_text`,
  (SELECT 'BigQuery is a data warehouse.' AS content)
)
UNION ALL
SELECT
  'gemini-embedding-001',
  ARRAY_LENGTH(embedding),
  statistics
FROM AI.GENERATE_EMBEDDING(
  MODEL `{PROJECT_ID}.{DATASET_ID}.embedding_gemini`,
  (SELECT 'BigQuery is a data warehouse.' AS content)
)
'''
client.query(query).to_dataframe()
```

---
## Multimodal — Document Embedding

`AI.GENERATE_EMBEDDING` supports image and video input via `multimodalembedding@001`. Input: a query with a `content` column containing ObjectRef values. Supports `output_dimensionality` (128, 256, 512, 1408 — default 1408).

> **New:** `gemini-embedding-2-preview` (Preview) supports text, images, audio, video, and PDFs — up to 3072 dimensions and 8192 tokens. It also returns `statistics` with per-modality token counts (unlike `multimodalembedding@001`). Currently US and us-central1 only. The examples below use the GA `multimodalembedding@001` approach.

Below we render invoice and receipt PDFs from this project's `data/documents` (document set) to PNG images, upload them to GCS, then embed them in batch.

### Multimodal embedding model

Create a remote model pointing to `multimodalembedding@001` for image and video embeddings.

```python
# Create remote multimodal embedding model (idempotent)
client.query(f'''
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.embedding_multimodal`
  REMOTE WITH CONNECTION `{PROJECT_ID}.{LOCATION}.{CONNECTION_ID}`
  OPTIONS (endpoint = \'multimodalembedding@001\')
''').result()
print('Model embedding_multimodal ready')
```

```python
import shutil, subprocess

if not shutil.which('pdftoppm'):
    subprocess.check_call(['sudo', 'apt-get', 'install', '-y', '-qq', 'poppler-utils'])
    print('Installed poppler-utils (provides pdftoppm)')
else:
    print('pdftoppm already available')
```

```python
import subprocess
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
prefix = 'bq_ai_functions/ai_generate_embedding'

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

### 6. Batch embed documents

Use `AI.GENERATE_EMBEDDING` with the multimodal model on a subquery that builds ObjectRef values inline. The subquery must produce a `content` column with ObjectRefRuntime values. Each document image gets a 1408-dimension embedding.

```python
query = f'''
SELECT
  doc_name,
  ARRAY_LENGTH(embedding) AS dims
FROM AI.GENERATE_EMBEDDING(
  MODEL `{PROJECT_ID}.{DATASET_ID}.embedding_multimodal`,
  (SELECT
    doc_name,
    OBJ.GET_ACCESS_URL(
      OBJ.FETCH_METADATA(
        OBJ.MAKE_REF(
          CONCAT('gs://{BUCKET}/bq_ai_functions/ai_generate_embedding/', doc_name),
          '{PROJECT_ID}.{LOCATION}.{CONNECTION_ID}'
        )
      ), 'r') AS content
  FROM UNNEST([
    'invoice_1.png', 'invoice_2.png', 'invoice_3.png',
    'receipt_1.png', 'receipt_2.png', 'receipt_3.png'
  ]) AS doc_name)
)
'''
client.query(query).to_dataframe()
```

### 7. Custom embedding dimensions

Use `output_dimensionality` to reduce the vector size. Smaller dimensions are faster to search but may lose some detail.

```python
query = f'''
SELECT
  doc_name,
  ARRAY_LENGTH(embedding) AS dims
FROM AI.GENERATE_EMBEDDING(
  MODEL `{PROJECT_ID}.{DATASET_ID}.embedding_multimodal`,
  (SELECT
    doc_name,
    OBJ.GET_ACCESS_URL(
      OBJ.FETCH_METADATA(
        OBJ.MAKE_REF(
          CONCAT('gs://{BUCKET}/bq_ai_functions/ai_generate_embedding/', doc_name),
          '{PROJECT_ID}.{LOCATION}.{CONNECTION_ID}'
        )
      ), 'r') AS content
  FROM UNNEST([
    'invoice_1.png', 'invoice_2.png', 'invoice_3.png'
  ]) AS doc_name),
  STRUCT(256 AS output_dimensionality)
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

### Embedding with `%%bigquery`

Since AI.GENERATE_EMBEDDING requires a MODEL reference, most usage is better via `client.query()` with f-strings.

```sql
%%bigquery --project {PROJECT_ID}

SELECT content, ARRAY_LENGTH(embedding) AS dims
FROM AI.GENERATE_EMBEDDING(
  MODEL `statmike-mlops-349915.bq_ai_functions.embedding_text`,
  (SELECT text AS content
   FROM UNNEST(['Machine learning', 'Deep learning', 'NLP']) AS text)
)
```

---
## Examples — BigFrames

BigFrames wraps `AI.GENERATE_EMBEDDING` via `bbq.ai.generate_embedding()`. It takes a model name string and a DataFrame/Series.

```python
import bigframes.pandas as bpd
import bigframes.bigquery as bbq

bpd.options.bigquery.project = PROJECT_ID
bpd.options.bigquery.location = LOCATION
```

### Batch embedding

```python
df = bpd.DataFrame({
    'content': [
        'BigQuery is a data warehouse.',
        'Cloud Functions runs event-driven code.',
        'Cloud Storage stores objects.'
    ]
})

model_name = f'{PROJECT_ID}.{DATASET_ID}.embedding_text'
result = bbq.ai.generate_embedding(model_name, df)
result[['content']].to_pandas()
```
