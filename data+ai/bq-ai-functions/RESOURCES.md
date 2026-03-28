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

BigQuery AI functions let you use generative AI, embeddings, forecasting, and anomaly detection directly within SQL queries. These functions span several categories: general-purpose text/multimodal generation, managed classification and scoring, embedding generation and semantic search, and time series forecasting. They connect to Vertex AI models (Gemini, embedding models, TimesFM, and third-party models) and can process structured data, text, images, audio, video, and PDFs -- all from within BigQuery SQL.

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
| `model_params` | JSON literal | Optional | -- | Additional parameters conforming to the `generateContent` request body format. Can set any field except `contents`. Supports `thinking_config`, `cachedContent`, `tools` (e.g., `googleSearch`, `googleMaps`), `generation_config`, etc. |
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

**Supported models:** Any GA or preview Gemini model. Default: `gemini-2.5-flash`. Examples: `gemini-2.5-flash`, `gemini-3-pro-preview`, `gemini-3-flash-preview`. Can use global endpoint for cross-region processing.

**Best practices:**
- Function incurs Vertex AI charges each time it is called. Track costs accordingly.
- To minimize charges when using LIMIT, materialize the selected data to a table first, then call AI.GENERATE on that table (avoids re-evaluating the subquery).

**Limitations:**
- Video input limited to 2 minutes maximum (only first 2 min processed).
- At most one video object per prompt.
- Global endpoint does not allow controlling or knowing the data processing region.
- Gemini 2.5 models incur thinking charges; budget can be set for Flash/Flash-Lite but not Pro.

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

**Limitations:** Preview feature (Pre-GA Offerings Terms apply). Video limited to 2 minutes. At most one video object per prompt. Gemini 2.5 thinking charges apply.

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

**Supported models:** Same as AI.GENERATE_TEXT (remote models over Gemini, Claude, Llama, Mistral, open models).

**Best practices / Limitations / Locations / Provisioned throughput:** Same as AI.GENERATE_TEXT.

**BigFrames API:** No direct `ML.GENERATE_TEXT` wrapper. BigFrames routes through `AI.GENERATE_TEXT` instead. Use `bbq.ai.generate_text()` or `GeminiTextGenerator`/`Claude3TextGenerator` classes (which generate `AI.GENERATE_TEXT` SQL under the hood).

---
## Managed Functions

These are higher-level "managed" AI functions that provide **simplified interfaces** and **automatic prompt optimization** for common tasks. Unlike the general-purpose functions, these functions automatically structure your prompts to improve output quality and return simple scalar values rather than full model response structs.

**Key characteristics:**
- All are **scalar functions** returning simple types (BOOL, FLOAT64, STRING/ARRAY\<STRING\>).
- All are in **Preview** status.
- All use **dynamic shared quota (DSQ)** only -- no Provisioned Throughput support.
- BigQuery **automatically chooses** the model if no endpoint is specified (optimizing for cost-to-quality tradeoff).
- Return `NULL` on error (no detailed status or full_response fields).
- Cannot control model parameters (temperature, top_p, etc.) -- unlike their general-purpose counterparts.

**Relationships to general-purpose functions:**
- `AI.IF` relates to `AI.GENERATE_BOOL` -- AI.IF has prompt optimization and simpler output; AI.GENERATE_BOOL provides more control and detailed output.
- `AI.SCORE` relates to `AI.GENERATE_DOUBLE` -- AI.SCORE automatically generates a scoring rubric; AI.GENERATE_DOUBLE provides more control and detailed output.
- `AI.CLASSIFY` has no direct general-purpose counterpart but can be approximated with AI.GENERATE using output_schema.

| Feature | AI.IF | AI.SCORE | AI.CLASSIFY |
|---------|-------|----------|-------------|
| **Return Type** | BOOL | FLOAT64 | STRING or ARRAY\<STRING\> |
| **Purpose** | Evaluate natural language condition | Rate/score inputs on a scale | Classify into user-defined categories |
| **Unique Input** | `PROMPT` only | `PROMPT` only | `INPUT` + `CATEGORIES` + optional `OUTPUT_MODE` |
| **Prompt Optimization** | Yes (auto-structures prompts) | Yes (auto-generates scoring rubric) | Yes (auto-structures for classification) |
| **Model Parameter Control** | No | No | No |
| **Multimodal Support** | Yes (STRUCT prompt) | Yes (STRUCT prompt) | Yes (STRUCT prompt) |
| **Error Return** | NULL | NULL | NULL |
| **Provisioned Throughput** | Not supported (DSQ only) | Not supported (DSQ only) | Not supported (DSQ only) |
| **Rows per Job** | 10,000,000 | 10,000,000 | 10,000,000 |

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
  [, connection_id => 'CONNECTION' ]
  [, endpoint => 'ENDPOINT' ]
)
```

**Inputs:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `PROMPT` | STRING or STRUCT | Required (must be first argument) | The prompt value to send to the model. STRING or STRUCT with STRING/ARRAY\<STRING\>/ObjectRefRuntime/ARRAY\<ObjectRefRuntime\> fields. At most one video object. |
| `CONNECTION` | STRING | Optional | Connection to use, format: `[PROJECT_ID].LOCATION.CONNECTION_ID`. If not specified, end-user credentials are used. |
| `ENDPOINT` | STRING | Optional | Vertex AI endpoint. Any GA or preview Gemini model. If not specified, BigQuery ML dynamically chooses a model for best cost-to-quality tradeoff. |

**Outputs:**

| Return Type | Description |
|-------------|-------------|
| BOOL | The result of evaluating the condition in the input prompt. |
| NULL | Returned if the call to Vertex AI is unsuccessful for any reason. |

**Supported models:** Any GA or preview Gemini model. If no endpoint specified, BigQuery dynamically chooses for best cost-to-quality tradeoff. Uses various `gemini-2.5-*` models.

**Best practices:**
- BigQuery optimizes queries to reduce Gemini calls. Place non-AI filters alongside AI.IF -- non-AI filters are evaluated first (e.g., `WHERE AI.IF(...) AND category = 'tech'`).
- Do not use the global endpoint if you have data processing location requirements.

**Limitations:** Preview status. Returns NULL on error (no detailed error info). No model parameter control (unlike AI.GENERATE_BOOL). At most one video object per input.

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
)
```

**Inputs:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `PROMPT` | STRING or STRUCT | Required (must be first argument) | The prompt describing the scoring criteria. STRING or STRUCT with STRING/ARRAY\<STRING\>/ObjectRefRuntime/ARRAY\<ObjectRefRuntime\> fields. At most one video object. |
| `CONNECTION` | STRING | Optional | Connection to use, format: `[PROJECT_ID].LOCATION.CONNECTION_ID`. |
| `ENDPOINT` | STRING | Optional | Vertex AI endpoint. If not specified, BigQuery dynamically chooses a model. |

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
  [, connection_id => 'CONNECTION' ]
  [, endpoint => 'ENDPOINT' ]
  [, output_mode => 'OUTPUT_MODE' ]
)
```

**Inputs:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `INPUT` | STRING or STRUCT | Required (must be first argument) | The input to classify. STRING or STRUCT with STRING/ARRAY\<STRING\>/ObjectRefRuntime/ARRAY\<ObjectRefRuntime\> fields. At most one video object. |
| `CATEGORIES` | ARRAY\<STRING\> or ARRAY\<STRUCT\<STRING, STRING\>\> | Required (must be second argument) | The categories to classify into. Without descriptions: `['positive', 'neutral', 'negative']`. With descriptions: `[('green', 'positive'), ('yellow', 'neutral'), ('red', 'negative')]`. Must be string literals (or use a DECLARE variable from a table column). |
| `CONNECTION` | STRING | Optional | Connection to use, format: `[PROJECT_ID].LOCATION.CONNECTION_ID`. |
| `ENDPOINT` | STRING | Optional | Vertex AI endpoint. If not specified, BigQuery dynamically chooses a model. |
| `OUTPUT_MODE` | STRING | Optional | `'single'` or `'multi'`. Changes return type to ARRAY\<STRING\>. |

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

**Limitations:** Preview status. Returns NULL on error. Categories must be string literals in the array (unless using a variable). No model parameter control.

**Locations:** All regions supporting Gemini models, plus US and EU multi-regions.

**Provisioned throughput:** Not supported. Uses dynamic shared quota (DSQ) only.

**BigFrames API:** `bigframes.bigquery.ai.classify(input, categories)` — Returns a Series of STRING directly (not a struct). Takes `categories` as a list/tuple. Example: `bbq.ai.classify(df["text"], ["positive", "negative", "neutral"])`.

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

| Feature | AI.EMBED | AI.GENERATE_EMBEDDING | ML.GENERATE_EMBEDDING | AI.SIMILARITY | VECTOR_SEARCH | AI.SEARCH |
|---------|----------|----------------------|----------------------|---------------|---------------|-----------|
| **Type** | Scalar | TVF | TVF | Scalar | TVF | TVF |
| **Status** | Preview | GA (some Preview) | GA (some Preview) | Preview | GA (single search Preview) | Preview |
| **Requires Model Object** | No (endpoint param) | Yes (MODEL reference) | Yes (MODEL reference) | No (endpoint param) | No | No (uses table config) |
| **Input Data** | Single value | Table/Query | Table/Query | Two values | Table/Query + Table/Query or single value | Table/Query + string literal |
| **Output** | STRUCT(result, status) | Table with embedding + stats | Table with ml_generate_embedding_* cols | FLOAT64 | Table with query/base/distance | Table with base/distance |
| **Supports Images/Video** | Yes (multimodal) | Yes (multimodal, object tables) | Yes (multimodal, object tables) | Yes (multimodal) | No (pre-computed only) | No (text only) |
| **Supports PCA/Autoencoder/MF** | No | Yes | Yes | No | No | No |
| **Uses Vector Index** | No | No | No | No | Yes | Yes |
| **Requires Autonomous Embedding** | No | No | No | No | Optional (for STRING cols) | Yes (required) |

---

### `AI.EMBED`
- **Description:** (Preview) Scalar function that creates embeddings from text or image data. Sends a request to a stable Vertex AI embedding model and returns the model's response. No pre-created model object required.
- **Use cases:** Semantic search, recommendation, classification, clustering, outlier detection.
- [documentation](https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-embed)
- **Type:** Scalar function (returns a STRUCT value per row) -- Preview

**Syntax (text embedding):**
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
| `content` | STRING, ObjectRef, or ObjectRefRuntime | Required | The data to embed. For text: string literal, column name, or expression. For images: ObjectRef column, ObjectRef from OBJ.FETCH_METADATA + OBJ.MAKE_REF, or ObjectRefRuntime from OBJ.GET_ACCESS_URL. |
| `endpoint` | STRING | Required | Vertex AI embedding model endpoint. Must include model version (e.g., `text-embedding-005`, `multimodalembedding@001`). BigQuery auto-resolves full endpoint from model name. |
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

**Supported models:** Text: `text-embedding-005` (and other Vertex AI text embedding models; must include model version). Multimodal: `multimodalembedding@001` (default 1408 dimensions; configurable: 128, 256, 512, 1408 via `model_params => JSON '{"dimension": 256}'`).

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

> **Note:** The `statistics` column is only returned by text embedding models. Multimodal models (`multimodalembedding@001`) do not include it — queries that SELECT `statistics` from a multimodal embedding will error.

**Supported models:**

| Model | Output Dimensions | Max Sequence Length | Languages |
|-------|-------------------|---------------------|-----------|
| `gemini-embedding-001` | up to 3072 | 2048 tokens | Multilingual |
| `text-embedding-005` | up to 768 | 2048 tokens | English |
| `text-multilingual-embedding-002` | up to 768 | 2048 tokens | Multilingual |
| `multilingual-e5-small` (Preview) | up to 384 | 512 tokens | Multilingual |
| `multilingual-e5-large` (Preview) | up to 1024 | 512 tokens | Multilingual |
| `multimodalembedding@001` | 128, 256, 512, 1408 | -- | -- |

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

**Supported models / Limitations / Locations / Provisioned throughput:** Same as AI.GENERATE_EMBEDDING.

**BigFrames API:** No direct `ML.GENERATE_EMBEDDING` wrapper. BigFrames routes through `AI.GENERATE_EMBEDDING` instead. Use `bbq.ai.generate_embedding()` or `TextEmbeddingGenerator`/`MultimodalEmbeddingGenerator` classes.

---

### `AI.SIMILARITY`
- **Description:** (Preview) Scalar function that computes the cosine similarity between two inputs (text or images). Creates embeddings for both inputs at runtime and computes the cosine similarity between them. Values closer to 1 indicate more similar inputs.
- **Use cases:** Semantic search without precomputed embeddings, recommendation, classification, prototyping similarity queries.
- [documentation](https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-similarity)
- **Type:** Scalar function (returns FLOAT64) -- Preview

**Syntax (text):**
```sql
AI.SIMILARITY(
  content1 => 'CONTENT1',
  content2 => 'CONTENT2',
  endpoint => 'ENDPOINT'
  [, model_params => MODEL_PARAMS]
  [, connection_id => 'CONNECTION_ID']
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
| `content1` | STRING, ObjectRef, or ObjectRefRuntime | Required | First value to compare. |
| `content2` | STRING, ObjectRef, or ObjectRefRuntime | Required | Second value to compare. |
| `endpoint` | STRING | Required | Vertex AI embedding model endpoint (e.g., `text-embedding-005`, `multimodalembedding@001`). |
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

**Supported models:** Text: `text-embedding-005`. Multimodal: `multimodalembedding@001`.

**Best practices:**
- Use for small comparisons and prototyping. Use VECTOR_SEARCH for large-scale searches.
- Supports **cross-modal** comparisons: `content1` can be text while `content2` is an image (or vice versa) when using `multimodalembedding@001`. Text and image embeddings share the same vector space, so text descriptions can be matched against document images.
- `multimodalembedding@001` supports images only (JPEG, PNG, BMP, GIF) — **not PDFs**. Render PDFs to images first.

**Limitations:** Incurs charges for two embedding generations per call. For multimodal, `connection_id` is required and the connection's service account needs `roles/aiplatform.user` and `roles/storage.objectViewer`.

**Locations:** All regions supporting Gemini models, plus US and EU multi-regions.

**Provisioned throughput:** Not specified in documentation.

**BigFrames API:** No direct equivalent. Use `%%bigquery` magics or `session.read_gbq_query()` to execute AI.SIMILARITY SQL from BigFrames.

---

### `VECTOR_SEARCH`
- **Description:** Table-valued function that searches embeddings to find the top-K closest embeddings from a base table to a given query embedding. Supports both batch searches (multiple query rows) and single searches (one embedding value). Can use vector indexes for approximate nearest neighbor (ANN) search.
- **Use cases:** Semantic search, recommendation systems, classification, clustering, retrieval augmented generation (RAG).
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

**Syntax (single search -- Preview):**
```sql
VECTOR_SEARCH(
  { TABLE base_table | (base_table_query) },
  column_to_search,
  query_value => single_query_value,
  [, top_k => top_k_value]
  [, distance_type => distance_type_value]
  [, options => options_value]
)
```

**Inputs:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `base_table` / `base_table_query` | Table/Query | Required | The table to search. Only SELECT, FROM, WHERE clauses allowed in query. Don't filter the embedding column. Can't use logical views. |
| `column_to_search` | STRING | Required | Base table column to search. Must be ARRAY\<FLOAT64\> or STRING (Preview, requires autonomous embedding generation). If indexed, BigQuery attempts to use it. |
| `query_table` / `query_table_query` | Table/Query | Required for batch | Query embeddings to find nearest neighbors for. |
| `query_column_to_search` | Named arg, STRING | Optional (batch only) | Column in query table containing embeddings. ARRAY\<FLOAT64\> or STRING. |
| `query_value` | Named arg, ARRAY\<FLOAT64\> or STRING | Required for single search | Single embedding or string to search for. |
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

**Supported models:** VECTOR_SEARCH does not directly reference models. Operates on pre-computed ARRAY\<FLOAT64\> embeddings or STRING columns with autonomous embedding generation. Embeddings can come from any source (AI.EMBED, AI.GENERATE_EMBEDDING, external).

**Best practices:** Use a vector index for large base tables. Use brute force for exact results. Use single search syntax for single queries (optimized performance).

**Limitations:** Row-level and column-level security policies apply. Project running the query must match the project containing the base table. Subqueries in base_table_query might interfere with index usage. Logical views cannot be used.

**Locations:** Not specified specifically -- operates wherever BigQuery tables exist.

**Provisioned throughput:** Not specified. When used with autonomous embedding generation on STRING columns, generative AI function limits apply.

**BigFrames API:** `bigframes.bigquery.vector_search(base_table, column_to_search, query)` — Takes base table as string, query as DataFrame/Series. Supports `distance_type`, `top_k`, `fraction_lists_to_search`, `use_brute_force`. Also `bigframes.bigquery.create_vector_index()` for creating vector indexes.

---

### `AI.SEARCH`
- **Description:** (Preview) Table-valued function for semantic search on tables that have autonomous embedding generation enabled. Embeds the search query at runtime and searches the specified table. Uses vector indexes when available.
- **Use cases:** Semantic search, recommendation, classification, clustering, outlier detection.
- [documentation](https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-search)
- **Type:** Table-valued function (TVF) -- Preview

**Syntax:**
```sql
AI.SEARCH(
  { TABLE base_table | base_table_query },
  column_to_search,
  query_value
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
| `top_k` | Named arg, INT64 | Optional | Default: 10. Negative = return all. |
| `distance_type` | Named arg, STRING | Optional | `EUCLIDEAN` (default), `COSINE`, or `DOT_PRODUCT`. |
| `options` | Named arg, JSON STRING | Optional | `fraction_lists_to_search`, `use_brute_force`. |

**Outputs:**

| Column | Type | Description |
|--------|------|-------------|
| `base` | STRUCT | All columns from base_table |
| `distance` | FLOAT64 | Distance between query_value embedding and base embedding |

**Supported models:** Uses whatever embedding model and connection are configured for the base table's autonomous embedding generation.

**AI.SEARCH vs VECTOR_SEARCH:** Use AI.SEARCH for simplified semantic search when the base table has autonomous embedding generation and you want to search for a single string literal. Use VECTOR_SEARCH for batch queries, custom embeddings, or tables without autonomous embedding generation.

**Best practices:** Create a vector index on the embedding column for better performance on large tables.

**Limitations:** Base table must have autonomous embedding generation enabled. If embedding generation fails for query_value, the entire query fails. Rows with missing embeddings are skipped.

**Locations:** All locations supporting Vertex AI embedding models, plus US and EU multi-regions.

**Provisioned throughput:** Not specified in documentation.

**BigFrames API:** No direct equivalent. Use `%%bigquery` magics or `session.read_gbq_query()` to execute AI.SEARCH SQL from BigFrames.

---

## Forecasting

These functions perform time series forecasting, anomaly detection, and forecast evaluation using BigQuery ML's built-in TimesFM models. They do not require creating or managing separate model objects -- the TimesFM model is built in. All three functions share a common parameter pattern (`data_col`, `timestamp_col`, `id_cols`) and support the same model versions.

**Key relationships:**
- `AI.FORECAST` generates future time series values from historical data.
- `AI.DETECT_ANOMALIES` compares target data against a forecast baseline from historical data to identify anomalous points.
- `AI.EVALUATE` computes standard forecasting metrics (MAE, MSE, RMSE, MAPE, sMAPE) by comparing a forecast against actual observed values.

| Attribute | AI.FORECAST | AI.DETECT_ANOMALIES | AI.EVALUATE |
|-----------|-------------|---------------------|-------------|
| **Status** | GA | Preview | GA |
| **Purpose** | Forecast future values | Detect anomalies | Evaluate forecast accuracy |
| **Input data sources** | 1 (history) | 2 (history + target) | 2 (history + actuals) |
| **Supported Models** | TimesFM 2.0 (default), TimesFM 2.5 | TimesFM 2.0 (default), TimesFM 2.5 | TimesFM 2.0 (default), TimesFM 2.5 |
| **Default Horizon** | 10 | N/A | 1024 |
| **Min Data Points** | 3 | 3 | 3 |
| **Max Data Points** | 2,048 (2.0) / 15,360 (2.5) | 1,024 (most recent) | Not specified |

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
  [, horizon => HORIZON]
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
| `model` | STRING | Optional | `'TimesFM 2.0'` | -- | `'TimesFM 2.0'` or `'TimesFM 2.5'` |
| `id_cols` | ARRAY\<STRING\> | Optional | -- | -- | ID columns identifying unique time series. Must be STRING, INT64, ARRAY\<STRING\>, or ARRAY\<INT64\>. |
| `horizon` | INT64 | Optional | 10 | [1, 10000] | Number of time series data points to forecast |
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
| `ai_forecast_status` | STRING | Empty if successful; error string if unsuccessful |

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

**Supported models:** TimesFM 2.0 (default), TimesFM 2.5.

**Best practices:** Set `output_historical_time_series` to TRUE to compare historical values with forecasted values. Minimum 3 data points required.

**Limitations:** TimesFM 2.0 max context: 2,048 data points. TimesFM 2.5 max context: 15,360 data points. Additional data points beyond the max are ignored. Minimum 3 data points.

**Locations:** All supported BigQuery ML locations.

**Provisioned throughput:** Not specified. Billed at the evaluation, inspection, and prediction rate (BigQuery ML on-demand pricing).

**BigFrames API:** `bigframes.bigquery.ai.forecast(df, data_col=..., timestamp_col=...)` — Wraps `AI.FORECAST` SQL directly. No model object needed. Supports `id_cols`, `horizon`, `confidence_level`, `context_window`, and `model` parameters. Note: `bigframes.ml.forecasting.ARIMAPlus` is a different model (ARIMA_PLUS, not TimesFM).

---

### `AI.DETECT_ANOMALIES`
- **Description:** (Preview) Table-valued function that detects anomalies in time series data using BigQuery ML's built-in TimesFM model. Forecasts expected values from historical data, then compares target data against those forecasts to identify anomalous data points.
- **Use cases:** Detecting anomalous spikes or drops in time series (e.g., sales, bike trips), detecting anomalies across multiple time series simultaneously, computing anomaly probability.
- [documentation](https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-detect-anomalies)
- **Type:** Table-valued function -- Preview

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
)
```

**Inputs:**

| Parameter | Type | Required | Default | Range | Description |
|-----------|------|----------|---------|-------|-------------|
| `HISTORY_TABLE` / `HISTORY_QUERY_STATEMENT` | Table/Query | Required | -- | -- | Historical data used to generate a forecast baseline |
| `TARGET_TABLE` / `TARGET_QUERY_STATEMENT` | Table/Query | Required | -- | -- | Data in which to detect anomalies. Schema must match historical data. |
| `data_col` | STRING | Required | -- | -- | Data column name. Must be INT64, NUMERIC, BIGNUMERIC, or FLOAT64. |
| `timestamp_col` | STRING | Required | -- | -- | Timestamp column name. Must be TIMESTAMP, DATE, or DATETIME. |
| `model` | STRING | Optional | `'TimesFM 2.0'` | -- | `'TimesFM 2.0'` or `'TimesFM 2.5'` |
| `id_cols` | ARRAY\<STRING\> | Optional | -- | -- | ID columns identifying unique time series |
| `anomaly_prob_threshold` | FLOAT64 | Optional | 0.95 | [0, 1) | Threshold for anomaly detection. A target value is anomalous if its anomaly probability exceeds this threshold. |

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
| `ai_detect_anomalies_status` | STRING | Empty if successful; error string if unsuccessful |

**Supported models:** TimesFM 2.0 (default), TimesFM 2.5.

**Best practices:** Historical and target data schemas must match. Use `id_cols` to break anomalies down by dimensions.

**Limitations:** Only the most recent 1,024 time points are evaluated. Minimum 3 data points required. Preview status.

**Locations:** All supported BigQuery ML locations.

**Provisioned throughput:** Not specified. Billed at the evaluation, inspection, and prediction rate.

**BigFrames API:** No direct equivalent for TimesFM-based anomaly detection. Use `%%bigquery` magics or `session.read_gbq_query()` to execute AI.DETECT_ANOMALIES SQL from BigFrames. Note: `bigframes.ml.forecasting.ARIMAPlus.detect_anomalies()` exists but uses ARIMA_PLUS, not TimesFM.

---

### `AI.EVALUATE`
- **Description:** Table-valued function that evaluates TimesFM forecasted data against actual observed values. Generates a forecast from historical data and computes evaluation metrics (MAE, MSE, RMSE, MAPE, sMAPE).
- **Use cases:** Evaluating forecast accuracy, benchmarking model configurations, comparing forecast quality across multiple time series.
- [documentation](https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-evaluate)
- **Type:** Table-valued function

**Syntax:**
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
)
```

**Inputs:**

| Parameter | Type | Required | Default | Range | Description |
|-----------|------|----------|---------|-------|-------------|
| `HISTORY_TABLE` / `HISTORY_QUERY_STATEMENT` | Table/Query | Required | -- | -- | Historical time series data used to generate a forecast |
| `ACTUAL_TABLE` / `ACTUAL_QUERY_STATEMENT` | Table/Query | Required | -- | -- | Actual time series data to evaluate the forecast against |
| `data_col` | STRING | Required | -- | -- | Data column name. Must be INT64, NUMERIC, BIGNUMERIC, or FLOAT64. |
| `timestamp_col` | STRING | Required | -- | -- | Timestamp column name. Must be TIMESTAMP, DATE, or DATETIME. |
| `model` | STRING | Optional | `'TimesFM 2.0'` | -- | `'TimesFM 2.0'` or `'TimesFM 2.5'` |
| `id_cols` | ARRAY\<STRING\> | Optional | -- | -- | ID columns identifying unique time series |
| `horizon` | INT64 | Optional | 1024 | [1, 10000] | Number of forecasted time points to evaluate |

**Outputs:**

| Column | Type | Description |
|--------|------|-------------|
| *id_cols* | (inherited) | Time series identifiers |
| `mean_absolute_error` | FLOAT64 | MAE for the time series |
| `mean_squared_error` | FLOAT64 | MSE for the time series |
| `root_mean_squared_error` | FLOAT64 | RMSE for the time series |
| `mean_absolute_percentage_error` | FLOAT64 | MAPE for the time series |
| `symmetric_mean_absolute_percentage_error` | FLOAT64 | sMAPE for the time series |
| `ai_evaluate_status` | STRING | Empty if successful; error string if unsuccessful |

**Supported models:** TimesFM 2.0 (default), TimesFM 2.5.

**Best practices:** Split data into historical (for forecasting) and actual (for comparison) portions using date-based filtering. Use `id_cols` to evaluate across multiple time series.

**Limitations:** Minimum 3 data points required. Default horizon is 1,024 (unlike AI.FORECAST which defaults to 10).

**Locations:** All supported BigQuery ML locations.

**Provisioned throughput:** Not specified. Billed at the evaluation, inspection, and prediction rate.

**BigFrames API:** No direct equivalent for TimesFM-based evaluation. Use `%%bigquery` magics or `session.read_gbq_query()` to execute AI.EVALUATE SQL from BigFrames. Note: `bigframes.ml.forecasting.ARIMAPlus.evaluate()` exists but uses ARIMA_PLUS, not TimesFM.

---
## Document Processing

These functions process unstructured documents (PDFs, images, forms, invoices) using Document AI processors, returning structured extraction results directly as BigQuery columns.

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
- Maximum **100 pages per document**. Rows with larger documents return an error.
- Custom Splitter only supports PDF, TIFF, TIF, and GIF.
- Quotas: 600 requests/min (for ~50 page docs), 100,000 rows/job, max 5 concurrent jobs/project.
- Some rows may show `RESOURCE EXHAUSTED` errors after job success — BigQuery retries internally, but parallel batch queries can exceed quota limits.

**Locations:** Models can only be created in the **US** and **EU** multi-regions. The dataset, connection, and Document AI processor must all be in the same region.

**Provisioned throughput:** Not specified. Subject to Document AI API quotas.

**BigFrames API:** No direct equivalent. Use `%%bigquery` magics or `session.read_gbq_query()` to execute ML.PROCESS_DOCUMENT SQL from BigFrames.

---
## Unstructured Data Infrastructure

These are not AI functions themselves, but the infrastructure that enables AI functions to work with unstructured data (images, PDFs, audio, video) stored in Cloud Storage. **Object tables** provide metadata-indexed access to Cloud Storage objects, and **ObjectRef functions** create and manage typed references to those objects for use in AI function prompts.

**Key relationships:**
- **Object tables** are read-only external tables over Cloud Storage objects with metadata columns (`uri`, `content_type`, `size`, etc.) and an optional `ref` column containing `ObjectRef` values.
- `OBJ.MAKE_REF` creates `ObjectRef` values from URI strings — the entry point for referencing Cloud Storage objects.
- `OBJ.FETCH_METADATA` enriches partial `ObjectRef` values with Cloud Storage metadata (content type, size, MD5 hash).
- `OBJ.GET_ACCESS_URL` converts `ObjectRef` into `ObjectRefRuntime` with signed URLs — the format accepted by AI functions like `AI.GENERATE`.
- **Typical pipeline:** URI → `OBJ.MAKE_REF` → `OBJ.FETCH_METADATA` → `OBJ.GET_ACCESS_URL` → `AI.GENERATE`/`AI.GENERATE_TEXT`/etc.

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
| Not supported | VECTOR_SEARCH, AI.SEARCH, AI.FORECAST, AI.DETECT_ANOMALIES, AI.EVALUATE | — | Text/numeric input only |
