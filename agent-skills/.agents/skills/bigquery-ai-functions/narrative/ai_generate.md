# AI.GENERATE — BigQuery AI Functions

`AI.GENERATE` is the simplest way to call a Gemini model from SQL. It's a **scalar function** — use it in SELECT, WHERE, or anywhere you'd use a regular function. No model creation required.

**What it does:** Sends a prompt to a Gemini model and returns generated text or structured output.

**When to use it:**
- You want to call Gemini from SQL with minimal setup
- You need free-form text generation or structured output with typed columns
- You're working with Gemini models only (for Claude/Llama/Mistral, use `functions/ai_generate_text` (`AI.GENERATE_TEXT`))

**Alternatives:**
- `functions/ai_generate_text` (`AI.GENERATE_TEXT`) — table-valued function, supports non-Gemini models, requires `CREATE MODEL`
- `functions/ai_if` (`AI.IF`), `functions/ai_score` (`AI.SCORE`), `functions/ai_classify` (`AI.CLASSIFY`) — simplified interfaces for common tasks with auto-optimized prompts
- `functions/ai_generate_bool` (`AI.GENERATE_BOOL`), `functions/ai_generate_double` (`AI.GENERATE_DOUBLE`), `functions/ai_generate_int` (`AI.GENERATE_INT`) — typed scalar variants returning `BOOL`, `FLOAT64`, `INT64`

**Multimodal:** Supports document, image, and video input via `RESOURCES.md#objectref-and-objectrefruntime-schema-reference` (ObjectRef). Pass a STRUCT prompt with ObjectRefRuntime fields to analyze unstructured data from Cloud Storage.

**Thinking:** Supports extended reasoning via `model_params` — use `thinking_budget` (Gemini 2.5) or `thinking_level` (Gemini 3.0+) to control reasoning depth.

**Featured in:** `workflows/content_analysis` (Content Analysis Pipeline) | `workflows/data_enrichment` (Data Enrichment) | `workflows/rag_pipeline` (RAG Pipeline) | `workflows/document_intelligence` (Document Intelligence) | `workflows/content_moderation` (Content Moderation) | `workflows/multimodal_analysis` (Multimodal Analysis) | `workflows/document_rag` (Document RAG Pipeline) | `workflows/metric_diagnostics` (Metric Diagnostics)

**References:** `RESOURCES.md` (Full syntax reference) | [Official documentation](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-generate) | `setup` (Setup guide)

---
## Setup

Set your project and location, authenticate, and create a temporary dataset for this notebook.

> `AI.GENERATE` doesn't require a connection or model — it uses end-user credentials and defaults to `gemini-2.5-flash`. The [multimodal examples](#examples--multimodal-with-objectref) later in this notebook add a connection for GCS access. See the `setup` (Setup Reference) for details.

```python
PROJECT_ID = 'statmike-mlops-349915'  # <-- Replace with your project ID
LOCATION = 'US'  # BigQuery dataset location
DATASET_ID = 'bq_ai_functions'  # Shared dataset across all notebooks
CONNECTION_ID = 'bq_ai_functions'  # Cloud resource connection (used by multimodal examples)
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

### Schema helper — Pydantic to BigQuery

For simple schemas, you can write the `output_schema` string directly. For complex schemas with descriptions, array types, and many fields, defining a Pydantic model is cleaner and less error-prone.

This helper converts a Pydantic `BaseModel` to the formats that `AI.GENERATE` (SQL string) and BigFrames (dict) expect.

```python
from pydantic import BaseModel, Field
from typing import get_origin, get_args

# Python type → BigQuery type
_BQ_TYPES = {str: 'STRING', int: 'INT64', float: 'FLOAT64', bool: 'BOOL'}

def _bq_type(annotation) -> str:
    """Map a Python type annotation to a BigQuery type string."""
    if get_origin(annotation) is list:
        inner = _BQ_TYPES[get_args(annotation)[0]]
        return f'ARRAY<{inner}>'
    return _BQ_TYPES[annotation]

def bq_schema(model: type[BaseModel]) -> str:
    """Convert a Pydantic model to a BigQuery output_schema string.

    Supports str, int, float, bool, and list[T].
    Field descriptions become OPTIONS(description = '...').
    """
    fields = []
    for name, info in model.model_fields.items():
        field_str = f'{name} {_bq_type(info.annotation)}'
        if info.description:
            field_str += f" OPTIONS(description = '{info.description}')"
        fields.append(field_str)
    return ', '.join(fields)

def bf_schema(model: type[BaseModel]) -> dict[str, str]:
    """Convert a Pydantic model to a BigFrames output_schema dict."""
    return {name: _bq_type(info.annotation) for name, info in model.model_fields.items()}
```

---
## Examples — SQL

Progressive examples from simplest to most advanced. Each cell adds one new concept.

### 1. Simplest possible call

`AI.GENERATE` takes a prompt string and returns a STRUCT. Access the generated text with `.result`.

```python
query = """
SELECT
  (AI.GENERATE('What is BigQuery?')).result AS answer
"""
df = client.query(query).to_dataframe()
print(df.iloc[0]['answer'])
```

### 2. Using column values in prompts

Use `CONCAT` to build prompts from column values. `AI.GENERATE` runs once per row.

```python
query = """
SELECT
  city,
  (AI.GENERATE(
    CONCAT('What country is ', city, ' in? Answer in one word.')
  )).result AS country
FROM UNNEST(['Tokyo', 'Paris', 'Nairobi', 'Lima', 'Sydney']) AS city
"""
client.query(query).to_dataframe()
```

### 3. Accessing the full response

`AI.GENERATE` returns a STRUCT with three fields:
- `.result` — the generated text (STRING)
- `.full_response` — the complete API response (JSON)
- `.status` — error message if failed, empty if successful (STRING)

```python
import json

query = """
SELECT AI.GENERATE('Explain cloud computing in one sentence.') AS response
"""
df = client.query(query).to_dataframe()

print('result:', df.iloc[0]['response']['result'])
print('status:', repr(df.iloc[0]['response']['status']))

# Explore the full_response JSON structure
full = json.loads(df.iloc[0]['response']['full_response'])
print('\nfull_response keys:', list(full.keys()))
if 'candidates' in full:
    print('candidate keys:', list(full['candidates'][0].keys()))
if 'usageMetadata' in full:
    print('usage:', full['usageMetadata'])
```

### 4. Specifying an endpoint

Override the default model (`gemini-2.5-flash`) with any Gemini model.

```python
query = """
SELECT
  (AI.GENERATE(
    'Write a haiku about data warehouses.',
    endpoint => 'gemini-2.5-pro'
  )).result AS haiku
"""
df = client.query(query).to_dataframe()
print(df.iloc[0]['haiku'])
```

### 5. Structured output with `output_schema`

Provide an `output_schema` to get typed columns instead of free-form text. The `result` field is replaced by your custom schema fields.

```python
query = """
SELECT
  animal,
  result.habitat,
  result.average_lifespan_years,
  result.is_endangered
FROM
  UNNEST(['Eagle', 'Salmon', 'Cobra']) AS animal,
  UNNEST([
    AI.GENERATE(
      CONCAT('Give me facts about: ', animal),
      output_schema => 'habitat STRING, average_lifespan_years INT64, is_endangered BOOL'
    )
  ]) AS result
"""
client.query(query).to_dataframe()
```

### 6. Structured output with Pydantic schemas

For complex schemas with descriptions and array types, define a Pydantic model and convert it with `bq_schema()`. `Field(description=...)` maps to BigQuery's `OPTIONS(description = '...')`.

```python
class ProductAnalysis(BaseModel):
    category: str = Field(description='Product category like Electronics, Apparel, Kitchen')
    price_range_usd: str = Field(description='Estimated price range like $50-$100')
    key_features: list[str] = Field(description='Top 3 selling points')
    needs_batteries: bool = Field(description='Whether the product typically requires batteries')

# See what the converter produces
print(bq_schema(ProductAnalysis))
```

```python
output_schema = bq_schema(ProductAnalysis)

query = f'''
SELECT
  product,
  result.category,
  result.price_range_usd,
  result.key_features,
  result.needs_batteries
FROM
  UNNEST(['laptop', 'running shoes', 'espresso machine']) AS product,
  UNNEST([
    AI.GENERATE(
      CONCAT('Analyze this product for an e-commerce listing: ', product),
      output_schema => """{output_schema}"""
    )
  ]) AS result
'''
client.query(query).to_dataframe()
```

### 7. Controlling generation with `model_params`

`model_params` accepts any field from the [Gemini `generateContent` request body](https://cloud.google.com/vertex-ai/generative-ai/docs/model-reference/gemini#request_body) (except `contents`). Common uses: temperature, top_p, max_output_tokens.

```python
query = """
SELECT
  (AI.GENERATE(
    'Invent a creative name for a new coffee shop. Just the name, nothing else.',
    model_params => JSON '{"generation_config": {"temperature": 1.5, "max_output_tokens": 50}}'
  )).result AS creative_name
"""
df = client.query(query).to_dataframe()
print(df.iloc[0]['creative_name'])
```

### 8. Thinking budget

Gemini 2.5 models support "thinking" — internal reasoning before responding. Control the thinking budget (in tokens) to balance quality vs cost.

> **Gemini 3.0+:** Use `thinking_level` (`LOW`, `MEDIUM`, `HIGH`) in `thinking_config` instead of `thinking_budget`:
> ```sql
> model_params => JSON '{"generation_config": {"thinking_config": {"thinking_level": "LOW"}}}'
> ```

```python
query = """
SELECT
  (AI.GENERATE(
    'What is the sum of all prime numbers less than 50?',
    model_params => JSON '{"generation_config": {"thinking_config": {"thinking_budget": 2048}}}'
  )).result AS answer
"""
df = client.query(query).to_dataframe()
print(df.iloc[0]['answer'])
```

### 9. Grounding with Google Search

Enable Google Search grounding via the `tools` field in `model_params`. The model searches the web for current information before responding.

```python
query = """
SELECT
  (AI.GENERATE(
    'What were the top 3 news stories today?',
    model_params => JSON '{"tools": [{"googleSearch": {}}]}'
  )).result AS grounded_answer
"""
df = client.query(query).to_dataframe()
print(df.iloc[0]['grounded_answer'])
```

### 10. Processing table data at scale

**Best practice:** When using `LIMIT`, materialize selected rows first to avoid re-evaluating the subquery and incurring extra Vertex AI charges.

```python
class SentimentResult(BaseModel):
    sentiment: str
    confidence: float

output_schema = bq_schema(SentimentResult)

query = f"""
WITH selected_reviews AS (
  SELECT *
  FROM UNNEST([
    STRUCT('r1' AS id, 'The product is amazing, fast delivery!' AS review),
    STRUCT('r2', 'Terrible quality. Broke after one day.'),
    STRUCT('r3', 'Average product, nothing special.'),
    STRUCT('r4', 'Great value for the price. Highly recommend!'),
    STRUCT('r5', 'Worst purchase ever. Do not buy.')
  ])
)
SELECT id, review, response.sentiment, response.confidence
FROM (
  SELECT
    id,
    review,
    AI.GENERATE(
      CONCAT('Classify this review sentiment as positive, negative, or neutral: ', review),
      output_schema => '{output_schema}'
    ) AS response
  FROM selected_reviews
)
"""
client.query(query).to_dataframe()
```

---
## Examples — Multimodal with ObjectRef

`AI.GENERATE` can process documents, images, and video stored in Cloud Storage. The **ObjectRef pipeline** creates a secure, temporary reference to a GCS object:

```
OBJ.MAKE_REF(uri, connection)        → ObjectRef (pointer to the object)
  → OBJ.FETCH_METADATA(objectref)    → adds content type and size
    → OBJ.GET_ACCESS_URL(ref, 'r')   → ObjectRefRuntime (signed URL)
```

Pass `ObjectRefRuntime` values in a STRUCT prompt with `prompt` and `object_ref_runtime` fields. See the `RESOURCES.md#objectref-and-objectrefruntime-schema-reference` (ObjectRef reference) for details.

### Multimodal setup — connection and sample documents

ObjectRef requires a `setup` (Cloud resource connection) to access GCS. The cells below create a connection (if needed) and upload two sample documents.

```python
import subprocess as _sp

# Create the connection (idempotent — succeeds even if it already exists)
_sp.run(
    ['bq', 'mk', '--connection', '--location', LOCATION,
     '--connection_type', 'CLOUD_RESOURCE',
     '--project_id', PROJECT_ID, CONNECTION_ID],
    capture_output=True, text=True
)

# Get the connection's service account
import json as _json
_conn = _sp.run(
    ['bq', 'show', '--connection', '--format=json',
     f'{PROJECT_ID}.{LOCATION}.{CONNECTION_ID}'],
    capture_output=True, text=True
)
sa = _json.loads(_conn.stdout)['cloudResource']['serviceAccountId']
print(f'Connection SA: {sa}')

# Grant GCS read access (needed for ObjectRef to read documents)
_sp.run(
    ['gcloud', 'projects', 'add-iam-policy-binding', PROJECT_ID,
     f'--member=serviceAccount:{sa}', '--role=roles/storage.objectViewer', '--quiet'],
    capture_output=True, text=True
)
print('Granted roles/storage.objectViewer')
```

```python
from google.cloud import storage as _storage
from pathlib import Path

_gcs = _storage.Client(project=PROJECT_ID)
_bucket = _gcs.bucket(BUCKET)
_prefix = 'bq_ai_functions/ai_generate'

# Find the data directory (works from repo checkout or notebook directory)
_data = Path('../../data/documents')
if not _data.exists():
    _data = Path('data/documents')

# Upload one invoice and one receipt
for subdir, filename in [('invoices', 'invoice_001.pdf'), ('receipts', 'receipt_001.pdf')]:
    blob = _bucket.blob(f'{_prefix}/{filename}')
    if not blob.exists():
        blob.upload_from_filename(str(_data / subdir / filename))
        print(f'Uploaded {filename} → gs://{BUCKET}/{_prefix}/{filename}')
    else:
        print(f'Already exists: gs://{BUCKET}/{_prefix}/{filename}')
```

### 11. Describe a document with ObjectRef

The ObjectRef pipeline turns a GCS URI into a signed reference that `AI.GENERATE` can read. Pass it in a STRUCT with `prompt` (text) and `object_ref_runtime` (array of signed references) fields.

```python
query = f"""
SELECT
  (AI.GENERATE(
    STRUCT(
      'Describe what this document is and summarize its key details.' AS prompt,
      [OBJ.GET_ACCESS_URL(
        OBJ.FETCH_METADATA(
          OBJ.MAKE_REF(
            'gs://{BUCKET}/bq_ai_functions/ai_generate/invoice_001.pdf',
            '{PROJECT_ID}.{LOCATION}.{CONNECTION_ID}'
          )
        ), 'r'
      )] AS object_ref_runtime
    )
  )).result AS description
"""
df = client.query(query).to_dataframe()
print(df.iloc[0]['description'])
```

### 12. Extract structured data from a document

Combine ObjectRef with `output_schema` to extract typed fields from documents — no Document AI processor needed.

```python
query = f"""
SELECT
  result.vendor_name,
  result.invoice_number,
  result.total_amount,
  result.currency,
  result.invoice_date,
  result.line_item_count
FROM UNNEST([
  AI.GENERATE(
    STRUCT(
      'Extract the key fields from this invoice.' AS prompt,
      [OBJ.GET_ACCESS_URL(
        OBJ.FETCH_METADATA(
          OBJ.MAKE_REF(
            'gs://{BUCKET}/bq_ai_functions/ai_generate/invoice_001.pdf',
            '{PROJECT_ID}.{LOCATION}.{CONNECTION_ID}'
          )
        ), 'r'
      )] AS object_ref_runtime
    ),
    output_schema => 'vendor_name STRING, invoice_number STRING, total_amount FLOAT64, currency STRING, invoice_date STRING, line_item_count INT64'
  )
]) AS result
"""
client.query(query).to_dataframe()
```

### 13. Process multiple documents

Process different document types in a single query by building ObjectRef from a list of URIs.

```python
query = f"""
SELECT
  uri,
  result.document_type,
  result.total_amount,
  result.date,
  result.summary
FROM
  UNNEST([
    'gs://{BUCKET}/bq_ai_functions/ai_generate/invoice_001.pdf',
    'gs://{BUCKET}/bq_ai_functions/ai_generate/receipt_001.pdf'
  ]) AS uri,
  UNNEST([
    AI.GENERATE(
      STRUCT(
        'Identify the document type and extract key details.' AS prompt,
        [OBJ.GET_ACCESS_URL(
          OBJ.FETCH_METADATA(
            OBJ.MAKE_REF(
              uri,
              '{PROJECT_ID}.{LOCATION}.{CONNECTION_ID}'
            )
          ), 'r'
        )] AS object_ref_runtime
      ),
      output_schema => 'document_type STRING, total_amount FLOAT64, date STRING, summary STRING'
    )
  ]) AS result
"""
client.query(query).to_dataframe()
```

---
## Examples — `%%bigquery` Magics

The same examples using IPython magic commands. Magics let you write SQL directly in notebook cells without Python string wrapping.

Key patterns:
- `%%bigquery` — run SQL, display results inline
- `%%bigquery df` — run SQL, capture results into a pandas DataFrame

### Basic call with `%%bigquery`

```sql
%%bigquery --project {PROJECT_ID}

SELECT
  city,
  (AI.GENERATE(
    CONCAT('What country is ', city, ' in? Answer in one word.')
  )).result AS country
FROM UNNEST(['Tokyo', 'Paris', 'Nairobi', 'Lima', 'Sydney']) AS city
```

### Capture results to a DataFrame with `%%bigquery df`

```sql
%%bigquery df_animals --project {PROJECT_ID}

SELECT
  animal,
  result.habitat,
  result.average_lifespan_years,
  result.is_endangered
FROM
  UNNEST(['Eagle', 'Salmon', 'Cobra']) AS animal,
  UNNEST([
    AI.GENERATE(
      CONCAT('Give me facts about: ', animal),
      output_schema => 'habitat STRING, average_lifespan_years INT64, is_endangered BOOL'
    )
  ]) AS result
```

```python
# Now df_animals is a regular pandas DataFrame
print(f'Shape: {df_animals.shape}')
print(f'Columns: {list(df_animals.columns)}')
df_animals
```

### Structured output with field descriptions

```sql
%%bigquery df_products --project {PROJECT_ID}

SELECT
  product,
  result.category,
  result.price_range_usd,
  result.key_features,
  result.needs_batteries
FROM
  UNNEST(['laptop', 'running shoes', 'espresso machine']) AS product,
  UNNEST([
    AI.GENERATE(
      CONCAT('Analyze this product for an e-commerce listing: ', product),
      output_schema => """
        category STRING OPTIONS(description = 'Product category like Electronics, Apparel, Kitchen'),
        price_range_usd STRING OPTIONS(description = 'Estimated price range like $50-$100'),
        key_features ARRAY<STRING> OPTIONS(description = 'Top 3 selling points'),
        needs_batteries BOOL OPTIONS(description = 'Whether the product typically requires batteries')
      """
    )
  ]) AS result
```

```python
df_products
```

### Grounding with Google Search

```sql
%%bigquery --project {PROJECT_ID}

SELECT
  (AI.GENERATE(
    'What were the top 3 news stories today?',
    model_params => JSON '{"tools": [{"googleSearch": {}}]}'
  )).result AS grounded_answer
```

---
## Examples — BigFrames

BigFrames provides a pandas-like interface to BigQuery. The `bigframes.bigquery.ai.generate()` function wraps `AI.GENERATE` for use in Python.

**Key difference from SQL:** Prompts use a **tuple pattern** — a tuple of string literals and Series that get concatenated:
```python
bbq.ai.generate(("Summarize: ", df["text"]))
```

```python
import bigframes.pandas as bpd
import bigframes.bigquery as bbq

bpd.options.bigquery.project = PROJECT_ID
bpd.options.bigquery.location = LOCATION
```

### Basic generation

```python
# Create a BigFrames DataFrame
df = bpd.DataFrame({'city': ['Tokyo', 'Paris', 'Nairobi', 'Lima', 'Sydney']})

# AI.GENERATE with tuple prompt: string literal + Series
df['response'] = bbq.ai.generate(
    ('What country is ', df['city'], ' in? Answer in one word.')
)

# The result is a struct — access .result with struct accessor
df['country'] = df['response'].struct.field('result')
df[['city', 'country']].to_pandas()
```

### Structured output with Pydantic + `bf_schema()`

BigFrames takes `output_schema` as a `dict[str, str]`. Use `bf_schema()` to convert the same Pydantic model.

```python
class AnimalFacts(BaseModel):
    habitat: str
    average_lifespan_years: int
    is_endangered: bool

df_animals = bpd.DataFrame({'animal': ['Eagle', 'Salmon', 'Cobra']})

df_animals['facts'] = bbq.ai.generate(
    ('Give me facts about: ', df_animals['animal']),
    output_schema=bf_schema(AnimalFacts)
)

# Extract structured fields
df_animals['habitat'] = df_animals['facts'].struct.field('habitat')
df_animals['lifespan'] = df_animals['facts'].struct.field('average_lifespan_years')
df_animals['endangered'] = df_animals['facts'].struct.field('is_endangered')

df_animals[['animal', 'habitat', 'lifespan', 'endangered']].to_pandas()
```

### Complex schema with descriptions

```python
# Reuse the ProductAnalysis model defined earlier
# bf_schema() extracts the types (descriptions are SQL-only via bq_schema())
print(bf_schema(ProductAnalysis))

df_products = bpd.DataFrame({'product': ['laptop', 'running shoes', 'espresso machine']})

df_products['analysis'] = bbq.ai.generate(
    ('Analyze this product for an e-commerce listing: ', df_products['product']),
    output_schema=bf_schema(ProductAnalysis)
)

df_products['category'] = df_products['analysis'].struct.field('category')
df_products['price'] = df_products['analysis'].struct.field('price_range_usd')
df_products['features'] = df_products['analysis'].struct.field('key_features')

df_products[['product', 'category', 'price', 'features']].to_pandas()
```

### Specifying an endpoint

```python
df = bpd.DataFrame({'prompt': ['Write a haiku about data warehouses.']})

result = bbq.ai.generate(
    df['prompt'],
    endpoint='gemini-2.5-pro'
)

result.struct.field('result').to_pandas()
```
