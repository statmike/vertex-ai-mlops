![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2Fdata%2Bai%2Fbq-ai-functions%2Freference&file=general-purpose-functions.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/data%2Bai/bq-ai-functions/reference/general-purpose-functions.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-ai-functions/reference/general-purpose-functions.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-ai-functions/reference/general-purpose-functions.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-ai-functions/reference/general-purpose-functions.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-ai-functions/reference/general-purpose-functions.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
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
    <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/data%2Bai/bq-ai-functions/reference/general-purpose-functions.md"><img src="https://www.svgrepo.com/download/5445/download-button.svg" alt="Download icon" width="20px"></a> <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/data%2Bai/bq-ai-functions/reference/general-purpose-functions.md">Download File</a> <i>(right-click and "Save As")</i>
  </td>
</tr>
</table><br/><br/>

---
# General Purpose Functions

> Part of the [BigQuery AI Functions Resources](../RESOURCES.md) · [Project README](../README.md)

These functions send prompts to generative AI models and return generated text or structured output. They differ primarily in **function type** (scalar vs table-valued), **whether they require a pre-created model object**, and **output type** (free-form text, structured schema, or typed scalar values).

**Key relationships:**
- `AI.GENERATE` is the newest scalar function -- no model object needed, supports structured output via `output_schema`, defaults to `gemini-2.5-flash`.
- `AI.GENERATE_TEXT` is the recommended table-valued function -- requires a pre-created remote model (`CREATE MODEL`), supports Gemini, Claude, Llama, Mistral, and open models.
- `AI.GENERATE_TABLE` is like `AI.GENERATE_TEXT` but requires an `output_schema` for structured output columns (Gemini only).
- `AI.GENERATE_BOOL`, `AI.GENERATE_DOUBLE`, `AI.GENERATE_INT` are typed scalar variants of `AI.GENERATE` that return `BOOL`, `FLOAT64`, and `INT64` respectively (all Preview).
- `ML.GENERATE_TEXT` is the predecessor to `AI.GENERATE_TEXT` with `ml_generate_text_*` prefixed column names. Google recommends using `AI.GENERATE_TEXT` for new queries.
- `AI.COUNT_TOKENS` is a **utility** companion (not a generator): it estimates a prompt's input token count for free (no Vertex AI charge), so you can size and cost prompts before calling the functions above.

| Feature | AI.GENERATE | AI.GENERATE_TEXT | AI.GENERATE_TABLE | AI.GENERATE_BOOL | AI.GENERATE_DOUBLE | AI.GENERATE_INT | ML.GENERATE_TEXT |
|---------|-------------|------------------|-------------------|------------------|-------------------|-----------------|------------------|
| **Function Type** | Scalar | Table-valued | Table-valued | Scalar | Scalar | Scalar | Table-valued |
| **Status** | GA | GA | GA | Preview | Preview | Preview | GA (recommend AI.GENERATE_TEXT) |
| **Requires CREATE MODEL** | No | Yes | Yes | No | No | No | Yes |
| **Result Type** | STRING or custom schema | STRING | Custom schema | BOOL | FLOAT64 | INT64 | STRING (or JSON) |
| **Supports output_schema** | Yes | No | Yes (required) | No | No | No | No |
| **Default model** | gemini-2.5-flash | Set at CREATE MODEL | Set at CREATE MODEL | gemini-2.5-flash | gemini-2.5-flash | gemini-2.5-flash | Set at CREATE MODEL |
| **Non-Gemini models** | No | Yes (Claude, Llama, Mistral, Open) | No | No | No | No | Yes (Claude, Llama, Mistral, Open) |
| **Grounding** | Yes (via model_params) | Yes (ground_with_google_search) | No | No | No | No | Yes (ground_with_google_search) |
| **Provisioned Throughput** | Yes (request_type) | Yes (request_type) | Yes (request_type) | Yes (request_type) | Yes (request_type) | Yes (request_type) | Yes (request_type) |

---

## `AI.GENERATE`
- **Description:** Scalar function that analyzes any combination of structured and unstructured data. You can generate text or structured output according to a custom schema. Sends requests to a Vertex AI Gemini model and returns a STRUCT containing generated data, the full model response, and a status.
- **Use cases:** Summarization, translation, entity extraction, classification, sentiment analysis, image analysis/captioning (via ObjectRef), grounding with Google Search or Google Maps, any general-purpose generative AI task.
- [documentation](https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-generate)
- **Type:** Scalar function (returns a STRUCT value per row)

**Syntax:**
```sql
AI.GENERATE(
  [prompt =>] 'PROMPT',
  [, endpoint => 'ENDPOINT']
  [, model_params => MODEL_PARAMS]
  [, output_schema => 'OUTPUT_SCHEMA']
  [, connection_id => 'CONNECTION']
  [, request_type => 'REQUEST_TYPE']
)
```

**Inputs:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `prompt` (positional, must be first) | STRING or STRUCT | Required | -- | The prompt to send to the model. Can be a STRING value or a STRUCT containing one or more fields of type STRING, ARRAY\<STRING\>, ObjectRefRuntime, or ARRAY\<ObjectRefRuntime\>. STRUCT fields are concatenated in order (like CONCAT). At most one video object is allowed. |
| `endpoint` | STRING | Optional | `gemini-2.5-flash` | The Vertex AI endpoint for the model. Specify any GA or preview Gemini model by name (BigQuery auto-resolves the full endpoint). Can also specify a full global endpoint URL. |
| `model_params` | JSON literal | Optional | -- | Additional parameters conforming to the `generateContent` request body format. Can set any field except `contents`. Supports `thinking_config` (use `thinking_budget` for Gemini 2.5 models, `thinking_level` for Gemini 3.0+), `cachedContent`, `tools` (e.g., `googleSearch` — requires Gemini 2.0+, `googleMaps`), `generation_config`, etc. |
| `output_schema` | STRING | Optional | -- | Schema for structured output as comma-separated fields. Each field has a name, data type, and optional `OPTIONS(description = '...')`. Supported types: `STRING`, `INT64`, `FLOAT64`, `BOOL`, `ARRAY`, `STRUCT`. When specified, replaces the `result` field in output with custom schema fields. |
| `connection_id` | STRING | Optional | End-user credentials | Connection for model communication, in format `[PROJECT_ID].LOCATION.CONNECTION_ID`. |
| `request_type` | STRING | Optional | `UNSPECIFIED` | Quota type. Values: `SHARED` (DSQ only), `DEDICATED` (Provisioned Throughput only, error if unavailable), `UNSPECIFIED` (default -- uses Provisioned Throughput first if purchased, overflows to DSQ). |

**ObjectRef/Unstructured Data Input Details:**
- ObjectRefRuntime values generated by `OBJ.GET_ACCESS_URL(objectref_column, 'r')` or `OBJ.GET_ACCESS_URL(OBJ.MAKE_REF('gs://path', 'connection'), 'r')`
- Must have `access_url.read_url` and `details.gcs_metadata.content_type` populated
- Content must be in supported Gemini mimeType formats
- Video max length: 2 minutes (only first 2 minutes analyzed if longer)

**Outputs:**

Returns a STRUCT with:

| Field | Type | Description |
|-------|------|-------------|
| `result` | STRING (or custom schema if `output_schema` specified) | The model's response. NULL if request fails or is filtered by responsible AI. When `output_schema` is specified, this field is replaced by the custom schema columns. |
| `full_response` | JSON | Full response from `projects.locations.endpoints.generateContent`. |
| `status` | STRING | API response status. Empty if successful. |

**Supported models:** Any GA or preview Gemini model. Default: `gemini-2.5-flash`. Can use global endpoint for cross-region processing.

**Best practices:**
- Function incurs Vertex AI charges each time it is called. Track costs accordingly.
- To minimize charges when using LIMIT, materialize the selected data to a table first, then call AI.GENERATE on that table (avoids re-evaluating the subquery).

**Limitations:**
- Video input limited to 2 minutes maximum (only first 2 min processed).
- At most one video object per prompt.
- Global endpoint does not allow controlling or knowing the data processing region.
- Gemini 2.5 models incur thinking charges; budget can be set for Flash/Flash-Lite but not Pro.
- Google Search grounding requires Gemini 2.0 or later models.
- For Gemini 3.0+, use `thinking_level` (`LOW`, `MEDIUM`, `HIGH`) in `thinking_config` instead of `thinking_budget`.

**Locations:** All regions that support Gemini models, plus US and EU multi-regions.

**Provisioned throughput:** Supported via `request_type` parameter. Must purchase Provisioned Throughput quota matching the same Gemini model and region. For US multi-region: select `us-central1` region when purchasing. For EU multi-region: select `europe-west4` region when purchasing.

**BigFrames API:** `bigframes.bigquery.ai.generate()` — Scalar function returning a Series of structs. Supports `output_schema` as `Mapping[str, str]`. Prompt is a tuple of string literals and Series: `bbq.ai.generate(("Summarize: ", df["text"]), output_schema={"summary": "STRING"})`. Access result via `.struct.field("result")`.

---

## `AI.GENERATE_TEXT`
- **Description:** Table-valued function that performs generative natural language tasks using any combination of text and unstructured data from BigQuery standard tables, or unstructured data from BigQuery object tables. Requires a pre-created remote model via `CREATE MODEL` that represents a Vertex AI model.
- **Use cases:** Classification, sentiment analysis, image captioning, transcription, text enrichment/summarization, audio content analysis, PDF content analysis, visual content analysis, entity extraction with structured JSON output, Google Search grounding, context caching.
- [documentation](https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-generate-text)
- **Type:** Table-valued function (returns a table with input columns plus output columns)

**Syntax (Gemini, standard tables):**
```sql
AI.GENERATE_TEXT(
  MODEL `PROJECT_ID.DATASET.MODEL`,
  { TABLE `PROJECT_ID.DATASET.TABLE` | (QUERY_STATEMENT) },
  STRUCT(
    { { [MAX_OUTPUT_TOKENS AS max_output_tokens]
        [, TOP_P AS top_p]
        [, TEMPERATURE AS temperature]
        [, STOP_SEQUENCES AS stop_sequences]
        [, GROUND_WITH_GOOGLE_SEARCH AS ground_with_google_search]
        [, SAFETY_SETTINGS AS safety_settings]
      }
      | [, MODEL_PARAMS AS model_params]
    }
    [, REQUEST_TYPE AS request_type]
  )
)
```

**Syntax (Claude, standard tables):**
```sql
AI.GENERATE_TEXT(
  MODEL `PROJECT_ID.DATASET.MODEL`,
  { TABLE `PROJECT_ID.DATASET.TABLE` | (QUERY_STATEMENT) },
  STRUCT(
    { { [MAX_OUTPUT_TOKENS AS max_output_tokens]
        [, TOP_K AS top_k]
        [, TOP_P AS top_p]
      }
      | [, MODEL_PARAMS AS model_params]
    }
  )
)
```

**Syntax (Llama / Mistral AI, standard tables):**
```sql
AI.GENERATE_TEXT(
  MODEL `PROJECT_ID.DATASET.MODEL`,
  { TABLE `PROJECT_ID.DATASET.TABLE` | (QUERY_STATEMENT) },
  STRUCT(
    { { [MAX_OUTPUT_TOKENS AS max_output_tokens]
        [, TOP_P AS top_p]
        [, TEMPERATURE AS temperature]
        [, STOP_SEQUENCES AS stop_sequences]
      }
      | [, MODEL_PARAMS AS model_params]
    }
  )
)
```

**Syntax (Open models, standard tables):**
```sql
AI.GENERATE_TEXT(
  MODEL `PROJECT_ID.DATASET.MODEL`,
  { TABLE `PROJECT_ID.DATASET.TABLE` | (QUERY_STATEMENT) },
  STRUCT(
    { { [MAX_OUTPUT_TOKENS AS max_output_tokens]
        [, TOP_K AS top_k]
        [, TOP_P AS top_p]
        [, TEMPERATURE AS temperature]
        [, USE_CHAT_MODE AS use_chat_mode]
      }
      | [, MODEL_PARAMS AS model_params]
    }
  )
)
```

**Syntax (Object tables, Gemini only):**
```sql
AI.GENERATE_TEXT(
  MODEL `PROJECT_ID.DATASET.MODEL`,
  { TABLE `PROJECT_ID.DATASET.TABLE` | (QUERY_STATEMENT) },
  STRUCT(
    PROMPT AS prompt
    { { [, MAX_OUTPUT_TOKENS AS max_output_tokens]
        [, TOP_P AS top_p]
        [, TEMPERATURE AS temperature]
        [, STOP_SEQUENCES AS stop_sequences]
        [, SAFETY_SETTINGS AS safety_settings]
      }
      | [, MODEL_PARAMS AS model_params]
    }
  )
)
```

**Inputs (all model types combined):**

| Parameter | Type | Availability | Required | Default | Range | Description |
|-----------|------|-------------|----------|---------|-------|-------------|
| `MODEL` | Model reference | All | Required | -- | -- | Name of the remote model (`PROJECT_ID.DATASET.MODEL`) |
| `TABLE` / `QUERY_STATEMENT` | Table/Query | All | Required (one of) | -- | -- | Input data. Must have a `prompt` column. If no prompt column exists, use QUERY_STATEMENT with an alias. |
| `PROMPT` (object tables) | STRING | Gemini object tables | Required | -- | <16,000 tokens | Prompt for analyzing visual content |
| `max_output_tokens` | INT64 | All | Optional | 1024 | Gemini: [1,8192]; Claude/Llama/Mistral/Open: [1,4096] | Max tokens in response |
| `top_p` | FLOAT64 | All | Optional | 0.95 (Gemini, Llama, Mistral); model-determined (Claude, Open) | [0.0, 1.0] | Nucleus sampling parameter |
| `temperature` | FLOAT64 | Gemini, Llama, Mistral, Open | Optional | 0 (Gemini, Llama, Mistral); model-determined (Open) | [0.0, 1.0] | Randomness in token selection |
| `top_k` | INT64 | Claude, Open | Optional | Model-determined | [1, 40] | Top-K sampling |
| `stop_sequences` | ARRAY\<STRING\> | Gemini, Llama, Mistral | Optional | Empty array | -- | Strings to exclude from responses |
| `ground_with_google_search` | BOOL | Gemini | Optional | FALSE | -- | Enable Google Search grounding |
| `safety_settings` | ARRAY\<STRUCT\<STRING AS category, STRING AS threshold\>\> | Gemini | Optional | BLOCK_MEDIUM_AND_ABOVE | -- | Content safety filtering |
| `request_type` | STRING | Gemini | Optional | UNSPECIFIED | SHARED, DEDICATED, UNSPECIFIED | Quota type for Provisioned Throughput |
| `use_chat_mode` | BOOL | Open models | Optional | FALSE | -- | When TRUE, enables chat mode for open models. |
| `model_params` | JSON string | All | Optional | -- | -- | JSON conforming to generateContent request body. Cannot be used simultaneously with top-level parameters. |

Safety settings categories: `HARM_CATEGORY_HATE_SPEECH`, `HARM_CATEGORY_DANGEROUS_CONTENT`, `HARM_CATEGORY_HARASSMENT`, `HARM_CATEGORY_SEXUALLY_EXPLICIT`

Safety thresholds: `BLOCK_NONE` (Restricted), `BLOCK_LOW_AND_ABOVE`, `BLOCK_MEDIUM_AND_ABOVE` (Default), `BLOCK_ONLY_HIGH`, `HARM_BLOCK_THRESHOLD_UNSPECIFIED`

**Outputs (vary by model type):**

All models return the input table columns plus:

| Model Type | Column | Type | Description |
|------------|--------|------|-------------|
| Gemini | `result` | STRING | Generated text |
| Gemini | `rai_result` | JSON | Responsible AI result/safety attributes |
| Gemini | `grounding_result` | JSON | Grounding sources (when grounding enabled) |
| Gemini | `statistics` | JSON | Generation statistics (e.g., token counts) |
| Gemini | `full_response` | JSON | Complete Vertex AI API JSON response |
| Gemini | `status` | STRING | API status (empty = success) |
| Claude | `result` | STRING | Generated text |
| Claude | `full_response` | JSON | Complete Vertex AI API JSON response |
| Claude | `status` | STRING | API status |
| Llama | `result` | STRING | Generated text |
| Llama | `full_response` | JSON | Complete Vertex AI API JSON response |
| Llama | `status` | STRING | API status |
| Mistral AI | `result` | STRING | Generated text |
| Mistral AI | `full_response` | JSON | Complete Vertex AI API JSON response |
| Mistral AI | `status` | STRING | API status |
| Open models | `result` | STRING | Generated text |
| Open models | `full_response` | JSON | Complete Vertex AI API JSON response |
| Open models | `status` | STRING | API status |

**Supported models:** Remote models over any GA or preview Gemini models, Anthropic Claude models, Mistral AI models, Llama models, and supported open models (all via `CREATE MODEL`).

**Best practices:**
- Avoid using LIMIT and OFFSET in the prompt query (causes processing all data first). Write query results to a table first, then reference that table.
- Model and input table must be in the same region.

**Limitations:**
- Model and input table must be in the same region.
- Resource exhausted errors can occur for some rows when API call volume exceeds quota limits. Use BigQuery remote inference SQL scripts or Dataform package to handle quota errors iteratively.
- Gemini 2.5 models incur thinking process charges.
- Object table Cloud Storage bucket must be in the same project as the model.
- Object table queries only support WHERE and ORDER BY clauses.
- Object table prompt must be under 16,000 tokens.

**Locations:** Must run in the same region or multi-region as the remote model. Gemini: all supported Gemini regions plus US and EU multi-regions. Claude, Llama, Mistral AI: see Google Cloud partner model endpoint locations.

**Provisioned throughput:** Supported via `request_type` parameter; must pre-purchase matching quota.

**BigFrames API:** `bigframes.bigquery.ai.generate_text(model, data)` — TVF wrapper that takes a model name string and DataFrame/Series. Also available as `bigframes.ml.llm.GeminiTextGenerator` (sklearn-style: create model, then `.predict()`). GeminiTextGenerator also supports `.fit()` for fine-tuning and `.score()` for evaluation. For Claude models: `bigframes.ml.llm.Claude3TextGenerator`.

---

## `AI.GENERATE_TABLE`
- **Description:** Table-valued function that performs generative natural language tasks and formats the response according to a user-specified schema. Requires a pre-created remote model representing a Vertex AI Gemini model.
- **Use cases:** Classification, sentiment analysis, image captioning, transcription, entity extraction with structured output, data formatting/enrichment using custom schemas.
- [documentation](https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-generate-table)
- **Type:** Table-valued function (returns a table with input columns plus structured output columns)

**Syntax:**
```sql
AI.GENERATE_TABLE(
  MODEL `PROJECT_ID.DATASET.MODEL`,
  { TABLE `PROJECT_ID.DATASET.TABLE` | (QUERY_STATEMENT) },
  STRUCT(
    OUTPUT_SCHEMA AS output_schema
    [, MAX_OUTPUT_TOKENS AS max_output_tokens]
    [, TOP_P AS top_p]
    [, TEMPERATURE AS temperature]
    [, STOP_SEQUENCES AS stop_sequences]
    [, SAFETY_SETTINGS AS safety_settings]
    [, REQUEST_TYPE AS request_type]
  )
)
```

**Inputs:**

| Parameter | Type | Required | Default | Range | Description |
|-----------|------|----------|---------|-------|-------------|
| `MODEL` | Model reference | Required | -- | -- | Name of the remote model (must be a Gemini model) |
| `TABLE` / `QUERY_STATEMENT` | Table/Query | Required (one of) | -- | -- | Input data. Must produce a `prompt` column. |
| `output_schema` | STRING | Required | -- | -- | Schema as comma-separated fields with name, type, optional `OPTIONS(description='...')`. Supported types: `STRING`, `INT64`, `FLOAT64`, `BOOL`, `ARRAY`, `STRUCT`. |
| `max_output_tokens` | INT64 | Optional | Model-determined | [1, 8192] | Max tokens in response |
| `top_p` | FLOAT64 | Optional | Model-determined | [0.0, 1.0] | Nucleus sampling |
| `temperature` | FLOAT64 | Optional | Model-determined | [0.0, 2.0] | Randomness control |
| `stop_sequences` | ARRAY\<STRING\> | Optional | Empty array | -- | Strings to exclude |
| `safety_settings` | ARRAY\<STRUCT\<STRING AS category, STRING AS threshold\>\> | Optional | BLOCK_MEDIUM_AND_ABOVE | -- | Content safety thresholds |
| `request_type` | STRING | Optional | UNSPECIFIED | SHARED, DEDICATED, UNSPECIFIED | Provisioned Throughput quota control |

Prompt input can be a STRING value or a STRUCT value with STRING, ARRAY\<STRING\>, ObjectRefRuntime, or ARRAY\<ObjectRefRuntime\> fields (same semantics as AI.GENERATE_TEXT).

**Outputs:**

| Column | Type | Description |
|--------|------|-------------|
| All input table columns | (varies) | Pass-through of input |
| Custom schema columns | As specified in `output_schema` | Columns from your schema definition |
| `full_response` | JSON | Response from `projects.locations.endpoints.generateContent` |
| `status` | STRING | API response status (empty = success) |

**Supported models:** Remote models over any GA or preview Gemini models (via CREATE MODEL).

**Best practices:** To minimize Vertex AI charges, write query results to a table and then reference that table. Model and input table must be in the same region.

**Limitations:** Model and input table must be in the same region. Resource exhausted errors possible. Video limited to 2 minutes. Gemini 2.5 models incur thinking charges.

**Locations:** Must run in the same region or multi-region as the remote model. Supported Gemini regions plus US and EU multi-regions.

**Provisioned throughput:** Supported via `request_type` parameter.

**BigFrames API:** `bigframes.bigquery.ai.generate_table(model, data, output_schema=...)` — TVF wrapper that takes a model name string, DataFrame/Series, and required `output_schema` (string or mapping). Also accessible via `GeminiTextGenerator.predict(X, output_schema={"col": "type"})` which routes to GENERATE_TABLE under the hood.

---

## `AI.GENERATE_BOOL`
- **Description:** (Preview) Scalar function that analyzes any combination of text and unstructured data, returning a STRUCT containing a BOOL value for each row. Sends requests to a Vertex AI Gemini model. Contact `bqml-feedback@google.com` for support during preview.
- **Use cases:** Classification (e.g., "Is this article about technology?"), boolean filtering in WHERE clauses, sentiment analysis (positive/negative as boolean), image classification (e.g., "Is this cat food?").
- [documentation](https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-generate-bool)
- **Type:** Scalar function (returns a STRUCT value per row) -- Preview

**Syntax:**
```sql
AI.GENERATE_BOOL(
  [prompt =>] 'PROMPT',
  [, endpoint => 'ENDPOINT']
  [, model_params => MODEL_PARAMS]
  [, connection_id => 'CONNECTION']
  [, request_type => 'REQUEST_TYPE']
)
```

**Inputs:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `prompt` (positional, must be first) | STRING or STRUCT | Required | -- | Same semantics as AI.GENERATE: STRING or STRUCT with STRING/ARRAY\<STRING\>/ObjectRefRuntime/ARRAY\<ObjectRefRuntime\> fields. At most one video. |
| `endpoint` | STRING | Optional | `gemini-2.5-flash` | Any GA or preview Gemini model. BigQuery auto-resolves the full endpoint from model name -- see [Choosing a Gemini Model Endpoint](../RESOURCES.md#choosing-a-gemini-model-endpoint) for the 3.x multi-regional restriction. |
| `model_params` | JSON literal | Optional | -- | Conforms to generateContent request body (all fields except `contents`). Supports thinking_config, etc. |
| `connection_id` | STRING | Optional | End-user credentials | Format: `[PROJECT_ID].LOCATION.CONNECTION_ID` |
| `request_type` | STRING | Optional | UNSPECIFIED | `SHARED`, `DEDICATED`, `UNSPECIFIED` |

**Outputs:**

Returns a STRUCT per row:

| Field | Type | Description |
|-------|------|-------------|
| `result` | BOOL | Model's boolean response. NULL if request fails or is filtered. |
| `full_response` | JSON | Full response from `projects.locations.endpoints.generateContent`. |
| `status` | STRING | API response status (empty = success). |

**Supported models:** Any GA or preview Gemini model. Default: `gemini-2.5-flash`.

**Best practices:** Incurs Vertex AI charges each call. Materialize data to a table before calling with LIMIT to minimize charges.

**Limitations:** Preview feature (Pre-GA Offerings Terms apply). Video limited to 2 minutes. At most one video object per prompt. Gemini 2.5 thinking charges apply. For Gemini 3.0+, use `thinking_level` in `thinking_config` instead of `thinking_budget`.

**Locations:** All regions supporting Gemini models, plus US and EU multi-regions.

**Provisioned throughput:** Supported via `request_type` parameter.

**BigFrames API:** `bigframes.bigquery.ai.generate_bool(prompt)` — Scalar function returning a Series of structs with BOOL result. Same tuple prompt pattern: `bbq.ai.generate_bool(("Is ", df["item"], " a fruit?"))`. Access result via `.struct.field("result")`.

---

## `AI.GENERATE_DOUBLE`
- **Description:** (Preview) Scalar function that analyzes any combination of text and unstructured data, returning a STRUCT containing a FLOAT64 value. Sends requests to a Vertex AI Gemini model. Contact `bqml-feedback@google.com` for support during preview.
- **Use cases:** Numeric estimation, scoring/rating, classification with numeric confidence, sentiment analysis with numeric score.
- [documentation](https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-generate-double)
- **Type:** Scalar function (returns a STRUCT value per row) -- Preview

**Syntax:**
```sql
AI.GENERATE_DOUBLE(
  [prompt =>] 'PROMPT',
  [, endpoint => 'ENDPOINT']
  [, model_params => MODEL_PARAMS]
  [, connection_id => 'CONNECTION']
  [, request_type => 'REQUEST_TYPE']
)
```

**Inputs:** Identical parameter set to AI.GENERATE_BOOL (see above for full details).

**Outputs:**

Returns a STRUCT per row:

| Field | Type | Description |
|-------|------|-------------|
| `result` | FLOAT64 | Model's numeric response. NULL if request fails or is filtered. |
| `full_response` | JSON | Full response from generateContent. |
| `status` | STRING | API response status (empty = success). |

**Supported models:** Any GA or preview Gemini model. Default: `gemini-2.5-flash`.

**Best practices:** Same as AI.GENERATE_BOOL.

**Limitations:** Same as AI.GENERATE_BOOL (Preview, video limits, thinking charges).

**Locations:** All Gemini-supporting regions plus US and EU multi-regions.

**Provisioned throughput:** Supported via `request_type` parameter.

**BigFrames API:** `bigframes.bigquery.ai.generate_double(prompt)` — Scalar function returning a Series of structs with FLOAT64 result. Same tuple prompt pattern as generate_bool. Access result via `.struct.field("result")`.

---

## `AI.GENERATE_INT`
- **Description:** (Preview) Scalar function that analyzes any combination of text and unstructured data, returning a STRUCT containing an INT64 value. Sends requests to a Vertex AI Gemini model. Contact `bqml-feedback@google.com` for support during preview.
- **Use cases:** Population counts / numeric fact retrieval, counting / quantity estimation, classification with integer labels, scoring with integer values.
- [documentation](https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-generate-int)
- **Type:** Scalar function (returns a STRUCT value per row) -- Preview

**Syntax:**
```sql
AI.GENERATE_INT(
  [prompt =>] 'PROMPT',
  [, endpoint => 'ENDPOINT']
  [, model_params => MODEL_PARAMS]
  [, connection_id => 'CONNECTION']
  [, request_type => 'REQUEST_TYPE']
)
```

**Inputs:** Identical parameter set to AI.GENERATE_BOOL (see above for full details).

**Outputs:**

Returns a STRUCT per row:

| Field | Type | Description |
|-------|------|-------------|
| `result` | INT64 | Model's integer response. NULL if request fails or is filtered. |
| `full_response` | JSON | Full response from generateContent. |
| `status` | STRING | API response status (empty = success). |

**Supported models:** Any GA or preview Gemini model. Default: `gemini-2.5-flash`.

**Best practices:** Same as AI.GENERATE_BOOL.

**Limitations:** Same as AI.GENERATE_BOOL (Preview, video limits, thinking charges).

**Locations:** All Gemini-supporting regions plus US and EU multi-regions.

**Provisioned throughput:** Supported via `request_type` parameter.

**BigFrames API:** `bigframes.bigquery.ai.generate_int(prompt)` — Scalar function returning a Series of structs with INT64 result. Same tuple prompt pattern as generate_bool. Access result via `.struct.field("result")`.

---

## `ML.GENERATE_TEXT`
- **Description:** Table-valued function that performs generative natural language tasks. Functionally identical to `AI.GENERATE_TEXT` but with `ml_generate_text_*` prefixed column names and an additional `flatten_json_output` parameter. **Google recommends using `AI.GENERATE_TEXT` instead for new queries.**
- **Use cases:** Same as AI.GENERATE_TEXT: classification, sentiment analysis, image captioning, transcription, text enrichment, audio analysis, PDF analysis, etc.
- [documentation](https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-generate-text)
- **Type:** Table-valued function (returns a table with input columns plus output columns)

**Syntax (Gemini, standard tables):**
```sql
ML.GENERATE_TEXT(
  MODEL `PROJECT_ID.DATASET.MODEL`,
  { TABLE `PROJECT_ID.DATASET.TABLE` | (QUERY_STATEMENT) },
  STRUCT(
    { { [MAX_OUTPUT_TOKENS AS max_output_tokens]
        [, TOP_P AS top_p]
        [, TEMPERATURE AS temperature]
        [, STOP_SEQUENCES AS stop_sequences]
        [, GROUND_WITH_GOOGLE_SEARCH AS ground_with_google_search]
        [, SAFETY_SETTINGS AS safety_settings]
      }
      | [, MODEL_PARAMS AS model_params]
    }
    [, FLATTEN_JSON_OUTPUT AS flatten_json_output]
    [, REQUEST_TYPE AS request_type]
  )
)
```

Other model type syntaxes (Claude, Llama, Mistral AI, Open models, Object tables) follow the same pattern as AI.GENERATE_TEXT but with the added `flatten_json_output` parameter.

**Key difference from AI.GENERATE_TEXT -- The `flatten_json_output` parameter:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `flatten_json_output` | BOOL | FALSE | When TRUE, JSON response is parsed into separate columns (changes column names). |

All other parameters are identical to AI.GENERATE_TEXT.

**Outputs (key difference -- column naming):**

When `flatten_json_output` is FALSE (default):

| Column | Type | Description |
|--------|------|-------------|
| `ml_generate_text_result` | JSON | Full JSON response |
| `ml_generate_text_status` | STRING | API status (empty = success) |

When `flatten_json_output` is TRUE:

| Column | Type | Description |
|--------|------|-------------|
| `ml_generate_text_llm_result` | STRING | Generated text |
| `ml_generate_text_rai_result` | STRING | Safety ratings (Gemini only, when safety_settings specified) |
| `ml_generate_text_grounding_result` | STRING | Grounding sources (Gemini only, when ground_with_google_search is TRUE) |
| `ml_generate_text_status` | STRING | API status |

**Supported models:** Same as AI.GENERATE_TEXT (remote models over Gemini, Claude, Llama, Mistral, open models). Also explicitly supports remote models over fine-tuned Gemini models.

**Best practices / Limitations / Locations / Provisioned throughput:** Same as AI.GENERATE_TEXT.

**BigFrames API:** No direct `ML.GENERATE_TEXT` wrapper. BigFrames routes through `AI.GENERATE_TEXT` instead. Use `bbq.ai.generate_text()` or `GeminiTextGenerator`/`Claude3TextGenerator` classes (which generate `AI.GENERATE_TEXT` SQL under the hood).

---

## `AI.COUNT_TOKENS`
- **Description:** (Preview) Utility scalar function that estimates the **input** token count of a text prompt. Token counting happens inside BigQuery and **incurs no Vertex AI charges** — unlike the generative functions, it does not send a generation request. Use it to estimate the cost or size of prompts before calling the paid AI functions.
- **Use cases:** Estimating the cost of an `AI.GENERATE` / `AI.GENERATE_TABLE` job before running it, checking prompts against a model's input token limit, comparing prompt sizes across rows/templates/models.
- [documentation](https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-count-tokens)
- **Type:** Scalar function (returns a STRUCT value per row) — Preview

**Syntax:**
```sql
AI.COUNT_TOKENS(
  INPUT
  [, endpoint => ENDPOINT]
)
```

**Inputs:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `INPUT` | STRING | Required | -- | The input text prompt for which to count tokens. |
| `endpoint` | STRING literal (named parameter) | Optional | The default model used by `AI.GENERATE` | Name of the generative AI model whose tokenization rules to use (e.g. `'gemini-2.5-pro'`). |

**Outputs:** Returns a `STRUCT` with:

| Field | Type | Description |
|-------|------|-------------|
| `result` | INT64 | Total **input** token count. `NULL` if the input is `NULL` or an API error occurred. |
| `full_response` | JSON | Per-modality token detail, e.g. `{"promptTokensDetails":[{"modality":"TEXT","tokenCount":180}],"totalTokens":180}`. `NULL` on `NULL` input or API error. |

**Best practices:**
- Because counting is free, aggregate `AI.COUNT_TOKENS(col).result` across a column (`SUM`/`AVG`/`MAX`) to size a batch workload before running the paid generation functions over it.
- Match the `endpoint` to the model you plan to generate with, so the token estimate reflects that model's tokenizer.

**Limitations:**
- Counts **input** tokens only — **thinking and output tokens are not included**. To see actual token counts (input + thinking + output) for a query, view the **Job information** tab of the Query results pane.
- **Text input only (verified 2026-07-17, Preview).** The `INPUT` argument coerces to `STRING` only — multimodal/ObjectRef prompts are rejected: both a STRUCT prompt (`STRUCT(text AS prompt, [...] AS object_ref_runtime)`, the AI.GENERATE pattern) and a bare `ObjectRefRuntime` fail with "Unable to coerce type ... to expected type STRING." Accordingly, `full_response.promptTokensDetails[].modality` is always `TEXT`. **This is a Preview function — re-evaluate multimodal support when it reaches GA, and re-test ObjectRef at that time** (AI.PARSE_DOCUMENT is precedent for multimodal input arriving without an obvious signature change).

**Undocumented parameters (verified 2026-07-17):** the function's actual signature is `AI.COUNT_TOKENS(STRING, [endpoint => STRING], [title => STRING], [model => STRING])` — but only `endpoint` is documented and usable. `model` is mutually exclusive with `endpoint` and rejected every tested value (bare Gemini strings and a remote MODEL reference: "Unsupported model"); `title` errors with "Title argument is not supported for gemini-2.5-flash." Both appear reserved (likely for non-Gemini/open models or a future capability). Do not teach these until they are documented and functional — re-check at GA.

**Locations:** All BigQuery regions supporting the generative AI functions (US and EU multi-regions, plus supported Gemini regions).

**Provisioned throughput:** Not applicable — no Vertex AI request is made.

**BigFrames API:** No native wrapper. Use `%%bigquery` magics or `session.read_gbq_query()` to run `AI.COUNT_TOKENS` SQL from BigFrames.
