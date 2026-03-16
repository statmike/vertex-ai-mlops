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
</table><br/><br/>

---
# BigQuery AI Functions

Use generative AI, embeddings, semantic search, forecasting, and anomaly detection directly in BigQuery SQL — no ML infrastructure to manage.

This project provides a progressive learning system: start with a quick overview of all available functions, drill into individual functions with hands-on examples (SQL, `%%bigquery` magics, and BigFrames), then compose functions together in end-to-end workflows.

## Start Here

| Resource | Description |
|----------|-------------|
| [Interactive Overview](overview.ipynb) | Runnable notebook tour — one example per category |
| [Setup Reference](setup/) | Connections, models, endpoints, quotas, and permissions |
| [Detailed Function Reference](RESOURCES.md) | Complete syntax, inputs, outputs, and limitations for every function |

---

## Workflows

Workflows compose multiple AI functions together for end-to-end scenarios. See [workflows/](workflows/) for the full list.

| Workflow | Functions Used | Description |
|----------|---------------|-------------|
| [Data Enrichment](workflows/data_enrichment/) | AI.GENERATE (Google Search grounding + output_schema) | Fix misspellings, fill missing fields, and correct errors using grounded web lookups |
| [Content Analysis Pipeline](workflows/content_analysis/) | AI.GENERATE_TABLE, AI.CLASSIFY, AI.SCORE, AI.GENERATE | Generate sample data, classify it, score it, and summarize findings |
| [Semantic Search System](workflows/semantic_search/) | AI.EMBED, VECTOR_SEARCH, AI.SEARCH | Build and query a semantic search index |
| [RAG Pipeline](workflows/rag_pipeline/) | AI.GENERATE_TABLE, AI.EMBED, VECTOR_SEARCH, AI.GENERATE | Generate a knowledge base, embed, search, answer questions |
| [Time Series Intelligence](workflows/time_series_intelligence/) | AI.FORECAST, AI.DETECT_ANOMALIES, AI.EVALUATE | Forecast, detect anomalies, evaluate accuracy |
| [Document Intelligence](workflows/document_intelligence/) | AI.CLASSIFY, AI.GENERATE, AI.SCORE | Classify mixed documents, extract key fields, score quality, summarize findings |
| [Content Moderation](workflows/content_moderation/) | AI.GENERATE_TABLE, AI.IF, AI.CLASSIFY, AI.SCORE, AI.GENERATE | Flag, categorize, and score user-generated content for moderation |
| [Multimodal Analysis](workflows/multimodal_analysis/) | AI.EMBED, AI.SIMILARITY, AI.GENERATE | Embed document images, find similar documents, generate visual descriptions |

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

### Managed — Simplified interfaces with automatic prompt optimization

| Function | Examples | Type | Status | Returns | Multimodal | What It Does |
|----------|----------|------|--------|---------|------------|--------------|
| `AI.IF` | [notebook](functions/ai_if/ai_if.ipynb) · [sql](functions/ai_if/ai_if.sql) | Scalar | Preview | BOOL | STRUCT prompt | Evaluate a natural language condition. Optimizes query plan to reduce Gemini calls. |
| `AI.SCORE` | [notebook](functions/ai_score/ai_score.ipynb) · [sql](functions/ai_score/ai_score.sql) | Scalar | Preview | FLOAT64 | STRUCT prompt | Rate inputs on a scale you describe. Auto-generates a scoring rubric. |
| `AI.CLASSIFY` | [notebook](functions/ai_classify/ai_classify.ipynb) · [sql](functions/ai_classify/ai_classify.sql) | Scalar | Preview | STRING or ARRAY | STRUCT prompt | Classify inputs into categories you provide. Supports multi-label. |

### Embeddings & Search — Create vectors, compute similarity, search semantically

| Function | Examples | Type | Status | Requires Model | Multimodal | What It Does |
|----------|----------|------|--------|----------------|------------|--------------|
| `AI.EMBED` | [notebook](functions/ai_embed/ai_embed.ipynb) · [sql](functions/ai_embed/ai_embed.sql) | Scalar | Preview | No | ObjectRef | Create text or image embeddings. Specify endpoint directly. |
| `AI.GENERATE_EMBEDDING` | [notebook](functions/ai_generate_embedding/ai_generate_embedding.ipynb) · [sql](functions/ai_generate_embedding/ai_generate_embedding.sql) | TVF | GA | Yes | ObjectRef | Create embeddings from text, images, or video via a remote model. |
| `ML.GENERATE_EMBEDDING` | [notebook](functions/ml_generate_embedding/ml_generate_embedding.ipynb) · [sql](functions/ml_generate_embedding/ml_generate_embedding.sql) | TVF | GA | Yes | ObjectRef | Legacy predecessor to AI.GENERATE_EMBEDDING. Use AI.GENERATE_EMBEDDING for new work. |
| `AI.SIMILARITY` | [notebook](functions/ai_similarity/ai_similarity.ipynb) · [sql](functions/ai_similarity/ai_similarity.sql) | Scalar | Preview | No | ObjectRef | Cosine similarity between two inputs. Generates embeddings at runtime. |
| `VECTOR_SEARCH` | [notebook](functions/vector_search/vector_search.ipynb) · [sql](functions/vector_search/vector_search.sql) | TVF | GA | No | — | Top-K nearest neighbor search on pre-computed embeddings. Supports vector indexes. |
| `AI.SEARCH` | [notebook](functions/ai_search/ai_search.ipynb) · [sql](functions/ai_search/ai_search.sql) | TVF | Preview | No | — | Semantic search on tables with autonomous embedding generation. |

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

### Forecasting — Time series forecasting, anomaly detection, and evaluation

| Function | Examples | Type | Status | Multimodal | What It Does |
|----------|----------|------|--------|------------|--------------|
| `AI.FORECAST` | [notebook](functions/ai_forecast/ai_forecast.ipynb) · [sql](functions/ai_forecast/ai_forecast.sql) | TVF | GA | — | Forecast future values with TimesFM. No model training required. |
| `AI.DETECT_ANOMALIES` | [notebook](functions/ai_detect_anomalies/ai_detect_anomalies.ipynb) · [sql](functions/ai_detect_anomalies/ai_detect_anomalies.sql) | TVF | Preview | — | Detect anomalous data points by comparing against a forecast baseline. |
| `AI.EVALUATE` | [notebook](functions/ai_evaluate/ai_evaluate.ipynb) · [sql](functions/ai_evaluate/ai_evaluate.sql) | TVF | GA | — | Evaluate forecast accuracy (MAE, MSE, RMSE, MAPE, sMAPE). |

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
└──────────────────────────┘   │                                      │
                               │  AI.SEARCH ◄── simplified search     │
┌──────────────────────────┐   │       needs autonomous embedding     │
│     FORECASTING          │   └──────────────────────────────────────┘
│                          │
│  AI.FORECAST             │   ┌──────────────────────────────────────┐
│       │                  │   │     DOCUMENT PROCESSING              │
│  AI.DETECT_ANOMALIES     │   │                                      │
│       │                  │   │  ML.PROCESS_DOCUMENT                 │
│  AI.EVALUATE             │   │       needs object table +           │
│                          │   │       Document AI processor           │
│  All use TimesFM         │   │       + remote model                  │
│  No model creation needed│   │                                      │
└──────────────────────────┘   └──────────────────────────────────────┘
```

**Key distinctions:**
- **Scalar functions** (AI.GENERATE, AI.IF, AI.EMBED, etc.) operate on individual values — use them in SELECT, WHERE, JOIN.
- **Table-valued functions** (AI.GENERATE_TEXT, VECTOR_SEARCH, AI.FORECAST, etc.) operate on tables — use them in FROM.
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
│   ├── ai_if/
│   ├── ai_score/
│   ├── ai_classify/
│   ├── ai_embed/
│   ├── ai_generate_embedding/
│   ├── vector_search/
│   ├── ai_search/
│   ├── ai_forecast/
│   ├── ai_detect_anomalies/
│   ├── ai_evaluate/
│   ├── ml_process_document/
│   └── ... (+ legacy/variant functions)
└── workflows/               ◄ End-to-end composed workflows
    ├── data_enrichment/
    ├── content_analysis/
    ├── semantic_search/
    ├── rag_pipeline/
    ├── time_series_intelligence/
    ├── document_intelligence/
    ├── content_moderation/
    └── multimodal_analysis/
```
