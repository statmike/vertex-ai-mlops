# AI.GENERATE_DOUBLE — BigQuery AI Functions

`AI.GENERATE_DOUBLE` is a scalar function that returns a STRUCT containing a FLOAT64 value per row. Unlike `AI.SCORE`, it gives you full control over model parameters and returns detailed response metadata.

**When to use it:**
- You need numeric scoring with control over model and parameters
- You want the full response metadata (full_response, status)
- You need to specify an endpoint or use model_params

**Alternatives:**
- `functions/ai_score` (`AI.SCORE`) — Managed function — auto-generated rubric, returns FLOAT64 directly, simpler
- `functions/ai_generate` (`AI.GENERATE`) — Full control with output_schema for custom structured output

**Multimodal:** Supports document, image, and video input via `RESOURCES.md#objectref-and-objectrefruntime-schema-reference` (ObjectRef). Pass a STRUCT prompt with ObjectRefRuntime fields to extract numeric values from unstructured data.

**References:** `RESOURCES.md` (Full syntax reference) | [Official documentation](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-generate-double) | `setup` (Setup guide)

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

### 1. Basic numeric estimation

`AI.GENERATE_DOUBLE` returns a STRUCT with `result` (FLOAT64), `full_response` (JSON), and `status` (STRING).

```python
query = """
SELECT
  city,
  (AI.GENERATE_DOUBLE(
    CONCAT('Estimate the population of ', city, ' in millions.')
  )).result AS population_millions
FROM UNNEST(['Tokyo', 'Paris', 'Nairobi', 'Lima', 'Sydney']) AS city
"""
client.query(query).to_dataframe()
```

### 2. Scoring with explicit scale

Ask the model to rate something on a specific numeric scale.

```python
query = """
SELECT
  review,
  (AI.GENERATE_DOUBLE(
    CONCAT('Rate the positivity of this review on a scale of 0.0 to 1.0: ', review)
  )).result AS positivity
FROM UNNEST([
  'Best product I have ever bought!',
  'Terrible experience, would not recommend.',
  'Average quality, nothing remarkable.',
  'Good value for money.'
]) AS review
ORDER BY positivity DESC
"""
client.query(query).to_dataframe()
```

### 3. With endpoint and model_params

```python
query = """
SELECT
  text,
  (AI.GENERATE_DOUBLE(
    CONCAT('Rate the reading difficulty on a scale of 1.0 to 10.0: ', text),
    endpoint => 'gemini-2.5-flash',
    model_params => JSON '{"generation_config": {"temperature": 0}}'
  )).result AS difficulty
FROM UNNEST([
  'The cat sat on the mat.',
  'Quantum entanglement demonstrates non-local correlations.',
  'Machine learning models can improve over time.'
]) AS text
"""
client.query(query).to_dataframe()
```

### 4. Comparison: AI.GENERATE_DOUBLE vs AI.SCORE

`AI.GENERATE_DOUBLE` returns a STRUCT; `AI.SCORE` returns FLOAT64 directly with auto-generated rubric.

```python
query = """
SELECT
  review,
  (AI.GENERATE_DOUBLE(CONCAT('Rate positivity 1-10: ', review))).result AS double_score,
  AI.SCORE(CONCAT('Rate positivity on a scale of 1 to 10: ', review)) AS managed_score
FROM UNNEST([
  'Excellent quality!', 'Terrible product.', 'Okay, nothing special.'
]) AS review
"""
client.query(query).to_dataframe()
```

---
## Examples — Multimodal with ObjectRef

`AI.GENERATE_DOUBLE` can analyze documents, images, and video stored in Cloud Storage. Use the **ObjectRef pipeline** to create a STRUCT prompt with signed references:

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
_prefix = 'bq_ai_functions/ai_generate_double'

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

### 5. Extract a numeric value from a document

Pass a document via ObjectRef in a STRUCT prompt to extract a floating-point value.

```python
query = f"""
SELECT
  (AI.GENERATE_DOUBLE(
    STRUCT(
      'What is the total dollar amount on this invoice?' AS prompt,
      [OBJ.GET_ACCESS_URL(
        OBJ.FETCH_METADATA(
          OBJ.MAKE_REF(
            'gs://{BUCKET}/bq_ai_functions/ai_generate_double/invoice_001.pdf',
            '{PROJECT_ID}.{LOCATION}.{CONNECTION_ID}'
          )
        ), 'r'
      )] AS object_ref_runtime
    )
  )).result AS total_amount
"""
client.query(query).to_dataframe()
```

---
## Examples — `%%bigquery` Magics

The same examples using IPython magic commands. Magics let you write SQL directly in notebook cells without Python string wrapping.

Key patterns:
- `%%bigquery` — run SQL, display results inline
- `%%bigquery df` — run SQL, capture results into a pandas DataFrame

### AI.GENERATE_DOUBLE with `%%bigquery`

```sql
%%bigquery --project {PROJECT_ID}

SELECT
  city,
  (AI.GENERATE_DOUBLE(
    CONCAT('Estimate the latitude of ', city, ' in degrees.')
  )).result AS latitude
FROM UNNEST(['London', 'Tokyo', 'Sydney', 'Cape Town']) AS city
```

---
## Examples — BigFrames

BigFrames wraps `AI.GENERATE_DOUBLE` via `bbq.ai.generate_double()`. Returns a Series of structs.

```python
import bigframes.pandas as bpd
import bigframes.bigquery as bbq

bpd.close_session()  # Reset session to apply connection settings
bpd.options.bigquery.project = PROJECT_ID
bpd.options.bigquery.location = LOCATION
bpd.options.bigquery.bq_connection = f'{PROJECT_ID}.{LOCATION}.{CONNECTION_ID}'
```

### Numeric estimation

```python
df = bpd.DataFrame({'city': ['Tokyo', 'Paris', 'Nairobi', 'Lima']})

df['response'] = bbq.ai.generate_double(('Estimate the population of ', df['city'], ' in millions.'))
df['population'] = df['response'].struct.field('result')
df[['city', 'population']].to_pandas()
```
