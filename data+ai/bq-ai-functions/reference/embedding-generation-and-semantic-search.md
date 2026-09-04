![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2Fdata%2Bai%2Fbq-ai-functions%2Freference&file=embedding-generation-and-semantic-search.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/data%2Bai/bq-ai-functions/reference/embedding-generation-and-semantic-search.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-ai-functions/reference/embedding-generation-and-semantic-search.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-ai-functions/reference/embedding-generation-and-semantic-search.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-ai-functions/reference/embedding-generation-and-semantic-search.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-ai-functions/reference/embedding-generation-and-semantic-search.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
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
    <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/data%2Bai/bq-ai-functions/reference/embedding-generation-and-semantic-search.md"><img src="https://www.svgrepo.com/download/5445/download-button.svg" alt="Download icon" width="20px"></a> <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/data%2Bai/bq-ai-functions/reference/embedding-generation-and-semantic-search.md">Download File</a> <i>(right-click and "Save As")</i>
  </td>
</tr>
</table><br/><br/>

---
# Embedding Generation and Semantic Search

> Part of the [BigQuery AI Functions Resources](../RESOURCES.md) · [Project README](../README.md)

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

## `AI.EMBED`
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

## `AI.GENERATE_EMBEDDING`
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

## `ML.GENERATE_EMBEDDING`
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

## `AI.SIMILARITY`
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

## `VECTOR_SEARCH`
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

## `AI.SEARCH`
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

## Hybrid Search *(capability)*

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

**What is measured, and what is inferred.** `VECTOR_SEARCH` returns no rank column, so only one of the two ranks is ever read directly. `rank_vector` comes from a separate semantic-only run over the same rows; the lexical term is whatever remains after subtracting `1/(60 + rank_vector)` from `1 - distance`. What the arithmetic pins is therefore a set of *denominators*, not a pair of constants. Measured on a 30-row corpus, the semantic leg's top row contributes `1/61`, the lexical leg's top row contributes `1/62`, and the remaining lexical denominators run contiguously from there.

Two readings fit identically, because `1/(61 + rank_lexical)` and `1/(60 + (rank_lexical + 1))` are the same number:

| Reading | Semantic leg | Lexical leg |
|---|---|---|
| A -- two constants | k = 60, ranks `1..n` | k = 61, ranks `1..n` |
| B -- one constant, offset ranks | k = 60, ranks `1..n` | k = 60, ranks `2..n+1` |

Nothing observable from outside BigQuery separates them, but **B is the likelier**. k = 60 over 1-based ranks is the canonical RRF of Cormack, Clarke and Buettcher (2009) and the default wherever the constant is exposed -- Elasticsearch and OpenSearch both name it `rank_constant` and default it to 60, and Spanner and AlloyDB write 60 into their documented SQL. A constant of 61 appears in no published implementation. What is measured is that the semantic leg lands on the canonical `1/61` for its own top row -- so this document's rank convention already agrees with BigQuery's on one leg, and the extra `+1` sits on the lexical side specifically.

**Why the lexical leg would start at 2 is a separate question, and it is open.** Reading B says *where* the extra `+1` sits, not *why*. Three mechanisms fit the observations equally well:

- **A deliberate tie-break.** At equal ranks the vector term `1/(60 + r)` exceeds the lexical term `1/(61 + r)`, so the semantic leg wins every tie by a hair. That is what you would implement if hybrid should never reorder a tie against the embedding.
- **A reserved slot.** If position 1 of the lexical list holds something that is not a result -- the query itself, a sentinel, a header row -- then real rows begin at 2 naturally.
- **An off-by-one.** 61 is universal as the rank-1 *denominator*, `1/(60 + 1)`. Transcribing that as the constant, or applying `+1` to an already-1-based rank, produces exactly the observed `1/62` on a top row.

Only the third is a defect, and it is the least charitable of the three. Nothing observable from outside BigQuery distinguishes them, so do not present any one of them as the explanation.

One argument that looks decisive and is not: decoding with k = 60 on both legs yields lexical ranks `2 .. n+1`, and no n-row list hands out rank n+1. That rules out a shared base combined with ordinary 1-based lexical numbering. It does *not* rule out reading B, where `2 .. n+1` is precisely what an offset 1-based ranking looks like. A contiguous block starting at 2 is evidence *for* an offset, not against a shared constant.

The 60/61 form is used throughout this document because it is the shortest expression that reproduces every observed value. Read it as arithmetic that holds, not as two deliberate design decisions.

Three worked examples from that run, each matching a live returned value exactly:

| rank_vector | rank_lexical | Arithmetic | Returned `distance` |
|---|---|---|---|
| 1 | 3 | `1 - (1/61 + 1/64)` | `0.967981557377` |
| 2 | 1 | `1 - (1/62 + 1/62)` | `0.967741935484` |
| 9 | 2 | `1 - (1/69 + 1/63)` | `0.969634230504` |

The middle row is the one that trips people up: `1/62 + 1/62` is a value the measured arithmetic produces -- `1/(60 + 2)` and `1/(61 + 1)` happen to coincide at ranks (2, 1). It is also the `distance` on the `tiger` row of Google's published hybrid example, which decodes to exactly those ranks. Seeing two equal denominators is not evidence of a shared rank base: under either reading above, ranks (2, 1) produce `1/62` twice.

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
- **`PARTITION BY` must match the base table's partitioning expression exactly.** The clause does not let you pick an arbitrary partitioning for the index. On a table partitioned by `RANGE_BUCKET(id, GENERATE_ARRAY(0, 30000, 5000))`, repeating that same expression validates; naming any other column -- `PARTITION BY category` -- fails with `Invalid Partition By expression`, and so does `PARTITION BY category` against a table that is not partitioned at all.

**Index lifecycle: coverage, drift, and rebuild.** Creating an index is not managing one. Three signals describe an index's health and they move *independently* -- all measured 2026-09-03 against a live 7,275-row `TREE_AH` hybrid index:

| Signal | Where to read it | What it actually means |
|---|---|---|
| `coverage_percentage`, `unindexed_row_count` | `INFORMATION_SCHEMA.VECTOR_INDEXES` | how much of the base table the index currently covers |
| `tfdv_drift` | `VECTOR_INDEX.STATISTICS(TABLE t)` | how far the *vector distribution* has moved since the index was built |
| `last_model_build_time` | `INFORMATION_SCHEMA.VECTOR_INDEXES` | when the TreeAH model itself was last built -- distinct from `last_refresh_time` |

`VECTOR_INDEX.STATISTICS` takes **exactly one argument** and it must be a relation: `VECTOR_INDEX.STATISTICS(TABLE my_table)`. Adding the index name as a second argument fails with `Signature accepts at most 1 argument, found 2 arguments`; passing a string instead of `TABLE t` fails with `argument 1 must be a relation (i.e. table subquery)`. It returns a single column, `tfdv_drift`, which is `null` until the index's first refresh and `"0.0"` at fresh 100% coverage. On a table carrying **no** index it returns **zero rows** rather than an error, and scans 0 bytes -- so it is safe to call unconditionally.

**A negative `tfdv_drift` is a sentinel, not a magnitude.** Two freshly built indexes at 100% coverage reported different things: `"0.0"` from an unpartitioned hybrid index, and `-1.0` from a `PARTITION BY` index with no `lexical_search_columns`. Those two indexes differ in more than one way, so this does not isolate a cause -- partitioning, the absence of lexical columns, and how recently the first refresh completed are all still in play. Read a negative value as *no drift figure available for this index yet* and corroborate with `coverage_percentage` and `last_refresh_time` before acting on it. Partitioned indexes do populate normally otherwise: one on a 19,055-row / ~8.6 MB table reached 100% coverage about seven minutes after `CREATE`.

**Coverage and drift are not the same alarm.** Inserting 11,780 rows whose vectors duplicate ones already indexed (7,275 -> 19,055 rows) dropped `coverage_percentage` from 100 to 38 and set `unindexed_row_count` to 11,780 -- while `tfdv_drift` moved only from `0.0` to `1.97e-5` and `last_model_build_time` did not change at all (held across six 90-second polls). That is the point of having both numbers: a large volume of *new but distributionally identical* rows is a coverage problem, not a drift problem. Coverage recovers on the automatic refresh; drift is what argues for a rebuild.

**`ALTER VECTOR INDEX ... REBUILD` requires a BACKGROUND reservation.** With no reservation on the project the statement is rejected outright:

```
Cannot alter vector index on table my_table because there is no BACKGROUND reservation.
```

The same gate covers search indexes -- `ALTER SEARCH INDEX ... SET OPTIONS (...)` and `ALTER SEARCH INDEX ... ADD COLUMN` return the identical message with `search index` in place of `vector index`. **The check fires before validation, so these statements cannot even be dry-run**: `bq query --dry_run` on any of them returns the reservation error rather than `Query successfully validated`, and it does so even when the named index does not exist. That rules out the usual trick of parse-checking index-maintenance DDL for free. Index *maintenance* runs as background work, and background work needs slots assigned to it, so a project billed purely on demand has nowhere to run it. Exercising these statements requires an Enterprise-edition reservation carrying a `BACKGROUND` job-type assignment; an autoscale reservation with baseline 0 is the cheap shape, since it bills only while the rebuild actually runs. Creating an index, populating it, and querying through it all work with no reservation at all -- only the `ALTER` path is gated. Related: `last_index_alteration_info` stays `null` until an `ALTER` succeeds, and it is a `RECORD`, so `bq query --format=csv` refuses to print it (`Cannot print record field "last_index_alteration_info" in CSV format`) -- use `--format=prettyjson`.

**Search indexes have a 10 GiB floor -- three orders of magnitude above the vector index gates.** `CREATE SEARCH INDEX` *succeeds* on a small table, and then the index never populates. `INFORMATION_SCHEMA.SEARCH_INDEXES` reports `index_status` = `TEMPORARILY DISABLED`, `disable_time` equal to `creation_time`, `coverage_percentage` 0, and this `disable_reason`:

> The base table size is below the threshold of 10737418240 bytes for indexing. The index does not provide noticeable search performance gains when the base table is too small.

10,737,418,240 bytes is exactly 10 GiB -- against the vector index's 5,000-row hard reject and ~10 MB population gate. No teaching-scale table can carry a populated search index, which is why this project creates none and reaches for `lexical_search_columns` on a vector index instead. Note also that the `ddl` column of `SEARCH_INDEXES` is normalized rather than a verbatim echo of what you ran: a statement written with `OPTIONS (analyzer = 'LOG_ANALYZER')` is recorded as `OPTIONS (data_types = ['STRING'])`, with the analyzer surfaced in the separate `analyzer` column.

**Related:** [`VECTOR_SEARCH`](#vector_search) · [`AI.SEARCH`](#aisearch) · workflow [`catalog_search`](../workflows/catalog_search/)
