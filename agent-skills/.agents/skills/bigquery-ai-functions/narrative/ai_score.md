# AI.SCORE — BigQuery AI Functions

`AI.SCORE` is a managed scalar function that rates inputs on a scale you describe and returns a FLOAT64. BigQuery automatically generates a scoring rubric to improve consistency.

**When to use it:**
- You want to rank or rate items using natural language scoring criteria
- You need consistent numeric scores for ordering (ORDER BY) or filtering
- You want BigQuery to auto-generate a scoring rubric
- You want to fail the query when too many rows error: set `max_error_ratio` (0.0–1.0)

**Alternatives:**
- `functions/ai_generate_double` (`AI.GENERATE_DOUBLE`) — More control over model and parameters, returns STRUCT
- `functions/ai_generate` (`AI.GENERATE`) — Full control with output_schema for multiple output fields
- `functions/ai_classify` (`AI.CLASSIFY`) — Categorical classification instead of numeric scoring

**Featured in:** `workflows/content_analysis` (Content Analysis Pipeline) | `workflows/document_intelligence` (Document Intelligence) | `workflows/content_moderation` (Content Moderation)

**Multimodal:** Supports document, image, and video input via `RESOURCES.md#objectref-and-objectrefruntime-schema-reference` (ObjectRef). Pass a STRUCT input with ObjectRefRuntime fields to score unstructured data.

**References:** `RESOURCES.md` (Full syntax reference) | [Official documentation](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-score) | `setup` (Setup guide)

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

### 1. Basic scoring

`AI.SCORE` takes a prompt describing scoring criteria and returns a FLOAT64 directly.

**Important:** There is no fixed default range. Always specify a range in your prompt (e.g., "on a scale of 1 to 10").

```python
query = """
SELECT
  review,
  AI.SCORE(CONCAT('Rate the positivity of this review on a scale of 1 to 10: ', review)) AS positivity_score
FROM UNNEST([
  'Amazing product, exceeded all my expectations!',
  'It was okay, nothing special.',
  'Terrible quality. Completely disappointed.',
  'Good value for the price. Would buy again.'
]) AS review
"""
client.query(query).to_dataframe()
```

### 2. Ranking with ORDER BY

Use `AI.SCORE` with `ORDER BY` to rank items.

```python
query = """
SELECT
  resume,
  AI.SCORE(CONCAT(
    'Rate this resume summary for a data engineer role on a scale of 1 to 10, ',
    'where 10 is perfectly qualified: ', resume
  )) AS qualification_score
FROM UNNEST([
  '5 years Python, SQL, Spark. Built data pipelines at scale. AWS certified.',
  'Junior developer, 1 year JavaScript experience. No data engineering.',
  '10 years data engineering. Expert in BigQuery, Dataflow, Airflow. Led team of 8.',
  '3 years analytics, some Python. Interested in transitioning to engineering.'
]) AS resume
ORDER BY qualification_score DESC
"""
client.query(query).to_dataframe()
```

### 3. Combining with AI.IF for filter + rank

Filter first, then rank — minimizing Gemini calls.

```python
query = """
WITH scored_reviews AS (
  SELECT
    review,
    AI.SCORE(CONCAT('Rate the urgency of this customer issue on a scale of 1 to 5: ', review)) AS urgency
  FROM UNNEST([
    'My order arrived damaged and I need a replacement ASAP.',
    'Just wondering about your return policy.',
    'Your product caused a safety hazard in my home!',
    'The color is slightly different from the photo.',
    'I was charged twice and need an immediate refund!'
  ]) AS review
)
SELECT review, urgency
FROM scored_reviews
WHERE urgency >= 3
ORDER BY urgency DESC
"""
client.query(query).to_dataframe()
```

### 4. Specifying an endpoint

Override the auto-selected model with a specific Gemini endpoint.

```python
query = """
SELECT
  text,
  AI.SCORE(
    CONCAT('Rate the reading difficulty of this text on a scale of 1 to 10, where 1 is elementary and 10 is PhD level: ', text),
    endpoint => 'gemini-2.5-flash'
  ) AS reading_level
FROM UNNEST([
  'The cat sat on the mat.',
  'Quantum entanglement demonstrates non-local correlations between particles.',
  'Machine learning models can improve over time with more training data.'
]) AS text
"""
client.query(query).to_dataframe()
```

### 5. Error ratio control

By default, `AI.SCORE` returns NULL for rows where the model call fails and continues the query. Set `max_error_ratio` (0.0–1.0) to fail the entire query when the error rate exceeds your threshold — useful for data pipelines where silent NULLs would corrupt downstream rankings.

```python
query = """
SELECT
  response,
  AI.SCORE(
    CONCAT('Rate the helpfulness of this customer support response on a scale of 1 to 5: ', response),
    max_error_ratio => 0.0
  ) AS helpfulness
FROM UNNEST([
  'I have escalated your issue to a senior agent who will call you within the hour.',
  'Please check the FAQ.',
  'I have processed your refund. You should see the credit within 3-5 business days.'
]) AS response
ORDER BY helpfulness DESC
"""
client.query(query).to_dataframe()
```

---
## Examples — Multimodal with ObjectRef

`AI.SCORE` can score documents, images, and video stored in Cloud Storage. Create an **object table** pointing to your files, then use the tuple syntax to pass both scoring criteria and document content:

```sql
AI.SCORE(('scoring criteria text', OBJ.GET_ACCESS_URL(ref, 'r')))
```

The object table provides a `ref` column that `OBJ.GET_ACCESS_URL` converts to a signed reference. See the `RESOURCES.md#objectref-and-objectrefruntime-schema-reference` (ObjectRef reference) for details.

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
_prefix = 'bq_ai_functions/ai_score'

_data = Path('../../data/documents')
if not _data.exists():
    _data = Path('data/documents')

blob = _bucket.blob(f'{_prefix}/invoice_001.pdf')
if not blob.exists():
    blob.upload_from_filename(str(_data / 'invoices' / 'invoice_001.pdf'))
    print(f'Uploaded invoice_001.pdf → gs://{BUCKET}/{_prefix}/invoice_001.pdf')
else:
    print(f'Already exists: gs://{BUCKET}/{_prefix}/invoice_001.pdf')

# Create object table pointing to the uploaded files
client.query(f"""
CREATE OR REPLACE EXTERNAL TABLE `{PROJECT_ID}.{DATASET_ID}.ai_score_docs`
WITH CONNECTION `{PROJECT_ID}.{LOCATION}.{CONNECTION_ID}`
OPTIONS (
  object_metadata = 'SIMPLE',
  uris = ['gs://{BUCKET}/{_prefix}/*.pdf']
)
""").result()
print('Object table ai_score_docs ready')
```

### 6. Score a document

Use the tuple syntax to pass both scoring criteria and a document reference from the object table.

```python
query = f"""
SELECT
  uri,
  AI.SCORE(
    ('Rate the professionalism and formality of this document on a scale of 0 to 1',
     OBJ.GET_ACCESS_URL(ref, 'r'))
  ) AS professionalism
FROM
  `{PROJECT_ID}.{DATASET_ID}.ai_score_docs`
"""
client.query(query).to_dataframe()
```

---
## Examples — `%%bigquery` Magics

The same examples using IPython magic commands. Magics let you write SQL directly in notebook cells without Python string wrapping.

Key patterns:
- `%%bigquery` — run SQL, display results inline
- `%%bigquery df` — run SQL, capture results into a pandas DataFrame

```sql
%%bigquery --project {PROJECT_ID}

SELECT
  review,
  AI.SCORE(CONCAT('Rate positivity on a scale of 1 to 10: ', review)) AS score
FROM UNNEST([
  'Amazing!', 'Terrible.', 'Pretty good.', 'Awful experience.'
]) AS review
ORDER BY score DESC
```

---
## Examples — BigFrames

BigFrames wraps `AI.SCORE` via `bbq.ai.score()`. It returns a Series of FLOAT64 directly.

**Key patterns:**
- Returns FLOAT64 directly — use for ranking and filtering
- Tuple prompt pattern: `bbq.ai.score(("Rate: ", df["col"], " on scale 1-10"))`
- No endpoint parameter — BigQuery auto-selects the model

```python
import bigframes.pandas as bpd
import bigframes.bigquery as bbq

bpd.close_session()  # Reset session to apply connection settings
bpd.options.bigquery.project = PROJECT_ID
bpd.options.bigquery.location = LOCATION
bpd.options.bigquery.bq_connection = f'{PROJECT_ID}.{LOCATION}.{CONNECTION_ID}'
```

### Scoring and ranking

```python
df = bpd.DataFrame({'review': [
    'Amazing product!', 'Terrible quality.', 'Pretty good.', 'Best purchase ever!'
]})

df['score'] = bbq.ai.score(('Rate the positivity of this review on a scale of 1 to 10: ', df['review']))
df.sort_values('score', ascending=False).to_pandas()
```
