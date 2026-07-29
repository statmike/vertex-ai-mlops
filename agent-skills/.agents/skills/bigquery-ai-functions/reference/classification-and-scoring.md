# Managed Classification & Scoring Functions in BigQuery

## Options

| Function | What it does | Use this when... | Key differentiator |
|---|---|---|---|
| `AI.IF` | Evaluates a natural-language condition, returns a plain BOOL | You need a fuzzy/semantic boolean test — a `WHERE` filter, a `JOIN` condition, or a branch — expressed in plain English | Returns BOOL directly (not a struct); relates to `AI.GENERATE_BOOL` but with automatic prompt optimization and less control |
| `AI.SCORE` | Rates/ranks input against a scale you describe, returns a FLOAT64 | You need a numeric quality/relevance/priority score to sort or threshold on (e.g. "most negative review", "best resume") | Auto-generates a scoring rubric from your prompt; no fixed default range — you must state the scale in the prompt |
| `AI.CLASSIFY` | Buckets input into a fixed, user-supplied category list, returns STRING or ARRAY&lt;STRING&gt; | You know the category set in advance and want single- or multi-label classification without writing an `output_schema` | Only managed function with no general-purpose counterpart; categories can carry descriptions and few-shot examples |
| `AI.AGG` | Aggregate function (like `SUM`/`COUNT`) that summarizes/synthesizes many rows per group into one STRING | You need a GROUP BY-level synthesis (sentiment across all reviews for a product, a summary of a log group) that may exceed a single prompt's context window | Only aggregate function of the four; auto-batches multi-level so it can process data beyond the Gemini context window |

## Choosing among them

- **"I want to filter/branch on a fuzzy condition."** → `AI.IF`. Put ordinary (non-AI) filters in the same `WHERE` clause alongside it — BigQuery evaluates non-AI filters first and short-circuits, which reduces the number of billed Gemini calls (e.g. `WHERE AI.IF(...) AND category = 'tech'`).

- **"I want a numeric quality/relevance/priority score."** → `AI.SCORE`. State the scale explicitly in the prompt (e.g. "rate 1–10") since there is no fixed default range. Commonly paired with `ORDER BY ... LIMIT` for ranking, and can be combined with `AI.IF` to pre-filter before scoring.

- **"I want to bucket rows into known categories."** → `AI.CLASSIFY`. Pass `categories` as an `ARRAY<STRING>` (bare labels) or `ARRAY<STRUCT<STRING,STRING>>` (label + description, for more nuanced classification). Use `output_mode => 'multi'` for multi-label problems (returns 0..N categories, empty array if none apply); leave it unset or `'single'` for one best-fit label. Categories can also come from a table via a `DECLARE ... ARRAY<STRING> DEFAULT (SELECT ARRAY_AGG(...))` variable rather than a hardcoded literal.

- **"I want to summarize/synthesize across many rows in a group."** → `AI.AGG(input, instruction [, connection_id =>][, endpoint =>])`, used with `GROUP BY` for per-group results or without it to aggregate the whole table into one STRING. Use `DISTINCT` to dedupe inputs and cut token usage. Prefer it over hand-rolling `STRING_AGG`/`ARRAY_AGG` into an `AI.GENERATE` prompt — `AI.AGG` batches automatically and can exceed the context window that a manual concatenation would blow past.

- **Managed vs. raw `AI.GENERATE`:** all four managed functions are Preview, DSQ-only (no Provisioned Throughput), auto-select a cost/quality-optimized model when no `endpoint` is given, return `NULL` on error (no detailed status/full_response), and give up model-parameter control (temperature, top_p, etc.). Prefer them when the task fits their shape (boolean test, single score, fixed category set, group summary) and you want BigQuery's automatic prompt engineering rather than hand-writing prompts. Drop down to `AI.GENERATE` (with `output_schema` if needed) when you need: model parameter control, a non-default/pinned model via `endpoint` with fine-grained `model_params`, Provisioned Throughput, detailed `full_response`/`status` for debugging, or an output shape (multi-field structured record) that doesn't map onto BOOL/FLOAT64/STRING/ARRAY&lt;STRING&gt;. `AI.GENERATE_BOOL`/`AI.GENERATE_DOUBLE` are the direct general-purpose analogs of `AI.IF`/`AI.SCORE` respectively when you need that extra control.

## Gotchas verified in this repo

- All four functions are **Preview** status — expect the "contact bqml-feedback@google.com" support model, not GA stability guarantees.
- None of the four support model-parameter control (temperature, top_p, thinking budget, etc.) — that control only exists on the general-purpose siblings (`AI.GENERATE`, `AI.GENERATE_BOOL/DOUBLE/INT`, `AI.GENERATE_TEXT`).
- `AI.CLASSIFY` categories must be **string literals in the array** (or a `DECLARE`d variable) — you cannot pass a column reference directly as the categories argument; if categories are dynamic per-row, this is a hard modeling constraint to plan around.
- `AI.CLASSIFY`'s `output_mode => 'multi'` is explicitly **not supported** when `optimization_mode` is set (the `MINIMIZE_COST`/`MAXIMIZE_QUALITY` optimized path) — multi-label classification and cost-optimized embeddings mode are mutually exclusive.
- `optimization_mode` (on `AI.IF` and `AI.CLASSIFY`) requires roughly **3,000 rows minimum** to be effective, and in optimized mode only string columns are supported for multi-column prompts/inputs — this is a distilled local-model path (`MINIMIZE_COST`, up to ~230x token reduction) that only pays off at that scale.
- `max_error_ratio` (available on `AI.IF`, `AI.SCORE`, `AI.CLASSIFY`) is **not supported** when `optimization_mode` is `MINIMIZE_COST` — you lose that safety valve in the cost-optimized path.
- `AI.AGG` has documented **known issues**: rows with 10+ images in a single row may be silently skipped; rows containing arrays of `ObjectRefRuntime` values (via `OBJ.GET_ACCESS_URL`) may be skipped; Workforce Identity Federation without an explicit connection can fail long-running queries; Gemini 3.0/3.1 with connection-based auth may intermittently return unauthenticated errors.
- `AI.AGG` output is capped at **10,000 tokens per group**, and the docs recommend staying under 20 million rows and 1,000 distinct groups per query to avoid timeouts — and it cannot use Gemini models that require a thinking budget.
- `AI.AGG`'s actual processed-row count can diverge from expectations on complex queries (JOINs, `ORDER BY ... LIMIT`) — materialize the intended input to a separate table first if you need predictable, auditable row counts/costs.
- `AI.SCORE` has **no fixed default score range** — omitting an explicit scale in the prompt (e.g. "1 to 10") produces inconsistent, hard-to-compare ranges across calls; always state the scale.
- None of the four managed functions support `DISTINCT` or `GROUP BY` except `AI.AGG` (which supports both, being the one aggregate in the family) — attempting to use the scalar three (`AI.IF`, `AI.SCORE`, `AI.CLASSIFY`) as if they were aggregates will not work since they operate strictly row by row.
- Row-count ceiling is **10,000,000 rows per job** for `AI.IF`/`AI.SCORE`/`AI.CLASSIFY`, versus a (recommended, not hard) **20,000,000** for `AI.AGG` — plan batch sizing accordingly, especially since none of these support Provisioned Throughput (DSQ only), so large jobs compete for shared quota.

## Canonical snippet

```sql
SELECT
  ticket_id,
  ticket_text,
  AI.CLASSIFY(
    input => ticket_text,
    categories => [
      ('billing', 'questions or disputes about charges, invoices, or refunds'),
      ('technical', 'product bugs, errors, or how-to questions'),
      ('account', 'login, password, or account-access issues'),
      ('other', 'anything that does not clearly fit the above')
    ]
  ) AS category
FROM `my_project.my_dataset.support_tickets`;
```

This uses category descriptions (not just bare labels) for more nuanced classification and includes an explicit "other" bucket to catch inputs that don't closely match any defined category.

## Go deeper

Full extracted notebook walkthroughs live in this skill's `narrative/` folder — no need to be inside the source repo:

- [`narrative/ai_if.md`](../narrative/ai_if.md) (source: `functions/ai_if/`)
- [`narrative/ai_score.md`](../narrative/ai_score.md) (source: `functions/ai_score/`)
- [`narrative/ai_classify.md`](../narrative/ai_classify.md) (source: `functions/ai_classify/`)
- [`narrative/ai_agg.md`](../narrative/ai_agg.md) (source: `functions/ai_agg/`)

Full syntax/options tables: see RESOURCES.md in the source repo (`bq-ai-functions/RESOURCES.md`).
