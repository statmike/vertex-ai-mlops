# Multimodal Analysis — BigQuery AI Functions

An end-to-end document analysis pipeline that composes AI functions with multimodal embeddings:

1. **Render** invoice and receipt PDFs to PNG images and upload to GCS
2. **Embed** all documents with `AI.EMBED` using `multimodalembedding@001`
3. **Find similar pairs** via cosine distance on embeddings (SQL)
4. **Cross-modal matching** — compare text descriptions to document images with `AI.SIMILARITY`
5. **Describe** the most similar document pair with `AI.GENERATE`

**What this demonstrates:**
- Multimodal embeddings: creating document image vectors with `multimodalembedding@001`
- Document-to-document similarity via embedding distance — same-type documents cluster together
- Cross-modal text-to-image similarity — text and images share a vector space
- Visual description with multimodal `AI.GENERATE`
- The inline ObjectRef pipeline: `OBJ.MAKE_REF` → `OBJ.FETCH_METADATA` → `OBJ.GET_ACCESS_URL`

**Functions used:** `functions/ai_embed` (`AI.EMBED`) | `functions/ai_similarity` (`AI.SIMILARITY`) | `functions/ai_generate` (`AI.GENERATE`)

**Prerequisites:** `setup` (Setup guide) | `RESOURCES.md` (Function reference)

---
## Setup

Set your project and location, authenticate, and create shared resources.

> This workflow uses `AI.EMBED` and `AI.SIMILARITY` with multimodal endpoints (requires connection + `storage.objectViewer`), and `AI.GENERATE` for visual descriptions. See the `setup` (Setup Reference) for details.

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
## Step 1 — Render documents and upload to GCS

Render invoice and receipt PDFs from this project's `data/documents` (document set) to PNG images using `pdftoppm`, then upload to GCS. The `multimodalembedding@001` endpoint supports images (not PDFs), so this rendering step is required.

```python
import shutil, subprocess

if not shutil.which('pdftoppm'):
    subprocess.check_call(['sudo', 'apt-get', 'install', '-y', '-qq', 'poppler-utils'])
    print('Installed poppler-utils (provides pdftoppm)')
else:
    print('pdftoppm already available')
```

```python
import subprocess as sp
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
prefix = 'bq_ai_functions/multimodal_analysis'

for name, pdf_path in docs:
    # Render first page of PDF to PNG using pdftoppm (poppler)
    result = sp.run(
        ['pdftoppm', '-png', '-f', '1', '-l', '1', '-r', '150', str(pdf_path)],
        capture_output=True
    )
    blob = bucket.blob(f'{prefix}/{name}')
    blob.upload_from_string(result.stdout, content_type='image/png')

print(f'Rendered and uploaded {len(docs)} document images to gs://{BUCKET}/{prefix}/')
```

---
## Step 2 — Embed documents with AI.EMBED

Create document image embeddings using `multimodalembedding@001` via the inline ObjectRef pipeline. Each image gets a 1408-dimension vector. Save results to a table for similarity computation.

```python
query = f"""
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.workflow_mm_embeddings` AS
SELECT
  doc_name,
  (AI.EMBED(
    content => OBJ.GET_ACCESS_URL(
      OBJ.FETCH_METADATA(
        OBJ.MAKE_REF(
          CONCAT('gs://{BUCKET}/bq_ai_functions/multimodal_analysis/', doc_name),
          '{PROJECT_ID}.{LOCATION}.{CONNECTION_ID}'
        )
      ), 'r'),
    endpoint => 'multimodalembedding@001',
    connection_id => '{PROJECT_ID}.{LOCATION}.{CONNECTION_ID}'
  )).result AS embedding
FROM UNNEST([
  'invoice_1.png', 'invoice_2.png', 'invoice_3.png',
  'receipt_1.png', 'receipt_2.png', 'receipt_3.png'
]) AS doc_name
"""
client.query(query).result()

# Verify
df = client.query(f"""
  SELECT doc_name, ARRAY_LENGTH(embedding) AS dims
  FROM `{PROJECT_ID}.{DATASET_ID}.workflow_mm_embeddings`
  ORDER BY doc_name
""").to_dataframe()
print(f'Embedded {len(df)} documents')
df
```

---
## Step 3 — Find similar document pairs

Compute cosine similarity between all embedding pairs using `ML.DISTANCE`. Documents of the same type (invoices vs receipts) should cluster together with higher similarity.

```python
query = f"""
SELECT
  a.doc_name AS doc_a,
  b.doc_name AS doc_b,
  ROUND(1 - ML.DISTANCE(a.embedding, b.embedding, 'COSINE'), 4) AS cosine_similarity
FROM `{PROJECT_ID}.{DATASET_ID}.workflow_mm_embeddings` a
CROSS JOIN `{PROJECT_ID}.{DATASET_ID}.workflow_mm_embeddings` b
WHERE a.doc_name < b.doc_name
ORDER BY cosine_similarity DESC
LIMIT 10
"""
pairs = client.query(query).to_dataframe()
print('Top 10 most similar document pairs:')
pairs
```

---
## Step 4 — Cross-modal similarity with AI.SIMILARITY

Compare text descriptions against document images. Multimodal embeddings place text and images in a shared vector space, so `AI.SIMILARITY` can measure how well a text description matches a document image. Each description should score highest against its matching document type.

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
          CONCAT('gs://{BUCKET}/bq_ai_functions/multimodal_analysis/', doc_name),
          '{PROJECT_ID}.{LOCATION}.{CONNECTION_ID}'
        )
      ), 'r'),
    endpoint => 'multimodalembedding@001',
    connection_id => '{PROJECT_ID}.{LOCATION}.{CONNECTION_ID}'
  ), 4) AS similarity
FROM
  UNNEST(['a business invoice', 'a store receipt']) AS description,
  UNNEST([
    'invoice_1.png', 'invoice_2.png', 'invoice_3.png',
    'receipt_1.png', 'receipt_2.png', 'receipt_3.png'
  ]) AS doc_name
ORDER BY description, similarity DESC
"""
cross_modal = client.query(query).to_dataframe()
print('Cross-modal similarity (text descriptions vs document images):')
cross_modal
```

---
## Step 5 — Describe documents with AI.GENERATE

Use `AI.GENERATE` with multimodal input to describe the most similar document pair and explain what makes them visually similar.

```python
# Get the most similar pair
top_pair = client.query(f"""
  SELECT a.doc_name AS doc_a, b.doc_name AS doc_b,
    ROUND(1 - ML.DISTANCE(a.embedding, b.embedding, 'COSINE'), 4) AS similarity
  FROM `{PROJECT_ID}.{DATASET_ID}.workflow_mm_embeddings` a
  CROSS JOIN `{PROJECT_ID}.{DATASET_ID}.workflow_mm_embeddings` b
  WHERE a.doc_name < b.doc_name
  ORDER BY similarity DESC
  LIMIT 1
""").to_dataframe()

doc_a = top_pair.iloc[0]['doc_a']
doc_b = top_pair.iloc[0]['doc_b']
sim = top_pair.iloc[0]['similarity']
print(f'Most similar pair: {doc_a} and {doc_b} (similarity: {sim})')

# Describe the pair
query = f"""
SELECT (AI.GENERATE(
  STRUCT(
    'Describe these two document images and explain what makes them visually similar. Be concise (2-3 sentences).' AS prompt,
    [OBJ.GET_ACCESS_URL(OBJ.FETCH_METADATA(OBJ.MAKE_REF('gs://{BUCKET}/bq_ai_functions/multimodal_analysis/{doc_a}', '{PROJECT_ID}.{LOCATION}.{CONNECTION_ID}')), 'r'),
     OBJ.GET_ACCESS_URL(OBJ.FETCH_METADATA(OBJ.MAKE_REF('gs://{BUCKET}/bq_ai_functions/multimodal_analysis/{doc_b}', '{PROJECT_ID}.{LOCATION}.{CONNECTION_ID}')), 'r')
    ] AS object_ref_runtime
  )
)).result AS description
"""
df = client.query(query).to_dataframe()
print(f'\nAI description of the most similar pair:')
print(df.iloc[0]['description'])
```
