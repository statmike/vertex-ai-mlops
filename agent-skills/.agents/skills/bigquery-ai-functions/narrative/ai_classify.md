# AI.CLASSIFY — BigQuery AI Functions

`AI.CLASSIFY` is a managed scalar function that classifies inputs into categories you provide. It supports single-label and multi-label classification with optional category descriptions.

**When to use it:**
- You have a fixed set of categories and want to classify text or images
- You need multi-label classification (items can belong to multiple categories)
- You want BigQuery to auto-optimize classification prompts
- You want to guide classification with few-shot `examples` (pairs of input → expected category)
- You want cost-optimized classification at scale: `optimization_mode => 'MINIMIZE_COST'` with `embeddings` trains a local distilled model (~3,000 row minimum, single-label only)

**Alternatives:**
- `functions/ai_generate` (`AI.GENERATE`) — Full control with output_schema for custom classification logic
- `functions/ai_if` (`AI.IF`) — Boolean classification (yes/no)
- `functions/ai_score` (`AI.SCORE`) — Numeric scoring instead of categorical

**Featured in:** `workflows/content_analysis` (Content Analysis Pipeline) | `workflows/document_intelligence` (Document Intelligence) | `workflows/content_moderation` (Content Moderation)

**Multimodal:** Supports document, image, and video input via `RESOURCES.md#objectref-and-objectrefruntime-schema-reference` (ObjectRef). Pass a STRUCT input with ObjectRefRuntime fields to classify documents, images, or video.

**References:** `RESOURCES.md` (Full syntax reference) | [Official documentation](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-classify) | `setup` (Setup guide)

---
## Setup

Set your project and location, authenticate, and create a temporary dataset for this notebook.

> This function doesn't require a connection or model for SQL usage — it uses end-user credentials automatically. The [multimodal examples](#examples--multimodal-with-objectref) and BigFrames section add a connection for GCS and Vertex AI access. See the `setup` (Setup Reference) for details.

```python
PROJECT_ID = 'statmike-mlops-349915'  # <-- Replace with your project ID
LOCATION = 'US'  # BigQuery dataset location
DATASET_ID = 'bq_ai_functions'  # Shared dataset across all notebooks
CONNECTION_ID = 'bq_ai_functions'  # Shared connection (used by multimodal examples and BigFrames)
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

### 1. Simple classification

`AI.CLASSIFY` takes an input and an array of categories. Returns the best-matching category as STRING.

```python
query = """
SELECT
  review,
  AI.CLASSIFY(
    review,
    ['positive', 'negative', 'neutral']
  ) AS sentiment
FROM UNNEST([
  'Amazing product, exceeded expectations!',
  'Terrible quality, fell apart immediately.',
  'It works as expected. Nothing special.'
]) AS review
"""
client.query(query).to_dataframe()
```

### 2. Categories with descriptions

Provide descriptions to guide the model. Use `STRUCT` pairs: `(category, description)`.

```python
query = """
SELECT
  ticket,
  AI.CLASSIFY(
    ticket,
    [('billing', 'Issues with charges, invoices, or payments'),
     ('technical', 'Product bugs, errors, or how-to questions'),
     ('shipping', 'Delivery, tracking, or logistics issues'),
     ('other', 'Anything not matching the above categories')]
  ) AS category
FROM UNNEST([
  'I was charged twice for my subscription.',
  'The app crashes when I try to upload files.',
  'My package has been in transit for 3 weeks.',
  'Can I get a gift card for my friend?'
]) AS ticket
"""
client.query(query).to_dataframe()
```

### 3. Multi-label classification

Set `output_mode => 'multi'` to allow items to belong to multiple categories. Returns `ARRAY<STRING>`.

```python
query = """
SELECT
  article,
  AI.CLASSIFY(
    article,
    ['technology', 'business', 'science', 'politics', 'health'],
    output_mode => 'multi'
  ) AS categories
FROM UNNEST([
  'New AI regulations proposed by the EU could reshape the tech industry.',
  'Scientists develop a cheaper solar panel that could boost clean energy stocks.',
  'Study shows regular exercise reduces risk of cognitive decline.'
]) AS article
"""
client.query(query).to_dataframe()
```

### 4. Single-label with array output

`output_mode => 'single'` returns an `ARRAY<STRING>` of length 1 — useful when you need consistent array output type.

```python
query = """
SELECT
  email,
  AI.CLASSIFY(
    email,
    ['spam', 'promotional', 'personal', 'work'],
    output_mode => 'single'
  ) AS category
FROM UNNEST([
  'You have won a million dollars! Click here NOW!',
  'Sale: 50% off all items this weekend only.',
  'Hey, are we still meeting for dinner tonight?',
  'Please review the Q3 budget spreadsheet by Friday.'
]) AS email
"""
client.query(query).to_dataframe()
```

### 5. Specifying an endpoint

Override the auto-selected model.

```python
query = """
SELECT
  product,
  AI.CLASSIFY(
    product,
    ['Electronics', 'Clothing', 'Home & Kitchen', 'Sports', 'Books'],
    endpoint => 'gemini-2.5-flash'
  ) AS category
FROM UNNEST([
  'Wireless noise-cancelling headphones',
  'Organic cotton t-shirt',
  'Stainless steel cooking pot set',
  'Yoga mat with carrying strap',
  'Data engineering textbook'
]) AS product
"""
client.query(query).to_dataframe()
```

### 6. Few-shot examples

The `examples` parameter provides input→category pairs that guide the model. For single-label mode, each example is a `STRUCT<STRING, STRING>`. This is useful when category boundaries are ambiguous or domain-specific.

```python
query = """
SELECT
  message,
  AI.CLASSIFY(
    message,
    ['urgent', 'normal', 'low'],
    examples => [
      ('Server is down and customers cannot checkout', 'urgent'),
      ('Update the logo on the about page', 'low'),
      ('Add validation to the signup form', 'normal'),
      ('Database backup failed overnight', 'urgent')
    ]
  ) AS priority
FROM UNNEST([
  'Payment processing is returning 500 errors for all users.',
  'Can we change the font size on the footer?',
  'The search feature should support filters.',
  'SSL certificate expires in 2 hours.'
]) AS message
"""
client.query(query).to_dataframe()
```

### 7. Error ratio control

By default, `AI.CLASSIFY` returns NULL for rows where the model call fails and continues the query. Set `max_error_ratio` (0.0–1.0) to fail the entire query when the error rate exceeds your threshold.

```python
query = """
SELECT
  fruit,
  AI.CLASSIFY(
    fruit,
    ['citrus', 'berry', 'tropical', 'stone fruit'],
    max_error_ratio => 0.0
  ) AS category
FROM UNNEST(['Orange', 'Blueberry', 'Mango', 'Peach', 'Lemon']) AS fruit
"""
client.query(query).to_dataframe()
```

### Optimized mode: `optimization_mode` and `embeddings` (Preview)

For large-scale classification (≥3,000 rows), `AI.CLASSIFY` supports an optimized mode that trains a local distilled model using embeddings:

```sql
SELECT
  ticket,
  AI.CLASSIFY(
    ticket,
    ['billing', 'technical', 'shipping', 'other'],
    embeddings => AI.EMBED(ticket),
    optimization_mode => 'MINIMIZE_COST'
  ) AS category
FROM `my_dataset.support_tickets`  -- needs ~3,000+ rows
```

- `optimization_mode => 'MINIMIZE_COST'` (default when `embeddings` provided) — trains a local model, dramatically reducing Gemini calls
- `optimization_mode => 'MAXIMIZE_QUALITY'` — always uses the remote LLM (ignores embeddings)
- `embeddings` can be generated on-the-fly with `AI.EMBED(...)` or pre-materialized
- **Single-label only** — `output_mode => 'multi'` is not supported in optimized mode
- Not demoed here because the minimum ~3,000 row requirement exceeds our example data size

---
## Examples — Multimodal with ObjectRef

`AI.CLASSIFY` can classify documents, images, and video stored in Cloud Storage. Create an **object table** to reference GCS files, then use `EXTERNAL_OBJECT_TRANSFORM` to get signed references that `AI.CLASSIFY` can read.

```
Object table (GCS URIs + connection)
  → EXTERNAL_OBJECT_TRANSFORM(TABLE, ['SIGNED_URL'])
    → ref column (ObjectRef with signed URL)
      → AI.CLASSIFY(ref, categories)
```

See the `RESOURCES.md#objectref-and-objectrefruntime-schema-reference` (ObjectRef reference) for details.

### Multimodal setup — connection, documents, and object table

ObjectRef requires a `setup` (Cloud resource connection) to access GCS. The cells below create a connection, upload sample documents, and create an object table.

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
_prefix = 'bq_ai_functions/ai_classify'

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

```python
# Create an object table pointing to the uploaded documents
client.query(f"""
CREATE OR REPLACE EXTERNAL TABLE `{PROJECT_ID}.{DATASET_ID}.ai_classify_docs`
WITH CONNECTION `{PROJECT_ID}.{LOCATION}.{CONNECTION_ID}`
OPTIONS (
  object_metadata = 'SIMPLE',
  uris = ['gs://{BUCKET}/bq_ai_functions/ai_classify/*.pdf']
)
""").result()
print('Object table ai_classify_docs ready')
```

### 8. Classify a document

Use `EXTERNAL_OBJECT_TRANSFORM` to get a signed `ref` from the object table, then pass it directly to `AI.CLASSIFY`.

```python
query = f"""
SELECT
  uri,
  AI.CLASSIFY(
    docs.ref,
    ['invoice', 'receipt', 'contract', 'report']
  ) AS document_type
FROM
  EXTERNAL_OBJECT_TRANSFORM(TABLE `{PROJECT_ID}.{DATASET_ID}.ai_classify_docs`,
                            ['SIGNED_URL']) AS docs
"""
client.query(query).to_dataframe()
```

### 9. Classify documents with category descriptions

Add descriptions to guide the model when distinguishing between similar document types.

```python
query = f"""
SELECT
  uri,
  AI.CLASSIFY(
    docs.ref,
    [('invoice', 'A bill for goods or services with line items, totals, and payment terms'),
     ('receipt', 'A proof of purchase showing items bought and amount paid'),
     ('contract', 'A legal agreement between parties with terms and conditions'),
     ('report', 'An analytical document with findings, data, or recommendations')]
  ) AS document_type
FROM
  EXTERNAL_OBJECT_TRANSFORM(TABLE `{PROJECT_ID}.{DATASET_ID}.ai_classify_docs`,
                            ['SIGNED_URL']) AS docs
"""
client.query(query).to_dataframe()
```

---
## Examples — `%%bigquery` Magics

The same examples using IPython magic commands. Magics let you write SQL directly in notebook cells without Python string wrapping.

Key patterns:
- `%%bigquery` — run SQL, display results inline
- `%%bigquery df` — run SQL, capture results into a pandas DataFrame

### Single-label classification

```sql
%%bigquery --project {PROJECT_ID}

SELECT
  review,
  AI.CLASSIFY(
    review,
    ['positive', 'negative', 'neutral']
  ) AS sentiment
FROM UNNEST([
  'Love it!', 'Terrible.', 'It was okay.', 'Best purchase ever!'
]) AS review
```

### Multi-label classification

```sql
%%bigquery df_classified --project {PROJECT_ID}

SELECT
  article,
  AI.CLASSIFY(
    article,
    ['technology', 'business', 'science', 'health'],
    output_mode => 'multi'
  ) AS categories
FROM UNNEST([
  'AI regulations could reshape tech industry profits.',
  'New drug shows promise in clinical trials for rare disease.'
]) AS article
```

```python
df_classified
```

---
## Examples — BigFrames

BigFrames wraps `AI.CLASSIFY` via `bbq.ai.classify()`. It returns a Series of STRING directly.

**Key patterns:**
- Takes `categories` as a list/tuple
- Returns STRING directly (single label)
- Example: `bbq.ai.classify(df["text"], ["positive", "negative", "neutral"])`

```python
import bigframes.pandas as bpd
import bigframes.bigquery as bbq

bpd.close_session()  # Reset session to apply connection settings
bpd.options.bigquery.project = PROJECT_ID
bpd.options.bigquery.location = LOCATION
bpd.options.bigquery.bq_connection = f'{PROJECT_ID}.{LOCATION}.{CONNECTION_ID}'
```

### Classification

```python
df = bpd.DataFrame({'review': [
    'Amazing product!', 'Terrible quality.', 'Pretty good.', 'Awful experience.'
]})

df['sentiment'] = bbq.ai.classify(df['review'], ['positive', 'negative', 'neutral'])
df.to_pandas()
```
