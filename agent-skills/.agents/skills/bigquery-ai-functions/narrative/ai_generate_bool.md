# AI.GENERATE_BOOL — BigQuery AI Functions

`AI.GENERATE_BOOL` is a scalar function that returns a STRUCT containing a BOOL value per row. Unlike `AI.IF`, it gives you full control over model parameters and returns detailed response metadata.

**When to use it:**
- You need boolean classification with control over model and parameters
- You want the full response metadata (full_response, status)
- You need to specify an endpoint or use model_params

**Alternatives:**
- `functions/ai_if` (`AI.IF`) — Managed function — auto-optimized prompts, returns BOOL directly, simpler
- `functions/ai_generate` (`AI.GENERATE`) — Full control with output_schema for custom structured output

**Multimodal:** Supports document, image, and video input via `RESOURCES.md#objectref-and-objectrefruntime-schema-reference` (ObjectRef). Pass a STRUCT prompt with ObjectRefRuntime fields for boolean questions about unstructured data.

**References:** `RESOURCES.md` (Full syntax reference) | [Official documentation](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-generate-bool) | `setup` (Setup guide)

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

### 1. Basic boolean evaluation

`AI.GENERATE_BOOL` returns a STRUCT with `result` (BOOL), `full_response` (JSON), and `status` (STRING).

```python
query = """
SELECT
  city,
  (AI.GENERATE_BOOL(CONCAT(city, ' is in Europe'))).result AS is_in_europe
FROM UNNEST(['London', 'Tokyo', 'Berlin', 'Sydney', 'Rome']) AS city
"""
client.query(query).to_dataframe()
```

### 2. Using in WHERE clause

Unlike `AI.IF` which returns BOOL directly, `AI.GENERATE_BOOL` returns a STRUCT — extract `.result` for filtering.

```python
query = """
SELECT review
FROM UNNEST([
  'Amazing product!',
  'Terrible quality.',
  'Pretty good for the price.',
  'Would not recommend.'
]) AS review
WHERE (AI.GENERATE_BOOL(CONCAT(review, ' is a positive review'))).result = TRUE
"""
client.query(query).to_dataframe()
```

### 3. Specifying endpoint and model_params

Unlike `AI.IF`, you can control the model and generation parameters.

```python
query = """
SELECT
  statement,
  (AI.GENERATE_BOOL(
    CONCAT(statement, ' is factually accurate'),
    endpoint => 'gemini-2.5-flash',
    model_params => JSON '{"generation_config": {"temperature": 0}}'
  )).result AS is_accurate
FROM UNNEST([
  'The Earth is the third planet from the Sun.',
  'Water boils at 50 degrees Celsius at sea level.',
  'Python was created by Guido van Rossum.'
]) AS statement
"""
client.query(query).to_dataframe()
```

### 4. Comparison: AI.GENERATE_BOOL vs AI.IF

`AI.GENERATE_BOOL` returns a STRUCT (with metadata); `AI.IF` returns BOOL directly.

```python
query = """
SELECT
  item,
  -- AI.GENERATE_BOOL: returns STRUCT, extract .result
  (AI.GENERATE_BOOL(CONCAT(item, ' is a fruit'))).result AS bool_result,
  -- AI.IF: returns BOOL directly
  AI.IF(CONCAT(item, ' is a fruit')) AS if_result
FROM UNNEST(['Apple', 'Carrot', 'Banana', 'Broccoli']) AS item
"""
client.query(query).to_dataframe()
```

---
## Examples — Multimodal with ObjectRef

`AI.GENERATE_BOOL` can analyze documents, images, and video stored in Cloud Storage. Use the **ObjectRef pipeline** to create a STRUCT prompt with signed references:

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
_prefix = 'bq_ai_functions/ai_generate_bool'

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

### 5. Boolean question about a document

Pass a document via ObjectRef in a STRUCT prompt to ask a yes/no question about its content.

```python
query = f"""
SELECT
  (AI.GENERATE_BOOL(
    STRUCT(
      'Does this invoice total exceed $5,000?' AS prompt,
      [OBJ.GET_ACCESS_URL(
        OBJ.FETCH_METADATA(
          OBJ.MAKE_REF(
            'gs://{BUCKET}/bq_ai_functions/ai_generate_bool/invoice_001.pdf',
            '{PROJECT_ID}.{LOCATION}.{CONNECTION_ID}'
          )
        ), 'r'
      )] AS object_ref_runtime
    )
  )).result AS exceeds_5000
"""
client.query(query).to_dataframe()
```

---
## Examples — `%%bigquery` Magics

The same examples using IPython magic commands. Magics let you write SQL directly in notebook cells without Python string wrapping.

Key patterns:
- `%%bigquery` — run SQL, display results inline
- `%%bigquery df` — run SQL, capture results into a pandas DataFrame

### AI.GENERATE_BOOL with `%%bigquery`

```sql
%%bigquery --project {PROJECT_ID}

SELECT
  city,
  (AI.GENERATE_BOOL(CONCAT(city, ' is a capital city'))).result AS is_capital
FROM UNNEST(['Paris', 'New York', 'Tokyo', 'Sydney', 'Berlin']) AS city
```

---
## Examples — BigFrames

BigFrames wraps `AI.GENERATE_BOOL` via `bbq.ai.generate_bool()`. Returns a Series of structs.

```python
import bigframes.pandas as bpd
import bigframes.bigquery as bbq

bpd.close_session()  # Reset session to apply connection settings
bpd.options.bigquery.project = PROJECT_ID
bpd.options.bigquery.location = LOCATION
bpd.options.bigquery.bq_connection = f'{PROJECT_ID}.{LOCATION}.{CONNECTION_ID}'
```

### Boolean evaluation

```python
df = bpd.DataFrame({'item': ['Apple', 'Carrot', 'Banana', 'Broccoli']})

df['response'] = bbq.ai.generate_bool(('Is ', df['item'], ' a fruit?'))
df['is_fruit'] = df['response'].struct.field('result')
df[['item', 'is_fruit']].to_pandas()
```
