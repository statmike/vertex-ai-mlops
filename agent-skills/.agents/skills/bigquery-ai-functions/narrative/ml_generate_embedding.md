# ML.GENERATE_EMBEDDING — BigQuery AI Functions

`ML.GENERATE_EMBEDDING` is the legacy predecessor to `AI.GENERATE_EMBEDDING`. Same capabilities but with `ml_generate_embedding_` prefixed column names. **Google recommends using `AI.GENERATE_EMBEDDING` for new queries.**

**When to use it:**
- You have existing code that uses ML.GENERATE_EMBEDDING and need to maintain it
- You need the `flatten_json_output` parameter

**Alternatives:**
- `functions/ai_generate_embedding` (`AI.GENERATE_EMBEDDING`) — Recommended replacement — same capabilities, cleaner column names
- `functions/ai_embed` (`AI.EMBED`) — Scalar function, no model required

**Multimodal:** Supports image and video input via `RESOURCES.md#objectref-and-objectrefruntime-schema-reference` (ObjectRef). Pass ObjectRef or ObjectRefRuntime values in the `content` column to create multimodal embeddings.

**References:** `RESOURCES.md` (Full syntax reference) | [Official documentation](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-generate-embedding) | `setup` (Setup guide)

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
# Create remote embedding model (idempotent)
client.query(f'''
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.embedding_text`
  REMOTE WITH CONNECTION `{PROJECT_ID}.{LOCATION}.{CONNECTION_ID}`
  OPTIONS (endpoint = \'text-embedding-005\')
''').result()
print('Model embedding_text ready')
```

---
## Examples — SQL

Progressive examples from simplest to most advanced. Each cell adds one new concept.

### 1. Basic text embedding

Column names are prefixed with `ml_generate_embedding_`. The `flatten_json_output` defaults to TRUE.

```python
query = f'''
SELECT content,
  ARRAY_LENGTH(ml_generate_embedding_result) AS dims,
  ml_generate_embedding_statistics
FROM ML.GENERATE_EMBEDDING(
  MODEL `{PROJECT_ID}.{DATASET_ID}.embedding_text`,
  (SELECT text AS content
   FROM UNNEST(['BigQuery is a data warehouse.', 'Cloud computing scales.']) AS text)
)
'''
client.query(query).to_dataframe()
```

### 2. Column name comparison with AI.GENERATE_EMBEDDING

```python
# ML.GENERATE_EMBEDDING columns
query_ml = f'''
SELECT *
FROM ML.GENERATE_EMBEDDING(
  MODEL `{PROJECT_ID}.{DATASET_ID}.embedding_text`,
  (SELECT 'test' AS content)
)
'''
df_ml = client.query(query_ml).to_dataframe()
print('ML.GENERATE_EMBEDDING columns:', list(df_ml.columns))

# AI.GENERATE_EMBEDDING columns
query_ai = f'''
SELECT *
FROM AI.GENERATE_EMBEDDING(
  MODEL `{PROJECT_ID}.{DATASET_ID}.embedding_text`,
  (SELECT 'test' AS content)
)
'''
df_ai = client.query(query_ai).to_dataframe()
print('AI.GENERATE_EMBEDDING columns:', list(df_ai.columns))
```

### 3. Using task_type for retrieval

`task_type` tells the embedding model the intended use of the text, which changes how the embedding is generated. This is a critical configuration choice.

**Asymmetric task types** — documents and queries use *different* task types. Use this pattern for retrieval, where what you index differs in intent from what you search with:

| Use Case | Document Task Type | Query Task Type |
|----------|-------------------|-----------------|
| Search | `RETRIEVAL_DOCUMENT` | `RETRIEVAL_QUERY` |
| Question Answering | `RETRIEVAL_DOCUMENT` | `QUESTION_ANSWERING` |
| Fact Checking | `RETRIEVAL_DOCUMENT` | `FACT_VERIFICATION` |
| Code Retrieval | `RETRIEVAL_DOCUMENT` | `CODE_RETRIEVAL_QUERY` |

**Symmetric task types** — both sides use the *same* task type:
- `SEMANTIC_SIMILARITY` — comparing how similar two texts are
- `CLASSIFICATION` — grouping texts by category
- `CLUSTERING` — organizing texts into clusters

> **Key point:** If your use case doesn't align with a specific task type, use `RETRIEVAL_DOCUMENT` when indexing and `RETRIEVAL_QUERY` when searching.

```python
query = f'''
SELECT content,
  ARRAY_LENGTH(ml_generate_embedding_result) AS dims
FROM ML.GENERATE_EMBEDDING(
  MODEL `{PROJECT_ID}.{DATASET_ID}.embedding_text`,
  (SELECT text AS content
   FROM UNNEST(['BigQuery', 'Cloud Functions', 'Cloud Storage']) AS text),
  STRUCT('RETRIEVAL_DOCUMENT' AS task_type)
)
'''
client.query(query).to_dataframe()
```

### Multimodal embeddings

For multimodal embedding examples (images, video), see the `functions/ai_generate_embedding` (`AI.GENERATE_EMBEDDING`) notebook, which demonstrates the same functionality with cleaner column names.

---
## Examples — `%%bigquery` Magics

The same examples using IPython magic commands. Magics let you write SQL directly in notebook cells without Python string wrapping.

Key patterns:
- `%%bigquery` — run SQL, display results inline
- `%%bigquery df` — run SQL, capture results into a pandas DataFrame

### ML.GENERATE_EMBEDDING with `%%bigquery`

```sql
%%bigquery --project {PROJECT_ID}

SELECT content, ARRAY_LENGTH(ml_generate_embedding_result) AS dims
FROM ML.GENERATE_EMBEDDING(
  MODEL `statmike-mlops-349915.bq_ai_functions.embedding_text`,
  (SELECT text AS content FROM UNNEST(['Machine learning', 'Deep learning']) AS text)
)
```

---
## Examples — BigFrames

BigFrames has no direct `ML.GENERATE_EMBEDDING` wrapper. It routes through `AI.GENERATE_EMBEDDING` instead.
Use `bbq.ai.generate_embedding()` or the `TextEmbeddingGenerator` class.

```python
import bigframes.pandas as bpd
import bigframes.bigquery as bbq

bpd.options.bigquery.project = PROJECT_ID
bpd.options.bigquery.location = LOCATION
```

### Using bbq.ai.generate_embedding (wraps AI.GENERATE_EMBEDDING)

```python
df = bpd.DataFrame({'content': ['BigQuery', 'Cloud Storage', 'Cloud Functions']})

model_name = f'{PROJECT_ID}.{DATASET_ID}.embedding_text'
result = bbq.ai.generate_embedding(model_name, df)
result[['content']].to_pandas()
```
