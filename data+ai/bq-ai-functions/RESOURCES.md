![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2Fdata%2Bai%2Fbq-ai-functions&file=RESOURCES.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/data%2Bai/bq-ai-functions/RESOURCES.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-ai-functions/RESOURCES.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-ai-functions/RESOURCES.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-ai-functions/RESOURCES.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-ai-functions/RESOURCES.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
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
    <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/data%2Bai/bq-ai-functions/RESOURCES.md"><img src="https://www.svgrepo.com/download/5445/download-button.svg" alt="Download icon" width="20px"></a> <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/data%2Bai/bq-ai-functions/RESOURCES.md">Download File</a> <i>(right-click and "Save As")</i>
  </td>
</tr>
</table><br/><br/>

---
# BigQuery AI Functions Resources

BigQuery AI functions let you use generative AI, embeddings, search, forecasting, and tabular prediction directly within SQL queries. These functions span several categories: general-purpose text/multimodal generation, managed classification and scoring, embedding generation and semantic/hybrid search, and predictive AI (forecasting, anomaly detection, regression, and classification). They connect to Vertex AI models (Gemini, embedding models, TimesFM, TabFM, and third-party models) and can process structured data, text, images, audio, video, and PDFs -- all from within BigQuery SQL.

For each function below we collect top level info. The documentation url is provided for each as a research retrieval page to help fill in this structure for each:
Function Name
- short description of type of function and what it does
- what this function can be used for examples
- documentation url:
- syntax
- inputs: list all possible inputs and combinations, calling out use of object refs and schemas
- outputs: list all possible outputs and their schemas (can be links)
- type: table valued, ....
- supported models: which gen ai models can be requested
- best practices
- limitations
- locations
- provisioned throughput usage

---
## General Purpose Functions

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

### `AI.GENERATE`
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

### `AI.GENERATE_TEXT`
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

### `AI.GENERATE_TABLE`
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

### `AI.GENERATE_BOOL`
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
| `endpoint` | STRING | Optional | `gemini-2.5-flash` | Any GA or preview Gemini model. BigQuery auto-resolves the full endpoint from model name. |
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

### `AI.GENERATE_DOUBLE`
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

### `AI.GENERATE_INT`
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

### `ML.GENERATE_TEXT`
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

### `AI.COUNT_TOKENS`
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

---
## Managed Functions

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

### `AI.IF`
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

### `AI.SCORE`
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

### `AI.CLASSIFY`
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

### `AI.AGG`
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

---
## Embedding Generation and Semantic Search

These functions create vector embeddings from text and multimodal data, compute similarity between inputs, and perform semantic search over embedding-indexed tables.

**Key relationships:**
- `AI.EMBED` is the scalar embedding function -- no model object needed, specify endpoint directly.
- `AI.GENERATE_EMBEDDING` is the recommended table-valued embedding function -- requires a pre-created remote model.
- `ML.GENERATE_EMBEDDING` is the predecessor to `AI.GENERATE_EMBEDDING` with `ml_generate_embedding_*` prefixed column names. Google recommends `AI.GENERATE_EMBEDDING` for new queries.
- `AI.SIMILARITY` computes cosine similarity between two inputs by generating embeddings at runtime -- good for prototyping and small comparisons.
- `VECTOR_SEARCH` performs top-K nearest neighbor search on pre-computed embeddings -- supports vector indexes for efficient ANN search.
- `AI.SEARCH` is a simplified semantic search over tables with autonomous embedding generation enabled.
- **Hybrid search** (semantic + keyword) is a *capability* of `VECTOR_SEARCH` and `AI.SEARCH`, not a separate function. See [Hybrid Search](#hybrid-search-capability).

| Feature | AI.EMBED | AI.GENERATE_EMBEDDING | ML.GENERATE_EMBEDDING | AI.SIMILARITY | VECTOR_SEARCH | AI.SEARCH |
|---------|----------|----------------------|----------------------|---------------|---------------|-----------|
| **Type** | Scalar | TVF | TVF | Scalar | TVF | TVF |
| **Status** | Preview | GA (some Preview) | GA (some Preview) | Preview | GA (single search Preview) | GA (`mode` Preview) |
| **Requires Model Object** | No (endpoint param) | Yes (MODEL reference) | Yes (MODEL reference) | No (endpoint param) | No | No (uses table config) |
| **Input Data** | Single value | Table/Query | Table/Query | Two values | Table/Query + Table/Query or single value | Table/Query + string literal |
| **Output** | STRUCT(result, status) | Table with embedding + stats | Table with ml_generate_embedding_* cols | FLOAT64 | Table with query/base/distance | Table with base/distance |
| **Supports Images/Video** | Yes (multimodal) | Yes (multimodal, object tables) | Yes (multimodal, object tables) | Yes (multimodal) | No (pre-computed only) | No (text only) |
| **Supports PCA/Autoencoder/MF** | No | Yes | Yes | No | No | No |
| **Uses Vector Index** | No | No | No | No | Yes | Yes |
| **Requires Autonomous Embedding** | No | No | No | No | Optional (for STRING cols) | Yes (required) |
| **Supports Hybrid Search** | No | No | No | No | Yes (single search only) | Yes (`mode => 'HYBRID'`) |

---

### `AI.EMBED`
- **Description:** (Preview) Scalar function that creates embeddings from text or image data. Sends a request to a stable Vertex AI embedding model and returns the model's response. No pre-created model object required.
- **Use cases:** Semantic search, recommendation, classification, clustering, outlier detection.
- [documentation](https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-embed)
- **Type:** Scalar function (returns a STRUCT value per row) -- Preview

**Syntax (text embedding with endpoint):**
```sql
AI.EMBED(
  [content =>] 'content',
  endpoint => 'endpoint'
  [, task_type => 'task_type']
  [, title => 'title']
  [, model_params => model_params]
  [, connection_id => 'connection']
)
```

**Syntax (text embedding with built-in model — Preview):**
```sql
AI.EMBED(
  [content =>] 'content',
  model => 'model'
)
```

**Syntax (multimodal embedding):**
```sql
AI.EMBED(
  [content =>] 'content',
  connection_id => 'connection',
  endpoint => 'endpoint'
  [, model_params => model_params]
)
```

**Inputs:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `content` | STRING, ObjectRef, ObjectRefRuntime, or STRUCT | Required | The data to embed. For text: string literal, column name, or expression. For images: ObjectRef/ObjectRefRuntime. For `gemini-embedding-2-preview`: can be a STRUCT containing STRING, ARRAY\<STRING\>, ObjectRef, and ARRAY\<ObjectRef\> (text, images, audio, video, PDFs). |
| `endpoint` | STRING | Required (unless `model` specified) | Vertex AI embedding model endpoint. Must include model version (e.g., `text-embedding-005`, `multimodalembedding@001`, `gemini-embedding-2-preview`). BigQuery auto-resolves full endpoint from model name. |
| `model` | STRING | Optional (Preview) | Built-in text embedding model. Only supported value: `embeddinggemma-300m` (768 dims, 2048 tokens). When specified, cannot use `endpoint`, `title`, `model_params`, or `connection_id`. Data stays in BigQuery — no Vertex AI charges, uses BQ slots. |
| `task_type` | STRING literal | Optional (text only) | Intended downstream application. Values: `RETRIEVAL_QUERY`, `RETRIEVAL_DOCUMENT`, `SEMANTIC_SIMILARITY`, `CLASSIFICATION`, `CLUSTERING`, `QUESTION_ANSWERING`, `FACT_VERIFICATION`, `CODE_RETRIEVAL_QUERY` |
| `title` | STRING | Optional (text only) | Document title to improve embedding quality. Can only be used when `task_type` is `RETRIEVAL_DOCUMENT`. |
| `model_params` | JSON literal | Optional | For text: any parameters object fields including `outputDimensionality`. For multimodal: only the `dimension` field is supported. |
| `connection_id` | STRING | Optional for text; Required for multimodal | Connection in format `PROJECT_ID.LOCATION.CONNECTION_ID`. The connection's service account needs the Vertex AI User role. If query runs 48+ hours, use a connection. |

**Outputs:**

Returns a STRUCT with:

| Field | Type | Description |
|-------|------|-------------|
| `result` | ARRAY\<FLOAT64\> | The generated embedding vector. |
| `status` | STRING | API response status (empty string if successful). |

**Supported models:**

| Model | Type | Max Dimensions | Max Tokens | Notes |
|-------|------|----------------|------------|-------|
| `model => 'embeddinggemma-300m'` (Preview) | Built-in text | 768 | 2048 | No Vertex AI charges, uses BQ slots |
| `endpoint => 'gemini-embedding-001'` | Text | up to 3072 | 2048 | Multilingual |
| `endpoint => 'text-embedding-005'` | Text | up to 768 | 2048 | English |
| `endpoint => 'text-multilingual-embedding-002'` | Text | up to 768 | 2048 | Multilingual |
| `endpoint => 'gemini-embedding-2-preview'` (Preview) | Multimodal | up to 3072 | 8192 | Text, images, audio, video, PDF. US and us-central1 only. `task_type`/`title` not compatible. |
| `endpoint => 'multimodalembedding@001'` | Multimodal | 128, 256, 512, 1408 | — | Images only (JPEG, PNG, BMP, GIF — not PDF) |

**Best practices:**
- If you need to reuse embeddings across many queries, save results to a table.
- For multimodal input, use the inline ObjectRef pipeline (`OBJ.MAKE_REF` → `OBJ.FETCH_METADATA` → `OBJ.GET_ACCESS_URL`) to pass image content. This avoids needing an object table or BigQuery reservation.
- `multimodalembedding@001` supports images only (JPEG, PNG, BMP, GIF) — **not PDFs**. Render PDFs to images first (e.g., using `pdftoppm`).

**Limitations:** Image content must be in supported formats (JPEG, PNG, BMP, GIF — not PDF). For multimodal embeddings, `connection_id` is required and the connection's service account needs `roles/aiplatform.user` and `roles/storage.objectViewer`. Incurs Vertex AI charges per call.

**Locations:** All locations supporting Vertex AI embedding models, plus US and EU multi-regions.

**Provisioned throughput:** Not specified in documentation.

**BigFrames API:** No direct equivalent. Use `%%bigquery` magics or `session.read_gbq_query()` to execute AI.EMBED SQL from BigFrames. For table-valued embedding generation, use `bbq.ai.generate_embedding()` instead.

---

### `AI.GENERATE_EMBEDDING`
- **Description:** Table-valued function that creates embeddings from text, image, video data, or from PCA, autoencoder, and matrix factorization models. Requires a pre-created remote model via `CREATE MODEL`. This is the recommended embedding TVF for new queries.
- **Use cases:** Semantic search, recommendation, classification, clustering, outlier detection, PCA, autoencoding, matrix factorization.
- [documentation](https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-generate-embedding)
- **Type:** Table-valued function (returns a table)

**Syntax (text embedding):**
```sql
AI.GENERATE_EMBEDDING(
  MODEL `PROJECT_ID.DATASET.MODEL_NAME`,
  { TABLE `PROJECT_ID.DATASET.TABLE_NAME` | (QUERY_STATEMENT) },
  STRUCT(
    [, TASK_TYPE AS task_type]
    [, OUTPUT_DIMENSIONALITY AS output_dimensionality]
  )
)
```

**Syntax (open models):**
```sql
AI.GENERATE_EMBEDDING(
  MODEL `PROJECT_ID.DATASET.MODEL_NAME`,
  { TABLE `PROJECT_ID.DATASET.TABLE_NAME` | (QUERY_STATEMENT) }
)
```

**Syntax (multimodal, standard tables):**
```sql
AI.GENERATE_EMBEDDING(
  MODEL `PROJECT_ID.DATASET.MODEL_NAME`,
  { TABLE `PROJECT_ID.DATASET.TABLE_NAME` | (QUERY_STATEMENT) },
  STRUCT(
    [, OUTPUT_DIMENSIONALITY AS output_dimensionality]
  )
)
```

**Syntax (multimodal, object tables):**
```sql
AI.GENERATE_EMBEDDING(
  MODEL `PROJECT_ID.DATASET.MODEL_NAME`,
  { TABLE `PROJECT_ID.DATASET.TABLE_NAME` | (QUERY_STATEMENT) },
  STRUCT(
    [, START_SECOND AS start_second]
    [, END_SECOND AS end_second]
    [, INTERVAL_SECONDS AS interval_seconds]
    [, OUTPUT_DIMENSIONALITY AS output_dimensionality]
  )
)
```

Additional syntaxes exist for PCA, Autoencoder, and Matrix factorization models.

**Inputs:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `MODEL` | Model reference | Required | Remote model reference (`PROJECT_ID.DATASET.MODEL_NAME`). Must reference a Vertex AI embedding model, multimodalembedding@001, a supported open model, PCA, autoencoder, or matrix factorization model. |
| `TABLE` / `QUERY_STATEMENT` | Table or query | Required (except matrix factorization) | Input data. For text: must contain a STRING column named `content`. |
| `TASK_TYPE` | STRING literal | Optional (text only) | Values: `RETRIEVAL_QUERY`, `RETRIEVAL_DOCUMENT`, `SEMANTIC_SIMILARITY`, `CLASSIFICATION`, `CLUSTERING`, `QUESTION_ANSWERING`, `FACT_VERIFICATION`, `CODE_RETRIEVAL_QUERY` |
| `OUTPUT_DIMENSIONALITY` | INT64 | Optional | Number of embedding dimensions. For multimodal: valid values are 128, 256, 512, 1408 (default: 1408). Cannot be used with video embeddings. |
| `START_SECOND` | FLOAT64 | Optional (video only) | Start second for video embedding. Default: 0. |
| `END_SECOND` | FLOAT64 | Optional (video only) | End second for video embedding. Max/default: 120. |
| `INTERVAL_SECONDS` | FLOAT64 | Optional (video only) | Interval for segmenting video. Must be >= 4 and < 120. Default: 16. |
| `TRIAL_ID` | INT64 | Optional (autoencoder, matrix factorization) | Identifies hyperparameter tuning trial. |

**Outputs (text embedding):**

| Column | Type | Description |
|--------|------|-------------|
| `embedding` | ARRAY\<FLOAT64\> | Generated embedding vector |
| `statistics` | JSON | Contains `token_count` and `truncated` fields (text only — not returned by `multimodalembedding@001`) |
| `status` | STRING | API response status (empty if successful) |

Additional output columns exist for multimodal (video_start_sec, video_end_sec), PCA, autoencoder (trial_id), and matrix factorization (trial_id, processed_input, feature).

> **Note:** The `statistics` column is returned by text embedding models and by `gemini-embedding-2-preview` (with per-modality token counts). `multimodalembedding@001` does NOT return it — queries that SELECT `statistics` from `multimodalembedding@001` will error.

**Supported models:**

| Model | Output Dimensions | Max Sequence Length | Languages |
|-------|-------------------|---------------------|-----------|
| `gemini-embedding-001` | up to 3072 | 2048 tokens | Multilingual |
| `text-embedding-005` | up to 768 | 2048 tokens | English |
| `text-multilingual-embedding-002` | up to 768 | 2048 tokens | Multilingual |
| `multilingual-e5-small` (Preview) | up to 384 | 512 tokens | Multilingual |
| `multilingual-e5-large` (Preview) | up to 1024 | 512 tokens | Multilingual |
| `multimodalembedding@001` | 128, 256, 512, 1408 | -- | -- |
| `gemini-embedding-2-preview` (Preview) | up to 3072 | 8192 | Multimodal (text, image, video, audio, PDF). Returns `statistics` with per-modality token counts. US and us-central1 only. |

Also supports PCA, autoencoder, and matrix factorization models.

**Best practices:**
- For multimodal input, prefer inline ObjectRef subqueries (`OBJ.MAKE_REF` → `OBJ.FETCH_METADATA` → `OBJ.GET_ACCESS_URL` as the `content` column) over object tables. Inline ObjectRef queries do not require a BigQuery reservation, while object tables used with remote models do.
- `multimodalembedding@001` supports images only (JPEG, PNG, BMP, GIF) — **not PDFs**. Render PDFs to images first.

**Limitations:** Model and input table must be in the same region. Resource exhausted errors possible when API volume exceeds quota. Videos: only first 2 minutes processed. Object tables used with remote models require a BigQuery reservation — use inline ObjectRef to avoid this requirement.

**Locations:** Must run in the same region or multi-region as the model. Also available in US multi-region.

**Provisioned throughput:** For multimodalembedding: default RPM for non-EU regions is 600; default RPM for EU regions is 120. See Vertex AI quotas.

**BigFrames API:** `bigframes.bigquery.ai.generate_embedding(model, data)` — TVF wrapper that takes a model name string and DataFrame/Series. Generates `AI.GENERATE_EMBEDDING` SQL. Also available as `bigframes.ml.llm.TextEmbeddingGenerator` (sklearn-style: create model, then `.predict()`) and `bigframes.ml.llm.MultimodalEmbeddingGenerator` for multimodal.

---

### `ML.GENERATE_EMBEDDING`
- **Description:** Table-valued function identical in capability to `AI.GENERATE_EMBEDDING` but with `ml_generate_embedding_*` prefixed output column names and an additional `flatten_json_output` parameter. **Google recommends using `AI.GENERATE_EMBEDDING` instead for new queries.**
- **Use cases:** Same as AI.GENERATE_EMBEDDING.
- [documentation](https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-generate-embedding)
- **Type:** Table-valued function

**Syntax:** Same patterns as AI.GENERATE_EMBEDDING, with the addition of `FLATTEN_JSON_OUTPUT AS flatten_json_output` in the STRUCT parameter.

**Key difference from AI.GENERATE_EMBEDDING:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `flatten_json_output` | BOOL | TRUE | Determines whether JSON content is parsed into separate columns. |

All other inputs are the same as AI.GENERATE_EMBEDDING. Additionally, when using `RETRIEVAL_DOCUMENT` task type, you can include a `title` column in the input query.

**Outputs (column naming difference):**

| Column | Type | Description |
|--------|------|-------------|
| `ml_generate_embedding_result` | ARRAY\<FLOAT64\> (flatten=TRUE) or JSON (flatten=FALSE) | Embedding vector or full JSON response |
| `ml_generate_embedding_statistics` | JSON | Token count and truncated fields (flatten=TRUE only) |
| `ml_generate_embedding_status` | STRING | API response status |
| `ml_generate_embedding_start_sec` | INT64 | Video only (NULL for images) |
| `ml_generate_embedding_end_sec` | INT64 | Video only (NULL for images) |

**Supported models / Limitations / Locations / Provisioned throughput:** Same as AI.GENERATE_EMBEDDING. Note: `gemini-embedding-001` has a default output dimensionality of 3072 (vs 768 for `text-embedding-005`). `gemini-embedding-2-preview` (Preview) is also supported for multimodal, same as AI.GENERATE_EMBEDDING.

**BigFrames API:** No direct `ML.GENERATE_EMBEDDING` wrapper. BigFrames routes through `AI.GENERATE_EMBEDDING` instead. Use `bbq.ai.generate_embedding()` or `TextEmbeddingGenerator`/`MultimodalEmbeddingGenerator` classes.

---

### `AI.SIMILARITY`
- **Description:** (Preview) Scalar function that computes the cosine similarity between two inputs (text or images). Creates embeddings for both inputs at runtime and computes the cosine similarity between them. Values closer to 1 indicate more similar inputs.
- **Use cases:** Semantic search without precomputed embeddings, recommendation, classification, prototyping similarity queries.
- [documentation](https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-similarity)
- **Type:** Scalar function (returns FLOAT64) -- Preview

**Syntax (text with endpoint):**
```sql
AI.SIMILARITY(
  content1 => 'CONTENT1',
  content2 => 'CONTENT2',
  endpoint => 'ENDPOINT'
  [, model_params => MODEL_PARAMS]
  [, connection_id => 'CONNECTION_ID']
)
```

**Syntax (text with built-in model — Preview):**
```sql
AI.SIMILARITY(
  content1 => 'CONTENT1',
  content2 => 'CONTENT2',
  model => 'MODEL'
)
```

**Syntax (multimodal):**
```sql
AI.SIMILARITY(
  content1 => 'CONTENT1',
  content2 => 'CONTENT2',
  connection_id => 'CONNECTION_ID',
  endpoint => 'ENDPOINT'
  [, model_params => MODEL_PARAMS]
)
```

**Inputs:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `content1` | STRING, ObjectRef, or ObjectRefRuntime | Required | First value to compare. For `gemini-embedding-2-preview`: can be a STRUCT (text, images, audio, video, PDFs). |
| `content2` | STRING, ObjectRef, or ObjectRefRuntime | Required | Second value to compare. Same types as `content1`. |
| `endpoint` | STRING | Required (unless `model` specified) | Vertex AI embedding model endpoint (e.g., `text-embedding-005`, `multimodalembedding@001`, `gemini-embedding-2-preview`). |
| `model` | STRING | Optional (Preview) | Built-in text embedding model. Only supported value: `embeddinggemma-300m`. When specified, cannot use `endpoint`, `model_params`, or `connection_id`. No Vertex AI charges. |
| `model_params` | JSON literal | Optional | For text: any parameters object fields including `outputDimensionality`. For multimodal: only `dimension`. |
| `connection_id` | STRING | Optional for text; Required for multimodal | Connection in format `PROJECT_ID.LOCATION.CONNECTION_ID`. |

**Outputs:** Returns FLOAT64 (cosine similarity). NULL on error.

**AI.SIMILARITY vs VECTOR_SEARCH:**

| Feature | AI.SIMILARITY | VECTOR_SEARCH |
|---------|---------------|---------------|
| Function type | Scalar | TVF |
| Primary purpose | Cosine similarity between two specific inputs | Top-K nearest neighbors from a base table |
| Embedding | Generates embeddings at runtime (2 per call) | Uses pre-computed embeddings |
| Indexing | No vector indexes | Designed to use vector indexes for ANN search |
| Use case | Small comparisons, prototyping | Large-scale semantic search, RAG |

**Supported models:** Same models as AI.EMBED: `embeddinggemma-300m` (built-in, Preview), `gemini-embedding-001`, `text-embedding-005`, `text-multilingual-embedding-002`, `gemini-embedding-2-preview` (multimodal, Preview), `multimodalembedding@001`.

**Best practices:**
- Use for small comparisons and prototyping. Use VECTOR_SEARCH for large-scale searches.
- Supports **cross-modal** comparisons: `content1` can be text while `content2` is an image (or vice versa) when using `multimodalembedding@001` or `gemini-embedding-2-preview`. Text and image embeddings share the same vector space, so text descriptions can be matched against document images.
- `multimodalembedding@001` supports images only (JPEG, PNG, BMP, GIF) — **not PDFs**. Use `gemini-embedding-2-preview` for PDF support, or render PDFs to images first.

**Limitations:** Incurs charges for two embedding generations per call. For multimodal, `connection_id` is required and the connection's service account needs `roles/aiplatform.user` and `roles/storage.objectViewer`.

**Locations:** All regions supporting Gemini models, plus US and EU multi-regions.

**Provisioned throughput:** Not specified in documentation.

**BigFrames API:** No direct equivalent. Use `%%bigquery` magics or `session.read_gbq_query()` to execute AI.SIMILARITY SQL from BigFrames.

---

### `VECTOR_SEARCH`
- **Description:** Table-valued function that searches embeddings to find the top-K closest embeddings from a base table to a given query embedding. Supports both batch searches (multiple query rows) and single searches (one embedding value). Can use vector indexes for approximate nearest neighbor (ANN) search. The single search syntax additionally supports **hybrid search** -- combining semantic similarity with lexical (keyword) matching -- via `lexical_search_columns` and `lexical_search_query_value`.
- **Use cases:** Semantic search, hybrid semantic + keyword search, recommendation systems, classification, clustering, retrieval augmented generation (RAG).
- [documentation](https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/search_functions#vector_search)
- **Type:** Table-valued function (TVF) -- GA (single search syntax is Preview)

**Syntax (batch search):**
```sql
VECTOR_SEARCH(
  { TABLE base_table | (base_table_query) },
  column_to_search,
  { TABLE query_table | (query_table_query) },
  [, query_column_to_search => query_column_to_search_value]
  [, top_k => top_k_value]
  [, distance_type => distance_type_value]
  [, options => options_value]
)
```

**Syntax (single search -- Preview; also the hybrid search syntax):**
```sql
VECTOR_SEARCH(
  { TABLE base_table | (base_table_query) },
  column_to_search,
  query_value => single_query_value,
  [, lexical_search_columns => lexical_search_columns_value]
  [, lexical_search_query_value => single_lexical_search_query_value]
  [, top_k => top_k_value]
  [, distance_type => distance_type_value]
  [, options => options_value]
)
```

Supplying a non-empty `lexical_search_columns` is what makes the search hybrid. Hybrid search is only available in the single search syntax -- **there is no batch hybrid search**. See [Hybrid Search](#hybrid-search-capability) below for how the fused score is computed.

**Inputs:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `base_table` / `base_table_query` | Table/Query | Required | The table to search. Only SELECT, FROM, WHERE clauses allowed in query. Don't filter the embedding column. Can't use logical views. |
| `column_to_search` | STRING | Required | Base table column to search. Must be ARRAY\<FLOAT64\> or STRING (Preview, requires autonomous embedding generation). If indexed, BigQuery attempts to use it. |
| `query_table` / `query_table_query` | Table/Query | Required for batch | Query embeddings to find nearest neighbors for. |
| `query_column_to_search` | Named arg, STRING | Optional (batch only) | Column in query table containing embeddings. ARRAY\<FLOAT64\> or STRING. |
| `query_value` | Named arg, ARRAY\<FLOAT64\> or STRING | Required for single search | Single embedding or string to search for. |
| `lexical_search_columns` | Named arg, ARRAY\<STRING\> | Optional (single search only) | Base table columns to match lexically. Non-empty value switches the call to hybrid search. If the base table has a vector index with `lexical_search_columns`, these columns must be a subset of the indexed ones. |
| `lexical_search_query_value` | Named arg, STRING | Optional (single search only) | The keyword query text for the lexical leg. Defaults to `query_value` when that is a STRING. |
| `top_k` | Named arg, INT64 | Optional | Number of nearest neighbors per query. Default: 10. Negative = return all. |
| `distance_type` | Named arg, STRING | Optional | `EUCLIDEAN` (default), `COSINE`, or `DOT_PRODUCT`. |
| `options` | Named arg, JSON STRING | Optional | `fraction_lists_to_search` (0.0-1.0, index only), `use_brute_force` (boolean). |

**Outputs (batch search):**

| Column | Type | Description |
|--------|------|-------------|
| `query` | STRUCT | All selected columns from the query data |
| `base` | STRUCT | All columns from base_table |
| `distance` | FLOAT64 | Distance between base and query data |

**Outputs (single search):** Same but without the `query` column.

**Outputs (hybrid search):** Same shape as single search, but `distance` is **not a distance** -- it is a reciprocal rank fusion (RRF) score derived from the row's rank in the semantic and lexical result lists. Hybrid `distance` values are not comparable to semantic-only `distance` values. See [Hybrid Search](#hybrid-search-capability).

**Supported models:** VECTOR_SEARCH does not directly reference models. Operates on pre-computed ARRAY\<FLOAT64\> embeddings or STRING columns with autonomous embedding generation. Embeddings can come from any source (AI.EMBED, AI.GENERATE_EMBEDDING, external).

**Best practices:** Use a vector index for large base tables. Use brute force for exact results. Use single search syntax for single queries (optimized performance).

**Limitations:** Row-level and column-level security policies apply. Project running the query must match the project containing the base table. Subqueries in base_table_query might interfere with index usage. Logical views cannot be used. Hybrid search requires the single search syntax and therefore cannot be combined with batch search.

**Locations:** Not specified specifically -- operates wherever BigQuery tables exist.

**Provisioned throughput:** Not specified. When used with autonomous embedding generation on STRING columns, generative AI function limits apply.

**BigFrames API:** `bigframes.bigquery.vector_search(base_table, column_to_search, query)` — Takes base table as string, query as DataFrame/Series. Supports `distance_type`, `top_k`, `fraction_lists_to_search`, `use_brute_force`. Also `bigframes.bigquery.create_vector_index()` for creating vector indexes.

---

### `AI.SEARCH`
- **Description:** Table-valued function for semantic and hybrid search on tables that have autonomous embedding generation enabled. Embeds the search query at runtime and searches the specified table. Uses vector indexes when available.
- **Use cases:** Semantic search, hybrid semantic + keyword search, recommendation, classification, clustering, outlier detection.
- [documentation](https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-search)
- **Type:** Table-valued function (TVF) -- GA (the `mode` argument is Preview)

**Syntax:**
```sql
AI.SEARCH(
  { TABLE base_table | base_table_query },
  column_to_search,
  query_value
  [, mode => mode_value]
  [, top_k => top_k_value]
  [, distance_type => distance_type_value]
  [, options => options_value]
)
```

**Inputs:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `base_table` / `base_table_query` | Table/Query | Required | Table to search. **Must have autonomous embedding generation enabled.** |
| `column_to_search` | STRING literal | Required | Name of the **source string column** (not the generated embedding column). |
| `query_value` | STRING literal | Required | Search query text. Embedded at runtime using the base table's connection and endpoint. |
| `mode` | Named arg, STRING | Optional (Preview) | `AUTO` (default), `VECTOR`, or `HYBRID`. See below. |
| `top_k` | Named arg, INT64 | Optional | Default: 10. Negative = return all. |
| `distance_type` | Named arg, STRING | Optional | `EUCLIDEAN` (default), `COSINE`, or `DOT_PRODUCT`. Ignored in `HYBRID` mode. |
| `options` | Named arg, JSON STRING | Optional | `fraction_lists_to_search`, `use_brute_force`. |

**Search modes:**

| Mode | Behavior |
|------|----------|
| `AUTO` | Default. Runs hybrid search **only if** the base table has a vector index configured with `lexical_search_columns`; otherwise silently runs semantic-only search. |
| `VECTOR` | Semantic-only search. `distance` is a true distance in the chosen `distance_type`. |
| `HYBRID` | Combines semantic and lexical matching on `column_to_search`. Runs with or without a vector index. `distance` is an RRF score, not a distance. |

> **Gotcha:** `AUTO` does not mean "hybrid". Because a vector index cannot currently be built on an autonomous embedding generation column (see [Hybrid Search](#hybrid-search-capability)), `AUTO` on an AI.SEARCH base table resolves to semantic-only. The query succeeds either way, so the fallback is silent. Specify `mode => 'HYBRID'` explicitly when you want hybrid behavior.

**Outputs:**

| Column | Type | Description |
|--------|------|-------------|
| `base` | STRUCT | All columns from base_table |
| `distance` | FLOAT64 | In `VECTOR`/`AUTO`-semantic mode, the distance between the query_value embedding and the base embedding. In `HYBRID` mode, a reciprocal rank fusion score -- not a distance, and not comparable across modes. |

**Supported models:** Uses whatever embedding model and connection are configured for the base table's autonomous embedding generation.

**AI.SEARCH vs VECTOR_SEARCH:** Use AI.SEARCH for simplified semantic or hybrid search when the base table has autonomous embedding generation and you want to search for a single string literal. Use VECTOR_SEARCH for batch queries, custom embeddings, control over which columns are matched lexically, or tables without autonomous embedding generation. In hybrid mode AI.SEARCH matches lexically only against `column_to_search`; VECTOR_SEARCH lets you name any set of columns in `lexical_search_columns`.

**Best practices:** Create a vector index on the embedding column for better performance on large tables. State `mode` explicitly rather than relying on `AUTO`.

**Limitations:** Base table must have autonomous embedding generation enabled. If embedding generation fails for query_value, the entire query fails. Rows with missing embeddings are skipped. Hybrid mode matches lexically only on `column_to_search`.

**Locations:** All locations supporting Vertex AI embedding models, plus US and EU multi-regions.

**Provisioned throughput:** Not specified in documentation.

**BigFrames API:** No direct equivalent. Use `%%bigquery` magics or `session.read_gbq_query()` to execute AI.SEARCH SQL from BigFrames.

---

### Hybrid Search *(capability)*

Hybrid search combines semantic (vector) retrieval with lexical (keyword) matching, so that exact tokens -- SKUs, error codes, model numbers, proper nouns -- can influence the ranking instead of being dissolved into embedding similarity. **BigQuery ships this as a capability of the two existing search functions, not as a separate `HYBRID_SEARCH` function.** There is no `HYBRID_SEARCH` in the SQL surface.

> **Set the expectation correctly before you reach for it.** Hybrid search fuses two *rankings* of the same corpus; it does not union two result sets. How deep a lexical match can reach is decided entirely by `top_k`, through **two independent gates**: BigQuery hands the lexical leg only the top `10 * top_k` rows by semantic rank, and inside that pool a lexical hit is worth a bounded amount of score -- at most `1/62` = `0.0161`. Effective reach is the smaller of the two. At the page sizes most demos use (`top_k` under ~30) the score gate holds reach to ~110 rows and the token only nudges rows the semantic leg already placed near the top. At `top_k` = 64 the pool gate holds it to semantic rank 640, and no exact-token match reaches deeper than that no matter how perfect the match. Sizing `top_k` is part of the design, not an afterthought.

| Route | How to invoke | Lexical columns | Batch? |
|-------|---------------|-----------------|--------|
| `VECTOR_SEARCH` | Single search syntax + `lexical_search_columns` (+ optional `lexical_search_query_value`) | Any set of base table columns you name | No -- single query only |
| `AI.SEARCH` | `mode => 'HYBRID'` | Only `column_to_search` | No -- single query only |

**Neither route requires a vector index.** Both run against an unindexed base table; the index is a speed optimization for the lexical leg, not a prerequisite.

**Two gates, and `top_k` sets both.** A lexically-matched row appears on the result page only if it clears both of these:

```
Gate 1 (candidate pool):   rank_vector <= 10 * top_k
Gate 2 (fusion score):     1/(60 + rank_vector) + 1/(61 + rank_lexical)
                             must beat the row holding the last slot
```

**Effective reach = `min( score_reach(top_k), 10 * top_k )`.** Gate 1 binds for `top_k` >= 51; Gate 2 binds below that. Everything else in this section is a consequence of those two lines.

**Gate 1: the lexical candidate pool is `10 * top_k` rows.** BigQuery hands the lexical (BM25) leg only the top `10 * top_k` rows by semantic rank. A row deeper than that receives **no lexical rank at all** -- BM25 never sees it, however exactly the token matches, and no amount of score can rescue it. This is why a page of 64 reaches semantic rank 640 and stops.

The diagnostic signature of a query whose target sits outside the pool is that the whole result set comes back with `rank_lexical = rank_vector`, so every returned value is exactly `1 - ( 1/(60 + r) + 1/(61 + r) )`. Read the top row: a best `distance` of **`0.967478`** (= `1 - (1/61 + 1/62)`) means *nothing matched*, while **`0.967734`** (= `1 - (1/61 + 1/63)`) means a match fired somewhere and pushed the top semantic row to lexical rank 2. Those two numbers tell you whether to raise `top_k` or fix the token.

**Gate 2 -- scoring: reciprocal rank fusion.** In hybrid mode the returned `distance` column is a fused rank score rather than a geometric distance. Each candidate is ranked separately by the semantic leg and the lexical leg, and the two ranks are combined. Reproduced against live results, the value matches reciprocal rank fusion with **k = 60 on the semantic leg and k = 61 on the lexical leg**, both ranks 1-based:

```
distance = 1 - ( 1/(60 + rank_vector) + 1/(61 + rank_lexical) )
```

**The two legs do not share a rank base.** This is only visible if you recover both ranks independently rather than solving for one of them: decoding a fused score with k = 60 on *both* terms yields lexical ranks `2 .. n+1`, and no n-row list can hand out rank n+1. Measured on a 30-row corpus where `rank_vector` was read directly from a separate semantic-only `VECTOR_SEARCH` run, the implied lexical ranks form an exact `1 .. 30` permutation only under k = 61. Which leg carries the extra 1 is settled by any row where the two ranks differ: at semantic rank 1 and lexical rank 2, BigQuery returns `1 - (1/61 + 1/63)` = `0.9677335415040333`. That value falls *between* the two readings a shared base would give those same ranks -- 60 on both legs gives `1 - (1/61 + 1/62)` = `0.9674775251189847`, and 61 on both legs gives `1 - (1/62 + 1/63)` = `0.9679979518689196`. Landing strictly between them is the signature of mixed bases: no single k reproduces the observed number. (`0.9674775251189847` carries two distinct meanings in this section, so keep them apart: here it is the shared-base-60 *reading* of a rank 1 / rank 2 row -- a candidate the measurement rules out -- while elsewhere it is the best score actually attainable under the measured law, at rank 1 in *both* legs. The same expression `1/61 + 1/62` produces both.) The asymmetry is determined, not cosmetic.

Three worked examples from that run, each matching a live returned value exactly:

| rank_vector | rank_lexical | Arithmetic | Returned `distance` |
|---|---|---|---|
| 1 | 3 | `1 - (1/61 + 1/64)` | `0.967981557377` |
| 2 | 1 | `1 - (1/62 + 1/62)` | `0.967741935484` |
| 9 | 2 | `1 - (1/69 + 1/63)` | `0.969634230504` |

The middle row is the one that trips people up: `1/62 + 1/62` is a value the *measured* law produces -- `1/(60 + 2)` and `1/(61 + 1)` happen to coincide at ranks (2, 1). It is also the `distance` on the `tiger` row of Google's published hybrid example, which decodes to exactly those ranks. Seeing two equal denominators is not evidence of a shared rank base; only reading both ranks independently settles that.

Consequences worth internalizing:

- **The best attainable score is `1 - (1/61 + 1/62)` = `0.9674775251189847`** -- rank 1 in *both* legs. An exact self-match does not return a near-zero "distance". (The oft-quoted `1 - 2/61` = `0.967213` is not attainable: the two denominators can never be equal at rank 1.)
- **Each leg contributes at most ~`1/61` = `0.0164`.** A rank-1 lexical hit is worth `1/62` = `0.0161` and nothing more. That single number is the budget the whole capability operates inside.
- **The lexical leg ranks the entire candidate pool, so no pooled row ever forfeits a term.** True BM25 matches take lexical ranks `1..m`; every remaining pooled row falls back to its *semantic* order behind them. Verified with a `lexical_search_query_value` matching zero rows -- every row still received a lexical term, with `rank_lexical = rank_vector`. Verified again by promoting one row to lexical rank 1: the row formerly at lexical rank 1 moved to 2, and every row below the promoted row was byte-identical. Within the pool there is no "single-list" state and no forfeiture ceiling; every row in the result is scored from both terms. Outside the pool there is no scoring at all -- that is Gate 1, not a forfeited term.
- **Therefore an unmatched row is not penalized, only un-promoted.** It keeps a lexical rank -- its own semantic rank, pushed down one place for each row below it that did match. Where nothing matched at all, that reduces to `1 - ( 1/(60 + r) + 1/(61 + r) )` at semantic rank `r` -- at `r = 10`, `1 - (1/70 + 1/71)` = `0.97163`. A lexical match moves that row to lexical rank 1, replacing its `1/(61 + r)` with `1/62`. That single substitution is the entire mechanism.
- **What limits hybrid is reach, and reach is a function of `top_k` twice over.** For the score gate: a matched row at semantic rank `R` scores `1/(60 + R) + 1/62`, and it has to displace the row holding the last slot, which sits at semantic rank `top_k` and -- pushed down one position by the match -- lexical rank `top_k + 1`, scoring `1/(60 + top_k) + 1/(61 + top_k + 1)`. For the pool gate the bound is simply `10 * top_k`. Taking the `min` of the two gives the deepest semantic rank a lexically-matched row can occupy and still make the page:

  | `top_k` | 2 | 3 | 5 | 10 | 20 | 30 | 40 | 50 | 51 | 64 | 100 | 208 | 300 |
  |---|---|---|---|---|---|---|---|---|---|---|---|---|---|
  | deepest semantic rank retrievable | 3 | 6 | 10 | 23 | 56 | 110 | 212 | 468 | 510 | 640 | 1,000 | 2,080 | 3,000 |
  | binding gate | score | score | score | score | score | score | score | score | pool | pool | pool | pool | pool |

  Below `top_k` = 51 the score gate is the binding one and growth is steeply non-linear -- nearly flat through the page sizes demos typically use, then accelerating. From `top_k` = 51 upward the pool gate takes over and reach becomes exactly linear at `10 * top_k`. There is no page size at which reach becomes unbounded. `top_k` >= `R/10` is therefore a floor for retrieving a row at semantic rank `R`, not a recipe: it is necessary everywhere, but sufficient only once the pool gate is the binding one. Below that crossover the score gate decides and `R/10` falls short -- a target at semantic rank 100 needs `top_k` of 29, not 10, and one at rank 200 needs 40, not 20. Read the real number off the row above.
- **The evidence.** A 500-row corpus: 499 rows about office and desk items, semantically close to the query `"desk accessories for a computer setup"`, plus one target row `ZQX-9999` described as `"bulk compost bin for garden waste and autumn leaf mulching"` -- semantic rank **500 of 500**. Searching with `lexical_search_query_value => 'ZQX-9999'`:

  | `top_k` | 10 | 49 | 50 | 51 | 63 | 64 |
  |---|---|---|---|---|---|---|
  | target returned | no | no | no | **yes** | yes | yes |

  The arithmetic predicts the flip between 50 and 51 to the exact position. The target's returned `distance`, `0.9820852534562212`, is exactly `1 - (1/560 + 1/62)` -- semantic rank 500, lexical rank 1. Here the score gate is the binding one: at `top_k` = 51 the pool is 510 rows, comfortably deeper than the target.

- **The pool gate, isolated.** Repeating the same construction on deeper corpora puts the target beyond any plausible score-gate reach, so the flip lands on `10 * top_k` exactly. Each of these was a sharp prediction made before the query ran; the 500-row probe is listed alongside them as the contrasting case, where the score gate is the binding one:

  | corpus | index | target semantic rank | predicted flip | observed |
  |---|---|---|---|---|
  | 3,000 rows | none | 3,000 | `top_k` = 300 | 299 no match, **300 match** |
  | 1,500 rows | none | 1,500 | `top_k` = 150 | 149 no match, **150 match** |
  | 500 rows | none | 500 | `top_k` = 51 (score gate) | 50 absent, **51 present** |
  | 7,275-row product catalog | `TREE_AH` hybrid, `ACTIVE`, 100% coverage | 2,072 | needs `top_k` >= 208 | `top_k` = 64 returned nothing |

  The three synthetic probe tables are **unindexed** -- at 3,000, 1,500 and 500 rows they sit below BigQuery's 5,000-row `CREATE VECTOR INDEX` floor and are brute-force scanned, so no index existed that could have restricted anything. The product catalog is the opposite case: it carried a fully populated hybrid `TREE_AH` index declaring `lexical_search_columns`, status `ACTIVE` at 100% coverage, when the `top_k` = 64 observation was made. The pool gate behaves identically with and without an index, which makes it both *not* an index artifact and *not* something an index can avoid. At `top_k` = 64 on the catalog the pool was 640 rows and the target at rank 2,072 was never a candidate; the result set carried the zero-match signature (`rank_lexical = rank_vector`, best `distance` `0.967478`).
- **This is why a hybrid demo at `top_k => 3` or `5` returns almost exactly the semantic-only rows:** at those page sizes reach is 6 and 10, deep enough to shuffle the top of the list, never deep enough to pull in something new. That is a property of the page size chosen, not a limit on the capability.
- **Promotion is a swap.** The fused list is a fixed-length page, so a row hybrid adds displaces one semantic-only would have returned. Always measure both the added *and* the dropped set.
- **When the token is all the user typed, use a predicate.** Hybrid *can* retrieve it, but only if `top_k` clears both gates for the target's semantic rank -- a tenth of that rank at the very least, and more than that whenever the score gate binds -- which you do not know in advance, and a fusion score is still a ranking that can be crowded. Use `WHERE sku = @sku` -- a predicate cannot be outranked and has no candidate pool. Hybrid earns its place on queries that carry descriptive words *and* an identifier.
- Scores are bounded in a narrow band near 1 and are **not comparable** to `VECTOR`-mode distances. Do not threshold hybrid scores with a cutoff tuned on cosine or Euclidean distance.
- Because the score depends only on ranks, `distance_type` has no effect in hybrid mode.

**The sizing rule:** hybrid search re-ranks *and* widens, and `top_k` decides how much of each you get -- the widening is real but bounded, never unbounded. At `top_k` up to about 30 the token only nudges rows already near the top -- do not size a page that way and then expect recall. Beyond that, an exact token surfaces a row from about `10 * top_k` deep and no deeper, so for a target you expect at semantic rank `R`, **size `top_k` to at least `R/10`, and above that to whatever the reach table requires** -- the two gates cross at `top_k` = 51, so for anything shallower than a few hundred ranks the score gate is the one that binds and the floor alone will not retrieve the row. If the identifier *is* the query and you need certainty, use a `WHERE` predicate instead.

> This formula is reverse-engineered from observed results, not documented by Google. Treat it as an explanation of the ordering you see, not as a contract -- it can change without notice.

**Vector indexes for hybrid search.** To accelerate the lexical leg, create a vector index that declares the lexical columns:

```sql
CREATE [ OR REPLACE ] VECTOR INDEX [ IF NOT EXISTS ] index_name
ON table_name(column_name)
[STORING(stored_column_name [, ...])]
[PARTITION BY partition_expression]
OPTIONS(index_option_list);
```

```sql
CREATE VECTOR INDEX IF NOT EXISTS my_hybrid_index
ON my_table(embedding)
STORING (product_name)
OPTIONS (index_type = 'TREE_AH', distance_type = 'COSINE',
         lexical_search_columns = ['product_name']);
```

Rules that are easy to get wrong, all confirmed against a live project:
- Every column in `lexical_search_columns` **must also appear in `STORING(...)`**. Omitting the `STORING` clause fails with `Lexical search column x must be in the list of stored columns`.
- A lexical column **may not also be the index key**. Naming the same column in `ON table(x)` and `STORING(x)` fails with `Column x found multiple times`.
- The index key must be an `ARRAY<FLOAT64>` embedding column. **A vector index cannot be created on an autonomous embedding generation column**, because that column is a `STRUCT`. Demonstrating both autonomous embeddings and a vector index in one pipeline therefore requires two tables.
- **Two separate size gates, and they fail differently.** (a) `CREATE VECTOR INDEX` is *rejected outright* below **5,000 rows**: `Total rows 30 is smaller than min allowed 5000 for CREATE VECTOR INDEX query with the IVF index type. Please use VECTOR_SEARCH table-valued function directly to perform the similarity search.` Verified 2026-09-02 on a 30-row table for **both** `IVF` and `TREE_AH` (the message names whichever `index_type` you passed), so this is not an IVF-only constraint. (b) Once created, **population** is asynchronous and does not begin until the base table exceeds roughly **10 MB**; below that the index sits at `coverage_percentage` 0 with `indexUnusedReasons` = `BASE_TABLE_TOO_SMALL` and queries silently fall back to brute force. A demo table must clear *both* bars to show a working index -- which is why the catalog workflow uses a real ~7,275-row public catalog rather than generated data. Note the 5,000-row floor is enforced by the engine but is **not** stated on the vector-index documentation page; only the 10 MB condition is documented.
- `index_type` is `TREE_AH` or `IVF`.

**Related:** [`VECTOR_SEARCH`](#vector_search) · [`AI.SEARCH`](#aisearch) · workflow [`catalog_search`](workflows/catalog_search/)

---

## Predictive AI

These functions make predictions from historical or tabular data using BigQuery ML's built-in foundation models. None of them require creating, training, or managing a model object -- the model is built in.

Two model families sit behind this section:

- **TimesFM** -- a time series foundation model, used by `AI.FORECAST`, `AI.DETECT_ANOMALIES`, and `AI.EVALUATE`. These three share a common parameter pattern (`data_col`, `timestamp_col`, `id_cols`) and the same model versions.
- **TabFM** -- a tabular foundation model, used by `AI.PREDICT` and by `AI.EVALUATE`'s second syntax. TabFM does zero-shot regression and classification by in-context learning: you hand it a training table and a prediction table in the same call, and it never persists a model.

**Key relationships:**
- `AI.FORECAST` generates future time series values from historical data.
- `AI.DETECT_ANOMALIES` compares target data against a forecast baseline from historical data to identify anomalous points.
- `AI.PREDICT` predicts a label column for unlabeled rows, given a labeled training table. Regression or classification, chosen automatically from the label column's type.
- `AI.EVALUATE` is dual-purpose: it computes forecasting metrics for a TimesFM forecast, **or** regression/classification metrics for a TabFM prediction. Which branch runs is determined by the arguments you pass.

| Attribute | AI.FORECAST | AI.DETECT_ANOMALIES | AI.PREDICT | AI.EVALUATE |
|-----------|-------------|---------------------|------------|-------------|
| **Status** | GA | GA | Preview | GA (TabFM branch Preview) |
| **Model family** | TimesFM | TimesFM | TabFM | TimesFM or TabFM |
| **Purpose** | Forecast future values | Detect anomalies | Predict a label for unlabeled rows | Evaluate a forecast or a prediction |
| **Input data sources** | 1 (history) | 2 (history + target) | 2 (training + prediction) | 2 (history + actuals, or training + prediction) |
| **Supported Models** | TimesFM 2.5 (default), TimesFM 2.0 | TimesFM 2.5 (default), TimesFM 2.0 | TabFM (not selectable) | TimesFM 2.5 (default), TimesFM 2.0; TabFM on the prediction branch |
| **Default Horizon** | 10 | N/A | N/A | 1024 |
| **Min Data Points** | 3 | 3 | Not specified | 3 |
| **Max Data Points** | 2,048 (2.0) / 15,360 (2.5) | 1,024 (most recent) | See AI.PREDICT limitations | Not specified |
| **Context Window** | Yes (auto-selected) | Yes (auto-selected) | N/A | Yes (auto-selected) |

> **Default model version changed.** All three TimesFM functions now default to **TimesFM 2.5** (previously TimesFM 2.0). Google made this change on the reference pages without a release note. Confirmed against a live query: an unpinned `AI.FORECAST` returns values identical to `model => 'TimesFM 2.5'` and different from `model => 'TimesFM 2.0'`. Any existing unpinned query silently changes behavior -- pin `model` explicitly if you need reproducibility.

---

### `AI.FORECAST`
- **Description:** Table-valued time series forecasting function. Forecasts a time series using BigQuery ML's built-in TimesFM model without requiring model creation or training.
- **Use cases:** Forecasting future values (e.g., daily bike trips), forecasting multiple independent time series using ID columns (e.g., forecast by user type), generating prediction intervals, comparing historical vs forecasted data.
- [documentation](https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-forecast)
- **Type:** Table-valued function

**Syntax:**
```sql
SELECT *
FROM AI.FORECAST(
  { TABLE TABLE | (QUERY_STATEMENT) },
  data_col => 'DATA_COL',
  timestamp_col => 'TIMESTAMP_COL'
  [, model => 'MODEL']
  [, id_cols => ID_COLS]
  [, { horizon => HORIZON | forecast_end_timestamp => FORECAST_END_TIMESTAMP }]
  [, confidence_level => CONFIDENCE_LEVEL]
  [, output_historical_time_series => OUTPUT_HISTORICAL_TIME_SERIES]
  [, context_window => CONTEXT_WINDOW]
)
```

**Inputs:**

| Parameter | Type | Required | Default | Range | Description |
|-----------|------|----------|---------|-------|-------------|
| `TABLE` / `QUERY_STATEMENT` | Table/Query | Required | -- | -- | Input data to forecast |
| `data_col` | STRING | Required | -- | -- | Name of the data column. Must be INT64, NUMERIC, BIGNUMERIC, or FLOAT64. |
| `timestamp_col` | STRING | Required | -- | -- | Name of the timestamp column. Must be TIMESTAMP, DATE, or DATETIME. |
| `model` | STRING | Optional | `'TimesFM 2.5'` | -- | `'TimesFM 2.0'` or `'TimesFM 2.5'`. Recommended: TimesFM 2.5 for all new work. |
| `id_cols` | ARRAY\<STRING\> | Optional | -- | -- | ID columns identifying unique time series. Must be STRING, INT64, ARRAY\<STRING\>, or ARRAY\<INT64\>. |
| `horizon` | INT64 | Optional | 10 | [1, 10000] | Number of time series data points to forecast. Mutually exclusive with `forecast_end_timestamp`. |
| `forecast_end_timestamp` | TIMESTAMP | Optional | -- | -- | End timestamp for forecasted values. Horizon is calculated from the end timestamp and input frequency. Mutually exclusive with `horizon`. Valid calculated horizon range: [1, 10000]. |
| `confidence_level` | FLOAT64 | Optional | 0.95 | [0, 1) | Percentage of future values that fall in the prediction interval |
| `output_historical_time_series` | BOOL | Optional | FALSE | -- | When TRUE, returns input data along with forecasted data |
| `context_window` | INT64 | Optional | Auto-selected | See below | Context window length for the TimesFM model |

**Context Window Supported Values:**

| Model | Supported Context Window Lengths |
|-------|----------------------------------|
| TimesFM 2.0 | 64, 128, 256, 512, 1024, 2048 |
| TimesFM 2.5 | 64, 128, 256, 512, 1024, 2048, 4096, 8192, 15360 |

When not specified, the smallest window covering the input data points is auto-selected.

**Outputs (when `output_historical_time_series = FALSE`):**

| Column | Type | Description |
|--------|------|-------------|
| *id_cols* | (inherited) | Time series identifiers |
| `forecast_timestamp` | TIMESTAMP | Timestamps of the forecasted time series |
| `forecast_value` | FLOAT64 | 50% quantile (median) value of the forecast |
| `confidence_level` | FLOAT64 | The confidence level value |
| `prediction_interval_lower_bound` | FLOAT64 | Lower bound of prediction interval |
| `prediction_interval_upper_bound` | FLOAT64 | Upper bound of prediction interval |
| `ai_forecast_status` | STRING | Empty string (zero-length, not `NULL`) if successful; error string if unsuccessful. This is the *only* one of the three TimesFM status columns that behaves this way -- `ai_evaluate_status` and `ai_detect_anomalies_status` return `NULL` on success. |

**Outputs (when `output_historical_time_series = TRUE`):**

| Column | Type | Description |
|--------|------|-------------|
| *id_cols* | (inherited) | Time series identifiers |
| `time_series_type` | STRING | `'history'` or `'forecast'` |
| `time_series_timestamp` | TIMESTAMP | Timestamps |
| `time_series_data` | FLOAT64 | Historical value or forecast median |
| `confidence_level` | FLOAT64 | The confidence level value |
| `prediction_interval_lower_bound` | FLOAT64 | Lower bound (NULL for historical points) |
| `prediction_interval_upper_bound` | FLOAT64 | Upper bound (NULL for historical points) |
| `ai_forecast_status` | STRING | Status |

**Supported models:** TimesFM 2.5 (default), TimesFM 2.0.

**Best practices:** Set `output_historical_time_series` to TRUE to compare historical values with forecasted values. Minimum 3 data points required.

**Limitations:** TimesFM 2.0 max context: 2,048 data points. TimesFM 2.5 max context: 15,360 data points. Additional data points beyond the max are ignored. Minimum 3 data points.

**Locations:** All supported BigQuery ML locations.

**Provisioned throughput:** Not specified. Billed at the evaluation, inspection, and prediction rate (BigQuery ML on-demand pricing).

**BigFrames API:** `bigframes.bigquery.ai.forecast(df, data_col=..., timestamp_col=...)` — Wraps `AI.FORECAST` SQL directly. No model object needed. Supports `id_cols`, `horizon`, `confidence_level`, `context_window`, and `model` parameters. Note: `bigframes.ml.forecasting.ARIMAPlus` is a different model (ARIMA_PLUS, not TimesFM).

> **Wrapper skew:** the BigFrames wrapper still declares `model: str = "TimesFM 2.0"` and its docstring claims 2.0 is the only supported value. The SQL function now defaults to TimesFM 2.5 and accepts both. Calling `bbq.ai.forecast()` without specifying `model` therefore gives you **2.0**, while the equivalent SQL gives you **2.5**. Pass `model` explicitly from BigFrames.

---

### `AI.DETECT_ANOMALIES`
- **Description:** Table-valued function that detects anomalies in time series data using BigQuery ML's built-in TimesFM model. Forecasts expected values from historical data, then compares target data against those forecasts to identify anomalous data points.
- **Use cases:** Detecting anomalous spikes or drops in time series (e.g., sales, bike trips), detecting anomalies across multiple time series simultaneously, computing anomaly probability.
- [documentation](https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-detect-anomalies)
- **Type:** Table-valued function -- GA

**Syntax:**
```sql
SELECT *
FROM AI.DETECT_ANOMALIES(
  { TABLE HISTORY_TABLE | (HISTORY_QUERY_STATEMENT) },
  { TABLE TARGET_TABLE | (TARGET_QUERY_STATEMENT) },
  data_col => 'DATA_COL',
  timestamp_col => 'TIMESTAMP_COL'
  [, model => 'MODEL']
  [, id_cols => ID_COLS]
  [, anomaly_prob_threshold => ANOMALY_PROB_THRESHOLD]
  [, context_window => CONTEXT_WINDOW]
)
```

**Inputs:**

| Parameter | Type | Required | Default | Range | Description |
|-----------|------|----------|---------|-------|-------------|
| `HISTORY_TABLE` / `HISTORY_QUERY_STATEMENT` | Table/Query | Required | -- | -- | Historical data used to generate a forecast baseline |
| `TARGET_TABLE` / `TARGET_QUERY_STATEMENT` | Table/Query | Required | -- | -- | Data in which to detect anomalies. Schema must match historical data. |
| `data_col` | STRING | Required | -- | -- | Data column name. Must be INT64, NUMERIC, BIGNUMERIC, or FLOAT64. |
| `timestamp_col` | STRING | Required | -- | -- | Timestamp column name. Must be TIMESTAMP, DATE, or DATETIME. |
| `model` | STRING | Optional | `'TimesFM 2.5'` | -- | `'TimesFM 2.0'` or `'TimesFM 2.5'`. Recommended: TimesFM 2.5 for all new work. |
| `id_cols` | ARRAY\<STRING\> | Optional | -- | -- | ID columns identifying unique time series |
| `anomaly_prob_threshold` | FLOAT64 | Optional | 0.95 | [0, 1) | Threshold for anomaly detection. A target value is anomalous if its anomaly probability exceeds this threshold. |
| `context_window` | INT64 | Optional | Auto-selected | See AI.FORECAST | Context window length for the TimesFM model. Same supported values as AI.FORECAST per model version. |

**Outputs:**

| Column | Type | Description |
|--------|------|-------------|
| *id_cols* | (inherited) | Time series identifiers |
| `time_series_timestamp` | STRING | Timestamp column |
| `time_series_data` | FLOAT64 | Data column value |
| `is_anomaly` | BOOL | Whether the value is an anomaly |
| `lower_bound` | FLOAT64 | Lower bound of prediction |
| `upper_bound` | FLOAT64 | Upper bound of prediction |
| `anomaly_probability` | FLOAT64 | Probability that the value is an anomaly |
| `ai_detect_anomalies_status` | STRING | **`NULL` on success** -- not an empty string (verified live 2026-09-02); error string if unsuccessful. Test with `IS NOT NULL`, not `<> ''` -- see the note under [`AI.EVALUATE`](#aievaluate)'s forecast outputs. |

**Supported models:** TimesFM 2.5 (default), TimesFM 2.0.

**Best practices:** Historical and target data schemas must match. Use `id_cols` to break anomalies down by dimensions.

**Limitations:** Only the most recent 1,024 time points are evaluated (contact bqml-feedback@google.com for more). Minimum 3 data points required.

**Locations:** All supported BigQuery ML locations.

**Provisioned throughput:** Not specified. Billed at the evaluation, inspection, and prediction rate.

**BigFrames API:** No direct equivalent for TimesFM-based anomaly detection. Use `%%bigquery` magics or `session.read_gbq_query()` to execute AI.DETECT_ANOMALIES SQL from BigFrames. Note: `bigframes.ml.forecasting.ARIMAPlus.detect_anomalies()` exists but uses ARIMA_PLUS, not TimesFM.

---

### `AI.PREDICT`
- **Description:** (Preview) Table-valued function that performs zero-shot regression and classification on structured data using TabFM, Google's pre-trained tabular foundation model. You pass a labeled training table and an unlabeled prediction table in a single call; the model learns in context. There is no `CREATE MODEL`, no training job, no connection, no endpoint, and no persisted model object.
- **Use cases:** Predicting a numeric or categorical column without building a model, filling in missing structured attributes, quick baselines before investing in a trained model, prediction inside an analytics pipeline where a model artifact would be overhead.
- [documentation](https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-predict)
- **Type:** Table-valued function (TVF) -- Preview

**Syntax:**
```sql
AI.PREDICT(
  { TABLE TRAINING_TABLE | (TRAINING_QUERY) },
  { TABLE PREDICTION_TABLE | (PREDICTION_QUERY) }
  [, label_col => 'LABEL_COL' ]
)
```

**Inputs:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `TRAINING_TABLE` / `TRAINING_QUERY` | Table/Query | Required | -- | Labeled training data. Must contain the label column; **every other column is treated as a feature**. |
| `PREDICTION_TABLE` / `PREDICTION_QUERY` | Table/Query | Required | -- | Rows to predict. Must contain all training feature columns; extra columns are allowed. |
| `label_col` | Named arg, STRING | Optional | `'label'` | Name of the label column in the training data. A column literally named `label` needs no argument. |

Feature and label columns must be `STRING`, `BOOL`, `INT64`, `FLOAT64`, `NUMERIC`, or `BIGNUMERIC`. `DATE`, `TIMESTAMP`, `BYTES`, `JSON`, `GEOGRAPHY`, `ARRAY`, and `STRUCT` are rejected -- `EXTRACT` date parts into integers first.

**Task selection is implicit and type-driven.** There is no `task_type` argument:

| Label column type | Task | Added output columns |
|---|---|---|
| `INT64`, `FLOAT64`, `NUMERIC`, `BIGNUMERIC` | Regression | `predicted_<label>` (same type as the label) |
| `BOOL`, `STRING` | Classification | `predicted_<label>`, plus `predicted_<label>_probs` as `ARRAY<STRUCT<label STRING, prob FLOAT64>>` |

> **Cast your label.** A categorical encoded as INT64 (0/1, or a 1–5 rating) is silently treated as *regression* and you get fractional predictions with no probabilities. Cast it to `STRING` or `BOOL` to get classification. This consequence follows from the documented rule but is not itself documented.

The `label` subfield of `predicted_<label>_probs` is typed `STRING` even when the label column is `BOOL`. Array element ordering is not documented.

**Outputs:** The prediction input's columns plus the predicted column(s) above.

> **Doc bug.** The reference page states that AI.PREDICT "returns the columns from the training table or query result". Both of Google's own worked examples contradict this -- the returned rows are the *prediction* rows. Trust the behavior, not the sentence.

**Supported models:** TabFM only. Not selectable -- there is no `model` argument and no version pinning.

**Best practices:** Keep the feature set tight; the 20-column cap is a hard limit, not a guideline. Split train/predict deterministically (e.g. `FARM_FINGERPRINT`) so that the same rows train and predict on every run -- note this pins the *split* only; the predictions themselves are not reproducible (see Limitations). Pair every AI.PREDICT call with `AI.EVALUATE` on a held-out set -- without a metric you have no idea whether the zero-shot prediction is any good. Use it as a baseline: if a trained `CREATE MODEL` beats it materially, the training cost is justified; if not, you have saved a model lifecycle.

**Limitations:**
- **Output is not deterministic.** Repeating a byte-identical `AI.PREDICT` call over the same `FARM_FINGERPRINT` split returns slightly different predictions -- consistent with the model averaging shuffled ensemble passes (`n_ensembles`, whose value Google does not document). Demonstrated by `functions/ai_predict/ai_predict.ipynb` cells 25 and 28, whose top-5 multisets differ (`5760` vs `5728` in one slot) despite identical SQL and an `ORDER BY value DESC LIMIT 5`, so tie-breaking cannot explain it. The `workflows/tabular_prediction/` notebook shows the downstream consequence: `AI.EVALUATE` scores its *own* fresh TabFM predictions rather than the rows you materialized, so the two disagree (measured across four runs: regression MAE 236.52 / 236.35 / 235.84, classification accuracy 0.9468 / 0.9362 / 0.9468 -- regression drift well under 1%, classification drift about 1pp, or 2 rows in 94). **Materialize results once and join to them; do not re-run the prediction to reproduce a number.** Drift appears to be input-dependent -- `workflows/data_enrichment/` reproduced exactly across two runs on a 6-row prediction relation -- so absence of drift on a small input is not evidence of determinism.
- **20 feature columns** maximum (documented). Escalation path is emailing bqml-feedback@google.com.
- **10 classification categories** maximum (documented).
- **Practical row ceiling, undocumented but observed:** a call with 10,000 training rows fails with `Resources exceeded ... allotted memory`; 8,000 rows succeeds. Budget for roughly 5,000 training rows on on-demand slots.
- **Latency is flat and high:** 30--95 seconds per call regardless of input size. A notebook with several AI.PREDICT calls takes minutes, not seconds.
- Max prediction rows, max input size, timeouts, concurrency, NULL handling, categorical encoding, and the `n_ensembles` value are all **undocumented**. AI.PREDICT does not appear in any table on the BigQuery quotas page.
- Whether these limits also bind `AI.EVALUATE`'s TabFM branch is undocumented, though it runs the same model.

**Locations:** Not stated on the AI.PREDICT page. The AI.EVALUATE page says TabFM is available in all supported BigQuery ML locations (non-remote models), plus the US and EU multi-regions.

**Pricing:** Today, standard BigQuery slot / bytes-processed pricing. **From 2026-10-30**, TabFM moves to token-based pricing: you are charged for TabFM tokens plus slots/bytes for the non-inference parts of the query.

```
Input tokens  = (train_rows * columns + predict_rows * (columns - 1)) * n_ensembles
Output tokens = predict_rows * n_ensembles
```

at $0.05 / mtok input and $0.20 / mtok output. Note that `n_ensembles` -- the number of shuffled passes the model averages -- is a multiplier on your bill that Google does not document the value of.

**Provisioned throughput:** Not specified.

**BigFrames API:** No wrapper. `bigframes.bigquery.ai` has `forecast` but no `predict` -- checked against **bigframes 2.39.0**, this project's pin in `uv.lock` and the version that executed `functions/ai_predict/ai_predict.ipynb`. Use `%%bigquery` magics or `session.read_gbq_query()`.

---

### `AI.EVALUATE`
- **Description:** Dual-purpose table-valued function. Given history and actuals it evaluates a **TimesFM forecast** (MAE, MSE, RMSE, MAPE, sMAPE, MASE). Given training and prediction inputs plus a `label_col` it evaluates a **TabFM prediction** (regression or classification metrics). Which branch runs is selected entirely by which arguments you pass.
- **Use cases:** Evaluating forecast accuracy, benchmarking model configurations, comparing forecast quality across multiple time series, scoring AI.PREDICT output against a held-out set.
- [documentation](https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-evaluate)
- **Type:** Table-valued function -- GA (the TabFM branch is Preview)

**Branch selection:**

| You pass | Branch | Model |
|---|---|---|
| `data_col` + `timestamp_col` | Forecast evaluation | TimesFM |
| `label_col` | Prediction evaluation | TabFM |

**Syntax (TimesFM -- forecast evaluation):**
```sql
SELECT *
FROM AI.EVALUATE(
  { TABLE HISTORY_TABLE | (HISTORY_QUERY_STATEMENT) },
  { TABLE ACTUAL_TABLE | (ACTUAL_QUERY_STATEMENT) },
  data_col => 'DATA_COL',
  timestamp_col => 'TIMESTAMP_COL'
  [, model => 'MODEL']
  [, id_cols => ID_COLS]
  [, horizon => HORIZON]
  [, context_window => CONTEXT_WINDOW]
)
```

**Syntax (TabFM -- prediction evaluation, Preview):**
```sql
SELECT *
FROM AI.EVALUATE(
  { TABLE TRAINING_TABLE | (TRAINING_QUERY) },
  { TABLE PREDICTION_TABLE | (PREDICTION_QUERY) },
  label_col => 'LABEL_COL'
)
```

**Inputs -- TimesFM:**

| Parameter | Type | Required | Default | Range | Description |
|-----------|------|----------|---------|-------|-------------|
| `HISTORY_TABLE` / `HISTORY_QUERY_STATEMENT` | Table/Query | Required | -- | -- | Historical time series data used to generate a forecast |
| `ACTUAL_TABLE` / `ACTUAL_QUERY_STATEMENT` | Table/Query | Required | -- | -- | Actual time series data to evaluate the forecast against |
| `data_col` | STRING | Required | -- | -- | Data column name. Must be INT64, NUMERIC, BIGNUMERIC, or FLOAT64. |
| `timestamp_col` | STRING | Required | -- | -- | Timestamp column name. Must be TIMESTAMP, DATE, or DATETIME. |
| `model` | STRING | Optional | `'TimesFM 2.5'` | -- | `'TimesFM 2.0'` or `'TimesFM 2.5'`. Recommended: TimesFM 2.5 for all new work. |
| `id_cols` | ARRAY\<STRING\> | Optional | -- | -- | ID columns identifying unique time series |
| `horizon` | INT64 | Optional | 1024 | [1, 10000] | Number of forecasted time points to evaluate |
| `context_window` | INT64 | Optional | Auto-selected | See AI.FORECAST | Context window length for the TimesFM model. Same supported values as AI.FORECAST per model version. |

**Inputs -- TabFM:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `TRAINING_TABLE` / `TRAINING_QUERY` | Table/Query | Required | -- | Labeled training data. Every column other than the label is a feature. |
| `PREDICTION_TABLE` / `PREDICTION_QUERY` | Table/Query | Required | -- | Labeled evaluation data. Must contain all training feature columns. |
| `label_col` | STRING | **Required** | none | Label column name. **Unlike AI.PREDICT, this has no default** -- AI.PREDICT falls back to `'label'`, AI.EVALUATE does not. A `STRING`/`BOOL` label evaluates classification; a numeric label evaluates regression. |

The TabFM branch accepts no `model`, `horizon`, `id_cols`, `context_window`, `data_col`, or `timestamp_col`.

**Outputs -- TimesFM:**

| Column | Type | Description |
|--------|------|-------------|
| *id_cols* | (inherited) | Time series identifiers |
| `mean_absolute_error` | FLOAT64 | MAE for the time series |
| `mean_squared_error` | FLOAT64 | MSE for the time series |
| `root_mean_squared_error` | FLOAT64 | RMSE for the time series |
| `mean_absolute_percentage_error` | FLOAT64 | MAPE for the time series |
| `symmetric_mean_absolute_percentage_error` | FLOAT64 | sMAPE for the time series |
| `mean_absolute_scaled_error` | FLOAT64 | MASE for the time series |
| `ai_evaluate_status` | STRING | **`NULL` on success** -- not an empty string; error string if unsuccessful. A common value is `The time series data is too short.` |

> **Test this column with `IS NOT NULL`, not `<> ''`.** The three TimesFM status columns are *not* consistent with each other, verified live 2026-09-02: `ai_evaluate_status` and `ai_detect_anomalies_status` come back **`NULL`** on success (`IS NULL` is `true`, `LENGTH` is `NULL`), while `ai_forecast_status` comes back as a genuine **zero-length empty string** (`IS NULL` is `false`, `LENGTH` is `0`). So on AI.EVALUATE and AI.DETECT_ANOMALIES, `WHERE ai_evaluate_status = ''` matches nothing at all, and `WHERE ai_evaluate_status <> ''` silently drops **every successful row** -- three-valued logic makes the `NULL` comparison unknown, not true. Select failures with `IS NOT NULL` and successes with `IS NULL`. Only AI.FORECAST's column behaves the way the empty-string wording suggests.

**Outputs -- TabFM regression** (6 columns; no `ai_evaluate_status`, no id passthrough):

| Column | Type | Description |
|--------|------|-------------|
| `mean_absolute_error` | FLOAT64 | MAE for the data |
| `mean_squared_error` | FLOAT64 | MSE for the data |
| `mean_squared_log_error` | FLOAT64 | Mean squared logarithmic error |
| `median_absolute_error` | FLOAT64 | Median absolute error |
| `r2_score` | FLOAT64 | Coefficient of determination |
| `explained_variance` | FLOAT64 | Explained variance |

**Outputs -- TabFM classification** (4 columns):

| Column | Type | Description |
|--------|------|-------------|
| `precision` | FLOAT64 | Macro-average precision across all classes |
| `recall` | FLOAT64 | Macro-average recall across all classes |
| `accuracy` | FLOAT64 | Accuracy of the prediction |
| `f1_score` | FLOAT64 | Macro-average F1 score across all classes |

> Note what is **missing** relative to `ML.EVALUATE` on a trained classification model: TabFM's AI.EVALUATE returns no `log_loss` and no `roc_auc`, and no confusion matrix. If you need threshold-tuning or ranking metrics, this function will not give them to you.

**Supported models:** TimesFM 2.5 (default), TimesFM 2.0 on the forecast branch. TabFM on the prediction branch, where the `model` argument is not accepted.

**Best practices:** For forecasting, split data into historical (for forecasting) and actual (for comparison) portions using date-based filtering, and use `id_cols` to evaluate across multiple time series. For prediction, pass AI.EVALUATE exactly the same training and holdout inputs you passed AI.PREDICT -- the pair is only meaningful if the split matches.

**Limitations:** Minimum 3 data points required on the forecast branch. Default horizon is 1,024 (unlike AI.FORECAST which defaults to 10). TimesFM silently ignores data points beyond the max context (2,048 for 2.0, 15,360 for 2.5). On the TabFM branch, AI.PREDICT's documented caps -- **20 feature columns** and **10 classification categories** -- apply to the same model, though the AI.EVALUATE page has no Limitations section and does not restate them.

**Locations:** All supported BigQuery ML locations.

**Provisioned throughput:** Not specified. Billed at the evaluation, inspection, and prediction rate.

**BigFrames API:** No direct equivalent for either branch. Use `%%bigquery` magics or `session.read_gbq_query()` to execute AI.EVALUATE SQL from BigFrames. Note: `bigframes.ml.forecasting.ARIMAPlus.evaluate()` exists but uses ARIMA_PLUS, not TimesFM.

---
## Augmented Analytics

These functions answer analytical "why" questions over structured data — explaining *which segments of your data drive a change* in a metric. Like the Forecasting functions, they run entirely in BigQuery with no `CREATE MODEL` step, no connection, and no Gemini endpoint.

**Key relationships:**
- `AI.KEY_DRIVERS` performs contribution / key-driver analysis: it compares an interest set against a reference set and surfaces the data segments that most explain the difference in a summable metric. It is the simplified, model-free equivalent of creating a contribution analysis model and calling `ML.GET_INSIGHTS`.

---

### `AI.KEY_DRIVERS`
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

**Relationship to contribution analysis models / ML.GET_INSIGHTS:** Calling `AI.KEY_DRIVERS` is similar to first creating a contribution analysis model and then calling `ML.GET_INSIGHTS` on it. For most applications, `AI.KEY_DRIVERS` is recommended — simpler syntax, faster results, and automatic pruning. Use a contribution analysis model when you need more than 12 dimensions or non-summable metrics — see [`../bq-ml/RESOURCES.md`](../bq-ml/RESOURCES.md)'s `CONTRIBUTION_ANALYSIS` entry and [`../bq-ml/models/contribution_analysis/`](../bq-ml/models/contribution_analysis/), which uses this exact dataset and interest/reference split for a direct side-by-side comparison, and verifies both differentiators (ratio/category metrics, >12 dimensions) live, plus a finding not covered here: `ML.GET_INSIGHTS`'s output schema differs by metric type (summable vs. ratio vs. category each return different derived-statistic columns).

| | AI.KEY_DRIVERS | Contribution analysis model + ML.GET_INSIGHTS |
|---|----------------|------------------------------------------------|
| **Dimensions** | Maximum 12 | More than 12 |
| **Metric types** | Summable only | Summable, summable by ratio, summable by category |
| **Pruning** | Prunes redundant insights by default | Returns all insights by default |
| **Segment column** | `drivers` | `contributors` |
| **Model management** | None required | Create and manage a model |

---
## Document Processing

These functions process unstructured documents (PDFs, images, forms, invoices) using Document AI processors, returning structured extraction results directly as BigQuery columns.

**Key relationships:**
- `ML.PROCESS_DOCUMENT` requires a Document AI processor **and** a remote model (`CREATE MODEL` with `REMOTE_SERVICE_TYPE = 'CLOUD_AI_DOCUMENT_V1'`). Supports all processor types (invoice, receipt, form, OCR, custom).
- `AI.PARSE_DOCUMENT` requires a Document AI Layout Parser processor but **no `CREATE MODEL`** — the `endpoint` parameter points directly to the processor. Layout Parser only (OCR + chunking).

---

### `ML.PROCESS_DOCUMENT`
- **Description:** Table-valued function that processes unstructured documents from an object table using the Document AI API. Sends documents stored in Cloud Storage (referenced via a BigQuery object table) to a Document AI processor and returns structured extraction results (entities, key-value pairs, parsed content) directly as BigQuery columns.
- **Use cases:** Invoice parsing, expense/receipt extraction, form key-value extraction, OCR text extraction, document layout analysis and chunking (for RAG pipelines), bank statement parsing, W2/tax form parsing, utility bill parsing, pay slip parsing, US passport and driver license parsing, identity document proofing, custom document classification, custom document splitting, document summarization.
- [documentation](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-process-document)
- **Type:** Table-valued function (returns a table)

**Syntax:**
```sql
SELECT *
FROM ML.PROCESS_DOCUMENT(
  MODEL `PROJECT_ID.DATASET.MODEL`,
  { TABLE `PROJECT_ID.DATASET.OBJECT_TABLE` | (QUERY_STATEMENT) }
  [, PROCESS_OPTIONS => (JSON 'PROCESS_OPTIONS')]
);
```

**Model creation (prerequisite):**
```sql
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET_ID.MODEL_NAME`
REMOTE WITH CONNECTION {DEFAULT | `PROJECT_ID.REGION.CONNECTION_ID`}
OPTIONS (
  REMOTE_SERVICE_TYPE = 'CLOUD_AI_DOCUMENT_V1',
  DOCUMENT_PROCESSOR = 'PROCESSOR_ID'
);
```

**Inputs:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `MODEL` | Model reference | Required | -- | Fully-qualified name of a remote model with `REMOTE_SERVICE_TYPE = 'CLOUD_AI_DOCUMENT_V1'`. |
| `TABLE` / `(QUERY_STATEMENT)` | Table or subquery | Required | -- | Object table reference or a `SELECT` subquery over the object table. Subquery cannot use `JOIN` or rename columns with aliases. Must include `uri` and `content_type` columns. |
| `PROCESS_OPTIONS` | JSON (named parameter) | Optional | -- | A `ProcessOptions` resource in JSON format. Configures processing options like OCR config, layout parser chunking, page selection. |

**PROCESS_OPTIONS details:**

| Field | Applicable To | Description |
|-------|---------------|-------------|
| `ocrConfig.hints.languageHints[]` | OCR, Form Parser | BCP-47 language codes. Auto-detection if not specified. |
| `ocrConfig.enableNativePdfParsing` | OCR, Form Parser | Better extraction for PDFs with existing text. |
| `ocrConfig.enableImageQualityScores` | OCR, Form Parser | Returns quality scores. Adds latency. |
| `ocrConfig.premiumFeatures.enableSelectionMarkDetection` | OCR 2.0+ | Enable checkbox detection. |
| `ocrConfig.premiumFeatures.computeStyleInfo` | OCR, Form Parser | Enable font identification and style info. |
| `ocrConfig.premiumFeatures.enableMathOcr` | OCR, Form Parser | Extract LaTeX math formulas. |
| `layoutConfig.chunkingConfig.chunkSize` | Layout Parser | Chunk size for splitting documents. |
| `layoutConfig.chunkingConfig.includeAncestorHeadings` | Layout Parser | Include ancestor headings when splitting. |
| `layoutConfig.returnImages` | Layout Parser | Include images in response. |
| `layoutConfig.returnBoundingBoxes` | Layout Parser | Include bounding boxes. |
| `individualPageSelector.pages[]` | All | 1-indexed list of specific pages to process. |
| `fromStart` | All | Only process this many pages from the start. |
| `fromEnd` | All | Only process this many pages from the end. |

Note: `individualPageSelector`, `fromStart`, and `fromEnd` are a union field — only one can be specified. Setting `ocrConfig` on a non-OCR processor or `layoutConfig` on a non-Layout Parser processor returns an error.

**Outputs:**

| Column | Type | Description |
|--------|------|-------------|
| `ml_process_document_result` | JSON | Entities returned by the Document AI API (confidence scores, mention text, page anchors, bounding polygons, properties). |
| `ml_process_document_status` | STRING | API response status. Empty if successful. Contains error messages (e.g., `RESOURCE EXHAUSTED`) if processing failed. |
| *(processor-specific fields)* | *(varies)* | Fields specific to the processor (e.g., invoice parser returns `invoice_type`, `currency`, `total_amount`). Visible in the model's Schema tab under Labels. |
| *(object table columns)* | *(varies)* | All columns from the input object table or query are passed through (e.g., `uri`, `content_type`). |

**Supported Document AI processors:**

| Category | Processor | Type ID |
|----------|-----------|---------|
| Digitize Text | Enterprise Document OCR | `OCR_PROCESSOR` |
| Extract (General) | Custom Extractor | `CUSTOM_EXTRACTION_PROCESSOR` |
| Extract (General) | Form Parser | `FORM_PARSER_PROCESSOR` |
| Extract (General) | Layout Parser | `LAYOUT_PARSER_PROCESSOR` |
| Extract (Pretrained) | Bank Statement Parser | `BANK_STATEMENT_PROCESSOR` |
| Extract (Pretrained) | W2 Parser | `FORM_W2_PROCESSOR` |
| Extract (Pretrained) | US Passport Parser | `US_PASSPORT_PROCESSOR` |
| Extract (Pretrained) | Utility Parser | `UTILITY_PROCESSOR` |
| Extract (Pretrained) | Identity Document Proofing | `ID_PROOFING_PROCESSOR` |
| Extract (Pretrained) | Pay Slip Parser | `PAYSTUB_PROCESSOR` |
| Extract (Pretrained) | US Driver License Parser | `US_DRIVER_LICENSE_PROCESSOR` |
| Extract (Pretrained) | Expense Parser | `EXPENSE_PROCESSOR` |
| Extract (Pretrained) | Invoice Parser | `INVOICE_PROCESSOR` |
| Classify | Custom Classifier | `CUSTOM_CLASSIFICATION_PROCESSOR` |
| Split | Custom Splitter | `CUSTOM_SPLITTING_PROCESSOR` |
| Summarize | Summarizer | `SUMMARY_PROCESSOR` |

**Supported file types:**

| Format | Extensions | MIME Type |
|--------|-----------|-----------|
| PDF | `.pdf` | `application/pdf` |
| GIF | `.gif` | `image/gif` |
| TIFF | `.tiff`, `.tif` | `image/tiff` |
| JPEG | `.jpg`, `.jpeg` | `image/jpeg` |
| PNG | `.png` | `image/png` |
| BMP | `.bmp` | `image/bmp` |
| WebP | `.webp` | `image/webp` |
| HTML | `.html` | `text/html` (Layout Parser only) |
| Word OOXML | `.docx` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` (Layout Parser only) |
| PowerPoint OOXML | `.pptx` | `application/vnd.openxmlformats-officedocument.presentationml.presentation` (Layout Parser only) |
| Excel OOXML | `.xlsx` | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` (Layout Parser only) |

**Best practices:**
- Filter documents with `WHERE`/`LIMIT` in a subquery rather than processing the entire object table.
- Use `CREATE TABLE ... AS SELECT` to persist results and avoid re-processing.
- Handle `RESOURCE_EXHAUSTED` errors with BigQuery remote inference SQL scripts or the Dataform package for retry-until-complete iteration.
- Select only the processor-specific columns you need rather than `SELECT *`.
- Minimum 200 dpi for document scans; 300 dpi or higher recommended.

**Limitations:**
- Maximum **130 pages per document**. Rows with larger documents return an error.
- **120-second timeout per request.** Documents that take longer to process will fail.
- **Requests are processed in batches of 10.**
- Custom Splitter only supports PDF, TIFF, TIF, and GIF.
- See [Cloud AI service functions quotas](https://cloud.google.com/bigquery/quotas#cloud_ai_service_functions) for current rate limits.
- Some rows may show `RESOURCE EXHAUSTED` errors after job success — BigQuery retries internally, but parallel batch queries can exceed quota limits.

**Locations:** Models can only be created in the **US** and **EU** multi-regions. The dataset, connection, and Document AI processor must all be in the same region.

**Provisioned throughput:** Not specified. Subject to Document AI API quotas.

**BigFrames API:** No direct equivalent. Use `%%bigquery` magics or `session.read_gbq_query()` to execute ML.PROCESS_DOCUMENT SQL from BigFrames.

---

### `AI.PARSE_DOCUMENT`
- **⚠️ Status (as of 2026-09-01): OFFLINE, and reference documentation now WITHDRAWN.** The function (Preview) was taken offline by Google for revision on 2026-06-01 and does not execute. As of this audit the situation has escalated: the reference page `.../bigqueryml-syntax-ai-parse-document` returns **HTTP 404**, the function no longer appears in the BigQuery docs navigation tree, and it is absent from the generative AI overview page. Google has published no release note explaining the withdrawal.
  - **Interim alternative:** use [`ML.PROCESS_DOCUMENT`](#ml_process_document) for OCR and document extraction. It reaches the same Document AI processors but requires a remote model and a `CREATE MODEL` step — precisely the setup AI.PARSE_DOCUMENT was introduced to remove.
  - **Affected content:** `functions/ai_parse_document/` and `workflows/document_rag/` carry warning banners. Their committed outputs are a record of the function working before 2026-06-01, not current behavior. Do not re-run them.
  - **Re-check** the [BigQuery release notes](https://docs.cloud.google.com/bigquery/docs/release-notes). If it returns, reverse this note, remove the notebook banners, and re-run to verify (precedent: AI.AGG disable Apr 2026 → re-enable May 2026). Documentation below is retained from the last published version of the page — treat it as an archived snapshot, not a live reference.
- **Description:** (Preview) Table-valued function that parses documents using the Document AI Layout Parser. Combines OCR, layout parsing, and chunking into a single SQL function call — no `CREATE MODEL` step required. The `endpoint` parameter points directly to a Document AI Layout Parser processor.
- **Use cases:** Document text extraction, chunking for RAG pipelines, OCR from scanned documents, layout-aware document parsing.
- [documentation](https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-parse-document) — **dead link (HTTP 404 as of 2026-09-01)**, retained so the page can be re-checked if the function returns
- **Type:** Table-valued function (returns a table) — Preview

**Syntax:**
```sql
SELECT *
FROM AI.PARSE_DOCUMENT(
  { TABLE `PROJECT_ID.DATASET.OBJECT_TABLE` | (QUERY_STATEMENT) },
  endpoint => 'projects/PROJECT_NUM/locations/LOCATION/processors/PROCESSOR_ID'
  [, chunk_size => CHUNK_SIZE ]
  [, connection_id => 'PROJECT_ID.LOCATION.CONNECTION_ID' ]
);
```

**Inputs:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `TABLE` / `(QUERY_STATEMENT)` | Table or subquery | Required | -- | Object table reference or a `SELECT` subquery. Must include a column named `ref` of type `OBJECTREF`. Can be an object table (which has `ref` built-in) or a subquery that constructs `ref` using `OBJ.MAKE_REF(uri, connection) AS ref`. |
| `endpoint` | STRING (named parameter) | Required | -- | Document AI Layout Parser processor endpoint. Format: `projects/{project}/locations/{location}/processors/{processor_id}`. |
| `chunk_size` | INT64 (named parameter) | Optional | ~1000 | Controls the size of text chunks when splitting documents. Smaller values (e.g., 250) produce more granular chunks for RAG pipelines. |
| `connection_id` | STRING (named parameter) | Optional | End-user credentials | BigQuery Cloud resource connection. Format: `PROJECT_ID.LOCATION.CONNECTION_ID`. Connection service account needs `documentai.apiUser` and `storage.objectViewer` roles. |

**Outputs:**

| Column | Type | Description |
|--------|------|-------------|
| `chunk_id` | INT64 | Sequence ID of an extracted document chunk, starting from 1. |
| `start_page` | INT64 | Page number where the chunk starts. |
| `end_page` | INT64 | Page number where the chunk ends. |
| `content` | STRING | Extracted text content of the chunk. |
| *(object table columns)* | *(varies)* | All columns from the input object table or query are passed through (e.g., `uri`, `content_type`). |

**Supported file types:** Same as ML.PROCESS_DOCUMENT — PDF, JPEG, PNG, BMP, GIF, TIFF, WebP, plus HTML, DOCX, PPTX, XLSX (Layout Parser only).

**ObjectRef alternative (no object table required):**

AI.PARSE_DOCUMENT requires a `ref` column in its input. Object tables provide this automatically, but you can also construct it inline using `OBJ.MAKE_REF`:

```sql
-- Single document — no object table needed
SELECT *
FROM AI.PARSE_DOCUMENT(
  (SELECT
    'gs://BUCKET/document.pdf' AS uri,
    OBJ.MAKE_REF('gs://BUCKET/document.pdf', 'PROJECT_ID.LOCATION.CONNECTION_ID') AS ref
  ),
  endpoint => 'projects/PROJECT_NUM/locations/LOCATION/processors/PROCESSOR_ID'
);

-- Multiple documents — use UNNEST
SELECT *
FROM AI.PARSE_DOCUMENT(
  (SELECT
    uri,
    OBJ.MAKE_REF(uri, 'PROJECT_ID.LOCATION.CONNECTION_ID') AS ref
  FROM UNNEST(['gs://BUCKET/doc1.pdf', 'gs://BUCKET/doc2.pdf']) AS uri),
  endpoint => 'projects/PROJECT_NUM/locations/LOCATION/processors/PROCESSOR_ID'
);
```

This is useful for ad-hoc parsing of specific documents without creating an object table first.

**Best practices:**
- Filter documents with `WHERE`/`LIMIT` in a subquery rather than processing the entire object table.
- Use `CREATE TABLE ... AS SELECT` to persist results and avoid re-processing.
- For RAG pipelines, use `chunk_size => 250` for more granular retrieval precision.
- Minimum 200 dpi for document scans; 300 dpi or higher recommended.

**Limitations:**
- Maximum **130 pages per document**. Rows with larger documents return an error.
- **Layout Parser only** — does not support other Document AI processor types (use ML.PROCESS_DOCUMENT for invoice, receipt, form, OCR, or custom processors).
- Requires creating a Document AI Layout Parser processor first (but no `CREATE MODEL` step).

**Locations:** The dataset, connection, and Document AI processor must all be in the **US** or **EU** multi-regions.

**Provisioned throughput:** Not specified. Subject to Document AI API quotas.

**BigFrames API:** No direct equivalent. Use `%%bigquery` magics or `session.read_gbq_query()` to execute AI.PARSE_DOCUMENT SQL from BigFrames.

**Relationship to ML.PROCESS_DOCUMENT:** AI.PARSE_DOCUMENT is to ML.PROCESS_DOCUMENT what AI.GENERATE is to AI.GENERATE_TEXT — a simplified alternative that skips the `CREATE MODEL` step. Use ML.PROCESS_DOCUMENT when you need specialized processors (invoice, form, custom) or full `PROCESS_OPTIONS` control. Use AI.PARSE_DOCUMENT for straightforward OCR + chunking workflows.

---
## Unstructured Data Infrastructure

These are not AI functions themselves, but the infrastructure that enables AI functions to work with unstructured data (images, PDFs, audio, video) stored in Cloud Storage. **Object tables** provide metadata-indexed access to Cloud Storage objects, and **ObjectRef functions** create and manage typed references to those objects for use in AI function prompts.

**Key relationships:**
- **Object tables** are read-only external tables over Cloud Storage objects with metadata columns (`uri`, `content_type`, `size`, etc.) and an optional `ref` column containing `ObjectRef` values.
- `OBJ.MAKE_REF` creates `ObjectRef` values from URI strings — the entry point for referencing Cloud Storage objects.
- `OBJ.FETCH_METADATA` enriches partial `ObjectRef` values with Cloud Storage metadata (content type, size, MD5 hash).
- `OBJ.GET_ACCESS_URL` converts `ObjectRef` into `ObjectRefRuntime` with signed URLs — the format accepted by AI functions like `AI.GENERATE`.
- **For AI.PARSE_DOCUMENT:** Only `OBJ.MAKE_REF` is needed — alias it as `ref` in the subquery. No `OBJ.FETCH_METADATA` or `OBJ.GET_ACCESS_URL` required.
- **Typical pipeline (Gemini functions):** URI → `OBJ.MAKE_REF` → `OBJ.FETCH_METADATA` → `OBJ.GET_ACCESS_URL` → `AI.GENERATE`/`AI.GENERATE_TEXT`/etc.
- **Typical pipeline (AI.PARSE_DOCUMENT):** URI → `OBJ.MAKE_REF` (as `ref` column) → `AI.PARSE_DOCUMENT`.

**Object tables vs inline ObjectRef:**
- **Object tables** with remote models (e.g., `AI.GENERATE_EMBEDDING` reading from an object table) require a BigQuery reservation. Best for large-scale processing where you have reservations configured.
- **Inline ObjectRef** queries (building the pipeline in a subquery: `OBJ.MAKE_REF` → `OBJ.FETCH_METADATA` → `OBJ.GET_ACCESS_URL`) do **not** require a reservation. Best for ad-hoc multimodal queries and prototyping. All embedding and similarity function notebooks in this project use inline ObjectRef.

---

### Object Tables
- **Description:** Read-only external tables over unstructured data objects in Cloud Storage. Each row corresponds to a Cloud Storage object, with columns for object metadata. Object tables use access delegation via a Cloud resource connection — users need access to the table, not direct access to Cloud Storage.
- **Use cases:** Indexing Cloud Storage objects for AI function processing, document analysis pipelines, image/video/audio inference, joining unstructured data results with structured BigQuery data.
- [introduction](https://cloud.google.com/bigquery/docs/object-table-introduction) · [create](https://cloud.google.com/bigquery/docs/object-table-create) · [DDL reference](https://cloud.google.com/bigquery/docs/reference/standard-sql/data-definition-language#create_external_table_statement)

**CREATE syntax:**
```sql
CREATE [ OR REPLACE ] EXTERNAL TABLE [ IF NOT EXISTS ] `PROJECT_ID.DATASET.TABLE_NAME`
WITH CONNECTION { `PROJECT_ID.REGION.CONNECTION_ID` | DEFAULT }
OPTIONS (
    object_metadata = 'SIMPLE',
    uris = ['BUCKET_PATH'[, ...]],
    [max_staleness = STALENESS_INTERVAL,]
    [metadata_cache_mode = 'CACHE_MODE']
);
```

**Example (minimal):**
```sql
CREATE EXTERNAL TABLE `myproject.mydataset.documents`
WITH CONNECTION `myproject.us.myconnection`
OPTIONS (
    object_metadata = 'SIMPLE',
    uris = ['gs://mybucket/documents/*.pdf']
);
```

**Example (with metadata caching):**
```sql
CREATE EXTERNAL TABLE `myproject.mydataset.documents`
WITH CONNECTION `myproject.us.myconnection`
OPTIONS (
    object_metadata = 'SIMPLE',
    uris = ['gs://mybucket/*'],
    max_staleness = INTERVAL 1 DAY,
    metadata_cache_mode = 'AUTOMATIC'
);
```

**Metadata columns:**

| Column | Type | Description |
|--------|------|-------------|
| `uri` | STRING | Cloud Storage URI (`gs://bucket/path/object`). |
| `generation` | INTEGER | Object version identifier. |
| `content_type` | STRING | MIME type of the object (e.g., `image/jpeg`, `application/pdf`). Defaults to `application/octet-stream` if not set. |
| `size` | INTEGER | Content length in bytes. |
| `md5_hash` | STRING | MD5 hash of the data, base64-encoded. |
| `updated` | TIMESTAMP | Last time the object's metadata was modified. |
| `metadata` | RECORD (REPEATED) | Custom metadata as key-value pairs (`name` STRING, `value` STRING). |
| `ref` | STRUCT (Preview) | `ObjectRef` value: `STRUCT<uri STRING, version STRING, authorizer STRING, details JSON>`. Created only if on the multimodal data preview allowlist. |

There is also a `data` pseudocolumn containing raw file bytes, used by `ML.DECODE_IMAGE`. It cannot be directly queried.

**CREATE parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `object_metadata` | STRING | Required | -- | Must be `'SIMPLE'` for object tables. |
| `uris` | ARRAY\<STRING\> | Required | -- | Cloud Storage URIs. One `*` wildcard allowed per path. Multiple buckets supported. |
| `max_staleness` | INTERVAL | Optional | `0` (disabled) | Metadata cache staleness. Range: 30 minutes to 7 days. |
| `metadata_cache_mode` | STRING | Optional (required if `max_staleness > 0`) | -- | `'AUTOMATIC'` (system-refreshed every 30–60 min) or `'MANUAL'` (you call `BQ.REFRESH_EXTERNAL_METADATA_CACHE`). |

**Metadata caching:**
- Without caching, queries must list files from Cloud Storage — can take several minutes for large tables.
- With caching, queries use cached metadata. Set `max_staleness` and `metadata_cache_mode`.
- Automatic refresh: system-defined interval (30–60 min). Recommended: create a `BACKGROUND` reservation for refresh jobs.
- Manual refresh: `CALL BQ.REFRESH_EXTERNAL_METADATA_CACHE('project.dataset.table');`
- Cache expires after 7 days if not refreshed.

**Signed URLs (EXTERNAL_OBJECT_TRANSFORM):**
```sql
SELECT uri, signed_url
FROM EXTERNAL_OBJECT_TRANSFORM(TABLE `mydataset.myobjecttable`, ['SIGNED_URL']);
```
Signed URLs expire after 6 hours. Row-level access policies restrict which URLs a user can generate.

**Connection requirements:**
- Requires a **Cloud resource connection** (type: "Vertex AI remote models, remote functions, BigLake and Spanner").
- Connection's service account needs `roles/storage.objectViewer` on the Cloud Storage bucket.
- Connection must be in the same region as the dataset.

**AI function integration:**
- `ML.PROCESS_DOCUMENT` — document extraction via Document AI processors.
- `AI.GENERATE_TEXT` / `AI.GENERATE` — text generation from object data via ObjectRef/signed URLs.
- `AI.GENERATE_EMBEDDING` — embeddings from image/video data.
- `AI.SCORE` — score documents using tuple syntax: `AI.SCORE(('text', OBJ.GET_ACCESS_URL(ref, 'r')))`.
- `AI.CLASSIFY` — classify documents via `EXTERNAL_OBJECT_TRANSFORM`: `AI.CLASSIFY(docs.ref, categories)`.
- `ML.ANNOTATE_IMAGE` — image annotation via Cloud Vision API.
- `ML.TRANSCRIBE` — audio transcription via Speech-to-Text API.

**Limitations:**
- Read-only — cannot alter data or use DML.
- Maximum **60 million rows** (300 million in preview with allowlist).
- Maximum **10 GB of object metadata** per query.
- Not available in Legacy SQL, AWS, or Azure.
- `UNION ALL` combining empty and non-empty object tables may error.
- Signed URLs expire after 6 hours.

**Locations:** Any BigQuery region or multi-region. Connection must be colocated with the dataset.

---

### `OBJ.MAKE_REF`
- **Description:** (Preview) Scalar function that creates an `ObjectRef` value containing reference information for a Cloud Storage object. This is the entry point for creating ObjectRef values from raw URI strings — no validation is performed on JSON input.
- **Use cases:** Create ObjectRef values for standard table columns without object tables, build ad-hoc ObjectRef values inline in queries for one-off multimodal analysis, reference transformation outputs saved to Cloud Storage.
- [documentation](https://cloud.google.com/bigquery/docs/reference/standard-sql/objectref_functions)
- **Type:** Scalar function (returns ObjectRef STRUCT) — Preview

**Syntax (URI + authorizer):**
```sql
OBJ.MAKE_REF(
  uri,
  authorizer
)
```

**Syntax (JSON input):**
```sql
OBJ.MAKE_REF(
  objectref_json
)
```

**Inputs:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `uri` | STRING | Required (overload 1) | Cloud Storage URI, e.g., `gs://mybucket/file.jpg`. Can be a column reference. |
| `authorizer` | STRING | Required (overload 1) | Cloud resource connection, e.g., `us.myconnection`. Must be in the same project and region as the query. |
| `objectref_json` | JSON | Required (overload 2) | JSON with schema `{"uri": "string", "authorizer": "string"}`. No validation performed. |

**Outputs:** Returns `STRUCT<uri STRING, version STRING, authorizer STRING, details JSON>`. Only `uri` and `authorizer` are populated; `version` and `details` are empty (use `OBJ.FETCH_METADATA` to fill them).

**Limitations:**
- Maximum **20 connections** per project+region for queries referencing ObjectRef values.
- Connection must be in the same project and region as the query.

**Locations:** All BigQuery regions supporting Cloud resource connections.

---

### `OBJ.FETCH_METADATA`
- **Description:** (Preview) Scalar function that fetches Cloud Storage metadata for a partially populated `ObjectRef` value. Takes an ObjectRef with `uri` and `authorizer` (typically from `OBJ.MAKE_REF`) and fills in the `details` field with `content_type`, `md5_hash`, `size`, and `updated` from Cloud Storage. Still succeeds on error — the `details` field contains an `error` field instead.
- **Use cases:** Populate ObjectRef columns with full metadata when not using object tables, refresh metadata for existing ObjectRef values after underlying objects change, combine with `OBJ.MAKE_REF` in a single expression: `OBJ.FETCH_METADATA(OBJ.MAKE_REF(uri, 'connection'))`.
- [documentation](https://cloud.google.com/bigquery/docs/reference/standard-sql/objectref_functions)
- **Type:** Scalar function (returns fully-populated ObjectRef STRUCT) — Preview

**Syntax:**
```sql
OBJ.FETCH_METADATA(
  objectref
)
```

**Inputs:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `objectref` | ObjectRef STRUCT | Required | Partially populated ObjectRef (with `uri` and `authorizer`). Typically from `OBJ.MAKE_REF()`. |

**Outputs:** Returns a fully populated `ObjectRef` STRUCT. The `details` JSON field contains:
```json
{
  "gcs_metadata": {
    "content_type": "image/png",
    "md5_hash": "d9c38814e44028bf7a012131941d5631",
    "size": 23000,
    "updated": 1741374857000000
  }
}
```
On error, `details` contains `{"errors": {"OBJ.FETCH_METADATA": "error message"}}` instead.

**Required permissions:** `bigquery.objectRefs.read` on the connection (from `roles/bigquery.objectRefReader` or `roles/bigquery.objectRefAdmin`). Connection service account needs `roles/storage.objectUser`.

**Limitations:**
- Same 20-connection limit per project+region.
- Less scalable than object tables for large numbers of objects (requires per-object metadata retrieval from Cloud Storage).

**Locations:** All BigQuery regions supporting Cloud resource connections.

---

### `OBJ.GET_ACCESS_URL`
- **Description:** (Preview) Scalar function that converts an `ObjectRef` into an `ObjectRefRuntime` JSON value containing signed access URLs. The resulting `ObjectRefRuntime` is the format accepted by AI functions (`AI.GENERATE`, `AI.GENERATE_TEXT`, `AI.GENERATE_EMBEDDING`, `AI.EMBED`, `AI.SIMILARITY`, etc.) for processing unstructured data.
- **Use cases:** Generate signed read URLs for AI function input, generate writable signed URLs for saving transformation outputs to Cloud Storage, bridge ObjectRef values to generative AI function prompts.
- [documentation](https://cloud.google.com/bigquery/docs/reference/standard-sql/objectref_functions)
- **Type:** Scalar function (returns ObjectRefRuntime JSON) — Preview

**Syntax:**
```sql
OBJ.GET_ACCESS_URL(
  objectref,
  mode
  [, duration]
)
```

**Inputs:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `objectref` | ObjectRef STRUCT | Required | -- | An ObjectRef value representing a Cloud Storage object. |
| `mode` | STRING | Required | -- | `'r'` for read-only URL, `'rw'` for read and write URLs. |
| `duration` | INTERVAL | Optional | `INTERVAL 6 HOUR` | URL validity period. Range: 30 minutes to 6 hours. |

**Outputs:** Returns `ObjectRefRuntime` JSON:
```json
{
  "obj_ref": {
    "uri": "gs://bucket/file.jpg",
    "version": "12345",
    "authorizer": "us.connection1",
    "details": {"gcs_metadata": {...}}
  },
  "access_urls": {
    "read_url": "https://storage.googleapis.com/...",
    "write_url": "https://storage.googleapis.com/...",
    "expiry_time": "2024-01-15T18:30:00Z"
  }
}
```
On error, `access_urls` is replaced by `runtime_errors`.

**Required permissions:**
- Read URLs (`'r'`): `bigquery.objectRefs.read` (from `roles/bigquery.objectRefReader` or `roles/bigquery.objectRefAdmin`).
- Write URLs (`'rw'`): `bigquery.objectRefs.write` (from `roles/bigquery.objectRefAdmin` only).

**Compatible AI functions:** `AI.GENERATE`, `AI.GENERATE_TEXT`, `AI.GENERATE_TABLE`, `AI.GENERATE_BOOL`, `AI.GENERATE_DOUBLE`, `AI.GENERATE_INT`, `AI.IF`, `AI.GENERATE_EMBEDDING`, `ML.GENERATE_EMBEDDING`, `AI.EMBED`, `AI.SIMILARITY`. Also used indirectly by `AI.SCORE` (via object table `ref` column with tuple syntax) and `AI.CLASSIFY` (via object table `ref` column with `EXTERNAL_OBJECT_TRANSFORM`). See [Multimodal Input Patterns](#multimodal-input-patterns-by-function) for details.

**Limitations:**
- Access URLs expire after at most 6 hours. Do not persist `ObjectRefRuntime` values long-term — regenerate from `ObjectRef` values.
- Same 20-connection limit per project+region.

**Locations:** All BigQuery regions supporting Cloud resource connections.

---

### ObjectRef and ObjectRefRuntime Schema Reference

**ObjectRef** — a STRUCT stored in BigQuery table columns:
```sql
STRUCT<
  uri STRING,           -- Cloud Storage URI (gs://bucket/path/file)
  version STRING,       -- Cloud Storage object version
  authorizer STRING,    -- Cloud resource connection for access
  details JSON          -- Cloud Storage metadata (content_type, md5_hash, size, updated)
>
```

**ObjectRefRuntime** — a JSON value produced by `OBJ.GET_ACCESS_URL`:
```json
{
  "obj_ref": { "uri", "version", "authorizer", "details" },
  "access_urls": { "read_url", "write_url", "expiry_time" }
}
```

**Array support:** `ARRAY<STRUCT<uri STRING, version STRING, authorizer STRING, details JSON>>` columns can store ordered collections of ObjectRef values (e.g., video frames). Use `ARRAY_AGG` with `ORDER BY` to aggregate and `UNNEST` with `WITH OFFSET` to decompose.

**Typical workflow:**
```
URI string
  → OBJ.MAKE_REF(uri, connection)        → ObjectRef (partial — uri + authorizer only)
  → OBJ.FETCH_METADATA(objectref)        → ObjectRef (full — with metadata)
  → OBJ.GET_ACCESS_URL(objectref, 'r')   → ObjectRefRuntime (with signed URLs)
  → AI.GENERATE(STRUCT(prompt, runtime))  → Generated output
```

**Shortcut from object tables:** When the `ref` column is available (preview allowlist), skip `MAKE_REF`/`FETCH_METADATA` and use `OBJ.GET_ACCESS_URL(ref, 'r')` directly.

---

### Multimodal Input Patterns by Function

Different AI functions accept multimodal input in different ways. Here are the four patterns, with examples for each.

#### Pattern 1: STRUCT Prompt (most generation functions + AI.IF)

Replace the STRING prompt with a STRUCT containing text and ObjectRefRuntime references. Works inline — no object table needed.

**Functions:** `AI.GENERATE`, `AI.GENERATE_TEXT`, `AI.GENERATE_TABLE`, `AI.GENERATE_BOOL`, `AI.GENERATE_DOUBLE`, `AI.GENERATE_INT`, `ML.GENERATE_TEXT`, `AI.IF`

```sql
-- Scalar function (AI.GENERATE)
SELECT (AI.GENERATE(
  STRUCT(
    'Summarize this document.' AS prompt,
    [OBJ.GET_ACCESS_URL(
      OBJ.FETCH_METADATA(
        OBJ.MAKE_REF('gs://bucket/doc.pdf', 'PROJECT.REGION.CONNECTION')
      ), 'r'
    )] AS object_ref_runtime
  )
)).result;

-- TVF (AI.GENERATE_TEXT)
SELECT result
FROM AI.GENERATE_TEXT(
  MODEL `project.dataset.model`,
  (SELECT STRUCT(
    'Summarize this document.' AS prompt,
    [OBJ.GET_ACCESS_URL(
      OBJ.FETCH_METADATA(
        OBJ.MAKE_REF('gs://bucket/doc.pdf', 'PROJECT.REGION.CONNECTION')
      ), 'r'
    )] AS object_ref_runtime
  ) AS prompt)
);

-- Managed function (AI.IF)
SELECT AI.IF(
  STRUCT(
    'This document is a financial invoice' AS prompt,
    [OBJ.GET_ACCESS_URL(
      OBJ.FETCH_METADATA(
        OBJ.MAKE_REF('gs://bucket/doc.pdf', 'PROJECT.REGION.CONNECTION')
      ), 'r'
    )] AS object_ref_runtime
  )
) AS is_invoice;
```

#### Pattern 2: Object Table with Tuple Syntax (AI.SCORE)

`AI.SCORE` does not accept the STRUCT prompt pattern. Instead, query an object table and pass a tuple of (scoring text, ObjectRefRuntime).

**Functions:** `AI.SCORE`

```sql
-- Create an object table first
CREATE EXTERNAL TABLE `project.dataset.docs`
WITH CONNECTION `project.region.connection`
OPTIONS (object_metadata = 'SIMPLE', uris = ['gs://bucket/path/*.pdf']);

-- Score documents using tuple syntax
SELECT
  uri,
  AI.SCORE(
    ('Rate the professionalism of this document on a scale of 0 to 1',
     OBJ.GET_ACCESS_URL(ref, 'r'))
  ) AS professionalism
FROM `project.dataset.docs`;
```

#### Pattern 3: Object Table with EXTERNAL_OBJECT_TRANSFORM (AI.CLASSIFY)

`AI.CLASSIFY` requires an object table queried through `EXTERNAL_OBJECT_TRANSFORM` to get signed URLs, then uses the transformed `ref` column.

**Functions:** `AI.CLASSIFY`

```sql
-- Create an object table first
CREATE EXTERNAL TABLE `project.dataset.docs`
WITH CONNECTION `project.region.connection`
OPTIONS (object_metadata = 'SIMPLE', uris = ['gs://bucket/path/*']);

-- Classify documents via EXTERNAL_OBJECT_TRANSFORM
SELECT
  docs.uri,
  AI.CLASSIFY(docs.ref, ['invoice', 'receipt', 'contract', 'letter']) AS doc_type
FROM EXTERNAL_OBJECT_TRANSFORM(
  TABLE `project.dataset.docs`, ['SIGNED_URL']) AS docs;
```

#### Pattern 4: ObjectRef Content Parameter (Embedding functions)

Embedding and similarity functions accept ObjectRef or ObjectRefRuntime directly as the content parameter (not as a STRUCT prompt). Requires a multimodal embedding endpoint (e.g., `multimodalembedding@001`).

**Functions:** `AI.EMBED`, `AI.GENERATE_EMBEDDING`, `ML.GENERATE_EMBEDDING`, `AI.SIMILARITY`

```sql
-- AI.EMBED with inline ObjectRef
SELECT AI.EMBED(
  OBJ.GET_ACCESS_URL(
    OBJ.FETCH_METADATA(
      OBJ.MAKE_REF('gs://bucket/image.jpg', 'PROJECT.REGION.CONNECTION')
    ), 'r'
  ),
  'multimodalembedding@001',
  connection_id => 'PROJECT.REGION.CONNECTION'
).result AS embedding;

-- AI.SIMILARITY with ObjectRef
SELECT AI.SIMILARITY(
  OBJ.GET_ACCESS_URL(
    OBJ.FETCH_METADATA(
      OBJ.MAKE_REF('gs://bucket/img1.jpg', 'PROJECT.REGION.CONNECTION')
    ), 'r'
  ),
  OBJ.GET_ACCESS_URL(
    OBJ.FETCH_METADATA(
      OBJ.MAKE_REF('gs://bucket/img2.jpg', 'PROJECT.REGION.CONNECTION')
    ), 'r'
  ),
  'multimodalembedding@001',
  connection_id => 'PROJECT.REGION.CONNECTION'
) AS similarity;
```

#### Pattern Summary

| Pattern | Functions | Object Table Required? | Input Method |
|---------|-----------|----------------------|--------------|
| STRUCT prompt | AI.GENERATE, AI.GENERATE_TEXT, AI.GENERATE_TABLE, AI.GENERATE_BOOL, AI.GENERATE_DOUBLE, AI.GENERATE_INT, ML.GENERATE_TEXT, AI.IF | No | `STRUCT(text AS prompt, [refs] AS object_ref_runtime)` |
| Tuple + object table | AI.SCORE | Yes | `('scoring text', OBJ.GET_ACCESS_URL(ref, 'r'))` |
| EXTERNAL_OBJECT_TRANSFORM | AI.CLASSIFY | Yes | `AI.CLASSIFY(docs.ref, categories)` via `EXTERNAL_OBJECT_TRANSFORM` |
| ObjectRef content | AI.EMBED, AI.SIMILARITY, AI.GENERATE_EMBEDDING, ML.GENERATE_EMBEDDING | No (but supported) | Pass ObjectRefRuntime as the `content` parameter |
| Object table (document processing) | ML.PROCESS_DOCUMENT | Yes | Object table rows as input to Document AI processor |
| Not supported | VECTOR_SEARCH, AI.SEARCH, AI.FORECAST, AI.DETECT_ANOMALIES, AI.PREDICT, AI.EVALUATE | — | Text/numeric input only |
