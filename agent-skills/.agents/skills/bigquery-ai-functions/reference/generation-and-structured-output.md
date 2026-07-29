# Generation & Structured Output Functions in BigQuery

## Options

| Function | What it returns | Use this when... | Key differentiator vs siblings |
|---|---|---|---|
| `AI.GENERATE` | STRUCT with `result` (STRING, or custom-schema fields if `output_schema` set), `full_response`, `status` | You want a scalar, no-setup call (no `CREATE MODEL`) that can return either free text or structured fields from the same function | Only general-purpose scalar function that supports `output_schema`; no remote model object required; Gemini only |
| `AI.GENERATE_TEXT` | Table (input columns + `result`, `rai_result`, `grounding_result`, `statistics`, `full_response`, `status` for Gemini; simpler set for others) | You need free-form text at scale over a table/query and want a choice of model family (Gemini, Claude, Llama, Mistral, open models) | Only one of the "big four" that runs non-Gemini models; requires a pre-created `CREATE MODEL` remote model |
| `AI.GENERATE_TABLE` | Table (input columns + your custom schema columns + `full_response`, `status`) | You need structured/tabular output at scale over many rows and want the output pre-parsed into typed columns rather than a JSON/STRING blob | Table-valued AND always structured (`output_schema` is required, not optional); Gemini only |
| `AI.GENERATE_BOOL` | STRUCT with `result` (BOOL), `full_response`, `status` | You want a plain boolean back per row without unpacking a schema or parsing text ("is this X?") | Scalar shortcut — no `output_schema` needed, one field, typed as BOOL directly |
| `AI.GENERATE_DOUBLE` | STRUCT with `result` (FLOAT64), `full_response`, `status` | You want a numeric estimate/score/count back per row as a real FLOAT64, with model_params control | Same shortcut pattern as GENERATE_BOOL but FLOAT64; more control (model_params, endpoint) than the managed `AI.SCORE` |
| `AI.GENERATE_INT` | STRUCT with `result` (INT64), `full_response`, `status` | You want a plain integer back per row (counts, integer ratings, quantities) | Same shortcut pattern as GENERATE_BOOL but INT64 |
| `ML.GENERATE_TEXT` (legacy) | Table (input columns + `ml_generate_text_result`/`ml_generate_text_status`, or flattened `ml_generate_text_llm_result` etc.) | You're maintaining an older notebook/pipeline that already calls it, or need `flatten_json_output` behavior from a JSON blob into named columns | Functionally identical to `AI.GENERATE_TEXT` but with `ml_` prefixed columns and an extra `flatten_json_output` param; Google recommends migrating new queries to `AI.GENERATE_TEXT` |
| `AI.COUNT_TOKENS` | STRUCT with `result` (INT64 input token count), `full_response` | You want to size/cost a prompt (or a whole column of prompts) **before** spending money on any of the functions above | Not a generator at all — free, no Vertex AI charge, input-tokens-only |

## Choosing among them

- **"I want free-form text back."**
  - One-off / no remote model set up yet → `AI.GENERATE` (scalar, works immediately, defaults to `gemini-2.5-flash`).
  - Batch over a table, or need a non-Gemini model (Claude/Llama/Mistral/open) → `AI.GENERATE_TEXT` (requires `CREATE MODEL` first).
  - Already have `ML.GENERATE_TEXT` calls in an existing pipeline → leave them if working, but write new queries against `AI.GENERATE_TEXT`.

- **"I want strict structured JSON/table output."**
  - Scalar, ad hoc → `AI.GENERATE` with `output_schema` (STRUCT-of-fields spec, e.g. `'category STRING, confidence FLOAT64'`); this replaces the `result` field with your named columns in the returned STRUCT.
  - Table-valued, batch, Gemini → `AI.GENERATE_TABLE`, which *requires* `output_schema` (there's no free-text mode) and returns your fields as real output columns alongside the input table's columns.
  - `output_schema` supports `STRING`, `INT64`, `FLOAT64`, `BOOL`, `ARRAY`, `STRUCT`, each with an optional `OPTIONS(description = '...')` to steer the model — the same schema syntax works in both `AI.GENERATE` and `AI.GENERATE_TABLE`.

- **"I want a single boolean/number back without parsing a struct's `result` field manually."**
  - Boolean condition → `AI.GENERATE_BOOL`.
  - Numeric estimate/score → `AI.GENERATE_DOUBLE`.
  - Integer count/label → `AI.GENERATE_INT`.
  - All three are scalar, Gemini-only, Preview, and share the exact same parameter set as `AI.GENERATE` (endpoint, model_params, connection_id, request_type) minus `output_schema` — you get a typed `result` instead of a STRING you'd have to CAST or parse.
  - If you want similar single-value outputs but don't need model_params control, consider the managed `AI.IF` / `AI.SCORE` (see classification-and-scoring.md) — they auto-optimize the prompt but give up parameter control.

- **"I want to estimate cost/tokens before running a large batch."**
  - `AI.COUNT_TOKENS(prompt_string [, endpoint => 'model'])` — free, no Vertex AI charge. Sum/average it across a column to size a workload before calling any paid function. Match `endpoint` to the model you intend to actually generate with, since tokenizers differ by model.

- **Google Search grounding:** `AI.GENERATE` supports grounding via `model_params` (the `tools` field, e.g. `googleSearch`, requires Gemini 2.0+; `googleMaps` also available). `AI.GENERATE_TEXT` and `ML.GENERATE_TEXT` support it via the simpler `ground_with_google_search` struct field (Gemini only). `AI.GENERATE_TABLE` does **not** support grounding.

## Gotchas verified in this repo

- `AI.COUNT_TOKENS` counts **input tokens only** — thinking and output tokens are excluded from `result`. To see the true total (input + thinking + output) for a query, check the Job Information tab of the query results pane, not this function.
- `AI.COUNT_TOKENS` is **text-only, verified in Preview**: passing a STRUCT prompt with an `ObjectRefRuntime` field (the same pattern that works fine in `AI.GENERATE`), or a bare `ObjectRefRuntime`, both fail with `"Unable to coerce type ... to expected type STRING."` `full_response.promptTokensDetails[].modality` is therefore always `"TEXT"`. Re-test at GA — `AI.PARSE_DOCUMENT` is precedent for multimodal support arriving without an obvious signature change.
- `AI.COUNT_TOKENS`'s real signature has two more undocumented parameters: `title => STRING` and `model => STRING`. `model` is mutually exclusive with `endpoint` and rejects every tested value (plain Gemini model names and a remote `MODEL` reference) with `"Unsupported model"`; `title` errors with `"Title argument is not supported for gemini-2.5-flash."` Don't teach these — they appear reserved for a future/non-Gemini capability.
- `output_schema` in `AI.GENERATE`/`AI.GENERATE_TABLE` **replaces** the `result` field entirely with your named columns — code that expects a `result` field will break the moment `output_schema` is added; update downstream SQL/notebooks accordingly.
- `AI.GENERATE_BOOL`/`DOUBLE`/`INT` are all **Preview** status — don't build production pipelines assuming GA stability, and expect the "contact bqml-feedback@google.com" support model rather than standard GA support.
- Video input is capped at 2 minutes across `AI.GENERATE`, `AI.GENERATE_BOOL/DOUBLE/INT`, and `AI.GENERATE_TABLE` — longer videos are silently truncated to the first 2 minutes, not rejected, and at most one video object is allowed per prompt.
- `AI.GENERATE_TEXT` and `AI.GENERATE_TABLE` require the model and the input table to be in the **same region** — a cross-region call fails outright; this is easy to hit when a dataset and a `CREATE MODEL` connection were provisioned in different regions.
- For `AI.GENERATE_TEXT` on object tables (image/video/audio analysis), the query is restricted to `WHERE` and `ORDER BY` only — no joins/aggregations in that query shape — and the underlying GCS bucket must be in the **same project** as the model.
- Using `LIMIT`/`OFFSET` directly against a live prompt query for any of these functions causes the full input to be evaluated before the limit is applied, so you still pay for/process the whole set — materialize the intended subset to a table first, then call the generation function against that table.
- Thinking-budget control differs by Gemini generation: use `thinking_budget` inside `model_params.thinking_config` for Gemini 2.5 models, but `thinking_level` (`LOW`/`MEDIUM`/`HIGH`) for Gemini 3.0+ — using the wrong key for the model generation silently does nothing useful rather than erroring loudly, so verify which key applies to the endpoint in use.
- `ML.GENERATE_TEXT`'s `flatten_json_output` defaults to `FALSE`, which returns a raw JSON blob in `ml_generate_text_result` rather than a parsed `result` STRING — the column-naming convention (`ml_generate_text_*` prefix) and this default are the main things that trip people migrating from/to `AI.GENERATE_TEXT`, which has no such flag and always returns parsed columns.

## Canonical snippet

```sql
SELECT
  AI.GENERATE(
    (
      'Extract the product name, sentiment, and a 1-sentence summary from this review: ',
      review_text
    ),
    output_schema => 'product_name STRING, sentiment STRING OPTIONS(description = "one of: positive, neutral, negative"), summary STRING'
  ).*
FROM `my_project.my_dataset.reviews`;
```

This returns `product_name`, `sentiment`, and `summary` as real typed columns (no `result` field — `output_schema` replaces it), plus `full_response` and `status`, with no `CREATE MODEL` step required.

## Go deeper

Full extracted notebook walkthroughs live in this skill's `narrative/` folder — no need to be inside the source repo:

- [`narrative/ai_generate.md`](../narrative/ai_generate.md) (source: `functions/ai_generate/`)
- [`narrative/ai_generate_text.md`](../narrative/ai_generate_text.md) (source: `functions/ai_generate_text/`)
- [`narrative/ai_generate_table.md`](../narrative/ai_generate_table.md) (source: `functions/ai_generate_table/`)
- [`narrative/ai_generate_bool.md`](../narrative/ai_generate_bool.md) (source: `functions/ai_generate_bool/`)
- [`narrative/ai_generate_double.md`](../narrative/ai_generate_double.md) (source: `functions/ai_generate_double/`)
- [`narrative/ai_generate_int.md`](../narrative/ai_generate_int.md) (source: `functions/ai_generate_int/`)
- [`narrative/ml_generate_text.md`](../narrative/ml_generate_text.md) (source: `functions/ml_generate_text/`) — legacy
- [`narrative/ai_count_tokens.md`](../narrative/ai_count_tokens.md) (source: `functions/ai_count_tokens/`)

Full syntax/options tables: see RESOURCES.md in the source repo (`bq-ai-functions/RESOURCES.md`).
