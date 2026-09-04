![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2Fdata%2Bai%2Fbq-ai-functions&file=PLANS.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/data%2Bai/bq-ai-functions/PLANS.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-ai-functions/PLANS.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-ai-functions/PLANS.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-ai-functions/PLANS.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-ai-functions/PLANS.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
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
| **[Data Enrichment](workflows/data_enrichment/)** | AI.GENERATE, AI.PREDICT | Fix misspellings and correct errors via search-grounded web lookups, then fill a missing structured attribute with TabFM |
| **[Content Analysis Pipeline](workflows/content_analysis/)** | AI.GENERATE_TABLE, AI.CLASSIFY, AI.SCORE, AI.GENERATE | Generate sample data, classify by topic, score urgency, generate executive summary |
| **[Semantic Search System](workflows/semantic_search/)** | AI.EMBED, VECTOR_SEARCH, AI.SEARCH | Build a semantic search index, compare manual (VECTOR_SEARCH), simplified (AI.SEARCH), and hybrid approaches |
| **[RAG Pipeline](workflows/rag_pipeline/)** | AI.GENERATE_TABLE, AI.EMBED, VECTOR_SEARCH, AI.GENERATE | Generate a knowledge base, embed it, search it, answer questions with retrieved context |
| **[Time Series Intelligence](workflows/time_series_intelligence/)** | AI.FORECAST, AI.DETECT_ANOMALIES, AI.EVALUATE, AI.KEY_DRIVERS | Forecast sales, detect anomalies, evaluate accuracy, compare TimesFM model versions, explain a change by segment |
| **[Metric Diagnostics](workflows/metric_diagnostics/)** | AI.KEY_DRIVERS, AI.PREDICT, AI.GENERATE | Explain why a metric moved between two periods, project it forward with TabFM, then narrate the key drivers in plain language |
| **[Document Intelligence](workflows/document_intelligence/)** | AI.CLASSIFY, AI.GENERATE, AI.SCORE | Classify mixed documents, extract key fields, score quality, summarize findings |
| **[Content Moderation](workflows/content_moderation/)** | AI.GENERATE_TABLE, AI.IF, AI.CLASSIFY, AI.SCORE, AI.GENERATE | Flag, categorize, and score user-generated content for moderation |
| **[Multimodal Analysis](workflows/multimodal_analysis/)** | AI.EMBED, AI.SIMILARITY, AI.GENERATE | Embed document images, find similar documents, generate visual descriptions |
| **[Document RAG](workflows/document_rag/)** ⚠️ | AI.PARSE_DOCUMENT, AI.EMBED, VECTOR_SEARCH, AI.GENERATE | Parse real documents, embed chunks, search, answer questions with grounded context. **Blocked — AI.PARSE_DOCUMENT is offline and its docs are withdrawn. Do not re-run.** |
| **[Log Analysis](workflows/log_analysis/)** | AI.GENERATE_TABLE, AI.CLASSIFY, AI.SCORE, AI.AGG, AI.EMBED, VECTOR_SEARCH | Classify support tickets, score priority, summarize patterns, and retrieve by error code with hybrid search |
| **[Image Deduplication](workflows/image_deduplication/)** | AI.EMBED, VECTOR_SEARCH | Group near-duplicate images using embedding similarity to protect train/test split integrity |
| **[Catalog Search](workflows/catalog_search/)** | AI.EMBED, VECTOR_SEARCH, AI.SEARCH | Hybrid retrieval over a product catalog — exact-token lookups pure semantics misses, with a populated vector index |
| **[Zero-Shot Tabular Prediction](workflows/tabular_prediction/)** | AI.PREDICT, AI.EVALUATE, AI.KEY_DRIVERS, AI.GENERATE | Zero-shot regression and classification with TabFM, evaluated and explained, with no model training |

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
| `log_analysis` (workflow) | `workflow_log_tickets`, `workflow_log_classified`, `workflow_log_scored`, `workflow_log_embedded` |
| `ai_predict` | none — AI.PREDICT creates no persistent resources |
| `image_deduplication` (workflow) | `workflow_dedup_embeddings` |
| `metric_diagnostics` (workflow) | `workflow_metricdiag_trips`, `workflow_metricdiag_segments`, `workflow_metricdiag_drivers`, `workflow_metricdiag_projection` |
| `catalog_search` (workflow) | `workflow_catalog_auto`, `workflow_catalog_products`, vector index: `workflow_catalog_hybrid_index` |
| `tabular_prediction` (workflow) | `workflow_tabpred_split`, `workflow_tabpred_regression`, `workflow_tabpred_classification`, `workflow_tabpred_h2h`, `workflow_tabpred_drivers` |

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

Every function notebook's overview cell (cell index **1** — cell index 0 is the header/badge table) includes a **Featured in:** line listing the workflows that use it:

```markdown
**Featured in:** [Content Analysis Pipeline](workflows/content_analysis/) | [RAG Pipeline](workflows/rag_pipeline/)
```

This line goes immediately before the **References:** line.

### Workflow notebooks → Functions

Every workflow notebook's overview cell (cell index **1** — cell index 0 is the header/badge table) includes a **Functions used:** line listing all functions demonstrated:

```markdown
**Functions used:** [`AI.GENERATE_TABLE`](functions/ai_generate_table/) | [`AI.CLASSIFY`](functions/ai_classify/) | [`AI.SCORE`](functions/ai_score/) | [`AI.GENERATE`](functions/ai_generate/)
```

### Link policy

This project is the canonical source of truth for BigQuery AI functions, and its content
is copied into a distributable agent skill that has to make sense with the rest of the
repository absent. A reference that points outside the project does not travel.

A link may target:

1. **this project** — relative, e.g. `functions/ai_generate/`
2. **the sibling project** — `../bq-ml/...`
3. **public documentation or public data** — `https://...`

Anything else is a violation: elsewhere in this repository, or outside it. Other parts
of the repo may link *in* to this project; this project does not link *out*.

Two cases are treated differently:

- A **link** (`[text](target)`) is followable, so an outward one always violates.
- A **mention** (a backticked path in prose) violates only when the target still exists
  outside the project — that is a live pointer a reader will chase. A mention of a path
  that no longer exists is *retirement provenance*: it records where content came from
  and there is nothing to follow, so it stays.

When removing an outward reference, **change the pointer, never delete the fact.** The
description attached to a link is usually first-hand knowledge; keep the sentence and
retarget it — to the native equivalent where one exists, or to public documentation when
the subject is genuinely another product surface.

Exemptions:

- **`PLANS.md`** is forward-looking, repo-bound, and never shipped in a skill. It may
  cite anything, including sources outside the repository.
- **`README.md`** may link to `agent-skills/`, the artifact built from this project.

Enforced by `agent-skills/tooling`:

```bash
cd agent-skills && PYTHONPATH=tooling/src python3 -m agent_skills_tooling.cli check-links \
  ../data+ai/bq-ai-functions --sibling ../data+ai/bq-ml --repo-root ..
```

This project currently passes with zero violations; `bq-ml` does not yet.

### Current mapping

| Function | Featured in Workflows |
|----------|----------------------|
| AI.GENERATE | Content Analysis, Data Enrichment, RAG Pipeline, Document Intelligence, Content Moderation, Multimodal Analysis, Document RAG, Metric Diagnostics, Tabular Prediction |
| AI.GENERATE_TABLE | Content Analysis, RAG Pipeline, Content Moderation, Log Analysis |
| AI.IF | Content Moderation |
| AI.CLASSIFY | Content Analysis, Document Intelligence, Content Moderation |
| AI.SCORE | Content Analysis, Document Intelligence, Content Moderation |
| AI.AGG | Content Analysis, Content Moderation, Document Intelligence, Log Analysis |
| AI.EMBED | Semantic Search, Catalog Search, RAG Pipeline, Multimodal Analysis, Document RAG, Log Analysis, Image Deduplication |
| AI.SIMILARITY | Multimodal Analysis |
| VECTOR_SEARCH | Semantic Search, Catalog Search, RAG Pipeline, Document RAG, Log Analysis, Image Deduplication |
| AI.SEARCH | Semantic Search, Catalog Search |
| AI.FORECAST | Time Series Intelligence |
| AI.DETECT_ANOMALIES | Time Series Intelligence |
| AI.PREDICT | Tabular Prediction, Metric Diagnostics, Data Enrichment |
| AI.EVALUATE | Time Series Intelligence, Tabular Prediction |
| AI.KEY_DRIVERS | Metric Diagnostics, Time Series Intelligence, Tabular Prediction |
| AI.PARSE_DOCUMENT | Document RAG |
| AI.COUNT_TOKENS | — (utility; not featured in a workflow) |

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

On **every** change, before commit:
1. Run `check-links` (command above) — it must report zero violations
2. Regenerate any affected `agent-skills/` narrative in the same commit

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

### Phase 4: Predictive AI (originally "Forecasting")
- [x] AI.FORECAST
- [x] AI.DETECT_ANOMALIES
- [x] AI.EVALUATE
- [x] AI.PREDICT — added in Phase 10; the section was renamed from Forecasting to Predictive AI when TabFM joined TimesFM

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

### Phase 9: New Functions
- [x] AI.AGG — aggregate function with auto-batching (function notebook + SQL + RESOURCES.md + README.md)
- [x] AI.AGG added to existing workflows: Content Analysis, Content Moderation, Document Intelligence
- [x] [Log Analysis](workflows/log_analysis/log_analysis.ipynb) — classify, score, and summarize support tickets with AI.AGG

### Phase 10: AI.PREDICT and Hybrid Search (2026-09-01)

Driven by three upstream changes landing together: `AI.PREDICT` shipped, `AI.EVALUATE` gained a second (tabular) branch, and hybrid search arrived as parameters on the two existing search functions rather than as the long-expected `HYBRID_SEARCH` TVF.

**New function**
- [x] `AI.PREDICT` — zero-shot tabular regression and classification on TabFM (`functions/ai_predict/`, 30 cells, 6 SQL examples, penguins)

**New workflows**
- [x] [Zero-Shot Tabular Prediction](workflows/tabular_prediction/) — AI.PREDICT → AI.EVALUATE → AI.KEY_DRIVERS → AI.GENERATE, with a head-to-head against trained bq-ml models
- [x] [Catalog Search](workflows/catalog_search/) — hybrid retrieval over a ~7,275-row product catalog, large enough to actually populate a vector index

**Enhanced existing content**
- [x] `AI.EVALUATE` — TabFM branch added alongside the TimesFM branch (30 → 36 cells)
- [x] `VECTOR_SEARCH` — 4 hybrid examples, the `STORING` rule, batch/hybrid exclusion (32 → 40 cells)
- [x] `AI.SEARCH` — full `mode` surface (VECTOR/HYBRID/AUTO), status corrected to GA (29 → 36 cells)
- [x] Semantic Search — third "hybrid" approach alongside manual and simplified
- [x] RAG Pipeline — Step 5 hybrid retrieval with a batch-vs-hybrid routing rule
- [x] Log Analysis — hand-authored error codes + AI.EMBED/hybrid retrieval sub-pipeline
- [x] Metric Diagnostics — AI.PREDICT projection step
- [x] Data Enrichment — expanded to 24 rows with a `sector` label; AI.PREDICT classification contrasted against search-grounded AI.GENERATE
- [x] Document RAG — header pointer to ML.PROCESS_DOCUMENT (markdown only; **do not re-run**)
- [x] Forecasting section renamed **Predictive AI** across README/RESOURCES/overview (TimesFM + TabFM)
- [x] `workflows/README.md` created (was missing, and linked from README.md)
- [x] `agent-skills` mirror updated in the same commit: `reference/forecasting-and-anomalies.md` → `reference/predictive-ai.md`, hybrid-search guidance corrected, 3 new narratives, manifest → 0.2.0

**Counts after this phase:** 25 functions, 14 workflows.

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
| `AI.FORECAST` | `bbq.ai.forecast(df, data_col=..., timestamp_col=...)` | No model object needed. Wraps `AI.FORECAST` SQL directly. Supports `id_cols`, `horizon`, `confidence_level`, `context_window`. **Wrapper skew:** still hardcodes `model='TimesFM 2.0'` while the SQL function now defaults to TimesFM 2.5 — pass `model` explicitly. |

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
| `AI.EVALUATE` (TimesFM and TabFM) | No BigFrames API | Use `%%bigquery` magics or raw SQL. (Note: `ARIMAPlus.evaluate()` exists but uses ARIMA_PLUS, not TimesFM.) |
| `AI.PREDICT` (TabFM) | No BigFrames API | Use `%%bigquery` magics or raw SQL via `session.read_gbq_query()`. `bigframes.bigquery.ai` has `forecast` but no `predict`. |
| `VECTOR_SEARCH` hybrid args | Not exposed | `bbq.vector_search()` has no `lexical_search_columns` / `lexical_search_query_value` parameter — hybrid search requires raw SQL. |
| `ML.GENERATE_TEXT` | No direct API | Use `bbq.ai.generate_text()` (wraps `AI.GENERATE_TEXT` instead) or `GeminiTextGenerator` |
| `ML.GENERATE_EMBEDDING` | No direct API | Use `bbq.ai.generate_embedding()` (wraps `AI.GENERATE_EMBEDDING` instead) or `TextEmbeddingGenerator` |

**Key insight for notebooks:** Most functions have BigFrames coverage via `bbq.ai.*`, but 6 functions (AI.EMBED, AI.SIMILARITY, AI.SEARCH, AI.DETECT_ANOMALIES, AI.EVALUATE, AI.PREDICT) need a `session.read_gbq_query()` workaround in the BigFrames section, as do the hybrid-search arguments on `VECTOR_SEARCH` and the `mode` argument on `AI.SEARCH`. This is still valuable to show — it demonstrates that BigFrames can always fall back to raw SQL execution.

**The wrapper lags the SQL surface.** Two independent findings from the 2026-09-01 audit make this a standing expectation, not a one-off: `bbq.ai.forecast` still defaults to a model version the SQL function no longer defaults to, and AI.PREDICT shipped with no wrapper at all. When a function is new or recently changed, verify the BigFrames signature against the installed wheel rather than assuming parity.

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

A function moves from Preview to GA. Mostly status labels — **except where *Tracked open questions — the Preview watch list* below has a row for that function.** GA is when undocumented behavior gets pinned down, defaults stop moving, and restrictions lift, so start there and work the checklist second.

- [ ] **Check *Tracked open questions* below first.** Any row naming this function: re-run the measurement, and follow that row's impact map rather than editing one file
- [ ] `reference/<category>.md`: Update status in the function's entry and in the category comparison table
- [ ] `README.md`: Update status column in the function map table
- [ ] Function notebook `cell-0`: Remove "Preview" mention if present in the description
- [ ] Function `.sql` file: Remove any Preview notes in the header comment
- [ ] Audit log: Record the change
- [ ] If this changes a decision tree, introduces a new cross-cutting gotcha, or adds a new head-to-head comparison with `bq-ml`: update `../../agent-skills/.agents/skills/bigquery-ai-functions/` (SKILL.md and/or the relevant `reference/*.md`)

#### New capability (new parameter, new model version, new supported model, etc.)

An existing function gains new features — e.g., a new parameter, a new supported model version, grounding support, etc.

- [ ] `reference/<category>.md`: Update syntax, inputs, outputs, supported models, and/or comparison table
- [ ] Function notebook: Add or update an example if the capability is significant enough to demonstrate
- [ ] Function `.sql` file: Add an example if appropriate
- [ ] Related function notebooks: Update "Alternatives" sections if relationships changed
- [ ] Workflow notebooks: Check if any workflows should demonstrate the new capability
- [ ] Audit log: Record the change
- [ ] If this changes a decision tree, introduces a new cross-cutting gotcha, or adds a new head-to-head comparison with `bq-ml`: update `../../agent-skills/.agents/skills/bigquery-ai-functions/` (SKILL.md and/or the relevant `reference/*.md`)

#### Removed capability (deprecated model version, removed parameter, etc.)

A function loses a capability — e.g., a model version is retired (like TimesFM 1.0 → 2.0/2.5).

- [ ] `RESOURCES.md`: Remove from syntax, inputs, supported models, and comparison table
- [ ] Function notebook: Update or remove examples that use the deprecated capability
- [ ] Function `.sql` file: Update or remove affected examples
- [ ] Workflow notebooks: Update any workflows that use the deprecated capability
- [ ] Audit log: Record the change
- [ ] If this changes a decision tree, introduces a new cross-cutting gotcha, or adds a new head-to-head comparison with `bq-ml`: update `../../agent-skills/.agents/skills/bigquery-ai-functions/` (SKILL.md and/or the relevant `reference/*.md`)

#### New function

A completely new BigQuery AI function is released.

- [ ] `reference/<category>.md`: Add a full entry in the appropriate category page; update that page's comparison table. If the function needs a whole new category, add the page and a row to the `RESOURCES.md` section index
- [ ] `README.md`: Add to the function map table; update category descriptions if needed
- [ ] Create `functions/{name}/` folder with:
  - `.ipynb` notebook following the template (overview → setup → SQL examples → magics → BigFrames → cleanup)
  - `.sql` file with progressive SQL examples
- [ ] Cross-reference — Alternatives: Add links to/from related function notebooks
- [ ] Cross-reference — Featured in: If used in any workflows, add `**Featured in:**` line; update workflow `**Functions used:**` lines
- [ ] `PLANS.md`: Update the cross-referencing mapping table; add to development phases if tracking
- [ ] Audit log: Record the addition
- [ ] If this changes a decision tree, introduces a new cross-cutting gotcha, or adds a new head-to-head comparison with `bq-ml`: update `../../agent-skills/.agents/skills/bigquery-ai-functions/` (SKILL.md and/or the relevant `reference/*.md`)

#### New workflow

A new end-to-end workflow notebook is added.

- [ ] Create `workflows/{name}/` folder with `.ipynb` notebook
- [ ] `workflows/README.md`: Add to the workflow index table
- [ ] `README.md`: Add to the workflow table in the landing page
- [ ] Cross-reference: Add `**Functions used:**` line to the workflow's overview cell
- [ ] Cross-reference: Add the workflow to the `**Featured in:**` line of each function notebook it uses
- [ ] **Cross-reference round-trip check** — do not eyeball this, run it. For every function named in the workflow's `**Functions used:**` line, confirm that function's notebook names this workflow in its `**Featured in:**` line, and vice versa. `workflows/README.md` promises these links are bidirectional, so a one-way link makes that promise false. A programmatic sweep of all function notebooks against all workflow notebooks in the 2026-09-02 review found five one-way links that had survived several phases precisely because they were only ever checked by hand:

  ```bash
  # from data+ai/bq-ai-functions/ — prints every one-way Functions-used / Featured-in edge
  python3 - <<'PY'
  import json, pathlib, re
  def line(p, tag):
      nb = json.load(open(p))
      for c in nb['cells'][:3]:
          m = re.search(rf'\*\*{tag}:\*\*(.*)', ''.join(c['source']))
          if m: return set(re.findall(r'\]\(([^)]+)\)', m.group(1)))
      return set()
  wf = {p.parent.name: line(p, 'Functions used') for p in pathlib.Path('workflows').glob('*/*.ipynb')}
  fn = {p.parent.name: line(p, 'Featured in') for p in pathlib.Path('functions').glob('*/*.ipynb')}
  for w, funcs in wf.items():
      for f in funcs:
          k = f.rstrip('/').split('/')[-1]
          if k in fn and not any(w == t.rstrip('/').split('/')[-1] for t in fn[k]):
              print(f'one-way: workflows/{w} -> functions/{k} (no back-link)')
  PY
  ```
- [ ] `PLANS.md`: Update the cross-referencing mapping table and the completed workflows list
- [ ] Audit log: Record the addition
- [ ] If this changes a decision tree, introduces a new cross-cutting gotcha, or adds a new head-to-head comparison with `bq-ml`: update `../../agent-skills/.agents/skills/bigquery-ai-functions/` (SKILL.md and/or the relevant `reference/*.md`)

### How to run an audit

Each function's documentation URL is recorded in the table below and mirrored in the matching `reference/*.md`. An audit compares our content against the current official documentation to catch status changes, new parameters, new models, and other updates.

**Step 1 — Prepare.** Review the audit log to see what was last checked and when. **Then read *Tracked open questions — the Preview watch list* below** — every row is a measurement of undocumented behavior, or a capability documented as absent, that a documentation change could invalidate, and each carries the impact map to follow if it has landed.

**Step 1b — Read the release notes since the last audit.** Steps 2 onward compare what is already built against current docs; they cannot surface a function that shipped and was never noticed. Read [BigQuery release notes](https://docs.cloud.google.com/bigquery/docs/release-notes) forward from the last audit date and triage every ML/AI entry into one of four buckets:

| Bucket | Action |
|--------|--------|
| New function | *New function* checklist above, and a row in *Tracked upcoming functions* until built |
| New capability on a covered function | *New capability* checklist above, and a row in *Tracked upcoming enhancements* until built |
| Status change on a covered function | *Status change* checklist above — start at the watch list |
| Belongs to `bq-ml`, not here | Record it in [`bq-ml/PLANS.md`](../bq-ml/PLANS.md)'s *Tracked upcoming* table in the same pass — `ML.*` functions and `CREATE MODEL` are that project's surface, and an entry noticed here and not written down there is lost |

Also watch for entries that **remove or disable** a feature. Preview surface can be pulled mid-Preview: hybrid search went Preview (2026-06-25) → temporarily disabled (2026-07-09) → restored (2026-08-03), and `AI.PARSE_DOCUMENT` went offline and then had its documentation withdrawn. Both need an audit-log row and, for an outage, banners in the affected notebooks.

**Skipping this step is what let six releases go unnoticed between April and September 2026** — the *Tracked upcoming* tables in both projects sat empty the whole time because nothing fed them.

**Step 2 — Fetch and compare by category.** For each function, fetch its documentation URL and compare against the corresponding entry in `reference/*.md`. Work in category batches (Generation, Managed, Embeddings & Search, Forecasting, Document Processing) to spot cross-cutting patterns. For each function, check:
- Status changes (Preview → GA, or new Preview badges)
- New, removed, or changed parameters (name, type, default, range)
- Syntax changes (new overloads, reordered params)
- New or retired model versions / endpoints
- New output columns or changed output types
- New capabilities (grounding, caching, optimized mode, etc.)
- Changed limitations (row limits, page limits, timeouts, region restrictions)
- Changed locations or provisioned throughput behavior
- New best practices or known issues sections
- BigFrames API additions or changes

**Step 3 — Classify each change.** Map each difference to a change type (status change, new capability, removed capability, new function) and apply the relevant checklist from the "Change types and checklists" section above.

**Step 4 — Update files in order.**
1. `reference/*.md` — All function entry updates (work top-to-bottom through each category page)
2. `reference/*.md` — Comparison tables at the top of each page (must match per-function entries)
3. `README.md` — Function map tables (status, multimodal, descriptions) and relationship diagram
4. `PLANS.md` — Documentation URLs table (add new functions), cross-referencing mapping table, audit log

**Step 5 — Check for new functions.** Search for newly announced BigQuery AI functions (blog posts, release notes, docs index pages). For each:
- If reference docs exist: add a full `reference/<category>.md` entry + `README.md` row using the "New function" checklist
- If only announced (no reference docs): add to the "Tracked upcoming functions" table below with status and source link

**Step 6 — Verify consistency.**
- Grep for status labels (Preview/GA) and confirm they match across `RESOURCES.md`, `README.md`, and `PLANS.md`
- Cross-check comparison tables in `RESOURCES.md` against per-function entries
- Verify the documentation URLs table below is complete
- Record the audit in the audit log

**Step 7 — Identify notebook impacts.** List notebooks that need updates based on the changes found. Notebook updates require a fresh "Restart & Run All" pass before review.

**Documentation URLs:**

> Google migrated these docs from `cloud.google.com` to `docs.cloud.google.com`. The old host 301-redirects, but tools that do not follow cross-host redirects (including `WebFetch`) silently return navigation chrome instead of the page. Use the `docs.` host, and prefer `curl -sL` plus extraction of the `devsite-article-body` div over a fetch tool.

| Function | Documentation URL |
|----------|-------------------|
| AI.GENERATE | https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-generate |
| AI.GENERATE_TEXT | https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-generate-text |
| AI.GENERATE_TABLE | https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-generate-table |
| AI.GENERATE_BOOL | https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-generate-bool |
| AI.GENERATE_DOUBLE | https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-generate-double |
| AI.GENERATE_INT | https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-generate-int |
| ML.GENERATE_TEXT | https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-generate-text |
| AI.IF | https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-if |
| AI.SCORE | https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-score |
| AI.CLASSIFY | https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-classify |
| AI.AGG | https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-agg |
| AI.EMBED | https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-embed |
| AI.GENERATE_EMBEDDING | https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-generate-embedding |
| ML.GENERATE_EMBEDDING | https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-generate-embedding |
| AI.SIMILARITY | https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-similarity |
| VECTOR_SEARCH | https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/search_functions#vector_search |
| AI.SEARCH | https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-search |
| AI.FORECAST | https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-forecast |
| AI.DETECT_ANOMALIES | https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-detect-anomalies |
| AI.PREDICT | https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-predict |
| AI.EVALUATE | https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-evaluate |
| ML.PROCESS_DOCUMENT | https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-process-document |
| AI.PARSE_DOCUMENT | ⚠️ **404 — withdrawn.** Was: https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-parse-document |
| AI.KEY_DRIVERS | https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-key-drivers |
| AI.COUNT_TOKENS | https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-count-tokens |

### Tracked upcoming functions

Functions announced but without published reference documentation. Check periodically and move to full coverage when docs publish.

| Function | Category | Status | Announced | Source | Expected Doc URL |
|----------|----------|--------|-----------|--------|-----------------|
| *(none currently tracked)* | — | — | — | — | — |

**Resolved 2026-09-01 — HYBRID_SEARCH does not exist.** It was tracked here from the Cloud Next 2026 announcement, but BigQuery shipped hybrid search as a *capability* of the two existing search functions, not as a new function: `VECTOR_SEARCH`'s `lexical_search_columns` argument and `AI.SEARCH`'s `mode => 'HYBRID'`. There is no `HYBRID_SEARCH` in the SQL surface and no reference page for one. Treated as "new capability ×2", not "new function". See [Hybrid Search](reference/embedding-generation-and-semantic-search.md#hybrid-search-capability).

### Tracked upcoming enhancements

Capabilities observed in training labs or announcements but not yet in published reference docs. When docs publish, add examples to notebooks and move to audit log.

| Function | Enhancement | Status | Source | Notes |
|----------|------------|--------|--------|-------|
| AI.PARSE_DOCUMENT | Gemini model endpoint (`endpoint => 'gemini-2.5-flash'`) | Blocked — the whole function is offline and its docs are withdrawn | [L400 Lab 1](../../../ds-l400/lab-1/teacher/lab_1_parse_2_extraction.ipynb) | Currently only Layout Parser processor endpoints are documented. Gemini endpoints would eliminate the Document AI processor setup entirely — just `endpoint => 'model-name'` with a connection. When available: add Example 7 to notebook, update RESOURCES.md endpoint description, update README.md ("No" for Requires Model). |
| All generative functions | `gemini-3.1-flash-lite` and `gemini-3.5-flash` | **GA 2026-08-10 — documented in [RESOURCES.md](RESOURCES.md#choosing-a-gemini-model-endpoint) as of 2026-09-02.** No notebook change needed | [Release notes](https://docs.cloud.google.com/bigquery/docs/release-notes) | **The default did not move** — omitting `endpoint` still gives `gemini-2.5-flash`, so every stored output in this project remains valid and no re-execution is required. The 3.x family is multi-regional-endpoint only, and `europe-west2`/`europe-west6` silently resolve to the **global** endpoint. **Re-check the default on every audit** — a default change *would* invalidate every generative notebook's stored output at once. |
| AI functions taking multimodal input | Accepting an `ObjectRef` column directly, without wrapping it in `OBJ.GET_ACCESS_URL` | **Announced GA 2026-06-12; reference docs contradict the announcement.** Measurable — not yet measured | [Release notes](https://docs.cloud.google.com/bigquery/docs/release-notes) · [ObjectRef functions](https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/objectref_functions) | The generative AI overview and the `AI.GENERATE_*` pages still say `OBJ.GET_ACCESS_URL` is required; `AI.SCORE`'s prompt spec accepts "an `ObjectRef` column" and `AI.IF`'s example passes `images.ref` bare. **This project can settle it by running it** — try the unwrapped form on one generative and one managed function against an existing object table. Until measured, every notebook keeps `OBJ.GET_ACCESS_URL(col, 'r')`. Recorded in [Unstructured Data Infrastructure](reference/unstructured-data-infrastructure.md). |
| ObjectRef utilities | `OBJ.GET_READ_URL` | **GA 2026-03-31 per release notes; absent from the ObjectRef functions reference page.** Documented here as observed-not-documented | [Release notes](https://docs.cloud.google.com/bigquery/docs/release-notes) | Appears only in a tutorial snippet, returning a signed URL for display while the AI function is still fed `OBJ.GET_ACCESS_URL`. Add a worked example when the reference page lists it. |

### Tracked open questions — the Preview watch list

Behavior this project has measured but that documentation does not cover or explain. **Unlike the two tables above, none of these is waiting on an announcement** — each is waiting on a documentation page or a behavior change that Preview surface area makes likely.

Re-check this list **every audit** and **on any Preview → GA transition**. GA is exactly when undocumented behavior gets pinned down, defaults stop moving, and restrictions lift — so a status change is a trigger to re-run every measurement below, not just to swap a status label. The generic checklist is *Status change (Preview → GA)* above; the rows here are what that checklist does not cover.

**Preview surface this depends on:** `AI.PREDICT` (Preview), `AI.EVALUATE`'s tabular branch (Preview), `VECTOR_SEARCH`'s single-search/hybrid syntax (Preview, on a GA function), `AI.SEARCH`'s `mode` argument (Preview, on a GA function). Two impact maps follow the tables — use them instead of hand-patching one file.

#### Predictive AI — TabFM and TimesFM (as of 2026-09-02)

| # | Open question | Our published position today | What would settle it | What we update when it does |
|---|---|---|---|---|
| P1 | **`AI.PREDICT` is not deterministic.** Identical calls return different predictions (regression MAE 235.8–236.5; classification accuracy 0.9468 / 0.9362 / 0.9468). A `FARM_FINGERPRINT` split does not change it, so it is in the inference, not the data | Published as measured non-determinism, cause unknown — "materialize results instead of re-running them" | Documentation of the behavior, a documented `n_ensembles`-style knob, or the behavior becoming stable | Predictive impact map. If it becomes deterministic, the "materialize results" advice and every reproducibility caveat come out |
| P2 | **`AI.EVALUATE` cannot score predictions you already have.** It generates its own, so re-running it on the same inputs gives different metrics each time | Published as a limitation with the workaround of materializing once | An argument that accepts a prediction table | `functions/ai_evaluate/`, `workflows/tabular_prediction/`, skill `reference/predictive-ai.md` |
| P3 | **Explainability** — feature attribution for an `AI.PREDICT` result (an `AI.KEY_DRIVERS`-style "which features moved this prediction") | Documented as absent; docs point to trained models | The capability shipping | New example in `functions/ai_predict/`, `RESOURCES.md`, and the `bigquery-ml` head-to-head in `choosing-a-bigquery-ai-approach` |
| P4 | **Training-relation ceiling.** 8,000 rows succeed, 10,000 fail, on a two-feature relation whose prediction side is 2 rows. Error is `resourcesExceeded` (peak 124% of limit, 91% `other/unattributed`), not a documented cap. Captured with the exact error text, a minimal repro and the job ladder | Published as a measured memory failure with the exact ladder — explicitly **not** a documented cap, and explicitly all on-demand with no reservation | A documented limit, or a successful run under an Enterprise reservation | Predictive impact map. **If a reservation turns out to be the fix, that is new setup guidance** — `setup/README.md` and the notebook Setup cells, not just a note |
| P5 | **No model-version argument on `AI.PREDICT`.** `AI.FORECAST` takes `model => 'TimesFM 2.5'`; `AI.PREDICT` has no equivalent, so results shift for everyone when the TabFM default advances | Published as "TabFM has no version to pin" | A `model` argument shipping | Predictive impact map, plus the SKILL.md cross-cutting gotcha that currently says so |
| P6 | **`AI.EVALUATE` and `AI.DETECT_ANOMALIES` are not reproducible run to run, and pinning `model` does not fix it.** With `model` **and** `context_window` both pinned, query cache off, on a deterministic synthetic series, 2 of 16 `AI.EVALUATE` runs returned `0.5913808905590097` where the other 14 returned `0.8652198481135486` — a ~32% swing in the headline metric at roughly 1 in 8. The majority value is the correct one: MAE hand-computed from `AI.FORECAST` output over the same history and horizon equals it to the last digit (3/3). `AI.DETECT_ANOMALIES` shows the same shape (1 of 8 runs off-value); `AI.FORECAST` is stable (12/12). Ruled out: context window (every legal value swept), horizon truncation (all 31 prefixes), and version mixing — it happens on 2.0 and 2.5 alike. **Mechanism unidentified, and no cause is published** | Published as measured nondeterminism with a repro, alongside the standing advice that pinning `model` protects against version drift but **not** against this | Documentation of the behavior, or the behavior becoming stable | `functions/ai_evaluate/`, `functions/ai_detect_anomalies/`, `workflows/time_series_intelligence/`, `RESOURCES.md`, skill `reference/predictive-ai.md` |
| P7 | **TimesFM 3, and covariate support** — both known-at-forecast-time and unknown. Today `ARIMA_PLUS_XREG` is the only covariate route, which costs the zero-training path | Documented as a gap, with the `ARIMA_PLUS_XREG` alternative | An announcement or release note | Predictive impact map, plus `choosing-a-bigquery-ai-approach` (the `AI.FORECAST` vs `ARIMA_PLUS` triage changes materially) |
| P8 | **BigFrames wrapper for `AI.PREDICT`** | Documented as absent; BigFrames coverage audit in *Resolved Questions* above tracks the general lag | The wrapper shipping | BigFrames sections of `functions/ai_predict/` and `workflows/tabular_prediction/`, plus the BigFrames coverage audit table above |

#### Hybrid search — `VECTOR_SEARCH` and `AI.SEARCH` (as of 2026-09-02)

| # | What we raised | Our published position today | What would settle it | What we update when it does |
|---|---|---|---|---|
| V1 | **The fusion formula, and why the lexical leg starts one rank higher.** `distance = 1 - ( 1/(60 + rank_vector) + 1/(61 + rank_lexical) )`, exact to 15–16 digits. Only `rank_vector` is observable, so the arithmetic pins *denominators*, not constants: `1/(61 + r)` = `1/(60 + (r + 1))`, making "k = 61 lexical" and "k = 60 with lexical ranks starting at 2" indistinguishable from outside | Reading B (offset) published as **likelier, not settled** — 60 is the canonical RRF constant and the default in Elasticsearch, OpenSearch, Azure AI Search, Spanner and AlloyDB; 61 is the constant in no published implementation. *Why* the offset exists is separately open: a **tie-break** (at equal ranks `1/(60 + r)` beats `1/(61 + r)`, so the semantic leg wins every tie), a **reserved slot** at lexical position 1, or an **off-by-one** all fit. Only the last is a defect and it is the least charitable — **never published as the explanation** | Documentation of the fusion algorithm | Hybrid impact map. If it turns out to be a defect and gets fixed, **every worked example and every stored notebook output changes** — this is a re-execution, not an edit |
| V2 | **The fusion is undocumented.** AlloyDB and Spanner publish theirs with the 60 in it; BigQuery's only public statement is a blog post naming "Reciprocal Rank Fusion and BM25", with no formula and no constants. Nor is it documented that a perfect match returns ~0.9675 rather than 0, which is what a cosine-tuned threshold assumes | Published with a standing "reverse-engineered, not documented — consume the ordering, never the number" warning in every location | A reference page stating the algorithm | Hybrid impact map. **Every "reverse-engineered, not documented" disclaimer becomes a citation** — that is the single largest edit in the map |
| V3 | **Is the `10 * top_k` lexical candidate-pool multiplier adjustable?** Only `fraction_lists_to_search` and `use_brute_force` are documented `options` keys | Published as measured across four corpora with three correct out-of-sample predictions; described as undocumented | A new `options` key, or documentation of the pool | Hybrid impact map — **every reach table and every `top_k` sizing rule is derived from this number** |
| V4 | **Batch hybrid.** `lexical_search_query_value` is required alongside `lexical_search_columns`, so a `query_table` call cannot be hybrid (`lexical_search_columns is not supported when query_value is not specified.`) | Published as a hard limitation | The restriction lifting | `RESOURCES.md` limitations, `functions/vector_search/` (notebook + `.sql`), `workflows/catalog_search/`, skill `reference/embeddings-and-search.md`. **A new batch example is warranted, not just a note** |
| V5 | **`AI.SEARCH` `mode => 'AUTO'` is always semantic-only on an autonomous-embedding table**, because the generated embedding column is a `STRUCT<result, status>` and a vector index key must be `ARRAY<FLOAT64>` | Published with the two-table workaround (project `.result` into a plain `ARRAY<FLOAT64>` and index that), which `workflows/catalog_search/` builds end to end | Vector indexes supporting the generated column, or `AUTO` gaining another route to hybrid | `functions/ai_search/` (notebook + `.sql`), `reference/embedding-generation-and-semantic-search.md`, SKILL.md cross-cutting gotchas. **If it is fixed, the two-table design in `catalog_search` stops being necessary** and the workflow's premise needs revisiting |

#### Impact map — hybrid search fusion behavior

Applies to V1–V3 (and partly V4–V5). The fusion algorithm, its constants, and the pool multiplier are **undocumented and Preview**. Every number is measured-today, not contracted. If any of them changes, **every entry below carries it** — regenerate the reach table and re-verify every worked example rather than patching one file:

*Hand-authored, `data+ai/bq-ai-functions/` (9 entries, 11 files):*
`README.md` · `reference/embedding-generation-and-semantic-search.md` (Hybrid Search section) · `overview.ipynb` · `functions/vector_search/vector_search.ipynb` + `.sql` · `functions/ai_search/ai_search.ipynb` + `.sql` · `workflows/semantic_search/semantic_search.ipynb` · `workflows/rag_pipeline/rag_pipeline.ipynb` · `workflows/log_analysis/log_analysis.ipynb` · `workflows/catalog_search/catalog_search.ipynb`

Also check `workflows/README.md`, which describes hybrid without carrying the arithmetic.

*Hand-authored, `agent-skills/.agents/skills/bigquery-ai-functions/` (3):*
`SKILL.md` · `reference/embeddings-and-search.md` · `reference/workflows.md`

*Tool-generated — regenerate, never hand-edit (7):*
`narrative/vector_search.md` · `narrative/ai_search.md` · `narrative/semantic_search.md` · `narrative/rag_pipeline.md` · `narrative/log_analysis.md` · `narrative/catalog_search.md` · `skill.manifest.json`

Two notebooks additionally **compute** the decomposition in code, so their stored output changes and they need re-execution rather than a text edit: `workflows/rag_pipeline/rag_pipeline.ipynb` (cell 27, prints the reading-A/B equivalence) and `workflows/catalog_search/catalog_search.ipynb` (cell 34, `K_VECTOR` / `K_LEXICAL`).

#### Impact map — predictive AI (TabFM / TimesFM) behavior

Applies to P1, P4, P5, P7. TabFM and TimesFM are foundation models with **moving defaults**, reached through Preview functions. If determinism, a version argument, a size limit, or a model generation changes, these carry it:

*Hand-authored, `data+ai/bq-ai-functions/` (13 entries):*
`README.md` · `RESOURCES.md` · `overview.ipynb` · `setup/README.md` (only if a reservation turns out to be the answer) · `functions/ai_predict/` (notebook + `.sql`) · `functions/ai_evaluate/` (notebook + `.sql`) · `functions/ai_forecast/` (notebook + `.sql`) · `functions/ai_detect_anomalies/` (notebook + `.sql`) · `workflows/tabular_prediction/` · `workflows/time_series_intelligence/` · `workflows/metric_diagnostics/` · `workflows/data_enrichment/` · `workflows/README.md`

*Hand-authored skills (4, across all three skills):*
`bigquery-ai-functions/SKILL.md` · `bigquery-ai-functions/reference/predictive-ai.md` · `bigquery-ai-functions/reference/workflows.md` · `choosing-a-bigquery-ai-approach/SKILL.md` (carries the `AI.FORECAST` vs `ARIMA_PLUS` and `AI.PREDICT` vs `BOOSTED_TREE_*` head-to-heads) — and `bigquery-ml/SKILL.md` + `reference/unsupervised-and-specialized.md` if the comparison shifts

*Tool-generated — regenerate, never hand-edit (8):*
`narrative/ai_predict.md` · `narrative/ai_evaluate.md` · `narrative/ai_forecast.md` · `narrative/ai_detect_anomalies.md` · `narrative/tabular_prediction.md` · `narrative/time_series_intelligence.md` · `narrative/metric_diagnostics.md` · `narrative/data_enrichment.md`

#### Regeneration and sweep commands

```bash
# Regenerate any tool-generated narrative, then the manifest, then validate
cd agent-skills/tooling
uv run agent-skills convert-notebook <notebook.ipynb> --subproject-root <subproject-root> --output <narrative>.md
uv run agent-skills manifest ../.agents/skills/bigquery-ai-functions
uv run agent-skills validate ../.agents/skills --all
```

```bash
# Confirm no location was missed — hybrid fusion
grep -rl "61 + rank_lexical\|10 \* top_k\|0.9674775251189847\|[Rr]eciprocal [Rr]ank [Ff]usion" \
  --include=*.ipynb --include=*.md --include=*.sql data+ai/bq-ai-functions agent-skills

# Confirm no location was missed — predictive AI
grep -rl "AI\.PREDICT\|AI\.EVALUATE\|TimesFM\|TabFM" \
  --include=*.ipynb --include=*.md --include=*.sql data+ai/bq-ai-functions agent-skills
```

**The sweeps return more than the maps list, and that is expected.** They match any mention of the terms, including passing references that carry no claim — as of 2026-09-02 the hybrid sweep returns 21 files and the predictive sweep 34. The two sets never match the maps exactly: the sweeps also hit this file, and they miss `skill.manifest.json`, which carries the claim in generated metadata without containing any of the search terms — regenerate it regardless. Treat the extra hits as a checklist: for each one, confirm it only *names* the function rather than asserting behavior. Anything asserting behavior belongs on the map — add it.

### Audit log

| Date | Scope | Changes Found |
|------|-------|---------------|
| 2026-03-13 | Initial build | All 19 functions documented, tested, and cross-referenced |
| 2026-03-13 | AI.EVALUATE, AI.FORECAST, AI.DETECT_ANOMALIES | TimesFM 1.0 retired — valid models are now TimesFM 2.0 and TimesFM 2.5. Updated time_series_intelligence workflow. |
| 2026-03-16 | Multimodal/ObjectRef documentation | Updated README.md: renamed ObjectRef column to Multimodal with per-function input method labels, added Multimodal Input section with pattern legend. Updated RESOURCES.md: added Multimodal Input Patterns section with 4 patterns (STRUCT prompt, tuple+object table, EXTERNAL_OBJECT_TRANSFORM, ObjectRef content), SQL examples, and summary table. Updated compatible functions lists. |
| 2026-03-16 | Phase 8 expansion | Added multimodal embedding examples to AI.EMBED, AI.GENERATE_EMBEDDING, AI.SIMILARITY notebooks + SQL files (multimodalembedding@001). Added multimodal note to ML.GENERATE_EMBEDDING. Created Content Moderation workflow (AI.GENERATE_TABLE → AI.IF → AI.CLASSIFY → AI.SCORE → AI.GENERATE). Created Multimodal Analysis workflow (document rendering → AI.EMBED → ML.DISTANCE → AI.SIMILARITY → AI.GENERATE). Updated all cross-references (7 function notebook Featured in lines, README.md workflows table, PLANS.md mapping table). |
| 2026-03-16 | Docs review post-implementation | README.md: Fixed AI.SCORE and AI.CLASSIFY multimodal labels from "Object table" to "STRUCT prompt" (both accept STRUCT with ObjectRefRuntime). RESOURCES.md: Added multimodal best practices to AI.EMBED (default 1408 dims, PDF not supported, inline ObjectRef preferred), AI.GENERATE_EMBEDDING (statistics not returned by multimodal model, inline ObjectRef avoids reservation requirement), AI.SIMILARITY (cross-modal text↔image capability). Updated Managed Functions table. Added "Object tables vs inline ObjectRef" guidance to Unstructured Data Infrastructure section. |
| 2026-04-07 | AI.AGG — new function + workflow | Added AI.AGG (Preview aggregate function with auto-batching). Created functions/ai_agg/ with notebook + SQL. Added to RESOURCES.md Managed Functions section with comparison table. Added to README.md function map, relationship diagram, and key distinctions. Added AI.AGG alternative cells to Content Analysis, Content Moderation, and Document Intelligence workflows. Created new Log Analysis workflow (AI.GENERATE_TABLE → AI.CLASSIFY → AI.SCORE → AI.AGG). Updated all cross-references. |
| 2026-05-22 | AI.AGG re-enablement | AI.AGG (Preview) re-enabled after temporary disable (April 13, 2026). Removed warning banners from 5 notebooks (ai_agg, content_analysis, content_moderation, document_intelligence, log_analysis). Expanded ai_agg.ipynb with 4 new examples: connection_id parameter, quantitative aggregation, AI.AGG vs STRING_AGG+AI.GENERATE comparison, multimodal ObjectRef. Added connection setup and GCS support to ai_agg notebook. |
| 2026-05-23 | AI.PARSE_DOCUMENT — new function | Created functions/ai_parse_document/ with notebook (37 cells, 6 SQL examples) and SQL file. AI.PARSE_DOCUMENT (Preview) uses Document AI Layout Parser for OCR + layout parsing + chunking — no CREATE MODEL step needed (endpoint points directly to processor). Updated RESOURCES.md with full documentation (syntax, inputs/outputs, supported file types, best practices, limitations). Updated README.md function table, relationship diagram, and project tree. Moved from tracked upcoming functions to documented. Gemini model endpoints (`endpoint => 'gemini-2.5-flash'`) observed in L400 training lab but not yet in public docs — tracked in upcoming enhancements for future notebook expansion. |
| 2026-05-23 | Document RAG — new workflow | Created workflows/document_rag/ with notebook (31 cells). End-to-end document RAG pipeline: AI.PARSE_DOCUMENT (parse 20 invoices into chunks) → AI.EMBED (embed chunks with text-embedding-005) → VECTOR_SEARCH (retrieve relevant chunks) → AI.GENERATE (answer questions with grounded context). Includes batch RAG (3 questions) and RAG vs direct generation comparison. Updated cross-references: added Featured in to ai_parse_document, ai_embed, vector_search, ai_generate notebooks. Updated README.md workflows table and project tree. Updated PLANS.md completed workflows table and mapping. |
| 2026-05-10 | Full audit — all functions | **Managed functions:** AI.IF and AI.CLASSIFY gained `examples`, `embeddings` (Preview), `optimization_mode` (Preview) params for optimized mode (230x cost reduction). AI.IF, AI.SCORE, AI.CLASSIFY gained `max_error_ratio`. AI.AGG added known issues section. **Embeddings:** AI.EMBED and AI.SIMILARITY gained `model` param (`embeddinggemma-300m` built-in). Four new embedding models across AI.EMBED/AI.SIMILARITY/AI.GENERATE_EMBEDDING/ML.GENERATE_EMBEDDING: `embeddinggemma-300m`, `gemini-embedding-001`, `text-multilingual-embedding-002`, `gemini-embedding-2-preview` (multimodal incl. PDFs). **Forecasting:** AI.FORECAST gained `forecast_end_timestamp`. AI.DETECT_ANOMALIES: Preview → GA, gained `context_window`. AI.EVALUATE gained `context_window` and `mean_absolute_scaled_error` output. **Generation:** AI.GENERATE: `thinking_level` for Gemini 3.0+, grounding requires 2.0+. AI.GENERATE_TEXT: `USE_CHAT_MODE` for Open models. **Document Processing:** ML.PROCESS_DOCUMENT max pages 100→130, added 120s timeout and batch size of 10. **New functions tracked:** AI.PARSE_DOCUMENT (Preview, docs pending), HYBRID_SEARCH (Preview, docs pending). Expanded audit procedure in PLANS.md. |
| 2026-06-19 | AI.KEY_DRIVERS — new function | Created functions/ai_key_drivers/ with notebook (36 cells, 7 SQL examples) and SQL file. AI.KEY_DRIVERS (Preview) is an augmented analytics TVF for key driver / contribution analysis — finds the segments driving a metric change between an interest and reference set. No CREATE MODEL, no connection, no endpoint (structured tables only; no ObjectRef). Added new "Augmented Analytics" section to RESOURCES.md with full documentation (syntax, inputs/outputs, best practices, limitations, and a comparison to contribution analysis models + ML.GET_INSIGHTS). Added README.md function-map subsection, relationship diagram box, and project tree entry. Examples use the public NYC Citi Bike dataset (April 2017 interest vs April 2016 reference; metric SUM(tripduration); dimensions usertype/gender/start_station_name). |
| 2026-06-19 | Metric Diagnostics — new workflow + TSI integration | Created workflows/metric_diagnostics/ with notebook (25 cells): build interest/reference dataset → confirm headline shift with SQL → AI.KEY_DRIVERS surfaces drivers → AI.GENERATE narrates an executive summary. Integrated AI.KEY_DRIVERS into time_series_intelligence as Step 5 (companion segmented region × product_line table with an injected H2 surge; explains which segments drove the H1→H2 change). Updated cross-references: Featured in lines (ai_key_drivers → both workflows; ai_generate → Metric Diagnostics), README.md workflows table + project tree, PLANS.md completed workflows + mapping table. |
| 2026-07-16 | AI.COUNT_TOKENS — new function | Created functions/ai_count_tokens/ with notebook (26 cells, 5 SQL examples) and SQL file. AI.COUNT_TOKENS (Preview) is a utility scalar function that estimates a prompt's INPUT token count inside BigQuery with no Vertex AI charge — used to size/cost prompts before calling the paid generation functions. No connection, model, or ObjectRef; signature AI.COUNT_TOKENS(INPUT [, endpoint => ...]) returns STRUCT<result INT64, full_response JSON> (input tokens only — not thinking/output). Added full RESOURCES.md entry in General Purpose Functions + section-intro note (kept out of the 7-column generation comparison table as it's a utility, not a generator). Added README.md function-map row, relationship-diagram note, and project tree entry. Added a short cell to overview.ipynb. Examples use bigquery-public-data.imdb.reviews. No native BigFrames wrapper — read_gbq_query fallback documented. All SQL pre-validated against BigQuery. |
| 2026-07-17 | AI.PARSE_DOCUMENT — offline for revision | Google took AI.PARSE_DOCUMENT (Preview) **offline for revision as of 2026-06-01**; it does not currently execute. Applied the AI.AGG-disable playbook: added `⚠️ NOT CURRENTLY WORKING` banners to the overview cells of functions/ai_parse_document/ai_parse_document.ipynb and workflows/document_rag/document_rag.ipynb (the whole Document RAG workflow is blocked — its Step 1 uses the function). Added a status note to the RESOURCES.md AI.PARSE_DOCUMENT entry and ⚠️ markers to the README.md function-map row and Document RAG workflow row. Existing documentation/examples retained as-is for when it returns. **Reversal when re-enabled:** remove the two notebook banners, clear the RESOURCES/README status markers, Restart & Run All both notebooks, verify, and log a re-enablement entry (precedent: AI.AGG disable 2026-04-13 → re-enable 2026-05-22). Banners are markdown-only, so no re-run was needed to apply them. |
| 2026-09-01 | AI.PREDICT — new function | Created `functions/ai_predict/` with notebook and SQL file. AI.PREDICT (Preview) runs zero-shot regression **or** classification on tabular rows using **TabFM**, a pre-trained tabular foundation model that learns in-context from a training relation at query time — no `CREATE MODEL`, no connection, no endpoint, no persisted model object. Examples use `bigquery-public-data.ml_datasets.penguins` (regression on `body_mass_g`, classification on `sex`). Renamed the Forecasting section to **Predictive AI** across README.md, RESOURCES.md, and the agent skill (`reference/forecasting-and-anomalies.md` → `reference/predictive-ai.md`) so it covers both foundation models — TimesFM for time series and TabFM for tabular rows. Verified limits: task type is inferred from the label column's **type** (an `INT64`-coded categorical silently becomes a regression); OOM at 10,000 training rows, works at 8,000; hard caps of 20 feature columns and 10 classes; `DATE`/`TIMESTAMP`/`BYTES`/`JSON`/`GEOGRAPHY`/`ARRAY`/`STRUCT` all rejected; 30–95s latency per call; token-based pricing formula effective 2026-10-30; no BigFrames wrapper. Documentation bug found: the reference page says passthrough columns come from the training table, but observed behavior returns the prediction rows. |
| 2026-09-01 | AI.EVALUATE — second (tabular) branch | AI.EVALUATE now has **two mutually exclusive branches**. The existing forecast branch scores a TimesFM forecast against actuals; the new tabular branch takes AI.PREDICT's two relations plus `label_col` and scores TabFM accuracy on held-out rows. Mixing forecast-shaped and tabular-shaped arguments in one call errors. Expanded `functions/ai_evaluate/` to cover both. Branch asymmetries documented: only the TimesFM branch returns `ai_evaluate_status` — the tabular branch has no per-row status column — and the tabular branch returns **no `log_loss`, no `roc_auc`, and no confusion matrix** for classification (use BigQuery ML's `ML.EVALUATE` on a trained classifier if you need those). |
| 2026-09-01 | AI.FORECAST — default model version flipped 2.0 → 2.5 | **The default `model` for the TimesFM functions is now TimesFM 2.5, not 2.0, and this changed without a release note.** Confirmed empirically with a three-way live comparison of the same AI.FORECAST query against `bigquery-public-data.new_york_citibike.citibike_trips`: unpinned and `'TimesFM 2.5'` agree to the last digit, while `'TimesFM 2.0'` differs (24125.2324 vs 24596.082 on the first forecast point). **Consequence:** every unpinned forecast query in this repo now returns different numbers than its committed output — `ai_forecast`, `ai_detect_anomalies`, `ai_evaluate`, and `time_series_intelligence` will all shift on their next Restart & Run All even with no code change. Also found a **wrapper skew**: `bigframes.bigquery.ai.forecast()` still hardcodes `model="TimesFM 2.0"`, so the same logical call returns different answers from Python than from SQL. Standing rule added: pin `model` explicitly in examples, and verify a BigFrames wrapper's defaults rather than assuming SQL parity. |
| 2026-09-01 | Hybrid search — resolved as a capability, not a function | **HYBRID_SEARCH does not exist and never shipped.** It had been tracked here since the Cloud Next 2026 announcement as an upcoming function with docs pending; BigQuery instead delivered hybrid retrieval as parameters on the two existing search TVFs — `VECTOR_SEARCH`'s `lexical_search_columns` / `lexical_search_query_value`, and `AI.SEARCH`'s `mode => 'VECTOR'\|'HYBRID'\|'AUTO'`. Removed from tracked-upcoming; reclassified as "new capability ×2". Enhanced `functions/vector_search/` and `functions/ai_search/` with hybrid examples and added a Hybrid Search section to RESOURCES.md. Verified findings: both routes are **single-query only** (batch `query_table` + `lexical_search_columns` fails with `lexical_search_columns is not supported when query_value is not specified.`); neither requires a vector index; the returned `distance` is **not a distance** but a reciprocal-rank-fusion score with **1-based ranks and a different rank base per leg** — `distance = 1 - ( 1/(60 + rank_vector) + 1/(61 + rank_lexical) )`, so a row ranked 1 by both legs scores `1 - (1/61 + 1/62)` = `0.9674775251189847`, not 0, and cosine-tuned thresholds must never be reused; every column in `lexical_search_columns` must also appear in `STORING(...)` and may not be the index key; and an AI.SEARCH base table can **never** have a hybrid vector index, because autonomous embedding generation produces a `STRUCT<result, status>` column while a vector index key must be `ARRAY<FLOAT64>` — which means `mode => 'AUTO'` silently resolves to semantic-only there, so name `'HYBRID'` explicitly. |
| 2026-09-01 | Catalog Search + Zero-Shot Tabular Prediction — new workflows | Created `workflows/catalog_search/`: hybrid retrieval over the full `bigquery-public-data.thelook_ecommerce.products` catalog (~7,275 rows) — the exact-token SKU lookups pure semantics misses, plus a corpus large enough to actually populate a vector index (index population is asynchronous and does not begin until the table exceeds ~10 MB, so small demo tables silently fall back to brute force). Demonstrates both the autonomous-embedding AI.SEARCH route and the indexed VECTOR_SEARCH route, which require two separate tables for the STRUCT-vs-ARRAY reason above. Created `workflows/tabular_prediction/`: the full TabFM tour — AI.PREDICT regression and classification on penguins, AI.EVALUATE scoring, AI.KEY_DRIVERS for explanation, AI.GENERATE for a model card — including a head-to-head against trained BigQuery ML models from `../../bq-ml/` (indicative only: the BQML side uses AUTO_SPLIT, not the notebook's FARM_FINGERPRINT 70/30 split). Counts after this phase: **25 functions, 14 workflows.** Created the previously-missing `workflows/README.md` (required by the new-workflow checklist and linked from README.md). |
| 2026-09-01 | Enhanced existing workflows | `log_analysis` — full rebuild: hand-authored error codes into the 30 seed STRUCTs and added an AI.EMBED + hybrid-retrieval sub-pipeline as Step 5, making it the clearest case where an exact token beats semantics outright. `data_enrichment` — expanded to ~24 rows with a new low-cardinality `sector` column containing genuine NULLs, so the workflow now contrasts Google Search grounding against AI.PREDICT zero-shot classification for the same gap (~4x the per-run Gemini cost, accepted). `metric_diagnostics` — added an AI.PREDICT projection alongside the AI.KEY_DRIVERS explanation. `semantic_search` and `rag_pipeline` — added hybrid alongside the existing semantic-only approaches. Updated all reciprocal `**Featured in:**` links in `ai_embed`, `ai_generate`, `ai_key_drivers`, and `vector_search`. |
| 2026-09-01 | AI.PARSE_DOCUMENT — escalated to documentation withdrawn | The 2026-07-17 outage has escalated: the reference page now returns **HTTP 404**, and the function is absent from both the docs navigation and the BigQuery AI functions overview page. (A web-search result claiming it was not deprecated was checked directly against the live URL and is wrong.) Escalated the `⚠️ NOT CURRENTLY WORKING` banners in `functions/ai_parse_document/ai_parse_document.ipynb` and its `.sql` header to `⚠️ NOT CURRENTLY WORKING — DOCUMENTATION WITHDRAWN`, and annotated the dead doc links in RESOURCES.md and the SQL file as `404 as of 2026-09-01` rather than deleting them, so the page can be re-checked if the function returns. Per Mike's decision, `workflows/document_rag/` gets a **header pointer to ML.PROCESS_DOCUMENT** as the interim alternative (with an honest note on the differences) — **not** a rebuild. **Neither notebook may be re-run**: their committed outputs are the only surviving record of the function working, and a Restart & Run All would fail at the parse step and destroy that evidence. **Reversal when re-enabled:** extends the 2026-07-17 instructions — first re-verify the doc URL returns 200, then remove the withdrawn-docs banners and the ML.PROCESS_DOCUMENT pointer, clear the RESOURCES/README markers, restore the dead-link annotations, Restart & Run All both notebooks, and log a re-enablement entry. |
| 2026-09-02 | Post-execution review — hybrid-search narrative corrected, three doc-vs-behavior mismatches fixed | Four findings, all verified against live queries rather than inferred. **(1) The sub-project's loudest Phase 10 claim was wrong.** All six hybrid demonstrations returned the same rows as semantic-only, so "hybrid retrieval recovers the exact tokens semantic search misses" was never a measured result. Root cause established live: reciprocal rank fusion **re-ranks the page and only modestly widens it** — a lexical hit promotes a row to lexical rank 1, worth `1/62` ≈ `0.0161` of score, and that is all the lift available. That caps its *reach*: a matched row at semantic rank `R` scores `1/(60 + R) + 1/62` and must displace the row holding the last slot, which sits at semantic rank `top_k` and — pushed down one by the match — lexical rank `top_k + 1`, scoring `1/(60 + top_k) + 1/(62 + top_k)`. That is the **score gate**, and it is one of two — a **candidate-pool gate** (next row) caps reach at `10 * top_k` independently, and the effective reach is the smaller of the two. Deepest semantic rank retrievable by `top_k` after both gates: 2 → 3, 3 → 6, 5 → 10, 10 → 23, 20 → 56, 30 → 110, 40 → 212, 50 → 468, 51 → 510, 64 → 640, 100 → 1,000, 208 → 2,080, 300 → 3,000. All six demos used `top_k` between 2 and 64 — reach 3 to 640 — deep enough to nudge a row already near the top, never deep enough to rescue a buried one. Demos re-engineered to give the target *both* signals and to **print the added/dropped sets rather than assert an outcome**; `vector_search`, `semantic_search`, `rag_pipeline`, `log_analysis` and `catalog_search` each carry a re-engineered demo written against the measured law. *(Corrected 2026-09-04: this row previously ended "the notebooks are pending re-execution, so the recall win is predicted by the arithmetic and not yet shown in stored output." All five have since been re-executed and every one of them prints a measured added/dropped set — see the 2026-09-04 row below.)* Narrative rewritten in `README.md`, `workflows/README.md`, `RESOURCES.md`, `SKILL.md`, `reference/embeddings-and-search.md` and `reference/workflows.md` in the same commit. **(2) The published RRF formula was off by one, and the "single-list penalty" published alongside it is withdrawn.** The measured law is `distance = 1 - ( 1/(60 + rank_vector) + 1/(61 + rank_lexical) )` — **the legs do not share a rank base**; decoding with k = 60 on both terms yields lexical ranks `2..n+1`, impossible for an n-row list, while k = 61 on the lexical leg yields an exact `1..n` permutation (verified on a 30-row corpus with `rank_vector` read from a separate semantic-only run). Best attainable score is therefore `1 - (1/61 + 1/62)` = `0.9674775251189847`, and the widely-quoted `1 - 2/61` = `0.967213` is **unattainable**. The single-list penalty — a row present in only one leg's list forfeits the other term, is capped at `1 - 1/61` = `0.98361`, and therefore loses to any dual-signal row — was published here and is now **withdrawn**. There is no single-list state inside the candidate pool: the lexical leg ranks the **entire pool**. BM25 matches take lexical ranks `1..m` and every remaining pooled row falls back to its semantic order behind them, so no *pooled* row forfeits a term and `0.98361` is not a reachable ceiling. Evidence: a `lexical_search_query_value` matching zero rows still gave every pooled row a lexical term, with `rank_lexical = rank_vector`; promoting one row to lexical rank 1 moved the former rank-1 row to 2 and left every row below the promoted row byte-identical. The actionable replacement is the reach list in finding (1) and the sizing rule that falls out of it: **to retrieve a row at semantic rank `R` by exact token, size `top_k` to at least `R/10`, and above that to whatever the reach list requires** — `R/10` is a floor, not a recipe. The two gates cross at `top_k` 51, so below a few hundred ranks deep the score gate is the one that binds and `R/10` is not enough: a target at semantic rank 100 needs `top_k` = 29, not 10. Reach grows with `top_k`, never without bound. Verified on a 500-row corpus whose target sat at semantic rank 500 of 500: absent at `top_k` 10, 49 and 50, returned from `top_k` 51 upward (the score gate predicted the flip between 50 and 51 exactly; the 510-row pool was not binding there), with distance `0.9820852534562212` = `1 - (1/560 + 1/62)`. When the identifier *is* the whole query and the answer must be certain, use a `WHERE` predicate — a predicate cannot be outranked by a fusion score. **(3) TabFM (`AI.PREDICT`) output is not deterministic** — `FARM_FINGERPRINT` pins the split only. Identical calls return different predictions (regression MAE 236.52 / 236.35 / 235.84; classification accuracy 0.9468 / 0.9362 / 0.9468), consistent with averaging shuffled `n_ensembles` passes. `AI.EVALUATE` therefore scores its own fresh predictions rather than the materialized rows. `RESOURCES.md`'s best-practice line scoped to the split, Limitations bullet added, mirrored in `reference/predictive-ai.md`. **(4) The three TimesFM status columns disagree about success.** `ai_evaluate_status` and `ai_detect_anomalies_status` return **`NULL`**; only `ai_forecast_status` returns a zero-length empty string. `RESOURCES.md` had flattened all three to "Empty if successful", so `WHERE ai_evaluate_status <> ''` silently dropped every successful row. Filter with `IS NOT NULL`. Also fixed: the vector-index floor is **two gates** — `CREATE VECTOR INDEX` is rejected outright below 5,000 rows (verified for both `IVF` and `TREE_AH`; undocumented by Google) while *population* waits for ~10 MB; `VECTOR_SEARCH` status aligned to `GA (single-search/hybrid syntax Preview)` across README and RESOURCES; bigframes version reconciled to **2.39.0** (the `uv.lock` pin that actually executed) from an unsourced 2.48.0; `AI.PREDICT` accepted column types corrected from five to six in the skill. A programmatic round-trip check for `**Functions used:**`/`**Featured in:**` was added to the "New workflow" checklist above, after five one-way links survived several phases of hand-checking. |
| 2026-09-02 | Hybrid reach — the lexical candidate-pool gate (supersedes the reach tail in the row above) | **BigQuery hands the BM25 leg only the top `10 * top_k` rows by semantic rank.** A row deeper than that receives **no lexical rank at all**, however perfectly the token matches — BM25 never sees it. Hybrid reach is therefore governed by **two gates**, not one: **Gate 1 (candidate pool)** `rank_vector <= 10 * top_k`; **Gate 2 (fusion score)** `1/(60 + rank_vector) + 1/(61 + rank_lexical)` must beat the row holding the last slot. **Effective reach = min( score_reach(`top_k`), 10 * `top_k` )** — Gate 1 binds for `top_k >= 51`, Gate 2 below that. Deepest semantic rank retrievable: 2 → 3, 3 → 6, 5 → 10, 10 → 23, 20 → 56, 30 → 110, 40 → 212, 50 → 468, 51 → 510, 64 → 640, 100 → 1,000, 208 → 2,080, 300 → 3,000. **Supersedes** two claims recorded above: the **`top_k >= 64` → any semantic rank / unbounded reach** threshold, and the `63 → 953,189` reach entry — both are the score gate read in isolation, and the pool gate caps `top_k = 63` at 630 and `top_k = 64` at 640. Also supersedes "the lexical leg ranks the **entire corpus**": it ranks the entire **pool**. The scoring law itself — 60 semantic base, 61 lexical base, exact to 15-16 significant digits — is **unchanged and still correct**. Measured across **four independent corpora** (8, 500, 1,500 and 3,000 synthetic rows plus the real 7,275-row `thelook_ecommerce.products` catalog), ~35 data points, including **three sharp out-of-sample predictions**: 3,000-row table with the target at semantic rank 3,000 — predicted flip at `top_k = 300`, observed 299 no match / **300 match**; 1,500-row table with the target at rank 1,500 — predicted 150, observed 149 / **150**; 500-row table with the target at rank 500 — flips at 51 on the score gate, the pool never binding. The catalog's target at semantic rank 2,072 is absent at `top_k = 64` precisely because the pool was 640 rows; it needs `top_k >= 208`. All three synthetic probe tables (500, 1,500 and 3,000 rows) were **unindexed**, sitting below the 5,000-row `CREATE VECTOR INDEX` floor established in the row above, and are brute-force scanned. The 7,275-row catalog — the fourth corpus — **was** indexed: it carried a `TREE_AH` hybrid vector index with `lexical_search_columns`, status `ACTIVE` at 100% coverage, when the `top_k = 64` observation was made. That is the stronger result: the pool gate shows up identically with and without an index, so it is neither an index artifact nor something an index can avoid. Diagnostic signature of a row outside the pool: the whole result set returns with `rank_lexical = rank_vector`, i.e. every distance equals `1 - ( 1/(60+r) + 1/(61+r) )`; a best distance of `0.967478` means **nothing matched**, `0.967734` means a match fired. **Rule to teach:** hybrid widens recall proportionally to `top_k`, never unboundedly — for a target at semantic rank `R`, size `top_k` to at least `R/10` and above that to whatever the reach list requires — `R/10` is necessary, not sufficient, and below `R ≈ 500` the score gate binds instead (rank 100 needs `top_k` = 29, not 10); when the identifier *is* the whole query and the answer must be certain, use `WHERE sku = @sku`, which cannot be outranked by a fusion score and has no pool. Correction applied in this commit to every hand-authored source carrying the reach claim: `README.md`, `RESOURCES.md` and `overview.ipynb`; `functions/vector_search/` and `functions/ai_search/` (notebook + `.sql` each); the `semantic_search`, `rag_pipeline`, `log_analysis` and `catalog_search` workflow notebooks; and the agent skill's hand-written files (`SKILL.md`, `reference/embeddings-and-search.md`, `reference/workflows.md`). The six matching `narrative/` files are tool-generated; all 39 narratives plus `skill.manifest.json` were regenerated from the corrected notebooks in this same commit, and `agent-skills validate --all` passes on all three skills. |
| 2026-09-02 | Hybrid RRF write-up — mixed-base counterexample made reproducible, `R/10` scoped, catalog index status corrected | Three corrections to the way the measured law is presented; the law itself is unchanged. **(1) The asymmetry counterexample was not reproducible.** The passage showing that the two legs do not share a rank base gave, for a row at semantic rank 1 / lexical rank 2, the observed `0.9677335415040333` = `1 - (1/61 + 1/63)` against a "symmetric prediction" of `1 - (1/62 + 1/62)` — but `1/62 + 1/62` is the shared-base-61 reading of a row at rank **1 in both legs**, not a reading of a (1, 2) row under any single base, so a reader who checked the arithmetic could not reproduce it. Replaced everywhere with the *between-the-shared-bases* framing: 60 on both legs gives `1 - (1/61 + 1/62)` = `0.9674775251189847`, 61 on both legs gives `1 - (1/62 + 1/63)` = `0.9679979518689196`, and the measured `0.9677335415040333` falls **between** them — which is the signature of mixed bases. Because `0.9674775251189847` is also the best attainable score under the true law (rank 1 in both legs), the two roles of that number are now stated explicitly wherever both appear. **(2) `top_k >= R/10` is necessary, not sufficient.** It was published as a sizing recipe; it is a floor. Below `R ≈ 500` the score gate binds and `R/10` falls short — rank 100 needs `top_k = 29` rather than 10, rank 200 needs `40` rather than 20, rank 500 needs 51 rather than 50. Every "size `top_k` to about `R/10`" phrasing now states the floor and points at the effective-reach table for the real answer. **(3) The probe corpora were misdescribed as "both probe tables unindexed".** There are **three** synthetic probe tables (3,000, 1,500 and 500 rows), all unindexed because they sit below the 5,000-row `CREATE VECTOR INDEX` floor, and the fourth corpus — the 7,275-row product catalog — **was** indexed, carrying a `TREE_AH` hybrid index with `lexical_search_columns` at `ACTIVE` / 100% coverage when the `top_k = 64` observation was made. That strengthens the finding rather than weakening it: the pool gate appears identically with and without an index, so it is neither an index artifact nor something an index can avoid. Also in this pass: the demo `top_k` range in the 2026-09-02 review row above corrected from "2 and 30 — reach 3 to 110" to **2 and 64 — reach 3 to 640** (`catalog_search` sweeps to `top_k => 64`, the largest page size any demo used), and the same row's file list restated to cover the hand-authored sources only, since the agent skill's `narrative/` files are tool-generated and pick up corrections on regeneration. |
| 2026-09-02 | `catalog_search` re-executed — two-gate model confirmed end to end, and a routing gap in the sibling skills closed | **The flagship demo now shows the pool gate live on a real 7,275-row catalog with an `ACTIVE` `TREE_AH` hybrid index.** Target at semantic rank 2,072: absent at `top_k` 5, 64 and **207** (pool 2,070 — two rows short), returned at **208** (pool 2,080) at page position 60. The fused distance matched the predicted `1 - (1/(60 + 2072) + 1/62)` = `0.983401924589965` to **zero difference across all 15 digits**. At `top_k` 207 the best distance was exactly `1 - (1/61 + 1/62)` = `0.967477525119`, the zero-match signature, confirming BM25 never saw the row; at 208 the same head-of-page rows shift to `0.967734`, the one-match signature, because the single match pushed every unmatched row down one lexical rank. Cell 32 independently shows a genuine recall change (1 row added, 1 dropped, all 4 shared rows repositioned) with the promoted row at `1 - (1/62 + 1/62)` = vector rank 2 / lexical rank 1. **Separately, Phase 10 opened a gap in the router skill and it is now fixed.** `choosing-a-bigquery-ai-approach` split the world as "tabular/trained → BigQuery ML, generative/unstructured → AI functions" and routed *all* structured prediction to `bigquery-ml`; `AI.PREDICT` breaks that split, since it is a foundation model for ordinary feature tables. Added a tabular-prediction decision question and head-to-head bullet (20-feature / 10-class caps, and the measured nondeterminism), corrected the routing lines, and added the reciprocal pointer in the `bigquery-ml` skill. Both bumped to 0.1.1; `bigquery-ai-functions` regenerated at 0.2.0 (39 narratives, 22 changed, 3 new). `agent-skills validate --all` passes on all three. |
| 2026-09-02 | Hybrid RRF — the "two rank bases" claim withdrawn as over-stated (supersedes the three rows above) | **The measured arithmetic is unchanged; the interpretation published alongside it was not supported by it.** `VECTOR_SEARCH` and `AI.SEARCH` return no rank column, so only `rank_vector` is ever observed — it comes from a separate semantic-only run — and the lexical term is the residual after subtracting `1/(60 + rank_vector)` from `1 - distance`. What that pins is a set of **denominators**, not a pair of constants. Because `1/(61 + r)` and `1/(60 + (r + 1))` are the same number, two readings fit every observation identically: **(A)** two constants, k = 60 semantic / k = 61 lexical, both ranks `1..n`; **(B)** one constant k = 60 on both legs, with lexical ranks running `2..n+1`. Nothing observable from outside BigQuery separates them. **B is the likelier.** k = 60 over 1-based ranks is canonical RRF (Cormack, Clarke & Buettcher, SIGIR 2009) and the default wherever the constant is exposed — Elasticsearch and OpenSearch both name it `rank_constant` and default it to 60, Azure AI Search fixes k = 60 and does not expose it, Spanner and AlloyDB write 60 into their documented SQL, and Vertex AI Vector Search documents no k at all. **61 appears as the constant in no published implementation**; where 61 does appear universally is as the *rank-1 denominator*, `1/(60 + 1)` — exactly the transcription slip that would produce the observed `1/62` on a top-ranked row. The semantic leg lands on the canonical `1/61` for its own top row, so this project's rank convention already agrees with BigQuery's on one leg and the extra `+1` sits on the lexical side specifically. **The argument published here as decisive is not.** "Decoding with k = 60 on both legs yields lexical ranks `2..n+1`, and no n-row list hands out rank n+1" rules out a shared base combined with *ordinary 1-based* lexical numbering — it does **not** rule out reading B, where a contiguous block starting at 2 is precisely what an offset ranking looks like. It is evidence *for* an offset, not against a shared constant. The between-the-shared-bases counterexample added in the row above has the same defect and is withdrawn with it. The `60`/`61` form stays in every formula because it is the shortest expression that reproduces every observed value to 15-16 significant digits; it is now framed as arithmetic that holds rather than as two deliberate design decisions. Corrected in every hand-authored source carrying the claim: `README.md`, `RESOURCES.md`, `overview.ipynb`, `functions/vector_search/` (notebook + `.sql`), `functions/ai_search/` (notebook + `.sql`), and the `semantic_search`, `rag_pipeline`, `log_analysis` and `catalog_search` workflow notebooks; plus the agent skill's hand-written `SKILL.md` and `reference/embeddings-and-search.md`. `rag_pipeline`'s decomposition cell prints the equivalence rather than asserting two bases, and its stored output was updated to match (the numbers it computes are unchanged). Six `narrative/` files regenerated from the corrected notebooks and `skill.manifest.json` rebuilt; `agent-skills validate --all` passes on all three skills. Tracked in *Tracked open questions* above: if the fusion is ever documented, the detail that matters is whether the lexical leg's ranks are offset or its constant differs. |
| 2026-09-02 | Release-notes sweep, April–September 2026 — six shipped capabilities found uncovered, and the intake gap that hid them | **The audit procedure had no step that reads the release notes**, so it could only re-check what was already built. Both this project's *Tracked upcoming* tables and `bq-ml`'s sat empty from April to September while six BigQuery ML/AI capabilities shipped. Added **Step 1b** to *How to run an audit* above: read the release notes forward from the last audit date, triage every ML/AI entry into new function / new capability / status change / belongs-to-`bq-ml`, and watch for entries that *remove* a feature. Findings recorded this pass, in this project's surface: **(1)** `gemini-3.1-flash-lite` and `gemini-3.5-flash` GA'd 2026-08-10 — **the default endpoint did not move**, it is still `gemini-2.5-flash`, so no stored output here is stale and nothing needed re-execution; documented in the new [Choosing a Gemini Model Endpoint](RESOURCES.md#choosing-a-gemini-model-endpoint) section along with the real gotcha, that the 3.x family is multi-regional-endpoint only and `europe-west2`/`europe-west6` silently resolve to the **global** endpoint, which is a data-residency problem and not a latency note. **(2)** Vector and search index lifecycle — `VECTOR_INDEX.STATISTICS`, `ALTER VECTOR INDEX REBUILD` and TreeAH `PARTITION BY` (GA 2026-04-29) plus `ALTER SEARCH INDEX` (Preview 2026-07-13) — this project creates indexes in eight files and manages none; queued as one unit of work against `functions/vector_search/` and `functions/ai_search/`, explicitly *not* a new workflow. **(3)** `OBJ.GET_READ_URL` GA'd 2026-03-31 but is absent from the ObjectRef functions reference page, which still lists only `OBJ.MAKE_REF`, `OBJ.GET_ACCESS_URL` and `OBJ.FETCH_METADATA`; recorded as observed-not-documented. **(4)** A genuine documentation contradiction: the 2026-06-12 release note says AI functions accept `ObjectRef` directly "without calling the `OBJ.GET_ACCESS_URL` function", the generative AI overview and every `AI.GENERATE_*` page still say the wrapper is required, and `AI.SCORE`/`AI.IF` document the bare form. **Not resolved by reading more documentation — this project can settle it by running it**, and until it does every notebook keeps `OBJ.GET_ACCESS_URL(col, 'r')`, the one form documented everywhere. **(5)** Hybrid search has already been pulled once mid-Preview — Preview 2026-06-25, *temporarily disabled* 2026-07-09, restored 2026-08-03. That episode was never recorded here even though all five hybrid rows in the watch list depend on that surface; it is precedent that the feature can vanish, not just change. **(6)** Two items belong to `bq-ml` and were written into that project's *Tracked upcoming* table in the same pass rather than left here: the `ML.TREND`/`ML.SEASONALITY`/`ML.DETECT_CHANGE_POINTS` TVFs (Preview 2026-08-20) and the `XGBOOST_VERSION` option (GA 2026-08-27). Also confirmed **not** gaps: index-side `lexical_search_columns` on `CREATE VECTOR INDEX` is already covered, and reciprocal rank fusion remains undocumented as of this date, so watch-list rows V1 and V2 stand as written. |
| 2026-09-03 | Vector and search index lifecycle — built, and gated behind a reservation requirement | Closes both index-lifecycle rows from the 2026-09-02 release-notes sweep (`VECTOR_INDEX.STATISTICS` / `ALTER VECTOR INDEX REBUILD` / TreeAH `PARTITION BY`, GA 2026-04-29; `ALTER SEARCH INDEX`, Preview 2026-07-13). Everything below was measured against a purpose-built 7,275-row `TREE_AH` hybrid index and a second partitioned index, both dropped after the run. **(1) `VECTOR_INDEX.STATISTICS` takes exactly one argument and it must be a relation.** `VECTOR_INDEX.STATISTICS(TABLE t)` — adding the index name as a second argument fails with `Signature accepts at most 1 argument, found 2 arguments`, and passing a string instead of `TABLE t` fails with `argument 1 must be a relation (i.e. table subquery)`. One output column, `tfdv_drift`: `null` before the first refresh, `"0.0"` at fresh 100% coverage, and **zero rows** — not an error, and 0 bytes scanned — on a table carrying no index at all, so it is safe to call unconditionally. **(2) Coverage and drift are independent signals, demonstrated rather than asserted.** Inserting 11,780 rows whose vectors duplicate ones already indexed (7,275 → 19,055) dropped `coverage_percentage` 100 → 38 and set `unindexed_row_count` to 11,780, while `tfdv_drift` moved only `0.0` → `1.97e-5` and `last_model_build_time` did not change at all, holding across six 90-second polls. A large volume of new-but-distributionally-identical rows is a **coverage** problem, not a drift problem — the two argue for different responses, and `last_model_build_time` is a third signal distinct from `last_refresh_time`. **(3) Both `ALTER` paths require a BACKGROUND reservation, and cannot even be dry-run.** `ALTER VECTOR INDEX ... REBUILD` returns `Cannot alter vector index on table <t> because there is no BACKGROUND reservation.`; `ALTER SEARCH INDEX ... SET OPTIONS (...)` and `ALTER SEARCH INDEX ... ADD COLUMN` return the identical message with `search index` substituted. The check fires **before** validation, so `--dry_run` returns the reservation error rather than `Query successfully validated`, even when the named index does not exist — which rules out the parse-check-for-free pattern used for `CREATE VECTOR INDEX` in `functions/vector_search/` section 9. Creating an index, populating it and querying through it are **not** gated; only altering one is. Running these needs an Enterprise-edition reservation carrying a `BACKGROUND` job-type assignment, and an autoscale reservation with baseline 0 is the cheap shape since it bills only while the alteration runs. **The post-rebuild field values are therefore unmeasured** and are not published: `last_index_alteration_info` stays `null` until an `ALTER` succeeds, and it is a `RECORD`, so `bq query --format=csv` refuses it (`Cannot print record field ... in CSV format`) — read it with `--format=prettyjson`. **(4) A vector index's `PARTITION BY` must match the base table's partitioning expression exactly.** Against a table partitioned by `RANGE_BUCKET(id, GENERATE_ARRAY(0, 30000, 5000))`, repeating that expression validates; `PARTITION BY category` fails with `Invalid Partition By expression`, and so does naming a column on a table that is not partitioned at all. Partitioned indexes populate normally — one on a 19,055-row / ~8.6 MB table reached 100% coverage about seven minutes after `CREATE`. **(5) Search indexes have a 10 GiB floor.** `CREATE SEARCH INDEX` *succeeds* on a small table and then never populates: `index_status` `TEMPORARILY DISABLED`, `coverage_percentage` 0, `disable_time` equal to `creation_time`, and `disable_reason` = "The base table size is below the threshold of 10737418240 bytes for indexing." 10,737,418,240 bytes is exactly 10 GiB, against the vector index's 5,000-row hard reject and ~10 MB population gate — three orders of magnitude apart. Nothing at teaching scale clears it, which is why this project creates no search index and reaches for `lexical_search_columns` on a vector index instead. Also noted: `SEARCH_INDEXES.ddl` is normalized rather than a verbatim echo — a statement written with `OPTIONS (analyzer = 'LOG_ANALYZER')` is recorded as `OPTIONS (data_types = ['STRING'])`, with the analyzer in its own column. **(6) A negative `tfdv_drift` is a sentinel, not a magnitude, and the cause is not isolated.** Two freshly built indexes at 100% coverage reported differently: `"0.0"` from the unpartitioned hybrid index, `-1.0` from the partitioned index, which also had no `lexical_search_columns`. Those two differ in more than one way, so partitioning, the absence of lexical columns, and refresh recency all remain in play; published as *read a negative value as no-figure-available and corroborate with `coverage_percentage`*, with the confound stated rather than a mechanism guessed. **Applied to:** a new lifecycle block in `RESOURCES.md` beside the existing vector-index rules, Example 10 in `functions/vector_search/vector_search.sql` plus a matching section 10 in its notebook, and a `CREATE`/`ALTER SEARCH INDEX` reference section in `functions/ai_search/` (notebook + `.sql`). The notebooks' new code cells query `INFORMATION_SCHEMA.VECTOR_INDEXES` / `SEARCH_INDEXES` and `VECTOR_INDEX.STATISTICS` only — all reservation-free and safe on a table with no index — while every gated `ALTER` ships as fenced reference SQL rather than an executable cell. **Not a new workflow**, as scoped. One earlier observation was **checked and withdrawn before publication**: `_SEARCH_INDEX_KW_*` shadow tables previously seen in the dataset were re-counted at zero, so no orphaned-shadow-table claim was written anywhere. |
| 2026-09-03 | Cross-links to the sibling project's new model-free time-series functions | `bq-ml` shipped `functions/time_series/` — `ML.TREND`, `ML.SEASONALITY`, `ML.DETECT_CHANGE_POINTS`, three Preview TVFs that decompose a series with no `CREATE MODEL`. They sit next to this project's TimesFM surface without competing with it: those describe history, `AI.FORECAST` predicts. Added pointers in `functions/ai_forecast/` (notebook Alternatives list + `.sql` header) and `workflows/time_series_intelligence/`, and a new triage branch in the `choosing-a-bigquery-ai-approach` skill — "I want to understand a time series" now has three answers, not two, split first on predict-vs-describe. Two measured results from that build matter here. **`ML.SEASONALITY`'s weekly and yearly components are bit-identical to a trained ARIMA_PLUS's** (mean abs diff 0.0, corr 1.0), so seasonality alone never justifies a model. And **all three TVFs gap-fill before computing**, which on a gapped series manufactures the structural break `ML.DETECT_CHANGE_POINTS` then reports — six of seven windows on the public Citi Bike table were ingestion-outage edges. That is the same class of trap as this project's anomaly baselines: `AI.DETECT_ANOMALIES` finds individual off-baseline rows, `ML.DETECT_CHANGE_POINTS` finds windows where the level moved, and neither should be trusted on a series with unprofiled gaps. No functions changed in this project. |
| 2026-09-03 | Second cross-link pass — `functions/ai_detect_anomalies/` | The first pass linked `functions/ai_forecast/` and `workflows/time_series_intelligence/` to the sibling project's `functions/time_series/` but missed `ai_detect_anomalies`, which carries the sharpest contrast of the three: `AI.DETECT_ANOMALIES` flags individual outlying **points** against a TimesFM forecast baseline, while `ML.DETECT_CHANGE_POINTS` finds **sustained** level shifts with no model and no baseline at all. A spike that returns to normal the next day is an anomaly and not a change point; a permanent step up in volume is a change point that may never register as an anomaly. Added to the notebook's Alternatives list and the `.sql` header. **Reviewed and deliberately skipped:** `functions/ai_forecast/` and `workflows/time_series_intelligence/` get no new cells — both run synthetic, complete `GENERATE_DATE_ARRAY` series with injected point anomalies and no gaps, so a change-point demo there would either find nothing or rediscover the injections. Markdown/comment-only; no notebook re-executed. |
| 2026-09-03 | Docs and skills catch-up — `RESOURCES.md` and the `bigquery-ai-functions` skill had no route to the sibling's model-free time-series functions at all | The cross-link passes updated notebooks only. Two gaps found on review: **(1)** `RESOURCES.md` contained zero mentions of `ML.TREND`/`ML.SEASONALITY`/`ML.DETECT_CHANGE_POINTS` — the reciprocal of the cross-link block `bq-ml`'s `RESOURCES.md` already carries for this project's TimesFM functions. Added to the *Predictive AI* section: what the model-free TVFs are for, plus the anomaly-vs-change-point distinction with the measured 79-anomalies-against-2-windows zero overlap. **(2)** The `bigquery-ai-functions` skill had no mention either, so an agent routed there for "something changed in my time series" could only reach `AI.DETECT_ANOMALIES` and would never surface the change-point option. Added a *"where did this series change, not which points are odd"* routing entry to `reference/predictive-ai.md` (carrying the gap-fill caveat, so the recommendation ships with its own precondition) and a pointer on the `SKILL.md` reference-file line (manifest 0.2.2 -> 0.2.3, validates OK). Confirmed adequate and left alone: `README.md`, whose single cross-project line routes to `choosing-a-bigquery-ai-approach`, which already covers change points vs. anomalies vs. drift as three distinct questions. |
| 2026-09-03 | Docs hygiene — six broken relative links in this file | Found in the pre-push review. `PLANS.md` lines 355 and 365 used notebook-relative paths (`../../workflows/content_analysis/`, `../../functions/ai_classify/` and four more), which from a project-root file overshoot to the repo root. Dropped the `../../`; all six targets verified to exist. Also confirmed the three `RESOURCES.md#anchor` links in this file resolve to real headings. The companion sweep in `../bq-ml/` (absolute local paths and a dead citation) is recorded in that project's audit log. |
| 2026-09-03 | Outward-link policy written down and made enforceable — this project already complies | The rule behind the recent link-hygiene fixes is now explicit: this project is the canonical source of truth for BigQuery AI functions, its content is copied into a distributable skill, and a reference pointing outside the project does not travel. Written into *Cross-Referencing Convention → Link policy* above (three allowed targets: this project, the sibling `../bq-ml/`, public documentation; `PLANS.md` exempt as forward-looking and never shipped; `README.md` may cite `agent-skills/`) and enforced by a new `check-links` subcommand in `agent-skills/tooling`, which separates a **link** (`[](…)`, followable, always a violation when outward) from a **mention** (a backticked path in prose, a violation only when the target still exists — a dangling one is retirement provenance and is kept). Baseline: **0 violations across 74 files** — this project is already clean, and the checklist above now requires it stay that way on every change. The `PLANS.md` exemption is what makes that true: this file's one out-of-repo citation is future-facing and legitimately outside a skill's scope. The sibling `bq-ml` starts at 141 violations; its cleanup is tracked in that project's audit log. Tooling and documentation only; no notebook touched, nothing re-executed. |
| 2026-09-04 | TimesFM defaults re-measured — a watch-list claim retracted, and a reproducibility problem found underneath it | **Watch-list row P6 was wrong and is retracted.** It claimed `AI.EVALUATE` defaults to TimesFM 2.0 while `AI.FORECAST` defaults to 2.5. Re-measured live: **all three TimesFM functions default to TimesFM 2.5** — `AI.FORECAST`, `AI.EVALUATE` and `AI.DETECT_ANOMALIES`. P6 was the only place in the project asserting otherwise; `RESOURCES.md`, `README.md`, `functions/ai_evaluate/` and every skill narrative already said 2.5, and P6 contradicted this file's own 2026-09-01 row recording the 2.0 → 2.5 flip for the whole family. **Nothing shipped to a reader was ever wrong** — the error lived only in the forward-looking watch list. **How a wrong claim got written: the BigQuery query cache.** Re-running identical SQL returns the cached first result, so an unstable function looks perfectly stable, and changing only the `SELECT` list creates a *different* cache entry, so two "identical" comparison loops can disagree and read as a version difference. A second artifact compounds it: putting the unpinned, `'TimesFM 2.0'` and `'TimesFM 2.5'` calls in one `UNION ALL` returned three distinct values, reproducibly, where isolated jobs showed unpinned and 2.5 bit-identical. **Method now required for any determinism or default-version question:** one variant per job, `--nouse_cache` on every job, collect a *value set* over ~10 runs and compare sets rather than single draws, and cross-check the "right" answer by recomputing it from a function that is deterministic. Measured under that method: `AI.FORECAST` unpinned `292.90997314453125` = 2.5 exactly, 12/12 stable, against 2.0's `294.2085876464844`; `AI.EVALUATE` unpinned and 2.5 produced identical value *sets* while 2.0's was disjoint; `AI.DETECT_ANOMALIES` 2.5 pinned 10/10 `0.8302092775192951`, unpinned matching, 2.0 at `0.3039181444304737`. **The real finding is underneath.** `AI.EVALUATE` is **not reproducible run to run, and pinning does not fix it** — with `model` and `context_window` both pinned, cache off, on a deterministic synthetic series, 2 of 16 runs returned `0.5913808905590097` against the other 14's `0.8652198481135486`, a ~32% swing in the headline metric at about 1 in 8. The majority value is provably the correct one: MAE hand-computed from `AI.FORECAST` output over the same history and horizon equals `0.8652198481135486` to the last digit, 3/3. `AI.DETECT_ANOMALIES` shows the same shape. Ruled out: context window (`64` → `0.7479417635990426`, `128` → `0.6498225880535273`, `256` → `0.7149326356365046`, and `512`/`1024`/`2048`/`4096` all → `0.8652198481135486`), horizon truncation (all 31 prefixes), and version mixing, since it occurs on 2.0 and 2.5 alike. **Mechanism unidentified, and none is published** — the behavior and the repro are, the cause is not. **Consequence for the project's standing advice:** "pin `model` for reproducibility" is true for version drift and **insufficient** here, so every place carrying it now says so, and any recorded `AI.EVALUATE` or `AI.DETECT_ANOMALIES` metric can move with no query change. P6 replaced with the reproducibility row. Applied to `RESOURCES.md` (a reproducibility block beside the default-version note, plus the Limitations lines on both functions), `README.md`, `overview.ipynb`, `functions/ai_evaluate/` and `functions/ai_detect_anomalies/` (notebook + `.sql` each), `workflows/time_series_intelligence/`, and the skill's hand-written `SKILL.md` and `reference/predictive-ai.md`. `functions/ai_forecast/` was reviewed and deliberately left alone — `AI.FORECAST` *is* reproducible once pinned, so its existing wording is correct as written. All notebook edits are markdown cells, so **nothing needed re-execution**; verified by diffing at `-U0` and confirming only `source` lines moved. Three `narrative/` files regenerated — `ai_evaluate`, `ai_detect_anomalies`, `time_series_intelligence`. `overview.ipynb` is edited here but is **deliberately not one of the skill's 39 narratives**, and converting it adds a 40th; if a regeneration ever leaves `narrative/overview.md` on disk, delete it and rebuild the manifest. Manifest bumped 0.2.3 → 0.2.4, `agent-skills validate --all` passes on all three skills, and `check-links` reports 0 violations across 74 files. **Also corrected in this pass:** the 2026-09-02 review row above claimed the five re-engineered hybrid demos were "pending re-execution, so the recall win is predicted by the arithmetic and not yet shown in stored output". All five have been re-executed and each prints a measured added/dropped set — `vector_search` cell 27 (`DCK-2210` added, `MON-2711` dropped, target at vector rank 8 of 24), `semantic_search` cell 25 (id 7 added at semantic rank 4, id 5 pushed out), `rag_pipeline` cell 25 (the `ERR-4417` entry added, a logging entry dropped), `log_analysis` cell 29 (ticket 28, the only one carrying `IDP-7761`, added; ticket 17 dropped) and `catalog_search` cell 32 (1 added, 1 dropped, all 4 shared rows repositioned). The recall win is shown, not predicted. |

### Notebook update plan (May 2026 audit)

Notebook updates following the 2026-05-10 documentation audit. Two categories per group:
- **Revise + verify**: Needs content edits (new cells, updated descriptions) before a Restart & Run All
- **Verify only**: No content changes expected — just confirm it still runs clean

Each notebook is touched exactly once: revise (if needed) → Restart & Run All → review. Workflow: Claude edits → Mike does Restart & Run All → Claude reviews outputs. One notebook at a time, checked off as completed.

#### Function notebooks — Revise + verify

| # | Notebook | Changes Needed | Priority |
|---|----------|---------------|----------|
| 1 | `functions/ai_embed/ai_embed.ipynb` | New `model` param, built-in `embeddinggemma-300m`, 4 new embedding models (esp. `gemini-embedding-2-preview` multimodal) | High |
| 2 | `functions/ai_similarity/ai_similarity.ipynb` | New `model` param, same new models as AI.EMBED | Medium |
| 3 | `functions/ai_generate_embedding/ai_generate_embedding.ipynb` | New `gemini-embedding-2-preview` model support | Medium |
| 4 | `functions/ai_if/ai_if.ipynb` | New `examples`, `optimization_mode` (Preview), `embeddings` (Preview), `max_error_ratio` params | High |
| 5 | `functions/ai_classify/ai_classify.ipynb` | Same new params as AI.IF | High |
| 6 | `functions/ai_score/ai_score.ipynb` | New `max_error_ratio` param | Medium |
| 7 | `functions/ai_detect_anomalies/ai_detect_anomalies.ipynb` | Status Preview → GA, new `context_window` param | Medium |
| 8 | `functions/ai_evaluate/ai_evaluate.ipynb` | New `context_window` param, new MASE output metric | Medium |
| 9 | `functions/ai_forecast/ai_forecast.ipynb` | New `forecast_end_timestamp` alternative to `horizon` | Low |
| 10 | `functions/ai_generate/ai_generate.ipynb` | `thinking_level` for Gemini 3.0+ | Low |
| 11 | `functions/ml_process_document/ml_process_document.ipynb` | Page limit 100→130, 120s timeout, batch size of 10 | Low |

#### Function notebooks — Verify only

| # | Notebook | Notes |
|---|----------|-------|
| 12 | `functions/ai_agg/ai_agg.ipynb` | AI.AGG re-enabled. Warning removed. Expanded with examples 8-11 (connection_id, quantitative, AI.AGG vs AI.GENERATE, multimodal ObjectRef). Examples 8-10 verified. **Example 11 (multimodal):** AI.AGG returns NULL with PDF input via ObjectRef — commented out. Docs say "images via ObjectRef" so PDFs may not be supported. Future: retry with PNG images or wait for PDF support. |
| 12b | `functions/ai_parse_document/ai_parse_document.ipynb` | New notebook (2026-05-23). Needs initial Restart & Run All to verify all cells run clean. |
| 13 | `functions/ai_generate_text/ai_generate_text.ipynb` | USE_CHAT_MODE is Open-models-only; verify existing examples still run |
| 14 | `functions/ai_generate_table/ai_generate_table.ipynb` | No doc changes |
| 15 | `functions/ai_generate_bool/ai_generate_bool.ipynb` | No doc changes |
| 16 | `functions/ai_generate_double/ai_generate_double.ipynb` | No doc changes |
| 17 | `functions/ai_generate_int/ai_generate_int.ipynb` | No doc changes |
| 18 | `functions/ml_generate_text/ml_generate_text.ipynb` | No doc changes |
| 19 | `functions/ml_generate_embedding/ml_generate_embedding.ipynb` | No doc changes |
| 20 | `functions/ai_search/ai_search.ipynb` | No doc changes |
| 21 | `functions/vector_search/vector_search.ipynb` | No doc changes |
| 22 | `overview.ipynb` | No doc changes — verify interactive tour still runs |

#### Workflow notebooks — Verify only

All workflows use functions that were updated. Verify they still run clean. If a workflow would benefit from demoing a new capability (e.g., optimized mode in Content Moderation), promote it to "Revise + verify" during review.

| # | Notebook | Functions with changes |
|---|----------|-----------------------|
| 23 | `workflows/content_analysis/content_analysis.ipynb` | AI.AGG re-enabled. Warning removed. Needs Restart & Run All. |
| 24 | `workflows/content_moderation/content_moderation.ipynb` | AI.AGG re-enabled. Warning removed. Includes Step 2b (AI.IF few-shot examples). Needs Restart & Run All. |
| 25 | `workflows/data_enrichment/data_enrichment.ipynb` | AI.GENERATE |
| 26 | `workflows/document_intelligence/document_intelligence.ipynb` | AI.AGG re-enabled. Warning removed. Needs Restart & Run All. |
| 27 | `workflows/log_analysis/log_analysis.ipynb` | AI.AGG re-enabled. Warning removed. Needs Restart & Run All. |
| 28 | `workflows/multimodal_analysis/multimodal_analysis.ipynb` | AI.EMBED, AI.SIMILARITY |
| 29 | `workflows/rag_pipeline/rag_pipeline.ipynb` | AI.EMBED |
| 30 | `workflows/semantic_search/semantic_search.ipynb` | AI.EMBED, AI.SEARCH |
| 31 | `workflows/time_series_intelligence/time_series_intelligence.ipynb` | AI.FORECAST, AI.DETECT_ANOMALIES, AI.EVALUATE |

---

## Remaining Open Questions

1. **Colab vs Vertex AI Workbench**: Should notebooks target plain Colab or also show Vertex AI Workbench usage?
