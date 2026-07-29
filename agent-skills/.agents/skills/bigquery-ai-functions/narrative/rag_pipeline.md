# RAG Pipeline — BigQuery AI Functions

A complete Retrieval-Augmented Generation (RAG) pipeline built entirely in BigQuery SQL:

1. **Generate** a knowledge base with `AI.GENERATE_TABLE`
2. **Embed** documents with `AI.EMBED`
3. **Search** for relevant context with `VECTOR_SEARCH`
4. **Answer** questions with `AI.GENERATE`, grounded in retrieved documents

**What this demonstrates:**
- Building a full RAG system without leaving BigQuery
- Asymmetric embedding pattern (RETRIEVAL_DOCUMENT / RETRIEVAL_QUERY)
- Composing search results into grounded prompts
- Comparing RAG answers with and without retrieved context

**Functions used:** `functions/ai_generate_table` (`AI.GENERATE_TABLE`) | `functions/ai_embed` (`AI.EMBED`) | `functions/vector_search` (`VECTOR_SEARCH`) | `functions/ai_generate` (`AI.GENERATE`)

**Prerequisites:** `setup` (Setup guide) | `RESOURCES.md` (Function reference)

---
## Setup

Set your project and location, authenticate, and create shared resources.

> This workflow requires a connection and a remote model for `AI.GENERATE_TABLE`. See the `setup` (Setup Reference) for details.

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
  OPTIONS (endpoint = 'gemini-2.5-flash')
''').result()
print('Model gemini_flash ready')
```

---
## Step 1 — Generate a knowledge base with AI.GENERATE_TABLE

Use `AI.GENERATE_TABLE` to create a realistic FAQ knowledge base for a fictional cloud platform. Each input row generates one FAQ entry with a question, answer, and category.

```python
output_schema = """question STRING OPTIONS(description = "The FAQ question"),
       answer STRING OPTIONS(description = "Detailed answer with technical specifics"),
       category STRING OPTIONS(description = "Category: Compute, Networking, Security, Database, DevOps, or Monitoring")"""

query = f'''
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.workflow_rag_knowledge` AS
SELECT question, answer, category
FROM AI.GENERATE_TABLE(
  MODEL `{PROJECT_ID}.{DATASET_ID}.gemini_flash`,
  (SELECT CONCAT(
     'Write a detailed FAQ entry about "', topic, '" for a cloud computing platform. ',
     'The answer should be 2-3 sentences with specific technical details.'
   ) AS prompt
   FROM UNNEST([
     'how to create a virtual machine',
     'setting up a load balancer',
     'configuring a firewall',
     'creating a database backup',
     'monitoring application performance',
     'setting up auto-scaling',
     'managing API keys',
     'configuring DNS records',
     'setting up CI/CD pipelines',
     'managing user permissions',
     'encrypting data at rest',
     'setting up logging and alerts'
   ]) AS topic),
  STRUCT(
    """{output_schema}""" AS output_schema
  )
)
'''
client.query(query).result()

kb = client.query(
    f'SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.workflow_rag_knowledge`'
).to_dataframe()
print(f'{len(kb)} FAQ entries generated')
kb[['category', 'question']]
```

---
## Step 2 — Embed the knowledge base with AI.EMBED

Create embeddings for each FAQ answer using `RETRIEVAL_DOCUMENT` task type. We embed the concatenation of question + answer for richer context.

```python
query = f'''
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.workflow_rag_embedded` AS
SELECT
  question, answer, category,
  (AI.EMBED(
    content => CONCAT(question, ' ', answer),
    endpoint => 'text-embedding-005',
    task_type => 'RETRIEVAL_DOCUMENT'
  )).result AS embedding
FROM `{PROJECT_ID}.{DATASET_ID}.workflow_rag_knowledge`
'''
client.query(query).result()

verify = client.query(f'''
  SELECT category, question, ARRAY_LENGTH(embedding) AS dims
  FROM `{PROJECT_ID}.{DATASET_ID}.workflow_rag_embedded`
''').to_dataframe()
print(f'All {len(verify)} entries embedded ({verify.iloc[0]["dims"]} dimensions)')
```

---
## Step 3 — Retrieve and generate (RAG)

The core RAG pattern: for each user question, retrieve the most relevant FAQ entries with `VECTOR_SEARCH`, then pass them as context to `AI.GENERATE` to produce a grounded answer.

```python
user_question = 'How do I protect my application from unauthorized access?'

query = f'''
WITH retrieved AS (
  SELECT
    base.question AS faq_question,
    base.answer AS faq_answer,
    base.category,
    distance
  FROM VECTOR_SEARCH(
    TABLE `{PROJECT_ID}.{DATASET_ID}.workflow_rag_embedded`,
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
    CONCAT('Q: ', faq_question, ' | A: ', faq_answer),
    ' ||| '
  ) AS docs
  FROM retrieved
)
SELECT (AI.GENERATE(
  CONCAT(
    'You are a cloud platform support assistant. Answer the user question based ONLY on the provided context. ',
    'If the context does not contain enough information, say so. ',
    'Context: ', c.docs,
    ' --- User question: {user_question}'
  )
)).result AS answer
FROM context c
'''
df = client.query(query).to_dataframe()
print(f'Question: {user_question}\n')
print(df.iloc[0]['answer'])
```

### View the retrieved context

See which FAQ entries were retrieved and used as context for the answer.

```python
query = f'''
SELECT
  base.category,
  base.question,
  base.answer,
  distance
FROM VECTOR_SEARCH(
  TABLE `{PROJECT_ID}.{DATASET_ID}.workflow_rag_embedded`,
  'embedding',
  query_value => (AI.EMBED(
    content => '{user_question}',
    endpoint => 'text-embedding-005',
    task_type => 'RETRIEVAL_QUERY'
  )).result,
  top_k => 3,
  distance_type => 'COSINE'
)
'''
client.query(query).to_dataframe()
```

---
## Step 4 — Batch RAG: answer multiple questions

Process multiple user questions through the RAG pipeline at once. Each question retrieves its own context and gets a tailored answer.

```python
query = f'''
WITH questions AS (
  SELECT question
  FROM UNNEST([
    'How do I make my app handle more traffic automatically?',
    'What is the best way to back up my database?',
    'How do I set up monitoring for my services?'
  ]) AS question
),
retrieved AS (
  SELECT
    query.question AS user_question,
    base.question AS faq_question,
    base.answer AS faq_answer,
    distance
  FROM VECTOR_SEARCH(
    TABLE `{PROJECT_ID}.{DATASET_ID}.workflow_rag_embedded`,
    'embedding',
    (SELECT question,
       (AI.EMBED(content => question, endpoint => 'text-embedding-005',
                 task_type => 'RETRIEVAL_QUERY')).result AS embedding
     FROM questions),
    top_k => 2,
    distance_type => 'COSINE'
  )
),
context_per_question AS (
  SELECT
    user_question,
    STRING_AGG(
      CONCAT('Q: ', faq_question, ' | A: ', faq_answer),
      ' ||| '
    ) AS context
  FROM retrieved
  GROUP BY user_question
)
SELECT
  user_question,
  (AI.GENERATE(
    CONCAT(
      'Answer this question concisely based on the context below. ',
      'Context: ', context,
      ' --- Question: ', user_question
    )
  )).result AS answer
FROM context_per_question
'''
df = client.query(query).to_dataframe()
for _, row in df.iterrows():
    print(f'Q: {row["user_question"]}')
    print(f'A: {row["answer"]}\n')
```
