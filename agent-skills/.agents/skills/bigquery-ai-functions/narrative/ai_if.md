# AI.IF — BigQuery AI Functions

`AI.IF` is a managed scalar function that evaluates a natural language condition and returns a BOOL. BigQuery automatically optimizes prompts and minimizes Gemini calls.

**When to use it:**
- You want boolean filtering in WHERE clauses with natural language conditions
- You need simple true/false classification without managing prompts
- You want BigQuery to auto-optimize your AI calls (query plan optimization)
- You want to guide evaluation with few-shot `examples` (pairs of input → expected BOOL)
- You want cost-optimized evaluation at scale: `optimization_mode => 'MINIMIZE_COST'` with `embeddings` trains a local distilled model (up to 230x token reduction, ~3,000 row minimum)

**Alternatives:**
- `functions/ai_generate_bool` (`AI.GENERATE_BOOL`) — More control over model and parameters, returns STRUCT
- `functions/ai_generate` (`AI.GENERATE`) — Full control with output_schema for custom structured output
- `functions/ai_classify` (`AI.CLASSIFY`) — Multi-category classification instead of boolean

**Multimodal:** Supports document, image, and video input via `RESOURCES.md#objectref-and-objectrefruntime-schema-reference` (ObjectRef). Pass a STRUCT condition with ObjectRefRuntime fields to evaluate conditions on unstructured data.

**Featured in:** `workflows/content_moderation` (Content Moderation)

**References:** `RESOURCES.md` (Full syntax reference) | [Official documentation](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-if) | `setup` (Setup guide)

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

### 1. Simplest call — boolean evaluation

`AI.IF` takes a prompt and returns TRUE or FALSE directly (not a struct).

```python
query = """
SELECT
  city,
  AI.IF(CONCAT(city, ' is in Asia')) AS is_in_asia
FROM UNNEST(['Tokyo', 'Paris', 'Nairobi', 'Bangkok', 'Sydney']) AS city
"""
client.query(query).to_dataframe()
```

### 2. Filtering with WHERE

Use `AI.IF` in WHERE clauses for semantic filtering. BigQuery evaluates non-AI filters first to reduce Gemini calls.

```python
query = """
SELECT review
FROM UNNEST([
  'Amazing product, fast delivery!',
  'Terrible quality. Broke after one day.',
  'Average, nothing special.',
  'Great value for the price!',
  'Worst purchase ever.'
]) AS review
WHERE AI.IF(CONCAT(review, ' is a positive review'))
"""
client.query(query).to_dataframe()
```

### 3. Combining with non-AI filters

**Best practice:** Place non-AI filters alongside `AI.IF` — BigQuery evaluates non-AI conditions first, reducing the number of Gemini calls.

```python
query = """
WITH articles AS (
  SELECT *
  FROM UNNEST([
    STRUCT('tech' AS category, 'New AI chip sets speed record' AS title),
    STRUCT('tech', 'Best smartphones of the year'),
    STRUCT('sports', 'Olympic records broken in swimming'),
    STRUCT('tech', 'Cloud computing market grows 30%'),
    STRUCT('sports', 'Local team wins championship')
  ])
)
SELECT category, title
FROM articles
WHERE category = 'tech'  -- evaluated first (no AI call)
  AND AI.IF(CONCAT(title, ' is about artificial intelligence'))  -- only called for tech articles
"""
client.query(query).to_dataframe()
```

### 4. Content moderation

Use `AI.IF` to flag content that may need review.

```python
query = """
SELECT
  comment,
  AI.IF(CONCAT(comment, ' contains inappropriate language or personal attacks')) AS needs_review
FROM UNNEST([
  'Great article, very informative!',
  'This is completely wrong and the author is incompetent.',
  'I disagree with the conclusion but appreciate the research.',
  'What a waste of time reading this garbage.'
]) AS comment
"""
client.query(query).to_dataframe()
```

### 5. Specifying an endpoint

Override the auto-selected model with a specific Gemini model.

```python
query = """
SELECT
  statement,
  AI.IF(CONCAT(statement, ' is a factually accurate statement'), endpoint => 'gemini-2.5-flash') AS is_accurate
FROM UNNEST([
  'The Earth orbits the Sun.',
  'Water boils at 50 degrees Celsius.',
  'Python is a programming language.'
]) AS statement
"""
client.query(query).to_dataframe()
```

### 6. Few-shot examples

The `examples` parameter provides input→output pairs that guide the model. Each example is a `STRUCT<STRING, BOOL>` mapping an input to an expected result. This is useful when the evaluation criteria are nuanced or when you want consistent behavior on edge cases.

```python
query = """
SELECT
  statement,
  AI.IF(
    CONCAT(statement, ' is a scientifically proven health claim'),
    examples => [
      ('Drinking water keeps you hydrated', TRUE),
      ('Eating carrots gives you night vision', FALSE),
      ('Exercise reduces the risk of heart disease', TRUE),
      ('Cracking knuckles causes arthritis', FALSE)
    ]
  ) AS is_proven
FROM UNNEST([
  'Vitamin C helps the immune system.',
  'Reading in dim light ruins your eyesight.',
  'Smoking increases cancer risk.',
  'We only use 10% of our brain.'
]) AS statement
"""
client.query(query).to_dataframe()
```

### 7. Error ratio control

By default, `AI.IF` returns NULL for rows where the model call fails and continues the query. Set `max_error_ratio` (0.0–1.0) to fail the entire query when the error rate exceeds your threshold — useful for data pipelines where silent NULLs would corrupt downstream results.

```python
query = """
SELECT
  city,
  AI.IF(
    CONCAT(city, ' is a capital city'),
    max_error_ratio => 0.0
  ) AS is_capital
FROM UNNEST(['Tokyo', 'Paris', 'Sydney', 'Ottawa', 'Munich']) AS city
"""
client.query(query).to_dataframe()
```

### Optimized mode: `optimization_mode` and `embeddings` (Preview)

For large-scale evaluation (≥3,000 rows), `AI.IF` supports an optimized mode that trains a local distilled model using embeddings — reducing token usage by up to **230x**:

```sql
SELECT
  review,
  AI.IF(
    CONCAT(review, ' is a positive review'),
    embeddings => AI.EMBED(review),
    optimization_mode => 'MINIMIZE_COST'
  ) AS is_positive
FROM `my_dataset.reviews`  -- needs ~3,000+ rows
```

- `optimization_mode => 'MINIMIZE_COST'` (default when `embeddings` provided) — trains a local model, dramatically reducing Gemini calls
- `optimization_mode => 'MAXIMIZE_QUALITY'` — always uses the remote LLM (ignores embeddings)
- `embeddings` can be generated on-the-fly with `AI.EMBED(...)` or pre-materialized
- If autonomous embedding generation is enabled on the table, BigQuery uses those embeddings automatically
- Not demoed here because the minimum ~3,000 row requirement exceeds our example data size

---
## Examples — Multimodal with ObjectRef

`AI.IF` can analyze documents, images, and video stored in Cloud Storage. Use the **ObjectRef pipeline** to create a STRUCT prompt with signed references:

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
_prefix = 'bq_ai_functions/ai_if'

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

### 8. Evaluate a condition on a document

Pass a document via ObjectRef in a STRUCT prompt to evaluate a boolean condition.

```python
query = f"""
SELECT
  AI.IF(
    STRUCT(
      'This document is a financial invoice' AS prompt,
      [OBJ.GET_ACCESS_URL(
        OBJ.FETCH_METADATA(
          OBJ.MAKE_REF(
            'gs://{BUCKET}/bq_ai_functions/ai_if/invoice_001.pdf',
            '{PROJECT_ID}.{LOCATION}.{CONNECTION_ID}'
          )
        ), 'r'
      )] AS object_ref_runtime
    )
  ) AS is_invoice
"""
client.query(query).to_dataframe()
```

---
## Examples — `%%bigquery` Magics

The same examples using IPython magic commands. Magics let you write SQL directly in notebook cells without Python string wrapping.

Key patterns:
- `%%bigquery` — run SQL, display results inline
- `%%bigquery df` — run SQL, capture results into a pandas DataFrame

### Filtering with `%%bigquery`

```sql
%%bigquery --project {PROJECT_ID}

SELECT
  city,
  AI.IF(CONCAT(city, ' is in Europe')) AS is_in_europe
FROM UNNEST(['London', 'Tokyo', 'Berlin', 'Sydney', 'Rome']) AS city
```

### Using in WHERE clause

```sql
%%bigquery df_positive --project {PROJECT_ID}

SELECT review
FROM UNNEST([
  'Love it!', 'Terrible.', 'Pretty good.', 'Awful experience.'
]) AS review
WHERE AI.IF(CONCAT(review, ' is a positive review'))
```

```python
df_positive
```

---
## Examples — BigFrames

BigFrames wraps `AI.IF` via `bbq.ai.if_()`. It returns a Series of BOOL directly (not a struct, unlike `generate_bool`).

**Key patterns:**
- Returns BOOL directly — use for boolean indexing
- Tuple prompt pattern: `bbq.ai.if_((df["col"], " condition"))`
- No endpoint parameter — BigQuery auto-selects the model

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
df = bpd.DataFrame({'city': ['Tokyo', 'Paris', 'Nairobi', 'Bangkok', 'Sydney']})

df['is_in_asia'] = bbq.ai.if_((df['city'], ' is in Asia'))
df.to_pandas()
```

### Boolean indexing (filtering)

```python
reviews = bpd.DataFrame({'review': [
    'Amazing product!', 'Terrible quality.', 'Pretty good.', 'Worst ever.'
]})

# Filter to only positive reviews
positive = reviews[bbq.ai.if_((reviews['review'], ' is a positive review'))]
positive.to_pandas()
```
