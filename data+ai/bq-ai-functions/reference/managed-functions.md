![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2Fdata%2Bai%2Fbq-ai-functions%2Freference&file=managed-functions.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/data%2Bai/bq-ai-functions/reference/managed-functions.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-ai-functions/reference/managed-functions.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-ai-functions/reference/managed-functions.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-ai-functions/reference/managed-functions.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-ai-functions/reference/managed-functions.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
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
    <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/data%2Bai/bq-ai-functions/reference/managed-functions.md"><img src="https://www.svgrepo.com/download/5445/download-button.svg" alt="Download icon" width="20px"></a> <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/data%2Bai/bq-ai-functions/reference/managed-functions.md">Download File</a> <i>(right-click and "Save As")</i>
  </td>
</tr>
</table><br/><br/>

---
# Managed Functions

> Part of the [BigQuery AI Functions Resources](../RESOURCES.md) · [Project README](../README.md)

These are higher-level "managed" AI functions that provide **simplified interfaces** and **automatic prompt optimization** for common tasks. Unlike the general-purpose functions, these functions automatically structure your prompts to improve output quality and return simple scalar values rather than full model response structs.

**Key characteristics:**
- All are in **Preview** status.
- `AI.IF`, `AI.SCORE`, and `AI.CLASSIFY` are **scalar functions** returning simple types (BOOL, FLOAT64, STRING/ARRAY\<STRING\>).
- `AI.AGG` is an **aggregate function** (like `SUM`, `COUNT`) that returns STRING -- one result per GROUP BY group.
- All use **dynamic shared quota (DSQ)** only -- no Provisioned Throughput support.
- BigQuery **automatically chooses** the model if no endpoint is specified (optimizing for cost-to-quality tradeoff).
- Return `NULL` on error (no detailed status or full_response fields).
- Cannot control model parameters (temperature, top_p, etc.) -- unlike their general-purpose counterparts.

**Relationships to general-purpose functions:**
- `AI.IF` relates to `AI.GENERATE_BOOL` -- AI.IF has prompt optimization and simpler output; AI.GENERATE_BOOL provides more control and detailed output.
- `AI.SCORE` relates to `AI.GENERATE_DOUBLE` -- AI.SCORE automatically generates a scoring rubric; AI.GENERATE_DOUBLE provides more control and detailed output.
- `AI.CLASSIFY` has no direct general-purpose counterpart but can be approximated with AI.GENERATE using output_schema.
- `AI.AGG` relates to manual aggregation with `AI.GENERATE` (using `STRING_AGG` or `ARRAY_AGG` to batch rows into a single prompt) -- AI.AGG automatically handles multi-level batching and can process data exceeding the Gemini context window.

| Feature | AI.IF | AI.SCORE | AI.CLASSIFY | AI.AGG |
|---------|-------|----------|-------------|--------|
| **Function Type** | Scalar | Scalar | Scalar | Aggregate |
| **Return Type** | BOOL | FLOAT64 | STRING or ARRAY\<STRING\> | STRING |
| **Purpose** | Evaluate natural language condition | Rate/score inputs on a scale | Classify into user-defined categories | Aggregate data with natural language instructions |
| **Unique Input** | `PROMPT` only | `PROMPT` only | `INPUT` + `CATEGORIES` + optional `OUTPUT_MODE` | `INPUT` + `INSTRUCTION` |
| **Supports DISTINCT** | No | No | No | Yes |
| **Supports GROUP BY** | No (scalar) | No (scalar) | No (scalar) | Yes (aggregate) |
| **Auto-batching** | No | No | No | Yes (multi-level) |
| **Prompt Optimization** | Yes (auto-structures prompts) | Yes (auto-generates scoring rubric) | Yes (auto-structures for classification) | Yes (auto-batches and aggregates) |
| **Model Parameter Control** | No | No | No | No |
| **Multimodal Support** | Yes (STRUCT prompt) | Yes (STRUCT prompt) | Yes (STRUCT prompt) | Yes (STRUCT input with ObjectRefRuntime) |
| **Few-shot Examples** | Yes (`examples` param) | No | Yes (`examples` param) | No |
| **Optimized Mode** | Yes (`optimization_mode`, `embeddings` — Preview) | No | Yes (`optimization_mode`, `embeddings` — Preview) | No |
| **Error Ratio Control** | Yes (`max_error_ratio`) | Yes (`max_error_ratio`) | Yes (`max_error_ratio`) | No |
| **Error Return** | NULL | NULL | NULL | NULL (partial results on partial failure) |
| **Provisioned Throughput** | Not supported (DSQ only) | Not supported (DSQ only) | Not supported (DSQ only) | Not supported (DSQ only) |
| **Rows per Job** | 10,000,000 | 10,000,000 | 10,000,000 | 20,000,000 (recommended) |
| **Output Cap** | N/A | N/A | N/A | 10,000 tokens per group |

---

## `AI.IF`
- **Description:** (Preview) Scalar function that uses a Vertex AI Gemini model to evaluate a condition described in natural language and returns a BOOL. BigQuery automatically structures (optimizes) your prompts to improve the quality of the output.
- **Use cases:** Sentiment analysis (find negative reviews), topic analysis (identify articles on a subject), image analysis (select images containing a specific item), security (identify suspicious emails), filtering in WHERE clauses, joining tables based on semantic or multimodal conditions.
- [documentation](https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-if)
- **Type:** Scalar function -- returns a single BOOL value per row (Preview)

**Syntax:**
```sql
AI.IF(
  [ prompt => ] 'PROMPT'
  [, examples => EXAMPLES ]
  [, connection_id => 'CONNECTION' ]
  [, endpoint => 'ENDPOINT' ]
  [, embeddings => EMBEDDINGS ]
  [, optimization_mode => 'OPTIMIZATION_MODE' ]
  [, max_error_ratio => MAX_ERROR_RATIO ]
)
```

**Inputs:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `PROMPT` | STRING or STRUCT | Required (must be first argument) | The prompt value to send to the model. STRING or STRUCT with STRING/ARRAY\<STRING\>/ObjectRefRuntime/ARRAY\<ObjectRefRuntime\> fields. At most one video object. |
| `EXAMPLES` | ARRAY\<STRUCT\<STRING, BOOL\>\> | Optional | Few-shot examples to guide the model. Each struct maps an example input string to an expected BOOL output. Example: `[("I love this product", TRUE), ("The product performed well", FALSE)]`. |
| `CONNECTION` | STRING | Optional | Connection to use, format: `[PROJECT_ID].LOCATION.CONNECTION_ID`. If not specified, end-user credentials are used. |
| `ENDPOINT` | STRING | Optional | Vertex AI endpoint. Any GA or preview Gemini model. If not specified, BigQuery ML dynamically chooses a model for best cost-to-quality tradeoff. |
| `EMBEDDINGS` | (Preview) | Optional | Embeddings for optimized mode. Can be generated on-the-fly via `AI.EMBED(...)` or pre-materialized. If autonomous embedding generation is enabled on the table, BigQuery automatically uses the embeddings. |
| `OPTIMIZATION_MODE` | STRING | Optional (Preview) | `MINIMIZE_COST` (default when embeddings provided — trains a local distilled model, up to 230x token reduction) or `MAXIMIZE_QUALITY` (always uses remote LLM). Requires ~3,000 rows minimum. |
| `MAX_ERROR_RATIO` | FLOAT64 | Optional | Range 0.0–1.0, default 1.0. If the error ratio exceeds this threshold, the query fails with an error describing the most frequent error types. Not supported when `optimization_mode` is `MINIMIZE_COST`. |

**Outputs:**

| Return Type | Description |
|-------------|-------------|
| BOOL | The result of evaluating the condition in the input prompt. |
| NULL | Returned if the call to Vertex AI is unsuccessful for any reason. |

**Supported models:** Any GA or preview Gemini model. If no endpoint specified, BigQuery dynamically chooses for best cost-to-quality tradeoff. Uses various `gemini-2.5-*` models.

**Best practices:**
- BigQuery optimizes queries to reduce Gemini calls. Place non-AI filters alongside AI.IF -- non-AI filters are evaluated first (e.g., `WHERE AI.IF(...) AND category = 'tech'`).
- Do not use the global endpoint if you have data processing location requirements.

**Limitations:** Preview status. Returns NULL on error (no detailed error info). No model parameter control (temperature, top_p, etc.) unlike AI.GENERATE_BOOL. At most one video object per input. Optimized mode requires ~3,000 rows minimum; only string columns supported for multi-column prompts in optimized mode.

**Locations:** All regions supporting Gemini models, plus US and EU multi-regions.

**Provisioned throughput:** Not supported. Uses dynamic shared quota (DSQ) only.

**BigFrames API:** `bigframes.bigquery.ai.if_(prompt)` — Returns a Series of BOOL directly (not a struct, unlike generate_bool). No endpoint param -- auto-selects model. Example: `bbq.ai.if_((df["review"], " is a positive review"))`. Can be used for boolean indexing: `df[bbq.ai.if_(...)]`.

---

## `AI.SCORE`
- **Description:** (Preview) Scalar function that uses a Vertex AI Gemini model to rate inputs based on a scoring system that you describe and returns a FLOAT64 value. BigQuery rewrites your input prompt to generate a scoring rubric that can improve the consistency and quality of the results.
- **Use cases:** Find the most negative customer reviews (retail), find the most qualified resumes (hiring), find the best customer support interactions, rating and ranking items. Commonly used with ORDER BY.
- [documentation](https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-score)
- **Type:** Scalar function -- returns a single FLOAT64 value per row (Preview)

**Syntax:**
```sql
AI.SCORE(
  [ prompt => ] 'PROMPT'
  [, connection_id => 'CONNECTION' ]
  [, endpoint => 'ENDPOINT' ]
  [, max_error_ratio => MAX_ERROR_RATIO ]
)
```

**Inputs:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `PROMPT` | STRING or STRUCT | Required (must be first argument) | The prompt describing the scoring criteria. STRING or STRUCT with STRING/ARRAY\<STRING\>/ObjectRefRuntime/ARRAY\<ObjectRefRuntime\> fields. At most one video object. |
| `CONNECTION` | STRING | Optional | Connection to use, format: `[PROJECT_ID].LOCATION.CONNECTION_ID`. |
| `ENDPOINT` | STRING | Optional | Vertex AI endpoint. If not specified, BigQuery dynamically chooses a model. |
| `MAX_ERROR_RATIO` | FLOAT64 | Optional | Range 0.0–1.0, default 1.0. If the error ratio exceeds this threshold, the query fails with an error. |

**Outputs:**

| Return Type | Description |
|-------------|-------------|
| FLOAT64 | The score assigned to the input. **There is no fixed default range for the score** -- provide a scoring range in your prompt. |
| NULL | Returned if the call to Vertex AI is unsuccessful. |

**Supported models:** Any GA or preview Gemini model. Uses various `gemini-2.5-*` models.

**Best practices:**
- Provide a scoring range in your prompt (e.g., "On a scale from 1 to 10") since there is no fixed default range.
- AI.SCORE automatically rewrites your prompt to generate a scoring rubric.
- Combine with AI.IF to filter results before or alongside scoring.
- Use with ORDER BY and LIMIT for ranking.

**Limitations:** Preview status. Returns NULL on error. No model parameter control. No fixed default score range.

**Locations:** All regions supporting Gemini models, plus US and EU multi-regions.

**Provisioned throughput:** Not supported. Uses dynamic shared quota (DSQ) only.

**BigFrames API:** `bigframes.bigquery.ai.score(prompt)` — Returns a Series of FLOAT64 directly (not a struct). No endpoint param -- auto-selects model. Example: `bbq.ai.score(("Rate the negativity of: ", df["review"], " on scale 1-10"))`.

---

## `AI.CLASSIFY`
- **Description:** (Preview) Scalar function that uses a Vertex AI Gemini model to classify inputs into categories that you provide. BigQuery automatically structures your input to improve the quality of the classification.
- **Use cases:** Classify reviews by sentiment, classify products by categories, classify support tickets by topic, image classification by style or contents, multi-label classification.
- [documentation](https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-classify)
- **Type:** Scalar function -- returns STRING or ARRAY\<STRING\> per row (Preview)

**Syntax:**
```sql
AI.CLASSIFY(
  [ input => ] 'INPUT',
  [ categories => ] 'CATEGORIES'
  [, examples => EXAMPLES ]
  [, connection_id => 'CONNECTION' ]
  [, endpoint => 'ENDPOINT' ]
  [, output_mode => 'OUTPUT_MODE' ]
  [, embeddings => EMBEDDINGS ]
  [, optimization_mode => 'OPTIMIZATION_MODE' ]
  [, max_error_ratio => MAX_ERROR_RATIO ]
)
```

**Inputs:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `INPUT` | STRING or STRUCT | Required (must be first argument) | The input to classify. STRING or STRUCT with STRING/ARRAY\<STRING\>/ObjectRefRuntime/ARRAY\<ObjectRefRuntime\> fields. At most one video object. |
| `CATEGORIES` | ARRAY\<STRING\> or ARRAY\<STRUCT\<STRING, STRING\>\> | Required (must be second argument) | The categories to classify into. Without descriptions: `['positive', 'neutral', 'negative']`. With descriptions: `[('green', 'positive'), ('yellow', 'neutral'), ('red', 'negative')]`. Must be string literals (or use a DECLARE variable from a table column). |
| `EXAMPLES` | ARRAY\<STRUCT\<STRING, STRING\>\> (single) or ARRAY\<STRUCT\<STRING, ARRAY\<STRING\>\>\> (multi) | Optional | Few-shot examples. For single mode: maps input to expected category. For multi mode: maps input to expected array of categories. Example: `[("This is a great phone", "tech"), ("The match was exciting", "sport")]`. |
| `CONNECTION` | STRING | Optional | Connection to use, format: `[PROJECT_ID].LOCATION.CONNECTION_ID`. |
| `ENDPOINT` | STRING | Optional | Vertex AI endpoint. If not specified, BigQuery dynamically chooses a model. |
| `OUTPUT_MODE` | STRING | Optional | `'single'` or `'multi'`. Changes return type to ARRAY\<STRING\>. |
| `EMBEDDINGS` | (Preview) | Optional | Embeddings for optimized mode, same as AI.IF. |
| `OPTIMIZATION_MODE` | STRING | Optional (Preview) | `MINIMIZE_COST` or `MAXIMIZE_QUALITY`. Same as AI.IF. Note: `output_mode => 'multi'` is NOT supported in optimized mode. |
| `MAX_ERROR_RATIO` | FLOAT64 | Optional | Range 0.0–1.0, default 1.0. Not supported when `optimization_mode` is `MINIMIZE_COST`. |

**Categories from a table column (using DECLARE):**
```sql
DECLARE article_types ARRAY<STRING>
  DEFAULT (SELECT ARRAY_AGG(category) FROM mydataset.categories);

SELECT AI.CLASSIFY(body, categories => article_types) AS category
FROM `bigquery-public-data.bbc_news.fulltext`;
```

**Outputs:**

| Condition | Return Type | Description |
|-----------|-------------|-------------|
| No OUTPUT_MODE specified | STRING | The single category that best fits the input. |
| OUTPUT_MODE = 'single' | ARRAY\<STRING\> | Array of length 1 containing the best-fit category. |
| OUTPUT_MODE = 'multi' | ARRAY\<STRING\> | Array of 0 to N categories. Empty array if no category applies. |
| Error | NULL | Returned if the call to Vertex AI is unsuccessful. |

**Supported models:** Any GA or preview Gemini model. Uses various `gemini-2.5-*` models.

**Best practices:**
- Include an 'Other' category to handle input that doesn't closely match any category.
- Use categories with descriptions for more nuanced classification.
- Use `output_mode => 'multi'` when items may belong to multiple categories.

**Limitations:** Preview status. Returns NULL on error. Categories must be string literals in the array (unless using a variable). No model parameter control. `output_mode => 'multi'` is not supported in optimized mode. Optimized mode requires ~3,000 rows minimum; only string columns supported for multi-column inputs.

**Locations:** All regions supporting Gemini models, plus US and EU multi-regions.

**Provisioned throughput:** Not supported. Uses dynamic shared quota (DSQ) only.

**BigFrames API:** `bigframes.bigquery.ai.classify(input, categories)` — Returns a Series of STRING directly (not a struct). Takes `categories` as a list/tuple. Example: `bbq.ai.classify(df["text"], ["positive", "negative", "neutral"])`.

---

## `AI.AGG`
- **Description:** (Preview) Aggregate function that uses a Vertex AI Gemini model to aggregate data based on natural language instructions. Automatically performs multi-level aggregation through batching, so it can analyze data exceeding the Gemini context window. Returns a single STRING per group.
- **Use cases:** Sentiment analysis across reviews, content summarization of text or images, log analysis and incident investigation, agent performance analysis, finding common categories or patterns across data, summarizing grouped data.
- [documentation](https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-agg)
- **Type:** Aggregate function -- returns a single STRING value per group (Preview). Use with GROUP BY for per-group results; without GROUP BY, aggregates all rows.

**Syntax:**
```sql
AI.AGG(
  [ DISTINCT ]
  INPUT,
  INSTRUCTION
  [, connection_id => 'CONNECTION']
  [, endpoint => 'ENDPOINT']
)
```

**Inputs:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `DISTINCT` | keyword | Optional | When specified, deduplicates input values before aggregating. |
| `INPUT` | STRING or STRUCT | Required (must be first argument) | The data to aggregate. STRING value, or STRUCT consisting of STRING values, ObjectRefRuntime values, and arrays of STRING and ObjectRefRuntime values. ObjectRefRuntime values reference text or image data in Cloud Storage (generated by `OBJ.GET_ACCESS_URL`). |
| `INSTRUCTION` | STRING | Required (must be second argument) | Natural language aggregation prompt describing what to extract or summarize from the input data. Can be a string literal or query parameter. |
| `CONNECTION` | STRING | Optional | Connection to use, format: `[PROJECT_ID.]LOCATION.CONNECTION_ID`. If not specified, end-user credentials are used. |
| `ENDPOINT` | STRING | Optional | Vertex AI endpoint. Any Gemini model that doesn't require thinking budget. If not specified, BigQuery chooses a model for you. |

**Outputs:**

| Return Type | Description |
|-------------|-------------|
| STRING | The aggregated result for the group. One result per GROUP BY group, or one result total without GROUP BY. |
| STRING (partial) | If some Vertex AI calls fail, returns partial results from successful calls. |
| NULL | Returned if all calls to Vertex AI fail, or if all input rows are invalid. |

**Output cap:** 10,000 tokens per group.

**Supported models:** Any Gemini model that doesn't require thinking budget. If no endpoint specified, BigQuery dynamically chooses a model. Uses various `gemini-2.5-*` models.

**Best practices:**
- Use `TO_JSON_STRING` to pass multiple columns as structured input -- the model sees each row's full context.
- Use `DISTINCT` to remove duplicate inputs and reduce token usage.
- Keep groups under 20 million rows per query and under 1,000 distinct groups to avoid timeouts.
- Prefer AI.AGG over manual aggregation with AI.GENERATE (STRING_AGG/ARRAY_AGG into a prompt) -- AI.AGG handles batching automatically and scales beyond the context window.

**Limitations:** Preview status. Returns NULL on total failure (no detailed error info). No model parameter control (temperature, top_p, etc.). Output capped at 10,000 tokens per group. Recommended limit of 20 million rows per query and 1,000 distinct groups. Cannot use Gemini models that require thinking budget.

**Known issues:**
- Input rows with 10 or more images in a single row might be skipped.
- Input rows with arrays of ObjectRefRuntime objects that call `OBJ.GET_ACCESS_URL` might be skipped.
- Workforce Identity Federation without a specified Cloud resource connection may cause failures on long-running queries.
- Queries using Gemini 3.0 or 3.1 with connection-based authentication might receive an unauthenticated error.

**Cost caveat:** The actual number of rows processed by the model might differ from expectations, particularly with complex queries (JOIN, ORDER BY ... LIMIT). Materialize data to a separate table first to ensure predictable processing.

**Locations:** All regions supporting Gemini models, plus US and EU multi-regions.

**Provisioned throughput:** Not supported. Uses dynamic shared quota (DSQ) only.

**BigFrames API:** No native BigFrames API. Use `bpd.read_gbq_query(sql)` to execute AI.AGG queries and get results as a BigFrames DataFrame.
