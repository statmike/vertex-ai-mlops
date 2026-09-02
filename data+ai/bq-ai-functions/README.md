![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2Fdata%2Bai%2Fbq-ai-functions&file=README.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/data%2Bai/bq-ai-functions/README.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-ai-functions/README.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-ai-functions/README.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-ai-functions/README.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-ai-functions/README.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
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
<tr>
  <td style="text-align: right">
    <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/data%2Bai/bq-ai-functions/README.md"><img src="https://www.svgrepo.com/download/5445/download-button.svg" alt="Download icon" width="20px"></a> <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/data%2Bai/bq-ai-functions/README.md">Download File</a> <i>(right-click and "Save As")</i>
  </td>
</tr>
</table><br/><br/>

---
# BigQuery AI Functions

Use generative AI, embeddings, semantic and hybrid search, forecasting, anomaly detection, and tabular prediction directly in BigQuery SQL — no ML infrastructure to manage.

This project provides a progressive learning system: start with a quick overview of all available functions, drill into individual functions with hands-on examples (SQL, `%%bigquery` magics, and BigFrames), then compose functions together in end-to-end workflows.

## Start Here

| Resource | Description |
|----------|-------------|
| [Interactive Overview](overview.ipynb) | Runnable notebook tour — one example per category |
| [Setup Reference](setup/) | Connections, models, endpoints, quotas, and permissions |
| [Detailed Function Reference](RESOURCES.md) | Complete syntax, inputs, outputs, and limitations for every function |
| [Agent Skill](../../agent-skills/.agents/skills/bigquery-ai-functions/SKILL.md) | Packaged, use-case-organized reference for AI coding agents — see below |

### Using this project with an AI coding agent

This project's Agent Skill content lives centrally in [`agent-skills/`](../../agent-skills/) at the repo root (alongside every other skill built from this repo), not inside this folder — see the [`bigquery-ai-functions` skill](../../agent-skills/.agents/skills/bigquery-ai-functions/SKILL.md), a use-case-organized (generation, classification/scoring, embeddings/search, predictive AI, driver analysis, document processing, workflows), gotcha-rich distillation of `RESOURCES.md` built for coding agents, not just human readers.

- **Claude Code** — picked up automatically from `.claude/skills/bigquery-ai-functions` (a repo-root symlink into `agent-skills/`) anywhere in this repo; no setup needed. It activates automatically when your request matches — generating/classifying/scoring content, embeddings and semantic or hybrid search, zero-training forecasting and tabular prediction, document processing — or invoke it explicitly.
- **Google Antigravity, Codex, and other `.agents/skills/`-compatible tools** — discovered from the repo-root `.agents/skills/bigquery-ai-functions/` symlink, using the same `SKILL.md` files.
- **Standalone / other repos** — the whole `agent-skills/.agents/skills/bigquery-ai-functions/` folder is self-contained and can be copied into any other project.

Not sure whether BigQuery AI Functions or [BigQuery ML](../bq-ml/) fits your task? The [`choosing-a-bigquery-ai-approach`](../../agent-skills/.agents/skills/choosing-a-bigquery-ai-approach/SKILL.md) skill triages between the two.

---

## Workflows

Workflows compose multiple AI functions together for end-to-end scenarios. See [workflows/](workflows/) for the full list.

| Workflow | Functions Used | Description |
|----------|---------------|-------------|
| [Data Enrichment](workflows/data_enrichment/) | AI.GENERATE (Google Search grounding + output_schema), AI.PREDICT | Fix misspellings and correct errors using grounded web lookups, then fill a missing structured attribute with TabFM |
| [Content Analysis Pipeline](workflows/content_analysis/) | AI.GENERATE_TABLE, AI.CLASSIFY, AI.SCORE, AI.GENERATE, AI.AGG | Generate sample data, classify it, score it, and summarize findings |
| [Semantic Search System](workflows/semantic_search/) | AI.EMBED, VECTOR_SEARCH, AI.SEARCH | Build and query a semantic search index, three ways: manual, simplified, and hybrid |
| [Catalog Search](workflows/catalog_search/) | AI.EMBED, VECTOR_SEARCH, AI.SEARCH | Hybrid retrieval over a real product catalog: what rank fusion does and does not buy you for exact-token lookups, with a corpus large enough to actually populate a vector index |
| [RAG Pipeline](workflows/rag_pipeline/) | AI.GENERATE_TABLE, AI.EMBED, VECTOR_SEARCH, AI.GENERATE | Generate a knowledge base, embed, search, answer questions |
| [Document RAG](workflows/document_rag/) ⚠️ | AI.PARSE_DOCUMENT, AI.EMBED, VECTOR_SEARCH, AI.GENERATE | Parse real documents, embed chunks, search, answer questions with grounded context. **⚠️ Blocked — depends on AI.PARSE_DOCUMENT, offline since 2026-06-01 and now with its reference docs withdrawn. Committed outputs are a pre-withdrawal record; do not re-run.** |
| [Time Series Intelligence](workflows/time_series_intelligence/) | AI.FORECAST, AI.DETECT_ANOMALIES, AI.EVALUATE, AI.KEY_DRIVERS | Forecast, detect anomalies, evaluate accuracy, explain changes by segment |
| [Zero-Shot Tabular Prediction](workflows/tabular_prediction/) | AI.PREDICT, AI.EVALUATE, AI.KEY_DRIVERS, AI.GENERATE | Zero-shot regression and classification with TabFM, scored and explained — no model training |
| [Metric Diagnostics](workflows/metric_diagnostics/) | AI.KEY_DRIVERS, AI.PREDICT, AI.GENERATE | Explain why a metric moved between two periods, project it forward, then narrate the drivers in plain language |
| [Document Intelligence](workflows/document_intelligence/) | AI.CLASSIFY, AI.GENERATE, AI.SCORE, AI.AGG | Classify mixed documents, extract key fields, score quality, summarize findings |
| [Content Moderation](workflows/content_moderation/) | AI.GENERATE_TABLE, AI.IF, AI.CLASSIFY, AI.SCORE, AI.GENERATE, AI.AGG | Flag, categorize, and score user-generated content for moderation |
| [Multimodal Analysis](workflows/multimodal_analysis/) | AI.EMBED, AI.SIMILARITY, AI.GENERATE | Embed document images, find similar documents, generate visual descriptions |
| [Log Analysis](workflows/log_analysis/) | AI.GENERATE_TABLE, AI.CLASSIFY, AI.SCORE, AI.AGG, AI.EMBED, VECTOR_SEARCH | Classify tickets, score priority, summarize patterns with AI.AGG, then retrieve by error code with hybrid search — and measure how far up the ranking a lexical hit can actually lift a row |
| [Image Deduplication](workflows/image_deduplication/) | AI.EMBED, VECTOR_SEARCH | Group near-duplicate images using embedding similarity for train/test split integrity |

---

## Function Map

Every function has two example files:
- **notebook** (`.ipynb`) — SQL, `%%bigquery` magics, and BigFrames examples in one runnable file
- **sql** (`.sql`) — standalone queries runnable directly in the BigQuery console

### Multimodal Input — Documents, Images, Audio, Video

Functions marked in the **Multimodal** column below can process files from Cloud Storage alongside text. Two mechanisms enable this:

- **ObjectRef pipeline** — Create signed references inline (no table needed): `OBJ.MAKE_REF → OBJ.FETCH_METADATA → OBJ.GET_ACCESS_URL`. Most functions accept these in a **STRUCT prompt** or as an **ObjectRef content** parameter.
- **Object tables** — External tables over Cloud Storage objects with a `ref` column. Required by some managed functions and ML.PROCESS_DOCUMENT. Best for processing many files at scale.

| Multimodal Label | How It Works |
|------------------|--------------|
| STRUCT prompt | Replace the STRING prompt with `STRUCT(text AS prompt, [refs] AS object_ref_runtime)` — works inline, no table needed |
| Object table | Query an object table with the `ref` column — function-specific syntax varies (see each notebook) |
| ObjectRef | Pass ObjectRef or ObjectRefRuntime directly as the content parameter |
| — | Text/numeric only — no unstructured data input |

See the [Unstructured Data Infrastructure](RESOURCES.md#unstructured-data-infrastructure) section in the Detailed Function Reference for the full ObjectRef pipeline, object table syntax, and schema details.

### Generation — Send prompts to GenAI models, get text or structured output

| Function | Examples | Type | Status | Requires Model | Multimodal | What It Does |
|----------|----------|------|--------|----------------|------------|--------------|
| `AI.GENERATE` | [notebook](functions/ai_generate/ai_generate.ipynb) · [sql](functions/ai_generate/ai_generate.sql) | Scalar | GA | No | STRUCT prompt | Generate text or structured output from any Gemini model. Default: `gemini-2.5-flash`. |
| `AI.GENERATE_TEXT` | [notebook](functions/ai_generate_text/ai_generate_text.ipynb) · [sql](functions/ai_generate_text/ai_generate_text.sql) | TVF | GA | Yes | STRUCT prompt | Generate text using Gemini, Claude, Llama, Mistral, or open models via a remote model. |
| `AI.GENERATE_TABLE` | [notebook](functions/ai_generate_table/ai_generate_table.ipynb) · [sql](functions/ai_generate_table/ai_generate_table.sql) | TVF | GA | Yes | STRUCT prompt | Generate structured output columns from a user-defined schema. Gemini only. |
| `AI.GENERATE_BOOL` | [notebook](functions/ai_generate_bool/ai_generate_bool.ipynb) · [sql](functions/ai_generate_bool/ai_generate_bool.sql) | Scalar | Preview | No | STRUCT prompt | Return a BOOL per row from a Gemini prompt. |
| `AI.GENERATE_DOUBLE` | [notebook](functions/ai_generate_double/ai_generate_double.ipynb) · [sql](functions/ai_generate_double/ai_generate_double.sql) | Scalar | Preview | No | STRUCT prompt | Return a FLOAT64 per row from a Gemini prompt. |
| `AI.GENERATE_INT` | [notebook](functions/ai_generate_int/ai_generate_int.ipynb) · [sql](functions/ai_generate_int/ai_generate_int.sql) | Scalar | Preview | No | STRUCT prompt | Return an INT64 per row from a Gemini prompt. |
| `ML.GENERATE_TEXT` | [notebook](functions/ml_generate_text/ml_generate_text.ipynb) · [sql](functions/ml_generate_text/ml_generate_text.sql) | TVF | GA | Yes | STRUCT prompt | Legacy predecessor to AI.GENERATE_TEXT. Use AI.GENERATE_TEXT for new work. |
| `AI.COUNT_TOKENS` | [notebook](functions/ai_count_tokens/ai_count_tokens.ipynb) · [sql](functions/ai_count_tokens/ai_count_tokens.sql) | Scalar | Preview | No | — | Utility: estimate a prompt's input token count for free (no Vertex AI charge) to size/cost prompts before generating. |

### Managed — Simplified interfaces with automatic prompt optimization

| Function | Examples | Type | Status | Returns | Multimodal | What It Does |
|----------|----------|------|--------|---------|------------|--------------|
| `AI.IF` | [notebook](functions/ai_if/ai_if.ipynb) · [sql](functions/ai_if/ai_if.sql) | Scalar | Preview | BOOL | STRUCT prompt | Evaluate a natural language condition. Optimizes query plan to reduce Gemini calls. |
| `AI.SCORE` | [notebook](functions/ai_score/ai_score.ipynb) · [sql](functions/ai_score/ai_score.sql) | Scalar | Preview | FLOAT64 | STRUCT prompt | Rate inputs on a scale you describe. Auto-generates a scoring rubric. |
| `AI.CLASSIFY` | [notebook](functions/ai_classify/ai_classify.ipynb) · [sql](functions/ai_classify/ai_classify.sql) | Scalar | Preview | STRING or ARRAY | STRUCT prompt | Classify inputs into categories you provide. Supports multi-label. |
| `AI.AGG` | [notebook](functions/ai_agg/ai_agg.ipynb) · [sql](functions/ai_agg/ai_agg.sql) | Aggregate | Preview | STRING | STRUCT input | Aggregate data with natural language instructions. Auto-batches beyond context window. |

### Embeddings & Search — Create vectors, compute similarity, search semantically

| Function | Examples | Type | Status | Requires Model | Multimodal | What It Does |
|----------|----------|------|--------|----------------|------------|--------------|
| `AI.EMBED` | [notebook](functions/ai_embed/ai_embed.ipynb) · [sql](functions/ai_embed/ai_embed.sql) | Scalar | Preview | No | ObjectRef | Create text or image embeddings. Specify endpoint directly. |
| `AI.GENERATE_EMBEDDING` | [notebook](functions/ai_generate_embedding/ai_generate_embedding.ipynb) · [sql](functions/ai_generate_embedding/ai_generate_embedding.sql) | TVF | GA | Yes | ObjectRef | Create embeddings from text, images, or video via a remote model. |
| `ML.GENERATE_EMBEDDING` | [notebook](functions/ml_generate_embedding/ml_generate_embedding.ipynb) · [sql](functions/ml_generate_embedding/ml_generate_embedding.sql) | TVF | GA | Yes | ObjectRef | Legacy predecessor to AI.GENERATE_EMBEDDING. Use AI.GENERATE_EMBEDDING for new work. |
| `AI.SIMILARITY` | [notebook](functions/ai_similarity/ai_similarity.ipynb) · [sql](functions/ai_similarity/ai_similarity.sql) | Scalar | Preview | No | ObjectRef | Cosine similarity between two inputs. Generates embeddings at runtime. |
| `VECTOR_SEARCH` | [notebook](functions/vector_search/vector_search.ipynb) · [sql](functions/vector_search/vector_search.sql) | TVF | GA (single-search/hybrid syntax Preview) | No | — | Top-K nearest neighbor search on pre-computed embeddings. Supports vector indexes and hybrid (semantic + keyword) search. |
| `AI.SEARCH` | [notebook](functions/ai_search/ai_search.ipynb) · [sql](functions/ai_search/ai_search.sql) | TVF | GA (`mode` Preview) | No | — | Semantic or hybrid search on tables with autonomous embedding generation. |

**Hybrid search is a capability, not a function.** There is no `HYBRID_SEARCH` in BigQuery SQL. Combine semantic and keyword matching either through `VECTOR_SEARCH`'s `lexical_search_columns` argument (single-query syntax only) or through `AI.SEARCH`'s `mode => 'HYBRID'`. Neither requires a vector index. In hybrid mode the returned `distance` is a reciprocal-rank-fusion score rather than a distance.

Reach for it when a query carries **both** descriptive words and an exact token — but know what it buys, because `top_k` gates it twice. First the pool: BigQuery hands the lexical leg only the top `10 * top_k` rows by semantic rank, and a row deeper than that gets no lexical rank at all, however perfectly it matches. Inside the pool the lexical leg ranks the *entire* candidate pool — BM25 matches take lexical ranks `1..m` and the remaining pooled rows fall back to their semantic order behind them — so no pooled row forfeits a term. Then the score: `distance = 1 - ( 1/(60 + rank_vector) + 1/(61 + rank_lexical) )`, where the two legs use different rank bases (60 semantic, 61 lexical), and a lexical match is worth promotion to lexical rank 1, or `1/62` ≈ `0.016` of score, which has to beat the row holding the last slot. Effective reach is the smaller of the two, `min(score gate, 10 * top_k)`: at `top_k` of 10 a matched row can come from semantic rank 23, at 30 from 110, at 50 from 468 — and from `top_k` of 51 up the pool is what binds, so 640 at 64, 1,000 at 100, 3,000 at 300. Hybrid re-ranks and widens recall in proportion to `top_k`, never unboundedly: to retrieve a row at semantic rank `R` by exact token, size `top_k` to *at least* `R/10` — that is a floor, not a recipe. Below a few hundred ranks deep the score gate is the one that binds, and it asks for more: a row at semantic rank 100 needs `top_k` = 29, not 10. Read the real number off the reach table. If an opaque identifier is *all* the user typed, use `WHERE sku = @sku` instead — a predicate cannot be outranked by a fusion score, and it has no pool. See [Hybrid Search](RESOURCES.md#hybrid-search-capability) for the measured formula, the full reach table, and the vector-index DDL rules.

**Embedding task types:** The `task_type` parameter tells the embedding model how the text will be used, which changes the resulting vector.

**Asymmetric** — embed documents and queries with different task types:

| Use Case | Embed Documents With | Embed Queries With |
|----------|---------------------|-------------------|
| Search | `RETRIEVAL_DOCUMENT` | `RETRIEVAL_QUERY` |
| Question Answering | `RETRIEVAL_DOCUMENT` | `QUESTION_ANSWERING` |
| Fact Checking | `RETRIEVAL_DOCUMENT` | `FACT_VERIFICATION` |
| Code Retrieval | `RETRIEVAL_DOCUMENT` | `CODE_RETRIEVAL_QUERY` |

**Symmetric** — use the same task type on both sides:

| Use Case | Task Type |
|----------|-----------|
| Comparing text similarity | `SEMANTIC_SIMILARITY` |
| Grouping by category | `CLASSIFICATION` |
| Organizing into clusters | `CLUSTERING` |

When unsure, default to `RETRIEVAL_DOCUMENT` / `RETRIEVAL_QUERY`. See the [`AI.EMBED` notebook](functions/ai_embed/ai_embed.ipynb) for details.

### Document Processing — Extract structured data from documents

| Function | Examples | Type | Status | Requires Model | Multimodal | What It Does |
|----------|----------|------|--------|----------------|------------|--------------|
| `ML.PROCESS_DOCUMENT` | [notebook](functions/ml_process_document/ml_process_document.ipynb) · [sql](functions/ml_process_document/ml_process_document.sql) | TVF | GA | Yes | Object table | Extract structured data from documents in Cloud Storage using Document AI processors. |
| `AI.PARSE_DOCUMENT` ⚠️ | [notebook](functions/ai_parse_document/ai_parse_document.ipynb) · [sql](functions/ai_parse_document/ai_parse_document.sql) | TVF | Preview (⚠️ **offline** since 2026-06-01; **reference docs withdrawn**) | No* | Object table | OCR + layout parsing + chunking via Document AI Layout Parser. No `CREATE MODEL` needed. **Does not execute, and its reference page now returns 404. Use `ML.PROCESS_DOCUMENT` in the meantime — see notebook.** |

### Predictive AI — Forecasting, anomaly detection, regression, classification, and evaluation

Two built-in foundation models sit behind these functions: **TimesFM** for time series and **TabFM** for tabular data. Neither requires `CREATE MODEL`, a connection, or an endpoint.

| Function | Examples | Type | Status | Model | What It Does |
|----------|----------|------|--------|-------|--------------|
| `AI.FORECAST` | [notebook](functions/ai_forecast/ai_forecast.ipynb) · [sql](functions/ai_forecast/ai_forecast.sql) | TVF | GA | TimesFM | Forecast future values. No model training required. |
| `AI.DETECT_ANOMALIES` | [notebook](functions/ai_detect_anomalies/ai_detect_anomalies.ipynb) · [sql](functions/ai_detect_anomalies/ai_detect_anomalies.sql) | TVF | GA | TimesFM | Detect anomalous data points by comparing against a forecast baseline. |
| `AI.PREDICT` | [notebook](functions/ai_predict/ai_predict.ipynb) · [sql](functions/ai_predict/ai_predict.sql) | TVF | Preview | TabFM | Zero-shot regression and classification on structured data. Pass a training table and a prediction table in one call — no training step. |
| `AI.EVALUATE` | [notebook](functions/ai_evaluate/ai_evaluate.ipynb) · [sql](functions/ai_evaluate/ai_evaluate.sql) | TVF | GA (TabFM branch Preview) | Both | Evaluate a TimesFM forecast (MAE, MSE, RMSE, MAPE, sMAPE, MASE) **or** a TabFM prediction (regression or classification metrics). |

> **Default model version changed.** The three TimesFM functions now default to **TimesFM 2.5** instead of TimesFM 2.0, with no release note announcing it. Unpinned queries silently return different numbers than they used to — pin `model` explicitly if you need reproducibility.

### Augmented Analytics — Find what drives metric changes

| Function | Examples | Type | Status | Multimodal | What It Does |
|----------|----------|------|--------|------------|--------------|
| `AI.KEY_DRIVERS` | [notebook](functions/ai_key_drivers/ai_key_drivers.ipynb) · [sql](functions/ai_key_drivers/ai_key_drivers.sql) | TVF | Preview | — | Key driver / contribution analysis — find the segments that drive a metric change between an interest and reference set. No model or connection. |

---

## How Functions Relate

```
                        ┌─────────────────────────────────────────────┐
                        │           GENERATION                        │
                        │                                             │
                        │  AI.GENERATE ◄── simplest, no model needed  │
                        │       │                                     │
                        │       ├── AI.GENERATE_BOOL (typed: BOOL)    │
                        │       ├── AI.GENERATE_DOUBLE (typed: FLOAT) │
                        │       └── AI.GENERATE_INT (typed: INT)      │
                        │                                             │
                        │  AI.GENERATE_TEXT ◄── needs CREATE MODEL    │
                        │       │                multi-provider       │
                        │       └── ML.GENERATE_TEXT (legacy naming)  │
                        │                                             │
                        │  AI.COUNT_TOKENS ◄── utility: free input    │
                        │       token count to size/cost prompts      │
                        │                                             │
                        │  AI.GENERATE_TABLE ◄── structured output   │
                        │       (also used to generate sample data)   │
                        └─────────────────────────────────────────────┘

┌──────────────────────────┐   ┌──────────────────────────────────────┐
│     MANAGED              │   │     EMBEDDINGS & SEARCH              │
│                          │   │                                      │
│  AI.IF ──── like         │   │  AI.EMBED ◄── scalar, no model      │
│       AI.GENERATE_BOOL   │   │       │                              │
│       but auto-optimized │   │  AI.GENERATE_EMBEDDING ◄── TVF      │
│                          │   │       │                              │
│  AI.SCORE ── like        │   │       └── ML.GENERATE_EMBEDDING     │
│       AI.GENERATE_DOUBLE │   │              (legacy naming)         │
│       but auto-rubric    │   │                                      │
│                          │   │  AI.SIMILARITY ◄── compare 2 inputs  │
│  AI.CLASSIFY ── unique   │   │                                      │
│       categories input   │   │  VECTOR_SEARCH ◄── top-K search     │
│                          │   │       pre-computed embeddings         │
│  AI.AGG ──── aggregate   │   │                                      │
│       summarize groups   │   │                                      │
│       auto-batches       │   │                                      │
│                          │   │                                      │
└──────────────────────────┘   │                                      │
                               │  AI.SEARCH ◄── simplified search     │
┌──────────────────────────┐   │       needs autonomous embedding     │
│     PREDICTIVE AI        │   │                                      │
│                          │   │  Hybrid search = semantic +          │
│  TimesFM - time series:  │   │       keyword. A capability of       │
│  AI.FORECAST             │   │       both search functions above,   │
│       │                  │   │       not a separate function.       │
│  AI.DETECT_ANOMALIES     │   └──────────────────────────────────────┘
│                          │
│  TabFM - tabular:        │   ┌──────────────────────────────────────┐
│  AI.PREDICT              │   │     DOCUMENT PROCESSING              │
│       zero-shot, no      │   │                                      │
│       CREATE MODEL       │   │  ML.PROCESS_DOCUMENT                 │
│                          │   │       needs object table +           │
│  AI.EVALUATE ◄── scores  │   │       Document AI processor          │
│       either family      │   │       + remote model                 │
│                          │   │                                      │
│  No model creation needed│   │  AI.PARSE_DOCUMENT ◄── simplified    │
└──────────────────────────┘   │       needs Layout Parser processor  │
                               │       but no CREATE MODEL step       │
┌──────────────────────────┐   │       (offline; docs withdrawn)      │
│   AUGMENTED ANALYTICS    │   └──────────────────────────────────────┘
│                          │
│  AI.KEY_DRIVERS          │
│       contribution /     │
│       key driver analysis│
│  No model / no connection│
└──────────────────────────┘
```

**Key distinctions:**
- **Scalar functions** (AI.GENERATE, AI.IF, AI.EMBED, etc.) operate on individual values — use them in SELECT, WHERE, JOIN.
- **Aggregate functions** (AI.AGG) operate across groups of rows — use with GROUP BY, like SUM or COUNT.
- **Table-valued functions** (AI.GENERATE_TEXT, VECTOR_SEARCH, AI.FORECAST, AI.PREDICT, etc.) operate on tables — use them in FROM.
- **"No model needed"** functions specify an endpoint directly or use a built-in model. **"Requires model"** functions need a `CREATE MODEL` statement first. See [Setup Reference](setup/) for details.
- **Multimodal functions** process documents, images, audio, or video from Cloud Storage. Input methods vary by function — see the [Multimodal Input](#multimodal-input--documents-images-audio-video) section above.

---

## Project Structure

```
bq-ai-functions/
├── README.md               ◄ You are here
├── RESOURCES.md             ◄ Detailed function reference
├── overview.ipynb           ◄ Interactive overview notebook
├── setup/                   ◄ Connections, models, quotas reference
├── functions/               ◄ Per-function deep dives (SQL + notebook)
│   ├── ai_generate/
│   ├── ai_generate_text/
│   ├── ai_generate_table/
│   ├── ai_count_tokens/
│   ├── ai_if/
│   ├── ai_score/
│   ├── ai_classify/
│   ├── ai_agg/
│   ├── ai_embed/
│   ├── ai_generate_embedding/
│   ├── vector_search/
│   ├── ai_search/
│   ├── ai_forecast/
│   ├── ai_detect_anomalies/
│   ├── ai_predict/
│   ├── ai_evaluate/
│   ├── ai_key_drivers/
│   ├── ml_process_document/
│   ├── ai_parse_document/
│   └── ... (+ legacy/variant functions)
└── workflows/               ◄ End-to-end composed workflows
    ├── data_enrichment/
    ├── document_rag/
    ├── content_analysis/
    ├── semantic_search/
    ├── catalog_search/
    ├── rag_pipeline/
    ├── metric_diagnostics/
    ├── tabular_prediction/
    ├── time_series_intelligence/
    ├── document_intelligence/
    ├── content_moderation/
    ├── multimodal_analysis/
    ├── log_analysis/
    └── image_deduplication/
```
