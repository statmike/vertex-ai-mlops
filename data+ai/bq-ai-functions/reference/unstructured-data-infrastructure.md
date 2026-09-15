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
- `OBJ.GET_ACCESS_URL` converts `ObjectRef` into `ObjectRefRuntime` with signed URLs — a tool for handing a URL to something outside the AI call, not a step on the way into one.
- `OBJ.GET_READ_URL` returns a 45-minute read URL as `STRUCT<url, status>`, for displaying an object in query results.
- **Typical pipeline:** URI → `OBJ.MAKE_REF` → any multimodal `AI.*` function. From an object table, the `ref` column replaces even the `OBJ.MAKE_REF` step.
- **`AI.PARSE_DOCUMENT` is stricter about the column name:** its subquery must alias the reference as `ref` specifically. (That function has been offline since 2026-06-01 with its reference docs withdrawn.)

**RESOLVED (2026-09-15) -- AI functions take an `ObjectRef` directly; `OBJ.GET_ACCESS_URL` is not required.** The 2026-06-12 release note said so, the reference pages disagreed, and this project kept the wrapper because it was the one form documented everywhere. Both halves of that disagreement have now closed:

| Evidence | Finding |
|----------|---------|
| Reference pages, re-read 2026-09-15 | **Eleven of the twelve** multimodal `AI.*` pages now document the input type as `ObjectRef` / `ARRAY<ObjectRef>`, with `OBJ.MAKE_REF('gs://my_image.jpg')` as the worked example. **`AI.AGG` is the twelfth and the sole holdout** — its `INPUT` row still says `ObjectRefRuntime`. |
| Measured live, 2026-09-15 | Wrapped and bare forms both return valid results for `AI.GENERATE`, `AI.GENERATE_BOOL`, `AI.GENERATE_INT`, `AI.GENERATE_DOUBLE`, `AI.GENERATE_TABLE`, `AI.IF`, `AI.SCORE`, `AI.CLASSIFY`, `AI.AGG`, `AI.EMBED`, and `AI.SIMILARITY` — eleven functions, including `AI.AGG`, whose page still specifies the wrapper. (`AI.GENERATE_EMBEDDING` is the twelfth page. It is a table-valued function, so it takes the reference as a `content` **column** in its input subquery rather than as `AI.EMBED`'s `content =>` named argument — the same `ObjectRef`, a different place to put it — and it was covered by its own notebook's re-run rather than by the matrix.) |
| `AI.CLASSIFY`, measured live | `EXTERNAL_OBJECT_TRANSFORM(TABLE t, ['SIGNED_URL'])` is not required either: the object table's bare `ref` column and the transformed one returned the same classifications over a 10-PDF table. |

Every notebook in this project now passes the `ObjectRef`. **Nothing was deprecated** — `ObjectRefRuntime` is still accepted everywhere, so existing queries keep working. See [Multimodal Input Patterns](#multimodal-input-patterns-by-function) for where the reference goes in each function's call.

**Object tables vs inline ObjectRef:**
- **Object tables** with remote models (e.g., `AI.GENERATE_EMBEDDING` reading from an object table) require a BigQuery reservation. Best for large-scale processing where you have reservations configured.
- **Inline ObjectRef** (`OBJ.MAKE_REF(uri, connection)` in a subquery) does **not** require a reservation. Best for ad-hoc multimodal queries and prototyping. All embedding and similarity function notebooks in this project use inline ObjectRef.
- **Inside a VPC Service Controls perimeter, inline is the only option that works.** An object table's `ref` column uses delegated access, which mints a signed HTTPS URL that Agent Platform blocks inside a perimeter. Single-argument `OBJ.MAKE_REF(uri)` uses direct access and sends the Cloud Storage URI itself. See the note under [`OBJ.MAKE_REF`](#objmake_ref).

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

> **The image-preprocessing family lives in the sibling project** — `ML.DECODE_IMAGE`, `ML.RESIZE_IMAGE`, `ML.CONVERT_COLOR_SPACE`, `ML.CONVERT_IMAGE_TYPE`, documented in [`bq-ml/reference/model-free-functions.md`](../../bq-ml/reference/model-free-functions.md#image-preprocessing-functions-mldecode_image-mlresize_image-mlconvert_image_type-mlconvert_color_space) with a tested example in [`bq-ml/functions/image/`](../../bq-ml/functions/image/). Two things carry over to any object-table work here: those four functions **require a BigQuery Editions reservation** and fail outright on on-demand pricing (verified live 2026-09-11; no official page says so), and `ML.DECODE_IMAGE` accepts **any** `BYTES` value, so the `data` pseudocolumn is the usual source rather than the only one.

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

`EXTERNAL_OBJECT_TRANSFORM` also rewrites the table's `ref` column from an `ObjectRef` into a signed `ObjectRefRuntime`. **No AI function requires that rewrite** — they all take the `ObjectRef` directly. Use the transform when something outside the AI call needs a fetchable URL: a display link, delegated access for another consumer, a shorter-lived credential.

**Connection requirements:**
- Requires a **Cloud resource connection** (type: "Vertex AI remote models, remote functions, BigLake and Spanner").
- Connection's service account needs `roles/storage.objectViewer` on the Cloud Storage bucket.
- Connection must be in the same region as the dataset.

**AI function integration:** every one of these reads the `ref` column as-is — an `ObjectRef` — with no signing step in between.
- `ML.PROCESS_DOCUMENT` — document extraction via Document AI processors.
- `AI.GENERATE_TEXT` / `AI.GENERATE` — text generation from object data: `STRUCT(text AS prompt, [ref] AS object_refs)`.
- `AI.GENERATE_EMBEDDING` — embeddings from image/video data: a `content` column of `ObjectRef`.
- `AI.SCORE` — score documents using tuple syntax: `AI.SCORE(('text', ref))`.
- `AI.CLASSIFY` — classify documents: `AI.CLASSIFY(ref, categories)`.
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

**Syntax (URI, optional authorizer):**
```sql
OBJ.MAKE_REF(
  uri
  [, authorizer]
  [, version => version_value]
  [, details => gcs_metadata_json]
)
```

**Syntax (JSON input):**
```sql
OBJ.MAKE_REF(
  objectref_json
)
```

**Syntax (re-authorize an existing ObjectRef):**
```sql
OBJ.MAKE_REF(
  objectref,
  authorizer
)
```
The top-level `authorizer` overwrites whatever the input `objectref` carried.

**Inputs:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `uri` | STRING | Required (overload 1) | Cloud Storage URI, e.g., `gs://mybucket/file.jpg`. Can be a column reference. |
| `authorizer` | STRING | Optional (overload 1) | Cloud resource connection, e.g., `us.myconnection`, used for **delegated access**. Must be in the same project and region as the query. Omit it and the ObjectRef uses **direct access** instead. |
| `version_value` | STRING | Optional | Cloud Storage object version. |
| `gcs_metadata_json` | JSON | Optional | Pre-supplied metadata: `{"content_type", "md5_hash", "size", "updated"}`. Fills `details` without a Cloud Storage round-trip. |
| `objectref_json` | JSON | Required (overload 2) | JSON with schema `{"uri": "string", "authorizer": "string"}`. No validation performed. |

**Outputs:** Returns `STRUCT<uri STRING, version STRING, authorizer STRING, details JSON>`. Only `uri` and `authorizer` are populated unless you supply `version` / `details`; otherwise use `OBJ.FETCH_METADATA` to fill them.

> **Dropping the authorizer changes who reads the object, not whether it works.** `OBJ.MAKE_REF('gs://bucket/file.pdf')` is legal and succeeds against private buckets — but only because the identity running the query holds `storage.objectViewer` on that bucket. That is **direct access**: the object is fetched as the query runner. Passing the connection gives **delegated access**, where the object is fetched as the connection's service account and the grant is auditable and independent of whoever runs the query. The examples throughout this project pass the connection for that reason.
>
> **Inside a VPC Service Controls perimeter the recommendation inverts.** Delegated access mints a signed HTTPS URL, and Agent Platform blocks HTTP/HTTPS fetches for projects inside a perimeter — so a delegated-access `ObjectRef`, **including an object table's `ref` column**, fails with `INVALID_ARGUMENT: HTTP links are not supported for requests restricted by VPCSC.` in the output's `status` field. In that environment use the single-argument `OBJ.MAKE_REF(uri)`: direct access sends the Cloud Storage URI to the model with no signed URL in between. This is also a reason to prefer inline `OBJ.MAKE_REF` over object tables inside a perimeter — an object table has no direct-access form.

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

OBJ.FETCH_METADATA(
  ARRAY<objectref>
)
```
The array overload fetches metadata for a whole `ARRAY<ObjectRef>` column in one call.

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
- **Description:** (Preview) Scalar function that converts an `ObjectRef` into an `ObjectRefRuntime` JSON value containing signed access URLs, with a caller-chosen mode (`'r'` / `'rw'`) and TTL.
- **Use cases:** Generate a **writable** signed URL for saving transformation outputs back to Cloud Storage, hand a read URL to a consumer outside BigQuery, pin an explicit expiry shorter than the 6-hour default.
- **Not needed to call an AI function.** Every multimodal `AI.*` function takes an `ObjectRef` directly; wrapping the reference in `OBJ.GET_ACCESS_URL` buys nothing but a longer query. See [Multimodal Input Patterns](#multimodal-input-patterns-by-function).
- [documentation](https://cloud.google.com/bigquery/docs/reference/standard-sql/objectref_functions)
- **Type:** Scalar function (returns ObjectRefRuntime JSON) — Preview

**Syntax:**
```sql
OBJ.GET_ACCESS_URL(
  objectref,
  mode
  [, duration]
)

OBJ.GET_ACCESS_URL(
  ARRAY<objectref>,
  mode
  [, duration]
)
```
The array overload signs a whole `ARRAY<ObjectRef>` column in one call.

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

**Accepted by AI functions:** yes — `ObjectRefRuntime` still works everywhere `ObjectRef` does, and `AI.AGG`'s reference page is the one that still specifies it. It is no longer the required form for any of them.

**Limitations:**
- Access URLs expire after at most 6 hours. Do not persist `ObjectRefRuntime` values long-term — regenerate from `ObjectRef` values.
- Same 20-connection limit per project+region.
- The `AI.AGG` page's Known Issues note that rows carrying arrays of `ObjectRefRuntime` values "might be skipped," and that some image objects created by `OBJ.GET_ACCESS_URL` "might fail to process." Passing the `ObjectRef` avoids both.

**Locations:** All BigQuery regions supporting Cloud resource connections.

---

## `OBJ.GET_READ_URL`
- **Description:** (Preview) Scalar function that returns a `STRUCT<url STRING, status STRING>` holding a read URL for a Cloud Storage object. The URL expires after **45 minutes**.
- **Use cases:** Render an object inline in BigQuery Studio query results — the `url` column displays the image rather than the link text. A shorter-lived, read-only alternative to `OBJ.GET_ACCESS_URL` when all you need is to look at the object.
- [documentation](https://cloud.google.com/bigquery/docs/reference/standard-sql/objectref_functions)
- **Type:** Scalar function (returns STRUCT) — Preview

**Syntax:**
```sql
OBJ.GET_READ_URL(objectref)
```

**Inputs:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `objectref` | ObjectRef STRUCT | Required | Must use **delegated access** — the ObjectRef has to carry an `authorizer`. A direct-access ObjectRef is rejected. |

**Outputs:** `STRUCT<url STRING, status STRING>`. On success `url` holds the read URL and `status` is `NULL`; on failure `url` is `NULL` and `status` holds the error message. Nothing raises — check `status`.

```sql
SELECT OBJ.GET_READ_URL(poster) AS read_url
FROM `mydataset.films`;
```

**How it differs from `OBJ.GET_ACCESS_URL`:**

| | `OBJ.GET_READ_URL` | `OBJ.GET_ACCESS_URL` |
|---|---|---|
| Returns | `STRUCT<url, status>` | `ObjectRefRuntime` JSON |
| Modes | Read only | `'r'` or `'rw'` |
| TTL | Fixed 45 minutes | 30 min – 6 hours, caller-set |
| Access | Delegated access required | Either |
| Errors | Reported in `status` | Reported in `runtime_errors` |

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

**Content requirements** (documented on `AI.GENERATE` and `AI.GENERATE_TEXT`, and applying wherever object references are accepted):
- Content must be in one of the formats the Gemini API's `mimeType` parameter supports.
- **At most one video object per input.** More than one is not rejected loudly — plan around the cap.
- Videos are truncated to **two minutes**; a longer video returns results based on its first two minutes only.

**Typical workflow:**
```
URI string
  → OBJ.MAKE_REF(uri, connection)     → ObjectRef
  → AI.GENERATE(STRUCT(prompt, ref))  → Generated output
```

**Shortcut from object tables:** when the `ref` column is available (preview allowlist), skip `OBJ.MAKE_REF` too — the column already *is* an `ObjectRef`.

**Where the other two functions fit.** `OBJ.FETCH_METADATA` and `OBJ.GET_ACCESS_URL` are no longer steps on the path to an AI call; they are tools you reach for on purpose:

| You want | Call |
|----------|------|
| Feed an object to an AI function | Nothing — pass the `ObjectRef` |
| `content_type`, `size`, `md5_hash`, `updated` in SQL | `OBJ.FETCH_METADATA(objectref)` |
| Display the object in query results | `OBJ.GET_READ_URL(objectref)` |
| Hand a URL to a consumer outside BigQuery | `OBJ.GET_ACCESS_URL(objectref, 'r')` |
| Write a transformation output back to GCS | `OBJ.GET_ACCESS_URL(objectref, 'rw')` |
| An expiry shorter than the 6-hour default | `OBJ.GET_ACCESS_URL(objectref, 'r', INTERVAL 30 MINUTE)` |

---

## Multimodal Input Patterns by Function

**Every multimodal AI function takes an `ObjectRef`.** What differs between them is only *where the reference goes in the call*: a field of a STRUCT prompt, the second slot of a tuple, a bare positional argument, or a named `content` parameter. There are four shapes, not four pipelines.

Where the `ObjectRef` comes from is an independent choice:

```sql
OBJ.MAKE_REF('gs://bucket/doc.pdf', 'PROJECT.REGION.CONNECTION')  -- inline, no table
ref                                                                -- object table column
```

### Shape 1: STRUCT Prompt (most generation functions + AI.IF)

Replace the STRING prompt with a STRUCT containing text and an array of `ObjectRef`. Works inline — no object table needed.

**Functions:** `AI.GENERATE`, `AI.GENERATE_TEXT`, `AI.GENERATE_TABLE`, `AI.GENERATE_BOOL`, `AI.GENERATE_DOUBLE`, `AI.GENERATE_INT`, `ML.GENERATE_TEXT`, `AI.IF`

```sql
-- Scalar function (AI.GENERATE)
SELECT (AI.GENERATE(
  STRUCT(
    'Summarize this document.' AS prompt,
    [OBJ.MAKE_REF('gs://bucket/doc.pdf', 'PROJECT.REGION.CONNECTION')] AS object_refs
  )
)).result;

-- TVF (AI.GENERATE_TEXT)
SELECT result
FROM AI.GENERATE_TEXT(
  MODEL `project.dataset.model`,
  (SELECT STRUCT(
    'Summarize this document.' AS prompt,
    [OBJ.MAKE_REF('gs://bucket/doc.pdf', 'PROJECT.REGION.CONNECTION')] AS object_refs
  ) AS prompt)
);

-- Managed function (AI.IF)
SELECT AI.IF(
  STRUCT(
    'This document is a financial invoice' AS prompt,
    [OBJ.MAKE_REF('gs://bucket/doc.pdf', 'PROJECT.REGION.CONNECTION')] AS object_refs
  )
) AS is_invoice;
```

> The STRUCT's field *names* are not part of the contract — the function concatenates the fields in the order given, the way `CONCAT` would. `object_refs` is this project's convention because it says what the field holds; `object_ref_runtime` or anything else behaves identically.

### Shape 2: Tuple Syntax (AI.SCORE)

`AI.SCORE` does not accept the STRUCT prompt. Pass a tuple of (scoring text, `ObjectRef`).

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
    ('Rate the professionalism of this document on a scale of 0 to 1', ref)
  ) AS professionalism
FROM `project.dataset.docs`;
```

### Shape 3: Direct Argument (AI.CLASSIFY, AI.AGG)

The reference is just an argument — no prompt STRUCT, no tuple. `AI.AGG` wraps it in a one-field `STRUCT` because that is how it takes any input.

**Functions:** `AI.CLASSIFY`, `AI.AGG`

```sql
-- Classify straight off the object table's ref column
SELECT
  uri,
  AI.CLASSIFY(ref, ['invoice', 'receipt', 'contract', 'letter']) AS doc_type
FROM `project.dataset.docs`;

-- AI.AGG wraps the reference in a one-field STRUCT
SELECT AI.AGG(
  STRUCT(ref),
  'Summarize the common themes across these documents.'
) AS themes
FROM `project.dataset.docs`;
```

`EXTERNAL_OBJECT_TRANSFORM(TABLE t, ['SIGNED_URL'])` is not required here — verified live 2026-09-15 against a 10-PDF object table, where the bare `ref` column and the transformed one returned the same classifications.

### Shape 4: `content` Parameter (Embedding and similarity functions)

Embedding and similarity functions take the reference as the content argument rather than in a prompt. Requires a multimodal embedding endpoint (e.g., `multimodalembedding@001`).

**Functions:** `AI.EMBED`, `AI.GENERATE_EMBEDDING`, `ML.GENERATE_EMBEDDING`, `AI.SIMILARITY`

```sql
-- AI.EMBED with inline ObjectRef
SELECT AI.EMBED(
  OBJ.MAKE_REF('gs://bucket/image.jpg', 'PROJECT.REGION.CONNECTION'),
  endpoint => 'multimodalembedding@001',
  connection_id => 'PROJECT.REGION.CONNECTION'
).result AS embedding;

-- AI.SIMILARITY with ObjectRef (returns a FLOAT64 directly, no .result accessor)
SELECT AI.SIMILARITY(
  OBJ.MAKE_REF('gs://bucket/img1.jpg', 'PROJECT.REGION.CONNECTION'),
  OBJ.MAKE_REF('gs://bucket/img2.jpg', 'PROJECT.REGION.CONNECTION'),
  endpoint => 'multimodalembedding@001',
  connection_id => 'PROJECT.REGION.CONNECTION'
) AS similarity;
```

### Shape Summary

| Shape | Functions | Object Table Required? | Input Method |
|-------|-----------|----------------------|--------------|
| STRUCT prompt | AI.GENERATE, AI.GENERATE_TEXT, AI.GENERATE_TABLE, AI.GENERATE_BOOL, AI.GENERATE_DOUBLE, AI.GENERATE_INT, ML.GENERATE_TEXT, AI.IF | No | `STRUCT(text AS prompt, [refs] AS object_refs)` |
| Tuple | AI.SCORE | No (object table is the convenient source) | `('scoring text', ref)` |
| Bare argument | AI.CLASSIFY, AI.AGG | No (object table is the convenient source) | `AI.CLASSIFY(ref, categories)`, `AI.AGG(STRUCT(ref), prompt)` |
| `content` parameter | AI.EMBED, AI.SIMILARITY, AI.GENERATE_EMBEDDING, ML.GENERATE_EMBEDDING | No | Pass the `ObjectRef` as the content argument |
| Object table (document processing) | ML.PROCESS_DOCUMENT | Yes | Object table rows as input to Document AI processor |
| Not supported | VECTOR_SEARCH, AI.SEARCH, AI.FORECAST, AI.DETECT_ANOMALIES, AI.PREDICT, AI.EVALUATE | — | Text/numeric input only |

> **`ObjectRefRuntime` still works everywhere.** Nothing in this section is a breaking change — wrapping a reference in `OBJ.GET_ACCESS_URL` is accepted by every function above. It is simply no longer necessary, and `AI.AGG`'s Known Issues give a reason to prefer the unwrapped form.
