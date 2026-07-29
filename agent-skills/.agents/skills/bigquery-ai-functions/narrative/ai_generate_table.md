# AI.GENERATE_TABLE — BigQuery AI Functions

`AI.GENERATE_TABLE` is a table-valued function that generates structured output columns from a user-defined schema. It requires a remote Gemini model and an `output_schema` — making it ideal for extracting typed, multi-column results.

**When to use it:**
- You need structured output with multiple typed columns from a TVF
- You want to generate sample/synthetic data with specific column types
- You need entity extraction with a defined schema
- You prefer the TVF interface over the scalar AI.GENERATE

**Alternatives:**
- `functions/ai_generate` (`AI.GENERATE`) — Scalar function with output_schema, no model required
- `functions/ai_generate_text` (`AI.GENERATE_TEXT`) — TVF for free-form text output, multi-provider

**Featured in:** `workflows/content_analysis` (Content Analysis Pipeline) | `workflows/rag_pipeline` (RAG Pipeline) | `workflows/content_moderation` (Content Moderation)

**Multimodal:** Supports document, image, and video input via `RESOURCES.md#objectref-and-objectrefruntime-schema-reference` (ObjectRef). Pass a STRUCT prompt with ObjectRefRuntime fields to extract structured data from unstructured files.

**References:** `RESOURCES.md` (Full syntax reference) | [Official documentation](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-generate-table) | `setup` (Setup guide)

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

### 1. Simple structured output

Provide an `output_schema` to get typed columns. Each input row produces one output row with your schema fields.

```python
query = f'''
SELECT prompt, category, sentiment, confidence
FROM AI.GENERATE_TABLE(
  MODEL `{PROJECT_ID}.{DATASET_ID}.gemini_flash`,
  (SELECT 'Analyze: Great product, love it!' AS prompt),
  STRUCT('category STRING, sentiment STRING, confidence FLOAT64' AS output_schema)
)
'''
client.query(query).to_dataframe()
```

### 2. Multiple rows with schema

Process multiple rows — each gets its own structured output.

```python
query = f'''
SELECT review, sentiment, confidence
FROM AI.GENERATE_TABLE(
  MODEL `{PROJECT_ID}.{DATASET_ID}.gemini_flash`,
  (SELECT CONCAT('Analyze this review: ', review) AS prompt, review
   FROM UNNEST(['Amazing quality!', 'Terrible, broke instantly.', 'It was okay.']) AS review),
  STRUCT('sentiment STRING, confidence FLOAT64' AS output_schema)
)
'''
client.query(query).to_dataframe()
```

### 3. Schema with field descriptions

Add `OPTIONS(description = ...)` to guide the model on what each field means.

```python
query = f'''
SELECT city, country, population_millions, continent, famous_landmark
FROM AI.GENERATE_TABLE(
  MODEL `{PROJECT_ID}.{DATASET_ID}.gemini_flash`,
  (SELECT CONCAT('Give me facts about: ', city) AS prompt, city
   FROM UNNEST([\'Tokyo\', \'Paris\', \'Nairobi\']) AS city),
  STRUCT(
    'country STRING OPTIONS(description = "Country name"), population_millions FLOAT64 OPTIONS(description = "City population in millions"), continent STRING OPTIONS(description = "Continent"), famous_landmark STRING OPTIONS(description = "Most famous landmark")' AS output_schema
  )
)
'''
client.query(query).to_dataframe()
```

### 4. Generating sample data

AI.GENERATE_TABLE produces one output row per input row. To generate multiple items, provide multiple input rows — one per desired output.

```python
query = f'''
SELECT product_name, category, price_usd, rating, in_stock
FROM AI.GENERATE_TABLE(
  MODEL `{PROJECT_ID}.{DATASET_ID}.gemini_flash`,
  (SELECT CONCAT('Generate a realistic e-commerce product in the ', cat, ' category.') AS prompt
   FROM UNNEST(['Electronics', 'Clothing', 'Home & Kitchen', 'Sports', 'Books']) AS cat),
  STRUCT(
    'product_name STRING, category STRING, price_usd FLOAT64, rating FLOAT64, in_stock BOOL' AS output_schema
  )
)
'''
client.query(query).to_dataframe()
```

### 5. Array output fields

Schema fields can be arrays for multi-valued outputs.

```python
query = f'''
SELECT topic, summary, key_points
FROM AI.GENERATE_TABLE(
  MODEL `{PROJECT_ID}.{DATASET_ID}.gemini_flash`,
  (SELECT CONCAT('Summarize the key aspects of: ', topic) AS prompt, topic
   FROM UNNEST(['Machine Learning', 'Cloud Computing']) AS topic),
  STRUCT('summary STRING, key_points ARRAY<STRING>' AS output_schema)
)
'''
client.query(query).to_dataframe()
```

### 6. Entity extraction

Use AI.GENERATE_TABLE to extract structured entities from unstructured text.

```python
query = f'''
SELECT text, person_name, organization, location, date_mentioned
FROM AI.GENERATE_TABLE(
  MODEL `{PROJECT_ID}.{DATASET_ID}.gemini_flash`,
  (SELECT text,
   CONCAT('Extract entities from this text: ', text) AS prompt
   FROM UNNEST([
     'Tim Cook announced new Apple products at the Cupertino event on March 15, 2025.',
     'Satya Nadella presented AI strategy at the Build conference in Seattle.'
   ]) AS text),
  STRUCT('person_name STRING, organization STRING, location STRING, date_mentioned STRING' AS output_schema)
)
'''
client.query(query).to_dataframe()
```

### 7. Using Pydantic to define schemas

Define your schema as a Python class with type hints and descriptions. Then convert it to the SQL schema string that `AI.GENERATE_TABLE` expects. This gives you type safety, reusability, and auto-generated field descriptions.

```python
from pydantic import BaseModel, Field

# Define the schema as a Pydantic model
class ProductReview(BaseModel):
    sentiment: str = Field(description="positive, negative, or neutral")
    confidence: float = Field(description="Confidence score from 0.0 to 1.0")
    topics: list[str] = Field(description="Key topics mentioned in the review")
    recommendation: bool = Field(description="Whether the reviewer would recommend the product")

# Convert Pydantic model to BigQuery SQL schema string
def pydantic_to_bq_schema(model_class):
    """Convert a Pydantic model to a BigQuery output_schema string."""
    type_map = {
        'string': 'STRING', 'number': 'FLOAT64',
        'integer': 'INT64', 'boolean': 'BOOL',
    }
    schema = model_class.model_json_schema()
    parts = []
    for name, prop in schema['properties'].items():
        # Handle arrays
        if prop.get('type') == 'array':
            item_type = type_map.get(prop.get('items', {}).get('type', 'string'), 'STRING')
            bq_type = f'ARRAY<{item_type}>'
        else:
            bq_type = type_map.get(prop.get('type', 'string'), 'STRING')
        desc = prop.get('description', '')
        if desc:
            parts.append(f'{name} {bq_type} OPTIONS(description = "{desc}")')
        else:
            parts.append(f'{name} {bq_type}')
    return ', '.join(parts)

# Generate the schema string
schema_str = pydantic_to_bq_schema(ProductReview)
print(f'Schema:\n{schema_str}\n')

# Use it in a query
query = f'''
SELECT review, sentiment, confidence, topics, recommendation
FROM AI.GENERATE_TABLE(
  MODEL `{PROJECT_ID}.{DATASET_ID}.gemini_flash`,
  (SELECT CONCAT('Analyze this product review: ', review) AS prompt, review
   FROM UNNEST([
     'Absolutely love this laptop! Fast processor, great battery life. Best purchase this year.',
     'The fabric started pilling after two washes. Sizing runs small. Would not buy again.',
     'Decent headphones for the price. Sound quality is average but comfortable to wear.'
   ]) AS review),
  STRUCT('{schema_str}' AS output_schema)
)
'''
client.query(query).to_dataframe()
```

---
## Examples — Multimodal with ObjectRef

`AI.GENERATE_TABLE` can extract structured data from documents, images, and video stored in Cloud Storage. Use the **ObjectRef pipeline** to create a STRUCT prompt with signed references:

```
OBJ.MAKE_REF(uri, connection)        → ObjectRef
  → OBJ.FETCH_METADATA(objectref)    → adds content type and size
    → OBJ.GET_ACCESS_URL(ref, 'r')   → ObjectRefRuntime (signed URL)
```

The STRUCT prompt replaces the STRING prompt in the input table. See the `RESOURCES.md#objectref-and-objectrefruntime-schema-reference` (ObjectRef reference) for details.

```python
from google.cloud import storage as _storage
from pathlib import Path

_gcs = _storage.Client(project=PROJECT_ID)
_bucket = _gcs.bucket(BUCKET)
_prefix = 'bq_ai_functions/ai_generate_table'

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

### 8. Extract structured data from a document

Pass a document via ObjectRef in the prompt column and extract typed fields with `output_schema`. The STRUCT prompt contains both text and `object_ref_runtime`.

```python
query = f"""
SELECT vendor_name, invoice_number, total_amount, currency, invoice_date, line_item_count
FROM AI.GENERATE_TABLE(
  MODEL `{PROJECT_ID}.{DATASET_ID}.gemini_flash`,
  (SELECT STRUCT(
    'Extract the key fields from this invoice.' AS prompt,
    [OBJ.GET_ACCESS_URL(
      OBJ.FETCH_METADATA(
        OBJ.MAKE_REF(
          'gs://{BUCKET}/bq_ai_functions/ai_generate_table/invoice_001.pdf',
          '{PROJECT_ID}.{LOCATION}.{CONNECTION_ID}'
        )
      ), 'r'
    )] AS object_ref_runtime
  ) AS prompt),
  STRUCT('vendor_name STRING, invoice_number STRING, total_amount FLOAT64, currency STRING, invoice_date STRING, line_item_count INT64' AS output_schema)
)
"""
client.query(query).to_dataframe()
```

### 9. Process multiple documents with detailed extraction

Process different document types in a single query. Use `UNNEST` to build ObjectRef from a list of URIs, with a richer schema including arrays.

```python
query = f"""
SELECT
  uri,
  document_type,
  vendor_or_store,
  total_amount,
  date,
  line_items
FROM AI.GENERATE_TABLE(
  MODEL `{PROJECT_ID}.{DATASET_ID}.gemini_flash`,
  (SELECT
    uri,
    STRUCT(
      'Identify the document type and extract all details.' AS prompt,
      [OBJ.GET_ACCESS_URL(
        OBJ.FETCH_METADATA(
          OBJ.MAKE_REF(
            uri,
            '{PROJECT_ID}.{LOCATION}.{CONNECTION_ID}'
          )
        ), 'r'
      )] AS object_ref_runtime
    ) AS prompt
   FROM UNNEST([
     'gs://{BUCKET}/bq_ai_functions/ai_generate_table/invoice_001.pdf',
     'gs://{BUCKET}/bq_ai_functions/ai_generate_table/receipt_001.pdf'
   ]) AS uri),
  STRUCT('document_type STRING, vendor_or_store STRING, total_amount FLOAT64, date STRING, line_items ARRAY<STRING>' AS output_schema)
)
"""
client.query(query).to_dataframe()
```

---
## Examples — `%%bigquery` Magics

The same examples using IPython magic commands. Magics let you write SQL directly in notebook cells without Python string wrapping.

Key patterns:
- `%%bigquery` — run SQL, display results inline
- `%%bigquery df` — run SQL, capture results into a pandas DataFrame

### Structured output with `%%bigquery`

Since AI.GENERATE_TABLE requires `MODEL` references, most usage is better via `client.query()` with f-strings. Here is one example with hardcoded references.

```sql
%%bigquery --project {PROJECT_ID}

SELECT product_name, category, price_usd
FROM AI.GENERATE_TABLE(
  MODEL `statmike-mlops-349915.bq_ai_functions.gemini_flash`,
  (SELECT CONCAT('Generate a realistic product in the ', cat, ' category.') AS prompt
   FROM UNNEST(['Electronics', 'Clothing', 'Books']) AS cat),
  STRUCT('product_name STRING, category STRING, price_usd FLOAT64' AS output_schema)
)
```

---
## Examples — BigFrames

BigFrames wraps `AI.GENERATE_TABLE` via `bbq.ai.generate_table()`. It takes a model name, DataFrame, and an `output_schema`.

`output_schema` can be a string or a dict mapping column names to types.

```python
import bigframes.pandas as bpd
import bigframes.bigquery as bbq

bpd.options.bigquery.project = PROJECT_ID
bpd.options.bigquery.location = LOCATION
```

### Structured output

```python
df = bpd.DataFrame({
    'prompt': [
        'Analyze: Great product, love it!',
        'Analyze: Terrible quality.',
        'Analyze: Average, nothing special.',
    ]
})

model_name = f'{PROJECT_ID}.{DATASET_ID}.gemini_flash'
result = bbq.ai.generate_table(
    model_name, df,
    output_schema={'sentiment': 'STRING', 'confidence': 'FLOAT64'}
)

result[['prompt', 'sentiment', 'confidence']].to_pandas()
```

### Pydantic schema with BigFrames

The same Pydantic model works with BigFrames — convert to a dict instead of a SQL string.

```python
# Convert Pydantic model to BigFrames output_schema dict
def pydantic_to_bf_schema(model_class):
    """Convert a Pydantic model to a BigFrames output_schema dict."""
    type_map = {
        'string': 'STRING', 'number': 'FLOAT64',
        'integer': 'INT64', 'boolean': 'BOOL',
    }
    schema = model_class.model_json_schema()
    result = {}
    for name, prop in schema['properties'].items():
        if prop.get('type') == 'array':
            item_type = type_map.get(prop.get('items', {}).get('type', 'string'), 'STRING')
            result[name] = f'ARRAY<{item_type}>'
        else:
            result[name] = type_map.get(prop.get('type', 'string'), 'STRING')
    return result

bf_schema = pydantic_to_bf_schema(ProductReview)
print(f'BigFrames schema: {bf_schema}\n')

df = bpd.DataFrame({'prompt': [
    'Analyze this review: Great laptop, fast and reliable!',
    'Analyze this review: Terrible quality, broke after a week.',
]})

result = bbq.ai.generate_table(
    f'{PROJECT_ID}.{DATASET_ID}.gemini_flash', df,
    output_schema=bf_schema
)
result[['prompt', 'sentiment', 'confidence', 'recommendation']].to_pandas()
```
