# AI.GENERATE_TEXT — BigQuery AI Functions

`AI.GENERATE_TEXT` is a table-valued function that generates text using a remote model. It supports Gemini, Claude, Llama, Mistral, and open models — making it the most flexible generation function.

**When to use it:**
- You need to use non-Gemini models (Claude, Llama, Mistral)
- You want table-valued output with all input columns preserved
- You need Google Search grounding with `ground_with_google_search`
- You have an existing `CREATE MODEL` workflow

**Alternatives:**
- `functions/ai_generate` (`AI.GENERATE`) — Scalar function, no model required, Gemini only
- `functions/ai_generate_table` (`AI.GENERATE_TABLE`) — TVF with structured output via output_schema
- `functions/ml_generate_text` (`ML.GENERATE_TEXT`) — Legacy predecessor with ml_generate_text_ column prefixes

**Multimodal:** Supports document, image, and video input via `RESOURCES.md#objectref-and-objectrefruntime-schema-reference` (ObjectRef). Pass a STRUCT prompt with ObjectRefRuntime fields to analyze unstructured data from Cloud Storage.

**References:** `RESOURCES.md` (Full syntax reference) | [Official documentation](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-generate-text) | `setup` (Setup guide)

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
# Create remote Gemini model (idempotent)
client.query(f'''
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.gemini_flash`
  REMOTE WITH CONNECTION `{PROJECT_ID}.{LOCATION}.{CONNECTION_ID}`
  OPTIONS (endpoint = \'gemini-2.5-flash\')
''').result()
print('Model gemini_flash ready')
```

---
## Examples — SQL

Progressive examples from simplest to most advanced. Each cell adds one new concept.

### 1. Simplest call — single prompt

The input query must have a `prompt` column. AI.GENERATE_TEXT returns all input columns plus `result`, `status`, and metadata columns.

```python
query = f'''
SELECT result
FROM AI.GENERATE_TEXT(
  MODEL `{PROJECT_ID}.{DATASET_ID}.gemini_flash`,
  (SELECT 'What is BigQuery?' AS prompt)
)
'''
df = client.query(query).to_dataframe()
print(df.iloc[0]['result'])
```

### 2. Processing multiple rows

Each row in the input gets its own model call. The prompt column is built with CONCAT.

```python
query = f'''
SELECT prompt, result
FROM AI.GENERATE_TEXT(
  MODEL `{PROJECT_ID}.{DATASET_ID}.gemini_flash`,
  (SELECT CONCAT('What country is ', city, ' in? Answer in one word.') AS prompt, city
   FROM UNNEST(['Tokyo', 'Paris', 'Nairobi']) AS city)
)
'''
client.query(query).to_dataframe()
```

### 3. Controlling generation parameters

Pass generation parameters as a STRUCT. Parameters are named arguments, not JSON.

```python
query = f'''
SELECT result
FROM AI.GENERATE_TEXT(
  MODEL `{PROJECT_ID}.{DATASET_ID}.gemini_flash`,
  (SELECT 'Write a haiku about cloud computing.' AS prompt),
  STRUCT(0.8 AS temperature, 100 AS max_output_tokens)
)
'''
df = client.query(query).to_dataframe()
print(df.iloc[0]['result'])
```

### 4. Google Search grounding

Enable Google Search grounding with `ground_with_google_search`. The model will search the web for current information.

```python
query = f'''
SELECT result
FROM AI.GENERATE_TEXT(
  MODEL `{PROJECT_ID}.{DATASET_ID}.gemini_flash`,
  (SELECT 'What is the current population of Tokyo?' AS prompt),
  STRUCT(TRUE AS ground_with_google_search)
)
'''
df = client.query(query).to_dataframe()
print(df.iloc[0]['result'])
```

### 5. Safety settings

Control content safety filtering with `safety_settings`.

```python
query = f'''
SELECT result
FROM AI.GENERATE_TEXT(
  MODEL `{PROJECT_ID}.{DATASET_ID}.gemini_flash`,
  (SELECT 'Explain the science of fireworks.' AS prompt),
  STRUCT(
    [STRUCT('HARM_CATEGORY_DANGEROUS_CONTENT' AS category, 'BLOCK_ONLY_HIGH' AS threshold)] AS safety_settings
  )
)
'''
df = client.query(query).to_dataframe()
print(df.iloc[0]['result'])
```

### 6. Inspecting response metadata

`AI.GENERATE_TEXT` returns additional columns beyond `result`: `full_response` (full JSON), `status`, `safety_attributes`, and token usage. These are useful for debugging, cost tracking, and safety auditing.

```python
query = f'''
SELECT *
FROM AI.GENERATE_TEXT(
  MODEL `{PROJECT_ID}.{DATASET_ID}.gemini_flash`,
  (SELECT 'What is 2 + 2? Answer in one word.' AS prompt)
)
'''
df = client.query(query).to_dataframe()
print('Columns returned:', list(df.columns))
print(f'Result: {df.iloc[0]["result"]}')
print(f'Status: {df.iloc[0]["status"]}')
```

### 7. Processing table data at scale

Use a CTE or subquery to select specific rows, then pass to AI.GENERATE_TEXT. Materialize first when using LIMIT to avoid extra charges.

```python
query = f'''
WITH reviews AS (
  SELECT *
  FROM UNNEST([
    STRUCT('r1' AS id, 'Amazing product, fast delivery!' AS review),
    STRUCT('r2', 'Terrible quality. Broke after one day.'),
    STRUCT('r3', 'Average product, nothing special.'),
    STRUCT('r4', 'Great value for the price!')
  ])
)
SELECT id, review, result AS sentiment
FROM AI.GENERATE_TEXT(
  MODEL `{PROJECT_ID}.{DATASET_ID}.gemini_flash`,
  (SELECT id, review,
   CONCAT('Classify this review as positive, negative, or neutral. Return only the label: ', review) AS prompt
   FROM reviews)
)
'''
client.query(query).to_dataframe()
```

---
## Examples — Multimodal with ObjectRef

`AI.GENERATE_TEXT` can analyze documents, images, and video stored in Cloud Storage. Use the **ObjectRef pipeline** to create a STRUCT prompt with signed references:

```
OBJ.MAKE_REF(uri, connection)        → ObjectRef
  → OBJ.FETCH_METADATA(objectref)    → adds content type and size
    → OBJ.GET_ACCESS_URL(ref, 'r')   → ObjectRefRuntime (signed URL)
```

The STRUCT replaces the STRING prompt. See the `RESOURCES.md#objectref-and-objectrefruntime-schema-reference` (ObjectRef reference) for details.

```python
from google.cloud import storage as _storage
from pathlib import Path

# Upload invoice for the multimodal example
_gcs = _storage.Client(project=PROJECT_ID)
_bucket = _gcs.bucket(BUCKET)
_prefix = 'bq_ai_functions/ai_generate_text'

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

### 8. Summarize a document

Pass a document via ObjectRef using a STRUCT prompt to analyze content from Cloud Storage.

```python
query = f"""
SELECT result
FROM AI.GENERATE_TEXT(
  MODEL `{PROJECT_ID}.{DATASET_ID}.gemini_flash`,
  (SELECT STRUCT(
    'Summarize this document in 2-3 sentences.' AS prompt,
    [OBJ.GET_ACCESS_URL(
      OBJ.FETCH_METADATA(
        OBJ.MAKE_REF(
          'gs://{BUCKET}/bq_ai_functions/ai_generate_text/invoice_001.pdf',
          '{PROJECT_ID}.{LOCATION}.{CONNECTION_ID}'
        )
      ), 'r'
    )] AS object_ref_runtime
  ) AS prompt)
)
"""
df = client.query(query).to_dataframe()
print(df.iloc[0]['result'])
```

---
## Examples — `%%bigquery` Magics

The same examples using IPython magic commands. Magics let you write SQL directly in notebook cells without Python string wrapping.

Key patterns:
- `%%bigquery` — run SQL, display results inline
- `%%bigquery df` — run SQL, capture results into a pandas DataFrame

### Basic call with `%%bigquery`

**Note:** `%%bigquery` magics cannot interpolate Python variables in the SQL body. Use `--project` on the magic line for project, but model/table references must be hardcoded or use `client.query()` instead.

Since AI.GENERATE_TEXT requires a `MODEL` reference with project/dataset, most examples are better run via `client.query()` with f-strings. Here we show one example with hardcoded references.

```sql
%%bigquery --project {PROJECT_ID}

SELECT result
FROM AI.GENERATE_TEXT(
  MODEL `statmike-mlops-349915.bq_ai_functions.gemini_flash`,
  (SELECT 'Write a haiku about SQL.' AS prompt),
  STRUCT(0.8 AS temperature)
)
```

### Capture results to a DataFrame

```sql
%%bigquery df_text --project {PROJECT_ID}

SELECT city, result AS country
FROM AI.GENERATE_TEXT(
  MODEL `statmike-mlops-349915.bq_ai_functions.gemini_flash`,
  (SELECT CONCAT('What country is ', city, ' in? One word.') AS prompt, city
   FROM UNNEST(['Tokyo', 'Paris', 'Nairobi']) AS city)
)
```

```python
df_text
```

---
## Examples — BigFrames

BigFrames wraps `AI.GENERATE_TEXT` via `bbq.ai.generate_text()`. It takes a model name string and a DataFrame.

**Key difference from SQL:** The function takes a model name and a DataFrame/Series with a `prompt` column.

```python
import bigframes.pandas as bpd
import bigframes.bigquery as bbq

bpd.options.bigquery.project = PROJECT_ID
bpd.options.bigquery.location = LOCATION
```

### Basic generation

```python
# Create input DataFrame with a 'prompt' column
df = bpd.DataFrame({
    'city': ['Tokyo', 'Paris', 'Nairobi'],
    'prompt': [
        'What country is Tokyo in? Answer in one word.',
        'What country is Paris in? Answer in one word.',
        'What country is Nairobi in? Answer in one word.',
    ]
})

# Use the model reference as a string
model_name = f'{PROJECT_ID}.{DATASET_ID}.gemini_flash'
result = bbq.ai.generate_text(model_name, df)

result[['city', 'result']].to_pandas()
```
