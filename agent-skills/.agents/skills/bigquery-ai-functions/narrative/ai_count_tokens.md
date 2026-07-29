# AI.COUNT_TOKENS — BigQuery AI Functions

`AI.COUNT_TOKENS` is a **utility scalar function** that estimates the number of **input tokens** in a text prompt. Token counting happens inside BigQuery and **incurs no Vertex AI charges** — so you can use it freely to size prompts and estimate cost *before* calling the paid generative functions.

**When to use it:**
- Estimate the cost of an `AI.GENERATE` / `AI.GENERATE_TABLE` job before running it
- Check prompts against a model's input token limit
- Compare prompt sizes across rows, templates, or models

**Alternatives / companions:**
- `functions/ai_generate` (`AI.GENERATE`) — the generation function whose default model this uses when no `endpoint` is given
- Actual per-query token usage (input + thinking + output) appears in the **Job information** tab of the Query results pane

**Note:** `AI.COUNT_TOKENS` counts **input** tokens only — not thinking or output tokens.

**Text only (Preview):** the input must be a `STRING` — multimodal/ObjectRef prompts are not accepted (verified 2026-07-17), so `full_response` always reports `modality: "TEXT"`. This is a Preview function; multimodal support should be re-evaluated at GA.

**References:** `RESOURCES.md` (Full syntax reference) | [Official documentation](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-count-tokens) | `setup` (Setup guide)

---
## Setup

Set your project and location, and authenticate.

> `AI.COUNT_TOKENS` needs no connection and no model — it uses your end-user credentials and counts tokens inside BigQuery. See the `setup` (Setup Reference) for details.

```python
PROJECT_ID = 'statmike-mlops-349915'  # <-- Replace with your project ID
LOCATION = 'US'  # BigQuery dataset location
DATASET_ID = 'bq_ai_functions'  # Shared dataset across all notebooks
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

# Register %%bigquery cell magic (auto-loaded in Colab, needed elsewhere)
%load_ext bigquery_magics
```

---
## Examples — SQL

Progressive examples from simplest to most advanced. `AI.COUNT_TOKENS(INPUT [, endpoint => ENDPOINT])` returns a `STRUCT<result INT64, full_response JSON>`.

### 1. Simplest call — count tokens in a literal string

`.result` is the integer token count. Token count isn't the same as word count.

```python
query = """
SELECT AI.COUNT_TOKENS("Token count isn't always equal to word count.").result AS num_tokens
"""
client.query(query).to_dataframe()
```

### 2. Understand the full output — `result` + `full_response`

`AI.COUNT_TOKENS` returns a `STRUCT` with two fields. Use `.*` to see both, and use `JSON_*` extractors to pull apart `full_response`:

- **`result`** (INT64) — the total input token count
- **`full_response`** (JSON) — `totalTokens` plus a `promptTokensDetails` array giving the token count per input `modality` (always `TEXT` for this text-only function)

```python
query = """
SELECT
  ct.result AS num_tokens,
  ct.full_response AS full_response,
  INT64(ct.full_response.totalTokens) AS total_tokens,
  STRING(ct.full_response.promptTokensDetails[0].modality) AS modality,
  INT64(ct.full_response.promptTokensDetails[0].tokenCount) AS modality_token_count
FROM (
  SELECT AI.COUNT_TOKENS('Summarize the quarterly earnings report.') AS ct
)
"""
client.query(query).to_dataframe()
```

### 3. Count tokens over a table column

Apply it per row to real text — here, public IMDB movie reviews.

```python
query = """
SELECT
  review,
  AI.COUNT_TOKENS(review).result AS num_tokens
FROM `bigquery-public-data.imdb.reviews`
LIMIT 5
"""
client.query(query).to_dataframe()
```

### 4. Specify a model endpoint

`endpoint` selects which model's tokenizer rules to use. If omitted, the default model used by `AI.GENERATE` is used.

```python
query = """
SELECT
  review,
  AI.COUNT_TOKENS(review, endpoint => 'gemini-2.5-pro').result AS num_tokens
FROM `bigquery-public-data.imdb.reviews`
LIMIT 5
"""
client.query(query).to_dataframe()
```

### 5. Estimate cost/size before a batch AI job

Because counting is free, aggregate token counts across a column to size a workload *before* running the paid generation functions over it.

```python
query = """
WITH counts AS (
  SELECT AI.COUNT_TOKENS(review).result AS tokens
  FROM `bigquery-public-data.imdb.reviews`
  LIMIT 100
)
SELECT
  COUNT(*) AS num_documents,
  SUM(tokens) AS total_input_tokens,
  ROUND(AVG(tokens), 1) AS avg_tokens_per_doc,
  MAX(tokens) AS max_tokens
FROM counts
"""
client.query(query).to_dataframe()
```

---
## Examples — `%%bigquery` Magics

The same call using IPython magics — SQL directly in the cell.

### Count tokens with `%%bigquery`

```sql
%%bigquery --project {PROJECT_ID}

SELECT
  review,
  AI.COUNT_TOKENS(review).result AS num_tokens
FROM `bigquery-public-data.imdb.reviews`
LIMIT 5
```

---
## Examples — BigFrames

There is no native BigFrames API for `AI.COUNT_TOKENS` yet. Use `session.read_gbq_query()` to run the SQL and return a BigFrames DataFrame.

```python
import bigframes.pandas as bpd

bpd.close_session()  # Reset session to apply project/location settings
bpd.options.bigquery.project = PROJECT_ID
bpd.options.bigquery.location = LOCATION
```

```python
query = f"""
SELECT
  review,
  AI.COUNT_TOKENS(review).result AS num_tokens
FROM `bigquery-public-data.imdb.reviews`
LIMIT 5
"""
bpd.read_gbq_query(query)
```
