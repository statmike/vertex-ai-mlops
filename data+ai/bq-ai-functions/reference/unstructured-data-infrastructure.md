![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2Fdata%2Bai%2Fbq-ai-functions%2Freference&file=unstructured-data-infrastructure.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/data%2Bai/bq-ai-functions/reference/unstructured-data-infrastructure.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-ai-functions/reference/unstructured-data-infrastructure.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-ai-functions/reference/unstructured-data-infrastructure.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-ai-functions/reference/unstructured-data-infrastructure.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-ai-functions/reference/unstructured-data-infrastructure.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
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
    <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/data%2Bai/bq-ai-functions/reference/unstructured-data-infrastructure.md"><img src="https://www.svgrepo.com/download/5445/download-button.svg" alt="Download icon" width="20px"></a> <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/data%2Bai/bq-ai-functions/reference/unstructured-data-infrastructure.md">Download File</a> <i>(right-click and "Save As")</i>
  </td>
</tr>
</table><br/><br/>

---
# Unstructured Data Infrastructure

> Part of the [BigQuery AI Functions Resources](../RESOURCES.md) · [Project README](../README.md)

These are not AI functions themselves, but the infrastructure that enables AI functions to work with unstructured data (images, PDFs, audio, video) stored in Cloud Storage. **Object tables** provide metadata-indexed access to Cloud Storage objects, and **ObjectRef functions** create and manage typed references to those objects for use in AI function prompts.

**Key relationships:**
- **Object tables** are read-only external tables over Cloud Storage objects with metadata columns (`uri`, `content_type`, `size`, etc.) and an optional `ref` column containing `ObjectRef` values.
- `OBJ.MAKE_REF` creates `ObjectRef` values from URI strings — the entry point for referencing Cloud Storage objects.
- `OBJ.FETCH_METADATA` enriches partial `ObjectRef` values with Cloud Storage metadata (content type, size, MD5 hash).
- `OBJ.GET_ACCESS_URL` converts `ObjectRef` into `ObjectRefRuntime` with signed URLs — the format accepted by AI functions like `AI.GENERATE`.
- **For AI.PARSE_DOCUMENT:** Only `OBJ.MAKE_REF` is needed — alias it as `ref` in the subquery. No `OBJ.FETCH_METADATA` or `OBJ.GET_ACCESS_URL` required.
- **Typical pipeline (Gemini functions):** URI → `OBJ.MAKE_REF` → `OBJ.FETCH_METADATA` → `OBJ.GET_ACCESS_URL` → `AI.GENERATE`/`AI.GENERATE_TEXT`/etc.
- **Typical pipeline (AI.PARSE_DOCUMENT):** URI → `OBJ.MAKE_REF` (as `ref` column) → `AI.PARSE_DOCUMENT`.

**OPEN -- can AI functions take an `ObjectRef` directly, without `OBJ.GET_ACCESS_URL`?** Google's release notes announced exactly that as GA on 2026-06-12, but the reference documentation has not caught up and the two now disagree:

| Source | What it says |
|--------|--------------|
| Release note, 2026-06-12 | AI functions accept `ObjectRef` values directly, "without calling the `OBJ.GET_ACCESS_URL` function" |
| Generative AI overview | You **must** use `OBJ.GET_ACCESS_URL` to convert `ObjectRef` to `ObjectRefRuntime` |
| `AI.GENERATE_BOOL` / `AI.GENERATE_INT` / `AI.GENERATE_DOUBLE` reference | Input is "`ObjectRefRuntime` values generated by the `OBJ.GET_ACCESS_URL` function" |
| `AI.SCORE` reference | The prompt struct needs "a reference to either a STRING column or an **`ObjectRef` column**" |
| `AI.IF` reference example | Passes `images.ref` straight into the prompt struct, **no wrapper** |

So the managed functions (`AI.SCORE`, `AI.IF`) document the direct form and the generative ones do not. Whether that is a real capability split or documentation lag is **not yet measured by this project** -- it is a tracked item in *Tracked upcoming enhancements* in [PLANS.md](../PLANS.md). Until it is measured, every notebook here keeps using `OBJ.GET_ACCESS_URL(col, 'r')`, which is the one form documented everywhere and works on every function.

**`OBJ.GET_READ_URL` is real but undocumented as a function.** It reached GA on 2026-03-31 per the release notes and appears in a tutorial snippet as `OBJ.GET_READ_URL(ref) AS signed_url` -- returning a signed URL for *display*, alongside an AI function still being fed `OBJ.GET_ACCESS_URL(ref, 'r')`. It is **not** listed on the ObjectRef functions reference page, which documents only `OBJ.MAKE_REF`, `OBJ.GET_ACCESS_URL`, and `OBJ.FETCH_METADATA`. Treat it as a display/debugging convenience, not part of the AI pipeline, until it is documented.

**Object tables vs inline ObjectRef:**
- **Object tables** with remote models (e.g., `AI.GENERATE_EMBEDDING` reading from an object table) require a BigQuery reservation. Best for large-scale processing where you have reservations configured.
- **Inline ObjectRef** queries (building the pipeline in a subquery: `OBJ.MAKE_REF` → `OBJ.FETCH_METADATA` → `OBJ.GET_ACCESS_URL`) do **not** require a reservation. Best for ad-hoc multimodal queries and prototyping. All embedding and similarity function notebooks in this project use inline ObjectRef.

---

## Object Tables
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

## `OBJ.MAKE_REF`
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

## `OBJ.FETCH_METADATA`
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

## `OBJ.GET_ACCESS_URL`
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

## ObjectRef and ObjectRefRuntime Schema Reference

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

## Multimodal Input Patterns by Function

Different AI functions accept multimodal input in different ways. Here are the four patterns, with examples for each.

### Pattern 1: STRUCT Prompt (most generation functions + AI.IF)

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

### Pattern 2: Object Table with Tuple Syntax (AI.SCORE)

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

### Pattern 3: Object Table with EXTERNAL_OBJECT_TRANSFORM (AI.CLASSIFY)

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

### Pattern 4: ObjectRef Content Parameter (Embedding functions)

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

### Pattern Summary

| Pattern | Functions | Object Table Required? | Input Method |
|---------|-----------|----------------------|--------------|
| STRUCT prompt | AI.GENERATE, AI.GENERATE_TEXT, AI.GENERATE_TABLE, AI.GENERATE_BOOL, AI.GENERATE_DOUBLE, AI.GENERATE_INT, ML.GENERATE_TEXT, AI.IF | No | `STRUCT(text AS prompt, [refs] AS object_ref_runtime)` |
| Tuple + object table | AI.SCORE | Yes | `('scoring text', OBJ.GET_ACCESS_URL(ref, 'r'))` |
| EXTERNAL_OBJECT_TRANSFORM | AI.CLASSIFY | Yes | `AI.CLASSIFY(docs.ref, categories)` via `EXTERNAL_OBJECT_TRANSFORM` |
| ObjectRef content | AI.EMBED, AI.SIMILARITY, AI.GENERATE_EMBEDDING, ML.GENERATE_EMBEDDING | No (but supported) | Pass ObjectRefRuntime as the `content` parameter |
| Object table (document processing) | ML.PROCESS_DOCUMENT | Yes | Object table rows as input to Document AI processor |
| Not supported | VECTOR_SEARCH, AI.SEARCH, AI.FORECAST, AI.DETECT_ANOMALIES, AI.PREDICT, AI.EVALUATE | — | Text/numeric input only |
