> **⚠️ NOT CURRENTLY WORKING:** The `AI.PARSE_DOCUMENT` function (preview) has been temporarily taken offline for revision (as of 2026-06-01). See the [BigQuery release notes](https://cloud.google.com/bigquery/docs/release-notes) for status. This notebook will not run successfully until the function is re-enabled.

# AI.PARSE_DOCUMENT — BigQuery AI Functions

`AI.PARSE_DOCUMENT` is a table-valued function that parses documents using the Document AI Layout Parser. It combines OCR, layout parsing, and chunking into a single SQL function call — no `CREATE MODEL` step required.

**When to use it:**
- You need to extract text from PDFs, images, or Office documents stored in Cloud Storage
- You want to parse specific documents by GCS URI without creating an object table (using ObjectRef)
- You're building a RAG (Retrieval-Augmented Generation) pipeline and need document chunks
- You want a simpler alternative to `ML.PROCESS_DOCUMENT` that skips the remote model creation step

**Alternatives:**
- `functions/ml_process_document` (`ML.PROCESS_DOCUMENT`) — Requires `CREATE MODEL` with a Document AI remote service, but supports all processor types (invoice parser, form parser, OCR, custom extractors). Use when you need specialized extraction beyond layout parsing.

**Key differences from ML.PROCESS_DOCUMENT:**
- `AI.PARSE_DOCUMENT` uses the `endpoint` parameter to point directly to a Document AI processor — **no `CREATE MODEL` needed**
- `AI.PARSE_DOCUMENT` supports both object tables and **inline ObjectRef** (`OBJ.MAKE_REF` as `ref` column) — no object table required for ad-hoc parsing
- `ML.PROCESS_DOCUMENT` requires creating a remote model with `REMOTE_SERVICE_TYPE = 'CLOUD_AI_DOCUMENT_V1'`
- `AI.PARSE_DOCUMENT` is **Layout Parser only** — it returns chunks (`chunk_id`, `start_page`, `end_page`, `content`)
- `ML.PROCESS_DOCUMENT` supports **all Document AI processor types** (invoice, receipt, form, OCR, custom)

**Featured in:** `workflows/document_rag` (Document RAG Pipeline)

**References:** `RESOURCES.md` (Full syntax reference) | [Official documentation](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-parse-document) | `setup` (Setup guide)

---
## Setup

Set your project and location, authenticate, and create shared resources.

> This function requires: (1) a **Cloud resource connection** with Document AI and Storage roles, (2) a **Document AI Layout Parser processor**, and (3) an **object table** pointing to documents in Cloud Storage. No `CREATE MODEL` step is needed. See the `setup` (Setup Reference) for details.

```python
PROJECT_ID = 'statmike-mlops-349915'  # <-- Replace with your project ID
LOCATION = 'US'  # BigQuery dataset location
DATASET_ID = 'bq_ai_functions'  # Shared dataset across all notebooks
CONNECTION_ID = 'bq_ai_functions'  # Shared connection
BUCKET = PROJECT_ID  # GCS bucket for document storage
```

### Environment

> **Already set up the project environment?** Skip to [Examples](#examples--sql).  
> **Running standalone** (Colab, Colab Enterprise, Vertex AI Workbench)? Run the cells below to install packages, authenticate, and create the shared dataset. See the `setup` (Setup Reference) for details.

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
for role in ['roles/aiplatform.user', 'roles/storage.objectViewer', 'roles/documentai.apiUser']:
    _sp.run(['gcloud', 'projects', 'add-iam-policy-binding', PROJECT_ID,
             f'--member=serviceAccount:{sa}', f'--role={role}', '--quiet'],
            capture_output=True, text=True)
print(f'Connection {CONNECTION_ID} ready (SA: {sa})')
```

```python
from google.cloud import documentai_v1 as documentai

docai_client = documentai.DocumentProcessorServiceClient()
parent = docai_client.common_location_path(PROJECT_ID, 'us')

# Check for existing layout parser processor (idempotent)
PROCESSOR_DISPLAY_NAME = 'bq_ai_functions_layout_parser'
processor = None
for p in docai_client.list_processors(parent=parent):
    if p.display_name == PROCESSOR_DISPLAY_NAME:
        processor = p
        break

if processor is None:
    processor = docai_client.create_processor(
        parent=parent,
        processor=documentai.Processor(
            display_name=PROCESSOR_DISPLAY_NAME,
            type_='LAYOUT_PARSER_PROCESSOR',
        ),
    )

PROCESSOR_ID = processor.name
print(f'Layout Parser processor ready: {PROCESSOR_ID}')
```

### Upload documents and create object table

Upload 10 sample invoices to Cloud Storage and create an object table to reference them from BigQuery.

```python
from google.cloud import storage
from pathlib import Path
from tqdm import tqdm

gcs = storage.Client(project=PROJECT_ID)
bucket = gcs.bucket(BUCKET)
prefix = 'bq_ai_functions/ai_parse_document'

data_dir = Path('../../data/documents/invoices')
if not data_dir.exists():
    data_dir = Path('data/documents/invoices')

files = sorted(data_dir.glob('*.pdf'))[:10]
uploaded, skipped = 0, 0
for f in tqdm(files, desc='Uploading'):
    blob = bucket.blob(f'{prefix}/{f.name}')
    if blob.exists():
        skipped += 1
    else:
        blob.upload_from_filename(str(f))
        uploaded += 1
print(f'Uploaded {uploaded} documents, skipped {skipped} (already exist)')
print(f'Location: gs://{BUCKET}/{prefix}/')
```

```python
client.query(f"""
CREATE OR REPLACE EXTERNAL TABLE `{PROJECT_ID}.{DATASET_ID}.ai_parse_document_invoices`
WITH CONNECTION `{PROJECT_ID}.{LOCATION}.{CONNECTION_ID}`
OPTIONS (
  object_metadata = 'SIMPLE',
  uris = ['gs://{BUCKET}/{prefix}/*.pdf']
)
""").result()

df = client.query(f"""
  SELECT uri, content_type, size
  FROM `{PROJECT_ID}.{DATASET_ID}.ai_parse_document_invoices`
  ORDER BY uri
""").to_dataframe()
print(f'Object table ai_parse_document_invoices ready — {len(df)} documents')
df.head()
```

---
## Examples — SQL

Progressive examples from simplest to most advanced. Each cell adds one new concept.

`AI.PARSE_DOCUMENT` is a **table-valued function** — it returns a table of chunks. Use it in `FROM` clauses, like `VECTOR_SEARCH` or `AI.GENERATE_TABLE`.

### 1. Parse a single document — discover output columns

Use `SELECT *` with a `LIMIT` subquery to see all columns `AI.PARSE_DOCUMENT` returns: the chunking columns (`chunk_id`, `start_page`, `end_page`, `content`) plus all columns from the input object table.

```python
query = f"""
SELECT *
FROM AI.PARSE_DOCUMENT(
  (SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.ai_parse_document_invoices` ORDER BY uri LIMIT 1),
  endpoint => '{PROCESSOR_ID}'
)
"""
df = client.query(query).to_dataframe()
print(f'Columns: {list(df.columns)}')
print(f'Chunks: {len(df)}')
df.head()
```

### 2. Select specific output fields

The key output columns are `chunk_id`, `start_page`, `end_page`, and `content`. Select just the fields you need.

```python
query = f"""
SELECT
  uri,
  chunk_id,
  start_page,
  end_page,
  LEFT(content, 200) AS content_preview
FROM AI.PARSE_DOCUMENT(
  (SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.ai_parse_document_invoices` ORDER BY uri LIMIT 3),
  endpoint => '{PROCESSOR_ID}'
)
ORDER BY uri, chunk_id
"""
client.query(query).to_dataframe()
```

### 3. Custom chunk_size — smaller chunks for RAG

The `chunk_size` parameter controls how the Layout Parser splits document text into chunks. Smaller chunks (e.g., 250) improve retrieval precision in RAG pipelines. The default is approximately 1000 characters.

```python
query = f"""
SELECT
  uri,
  chunk_id,
  start_page,
  end_page,
  LENGTH(content) AS chunk_length,
  LEFT(content, 100) AS content_preview
FROM AI.PARSE_DOCUMENT(
  (SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.ai_parse_document_invoices` ORDER BY uri LIMIT 3),
  endpoint => '{PROCESSOR_ID}',
  chunk_size => 250
)
ORDER BY uri, chunk_id
"""
df = client.query(query).to_dataframe()
print(f'Total chunks with chunk_size=250: {len(df)} (vs fewer with default ~1000)')
df
```

### 4. Subquery filtering — parse specific documents

Use a subquery to filter which documents to process, avoiding unnecessary parsing of the entire object table.

```python
query = f"""
SELECT
  uri,
  chunk_id,
  LEFT(content, 200) AS content_preview
FROM AI.PARSE_DOCUMENT(
  (SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.ai_parse_document_invoices`
   WHERE uri LIKE '%invoice_001%' OR uri LIKE '%invoice_005%'),
  endpoint => '{PROCESSOR_ID}'
)
ORDER BY uri, chunk_id
"""
client.query(query).to_dataframe()
```

### 5. Persist results — avoid re-parsing

Save parsed output to a regular BigQuery table. This avoids re-processing documents on every query and lets you build indexes for search.

```python
query = f"""
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.ai_parse_document_results` AS
SELECT
  uri,
  chunk_id,
  start_page,
  end_page,
  content
FROM AI.PARSE_DOCUMENT(
  TABLE `{PROJECT_ID}.{DATASET_ID}.ai_parse_document_invoices`,
  endpoint => '{PROCESSOR_ID}'
)
"""
client.query(query).result()

df = client.query(f"""
  SELECT COUNT(*) AS total_chunks, COUNT(DISTINCT uri) AS documents
  FROM `{PROJECT_ID}.{DATASET_ID}.ai_parse_document_results`
""").to_dataframe()
print(f'Persisted {df.iloc[0]["total_chunks"]} chunks from {df.iloc[0]["documents"]} documents')
```

### 6. Using connection_id — service account credentials

Use the `connection_id` parameter to authenticate with a service account instead of end-user credentials — useful for shared environments and production pipelines.

```python
query = f"""
SELECT
  uri,
  chunk_id,
  LEFT(content, 200) AS content_preview
FROM AI.PARSE_DOCUMENT(
  (SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.ai_parse_document_invoices` ORDER BY uri LIMIT 2),
  endpoint => '{PROCESSOR_ID}',
  connection_id => '{PROJECT_ID}.{LOCATION}.{CONNECTION_ID}'
)
ORDER BY uri, chunk_id
"""
client.query(query).to_dataframe()
```

### 7. ObjectRef — parse a document without an object table

`AI.PARSE_DOCUMENT` requires a `ref` column in its input. Object tables provide this automatically, but you can construct it inline using `OBJ.MAKE_REF` — no object table creation needed.

This is useful for ad-hoc parsing of specific documents when you know the GCS URI.

```python
# Parse a single document using ObjectRef — no object table needed
test_uri = f'gs://{BUCKET}/{prefix}/invoice_001.pdf'

query = f"""
SELECT
  uri,
  chunk_id,
  start_page,
  end_page,
  LEFT(content, 200) AS content_preview
FROM AI.PARSE_DOCUMENT(
  (SELECT
    '{test_uri}' AS uri,
    OBJ.MAKE_REF('{test_uri}', '{PROJECT_ID}.{LOCATION}.{CONNECTION_ID}') AS ref
  ),
  endpoint => '{PROCESSOR_ID}'
)
"""
client.query(query).to_dataframe()
```

### 8. ObjectRef — parse multiple documents with UNNEST

Use `UNNEST` to create rows from an array of GCS URIs, then add a `ref` column with `OBJ.MAKE_REF`. This parses multiple documents without creating an object table.

```python
# Parse multiple documents using ObjectRef + UNNEST
uris = [f'gs://{BUCKET}/{prefix}/invoice_{i:03d}.pdf' for i in range(1, 4)]
uris_sql = ', '.join(f"'{u}'" for u in uris)

query = f"""
SELECT
  uri,
  chunk_id,
  LEFT(content, 200) AS content_preview
FROM AI.PARSE_DOCUMENT(
  (SELECT
    uri,
    OBJ.MAKE_REF(uri, '{PROJECT_ID}.{LOCATION}.{CONNECTION_ID}') AS ref
  FROM UNNEST([{uris_sql}]) AS uri),
  endpoint => '{PROCESSOR_ID}'
)
ORDER BY uri, chunk_id
"""
df = client.query(query).to_dataframe()
print(f'Parsed {df["uri"].nunique()} documents into {len(df)} chunks')
df
```

---
## Examples — `%%bigquery` Magics

The same examples using IPython magic commands. Magics let you write SQL directly in notebook cells without Python string wrapping.

**Note:** The `endpoint` parameter requires a processor ID that varies per environment, so the magics example below queries the persisted results table from Example 5. To use `AI.PARSE_DOCUMENT` directly in magics, hardcode the processor endpoint in the SQL.

### Parse and preview chunks

```sql
%%bigquery --project {PROJECT_ID}

SELECT
  uri,
  chunk_id,
  start_page,
  end_page,
  LEFT(content, 150) AS content_preview
FROM `statmike-mlops-349915.bq_ai_functions.ai_parse_document_results`
ORDER BY uri, chunk_id
LIMIT 10
```

---
## Examples — BigFrames

There is no native BigFrames API for `AI.PARSE_DOCUMENT` yet. Use `session.read_gbq_query()` to execute AI.PARSE_DOCUMENT queries and get results as a BigFrames DataFrame.

```python
import bigframes.pandas as bpd

bpd.close_session()  # Reset session to apply connection settings
bpd.options.bigquery.project = PROJECT_ID
bpd.options.bigquery.location = LOCATION
```

### AI.PARSE_DOCUMENT via `read_gbq_query()`

```python
query = f"""
SELECT
  uri,
  chunk_id,
  start_page,
  end_page,
  LEFT(content, 150) AS content_preview
FROM AI.PARSE_DOCUMENT(
  (SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.ai_parse_document_invoices` ORDER BY uri LIMIT 2),
  endpoint => '{PROCESSOR_ID}'
)
ORDER BY uri, chunk_id
"""
bf_df = bpd.read_gbq_query(query)
bf_df.to_pandas()
```
