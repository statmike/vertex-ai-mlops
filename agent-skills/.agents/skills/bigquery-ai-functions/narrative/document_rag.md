> **⚠️ NOT CURRENTLY WORKING:** This workflow's first step uses `AI.PARSE_DOCUMENT` (preview), which has been temporarily taken offline for revision (as of 2026-06-01). See the [BigQuery release notes](https://cloud.google.com/bigquery/docs/release-notes) for status. The entire workflow is blocked until the function is re-enabled — see the `functions/ai_parse_document` (`AI.PARSE_DOCUMENT` notebook) for details.

# Document RAG — BigQuery AI Functions

A complete document-based Retrieval-Augmented Generation (RAG) pipeline built entirely in BigQuery SQL:

1. **Parse** real documents with `AI.PARSE_DOCUMENT`
2. **Embed** document chunks with `AI.EMBED`
3. **Search** for relevant chunks with `VECTOR_SEARCH`
4. **Answer** questions with `AI.GENERATE`, grounded in document content

**What this demonstrates:**
- Building a document RAG pipeline entirely in BigQuery SQL — no external tools
- Parsing real PDFs into searchable chunks with `AI.PARSE_DOCUMENT`
- Asymmetric embedding pattern (RETRIEVAL_DOCUMENT / RETRIEVAL_QUERY)
- Composing parsed document chunks into grounded prompts
- Using ObjectRef (`OBJ.MAKE_REF`) as an alternative to object tables for document parsing
- Comparing RAG answers with and without retrieved context

**Functions used:** `functions/ai_parse_document` (`AI.PARSE_DOCUMENT`) | `functions/ai_embed` (`AI.EMBED`) | `functions/vector_search` (`VECTOR_SEARCH`) | `functions/ai_generate` (`AI.GENERATE`)

**Prerequisites:** `setup` (Setup guide) | `RESOURCES.md` (Function reference)

---
## Setup

Set your project and location, authenticate, and create shared resources.

> This workflow requires: (1) a **Cloud resource connection** with Document AI and Storage roles, (2) a **Document AI Layout Parser processor**, and (3) an **object table** pointing to documents in Cloud Storage. See the `setup` (Setup Reference) for details.

```python
PROJECT_ID = 'statmike-mlops-349915'  # <-- Replace with your project ID
LOCATION = 'US'  # BigQuery dataset location
DATASET_ID = 'bq_ai_functions'  # Shared dataset across all notebooks
CONNECTION_ID = 'bq_ai_functions'  # Shared connection
BUCKET = PROJECT_ID  # GCS bucket for document storage
```

### Environment

> **Already set up the project environment?** Skip to [Step 1](#step-1--parse-documents-with-aiparse_document).  
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
for role in ['roles/aiplatform.user', 'roles/storage.objectViewer', 'roles/documentai.apiUser']:
    _sp.run(['gcloud', 'projects', 'add-iam-policy-binding', PROJECT_ID,
             f'--member=serviceAccount:{sa}', f'--role={role}', '--quiet'],
            capture_output=True, text=True)
print(f'Connection {CONNECTION_ID} ready (SA: {sa})')
```

```python
from google.cloud import documentai_v1 as documentai

docai_client = documentai.DocumentProcessorServiceClient()
parent = docai_client.common_location_path(PROJECT_ID, 'us')

# Check for existing layout parser processor (idempotent)
PROCESSOR_DISPLAY_NAME = 'bq_ai_functions_layout_parser'
processor = None
for p in docai_client.list_processors(parent=parent):
    if p.display_name == PROCESSOR_DISPLAY_NAME:
        processor = p
        break

if processor is None:
    processor = docai_client.create_processor(
        parent=parent,
        processor=documentai.Processor(
            display_name=PROCESSOR_DISPLAY_NAME,
            type_='LAYOUT_PARSER_PROCESSOR',
        ),
    )

PROCESSOR_ID = processor.name
print(f'Layout Parser processor ready: {PROCESSOR_ID}')
```

### Upload documents and create object table

Upload 20 sample invoices to Cloud Storage and create an object table to reference them from BigQuery.

```python
from google.cloud import storage
from pathlib import Path
from tqdm import tqdm

gcs = storage.Client(project=PROJECT_ID)
bucket = gcs.bucket(BUCKET)
prefix = 'bq_ai_functions/document_rag'

data_dir = Path('../../data/documents/invoices')
if not data_dir.exists():
    data_dir = Path('data/documents/invoices')

files = sorted(data_dir.glob('*.pdf'))[:20]
uploaded, skipped = 0, 0
for f in tqdm(files, desc='Uploading'):
    blob = bucket.blob(f'{prefix}/{f.name}')
    if blob.exists():
        skipped += 1
    else:
        blob.upload_from_filename(str(f))
        uploaded += 1
print(f'Uploaded {uploaded} documents, skipped {skipped} (already exist)')
print(f'Location: gs://{BUCKET}/{prefix}/')
```

```python
client.query(f"""
CREATE OR REPLACE EXTERNAL TABLE `{PROJECT_ID}.{DATASET_ID}.workflow_docrag_objects`
WITH CONNECTION `{PROJECT_ID}.{LOCATION}.{CONNECTION_ID}`
OPTIONS (
  object_metadata = 'SIMPLE',
  uris = ['gs://{BUCKET}/{prefix}/*.pdf']
)
""").result()

df = client.query(f"""
  SELECT uri, content_type, size
  FROM `{PROJECT_ID}.{DATASET_ID}.workflow_docrag_objects`
  ORDER BY uri
""").to_dataframe()
print(f'Object table workflow_docrag_objects ready — {len(df)} documents')
df.head()
```

---
## Step 1 — Parse documents with AI.PARSE_DOCUMENT

`AI.PARSE_DOCUMENT` reads documents from the object table, runs them through the Document AI Layout Parser, and returns text chunks. Each document becomes one or more chunks with `chunk_id`, `start_page`, `end_page`, and `content`. We persist the results to avoid re-parsing on every query.

```python
query = f"""
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.workflow_docrag_chunks` AS
SELECT
  uri,
  chunk_id,
  start_page,
  end_page,
  content
FROM AI.PARSE_DOCUMENT(
  TABLE `{PROJECT_ID}.{DATASET_ID}.workflow_docrag_objects`,
  endpoint => '{PROCESSOR_ID}'
)
"""
client.query(query).result()

stats = client.query(f"""
  SELECT COUNT(*) AS total_chunks, COUNT(DISTINCT uri) AS documents
  FROM `{PROJECT_ID}.{DATASET_ID}.workflow_docrag_chunks`
""").to_dataframe()
print(f'Parsed {stats.iloc[0]["documents"]} documents into {stats.iloc[0]["total_chunks"]} chunks')
```

```python
client.query(f"""
  SELECT uri, chunk_id, start_page, end_page, LEFT(content, 200) AS content_preview
  FROM `{PROJECT_ID}.{DATASET_ID}.workflow_docrag_chunks`
  ORDER BY uri, chunk_id
  LIMIT 5
""").to_dataframe()
```

### Alternative: ObjectRef — skip the object table

`AI.PARSE_DOCUMENT` requires a `ref` column in its input. Object tables provide this automatically, but you can construct it inline using `OBJ.MAKE_REF` — no object table creation needed.

This approach uses `UNNEST` to create rows from GCS URIs, adds a `ref` column with `OBJ.MAKE_REF`, and passes the result directly to `AI.PARSE_DOCUMENT`. The output is identical to the object table approach above.

```python
# ObjectRef alternative — parse documents without an object table
# Build URIs from the uploaded files
uris = [f'gs://{BUCKET}/{prefix}/invoice_{i:03d}.pdf' for i in range(1, 21)]
uris_sql = ', '.join(f"'{u}'" for u in uris)

query = f"""
SELECT
  uri,
  chunk_id,
  LEFT(content, 200) AS content_preview
FROM AI.PARSE_DOCUMENT(
  (SELECT
    uri,
    OBJ.MAKE_REF(uri, '{PROJECT_ID}.{LOCATION}.{CONNECTION_ID}') AS ref
  FROM UNNEST([{uris_sql}]) AS uri),
  endpoint => '{PROCESSOR_ID}'
)
ORDER BY uri, chunk_id
LIMIT 5
"""
df = client.query(query).to_dataframe()
print(f'ObjectRef approach: parsed {df["uri"].nunique()} documents (showing first 5 chunks)')
df
```

---
## Step 2 — Embed chunks with AI.EMBED

Create embeddings for each document chunk using `text-embedding-005` with `RETRIEVAL_DOCUMENT` task type. This tells the embedding model that these are documents to be retrieved — queries will use the complementary `RETRIEVAL_QUERY` task type for asymmetric search.

```python
query = f"""
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.workflow_docrag_embedded` AS
SELECT
  uri, chunk_id, start_page, end_page, content,
  (AI.EMBED(
    content => content,
    endpoint => 'text-embedding-005',
    task_type => 'RETRIEVAL_DOCUMENT'
  )).result AS embedding
FROM `{PROJECT_ID}.{DATASET_ID}.workflow_docrag_chunks`
"""
client.query(query).result()

verify = client.query(f"""
  SELECT COUNT(*) AS chunks, ARRAY_LENGTH(embedding) AS dims
  FROM `{PROJECT_ID}.{DATASET_ID}.workflow_docrag_embedded`
  GROUP BY dims
""").to_dataframe()
print(f'All {verify.iloc[0]["chunks"]} chunks embedded ({verify.iloc[0]["dims"]} dimensions)')
```

---
## Step 3 — Retrieve and generate (RAG)

The core RAG pattern: embed the user question with `RETRIEVAL_QUERY`, find the most relevant document chunks with `VECTOR_SEARCH`, then pass them as context to `AI.GENERATE` to produce a grounded answer.

```python
user_question = 'What is the total amount due on the invoice from Nexus Innovations Group?'

query = f"""
WITH retrieved AS (
  SELECT
    base.uri,
    base.chunk_id,
    base.content,
    distance
  FROM VECTOR_SEARCH(
    TABLE `{PROJECT_ID}.{DATASET_ID}.workflow_docrag_embedded`,
    'embedding',
    query_value => (AI.EMBED(
      content => '{user_question}',
      endpoint => 'text-embedding-005',
      task_type => 'RETRIEVAL_QUERY'
    )).result,
    top_k => 3,
    distance_type => 'COSINE'
  )
),
context AS (
  SELECT STRING_AGG(
    CONCAT('--- Document: ', uri, ' (chunk ', CAST(chunk_id AS STRING), ') --- ', content),
    ' ||| '
  ) AS docs
  FROM retrieved
)
SELECT (AI.GENERATE(
  CONCAT(
    'You are a document analyst. Answer the user question based ONLY on the provided document excerpts. ',
    'Include specific details (amounts, dates, reference numbers) from the documents. ',
    'If the documents do not contain enough information, say so. ',
    'Document excerpts: ', c.docs,
    ' --- User question: {user_question}'
  )
)).result AS answer
FROM context c
"""
df = client.query(query).to_dataframe()
print(f'Question: {user_question}\n')
print(df.iloc[0]['answer'])
```

### View the retrieved chunks

See which document chunks were retrieved and used as context for the answer. Lower distance = higher relevance.

```python
query = f"""
SELECT
  base.uri,
  base.chunk_id,
  LEFT(base.content, 200) AS content_preview,
  distance
FROM VECTOR_SEARCH(
  TABLE `{PROJECT_ID}.{DATASET_ID}.workflow_docrag_embedded`,
  'embedding',
  query_value => (AI.EMBED(
    content => '{user_question}',
    endpoint => 'text-embedding-005',
    task_type => 'RETRIEVAL_QUERY'
  )).result,
  top_k => 3,
  distance_type => 'COSINE'
)
"""
client.query(query).to_dataframe()
```

### Batch RAG: answer multiple questions

Process multiple questions through the document RAG pipeline at once. Each question retrieves its own relevant chunks and gets a tailored answer.

```python
query = f"""
WITH questions AS (
  SELECT question
  FROM UNNEST([
    'Which vendor has the highest total invoice amount?',
    'What are the payment terms on invoice INV-2024-0013?',
    'List all invoices due in November 2023.'
  ]) AS question
),
retrieved AS (
  SELECT
    query.question AS user_question,
    base.uri,
    base.content,
    distance
  FROM VECTOR_SEARCH(
    TABLE `{PROJECT_ID}.{DATASET_ID}.workflow_docrag_embedded`,
    'embedding',
    (SELECT question,
       (AI.EMBED(content => question, endpoint => 'text-embedding-005',
                 task_type => 'RETRIEVAL_QUERY')).result AS embedding
     FROM questions),
    top_k => 3,
    distance_type => 'COSINE'
  )
),
context_per_question AS (
  SELECT
    user_question,
    STRING_AGG(
      CONCAT('--- ', uri, ' --- ', content),
      ' ||| '
    ) AS context
  FROM retrieved
  GROUP BY user_question
)
SELECT
  user_question,
  (AI.GENERATE(
    CONCAT(
      'Answer this question concisely based on the document excerpts below. ',
      'Include specific amounts, dates, and reference numbers. ',
      'Documents: ', context,
      ' --- Question: ', user_question
    )
  )).result AS answer
FROM context_per_question
"""
df = client.query(query).to_dataframe()
for _, row in df.iterrows():
    print(f'Q: {row["user_question"]}')
    print(f'A: {row["answer"]}\n')
```

---
## Step 4 — RAG vs direct generation

Compare the same question answered with and without retrieved document context. Without RAG, the model can only guess or hallucinate invoice details. With RAG, it grounds its answer in actual document content.

```python
comparison_question = 'What is the total amount due on the invoice from Nexus Innovations Group?'

query = f"""
WITH no_rag AS (
  SELECT (AI.GENERATE(
    CONCAT(
      'Answer this question. If you do not have the information, say so. ',
      'Question: {comparison_question}'
    )
  )).result AS answer
),
rag_context AS (
  SELECT STRING_AGG(
    CONCAT('--- ', base.uri, ' --- ', base.content),
    ' ||| '
  ) AS docs
  FROM VECTOR_SEARCH(
    TABLE `{PROJECT_ID}.{DATASET_ID}.workflow_docrag_embedded`,
    'embedding',
    query_value => (AI.EMBED(
      content => '{comparison_question}',
      endpoint => 'text-embedding-005',
      task_type => 'RETRIEVAL_QUERY'
    )).result,
    top_k => 3,
    distance_type => 'COSINE'
  )
),
with_rag AS (
  SELECT (AI.GENERATE(
    CONCAT(
      'Answer this question based ONLY on the provided documents. ',
      'Include specific amounts and reference numbers. ',
      'Documents: ', docs,
      ' --- Question: {comparison_question}'
    )
  )).result AS answer
  FROM rag_context
)
SELECT
  'Without RAG' AS method, answer FROM no_rag
UNION ALL
SELECT
  'With RAG' AS method, answer FROM with_rag
"""
df = client.query(query).to_dataframe()
for _, row in df.iterrows():
    print(f'=== {row["method"]} ===')
    print(f'{row["answer"]}\n')
```

The **Without RAG** answer is either a refusal ("I don't have that information") or a hallucinated amount. The **With RAG** answer references actual invoice data — amounts, dates, and reference numbers from the retrieved document chunks. This is the core value of RAG: grounding generation in retrieved evidence.
