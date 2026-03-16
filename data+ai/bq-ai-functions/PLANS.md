# BigQuery AI Functions — Project Plan

## Vision

A self-contained, progressive-disclosure learning system for BigQuery AI functions. Users start with a high-level overview of what's available and how functions relate, drill into individual functions with incremental hands-on examples across multiple BigQuery interfaces, and graduate to end-to-end workflows that compose functions together.

**Design principles:**
- **Progressive depth**: Overview → Function details → Hands-on examples → Workflows
- **Self-contained examples**: Every notebook runs standalone — setup is inline, sample data is generated with AI.GENERATE_TABLE or inline SQL
- **Multiple interfaces**: Show every way to use these functions — raw SQL, SQL in notebooks, `%%bigquery` magics, and BigFrames Python API
- **Centralized reference, linked not repeated**: Setup concepts (connections, models, endpoints) are explained once in a reference section and linked from examples — not copy-pasted everywhere
- **Simplicity first**: Each example starts simple and layers complexity incrementally

---

## Content Architecture

```
bq-ai-functions/
│
├── README.md                          # GitHub landing page: visual overview, function map, links
├── RESOURCES.md                       # Detailed function reference (complete)
├── PLANS.md                           # This file
├── overview.ipynb                     # Interactive overview notebook
│
├── setup/
│   └── README.md                      # Reference guide: connections, models, endpoints, permissions
│
├── functions/
│   ├── ai_generate/
│   │   ├── ai_generate.sql            # Progressive SQL examples
│   │   └── ai_generate.ipynb          # Notebook: SQL → magics → BigFrames
│   ├── ai_generate_text/
│   │   ├── ...
│   ├── ai_generate_table/
│   ├── ai_generate_bool/
│   ├── ai_generate_double/
│   ├── ai_generate_int/
│   ├── ml_generate_text/
│   ├── ai_if/
│   ├── ai_score/
│   ├── ai_classify/
│   ├── ai_embed/
│   ├── ai_generate_embedding/
│   ├── ml_generate_embedding/
│   ├── ai_similarity/
│   ├── vector_search/
│   ├── ai_search/
│   ├── ai_forecast/
│   ├── ai_detect_anomalies/
│   └── ai_evaluate/
│
└── workflows/
    ├── README.md                      # Index of workflows with descriptions
    └── (individual workflow folders)
```

---

## Component Details

### 1. README.md — GitHub Landing Page

The first thing users see. Must immediately communicate:
- What BigQuery AI functions are (one sentence)
- Visual map of all functions organized by category with one-line descriptions
- How functions relate to each other (which are scalar vs TVF, which require models, which are newer vs legacy)
- Clear navigation: links to each function folder, the setup guide, the overview notebook, and workflows
- A "start here" path for new users

**Format:** Markdown with tables/diagrams. Should render well on GitHub without needing to open anything.

### 2. overview.ipynb — Interactive Overview Notebook

A Colab notebook that:
- Gives a runnable tour of the function landscape
- Shows one simple example per category (generation, classification, embedding, forecasting) so users can see the functions in action
- Helps users decide which functions to explore deeper
- Links to individual function notebooks for deep dives

### 3. setup/ — Centralized Setup Reference

A `README.md` that explains the prerequisites these functions need — not as a "run this first" step, but as a reference that examples link to for deeper understanding.

**Topics to cover:**
- **Connections**: What BigQuery connections are, when they're needed (multimodal, long-running jobs, service accounts), how to create them, required IAM roles (Vertex AI User)
- **Remote Models**: What `CREATE MODEL` does for remote models, when it's needed (AI.GENERATE_TEXT, AI.GENERATE_TABLE, AI.GENERATE_EMBEDDING, ML.* functions) vs when it's not (AI.GENERATE, AI.IF, AI.SCORE, AI.CLASSIFY, AI.EMBED, AI.SIMILARITY, AI.SEARCH, AI.FORECAST, AI.DETECT_ANOMALIES, AI.EVALUATE)
- **Endpoints**: How model endpoints work, version pinning, global endpoints
- **Quotas & Provisioned Throughput**: DSQ vs dedicated, request_type parameter, how to purchase
- **Permissions**: Required IAM roles for different function types
- **Autonomous embedding generation**: What it is, how to configure it (for AI.SEARCH and VECTOR_SEARCH with STRING columns)

Each function's notebook includes inline setup cells but links back here for the "why" explanations.

### 4. functions/ — Per-Function Deep Dives

Each function gets a folder with two files:

#### `.sql` file
Progressive SQL examples, from simplest to most complex. Each example:
- Has a comment header explaining what it demonstrates
- Is runnable in the BigQuery console
- Builds on the previous example (adds one new parameter or concept)

**Example progression for `ai_generate.sql`:**
```
-- Example 1: Simplest possible call (just a prompt)
-- Example 2: Using a column as input
-- Example 3: Specifying an endpoint
-- Example 4: Using output_schema for structured output
-- Example 5: Using model_params (temperature, thinking)
-- Example 6: Multimodal input with ObjectRef
-- Example 7: Grounding with Google Search
-- Example 8: Using request_type for Provisioned Throughput
```

#### `.ipynb` notebook
A Colab notebook with sections:

1. **Setup** — Project config, enable APIs, create any needed resources (connection, model, sample data). Self-contained but with links to `setup/README.md` for deeper explanation.

2. **About this function** — Brief description, when to use it, relationship to other functions (e.g., "AI.GENERATE vs AI.GENERATE_TEXT: use AI.GENERATE when you don't need a pre-created model").

3. **SQL examples** — The same progressive examples from the `.sql` file, but executed inline with results shown. Each in its own cell with markdown explanation.

4. **Using `%%bigquery` magics** — Same examples but using BQ magics in Colab. Shows how to:
   - Run queries with `%%bigquery`
   - Capture results into a DataFrame with `%%bigquery df`
   - Use query parameters

5. **Using BigFrames** — Same examples but using the `bigframes` Python API. Shows how to:
   - Connect to BigQuery via BigFrames
   - Use the BigFrames equivalent of the AI function (if available)
   - Integrate results with pandas-like workflows

6. **Cleanup** — Drop any resources created during setup.

#### Which functions get full treatment vs lightweight treatment

**Full treatment** (all sections, rich examples):
- AI.GENERATE — flagship scalar generation function
- AI.GENERATE_TEXT — flagship TVF generation function
- AI.GENERATE_TABLE — structured output TVF
- AI.IF, AI.SCORE, AI.CLASSIFY — managed functions (unique behavior)
- AI.EMBED — scalar embedding function
- AI.GENERATE_EMBEDDING — TVF embedding function
- VECTOR_SEARCH — semantic search
- AI.SEARCH — simplified semantic search
- AI.FORECAST — time series forecasting
- AI.DETECT_ANOMALIES — anomaly detection
- AI.EVALUATE — forecast evaluation

**Lightweight treatment** (shorter, focused on differences from the recommended version):
- AI.GENERATE_BOOL, AI.GENERATE_DOUBLE, AI.GENERATE_INT — typed scalar variants; show unique aspects, link to AI.GENERATE for shared concepts
- ML.GENERATE_TEXT — legacy; show column naming differences, link to AI.GENERATE_TEXT
- ML.GENERATE_EMBEDDING — legacy; show column naming differences, link to AI.GENERATE_EMBEDDING
- AI.SIMILARITY — show unique comparison use case, link to AI.EMBED for embedding concepts

### 5. workflows/ — Composed End-to-End Workflows

Each workflow is a notebook that uses multiple AI functions together to accomplish a real task. These are the "graduation" content — users should understand individual functions first.

**Completed workflows:**

| Workflow | Functions Used | Description |
|----------|---------------|-------------|
| **[Data Enrichment](workflows/data_enrichment/)** | AI.GENERATE | Fix misspellings, fill missing fields, correct errors via search-grounded web lookups |
| **[Content Analysis Pipeline](workflows/content_analysis/)** | AI.GENERATE_TABLE, AI.CLASSIFY, AI.SCORE, AI.GENERATE | Generate sample data, classify by topic, score urgency, generate executive summary |
| **[Semantic Search System](workflows/semantic_search/)** | AI.EMBED, VECTOR_SEARCH, AI.SEARCH | Build a semantic search index, compare manual (VECTOR_SEARCH) vs simplified (AI.SEARCH) approaches |
| **[RAG Pipeline](workflows/rag_pipeline/)** | AI.GENERATE_TABLE, AI.EMBED, VECTOR_SEARCH, AI.GENERATE | Generate a knowledge base, embed it, search it, answer questions with retrieved context |
| **[Time Series Intelligence](workflows/time_series_intelligence/)** | AI.FORECAST, AI.DETECT_ANOMALIES, AI.EVALUATE | Forecast sales, detect anomalies, evaluate accuracy, compare TimesFM model versions |
| **[Document Intelligence](workflows/document_intelligence/)** | AI.CLASSIFY, AI.GENERATE, AI.SCORE | Classify mixed documents, extract key fields, score quality, summarize findings |
| **[Content Moderation](workflows/content_moderation/)** | AI.GENERATE_TABLE, AI.IF, AI.CLASSIFY, AI.SCORE, AI.GENERATE | Flag, categorize, and score user-generated content for moderation |
| **[Multimodal Analysis](workflows/multimodal_analysis/)** | AI.EMBED, AI.SIMILARITY, AI.GENERATE | Embed document images, find similar documents, generate visual descriptions |

Each workflow notebook includes:
- Problem statement and approach
- Self-contained setup (generates its own data using AI.GENERATE_TABLE or inline SQL)
- Step-by-step implementation with explanations
- Results, visualizations, and interpretation

---

## Sample Data Strategy

A key design decision: examples need data, and we want them self-contained.

**Approach:** Use `AI.GENERATE_TABLE` (or `AI.GENERATE` with `output_schema`) to generate sample data inline. This:
- Makes every example self-contained (no external datasets to load)
- Simultaneously demonstrates AI.GENERATE_TABLE as a function
- Produces realistic, varied data that makes examples meaningful
- Lets us tailor data to each function's strengths

**For functions that need pre-existing tables** (VECTOR_SEARCH, AI.SEARCH, AI.FORECAST):
- Generate data with AI.GENERATE_TABLE, materialize to a temp table or CTE, then use it
- For AI.SEARCH: demonstrate the autonomous embedding generation setup as part of the example

**For time series functions:**
- Use BigQuery public datasets (e.g., `bigquery-public-data.austin_bikeshare.bikeshare_trips`) as shown in the existing documentation examples, or generate synthetic time series with AI.GENERATE_TABLE

**For multimodal document functions** (classification, extraction, document processing):
- BigQuery can't generate images, so synthetic receipts and invoices are pre-generated as PDFs
- See `data/documents/` — a standalone generation pipeline using `AI.GENERATE` + Jinja2 + weasyprint
- PDFs are committed to the repo so downstream notebooks work without running the generator
- Documents are uploaded to GCS with generic naming (`doc_001.pdf`–`doc_100.pdf`) so file names don't reveal type
- A `manifest.json` provides ground truth for classification and extraction accuracy validation

---

## Resource Naming Strategy

All notebooks share a single dataset and reuse common resources. Each notebook creates only what it needs and uses `CREATE OR REPLACE` so running notebooks in any order is safe.

### Config variables (every notebook)

```python
PROJECT_ID = 'your-project-id'
LOCATION = 'US'
DATASET_ID = 'bq_ai_functions'         # Shared dataset (configurable, default: bq_ai_functions)
CONNECTION_ID = 'bq_ai_functions'       # Shared connection (notebooks that need one)
```

Notebooks that don't need a connection (AI.GENERATE, AI.IF, AI.SCORE, AI.CLASSIFY, etc.) omit `CONNECTION_ID`.

### Shared resources (created by whichever notebook runs first)

| Resource | Name | Created by | Used by |
|----------|------|------------|---------|
| Dataset | `bq_ai_functions` | Any notebook | All notebooks |
| Connection | `bq_ai_functions` | Notebooks that need it (auto-created via `bq` CLI) | AI.GENERATE_TEXT, AI.GENERATE_TABLE, AI.GENERATE_EMBEDDING, AI.SEARCH |
| Gemini model | `gemini_flash` | First notebook needing it | AI.GENERATE_TEXT, AI.GENERATE_TABLE, overview |
| Embedding model | `embedding_text` | First notebook needing it | AI.GENERATE_EMBEDDING, ML.GENERATE_EMBEDDING |

All models use `CREATE OR REPLACE` — idempotent and safe to re-run.

**Connection creation pattern** (using `bq` CLI — project/location are separate flags):
```python
import subprocess, json

subprocess.run(
    ['bq', 'mk', '--connection', '--location', LOCATION,
     '--connection_type', 'CLOUD_RESOURCE',
     '--project_id', PROJECT_ID, CONNECTION_ID],
    capture_output=True, text=True
)
r = subprocess.run(
    ['bq', 'show', '--connection', '--format=json',
     '--project_id', PROJECT_ID, '--location', LOCATION, CONNECTION_ID],
    capture_output=True, text=True, check=True
)
sa = json.loads(r.stdout)['cloudResource']['serviceAccountId']
subprocess.run(
    ['gcloud', 'projects', 'add-iam-policy-binding', PROJECT_ID,
     f'--member=serviceAccount:{sa}', '--role=roles/aiplatform.user', '--quiet'],
    capture_output=True, text=True
)
```

**Remote model creation** (use `REMOTE WITH CONNECTION` clause, NOT `connection` in OPTIONS):
```sql
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.gemini_flash`
  REMOTE WITH CONNECTION `PROJECT_ID.LOCATION.CONNECTION_ID`
  OPTIONS (endpoint = 'gemini-2.5-flash')
```

**Selecting from AI functions**: Use explicit column names instead of `SELECT *` to avoid
`full_response`, `status`, and `prompt` metadata columns in the output.

### Notebook-specific resources

Tables and other notebook-specific resources use a `{function_name}_` prefix:

| Notebook | Table examples |
|----------|---------------|
| `ai_forecast` | `ai_forecast_sales`, `ai_forecast_multi_series` |
| `ai_embed` | `ai_embed_documents`, GCS: `gs://BUCKET/bq_ai_functions/ai_embed/` |
| `ai_similarity` | GCS: `gs://BUCKET/bq_ai_functions/ai_similarity/` |
| `ai_search` | `ai_search_knowledge_base` |
| `vector_search` | `vector_search_products` |
| `data_enrichment` (workflow) | `workflow_enrichment_businesses` |
| `content_analysis` (workflow) | `workflow_analysis_reviews`, `workflow_analysis_classified`, `workflow_analysis_scored` |
| `semantic_search` (workflow) | `workflow_search_articles`, `workflow_search_embedded` |
| `rag_pipeline` (workflow) | `workflow_rag_knowledge`, `workflow_rag_embedded` |
| `time_series_intelligence` (workflow) | `workflow_ts_sales` |
| `ml_process_document` | `ml_process_document_invoices` (object table), `ml_process_document_results`, model: `ml_process_document_invoice_parser`, GCS: `gs://BUCKET/bq_ai_functions/ml_process_document/` |
| `document_intelligence` (workflow) | `workflow_di_docs` (object table), `workflow_di_classified`, `workflow_di_extracted`, `workflow_di_scored`, GCS: `gs://BUCKET/bq_ai_functions/document_intelligence/` |
| `ai_generate_embedding` | `ai_generate_embedding_docs`, model: `embedding_multimodal`, GCS: `gs://BUCKET/bq_ai_functions/ai_generate_embedding/` |
| `content_moderation` (workflow) | `workflow_mod_posts`, `workflow_mod_flagged`, `workflow_mod_classified`, `workflow_mod_scored` |
| `multimodal_analysis` (workflow) | `workflow_mm_embeddings`, GCS: `gs://BUCKET/bq_ai_functions/multimodal_analysis/` |

### Cleanup strategy

- **Per-notebook cleanup:** Each notebook drops only the tables it created (by specific name). Shared resources (dataset, models, connection) are left for other notebooks.
- **Full cleanup:** Documented at the bottom of every notebook:
  ```sql
  DROP SCHEMA `your-project-id.bq_ai_functions` CASCADE;
  ```

---

## Cross-Referencing Convention

Bidirectional links between functions and workflows help users navigate the project. Maintain these whenever adding or updating content.

### Function notebooks → Workflows

Every function notebook's overview cell (cell-0) includes a **Featured in:** line listing the workflows that use it:

```markdown
**Featured in:** [Content Analysis Pipeline](../../workflows/content_analysis/) | [RAG Pipeline](../../workflows/rag_pipeline/)
```

This line goes immediately before the **References:** line.

### Workflow notebooks → Functions

Every workflow notebook's overview cell (cell-0) includes a **Functions used:** line listing all functions demonstrated:

```markdown
**Functions used:** [`AI.GENERATE_TABLE`](../../functions/ai_generate_table/) | [`AI.CLASSIFY`](../../functions/ai_classify/) | [`AI.SCORE`](../../functions/ai_score/) | [`AI.GENERATE`](../../functions/ai_generate/)
```

### Current mapping

| Function | Featured in Workflows |
|----------|----------------------|
| AI.GENERATE | Content Analysis, Data Enrichment, RAG Pipeline, Document Intelligence, Content Moderation, Multimodal Analysis |
| AI.GENERATE_TABLE | Content Analysis, RAG Pipeline, Content Moderation |
| AI.IF | Content Moderation |
| AI.CLASSIFY | Content Analysis, Document Intelligence, Content Moderation |
| AI.SCORE | Content Analysis, Document Intelligence, Content Moderation |
| AI.EMBED | Semantic Search, RAG Pipeline, Multimodal Analysis |
| AI.SIMILARITY | Multimodal Analysis |
| VECTOR_SEARCH | Semantic Search, RAG Pipeline |
| AI.SEARCH | Semantic Search |
| AI.FORECAST | Time Series Intelligence |
| AI.DETECT_ANOMALIES | Time Series Intelligence |
| AI.EVALUATE | Time Series Intelligence |

### Maintenance checklist

When **adding a new workflow**:
1. Add `**Functions used:**` line to the workflow's overview cell
2. Add workflow to the `**Featured in:**` line of each function notebook it uses
3. Update the mapping table above

When **adding a new function**:
1. Check if any existing workflows use this function
2. If so, add `**Featured in:**` line to the function's overview cell
3. Update the mapping table above

When **removing a workflow or function**:
1. Remove the cross-references from all linked notebooks
2. Update the mapping table above

---

## Development Phases

### Phase 1: Foundation
- [x] Create folder structure
- [x] Write README.md (landing page with function map and navigation)
- [x] Write setup/README.md (centralized setup reference)
- [x] Create overview.ipynb (interactive tour)

### Phase 2: Core Functions
Build out the full-treatment functions, starting with the most commonly used:
- [x] AI.GENERATE (flagship scalar — template for all others)
- [x] AI.GENERATE_TABLE (structured output TVF)
- [x] AI.GENERATE_TEXT (flagship TVF)
- [x] AI.IF, AI.SCORE, AI.CLASSIFY (managed functions)

### Phase 3: Embeddings & Search
- [x] AI.EMBED
- [x] AI.GENERATE_EMBEDDING
- [x] VECTOR_SEARCH
- [x] AI.SEARCH
- [x] AI.SIMILARITY

### Phase 4: Forecasting
- [x] AI.FORECAST
- [x] AI.DETECT_ANOMALIES
- [x] AI.EVALUATE

### Phase 5: Legacy Functions (Lightweight)
- [x] ML.GENERATE_TEXT
- [x] ML.GENERATE_EMBEDDING
- [x] AI.GENERATE_BOOL, AI.GENERATE_DOUBLE, AI.GENERATE_INT

### Phase 6: Workflows
- [x] [Data Enrichment](workflows/data_enrichment/data_enrichment.ipynb) — search-grounded data quality improvement
- [x] [Content Analysis Pipeline](workflows/content_analysis/content_analysis.ipynb) — classify, score, and summarize product reviews
- [x] [Semantic Search System](workflows/semantic_search/semantic_search.ipynb) — manual vs simplified semantic search
- [x] [RAG Pipeline](workflows/rag_pipeline/rag_pipeline.ipynb) — generate, embed, search, answer with context
- [x] [Time Series Intelligence](workflows/time_series_intelligence/time_series_intelligence.ipynb) — forecast, detect anomalies, evaluate accuracy with visualizations
- [x] [Document Intelligence](workflows/document_intelligence/document_intelligence.ipynb) — classify, extract, score, and summarize real documents
- [x] [Content Moderation](workflows/content_moderation/content_moderation.ipynb) — flag, categorize, and score content for moderation
- [x] [Multimodal Analysis](workflows/multimodal_analysis/multimodal_analysis.ipynb) — embed images, find similar products, generate visual descriptions

### Phase 7: Polish
- [x] Cross-link everything (functions ↔ workflows bidirectional, functions ↔ alternatives)
- [x] Review for consistency across all notebooks
- [x] Test all examples end-to-end
- [x] Standardize cleanup sections: split into two cells (notebook-specific cleanup, then project-wide cleanup)

### Phase 8: Multimodal Document Data
- [x] Synthetic document generation pipeline (`data/documents/generate.ipynb`)
- [x] Receipt and invoice PDF templates (Jinja2 + weasyprint)
- [x] Reusable Python modules (`schemas.py`, `renderers.py`, `styles.py`)
- [x] Ground truth manifest with generic GCS naming
- [x] ML.PROCESS_DOCUMENT notebook (invoice parsing with Document AI)
- [x] ObjectRef multimodal examples added to Tier 1 notebooks (AI.GENERATE, AI.CLASSIFY, AI.GENERATE_TABLE)
- [x] ObjectRef multimodal examples added to Tier 2 notebooks (AI.GENERATE_BOOL, AI.GENERATE_DOUBLE, AI.GENERATE_INT, AI.IF, AI.SCORE, AI.GENERATE_TEXT)
- [x] SQL files updated with matching ObjectRef examples for all Tier 1 and Tier 2 functions
- [x] README.md: ObjectRef column → Multimodal with per-function input method labels + Multimodal Input section
- [x] RESOURCES.md: Multimodal Input Patterns section with 4 patterns, SQL examples, and summary table
- [x] Embedding notebook multimodal examples (AI.EMBED, AI.GENERATE_EMBEDDING, AI.SIMILARITY — multimodal embedding with multimodalembedding@001)
- [x] Document Intelligence workflow (combines classification + extraction + scoring + summarization)
- [x] Content Moderation workflow (AI.GENERATE_TABLE → AI.IF → AI.CLASSIFY → AI.SCORE → AI.GENERATE)
- [x] Multimodal Analysis workflow (document rendering → AI.EMBED → ML.DISTANCE → AI.SIMILARITY → AI.GENERATE)
- [x] README.md and RESOURCES.md updated with implementation learnings (inline ObjectRef vs object tables, multimodal statistics, cross-modal similarity, PDF limitations)

---

## Resolved Questions

### 1. BigFrames API Coverage Audit

**Audited from `bigframes` package source code.** BigFrames provides two API surfaces for AI functions:

**`bigframes.bigquery.ai.*` — Scalar AI functions (maps to BQ's `AI.*` scalar functions):**

| BQ SQL Function | BigFrames API | Notes |
|----------------|---------------|-------|
| `AI.GENERATE` | `bbq.ai.generate()` | Returns Series of structs. Supports `output_schema` as `Mapping[str, str]`. |
| `AI.GENERATE_BOOL` | `bbq.ai.generate_bool()` | Returns Series of structs with BOOL result. |
| `AI.GENERATE_INT` | `bbq.ai.generate_int()` | Returns Series of structs with INT64 result. |
| `AI.GENERATE_DOUBLE` | `bbq.ai.generate_double()` | Returns Series of structs with FLOAT64 result. |
| `AI.IF` | `bbq.ai.if_()` | Returns Series of BOOL directly (not struct). No endpoint param — auto-selects model. |
| `AI.CLASSIFY` | `bbq.ai.classify()` | Returns Series of STRING directly. Takes `categories` as list/tuple. |
| `AI.SCORE` | `bbq.ai.score()` | Returns Series of FLOAT64 directly. No endpoint param — auto-selects model. |

**`bigframes.bigquery.ai.*` — TVF wrappers (execute SQL queries under the hood):**

| BQ SQL Function | BigFrames API | Notes |
|----------------|---------------|-------|
| `AI.GENERATE_TEXT` | `bbq.ai.generate_text(model, data)` | Takes model name string + DataFrame/Series. Generates `AI.GENERATE_TEXT` SQL. |
| `AI.GENERATE_TABLE` | `bbq.ai.generate_table(model, data, output_schema=...)` | Takes model name string + DataFrame/Series. `output_schema` can be string or mapping. |
| `AI.GENERATE_EMBEDDING` | `bbq.ai.generate_embedding(model, data)` | Takes model name string + DataFrame/Series. Generates `AI.GENERATE_EMBEDDING` SQL. |
| `AI.FORECAST` | `bbq.ai.forecast(df, data_col=..., timestamp_col=...)` | No model object needed. Wraps `AI.FORECAST` SQL directly. Supports `id_cols`, `horizon`, `confidence_level`, `context_window`. |

**`bigframes.bigquery.*` — Search functions:**

| BQ SQL Function | BigFrames API | Notes |
|----------------|---------------|-------|
| `VECTOR_SEARCH` | `bbq.vector_search(base_table, column, query)` | Takes base table as string, query as DataFrame/Series. Supports `distance_type`, `top_k`, `fraction_lists_to_search`, `use_brute_force`. |
| `CREATE VECTOR INDEX` | `bbq.create_vector_index(table, column)` | DDL helper for creating vector indexes. |

**`bigframes.ml.llm.*` — Scikit-learn style model classes (create model + predict):**

| BQ SQL Function | BigFrames Class | Notes |
|----------------|----------------|-------|
| `AI.GENERATE_TEXT` / `ML.GENERATE_TEXT` | `bigframes.ml.llm.GeminiTextGenerator` | Creates remote model, `.predict()` calls GENERATE_TEXT. Supports `output_schema` on predict (uses GENERATE_TABLE under the hood). Also supports `.fit()` for fine-tuning and `.score()` for evaluation. |
| `AI.GENERATE_TEXT` / `ML.GENERATE_TEXT` | `bigframes.ml.llm.Claude3TextGenerator` | Same pattern for Claude models. |
| `AI.GENERATE_EMBEDDING` / `ML.GENERATE_EMBEDDING` | `bigframes.ml.llm.TextEmbeddingGenerator` | Creates remote model, `.predict()` calls GENERATE_EMBEDDING. |
| `AI.GENERATE_EMBEDDING` / `ML.GENERATE_EMBEDDING` | `bigframes.ml.llm.MultimodalEmbeddingGenerator` | Same for multimodal embeddings. |

**`bigframes.ml.forecasting.*` — Scikit-learn style forecasting:**

| BQ SQL Function | BigFrames Class | Notes |
|----------------|----------------|-------|
| `ML.FORECAST` (ARIMA_PLUS) | `bigframes.ml.forecasting.ARIMAPlus` | Traditional ARIMA_PLUS model. `.predict()` for forecast, `.detect_anomalies()`, `.evaluate()`, `.summary()`. This is NOT the same as `AI.FORECAST` (TimesFM). |

**Functions with NO BigFrames equivalent:**

| BQ SQL Function | Status | Workaround |
|----------------|--------|------------|
| `AI.EMBED` | No BigFrames API | Use `%%bigquery` magics or raw SQL via `session.read_gbq_query()` |
| `AI.SIMILARITY` | No BigFrames API | Use `%%bigquery` magics or raw SQL via `session.read_gbq_query()` |
| `AI.SEARCH` | No BigFrames API | Use `%%bigquery` magics or raw SQL via `session.read_gbq_query()` |
| `AI.DETECT_ANOMALIES` (TimesFM) | No BigFrames API | Use `%%bigquery` magics or raw SQL. (Note: `ARIMAPlus.detect_anomalies()` exists but uses ARIMA_PLUS, not TimesFM.) |
| `AI.EVALUATE` (TimesFM) | No BigFrames API | Use `%%bigquery` magics or raw SQL. (Note: `ARIMAPlus.evaluate()` exists but uses ARIMA_PLUS, not TimesFM.) |
| `ML.GENERATE_TEXT` | No direct API | Use `bbq.ai.generate_text()` (wraps `AI.GENERATE_TEXT` instead) or `GeminiTextGenerator` |
| `ML.GENERATE_EMBEDDING` | No direct API | Use `bbq.ai.generate_embedding()` (wraps `AI.GENERATE_EMBEDDING` instead) or `TextEmbeddingGenerator` |

**Key insight for notebooks:** Most functions have BigFrames coverage via `bbq.ai.*`, but 5 functions (AI.EMBED, AI.SIMILARITY, AI.SEARCH, AI.DETECT_ANOMALIES, AI.EVALUATE) will need a `session.read_gbq_query()` workaround in the BigFrames section. This is still valuable to show — it demonstrates that BigFrames can always fall back to raw SQL execution.

**Prompt pattern difference:** The scalar `bbq.ai.*` functions use a tuple-based prompt pattern:
```python
bbq.ai.generate(("Summarize: ", df["text_col"]))
bbq.ai.if_((df["review"], " is a positive review"))
bbq.ai.classify(df["text"], ["positive", "negative", "neutral"])
```
This is worth highlighting in notebooks as a distinct "BigFrames way" vs the SQL prompt concatenation approach.

### 2. Notebook Template

**Decision:** Yes — establish a standard template before building notebooks. Setup at top, cleanup/delete at bottom.

**Template structure:**

```
# [Function Name] — BigQuery AI Functions

## Overview
- What this function does (1-2 sentences)
- When to use it vs alternatives
- **Featured in:** links to workflow notebooks that use this function
- **References:** links to RESOURCES.md, official docs, setup guide

## Setup
- Set project, region, dataset, connection variables

### Environment
> **Already set up the project environment?** ... See the Setup Reference for details.
> **Running standalone** (Colab, Colab Enterprise, Vertex AI Workbench)? ...

- install() helper cell — uv-first with pip fallback, per-notebook package list:
  ```python
  import subprocess, sys, shutil

  def install(*packages):
      """Install packages using uv (fast) with pip fallback."""
      uv = shutil.which('uv')
      if uv:
          subprocess.check_call([uv, 'pip', 'install', '-q', '--python', sys.executable, *packages])
      else:
          subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-q', '--upgrade', *packages])

  install('google-cloud-bigquery', 'db-dtypes', 'bigquery-magics', 'tqdm', ...)  # per-notebook list
  ```

- Authenticate — try Colab auth, fall back to ADC:
  ```python
  try:
      from google.colab import auth
      auth.authenticate_user()
  except ImportError:
      pass  # Not in Colab — ADC is used automatically
  ```

- Create BQ client + shared dataset
- Register `%%bigquery` magic: `%load_ext bigquery_magics`
- Create connection (if needed — use `bq` CLI, see below)
- Create remote model (if needed — use `REMOTE WITH CONNECTION`, see below)
- Generate sample data with AI.GENERATE_TABLE (where applicable)

## Examples — SQL
Progressive SQL examples, each in its own cell with markdown explanation.
Start with simplest possible call, layer one concept per example.

**Display pattern:** For single-row text results, use `print(df.iloc[0]['col'])` instead of
showing the DataFrame — this renders newlines properly. For multi-row tabular results,
use `.to_dataframe()` directly.

**Quoting `output_schema` with descriptions:** When `bq_schema()` produces descriptions
containing single quotes (`OPTIONS(description = '...')`), use BigQuery triple-double-quotes
(`"""..."""`) to wrap the output_schema value. In Python, use `f'''...'''` for the f-string
so `"""` can nest inside:
```python
output_schema = bq_schema(MyModel)
query = f'''SELECT ... output_schema => """{output_schema}""" ...'''
```

## Examples — %%bigquery Magics
Same examples using magics. Show:
- Basic %%bigquery execution
- %%bigquery df — capturing results to DataFrame

**Important:** `%%bigquery` magics can interpolate Python variables on the magic line
(`--project {PROJECT_ID}`) but NOT in the SQL body. For SQL that references Python
variables (model names, table names), use `client.query()` with f-strings instead.

## Examples — BigFrames
Same examples using bigframes.bigquery.ai.* API (or session.read_gbq_query() fallback).
Show the BigFrames prompt pattern and DataFrame integration.

## Cleanup
- Per-notebook: drop only tables this notebook created (by specific name)
- Shared resources (dataset, models, connection) left for other notebooks
- Full cleanup documented (commented out): `DROP SCHEMA ... CASCADE`
```

**Per-notebook package lists** (every notebook includes `bigquery-magics` and `tqdm`):

| Notebook | Additional Packages |
|----------|----------|
| `overview.ipynb` | `matplotlib` |
| Generation functions | `bigframes`, `pydantic` |
| Managed functions | `bigframes` |
| Embedding/search functions | `bigframes` |
| Forecasting functions | `bigframes`, `matplotlib` |
| Workflows | `bigframes`, `pydantic`, `matplotlib` |

All notebooks include: `google-cloud-bigquery`, `db-dtypes`, `bigquery-magics`, `tqdm`

### 3. Time Series Data Generation Strategy

**Decision:** Use AI-generated synthetic data with schema-driven patterns. This keeps examples self-contained while producing realistic, interesting time series.

**Approach:** Use `AI.GENERATE` (or `AI.GENERATE_TABLE`) with a carefully crafted prompt and `output_schema` to generate time series data that has built-in patterns. The prompt instructs the model to create data with specific characteristics:

```sql
-- Example: Generate daily sales data with realistic patterns
SELECT *
FROM AI.GENERATE_TABLE(
  MODEL `project.dataset.gemini_model`,
  (SELECT "Generate 365 rows of daily retail sales data for 2025.
    Include realistic patterns:
    - Weekly seasonality: higher sales on Friday/Saturday, lowest on Monday
    - Monthly trends: peaks in November-December (holidays), dip in January
    - Weekend effect: Saturday 30% higher than weekday average
    - Holiday spikes: Black Friday, Christmas week, Memorial Day, July 4th, Labor Day
    - Overall upward trend of ~10% year-over-year
    - Some random noise (±5-15%)
    - Base daily sales around 10,000 units
    Include columns for date, daily_sales, and store_id (3 stores with different baseline volumes)." AS prompt),
  STRUCT(
    "date DATE, store_id STRING, daily_sales FLOAT64" AS output_schema
  )
)
```

**Why this works well:**
- Self-contained: no external datasets to reference
- Demonstrates AI.GENERATE_TABLE simultaneously
- The `output_schema` enforces proper column types
- The prompt can describe exactly the patterns we want (trends, seasonality, holidays, weekends)
- Each run produces slightly different but structurally similar data
- We can adjust complexity: simple (1 series, basic trend) → complex (multiple series, multiple seasonal patterns, anomalies)

**Considerations:**
- Generated data may not perfectly follow instructions (LLMs aren't precise number generators) — this is actually fine because it creates realistic "messy" data
- For anomaly detection demos: generate a separate "clean" history and a "target" period with injected anomalies
- For evaluation demos: generate a longer series, use first N% as history, last N% as actuals
- 365 rows × 3 stores = 1,095 rows is well within generation limits

**Alternative hybrid approach:** For very precise patterns, generate the structure with SQL (date spine + CASE expressions for day-of-week/holiday logic) and use AI only for realistic noise or descriptions. This gives exact control over patterns while keeping the creative/realistic elements AI-driven.

### 4. Google Search Grounding + output_schema Incompatibility

**Discovered while building the Data Enrichment workflow.** Using `AI.GENERATE` with both
Google Search grounding (`model_params => JSON '{"tools": [{"googleSearch": {}}]}'`) and
`output_schema` in the same call returns all NULL fields. Grounding produces text with
citations that can't be parsed into a typed schema.

**Workaround:** Use a two-step CTE approach:
1. First `AI.GENERATE` call: grounding enabled, no `output_schema` → returns text with real info
2. Second `AI.GENERATE` call: `output_schema` enabled, no grounding → parses the text into structured fields

```sql
WITH grounded AS (
  SELECT
    source.name AS original_name,
    (AI.GENERATE(
      CONCAT('Look up this business: ', source.name, ...),
      model_params => JSON '{"tools": [{"googleSearch": {}}]}'
    )).result AS lookup_text
  FROM source_table AS source
)
SELECT g.original_name, result.*
FROM grounded AS g,
UNNEST([
  AI.GENERATE(
    CONCAT('Extract business info from this text: ', g.lookup_text),
    output_schema => "name STRING, address STRING, ..."
  )
]) AS result
```

**Also learned:** When the extraction step encounters values it can't find, it may return
the literal string `"null"` instead of an empty string. Fix by adding to the extraction
prompt: `"If any value is not found, return an empty string — never return the word null."`

---

## Maintenance & Audit

### Change types and checklists

#### Status change (Preview → GA)

A function moves from Preview to GA. Minimal content changes, mostly status labels.

- [ ] `RESOURCES.md`: Update status in the function's entry and in the category comparison table
- [ ] `README.md`: Update status column in the function map table
- [ ] Function notebook `cell-0`: Remove "Preview" mention if present in the description
- [ ] Function `.sql` file: Remove any Preview notes in the header comment
- [ ] Audit log: Record the change

#### New capability (new parameter, new model version, new supported model, etc.)

An existing function gains new features — e.g., a new parameter, a new supported model version, grounding support, etc.

- [ ] `RESOURCES.md`: Update syntax, inputs, outputs, supported models, and/or comparison table
- [ ] Function notebook: Add or update an example if the capability is significant enough to demonstrate
- [ ] Function `.sql` file: Add an example if appropriate
- [ ] Related function notebooks: Update "Alternatives" sections if relationships changed
- [ ] Workflow notebooks: Check if any workflows should demonstrate the new capability
- [ ] Audit log: Record the change

#### Removed capability (deprecated model version, removed parameter, etc.)

A function loses a capability — e.g., a model version is retired (like TimesFM 1.0 → 2.0/2.5).

- [ ] `RESOURCES.md`: Remove from syntax, inputs, supported models, and comparison table
- [ ] Function notebook: Update or remove examples that use the deprecated capability
- [ ] Function `.sql` file: Update or remove affected examples
- [ ] Workflow notebooks: Update any workflows that use the deprecated capability
- [ ] Audit log: Record the change

#### New function

A completely new BigQuery AI function is released.

- [ ] `RESOURCES.md`: Add full entry in the appropriate category section; update the category comparison table
- [ ] `README.md`: Add to the function map table; update category descriptions if needed
- [ ] Create `functions/{name}/` folder with:
  - `.ipynb` notebook following the template (overview → setup → SQL examples → magics → BigFrames → cleanup)
  - `.sql` file with progressive SQL examples
- [ ] Cross-reference — Alternatives: Add links to/from related function notebooks
- [ ] Cross-reference — Featured in: If used in any workflows, add `**Featured in:**` line; update workflow `**Functions used:**` lines
- [ ] `PLANS.md`: Update the cross-referencing mapping table; add to development phases if tracking
- [ ] Audit log: Record the addition

#### New workflow

A new end-to-end workflow notebook is added.

- [ ] Create `workflows/{name}/` folder with `.ipynb` notebook
- [ ] `workflows/README.md`: Add to the workflow index table
- [ ] `README.md`: Add to the workflow table in the landing page
- [ ] Cross-reference: Add `**Functions used:**` line to the workflow's overview cell
- [ ] Cross-reference: Add the workflow to the `**Featured in:**` line of each function notebook it uses
- [ ] `PLANS.md`: Update the cross-referencing mapping table and the completed workflows list
- [ ] Audit log: Record the addition

### How to run an audit

Each function's documentation URL is already recorded in `RESOURCES.md`. An audit compares our content against the current official documentation.

**Process:**

1. For each function, fetch its documentation URL from `RESOURCES.md`
2. Compare the current docs against our `RESOURCES.md` entry — look for:
   - Status changes (Preview → GA)
   - New or removed parameters
   - New or retired model versions
   - Syntax changes
   - New capabilities (grounding, new output fields, etc.)
   - Changes to limitations or locations
3. For any differences found, apply the relevant checklist above
4. Record what was checked and changed in the audit log below

**Documentation URLs (from RESOURCES.md):**

| Function | Documentation URL |
|----------|-------------------|
| AI.GENERATE | https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-generate |
| AI.GENERATE_TEXT | https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-generate-text |
| AI.GENERATE_TABLE | https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-generate-table |
| AI.GENERATE_BOOL | https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-generate-bool |
| AI.GENERATE_DOUBLE | https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-generate-double |
| AI.GENERATE_INT | https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-generate-int |
| ML.GENERATE_TEXT | https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-generate-text |
| AI.IF | https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-if |
| AI.SCORE | https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-score |
| AI.CLASSIFY | https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-classify |
| AI.EMBED | https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-embed |
| AI.GENERATE_EMBEDDING | https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-generate-embedding |
| ML.GENERATE_EMBEDDING | https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-generate-embedding |
| AI.SIMILARITY | https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-similarity |
| VECTOR_SEARCH | https://cloud.google.com/bigquery/docs/reference/standard-sql/search_functions#vector_search |
| AI.SEARCH | https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-search |
| AI.FORECAST | https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-forecast |
| AI.DETECT_ANOMALIES | https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-detect-anomalies |
| AI.EVALUATE | https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-evaluate |

### Audit log

| Date | Scope | Changes Found |
|------|-------|---------------|
| 2026-03-13 | Initial build | All 19 functions documented, tested, and cross-referenced |
| 2026-03-13 | AI.EVALUATE, AI.FORECAST, AI.DETECT_ANOMALIES | TimesFM 1.0 retired — valid models are now TimesFM 2.0 and TimesFM 2.5. Updated time_series_intelligence workflow. |
| 2026-03-16 | Multimodal/ObjectRef documentation | Updated README.md: renamed ObjectRef column to Multimodal with per-function input method labels, added Multimodal Input section with pattern legend. Updated RESOURCES.md: added Multimodal Input Patterns section with 4 patterns (STRUCT prompt, tuple+object table, EXTERNAL_OBJECT_TRANSFORM, ObjectRef content), SQL examples, and summary table. Updated compatible functions lists. |
| 2026-03-16 | Phase 8 expansion | Added multimodal embedding examples to AI.EMBED, AI.GENERATE_EMBEDDING, AI.SIMILARITY notebooks + SQL files (multimodalembedding@001). Added multimodal note to ML.GENERATE_EMBEDDING. Created Content Moderation workflow (AI.GENERATE_TABLE → AI.IF → AI.CLASSIFY → AI.SCORE → AI.GENERATE). Created Multimodal Analysis workflow (document rendering → AI.EMBED → ML.DISTANCE → AI.SIMILARITY → AI.GENERATE). Updated all cross-references (7 function notebook Featured in lines, README.md workflows table, PLANS.md mapping table). |
| 2026-03-16 | Docs review post-implementation | README.md: Fixed AI.SCORE and AI.CLASSIFY multimodal labels from "Object table" to "STRUCT prompt" (both accept STRUCT with ObjectRefRuntime). RESOURCES.md: Added multimodal best practices to AI.EMBED (default 1408 dims, PDF not supported, inline ObjectRef preferred), AI.GENERATE_EMBEDDING (statistics not returned by multimodal model, inline ObjectRef avoids reservation requirement), AI.SIMILARITY (cross-modal text↔image capability). Updated Managed Functions table. Added "Object tables vs inline ObjectRef" guidance to Unstructured Data Infrastructure section. |

---

## Remaining Open Questions

1. **Colab vs Vertex AI Workbench**: Should notebooks target plain Colab or also show Vertex AI Workbench usage?
