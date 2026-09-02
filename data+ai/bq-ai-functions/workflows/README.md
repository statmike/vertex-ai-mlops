![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2Fdata%2Bai%2Fbq-ai-functions%2Fworkflows&file=README.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/data%2Bai/bq-ai-functions/workflows/README.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-ai-functions/workflows/README.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-ai-functions/workflows/README.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-ai-functions/workflows/README.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-ai-functions/workflows/README.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
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
# BigQuery AI Functions — Workflows

Workflows are the graduation content of this project. Each one is a single runnable notebook that composes several AI functions into an end-to-end scenario, generates or loads its own data, and cleans up after itself.

Work through [the individual function notebooks](../functions/) first. A workflow assumes you already know what each function does on its own; its job is to show how they fit together and where the seams are.

**Parent:** [BigQuery AI Functions](../) · [Detailed Function Reference](../RESOURCES.md) · [Interactive Overview](../overview.ipynb)

---

## The workflows

### Search and retrieval

| Workflow | Functions Used | What It Shows |
|----------|---------------|---------------|
| [Semantic Search System](semantic_search/) | AI.EMBED, VECTOR_SEARCH, AI.SEARCH | The same search index built three ways — manual, simplified, and hybrid — so you can see what each layer of convenience costs you |
| [Catalog Search](catalog_search/) | AI.EMBED, VECTOR_SEARCH, AI.SEARCH | Hybrid retrieval over a real product catalog: what rank fusion buys for an exact-token lookup and what it does not, plus a corpus large enough to actually populate a vector index |
| [RAG Pipeline](rag_pipeline/) | AI.GENERATE_TABLE, AI.EMBED, VECTOR_SEARCH, AI.GENERATE | Generate a knowledge base, embed it, retrieve against it, and answer questions with the retrieved context |
| [Document RAG](document_rag/) ⚠️ | AI.PARSE_DOCUMENT, AI.EMBED, VECTOR_SEARCH, AI.GENERATE | The same pipeline over real PDFs. **Blocked** — see the note below |
| [Image Deduplication](image_deduplication/) | AI.EMBED, VECTOR_SEARCH | Grouping near-duplicate images by embedding similarity to keep train/test splits honest |

### Prediction and diagnosis

| Workflow | Functions Used | What It Shows |
|----------|---------------|---------------|
| [Time Series Intelligence](time_series_intelligence/) | AI.FORECAST, AI.DETECT_ANOMALIES, AI.EVALUATE, AI.KEY_DRIVERS | Forecast, flag anomalies, score the forecast, and explain a shift by segment |
| [Zero-Shot Tabular Prediction](tabular_prediction/) | AI.PREDICT, AI.EVALUATE, AI.KEY_DRIVERS, AI.GENERATE | Zero-shot regression and classification with TabFM — no training step — then scored, explained, and written up |
| [Metric Diagnostics](metric_diagnostics/) | AI.KEY_DRIVERS, AI.PREDICT, AI.GENERATE | Why a metric moved between two periods, where it projects next, and a plain-language narration of both |

### Classification, scoring, and summarization

| Workflow | Functions Used | What It Shows |
|----------|---------------|---------------|
| [Content Analysis Pipeline](content_analysis/) | AI.GENERATE_TABLE, AI.CLASSIFY, AI.SCORE, AI.GENERATE, AI.AGG | The canonical generate → classify → score → summarize chain |
| [Content Moderation](content_moderation/) | AI.GENERATE_TABLE, AI.IF, AI.CLASSIFY, AI.SCORE, AI.GENERATE, AI.AGG | Flagging as a cheap first pass before the expensive per-row calls |
| [Log Analysis](log_analysis/) | AI.GENERATE_TABLE, AI.CLASSIFY, AI.SCORE, AI.AGG, AI.EMBED, VECTOR_SEARCH | Triaging support tickets, plus hybrid retrieval by error code — and the clearest measurement of how far up the ranking a lexical hit can lift a row, and why `top_k` decides whether you ever see it |
| [Document Intelligence](document_intelligence/) | AI.CLASSIFY, AI.GENERATE, AI.SCORE, AI.AGG | Classify mixed documents, extract fields, score quality, summarize |

### Enrichment and multimodal

| Workflow | Functions Used | What It Shows |
|----------|---------------|---------------|
| [Data Enrichment](data_enrichment/) | AI.GENERATE (Google Search grounding + output_schema), AI.PREDICT | Two ways to fill a gap: retrieve the answer from the web, or infer it from the rows you already have |
| [Multimodal Analysis](multimodal_analysis/) | AI.EMBED, AI.SIMILARITY, AI.GENERATE | Embedding document images, finding near matches, and describing them |

---

## Before you run one

- **One notebook at a time.** Every workflow writes into the same `bq_ai_functions` dataset and they share a virtual environment. Running two concurrently will collide on both.
- **They create real resources and real charges.** Each notebook ends with a cleanup section that drops what it made. Shared resources — the dataset, connections, remote models — are deliberately left in place for the next notebook.
- **Restart & Run All is the intended way to run them.** Committed outputs are a record of a full clean pass; partial re-runs of individual cells can leave a notebook in a state its narration does not describe.
- **⚠️ Document RAG does not run.** It depends on `AI.PARSE_DOCUMENT`, which Google took offline on 2026-06-01 and whose reference documentation has since been withdrawn entirely. Its committed outputs are a record of the workflow working before the withdrawal. Use [`ML.PROCESS_DOCUMENT`](../functions/ml_process_document/) for document extraction in the meantime.

---

## Conventions every workflow follows

- **Self-contained data.** A workflow either generates its own sample data with `AI.GENERATE_TABLE`/inline SQL or reads from `bigquery-public-data`. Nothing depends on another notebook having run first.
- **Named tables.** Tables use a `workflow_{short}_{stage}` prefix so it is obvious what created them and at what point in the pipeline.
- **A `**Functions used:**` line** in the overview cell, linking each function back to its deep-dive notebook. Every function named there must also name this workflow in its own `**Featured in:**` line — the cross-references are required to be bidirectional, and the round-trip check is a step on the "New workflow" checklist in [PLANS.md](../PLANS.md) rather than something to remember by hand.
- **A closing comparison table** where the workflow demonstrates more than one approach, always ending with a `**Best for**` row.

Adding a workflow? The checklist lives in [PLANS.md](../PLANS.md) under "New workflow".
