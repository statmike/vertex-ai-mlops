# Driver / Key-Factor Analysis in BigQuery AI Functions

## What it is

`AI.KEY_DRIVERS` is a (Preview) table-valued function that identifies which segments of your data are statistically driving a change in a summable metric between an interest set and a reference set — key-driver / contribution analysis. It requires no `CREATE MODEL` step, no connection, and no Gemini endpoint; it runs directly over a table or subquery. It's the simplified, model-free equivalent of creating a BigQuery ML contribution analysis model and calling `ML.GET_INSIGHTS`.

## When to use it

- Reach for `AI.KEY_DRIVERS` when you're answering "why did this metric move?" questions — e.g., comparing this month vs. last, test vs. control, or attributing a revenue/usage change to segments, geographies, or product categories — and you have **12 or fewer dimension columns** and a **summable metric** (expressed as `SUM(column)` or a bare `column` reference). It's simpler syntax, faster results, automatic redundancy pruning, and no model lifecycle to manage.
- Reach for `../../bq-ml/models/contribution_analysis/` (`CREATE MODEL ... OPTIONS(model_type='CONTRIBUTION_ANALYSIS')` + `ML.GET_INSIGHTS`) instead when you need **more than 12 dimensions**, or a metric type other than plain-summable — contribution analysis models additionally support **summable-by-ratio** and **summable-by-category** metrics, which `AI.KEY_DRIVERS` does not support at all.
- `AI.KEY_DRIVERS` is Preview and scoped to **US and EU multi-regions only** — check region availability before defaulting to it in a pipeline that runs elsewhere.

## Gotchas verified in this repo

- Hard dimension ceiling: `dimension_cols` accepts **between 1 and 12** columns (`INT64`, `BOOL`, or `STRING` only) — this is the single biggest reason to fall back to a contribution analysis model.
- `min_apriori_support` (default 0.1) and `top_k` are **mutually exclusive** — passing both is an error; if you specify neither, `min_apriori_support => 0.1` is silently applied, which can hide low-support-but-real segments. Use `min_apriori_support => 0` to see everything.
- The interest/reference split is a single BOOL column (`interest_label_col`) inside one table, not two separate tables — build it in the `QUERY_STATEMENT` (e.g., `(EXTRACT(YEAR FROM ts) = 2017) AS is_interest`), and keep interest/reference row counts roughly balanced to avoid biased results.
- `metric_col` only accepts a bare column name or `SUM(column_name)` — no nested computation like `SUM(AVG(...))` is allowed in the expression; do that math upstream in the `QUERY_STATEMENT`.
- Output uses a `drivers` ARRAY<STRING> column (e.g., `["usertype=Subscriber","gender=male"]`), not a scalar per-dimension breakdown — the whole-population baseline row is always `["all"]` and is never pruned even with `enable_pruning => TRUE`.
- `enable_pruning` defaults to `TRUE`, which drops any segment whose dimensions/values are a strict subset of another segment with an equal metric value — set it to `FALSE` if you need the full unpruned breakdown for auditing.
- Output includes both `difference` (interest − reference) and `unexpected_difference` (deviation from what the segment's change *should* have been given the overall trend) — sort by `contribution` (`ABS(difference)`) for largest movers, or by `unexpected_difference` for segments defying the overall trend.
- Segment column naming differs between the two approaches: `AI.KEY_DRIVERS` uses `drivers`; the contribution analysis model + `ML.GET_INSIGHTS` uses `contributors` — and per the contribution-analysis writeup, `ML.GET_INSIGHTS`'s output schema additionally varies by metric type (summable vs. ratio vs. category each return different derived-statistic columns), which `AI.KEY_DRIVERS` avoids entirely since it only supports one metric type.

## Canonical snippet

```sql
SELECT *
FROM AI.KEY_DRIVERS(
  (
    SELECT
      usertype,
      gender,
      trip_duration,
      EXTRACT(YEAR FROM start_date) = 2017 AS is_interest
    FROM `project.dataset.bike_trips`
    WHERE EXTRACT(YEAR FROM start_date) IN (2016, 2017)
  ),
  metric_col => 'trip_duration',
  dimension_cols => ['usertype', 'gender'],
  interest_label_col => 'is_interest',
  top_k => 20
)
ORDER BY contribution DESC;
```

## Go deeper

- [`narrative/ai_key_drivers.md`](../narrative/ai_key_drivers.md) (source: `functions/ai_key_drivers/`) — cross-linked bidirectionally with bq-ml's contribution_analysis, which uses this exact dataset and interest/reference split for a direct side-by-side comparison

The `bigquery-ml` skill's `narrative/contribution_analysis.md` has the other half of that comparison.

Full syntax/options tables: see RESOURCES.md in the source repo (`bq-ai-functions/RESOURCES.md`).
