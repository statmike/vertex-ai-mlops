# Composed Workflows in BigQuery AI Functions

Individual functions rarely answer a real business question alone. These 12 workflows compose several functions into a genuine end-to-end task — use them as worked patterns to copy from, not just a function catalog.

| Workflow | Functions used | What it does |
|---|---|---|
| `data_enrichment` | `AI.GENERATE` (Google Search grounding + `output_schema`) | Fix misspellings, fill missing fields, and correct errors using grounded web lookups. |
| `content_analysis` | `AI.GENERATE_TABLE`, `AI.CLASSIFY`, `AI.SCORE`, `AI.GENERATE`, `AI.AGG` | Generate sample data, classify it, score it, and summarize findings — a good template for any "classify then score then summarize" pipeline. |
| `semantic_search` | `AI.EMBED`, `VECTOR_SEARCH`, `AI.SEARCH` | Build and query a semantic search index. |
| `rag_pipeline` | `AI.GENERATE_TABLE`, `AI.EMBED`, `VECTOR_SEARCH`, `AI.GENERATE` | Generate a knowledge base, embed it, search it, answer questions grounded in the retrieved context. |
| `document_rag` | `AI.PARSE_DOCUMENT`, `AI.EMBED`, `VECTOR_SEARCH`, `AI.GENERATE` | Parse real documents, embed chunks, search, answer questions with grounded context. **Currently blocked** — depends on `AI.PARSE_DOCUMENT`, which is offline for revision (see `document-processing.md`). |
| `time_series_intelligence` | `AI.FORECAST`, `AI.DETECT_ANOMALIES`, `AI.EVALUATE`, `AI.KEY_DRIVERS` | Forecast a series, detect anomalies in it, evaluate forecast accuracy, then explain movement by segment — the single most complete tour of the forecasting/anomaly/driver functions together. |
| `metric_diagnostics` | `AI.KEY_DRIVERS`, `AI.GENERATE` | Explain why a metric moved between two periods, then narrate the drivers in plain language — pairs a structured analysis function with a generation function for a readable output. |
| `document_intelligence` | `AI.CLASSIFY`, `AI.GENERATE`, `AI.SCORE`, `AI.AGG` | Classify mixed documents, extract key fields, score quality, summarize findings. |
| `content_moderation` | `AI.GENERATE_TABLE`, `AI.IF`, `AI.CLASSIFY`, `AI.SCORE`, `AI.GENERATE`, `AI.AGG` | Flag, categorize, and score user-generated content — the broadest single-workflow tour of the managed functions. |
| `multimodal_analysis` | `AI.EMBED`, `AI.SIMILARITY`, `AI.GENERATE` | Embed document images, find similar documents, generate visual descriptions. |
| `log_analysis` | `AI.GENERATE_TABLE`, `AI.CLASSIFY`, `AI.SCORE`, `AI.AGG` | Classify tickets, score priority, summarize patterns — a support/ops-triage template. |
| `image_deduplication` | `AI.EMBED`, `VECTOR_SEARCH` | Group near-duplicate images using embedding similarity, e.g. to protect train/test split integrity. |

## Choosing a starting template

- **Need to classify + score + summarize unstructured records at volume** (tickets, documents, user content) → `content_analysis`, `document_intelligence`, `content_moderation`, or `log_analysis` — pick by how many of the managed functions (`AI.CLASSIFY`/`AI.SCORE`/`AI.IF`/`AI.AGG`) you need together; `content_moderation` is the most complete template.
- **Need to answer questions grounded in your own data** → `rag_pipeline` (text) or `document_rag` (real documents — currently blocked, see above).
- **Need to find similar items** (text, images, documents) → `semantic_search` or `image_deduplication` depending on whether you need a queryable index or a one-off grouping pass.
- **Need to explain a metric or forecast something over time** → `time_series_intelligence` (the full forecast/anomaly/evaluate/drivers tour) or `metric_diagnostics` (just drivers + narration, lighter weight).
- **Need to enrich/clean records against external knowledge** → `data_enrichment` (Google Search grounding pattern).
- **Working with images/visual content specifically** → `multimodal_analysis`.

## Go deeper

Full extracted notebook walkthroughs live in this skill's `narrative/` folder:

- [`narrative/content_analysis.md`](../narrative/content_analysis.md) (source: `workflows/content_analysis/`)
- [`narrative/content_moderation.md`](../narrative/content_moderation.md) (source: `workflows/content_moderation/`)
- [`narrative/data_enrichment.md`](../narrative/data_enrichment.md) (source: `workflows/data_enrichment/`)
- [`narrative/document_intelligence.md`](../narrative/document_intelligence.md) (source: `workflows/document_intelligence/`)
- [`narrative/document_rag.md`](../narrative/document_rag.md) (source: `workflows/document_rag/`) — currently blocked on the AI.PARSE_DOCUMENT outage
- [`narrative/image_deduplication.md`](../narrative/image_deduplication.md) (source: `workflows/image_deduplication/`)
- [`narrative/log_analysis.md`](../narrative/log_analysis.md) (source: `workflows/log_analysis/`)
- [`narrative/metric_diagnostics.md`](../narrative/metric_diagnostics.md) (source: `workflows/metric_diagnostics/`)
- [`narrative/multimodal_analysis.md`](../narrative/multimodal_analysis.md) (source: `workflows/multimodal_analysis/`)
- [`narrative/rag_pipeline.md`](../narrative/rag_pipeline.md) (source: `workflows/rag_pipeline/`)
- [`narrative/semantic_search.md`](../narrative/semantic_search.md) (source: `workflows/semantic_search/`)
- [`narrative/time_series_intelligence.md`](../narrative/time_series_intelligence.md) (source: `workflows/time_series_intelligence/`)

Full function-to-workflow map and "How Functions Relate" diagram: see the README in the source repo (`bq-ai-functions/README.md`).
