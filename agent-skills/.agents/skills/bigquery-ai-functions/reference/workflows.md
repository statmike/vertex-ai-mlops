# Composed Workflows in BigQuery AI Functions

Individual functions rarely answer a real business question alone. These 14 workflows compose several functions into a genuine end-to-end task — use them as worked patterns to copy from, not just a function catalog.

| Workflow | Functions used | What it does |
|---|---|---|
| `data_enrichment` | `AI.GENERATE` (Google Search grounding + `output_schema`), `AI.PREDICT` | Fill gaps two ways: retrieve the answer from the web, or infer it from the rows you already have. A direct contrast between grounded generation and zero-shot tabular inference. |
| `content_analysis` | `AI.GENERATE_TABLE`, `AI.CLASSIFY`, `AI.SCORE`, `AI.GENERATE`, `AI.AGG` | Generate sample data, classify it, score it, and summarize findings — a good template for any "classify then score then summarize" pipeline. |
| `semantic_search` | `AI.EMBED`, `VECTOR_SEARCH`, `AI.SEARCH` | Build and query a semantic search index three ways — manual, simplified, and hybrid — to see what each layer of convenience costs. |
| `catalog_search` | `AI.EMBED`, `VECTOR_SEARCH`, `AI.SEARCH` | Hybrid retrieval over a real ~7,275-row product catalog: what rank fusion buys for an exact-token lookup and what it does not, plus a corpus large enough to actually populate a vector index. The clearest demonstration that a bare SKU is not retrievable at the small `top_k` these demos use — its row sits at semantic rank 2,072, outside the `10 * top_k` lexical candidate pool until `top_k >= 208` — while the same SKU alongside descriptive words surfaces either way. |
| `rag_pipeline` | `AI.GENERATE_TABLE`, `AI.EMBED`, `VECTOR_SEARCH`, `AI.GENERATE` | Generate a knowledge base, embed it, search it (semantic and hybrid), answer questions grounded in the retrieved context. |
| `tabular_prediction` | `AI.PREDICT`, `AI.EVALUATE`, `AI.KEY_DRIVERS`, `AI.GENERATE` | Zero-shot regression and classification with TabFM — no training step — then scored, explained by driver, and written up as a model card. Includes a head-to-head against trained BigQuery ML models. |
| `document_rag` | `AI.PARSE_DOCUMENT`, `AI.EMBED`, `VECTOR_SEARCH`, `AI.GENERATE` | Parse real documents, embed chunks, search, answer questions with grounded context. **Currently blocked** — depends on `AI.PARSE_DOCUMENT`, which is offline for revision (see `document-processing.md`). |
| `time_series_intelligence` | `AI.FORECAST`, `AI.DETECT_ANOMALIES`, `AI.EVALUATE`, `AI.KEY_DRIVERS` | Forecast a series, detect anomalies in it, evaluate forecast accuracy, then explain movement by segment — the single most complete tour of the forecasting/anomaly/driver functions together. |
| `metric_diagnostics` | `AI.KEY_DRIVERS`, `AI.PREDICT`, `AI.GENERATE` | Explain why a metric moved between two periods, project where it goes next, then narrate both in plain language — pairs structured analysis and zero-shot prediction with a generation function for a readable output. |
| `document_intelligence` | `AI.CLASSIFY`, `AI.GENERATE`, `AI.SCORE`, `AI.AGG` | Classify mixed documents, extract key fields, score quality, summarize findings. |
| `content_moderation` | `AI.GENERATE_TABLE`, `AI.IF`, `AI.CLASSIFY`, `AI.SCORE`, `AI.GENERATE`, `AI.AGG` | Flag, categorize, and score user-generated content — the broadest single-workflow tour of the managed functions. |
| `multimodal_analysis` | `AI.EMBED`, `AI.SIMILARITY`, `AI.GENERATE` | Embed document images, find similar documents, generate visual descriptions. |
| `log_analysis` | `AI.GENERATE_TABLE`, `AI.CLASSIFY`, `AI.SCORE`, `AI.AGG`, `AI.EMBED`, `VECTOR_SEARCH` | Classify tickets, score priority, summarize patterns, then retrieve by error code with hybrid search — a support/ops-triage template, and the sub-project's clearest measurement of how far up the ranking a lexical hit can lift a row (vector rank 24 of 30 → fused position 11) and why `top_k` decides whether you ever see it. |
| `image_deduplication` | `AI.EMBED`, `VECTOR_SEARCH` | Group near-duplicate images using embedding similarity, e.g. to protect train/test split integrity. |

## Choosing a starting template

- **Need to classify + score + summarize unstructured records at volume** (tickets, documents, user content) → `content_analysis`, `document_intelligence`, `content_moderation`, or `log_analysis` — pick by how many of the managed functions (`AI.CLASSIFY`/`AI.SCORE`/`AI.IF`/`AI.AGG`) you need together; `content_moderation` is the most complete template.
- **Need to answer questions grounded in your own data** → `rag_pipeline` (text) or `document_rag` (real documents — currently blocked, see above).
- **Need to find similar items** (text, images, documents) → `semantic_search` or `image_deduplication` depending on whether you need a queryable index or a one-off grouping pass.
- **Need search that weighs exact tokens** (SKUs, error codes, part numbers) → `catalog_search` for the full hybrid treatment on a real corpus with a vector index, or `log_analysis`'s Step 5 for the compact version. `semantic_search` shows hybrid alongside the two semantic-only approaches for contrast. **Set expectations first:** hybrid re-ranks and modestly widens, and `top_k` decides how far — a lexical hit reaches 10 semantic ranks deep at `top_k => 5`, 110 at `top_k => 30`, and 640 at `top_k => 64`. Two gates set that reach and effective reach is `min( score gate, 10 * top_k )`: the fused score has to beat the last slot on the page, which is what binds at `top_k` below 51, and BigQuery only pools the top `10 * top_k` rows for the lexical leg, which is what binds from 51 up. So it pays off when the query carries descriptive words *alongside* the token, and exact-token retrieval for a target at semantic rank `R` needs `top_k` of **at least** `R/10` — a floor, not a recipe, since below a few hundred ranks deep the score gate demands considerably more (a target at rank 100 needs `top_k` near 29, not 10). Read the reach table for the number that actually applies. When the token is the entire query and the answer must be certain, point the user at a `WHERE` predicate instead — `catalog_search` demonstrates exactly that trade-off. See `reference/embeddings-and-search.md` for the arithmetic and the reach table.
- **Need to predict a value or category from structured rows with no training** → `tabular_prediction` (the full TabFM tour: predict, score, explain, narrate) or `metric_diagnostics` (drivers + a lighter projection).
- **Need to explain a metric or forecast something over time** → `time_series_intelligence` (the full forecast/anomaly/evaluate/drivers tour) or `metric_diagnostics` (drivers + narration, lighter weight).
- **Need to enrich/clean records against external knowledge** → `data_enrichment`, which contrasts the Google Search grounding pattern against zero-shot tabular inference for the same gap.
- **Working with images/visual content specifically** → `multimodal_analysis`.

## Go deeper

Full extracted notebook walkthroughs live in this skill's `narrative/` folder:

- [`narrative/catalog_search.md`](../narrative/catalog_search.md) (source: `workflows/catalog_search/`)
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
- [`narrative/tabular_prediction.md`](../narrative/tabular_prediction.md) (source: `workflows/tabular_prediction/`)
- [`narrative/time_series_intelligence.md`](../narrative/time_series_intelligence.md) (source: `workflows/time_series_intelligence/`)

Full function-to-workflow map and "How Functions Relate" diagram: see the README in the source repo (`bq-ai-functions/README.md`).
