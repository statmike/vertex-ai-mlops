# AI.GENERATE_INT — BigQuery AI Functions

`AI.GENERATE_INT` is a scalar function that returns a STRUCT containing an INT64 value per row. Use it for integer estimation, counting, and classification with numeric labels.

**When to use it:**
- You need integer outputs (counts, labels, ratings on integer scale)
- You want full control over model and parameters
- You need response metadata (full_response, status)

**Alternatives:**
- `functions/ai_generate_double` (`AI.GENERATE_DOUBLE`) — FLOAT64 output for continuous numeric values
- `functions/ai_generate_bool` (`AI.GENERATE_BOOL`) — BOOL output for true/false questions
- `functions/ai_generate` (`AI.GENERATE`) — Full control with output_schema for any structured output

**Multimodal:** Supports document, image, and video input via `RESOURCES.md#objectref-and-objectrefruntime-schema-reference` (ObjectRef). Pass a STRUCT prompt with ObjectRefRuntime fields to extract integer values from unstructured data.

**References:** `RESOURCES.md` (Full syntax reference) | [Official documentation](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-generate-int) | `setup` (Setup guide)

---
## Setup

Set your project and location, authenticate, and create a temporary dataset for this notebook.

> This function doesn't require a connection or model for SQL usage — it uses end-user credentials automatically. BigFrames requires a connection, so we reference the shared one here. See the `setup` (Setup Reference) for details.

```python
PROJECT_ID = 'statmike-mlops-349915'  # <-- Replace with your project ID
LOCATION = 'US'  # BigQuery dataset location
DATASET_ID = 'bq_ai_functions'  # Shared dataset across all notebooks
CONNECTION_ID = 'bq_ai_functions'  # Shared connection (used by BigFrames)
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

---
## Examples — SQL

Progressive examples from simplest to most advanced. Each cell adds one new concept.

### 1. Numeric fact retrieval

`AI.GENERATE_INT` returns a STRUCT with `result` (INT64), `full_response` (JSON), and `status` (STRING).

```python
query = """
SELECT
  country,
  (AI.GENERATE_INT(
    CONCAT('How many states or provinces does ', country, ' have? Return just the number.')
  )).result AS num_divisions
FROM UNNEST(['United States', 'Canada', 'Brazil', 'India', 'Australia']) AS country
"""
client.query(query).to_dataframe()
```

### 2. Integer scoring

Rate items on an integer scale.

```python
query = """
SELECT
  review,
  (AI.GENERATE_INT(
    CONCAT('Rate this product review on a scale of 1 to 5 stars: ', review)
  )).result AS stars
FROM UNNEST([
  'Best purchase I have made this year!',
  'Complete waste of money.',
  'Decent product, does what it says.',
  'Exceeded my expectations in every way!',
  'Not great, not terrible.'
]) AS review
ORDER BY stars DESC
"""
client.query(query).to_dataframe()
```

### 3. Counting and estimation

```python
query = """
SELECT
  sentence,
  (AI.GENERATE_INT(
    CONCAT('How many words are in this sentence? Just the number: ', sentence)
  )).result AS word_count
FROM UNNEST([
  'The quick brown fox jumps over the lazy dog.',
  'Hello world.',
  'BigQuery is a fully managed enterprise data warehouse.'
]) AS sentence
"""
client.query(query).to_dataframe()
```

### 4. With endpoint

```python
query = """
SELECT
  element,
  (AI.GENERATE_INT(
    CONCAT('What is the atomic number of ', element, '?'),
    endpoint => 'gemini-2.5-flash'
  )).result AS atomic_number
FROM UNNEST(['Hydrogen', 'Carbon', 'Oxygen', 'Iron', 'Gold']) AS element
"""
client.query(query).to_dataframe()
```

---
## Examples — Multimodal with ObjectRef

`AI.GENERATE_INT` can analyze documents, images, and video stored in Cloud Storage. Use the **ObjectRef pipeline** to create a STRUCT prompt with signed references:

```
OBJ.MAKE_REF(uri, connection)        → ObjectRef
  → OBJ.FETCH_METADATA(objectref)    → adds content type and size
    → OBJ.GET_ACCESS_URL(ref, 'r')   → ObjectRefRuntime (signed URL)
```

The STRUCT replaces the STRING prompt. See the `RESOURCES.md#objectref-and-objectrefruntime-schema-reference` (ObjectRef reference) for details.

```python
import subprocess as _sp, json as _json
from google.cloud import storage as _storage
from pathlib import Path

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

# Upload invoice for the multimodal example
_gcs = _storage.Client(project=PROJECT_ID)
_bucket = _gcs.bucket(BUCKET)
_prefix = 'bq_ai_functions/ai_generate_int'

_data = Path('../../data/documents')
if not _data.exists():
    _data = Path('data/documents')

blob = _bucket.blob(f'{_prefix}/invoice_001.pdf')
if not blob.exists():
    blob.upload_from_filename(str(_data / 'invoices' / 'invoice_001.pdf'))
    print(f'Uploaded invoice_001.pdf → gs://{BUCKET}/{_prefix}/invoice_001.pdf')
else:
    print(f'Already exists: gs://{BUCKET}/{_prefix}/invoice_001.pdf')
```

### 5. Count items in a document

Pass a document via ObjectRef in a STRUCT prompt to extract an integer value.

```python
query = f"""
SELECT
  (AI.GENERATE_INT(
    STRUCT(
      'How many line items are on this invoice?' AS prompt,
      [OBJ.GET_ACCESS_URL(
        OBJ.FETCH_METADATA(
          OBJ.MAKE_REF(
            'gs://{BUCKET}/bq_ai_functions/ai_generate_int/invoice_001.pdf',
            '{PROJECT_ID}.{LOCATION}.{CONNECTION_ID}'
          )
        ), 'r'
      )] AS object_ref_runtime
    )
  )).result AS line_item_count
"""
client.query(query).to_dataframe()
```

---
## Examples — `%%bigquery` Magics

The same examples using IPython magic commands. Magics let you write SQL directly in notebook cells without Python string wrapping.

Key patterns:
- `%%bigquery` — run SQL, display results inline
- `%%bigquery df` — run SQL, capture results into a pandas DataFrame

### AI.GENERATE_INT with `%%bigquery`

```sql
%%bigquery --project {PROJECT_ID}

SELECT
  country,
  (AI.GENERATE_INT(
    CONCAT('How many official languages does ', country, ' have?')
  )).result AS num_languages
FROM UNNEST(['Switzerland', 'Canada', 'India', 'Japan']) AS country
```

---
## Examples — BigFrames

BigFrames wraps `AI.GENERATE_INT` via `bbq.ai.generate_int()`. Returns a Series of structs.

```python
import bigframes.pandas as bpd
import bigframes.bigquery as bbq

bpd.close_session()  # Reset session to apply connection settings
bpd.options.bigquery.project = PROJECT_ID
bpd.options.bigquery.location = LOCATION
bpd.options.bigquery.bq_connection = f'{PROJECT_ID}.{LOCATION}.{CONNECTION_ID}'
```

### Integer estimation

```python
df = bpd.DataFrame({'element': ['Hydrogen', 'Carbon', 'Oxygen', 'Iron', 'Gold']})

df['response'] = bbq.ai.generate_int(('What is the atomic number of ', df['element'], '?'))
df['atomic_number'] = df['response'].struct.field('result')
df[['element', 'atomic_number']].to_pandas()
```
