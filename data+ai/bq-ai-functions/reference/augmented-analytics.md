![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2Fdata%2Bai%2Fbq-ai-functions%2Freference&file=augmented-analytics.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/data%2Bai/bq-ai-functions/reference/augmented-analytics.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-ai-functions/reference/augmented-analytics.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-ai-functions/reference/augmented-analytics.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-ai-functions/reference/augmented-analytics.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-ai-functions/reference/augmented-analytics.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
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
    <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/data%2Bai/bq-ai-functions/reference/augmented-analytics.md"><img src="https://www.svgrepo.com/download/5445/download-button.svg" alt="Download icon" width="20px"></a> <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/data%2Bai/bq-ai-functions/reference/augmented-analytics.md">Download File</a> <i>(right-click and "Save As")</i>
  </td>
</tr>
</table><br/><br/>

---
# Augmented Analytics

> Part of the [BigQuery AI Functions Resources](../RESOURCES.md) · [Project README](../README.md)

These functions answer analytical "why" questions over structured data — explaining *which segments of your data drive a change* in a metric. Like the Forecasting functions, they run entirely in BigQuery with no `CREATE MODEL` step, no connection, and no Gemini endpoint.

**Key relationships:**
- `AI.KEY_DRIVERS` performs contribution / key-driver analysis: it compares an interest set against a reference set and surfaces the data segments that most explain the difference in a summable metric. It is the simplified, model-free equivalent of creating a contribution analysis model and calling `ML.GET_INSIGHTS`.

---

## `AI.KEY_DRIVERS`
- **Description:** (Preview) Table-valued function that identifies segments of data causing statistically significant changes to a summable metric between an interest set and a reference set (key driver / contribution analysis). No `CREATE MODEL` step, connection, or endpoint required — it operates directly on a table or subquery.
- **Use cases:** Explaining why a metric moved between two periods (e.g., this month vs last), comparing test vs control groups, attributing revenue/usage changes to customer segments, geographies, or product categories, root-cause analysis for KPI shifts.
- [documentation](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-key-drivers)
- **Type:** Table-valued function — Preview

**Syntax:**
```sql
AI.KEY_DRIVERS(
  { TABLE TABLE_NAME | (QUERY_STATEMENT) },
  metric_col => 'METRIC_COL',
  dimension_cols => DIMENSION_COLS,
  interest_label_col => 'INTEREST_LABEL_COL'
  [, min_apriori_support => MIN_APRIORI_SUPPORT ]
  [, top_k => TOP_K ]
  [, enable_pruning => ENABLE_PRUNING ]
);
```

**Inputs:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `TABLE` / `(QUERY_STATEMENT)` | Table or subquery | Required | -- | The interest and reference data to analyze. Must contain a summable metric column, a BOOL interest/reference column, and one or more dimension columns. |
| `metric_col` | STRING (named parameter) | Required | -- | A summable metric, expressed as `SUM(column_name)` or `column_name` (both are equivalent and case-insensitive). No additional computation allowed in the expression (e.g., no `SUM(AVG(...))`); do extra math in `QUERY_STATEMENT` instead. |
| `dimension_cols` | ARRAY<STRING> (named parameter) | Required | -- | Names of the columns to use as dimensions when summarizing the metric. Must be `INT64`, `BOOL`, or `STRING`. Provide **between 1 and 12** columns. Cannot reuse the `metric_col` or `interest_label_col`. |
| `interest_label_col` | STRING (named parameter) | Required | -- | Name of a `BOOL` column. `TRUE` rows are the interest (test) group; `FALSE` rows are the reference (control) group. |
| `min_apriori_support` | FLOAT64 (named parameter) | Optional | 0.1 | Minimum apriori support threshold in `[0,1]` for including segments. Segments below the threshold are excluded. **Mutually exclusive with `top_k`.** |
| `top_k` | INT64 (named parameter) | Optional | -- | Between 1 and 1,000,000. Returns the insights with the highest apriori support and prunes the rest, reducing runtime. **Mutually exclusive with `min_apriori_support`.** If neither is set, a `min_apriori_support` of 0.1 is applied. |
| `enable_pruning` | BOOL (named parameter) | Optional | TRUE | When `TRUE`, redundant insights are omitted (a row whose dimensions/values are a subset of another row with an equal metric is pruned, keeping the more descriptive row). The `["all"]` row is never pruned. When `FALSE`, all insights pass through except those filtered by support thresholds. |

**Outputs:** Returns the following columns in addition to the dimension columns:

| Column | Type | Description |
|--------|------|-------------|
| `drivers` | ARRAY<STRING> | The dimension values describing the segment (e.g., `["usertype=Subscriber","gender=male"]`). The other columns in the row apply to this segment. The whole-population row is `["all"]`. |
| `metric_interest` | NUMERIC | Sum of the metric in the interest set for the segment. |
| `metric_reference` | NUMERIC | Sum of the metric in the reference set for the segment. |
| `difference` | NUMERIC | `metric_interest - metric_reference`. |
| `relative_difference` | NUMERIC | `difference / metric_reference`. |
| `unexpected_difference` | NUMERIC | Difference between the segment's actual and *expected* `metric_interest`, where the expectation is derived from the change ratio of all other segments. Highlights segments changing differently than the overall trend. |
| `relative_unexpected_difference` | NUMERIC | `unexpected_difference / expected_metric_interest`. |
| `apriori_support` | NUMERIC | `GREATEST(metric_interest / total_interest, metric_reference / total_reference)` — how large the segment is relative to the population. |
| `contribution` | NUMERIC | `ABS(difference)` — magnitude of the segment's contribution to the overall change. |

**Input data requirements:** A single table containing both the interest (test) and reference (control) rows, distinguished by the BOOL `interest_label_col`. For best results, use roughly equal numbers of interest and reference rows to avoid biased results. Typical interest/reference splits: two time periods, two geographies, two product types, or two campaigns.

**Best practices:**
- Build the BOOL interest/reference column inside `QUERY_STATEMENT` (e.g., `(EXTRACT(YEAR FROM ts) = 2017) AS is_interest`).
- Use `top_k` for fast, ranked top insights; use `min_apriori_support => 0` to see every segment.
- Sort the output by `contribution` (largest absolute movers) or `unexpected_difference` (segments defying the overall trend).
- Keep `enable_pruning => TRUE` (default) for a concise insight set; set `FALSE` when you need the full unpruned breakdown.

**Limitations:**
- Supports a **maximum of 12 dimensions**.
- Supports **summable metrics only** (contribution analysis models additionally support summable-by-ratio and summable-by-category metrics).
- `min_apriori_support` and `top_k` cannot be used together.

**Locations:** US and EU multi-regions.

**Provisioned throughput:** Not specified.

**BigFrames API:** No direct equivalent. Use `%%bigquery` magics or `session.read_gbq_query()` to execute AI.KEY_DRIVERS SQL from BigFrames.

**Relationship to contribution analysis models / ML.GET_INSIGHTS:** Calling `AI.KEY_DRIVERS` is similar to first creating a contribution analysis model and then calling `ML.GET_INSIGHTS` on it. For most applications, `AI.KEY_DRIVERS` is recommended — simpler syntax, faster results, and automatic pruning. Use a contribution analysis model when you need more than 12 dimensions or non-summable metrics — see [`../bq-ml/RESOURCES.md`](../../bq-ml/RESOURCES.md)'s `CONTRIBUTION_ANALYSIS` entry and [`../bq-ml/models/contribution_analysis/`](../../bq-ml/models/contribution_analysis/), which uses this exact dataset and interest/reference split for a direct side-by-side comparison, and verifies both differentiators (ratio/category metrics, >12 dimensions) live, plus a finding not covered here: `ML.GET_INSIGHTS`'s output schema differs by metric type (summable vs. ratio vs. category each return different derived-statistic columns).

| | AI.KEY_DRIVERS | Contribution analysis model + ML.GET_INSIGHTS |
|---|----------------|------------------------------------------------|
| **Dimensions** | Maximum 12 | More than 12 |
| **Metric types** | Summable only | Summable, summable by ratio, summable by category |
| **Pruning** | Prunes redundant insights by default | Returns all insights by default |
| **Segment column** | `drivers` | `contributors` |
| **Model management** | None required | Create and manage a model |
