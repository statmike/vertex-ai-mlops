---
name: bigquery-ai-functions
description: Use when calling Gemini or other generative AI models directly from BigQuery SQL — text/structured generation, classification/scoring, embeddings and semantic search, zero-training forecasting/anomaly detection, driver analysis, or document/image processing via AI.* and ML.* functions and Object Tables/ObjectRef. Covers all 24 functions in this family plus 12 composed workflows (RAG, content moderation, log triage, semantic search, etc.).
---

# BigQuery AI Functions

This is BigQuery's generative-AI-in-SQL surface: `AI.*` (and some legacy `ML.*`) functions call Gemini and other foundation models directly from a query — no separate serving infrastructure, no model training. It's organized per function rather than per model lifecycle, since each function is a complete, independently-callable capability.

This skill packages a verified, field-tested reference distilled from a project that built and live-tested every function and workflow listed below — specific, evidence-backed gotchas (exact error messages, exact parameter interactions, exact output-schema behavior, confirmed outages) found by actually running this in BigQuery, not general LLM-prompting advice.

## Decision tree

1. **Do you want the model to generate free-form or structured output** (summaries, extracted fields, translations)? → `reference/generation-and-structured-output.md`
2. **Do you want a fixed-shape judgment per row** (a boolean condition, a numeric score, a category label, or a group-level summary)? → `reference/classification-and-scoring.md`
3. **Do you need to turn content into vectors, compare things for similarity, or search a corpus?** → `reference/embeddings-and-search.md`
4. **Do you need to forecast a time series or detect anomalies in one, with no training step?** → `reference/forecasting-and-anomalies.md`
5. **Do you need to explain why a metric moved (driver/key-factor analysis)?** → `reference/driver-analysis.md`
6. **Are you extracting data from documents, or need to pass images/PDFs/audio/video into any of the above?** → `reference/document-processing.md`
7. **Are you composing several of these into a real end-to-end task** (RAG, moderation, log triage, etc.)? → `reference/workflows.md`

If the ask is ambiguous between these generative functions and BigQuery ML's trained models (`CREATE MODEL` + `ML.*` — the sibling `bigquery-ml` skill), and you have access to it, consult the `choosing-a-bigquery-ai-approach` skill first — it triages between the two and encodes specific head-to-head comparisons already worked out in this project (e.g. `AI.FORECAST` vs. `ARIMA_PLUS`, `AI.KEY_DRIVERS` vs. `CONTRIBUTION_ANALYSIS`). If that skill isn't available, ask directly: does the user need training-time control / scheduled retraining / interpretable coefficients (→ BigQuery ML), or a fast, zero-setup, prompt-driven answer (→ these functions)?

## Cross-cutting gotchas (apply across most functions)

- **Almost everything here is Preview, not GA** — the four managed functions (`AI.IF`/`AI.SCORE`/`AI.CLASSIFY`/`AI.AGG`), the typed generation shortcuts (`AI.GENERATE_BOOL`/`DOUBLE`/`INT`), `AI.KEY_DRIVERS`, `AI.SEARCH`, and `AI.PARSE_DOCUMENT` are all Preview. Don't assume GA stability guarantees; expect the "contact bqml-feedback@google.com" support model rather than a standard support case.
- **`AI.PARSE_DOCUMENT` is currently offline** (taken down by Google for revision, as of 2026-06-01) — do not recommend it as a working option until confirmed restored; there's precedent (`AI.AGG` had a similar April–May 2026 outage) for these Preview functions being pulled and re-enabled.
- **`output_schema` replaces the `result` field entirely**, in both `AI.GENERATE` and `AI.GENERATE_TABLE` — code expecting a `result` field breaks the moment a schema is added.
- **`LIMIT`/`OFFSET` does not reduce billed work** — the full input is evaluated before a limit is applied on any of these row-by-row functions. Materialize the intended subset to a table first if you're testing on a sample.
- **ObjectRef vs. ObjectRefRuntime are not interchangeable** — table/`OBJ.MAKE_REF` output is `ObjectRef`; AI functions actually consume `ObjectRefRuntime`, produced only by `OBJ.GET_ACCESS_URL`. Signed URLs inside `ObjectRefRuntime` expire in at most 6 hours — never persist them long-term.
- **Not every function accepts multimodal input, and the ones that do don't all wire it the same way** — `VECTOR_SEARCH`, `AI.SEARCH`, `AI.FORECAST`, `AI.DETECT_ANOMALIES`, and `AI.EVALUATE` are text/numeric only. See `reference/document-processing.md` for the four distinct multimodal wiring patterns across the functions that do support it.
- **`AI.COUNT_TOKENS` is the free pre-flight check** — always available to size/cost a batch before running a paid function over it; note it counts input tokens only (not thinking/output tokens).
- **Managed functions (`AI.IF`/`AI.SCORE`/`AI.CLASSIFY`/`AI.AGG`) trade control for convenience** — no model-parameter control, DSQ-only (no Provisioned Throughput), return `NULL` on error rather than detailed status. Drop to `AI.GENERATE`(`_BOOL`/`_DOUBLE`/`_TABLE`) when you need model params, a pinned endpoint, or a shape these four don't cover.
- **Cross-region and same-project constraints are real and easy to hit**: `AI.GENERATE_TEXT`/`AI.GENERATE_TABLE` require model and input table in the same region; object-table-based generation requires the GCS bucket in the same project as the model.

## Reference files

- `reference/generation-and-structured-output.md` — AI.GENERATE, AI.GENERATE_TEXT, AI.GENERATE_TABLE, AI.GENERATE_BOOL/DOUBLE/INT, legacy ML.GENERATE_TEXT, AI.COUNT_TOKENS
- `reference/classification-and-scoring.md` — AI.IF, AI.SCORE, AI.CLASSIFY, AI.AGG
- `reference/embeddings-and-search.md` — AI.EMBED, AI.GENERATE_EMBEDDING, legacy ML.GENERATE_EMBEDDING, AI.SIMILARITY, VECTOR_SEARCH, AI.SEARCH, HYBRID_SEARCH (not yet built)
- `reference/forecasting-and-anomalies.md` — AI.FORECAST, AI.DETECT_ANOMALIES, AI.EVALUATE
- `reference/driver-analysis.md` — AI.KEY_DRIVERS
- `reference/document-processing.md` — ML.PROCESS_DOCUMENT, AI.PARSE_DOCUMENT (offline), Object Tables, OBJ.MAKE_REF/FETCH_METADATA/GET_ACCESS_URL
- `reference/workflows.md` — 12 composed workflows (RAG, content moderation, semantic search, time series intelligence, etc.) as worked starting templates

## Go deeper (only resolves inside this repo)

If you're working inside the `vertex-ai-mlops` repo, every reference file's "Go deeper" pointers resolve to real, tested notebooks/`.sql` files under `functions/` and `workflows/`, plus the full syntax/options tables in `RESOURCES.md`. This skill is self-contained without that repo — the reference files above already carry the distilled decision guidance and verified gotchas — but the repo is where the full progressive examples and raw evidence live.
