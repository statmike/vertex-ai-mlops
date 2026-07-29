# AI.AGG — BigQuery AI Functions

`AI.AGG` is an aggregate function that uses a Gemini model to aggregate data based on natural language instructions. It automatically handles multi-level batching, so it can analyze data that exceeds the Gemini context window.

**When to use it:**
- You need to summarize, analyze, or find patterns across groups of rows
- Your data may exceed the Gemini context window (AI.AGG auto-batches)
- You want one result per GROUP BY group, not one per row

**Alternatives:**
- `functions/ai_generate` (`AI.GENERATE`) — Per-row generation. For aggregation, you'd need to manually batch data into a single prompt (e.g., with `STRING_AGG` or `ARRAY_AGG` + `TO_JSON_STRING`)
- `functions/ai_generate_text` (`AI.GENERATE_TEXT`) — Same manual batching issue, but supports non-Gemini models

**Key differences from AI.GENERATE:**
- `AI.AGG` is an **aggregate** function (like `SUM`, `COUNT`) — use with `GROUP BY`
- `AI.GENERATE` is a **scalar** function — returns one result per input row
- `AI.AGG` automatically batches large datasets; `AI.GENERATE` requires manual batching

**Featured in:** `workflows/content_analysis` (Content Analysis Pipeline) | `workflows/content_moderation` (Content Moderation) | `workflows/document_intelligence` (Document Intelligence) | `workflows/log_analysis` (Log Analysis)

**Multimodal:** Supports image input via `RESOURCES.md#objectref-and-objectrefruntime-schema-reference` (ObjectRef). Pass a STRUCT input with ObjectRefRuntime fields to aggregate over images.

**References:** `RESOURCES.md` (Full syntax reference) | [Official documentation](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-agg) | `setup` (Setup guide)

---
## Setup

Set your project and location, authenticate, and create a temporary dataset for this notebook.

> This function doesn't require a connection or model for basic SQL usage — it uses end-user credentials automatically. A connection is needed for the `connection_id` parameter and multimodal examples. See the `setup` (Setup Reference) for details.

```python
PROJECT_ID = 'statmike-mlops-349915'  # <-- Replace with your project ID
LOCATION = 'US'  # BigQuery dataset location
DATASET_ID = 'bq_ai_functions'  # Shared dataset across all notebooks
CONNECTION_ID = 'bq_ai_functions'  # Shared connection (for connection_id and multimodal examples)
BUCKET = PROJECT_ID  # GCS bucket for multimodal examples
```

### Environment

> **Already set up the project environment?** Skip to [Examples](#examples--sql).  
> **Running standalone** (Colab, Colab Enterprise, Vertex AI Workbench)? Run the cells below to install packages, authenticate, and create the shared dataset. See the `setup` (Setup Reference) for details.

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

---
## Examples — SQL

Progressive examples from simplest to most advanced. Each cell adds one new concept.

`AI.AGG` is an **aggregate function** — it works like `SUM()` or `COUNT()`. Without `GROUP BY`, it aggregates all rows into one result. With `GROUP BY`, it returns one result per group.

### 1. Simplest call — aggregate without GROUP BY

Without `GROUP BY`, `AI.AGG` aggregates all input rows into a single summary.

```python
query = """
SELECT
  AI.AGG(
    review,
    'What is the overall sentiment of these reviews?'
  ) AS sentiment_summary
FROM UNNEST([
  'Absolutely love this product! Best purchase ever.',
  'Terrible quality, broke after one week.',
  'Pretty decent for the price. Nothing fancy.',
  'Would not recommend. Waste of money.',
  'Exceeded my expectations in every way!'
]) AS review
"""
df = client.query(query).to_dataframe()
print(df.iloc[0]['sentiment_summary'])
```

### 2. GROUP BY — one summary per group

`AI.AGG` returns one STRING per group, making it ideal for summarizing data by category.

```python
query = """
SELECT
  category,
  AI.AGG(
    feedback,
    'Summarize the main themes in this feedback.'
  ) AS themes
FROM UNNEST([
  STRUCT('product' AS category, 'The battery life is incredible' AS feedback),
  STRUCT('product', 'Screen quality is outstanding'),
  STRUCT('product', 'Too heavy to carry around comfortably'),
  STRUCT('shipping', 'Arrived two days early, great packaging'),
  STRUCT('shipping', 'Package was damaged during transit'),
  STRUCT('shipping', 'Delivery took three weeks instead of five days'),
  STRUCT('support', 'Agent resolved my issue in minutes'),
  STRUCT('support', 'Was on hold for over an hour before getting help'),
  STRUCT('support', 'Very knowledgeable and patient support team')
]) AS t
GROUP BY category
"""
client.query(query).to_dataframe()
```

### 3. DISTINCT — deduplicate before aggregating

Use `DISTINCT` to remove duplicate inputs before sending them to the model.

```python
query = """
SELECT
  AI.AGG(
    DISTINCT comment,
    'What topics do these comments discuss?'
  ) AS topics
FROM UNNEST([
  'Great performance on the new update',
  'Great performance on the new update',
  'Battery drain is still an issue',
  'Battery drain is still an issue',
  'Love the new camera features',
  'UI feels sluggish after the patch'
]) AS comment
"""
df = client.query(query).to_dataframe()
print(df.iloc[0]['topics'])
```

### 4. TO_JSON_STRING — aggregate structured rows

Use `TO_JSON_STRING` to pass multiple columns as context. The model sees each row's full structure.

```python
query = """
WITH tickets AS (
  SELECT *
  FROM UNNEST([
    STRUCT('Alice' AS agent, 'password reset' AS issue, 2 AS resolution_minutes),
    STRUCT('Alice', 'account locked', 5),
    STRUCT('Bob', 'billing error', 15),
    STRUCT('Bob', 'refund request', 30),
    STRUCT('Bob', 'subscription cancel', 8),
    STRUCT('Carol', 'login failure', 3),
    STRUCT('Carol', 'two-factor setup', 7)
  ])
)
SELECT
  agent,
  AI.AGG(
    TO_JSON_STRING(STRUCT(agent, issue, resolution_minutes)),
    'Analyze this support agent performance. What types of issues do they handle and how quickly?'
  ) AS performance_summary
FROM tickets
GROUP BY agent
"""
client.query(query).to_dataframe()
```

### 5. Finding patterns across data

`AI.AGG` excels at root cause analysis and pattern identification across structured log data.

```python
query = """
WITH error_logs AS (
  SELECT *
  FROM UNNEST([
    STRUCT('2025-01-15 08:23:01' AS timestamp, 'auth-service' AS service, 'Connection timeout to user DB' AS message),
    STRUCT('2025-01-15 08:23:05', 'auth-service', 'Failed to validate token: DB unavailable'),
    STRUCT('2025-01-15 08:23:12', 'api-gateway', 'Upstream auth-service returned 503'),
    STRUCT('2025-01-15 08:23:15', 'api-gateway', 'Circuit breaker opened for auth-service'),
    STRUCT('2025-01-15 08:24:00', 'payment-service', 'Transaction failed: auth token invalid'),
    STRUCT('2025-01-15 08:24:02', 'notification-service', 'Unable to send email: rate limit exceeded'),
    STRUCT('2025-01-15 08:25:00', 'auth-service', 'Connection to user DB restored'),
    STRUCT('2025-01-15 08:25:01', 'api-gateway', 'Circuit breaker closed for auth-service')
  ])
)
SELECT
  AI.AGG(
    TO_JSON_STRING(STRUCT(timestamp, service, message)),
    'Analyze these error logs. What was the root cause, which services were affected, and what was the sequence of events?'
  ) AS incident_analysis
FROM error_logs
"""
df = client.query(query).to_dataframe()
print(df.iloc[0]['incident_analysis'])
```

### 6. Specifying an endpoint

Override the default model with any Gemini model that doesn't require thinking budget.

```python
query = """
SELECT
  AI.AGG(
    review,
    'What do customers like and dislike? Be concise.',
    endpoint => 'gemini-2.5-flash'
  ) AS summary
FROM UNNEST([
  'Fast delivery but the box was crushed.',
  'Product works great, very happy with it.',
  'Instructions were confusing but the item itself is solid.'
]) AS review
"""
df = client.query(query).to_dataframe()
print(df.iloc[0]['summary'])
```

### 7. Using a public dataset

Analyze real IMDB reviews grouped by movie — demonstrates AI.AGG's ability to handle large groups with automatic batching.

```python
query = """
SELECT
  title,
  movie_id,
  AI.AGG(
    review,
    'Summarize the overall sentiment towards this movie.'
  ) AS sentiment
FROM `bigquery-public-data.imdb.reviews`
WHERE movie_id IN ('tt0339384', 'tt0084787', 'tt0029850')
GROUP BY movie_id, title
"""
client.query(query).to_dataframe()
```

### 8. Using connection_id — service account credentials

By default, `AI.AGG` uses end-user credentials. The `connection_id` parameter lets you use a Cloud resource connection's service account instead — useful for shared environments, production pipelines, or when end-user credentials don't have Vertex AI access.

```python
query = f"""
SELECT
  AI.AGG(
    review,
    'What is the overall sentiment of these reviews?',
    connection_id => '{PROJECT_ID}.{LOCATION}.{CONNECTION_ID}'
  ) AS sentiment_summary
FROM UNNEST([
  'Absolutely love this product! Best purchase ever.',
  'Terrible quality, broke after one week.',
  'Pretty decent for the price. Nothing fancy.',
  'Would not recommend. Waste of money.',
  'Exceeded my expectations in every way!'
]) AS review
"""
df = client.query(query).to_dataframe()
print(df.iloc[0]['sentiment_summary'])
```

### 9. Quantitative aggregation — counting and ranking

`AI.AGG` isn't limited to text summaries. It can count, rank, compare quantities, and extract structured insights from data — treating the model as an analyst, not just a summarizer.

```python
query = """
WITH tasks AS (
  SELECT *
  FROM UNNEST([
    STRUCT('backend' AS team, 'critical' AS priority, 'Fix auth token expiry' AS task),
    STRUCT('backend', 'critical', 'Patch SQL injection vulnerability'),
    STRUCT('backend', 'high', 'Optimize query performance'),
    STRUCT('backend', 'medium', 'Add request logging'),
    STRUCT('frontend', 'critical', 'Fix checkout form validation'),
    STRUCT('frontend', 'high', 'Implement dark mode'),
    STRUCT('frontend', 'high', 'Add accessibility labels'),
    STRUCT('frontend', 'low', 'Update footer copyright year'),
    STRUCT('data', 'critical', 'Fix broken ETL pipeline'),
    STRUCT('data', 'high', 'Add data quality checks'),
    STRUCT('data', 'medium', 'Document schema changes'),
    STRUCT('data', 'medium', 'Archive old partitions')
  ])
)
SELECT
  AI.AGG(
    TO_JSON_STRING(STRUCT(team, priority, task)),
    'Count the tasks by priority level for each team. Which team has the most critical items? Present as a concise breakdown.'
  ) AS task_analysis
FROM tasks
"""
df = client.query(query).to_dataframe()
print(df.iloc[0]['task_analysis'])
```

### 10. AI.AGG vs manual STRING_AGG + AI.GENERATE

Before `AI.AGG`, aggregating data required manually concatenating rows into a single prompt with `STRING_AGG` + `AI.GENERATE`. This works for small datasets but breaks when data exceeds the context window. `AI.AGG` handles batching automatically.

Compare both approaches on the same data:

```python
query = """
WITH feedback AS (
  SELECT *
  FROM UNNEST([
    STRUCT('product' AS category, 'The battery life is incredible' AS comment),
    STRUCT('product', 'Screen quality is outstanding'),
    STRUCT('product', 'Too heavy to carry around comfortably'),
    STRUCT('shipping', 'Arrived two days early, great packaging'),
    STRUCT('shipping', 'Package was damaged during transit'),
    STRUCT('shipping', 'Delivery took three weeks instead of five days')
  ])
),

-- Approach 1: Manual STRING_AGG + AI.GENERATE (the old way)
manual_approach AS (
  SELECT
    category,
    (AI.GENERATE(
      CONCAT(
        'Summarize the main themes in this feedback: ',
        STRING_AGG(comment, ' | ')
      )
    )).result AS themes
  FROM feedback
  GROUP BY category
),

-- Approach 2: AI.AGG (the better way)
agg_approach AS (
  SELECT
    category,
    AI.AGG(comment, 'Summarize the main themes in this feedback.') AS themes
  FROM feedback
  GROUP BY category
)

SELECT
  'STRING_AGG + AI.GENERATE' AS approach,
  category, themes
FROM manual_approach
UNION ALL
SELECT
  'AI.AGG' AS approach,
  category, themes
FROM agg_approach
ORDER BY category, approach
"""
client.query(query).to_dataframe()
```

### 11. Multimodal — aggregate documents with ObjectRef

`AI.AGG` supports multimodal input via ObjectRef. Pass a `STRUCT` containing `OBJ.GET_ACCESS_URL(ref, 'r')` to aggregate over files stored in Cloud Storage.

> **Note:** Multimodal `AI.AGG` currently works with images. PDF support returns NULL (preview limitation). The syntax below shows the pattern — uncomment and run when image-based object tables are available.

```python
# from google.cloud import storage
# from pathlib import Path
#
# gcs = storage.Client(project=PROJECT_ID)
# bucket = gcs.bucket(BUCKET)
# prefix = 'bq_ai_functions/ai_agg_docs'
#
# data_dir = Path('../../data/documents')
# if not data_dir.exists():
#     data_dir = Path('data/documents')
#
# files_to_upload = [
#     ('invoices/invoice_001.pdf', 'invoice_001.pdf'),
#     ('invoices/invoice_002.pdf', 'invoice_002.pdf'),
#     ('invoices/invoice_003.pdf', 'invoice_003.pdf'),
#     ('receipts/receipt_001.pdf', 'receipt_001.pdf'),
#     ('receipts/receipt_002.pdf', 'receipt_002.pdf'),
#     ('receipts/receipt_003.pdf', 'receipt_003.pdf'),
# ]
#
# for src, dst in files_to_upload:
#     blob = bucket.blob(f'{prefix}/{dst}')
#     if not blob.exists():
#         blob.upload_from_filename(str(data_dir / src))
# print(f'{len(files_to_upload)} documents uploaded to gs://{BUCKET}/{prefix}/')
#
# client.query(f"""
# CREATE OR REPLACE EXTERNAL TABLE `{PROJECT_ID}.{DATASET_ID}.ai_agg_docs`
# WITH CONNECTION `{PROJECT_ID}.{LOCATION}.{CONNECTION_ID}`
# OPTIONS (
#   object_metadata = 'SIMPLE',
#   uris = ['gs://{BUCKET}/{prefix}/*.pdf']
# )
# """).result()
# print('Object table ai_agg_docs ready')
```

```python
# query = f"""
# SELECT
#   AI.AGG(
#     STRUCT(OBJ.GET_ACCESS_URL(ref, 'r')),
#     'These are financial documents (invoices and receipts). Summarize the types of documents, the vendors/stores involved, and the typical transaction amounts.',
#     connection_id => '{PROJECT_ID}.{LOCATION}.{CONNECTION_ID}'
#   ) AS document_summary
# FROM
#   `{PROJECT_ID}.{DATASET_ID}.ai_agg_docs`
# """
# df = client.query(query).to_dataframe()
# print(df.iloc[0]['document_summary'])
```

```python
# # Cleanup multimodal resources
# client.query(f'DROP EXTERNAL TABLE IF EXISTS `{PROJECT_ID}.{DATASET_ID}.ai_agg_docs`').result()
# blobs = list(bucket.list_blobs(prefix=prefix))
# for blob in blobs:
#     blob.delete()
# print(f'Cleaned up object table and {len(blobs)} GCS files')
```

---
## Examples — `%%bigquery` Magics

The same examples using IPython magic commands. Magics let you write SQL directly in notebook cells without Python string wrapping.

Key patterns:
- `%%bigquery` — run SQL, display results inline
- `%%bigquery df` — run SQL, capture results into a pandas DataFrame

### Simple aggregation

```sql
%%bigquery --project {PROJECT_ID}

SELECT
  AI.AGG(
    review,
    'What is the overall sentiment?'
  ) AS sentiment
FROM UNNEST([
  'Love it!', 'Terrible.', 'It was okay.', 'Best purchase ever!'
]) AS review
```

### Aggregation with GROUP BY — capture to DataFrame

```sql
%%bigquery df_agg --project {PROJECT_ID}

SELECT
  category,
  AI.AGG(
    feedback,
    'Summarize the main themes.'
  ) AS themes
FROM UNNEST([
  STRUCT('product' AS category, 'Battery life is great' AS feedback),
  STRUCT('product', 'Too heavy'),
  STRUCT('shipping', 'Fast delivery'),
  STRUCT('shipping', 'Box was damaged')
]) AS t
GROUP BY category
```

```python
df_agg
```

---
## Examples — BigFrames

There is no native BigFrames API for `AI.AGG` yet. Use `session.read_gbq_query()` to execute AI.AGG queries and get results as a BigFrames DataFrame.

```python
import bigframes.pandas as bpd

bpd.close_session()  # Reset session to apply connection settings
bpd.options.bigquery.project = PROJECT_ID
bpd.options.bigquery.location = LOCATION
```

### AI.AGG via `read_gbq_query()`

```python
query = """
SELECT
  category,
  AI.AGG(
    feedback,
    'Summarize the key themes in this feedback. Keep it concise.'
  ) AS themes
FROM UNNEST([
  STRUCT('product' AS category, 'Battery life is incredible' AS feedback),
  STRUCT('product', 'Screen quality is outstanding'),
  STRUCT('product', 'Too heavy to carry'),
  STRUCT('shipping', 'Arrived early, great packaging'),
  STRUCT('shipping', 'Package was damaged'),
  STRUCT('support', 'Quick and helpful response'),
  STRUCT('support', 'Long hold time before getting help')
]) AS t
GROUP BY category
"""
bf_df = bpd.read_gbq_query(query)
bf_df.to_pandas()
```
