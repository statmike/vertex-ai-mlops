# AI.SIMILARITY — BigQuery AI Functions

`AI.SIMILARITY` is a scalar function that computes cosine similarity between two inputs by generating embeddings at runtime. Specify an endpoint, or use the built-in `embeddinggemma-300m` model with no Vertex AI charges. Values closer to 1 indicate more similar inputs.

**When to use it:**
- You want to compare two specific texts or images for similarity
- You need a quick similarity check without pre-computed embeddings
- You are prototyping a similarity-based feature
- You want zero-cost text similarity using the built-in model (`embeddinggemma-300m`)

**Alternatives:**
- `functions/vector_search` (`VECTOR_SEARCH`) — Top-K search over pre-computed embeddings at scale
- `functions/ai_embed` (`AI.EMBED`) — Create embeddings yourself and compute distance manually
- `functions/ai_search` (`AI.SEARCH`) — Simplified semantic search with autonomous embedding generation

**Multimodal:** Supports image input via `RESOURCES.md#objectref-and-objectrefruntime-schema-reference` (ObjectRef) with `multimodalembedding@001`. For PDFs, use `gemini-embedding-2-preview` (Preview) which compares PDFs directly without rendering to images.

**Featured in:** `workflows/multimodal_analysis` (Multimodal Analysis)

**References:** `RESOURCES.md` (Full syntax reference) | [Official documentation](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-similarity) | `setup` (Setup guide)

---
## Setup

Set your project and location, authenticate, and create a temporary dataset for this notebook.

> Text similarity uses end-user credentials automatically — no connection needed. **Multimodal** similarity (images) requires a connection. See the `setup` (Setup Reference) for details.

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

Multimodal similarity (images) requires a connection with `aiplatform.user` and `storage.objectViewer` roles.

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

### 1. Basic text similarity

`AI.SIMILARITY` takes two text inputs and an endpoint, returns a FLOAT64 (cosine similarity).

**Note:** Either `endpoint` or `model` is required. When using the built-in model, use `model` instead (see Example 5). This function uses **symmetric** embeddings internally (both inputs are embedded the same way), making it ideal for comparing two texts of similar nature. For asymmetric use cases like search (where queries and documents are fundamentally different), use `functions/vector_search` (`VECTOR_SEARCH`) or `functions/ai_search` (`AI.SEARCH`) instead. See the `functions/ai_embed` (`AI.EMBED`) notebook for the full list of task types.

```python
query = """
SELECT
  AI.SIMILARITY(
    content1 => 'BigQuery is a data warehouse',
    content2 => 'BigQuery stores and analyzes data',
    endpoint => 'text-embedding-005'
  ) AS similarity
"""
df = client.query(query).to_dataframe()
print(f'Similarity: {df.iloc[0]["similarity"]:.4f}')
```

### 2. Comparing multiple pairs

Use a CROSS JOIN to compare multiple items against each other.

```python
query = """
SELECT
  text_a,
  text_b,
  AI.SIMILARITY(
    content1 => text_a,
    content2 => text_b,
    endpoint => 'text-embedding-005'
  ) AS similarity
FROM
  UNNEST(['machine learning', 'deep learning', 'cooking recipes']) AS text_a,
  UNNEST(['artificial intelligence', 'neural networks', 'baking bread']) AS text_b
ORDER BY similarity DESC
"""
client.query(query).to_dataframe()
```

### 3. Finding the best match

Use AI.SIMILARITY to find which item from a catalog best matches a query.

```python
query = """
SELECT
  product,
  AI.SIMILARITY(
    content1 => 'comfortable typing device',
    content2 => product,
    endpoint => 'text-embedding-005'
  ) AS similarity
FROM UNNEST([
  'mechanical keyboard with ergonomic design',
  'wireless mouse with adjustable DPI',
  'standing desk with memory presets',
  'noise-cancelling headphones'
]) AS product
ORDER BY similarity DESC
LIMIT 1
"""
client.query(query).to_dataframe()
```

### 4. Semantic deduplication

Find near-duplicate entries by checking similarity above a threshold.

```python
query = """
WITH items AS (
  SELECT *
  FROM UNNEST([
    STRUCT(1 AS id, 'BigQuery data warehouse' AS text),
    STRUCT(2, 'BigQuery serverless warehouse'),
    STRUCT(3, 'Cloud Functions serverless'),
    STRUCT(4, 'Cloud Functions event-driven compute')
  ])
)
SELECT
  a.id AS id_a, a.text AS text_a,
  b.id AS id_b, b.text AS text_b,
  AI.SIMILARITY(content1 => a.text, content2 => b.text, endpoint => 'text-embedding-005') AS similarity
FROM items a, items b
WHERE a.id < b.id
  AND AI.SIMILARITY(content1 => a.text, content2 => b.text, endpoint => 'text-embedding-005') > 0.8
ORDER BY similarity DESC
"""
client.query(query).to_dataframe()
```

### 5. Built-in model (no Vertex AI charges)

Use `model => 'embeddinggemma-300m'` for zero-cost similarity comparisons. No endpoint, no connection, no Vertex AI billing — data stays in BigQuery.

> **Note:** `embeddinggemma-300m` is in Preview. When using `model`, you cannot specify `endpoint`, `model_params`, or `connection_id`.

```python
query = """
SELECT
  text_a,
  text_b,
  AI.SIMILARITY(
    content1 => text_a,
    content2 => text_b,
    model => 'embeddinggemma-300m'
  ) AS similarity
FROM
  UNNEST(['machine learning', 'deep learning', 'cooking recipes']) AS text_a,
  UNNEST(['artificial intelligence', 'neural networks', 'baking bread']) AS text_b
ORDER BY similarity DESC
"""
client.query(query).to_dataframe()
```

---
## Multimodal — Document and Cross-Modal Similarity

`AI.SIMILARITY` supports image-to-image and text-to-image comparison using `multimodalembedding@001`. A `connection_id` is required. The function uses the inline ObjectRef pipeline to access images from GCS.

> **New:** `gemini-embedding-2-preview` (Preview) supports PDF comparison directly — no rendering to PNG needed. The examples below use the GA `multimodalembedding@001` approach with rendered PNGs.

Below we render invoice and receipt PDFs from this project's `data/documents` (document set) to PNG images, then compare them directly and cross-modally with text.

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

# Pick 2 invoices and 2 receipts
docs = [
    ('invoice_1.png', data_dir / 'invoices' / 'invoice_001.pdf'),
    ('invoice_2.png', data_dir / 'invoices' / 'invoice_002.pdf'),
    ('receipt_1.png', data_dir / 'receipts' / 'receipt_001.pdf'),
    ('receipt_2.png', data_dir / 'receipts' / 'receipt_002.pdf'),
]

gcs = storage.Client(project=PROJECT_ID)
bucket = gcs.bucket(BUCKET)
prefix = 'bq_ai_functions/ai_similarity'

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

### 6. Document-to-document similarity

Compare two document images using inline ObjectRef. The function embeds both with `multimodalembedding@001` and returns cosine similarity. Same-type documents (invoice vs invoice) should score higher than cross-type pairs.

```python
# Compare an invoice pair vs an invoice-receipt pair
for label, doc_a, doc_b in [
    ('invoice vs invoice', 'invoice_1.png', 'invoice_2.png'),
    ('invoice vs receipt', 'invoice_1.png', 'receipt_1.png'),
]:
    query = f"""
    SELECT
      AI.SIMILARITY(
        content1 => OBJ.GET_ACCESS_URL(
          OBJ.FETCH_METADATA(
            OBJ.MAKE_REF('gs://{BUCKET}/bq_ai_functions/ai_similarity/{doc_a}', '{PROJECT_ID}.{LOCATION}.{CONNECTION_ID}')
          ), 'r'),
        content2 => OBJ.GET_ACCESS_URL(
          OBJ.FETCH_METADATA(
            OBJ.MAKE_REF('gs://{BUCKET}/bq_ai_functions/ai_similarity/{doc_b}', '{PROJECT_ID}.{LOCATION}.{CONNECTION_ID}')
          ), 'r'),
        endpoint => 'multimodalembedding@001',
        connection_id => '{PROJECT_ID}.{LOCATION}.{CONNECTION_ID}'
      ) AS similarity
    """
    df = client.query(query).to_dataframe()
    print(f'{label} ({doc_a} vs {doc_b}): {df.iloc[0]["similarity"]:.4f}')
```

### 7. Cross-modal similarity (text to document)

Compare text descriptions against document images. Multimodal embeddings live in a shared vector space, so text and images can be compared directly. Each description should match its corresponding document type.

```python
query = f"""
SELECT
  description,
  doc_name,
  ROUND(AI.SIMILARITY(
    content1 => description,
    content2 => OBJ.GET_ACCESS_URL(
      OBJ.FETCH_METADATA(
        OBJ.MAKE_REF(
          CONCAT('gs://{BUCKET}/bq_ai_functions/ai_similarity/', doc_name),
          '{PROJECT_ID}.{LOCATION}.{CONNECTION_ID}'
        )
      ), 'r'),
    endpoint => 'multimodalembedding@001',
    connection_id => '{PROJECT_ID}.{LOCATION}.{CONNECTION_ID}'
  ), 4) AS similarity
FROM
  UNNEST(['a business invoice for services rendered', 'a store receipt for purchased items']) AS description,
  UNNEST(['invoice_1.png', 'invoice_2.png', 'receipt_1.png', 'receipt_2.png']) AS doc_name
ORDER BY description, similarity DESC
"""
client.query(query).to_dataframe()
```

---
## Examples — `%%bigquery` Magics

The same examples using IPython magic commands. Magics let you write SQL directly in notebook cells without Python string wrapping.

Key patterns:
- `%%bigquery` — run SQL, display results inline
- `%%bigquery df` — run SQL, capture results into a pandas DataFrame

### Similarity with `%%bigquery`

```sql
%%bigquery --project {PROJECT_ID}

SELECT
  text_a,
  text_b,
  AI.SIMILARITY(
    content1 => text_a,
    content2 => text_b,
    endpoint => 'text-embedding-005'
  ) AS similarity
FROM
  UNNEST(['machine learning', 'cooking']) AS text_a,
  UNNEST(['artificial intelligence', 'baking']) AS text_b
ORDER BY similarity DESC
```

---
## Examples — BigFrames

`AI.SIMILARITY` has no direct BigFrames equivalent. Use `session.read_gbq_query()` to execute AI.SIMILARITY SQL from BigFrames.

```python
import bigframes.pandas as bpd

bpd.options.bigquery.project = PROJECT_ID
bpd.options.bigquery.location = LOCATION
```

### Running AI.SIMILARITY via read_gbq_query

```python
query = """
SELECT
  AI.SIMILARITY(
    content1 => 'data warehouse',
    content2 => 'analytics platform',
    endpoint => 'text-embedding-005'
  ) AS similarity
"""
df = bpd.read_gbq_query(query)
df.to_pandas()
```
