# ML.GENERATE_TEXT — BigQuery AI Functions

`ML.GENERATE_TEXT` is the legacy predecessor to `AI.GENERATE_TEXT`. It has the same capabilities but uses `ml_generate_text_` prefixed column names. **Google recommends using `AI.GENERATE_TEXT` for new queries.**

**When to use it:**
- You have existing code that uses ML.GENERATE_TEXT and need to maintain it
- You need the `flatten_json_output` parameter for JSON response handling

**Alternatives:**
- `functions/ai_generate_text` (`AI.GENERATE_TEXT`) — Recommended replacement — same capabilities, cleaner column names
- `functions/ai_generate` (`AI.GENERATE`) — Scalar function, no model required, Gemini only

**Multimodal:** Supports document, image, and video input via `RESOURCES.md#objectref-and-objectrefruntime-schema-reference` (ObjectRef). Pass a STRUCT prompt with ObjectRefRuntime fields to analyze unstructured data from Cloud Storage.

**References:** `RESOURCES.md` (Full syntax reference) | [Official documentation](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-generate-text) | `setup` (Setup guide)

---
## Setup

Set your project and location, authenticate, and create a temporary dataset for this notebook.

> This function requires a connection and a remote model. The cells below create them if they don't exist. See the `setup` (Setup Reference) for details.

```python
PROJECT_ID = 'statmike-mlops-349915'  # <-- Replace with your project ID
LOCATION = 'US'  # BigQuery dataset location
DATASET_ID = 'bq_ai_functions'  # Shared dataset across all notebooks
CONNECTION_ID = 'bq_ai_functions'  # Shared connection
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
_sp.run(['gcloud', 'projects', 'add-iam-policy-binding', PROJECT_ID,
         f'--member=serviceAccount:{sa}', '--role=roles/aiplatform.user', '--quiet'],
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

### 1. Basic call with flattened output

The key difference from `AI.GENERATE_TEXT`: column names are prefixed with `ml_generate_text_`.

Set `flatten_json_output = TRUE` to get `ml_generate_text_llm_result` (the generated text) as a separate column.

```python
query = f'''
SELECT ml_generate_text_llm_result
FROM ML.GENERATE_TEXT(
  MODEL `{PROJECT_ID}.{DATASET_ID}.gemini_flash`,
  (SELECT 'What is BigQuery?' AS prompt),
  STRUCT(TRUE AS flatten_json_output)
)
'''
df = client.query(query).to_dataframe()
print(df.iloc[0]['ml_generate_text_llm_result'])
```

### 2. Default output (JSON)

Without `flatten_json_output` (or set to FALSE), the result is a single JSON column.

```python
import json

query = f'''
SELECT ml_generate_text_result, ml_generate_text_status
FROM ML.GENERATE_TEXT(
  MODEL `{PROJECT_ID}.{DATASET_ID}.gemini_flash`,
  (SELECT 'Write a haiku about SQL.' AS prompt)
)
'''
df = client.query(query).to_dataframe()
result = json.loads(df.iloc[0]['ml_generate_text_result'])
print(result['candidates'][0]['content']['parts'][0]['text'])
```

### 3. Column name comparison with AI.GENERATE_TEXT

Side-by-side showing the naming difference.

```python
# ML.GENERATE_TEXT columns
query_ml = f'''
SELECT *
FROM ML.GENERATE_TEXT(
  MODEL `{PROJECT_ID}.{DATASET_ID}.gemini_flash`,
  (SELECT 'Hello' AS prompt),
  STRUCT(TRUE AS flatten_json_output)
)
'''
df_ml = client.query(query_ml).to_dataframe()
print('ML.GENERATE_TEXT columns:', list(df_ml.columns))

# AI.GENERATE_TEXT columns
query_ai = f'''
SELECT *
FROM AI.GENERATE_TEXT(
  MODEL `{PROJECT_ID}.{DATASET_ID}.gemini_flash`,
  (SELECT 'Hello' AS prompt)
)
'''
df_ai = client.query(query_ai).to_dataframe()
print('AI.GENERATE_TEXT columns:', list(df_ai.columns))
```

### 4. Generation parameters

Parameters work the same as `AI.GENERATE_TEXT`.

```python
query = f'''
SELECT prompt, ml_generate_text_llm_result AS result
FROM ML.GENERATE_TEXT(
  MODEL `{PROJECT_ID}.{DATASET_ID}.gemini_flash`,
  (SELECT CONCAT('What country is ', city, ' in? One word.') AS prompt, city
   FROM UNNEST(['Tokyo', 'Paris', 'Nairobi']) AS city),
  STRUCT(TRUE AS flatten_json_output, 0.0 AS temperature)
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

### ML.GENERATE_TEXT with `%%bigquery`

```sql
%%bigquery --project {PROJECT_ID}

SELECT ml_generate_text_llm_result AS result
FROM ML.GENERATE_TEXT(
  MODEL `statmike-mlops-349915.bq_ai_functions.gemini_flash`,
  (SELECT 'Write a haiku about data.' AS prompt),
  STRUCT(TRUE AS flatten_json_output)
)
```

---
## Examples — BigFrames

BigFrames has no direct `ML.GENERATE_TEXT` wrapper. It routes through `AI.GENERATE_TEXT` instead.
Use `bbq.ai.generate_text()` or the `GeminiTextGenerator` class.

```python
import bigframes.pandas as bpd
import bigframes.bigquery as bbq

bpd.options.bigquery.project = PROJECT_ID
bpd.options.bigquery.location = LOCATION
```

### Using bbq.ai.generate_text (wraps AI.GENERATE_TEXT)

```python
df = bpd.DataFrame({'prompt': [
    'What is BigQuery? Answer in one sentence.',
    'What is Cloud Storage? Answer in one sentence.'
]})

model_name = f'{PROJECT_ID}.{DATASET_ID}.gemini_flash'
result = bbq.ai.generate_text(model_name, df)
result[['prompt', 'result']].to_pandas()
```
