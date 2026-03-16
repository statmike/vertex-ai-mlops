![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2Fdata%2Bai%2Fbq-ai-functions%2Fsetup&file=README.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/data%2Bai/bq-ai-functions/setup/README.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-ai-functions/setup/README.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-ai-functions/setup/README.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-ai-functions/setup/README.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-ai-functions/setup/README.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Connect With Author On: </b> 
    <a href="https://www.linkedin.com/in/statmike"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a>
    <a href="https://www.github.com/statmike"><img src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub Logo" width="20px"></a> 
    <a href="https://www.youtube.com/@statmike-channel"><img src="https://upload.wikimedia.org/wikipedia/commons/f/fd/YouTube_full-color_icon_%282024%29.svg" alt="YouTube Logo" width="20px"></a>
    <a href="https://bsky.app/profile/statmike.bsky.social"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://x.com/statmike"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a>
  </td>
</tr>
</table><br/><br/>

---
# Setup Reference

This page explains the infrastructure needed for BigQuery AI functions: the Python environment for running notebooks, plus BigQuery concepts like connections, remote models, endpoints, quotas, and permissions.

Individual function notebooks include inline setup cells — this page provides the deeper "why" behind each concept.

---

## Table of Contents

- [Python Environment](#python-environment)
- [Which Functions Need What](#which-functions-need-what)
- [Connections](#connections)
- [Remote Models (CREATE MODEL)](#remote-models-create-model)
- [Endpoints](#endpoints)
- [Quotas and Provisioned Throughput](#quotas-and-provisioned-throughput)
- [Permissions (IAM)](#permissions-iam)
- [Object Tables](#object-tables)
- [Document AI Processors](#document-ai-processors)
- [Autonomous Embedding Generation](#autonomous-embedding-generation)

---

## Python Environment

Each notebook installs its own dependencies inline, so you can run any notebook standalone in Colab, Colab Enterprise, or Vertex AI Workbench with no prior setup.

If you're working locally (VSCode, JupyterLab) or want a pre-configured environment, use `uv` to set up once:

### Local setup with `uv`

```bash
# From the project root (bq-ai-functions/)
uv sync --group dev
```

This creates a `.venv` with all packages needed across every notebook. To use it as a Jupyter kernel:

```bash
uv run python -m ipykernel install --user --name bq-ai-functions --display-name "BQ AI Functions"
```

Then select the **BQ AI Functions** kernel in your notebook editor.

### How notebooks handle dependencies

Every notebook includes an install cell near the top:

```python
import subprocess, sys, shutil

def install(*packages):
    """Install packages using uv (fast) with pip fallback."""
    uv = shutil.which('uv')
    if uv:
        subprocess.check_call([uv, 'pip', 'install', '-q', '--python', sys.executable, *packages])
    else:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-q', '--upgrade', *packages])

install('google-cloud-bigquery', 'bigframes', 'pydantic', 'db-dtypes')
```

- Uses `uv` when available (faster installs), falls back to `pip`
- Targets `sys.executable` so packages go into the active kernel's environment
- If you set up the local environment above, this cell is a fast no-op

### Packages used across notebooks

| Package | What it's for |
|---------|---------------|
| `google-cloud-bigquery` | BigQuery Python client — run queries, manage datasets |
| `db-dtypes` | BigQuery-specific pandas dtypes (DATE, GEOGRAPHY, etc.) |
| `bigquery-magics` | `%%bigquery` cell magic for running SQL directly in notebook cells |
| `tqdm` | Progress bars for long-running BigQuery queries |
| `bigframes` | BigFrames — pandas-like API backed by BigQuery |
| `pydantic` | Schema helpers — define `output_schema` as Python classes |
| `matplotlib` | Visualization for forecasting notebooks |
| `google-cloud-storage` | Cloud Storage client — upload documents for object tables |
| `google-cloud-documentai` | Document AI client — create and manage processors |

---

## Which Functions Need What

Not all AI functions require the same setup. Here's a quick reference:

| Function | Connection | Remote Model | Endpoint | Notes |
|----------|:----------:|:------------:|:--------:|-------|
| `AI.GENERATE` | Optional | No | Optional (default: gemini-2.5-flash) | Uses end-user credentials by default |
| `AI.GENERATE_BOOL` | Optional | No | Optional (default: gemini-2.5-flash) | |
| `AI.GENERATE_DOUBLE` | Optional | No | Optional (default: gemini-2.5-flash) | |
| `AI.GENERATE_INT` | Optional | No | Optional (default: gemini-2.5-flash) | |
| `AI.IF` | Optional | No | Optional (auto-selected) | |
| `AI.SCORE` | Optional | No | Optional (auto-selected) | |
| `AI.CLASSIFY` | Optional | No | Optional (auto-selected) | |
| `AI.EMBED` | Text: Optional, Multimodal: Required | No | Required | Must include model version |
| `AI.SIMILARITY` | Text: Optional, Multimodal: Required | No | Required | |
| `AI.FORECAST` | No | No | No | Uses built-in TimesFM |
| `AI.DETECT_ANOMALIES` | No | No | No | Uses built-in TimesFM |
| `AI.EVALUATE` | No | No | No | Uses built-in TimesFM |
| `AI.GENERATE_TEXT` | Yes (via model) | **Yes** | Set at CREATE MODEL | Gemini, Claude, Llama, Mistral, Open |
| `AI.GENERATE_TABLE` | Yes (via model) | **Yes** | Set at CREATE MODEL | Gemini only |
| `AI.GENERATE_EMBEDDING` | Yes (via model) | **Yes** | Set at CREATE MODEL | |
| `ML.GENERATE_TEXT` | Yes (via model) | **Yes** | Set at CREATE MODEL | Legacy — use AI.GENERATE_TEXT |
| `ML.GENERATE_EMBEDDING` | Yes (via model) | **Yes** | Set at CREATE MODEL | Legacy — use AI.GENERATE_EMBEDDING |
| `VECTOR_SEARCH` | No | No | No | Operates on pre-computed embeddings |
| `AI.SEARCH` | Configured on table | No | Configured on table | Requires autonomous embedding generation |
| `ML.PROCESS_DOCUMENT` | Yes (via model + object table) | **Yes** | N/A | Also needs object table + Document AI processor |

**Summary:** The newer `AI.*` scalar functions (AI.GENERATE, AI.IF, AI.SCORE, AI.CLASSIFY, AI.EMBED, AI.SIMILARITY) and the forecasting functions (AI.FORECAST, AI.DETECT_ANOMALIES, AI.EVALUATE) require minimal or no setup. The table-valued generation and embedding functions (AI.GENERATE_TEXT, AI.GENERATE_TABLE, AI.GENERATE_EMBEDDING) require creating a connection and a remote model first. `ML.PROCESS_DOCUMENT` additionally requires an object table pointing to documents in Cloud Storage and a Document AI processor.

---

## Connections

### What is a connection?

A [BigQuery connection](https://cloud.google.com/bigquery/docs/create-cloud-resource-connection) is a resource that lets BigQuery access external services like Vertex AI. When you create a connection, BigQuery provisions a service account that acts on your behalf.

### When do you need one?

- **Required** for functions that use a remote model (AI.GENERATE_TEXT, AI.GENERATE_TABLE, AI.GENERATE_EMBEDDING, ML.PROCESS_DOCUMENT, ML.* functions) — the connection is specified in the `CREATE MODEL` statement.
- **Required** for object tables used with ML.PROCESS_DOCUMENT — the connection is specified in the `CREATE EXTERNAL TABLE` statement.
- **Required** for multimodal operations with AI.EMBED and AI.SIMILARITY (image/video content).
- **Optional** for scalar AI functions (AI.GENERATE, AI.IF, etc.) — if not specified, end-user credentials are used. Use a connection when:
  - The query job may run longer than 48 hours
  - You want to use a service account instead of user credentials
  - You need consistent permissions across users

### How to create one

```sql
-- Create a Cloud Resource connection
CREATE CONNECTION `PROJECT_ID.LOCATION.CONNECTION_NAME`
  OPTIONS (type = 'CLOUD_RESOURCE');
```

Or with the `bq` CLI:
```bash
bq mk --connection \
  --location=LOCATION \
  --connection_type=CLOUD_RESOURCE \
  PROJECT_ID.LOCATION.CONNECTION_NAME
```

After creating the connection, you need to:

1. **Find the service account** — look up the connection details to get the auto-generated service account email:
   ```bash
   bq show --connection PROJECT_ID.LOCATION.CONNECTION_NAME
   ```

2. **Grant the Vertex AI User role** to the service account:
   ```bash
   gcloud projects add-iam-policy-binding PROJECT_ID \
     --member="serviceAccount:SERVICE_ACCOUNT_EMAIL" \
     --role="roles/aiplatform.user"
   ```

### Connection format in SQL

Connections are referenced as `PROJECT_ID.LOCATION.CONNECTION_NAME`:

```sql
-- In CREATE MODEL
CREATE MODEL `project.dataset.my_model`
  REMOTE WITH CONNECTION `project.us.my_connection`
  OPTIONS (endpoint = 'gemini-2.5-flash');

-- In scalar functions (optional)
SELECT AI.GENERATE(
  'Summarize this text',
  connection_id => 'project.us.my_connection'
);
```

---

## Remote Models (CREATE MODEL)

### What is a remote model?

A [remote model](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-remote-model) is a BigQuery ML model object that points to an external AI model hosted on Vertex AI. It stores the connection and endpoint configuration so you don't repeat them in every query.

### When do you need one?

Only for the table-valued functions:
- `AI.GENERATE_TEXT` / `ML.GENERATE_TEXT`
- `AI.GENERATE_TABLE`
- `AI.GENERATE_EMBEDDING` / `ML.GENERATE_EMBEDDING`
- `ML.PROCESS_DOCUMENT`

You do **not** need a remote model for:
- AI.GENERATE, AI.GENERATE_BOOL/DOUBLE/INT (specify endpoint directly)
- AI.IF, AI.SCORE, AI.CLASSIFY (auto-select model)
- AI.EMBED, AI.SIMILARITY (specify endpoint directly)
- AI.FORECAST, AI.DETECT_ANOMALIES, AI.EVALUATE (use built-in TimesFM)
- VECTOR_SEARCH, AI.SEARCH (operate on existing data)

### How to create one

**For Gemini models:**
```sql
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.gemini_model`
  REMOTE WITH CONNECTION `PROJECT_ID.LOCATION.CONNECTION_NAME`
  OPTIONS (endpoint = 'gemini-2.5-flash');
```

**For text embedding models:**
```sql
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.embedding_model`
  REMOTE WITH CONNECTION `PROJECT_ID.LOCATION.CONNECTION_NAME`
  OPTIONS (endpoint = 'text-embedding-005');
```

**For multimodal embedding models:**
```sql
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.multimodal_embedding_model`
  REMOTE WITH CONNECTION `PROJECT_ID.LOCATION.CONNECTION_NAME`
  OPTIONS (endpoint = 'multimodalembedding@001');
```

**For Claude models:**
```sql
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.claude_model`
  REMOTE WITH CONNECTION `PROJECT_ID.LOCATION.CONNECTION_NAME`
  OPTIONS (endpoint = 'claude-sonnet-4-20250514');
```

**For Document AI processors (ML.PROCESS_DOCUMENT):**
```sql
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.invoice_parser`
  REMOTE WITH CONNECTION `PROJECT_ID.LOCATION.CONNECTION_NAME`
  OPTIONS (
    REMOTE_SERVICE_TYPE = 'CLOUD_AI_DOCUMENT_V1',
    DOCUMENT_PROCESSOR = 'projects/PROJECT_NUMBER/locations/us/processors/PROCESSOR_ID'
  );
```

### Model and data co-location

The remote model and the data it processes must be in the same region or multi-region. For example, a model created in `us` can only process tables in `us`.

---

## Endpoints

### What is an endpoint?

An endpoint identifies which AI model to use. For Gemini models, you can specify just the model name (e.g., `gemini-2.5-flash`) and BigQuery auto-resolves the full Vertex AI endpoint URL.

### Where endpoints are specified

| Context | Where | Example |
|---------|-------|---------|
| Scalar functions (AI.GENERATE, etc.) | `endpoint` parameter | `endpoint => 'gemini-2.5-flash'` |
| Remote models | `endpoint` option in CREATE MODEL | `endpoint = 'gemini-2.5-flash'` |
| Embedding scalars (AI.EMBED, AI.SIMILARITY) | `endpoint` parameter | `endpoint => 'text-embedding-005'` |

### Model version pinning

- For embedding models, you **must** include the model version: `text-embedding-005`, not `text-embedding`.
- For Gemini models in scalar functions, you can use short names: `gemini-2.5-flash`.
- When no endpoint is specified, AI.GENERATE defaults to `gemini-2.5-flash`; managed functions (AI.IF, AI.SCORE, AI.CLASSIFY) auto-select a model optimized for cost-to-quality tradeoff.

### Global endpoints

You can specify a full global endpoint URL for cross-region processing, but this means you cannot control or know which region processes your data. Avoid global endpoints if you have data residency requirements.

---

## Quotas and Provisioned Throughput

### Dynamic Shared Quota (DSQ)

By default, AI function calls use dynamic shared quota — a pool shared across all BigQuery users in the region. This is sufficient for development and moderate workloads.

### Provisioned Throughput

For production workloads that need guaranteed capacity, you can purchase [Provisioned Throughput](https://cloud.google.com/bigquery/docs/generative-ai-provisioned-throughput). This gives you dedicated quota that isn't shared.

### The `request_type` parameter

Functions that support Provisioned Throughput accept a `request_type` parameter:

| Value | Behavior |
|-------|----------|
| `'UNSPECIFIED'` (default) | Uses Provisioned Throughput if purchased; overflows to DSQ |
| `'DEDICATED'` | Uses only Provisioned Throughput; errors if unavailable |
| `'SHARED'` | Uses only DSQ, even if Provisioned Throughput is purchased |

**Functions that support `request_type`:** AI.GENERATE, AI.GENERATE_BOOL, AI.GENERATE_DOUBLE, AI.GENERATE_INT, AI.GENERATE_TEXT, AI.GENERATE_TABLE, AI.GENERATE_EMBEDDING, ML.GENERATE_TEXT, ML.GENERATE_EMBEDDING.

**Functions that do NOT support `request_type`:** AI.IF, AI.SCORE, AI.CLASSIFY (DSQ only), AI.FORECAST, AI.DETECT_ANOMALIES, AI.EVALUATE (BigQuery ML pricing), VECTOR_SEARCH, AI.SEARCH.

### Purchasing Provisioned Throughput

Purchase through the Google Cloud console for a specific Gemini model and region. Important: for the US multi-region, select `us-central1` when purchasing. For the EU multi-region, select `europe-west4`.

### Handling quota errors

When API call volume exceeds quota, some rows may return `RESOURCE_EXHAUSTED` errors in the `status` column. To iterate until all rows succeed, use:
- [BigQuery remote inference SQL scripts](https://cloud.google.com/bigquery/docs/remote-inference-sql-scripts)
- [BigQuery remote inference pipeline Dataform package](https://cloud.google.com/bigquery/docs/remote-inference-dataform)

---

## Permissions (IAM)

### For end-user credential flows (no connection)

The user running the query needs:
- `roles/bigquery.user` or `roles/bigquery.jobUser` — to run queries
- Access to Vertex AI is implicit through the user's own credentials

### For connection-based flows

The connection's service account needs:
- `roles/aiplatform.user` — to call Vertex AI endpoints

The user running the query needs:
- `roles/bigquery.user` or `roles/bigquery.jobUser` — to run queries
- `roles/bigquery.connectionUser` — to use the connection

### For ML.PROCESS_DOCUMENT

The connection's service account needs additional roles beyond `roles/aiplatform.user`:
- `roles/storage.objectViewer` — to read documents from Cloud Storage via the object table
- `roles/documentai.apiUser` — to call Document AI processors at runtime
- `roles/documentai.viewer` — to read processor metadata when creating the remote model

### For AI.SEARCH

The user needs:
- `roles/bigquery.connectionUser` on the connection specified in the table's autonomous embedding generation configuration

### Additional roles for specific features

| Feature | Required Role |
|---------|---------------|
| Create connections | `roles/bigquery.connectionAdmin` |
| Create models | `roles/bigquery.dataEditor` on the dataset |
| Create vector indexes | `roles/bigquery.dataEditor` on the dataset |
| Use `BLOCK_NONE` safety setting | Restricted access — requires allowlisting |

---

## Object Tables

### What is an object table?

An [object table](https://cloud.google.com/bigquery/docs/object-table-introduction) is an external table that references unstructured data (PDFs, images, audio, video, etc.) stored in Cloud Storage. Object tables provide metadata columns like `uri`, `content_type`, and `size` — enabling BigQuery to reference external files without loading their contents into a table.

### When do you need one?

- **Required** for `ML.PROCESS_DOCUMENT` — the function reads documents through an object table
- Useful for any workflow that processes unstructured files from Cloud Storage within BigQuery

### How to create one

```sql
CREATE OR REPLACE EXTERNAL TABLE `PROJECT_ID.DATASET.my_object_table`
  WITH CONNECTION `PROJECT_ID.LOCATION.CONNECTION_NAME`
  OPTIONS (
    object_metadata = 'SIMPLE',
    uris = ['gs://BUCKET/path/to/files/*']
  );
```

- The connection's service account needs `roles/storage.objectViewer` to read from the specified GCS path.
- `object_metadata = 'SIMPLE'` includes `uri`, `generation`, `content_type`, `size`, `md5_hash`, and `updated` columns.
- The `uris` option supports wildcards (`*`) to match multiple files.

### Verifying an object table

```sql
SELECT uri, content_type, size
FROM `PROJECT_ID.DATASET.my_object_table`
LIMIT 5;
```

---

## Document AI Processors

### What is a Document AI processor?

A [Document AI processor](https://cloud.google.com/document-ai/docs/overview) is a cloud resource that applies a specific document understanding model — invoice parsing, OCR, form extraction, layout analysis, etc. — to documents you send it.

### When do you need one?

- **Required** for `ML.PROCESS_DOCUMENT` — you create a remote model that points to a processor, and the function uses that model to process documents.

### How to create one

**Via the Google Cloud Console:** Navigate to Document AI > Processors > Create Processor, select a processor type (e.g., Invoice Parser), and choose a location.

**Via the Python client:**
```python
from google.cloud import documentai_v1 as documentai

client = documentai.DocumentProcessorServiceClient()
parent = client.common_location_path('PROJECT_ID', 'us')

processor = client.create_processor(
    parent=parent,
    processor=documentai.Processor(
        display_name='my_invoice_parser',
        type_='INVOICE_PROCESSOR',
    ),
)
print(processor.name)  # Use this in CREATE MODEL
```

### Processor types

| Category | Processor | Type ID |
|----------|-----------|---------|
| Digitize Text | Enterprise Document OCR | `OCR_PROCESSOR` |
| Extract (General) | Form Parser | `FORM_PARSER_PROCESSOR` |
| Extract (General) | Layout Parser | `LAYOUT_PARSER_PROCESSOR` |
| Extract (Pretrained) | Invoice Parser | `INVOICE_PROCESSOR` |
| Extract (Pretrained) | Expense Parser | `EXPENSE_PROCESSOR` |
| Extract (Pretrained) | Bank Statement Parser | `BANK_STATEMENT_PROCESSOR` |
| Extract (Pretrained) | W2 Parser | `FORM_W2_PROCESSOR` |
| Summarize | Summarizer | `SUMMARY_PROCESSOR` |

See the [RESOURCES.md](../RESOURCES.md) entry for `ML.PROCESS_DOCUMENT` for the full list.

### Linking a processor to BigQuery

After creating a processor, create a BigQuery remote model that references it:

```sql
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.my_parser_model`
  REMOTE WITH CONNECTION `PROJECT_ID.LOCATION.CONNECTION_NAME`
  OPTIONS (
    REMOTE_SERVICE_TYPE = 'CLOUD_AI_DOCUMENT_V1',
    DOCUMENT_PROCESSOR = 'projects/PROJECT_NUMBER/locations/us/processors/PROCESSOR_ID'
  );
```

The `DOCUMENT_PROCESSOR` value is the full resource name returned when you create the processor (e.g., `projects/123456/locations/us/processors/abc123`).

---

## Autonomous Embedding Generation

### What is it?

Autonomous embedding generation automatically creates and maintains embeddings for a text column in a BigQuery table. When you add or update rows, BigQuery asynchronously generates embeddings using the configured model and connection. This is required for `AI.SEARCH` and optional for `VECTOR_SEARCH` (when using STRING columns).

### How to set it up

1. **Create a table with a generated embedding column:**

```sql
CREATE OR REPLACE TABLE `PROJECT_ID.DATASET.my_table` (
  id INT64,
  text_content STRING,
  -- Generated column that auto-embeds text_content
  text_embedding ARRAY<FLOAT64>
    GENERATED ALWAYS AS (
      AI.EMBED(
        content => text_content,
        endpoint => 'text-embedding-005'
      ).result
    ) STORED
    OPTIONS (asynchronous = TRUE)
);
```

2. **Create a vector index** (recommended for performance):

```sql
CREATE VECTOR INDEX my_index
  ON `PROJECT_ID.DATASET.my_table`(text_embedding)
  OPTIONS (
    index_type = 'IVF',
    distance_type = 'COSINE'
  );
```

3. **Use AI.SEARCH** to query:

```sql
SELECT *
FROM AI.SEARCH(
  TABLE `PROJECT_ID.DATASET.my_table`,
  'text_content',
  'What is the return policy?',
  top_k => 5,
  distance_type => 'COSINE'
);
```

### Key details

- The `asynchronous = TRUE` option means embeddings are generated in the background after data is inserted.
- Rows without completed embeddings are skipped during search.
- The connection used for embedding generation must have the Vertex AI User role.
- When using `AI.SEARCH`, the search query text is embedded at runtime using the same model and connection configured on the table.
