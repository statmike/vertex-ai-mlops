# ML.PROCESS_DOCUMENT — BigQuery AI Functions

`ML.PROCESS_DOCUMENT` is a table-valued function that processes documents stored in Cloud Storage using the Document AI API. It sends PDFs, images, and other documents (referenced via a BigQuery object table) to a Document AI processor and returns structured extraction results — entities, key-value pairs, and parsed fields — directly as BigQuery columns.

**When to use it:**
- You need to extract structured data from invoices, receipts, forms, or other documents at scale
- You want to process documents stored in Cloud Storage without leaving BigQuery
- You need OCR, form parsing, or document layout analysis within SQL queries

**Alternatives:**
- `functions/ai_generate` (`AI.GENERATE`) — Multimodal Gemini prompts for ad-hoc document understanding (no Document AI processor required)

**Limits:**
- Up to **130 pages** per document (pages beyond this are not processed)
- **120-second** timeout per document processing request
- Documents are processed in **batches of 10**

**References:** `RESOURCES.md` (Full syntax reference) | [Official documentation](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-process-document) | `setup` (Setup guide)

---
## Setup

This function requires several resources: a connection, a Document AI processor, a remote model pointing to the processor, documents uploaded to Cloud Storage, and an object table referencing those documents.

> See the `setup` (Setup Reference) for details on connections, remote models, object tables, and Document AI processors.

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

# Get service account
r = _sp.run(['bq', 'show', '--connection', '--format=json',
             '--project_id', PROJECT_ID, '--location', LOCATION, CONNECTION_ID],
            capture_output=True, text=True, check=True)
sa = _json.loads(r.stdout)['cloudResource']['serviceAccountId']

# Grant required roles to connection service account
for role in ['roles/aiplatform.user', 'roles/storage.objectViewer', 'roles/documentai.apiUser', 'roles/documentai.viewer']:
    _sp.run(['gcloud', 'projects', 'add-iam-policy-binding', PROJECT_ID,
             f'--member=serviceAccount:{sa}', f'--role={role}', '--quiet'],
            capture_output=True, text=True)
print(f'Connection {CONNECTION_ID} ready (SA: {sa})')
```

```python
# give permissions time to propogate
import time
time.sleep(60)
```

### Step 1 — Upload invoices to GCS

Upload 50 synthetic invoice PDFs to Cloud Storage. The invoices are in the `data/documents/invoices/` directory of this repository.

> **Running from a repo checkout?** The cell below resolves the path automatically.
> **Running in Colab?** Clone the repo first: `!git clone https://github.com/statmike/vertex-ai-mlops.git`

```python
from google.cloud import storage
from pathlib import Path
from tqdm import tqdm

storage_client = storage.Client(project=PROJECT_ID)
bucket = storage_client.bucket(BUCKET)

# Resolve local path to invoice PDFs
local_dir = Path('../../data/documents/invoices')
if not local_dir.exists():
    local_dir = Path('vertex-ai-mlops/data+ai/bq-ai-functions/data/documents/invoices')
assert local_dir.exists(), f'Invoice directory not found. Clone the repo or adjust the path.'

gcs_prefix = 'bq_ai_functions/ml_process_document/'
pdfs = sorted(local_dir.glob('*.pdf'))

uploaded = 0
for pdf in tqdm(pdfs, desc='Uploading invoices'):
    blob_name = f'{gcs_prefix}{pdf.name}'
    blob = bucket.blob(blob_name)
    if not blob.exists():
        blob.upload_from_filename(str(pdf))
        uploaded += 1

print(f'Uploaded {uploaded} new files ({len(pdfs)} total in gs://{BUCKET}/{gcs_prefix})')
```

### Step 2 — Create object table

An [object table](https://cloud.google.com/bigquery/docs/object-table-introduction) is an external table that references unstructured data (PDFs, images, etc.) in Cloud Storage. ML.PROCESS_DOCUMENT reads documents through the object table.

```python
# Create object table over the uploaded invoices
client.query(f'''
CREATE OR REPLACE EXTERNAL TABLE `{PROJECT_ID}.{DATASET_ID}.ml_process_document_invoices`
  WITH CONNECTION `{PROJECT_ID}.{LOCATION}.{CONNECTION_ID}`
  OPTIONS (
    object_metadata = 'SIMPLE',
    uris = ['gs://{BUCKET}/bq_ai_functions/ml_process_document/*']
  )
''').result()
print('Object table ml_process_document_invoices ready')

# Verify — show a few rows
client.query(f'''
SELECT uri, content_type, size
FROM `{PROJECT_ID}.{DATASET_ID}.ml_process_document_invoices`
ORDER BY uri
LIMIT 5
''').to_dataframe()
```

### Step 3 — Create Document AI processor and remote model

ML.PROCESS_DOCUMENT requires a remote model that points to a [Document AI processor](https://cloud.google.com/document-ai/docs/overview). The processor determines what type of extraction to perform (invoice parsing, OCR, form parsing, etc.).

We create an Invoice Parser processor via the `google-cloud-documentai` Python client, then create a BigQuery remote model that references it.

```python
from google.cloud import documentai_v1 as documentai

docai_client = documentai.DocumentProcessorServiceClient()
parent = docai_client.common_location_path(PROJECT_ID, 'us')

# Check if processor already exists (idempotent)
existing = [
    p for p in docai_client.list_processors(parent=parent)
    if p.display_name == 'bq_ai_functions_invoice_parser'
]

if existing:
    processor = existing[0]
    print(f'Processor already exists: {processor.name}')
else:
    processor = docai_client.create_processor(
        parent=parent,
        processor=documentai.Processor(
            display_name='bq_ai_functions_invoice_parser',
            type_='INVOICE_PROCESSOR',
        ),
    )
    print(f'Created processor: {processor.name}')

PROCESSOR_NAME = processor.name
```

```python
# Create remote model pointing to the Document AI processor
client.query(f'''
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.ml_process_document_invoice_parser`
  REMOTE WITH CONNECTION `{PROJECT_ID}.{LOCATION}.{CONNECTION_ID}`
  OPTIONS (
    REMOTE_SERVICE_TYPE = 'CLOUD_AI_DOCUMENT_V1',
    DOCUMENT_PROCESSOR = '{PROCESSOR_NAME}'
  )
''').result()
print('Model ml_process_document_invoice_parser ready')
```

---
## Examples — SQL

Progressive examples using ML.PROCESS_DOCUMENT to extract data from invoices.

### 1. Process a single invoice — discover output columns

Process one invoice with `SELECT *` to see all columns the Invoice Parser returns. This is useful for discovering processor-specific fields.

```python
query = f'''
SELECT *
FROM ML.PROCESS_DOCUMENT(
  MODEL `{PROJECT_ID}.{DATASET_ID}.ml_process_document_invoice_parser`,
  (SELECT *
   FROM `{PROJECT_ID}.{DATASET_ID}.ml_process_document_invoices`
   ORDER BY uri
   LIMIT 1)
)
'''
df = client.query(query).to_dataframe()
print('Columns returned:', list(df.columns))
df
```

### 2. Extract specific invoice fields

Select only the processor-specific columns you need. The Invoice Parser returns many fields — `invoice_id`, `supplier_name`, `receiver_name`, `total_amount`, `net_amount`, `total_tax_amount`, `currency`, `invoice_date`, `due_date`, `line_item`, and more. Use Example 1's `SELECT *` output to discover all available columns.

```python
query = f'''
SELECT
  uri,
  invoice_id,
  supplier_name,
  total_amount,
  currency,
  invoice_date,
  due_date
FROM ML.PROCESS_DOCUMENT(
  MODEL `{PROJECT_ID}.{DATASET_ID}.ml_process_document_invoice_parser`,
  (SELECT *
   FROM `{PROJECT_ID}.{DATASET_ID}.ml_process_document_invoices`
   ORDER BY uri
   LIMIT 5)
)
'''
client.query(query).to_dataframe()
```

### 3. Process all 50 invoices

Process every invoice in the object table. Extract key fields and display as a table.

```python
query = f'''
SELECT
  uri,
  invoice_id,
  supplier_name,
  total_amount,
  currency,
  invoice_date,
  due_date,
  ml_process_document_status
FROM ML.PROCESS_DOCUMENT(
  MODEL `{PROJECT_ID}.{DATASET_ID}.ml_process_document_invoice_parser`,
  TABLE `{PROJECT_ID}.{DATASET_ID}.ml_process_document_invoices`
)
ORDER BY uri
'''
df_all = client.query(query).to_dataframe()
print(f'{len(df_all)} invoices processed')
df_all
```

### 4. Persist results to a table

Use `CREATE TABLE ... AS SELECT` to save extraction output. This avoids re-processing documents and makes results queryable by other users.

```python
query = f'''
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.ml_process_document_results` AS
SELECT
  uri,
  invoice_id,
  supplier_name,
  total_amount,
  currency,
  invoice_date,
  due_date
FROM ML.PROCESS_DOCUMENT(
  MODEL `{PROJECT_ID}.{DATASET_ID}.ml_process_document_invoice_parser`,
  TABLE `{PROJECT_ID}.{DATASET_ID}.ml_process_document_invoices`
)
'''
client.query(query).result()
print('Results persisted to ml_process_document_results')

# Verify
client.query(f'''
SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.ml_process_document_results`
ORDER BY uri
LIMIT 5
''').to_dataframe()
```

### 5. Using PROCESS_OPTIONS — page selection

Use `PROCESS_OPTIONS` to control which pages to process. The `fromStart` option processes only the first N pages of each document.

```python
query = f'''
SELECT
  uri,
  invoice_id,
  supplier_name,
  total_amount
FROM ML.PROCESS_DOCUMENT(
  MODEL `{PROJECT_ID}.{DATASET_ID}.ml_process_document_invoice_parser`,
  (SELECT *
   FROM `{PROJECT_ID}.{DATASET_ID}.ml_process_document_invoices`
   ORDER BY uri
   LIMIT 3),
  PROCESS_OPTIONS => JSON '{{"fromStart": 1}}'
)
'''
client.query(query).to_dataframe()
```

---
## Examples — `%%bigquery` Magics

`%%bigquery` magics cannot interpolate Python variables in the SQL body. Since ML.PROCESS_DOCUMENT requires `MODEL` and `TABLE` references with project/dataset, most examples are better run via `client.query()` with f-strings. Here we show one example with hardcoded references.

### Process invoices with `%%bigquery`

```sql
%%bigquery --project {PROJECT_ID}

SELECT
  uri,
  invoice_id,
  supplier_name,
  total_amount
FROM ML.PROCESS_DOCUMENT(
  MODEL `statmike-mlops-349915.bq_ai_functions.ml_process_document_invoice_parser`,
  (SELECT *
   FROM `statmike-mlops-349915.bq_ai_functions.ml_process_document_invoices`
   ORDER BY uri
   LIMIT 3)
)
```

---
## Examples — BigFrames

ML.PROCESS_DOCUMENT has no BigFrames equivalent. Use `session.read_gbq_query()` to execute the SQL from BigFrames.

```python
import bigframes.pandas as bpd

bpd.options.bigquery.project = PROJECT_ID
bpd.options.bigquery.location = LOCATION

session = bpd.get_global_session()
df_bf = session.read_gbq_query(f'''
SELECT
  uri,
  invoice_id,
  supplier_name,
  total_amount,
  currency
FROM ML.PROCESS_DOCUMENT(
  MODEL `{PROJECT_ID}.{DATASET_ID}.ml_process_document_invoice_parser`,
  (SELECT *
   FROM `{PROJECT_ID}.{DATASET_ID}.ml_process_document_invoices`
   ORDER BY uri
   LIMIT 5)
)
''')
df_bf.to_pandas()
```
