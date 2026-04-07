# Shareable Blurb

Copy/paste for internal chats, LinkedIn, X, etc. Adjust tone and length as needed.

---

## Short (chat / X)

BigQuery has 21 AI functions that let you call Gemini directly from SQL — classify, score, generate, embed, search, forecast, and more. I built a hands-on repo to help you learn, demo, or jumpstart a POC. Progressive examples for every function + end-to-end workflows you can run immediately.

Check it out: https://github.com/statmike/vertex-ai-mlops/tree/main/data%2Bai/bq-ai-functions

---

## Medium (LinkedIn / internal post)

**BigQuery AI Functions — Learn, Demo, and Get Started**

BigQuery now has 21 AI functions that bring Gemini directly into SQL. No endpoints to deploy, no pipelines to build — just SQL.

Whether you're learning these functions for the first time, building a demo, or kickstarting a POC/MVP, I put together a hands-on resource that covers every function with progressive examples — from simplest possible call to production-ready patterns:

**Functions (21 notebooks + SQL files):**
- [AI.GENERATE](https://github.com/statmike/vertex-ai-mlops/tree/main/data%2Bai/bq-ai-functions/functions/ai_generate) — free-form text generation
- [AI.CLASSIFY](https://github.com/statmike/vertex-ai-mlops/tree/main/data%2Bai/bq-ai-functions/functions/ai_classify) — categorize into labels
- [AI.SCORE](https://github.com/statmike/vertex-ai-mlops/tree/main/data%2Bai/bq-ai-functions/functions/ai_score) — numeric scoring with natural language
- [AI.AGG](https://github.com/statmike/vertex-ai-mlops/tree/main/data%2Bai/bq-ai-functions/functions/ai_agg) — aggregate with GROUP BY using Gemini (new!)
- [AI.IF](https://github.com/statmike/vertex-ai-mlops/tree/main/data%2Bai/bq-ai-functions/functions/ai_if) — yes/no decisions
- [AI.GENERATE_TABLE](https://github.com/statmike/vertex-ai-mlops/tree/main/data%2Bai/bq-ai-functions/functions/ai_generate_table) — structured output as rows
- [AI.SEARCH](https://github.com/statmike/vertex-ai-mlops/tree/main/data%2Bai/bq-ai-functions/functions/ai_search) — semantic search
- [AI.FORECAST / AI.DETECT_ANOMALIES](https://github.com/statmike/vertex-ai-mlops/tree/main/data%2Bai/bq-ai-functions/functions/ai_forecast) — time series intelligence
- ...and 12 more

**End-to-end workflows that compose multiple functions:**
- [Content Analysis](https://github.com/statmike/vertex-ai-mlops/tree/main/data%2Bai/bq-ai-functions/workflows/content_analysis) — generate + classify + score + summarize
- [Content Moderation](https://github.com/statmike/vertex-ai-mlops/tree/main/data%2Bai/bq-ai-functions/workflows/content_moderation) — flag + classify + score + summarize
- [Document Intelligence](https://github.com/statmike/vertex-ai-mlops/tree/main/data%2Bai/bq-ai-functions/workflows/document_intelligence) — classify + extract + score PDFs
- [Log Analysis](https://github.com/statmike/vertex-ai-mlops/tree/main/data%2Bai/bq-ai-functions/workflows/log_analysis) — generate + classify + score + aggregate (new!)
- [Semantic Search](https://github.com/statmike/vertex-ai-mlops/tree/main/data%2Bai/bq-ai-functions/workflows/semantic_search) — embed + vector search
- [RAG Pipeline](https://github.com/statmike/vertex-ai-mlops/tree/main/data%2Bai/bq-ai-functions/workflows/rag_pipeline) — embed + search + generate
- [Data Enrichment](https://github.com/statmike/vertex-ai-mlops/tree/main/data%2Bai/bq-ai-functions/workflows/data_enrichment) — enrich rows with AI
- [Multimodal Analysis](https://github.com/statmike/vertex-ai-mlops/tree/main/data%2Bai/bq-ai-functions/workflows/multimodal_analysis) — images + embeddings
- [Time Series Intelligence](https://github.com/statmike/vertex-ai-mlops/tree/main/data%2Bai/bq-ai-functions/workflows/time_series_intelligence) — forecast + anomaly detection

Every notebook runs in Colab, Colab Enterprise, BigQuery Studio, or Vertex AI Workbench — one click to open, no local setup needed. Each includes SQL examples, `%%bigquery` magics, and BigFrames (Python) patterns. Great for learning, live demos, or as a starting point for your own POC.

Start here: https://github.com/statmike/vertex-ai-mlops/tree/main/data%2Bai/bq-ai-functions

---

## Internal-only (longer, more technical)

**BigQuery AI Functions — Learn, Demo, POC Starter**

I built a hands-on reference for all 21 BigQuery AI functions — designed for learning, demos, and getting started with initial use (POC/MVP). Each function has:
- A `.sql` file with progressive examples (copy-paste into BigQuery console)
- A `.ipynb` notebook with the same examples + magics + BigFrames patterns
- Cross-references to workflows that use it

The repo also includes 9 end-to-end workflows that show how to compose functions together into real pipelines — content analysis, moderation, document processing, log analysis, semantic search, RAG, and more. Each workflow is a ready-to-run demo that can also serve as a blueprint for your own use case.

**Quick links:**

| Entry Point | What you get |
|---|---|
| [Landing page](https://github.com/statmike/vertex-ai-mlops/tree/main/data%2Bai/bq-ai-functions) | Function map, relationship diagram, workflow list |
| [RESOURCES.md](https://github.com/statmike/vertex-ai-mlops/blob/main/data%2Bai/bq-ai-functions/RESOURCES.md) | Detailed syntax, inputs, outputs, best practices for every function |
| [All functions](https://github.com/statmike/vertex-ai-mlops/tree/main/data%2Bai/bq-ai-functions/functions) | 21 function notebooks + SQL files |
| [All workflows](https://github.com/statmike/vertex-ai-mlops/tree/main/data%2Bai/bq-ai-functions/workflows) | 9 end-to-end pipelines composing multiple functions |
| [Setup guide](https://github.com/statmike/vertex-ai-mlops/tree/main/data%2Bai/bq-ai-functions/setup) | Project setup, connections, IAM roles |

**New additions:**
- **AI.AGG** — BigQuery's first aggregate AI function. Use it with GROUP BY to summarize groups of rows with Gemini. Supports DISTINCT, auto-batching, and multimodal input.
- **Log Analysis workflow** — Generates IT support tickets, classifies by category, scores business impact, then uses AI.AGG to produce per-category analysis and an executive summary.
- Updated Content Analysis, Content Moderation, and Document Intelligence workflows with AI.AGG alternatives.
