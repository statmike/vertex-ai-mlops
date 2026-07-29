# Document Processing & Unstructured Data (Object Tables / ObjectRef) in BigQuery

## Options

| Capability | What it does | Use this when |
|---|---|---|
| `ML.PROCESS_DOCUMENT` | Table-valued function that sends documents from an object table to a Document AI processor (invoice, receipt, form, OCR, custom, and more) via a `REMOTE_SERVICE_TYPE = 'CLOUD_AI_DOCUMENT_V1'` remote model, returning structured extraction results as columns. | You need specialized document extraction (invoices, receipts, forms, tax/ID documents, custom classifiers/splitters) at scale, and can create a Document AI processor + remote model. |
| `AI.PARSE_DOCUMENT` | **CURRENTLY OFFLINE (as of 2026-06-01), taken down by Google for revision — does not execute.** When working, it's a Preview table-valued function that runs OCR + layout parsing + chunking against a Document AI Layout Parser processor with no `CREATE MODEL` step needed. | Do not recommend right now — it is non-functional. When it returns: for straightforward OCR + chunking workflows (e.g., feeding a RAG pipeline) without the overhead of creating a remote model. |
| Object Tables | Read-only external SQL tables over Cloud Storage objects (PDFs, images, audio, video), exposing metadata columns (`uri`, `content_type`, `size`, etc.) and an optional `ref` (ObjectRef) column. | You want to index/query a whole GCS prefix as rows and feed many objects into AI functions or `ML.PROCESS_DOCUMENT` at scale. |
| `OBJ.MAKE_REF` | Scalar function that builds a partial `ObjectRef` STRUCT (`uri` + `authorizer`) from a URI string and a connection — no object table required. | You need a one-off reference to a single (or small UNNEST list of) GCS file(s) without registering a whole Object Table. |
| `OBJ.FETCH_METADATA` | Scalar function that fills in the `details` field of a partial `ObjectRef` with GCS metadata (content type, size, MD5 hash, updated time). | You need actual object metadata (size, content-type, hash) attached to an ObjectRef, or need it before generating an access URL. |
| `OBJ.GET_ACCESS_URL` | Scalar function that converts an `ObjectRef` into `ObjectRefRuntime` JSON containing signed read/write URLs — the format AI functions actually consume. | You need to pass an image/PDF/audio/video object into `AI.GENERATE`, `AI.EMBED`, `AI.SIMILARITY`, etc., or need a temporary signed URL to a GCS object. |

## Choosing among them

- **"I need to extract structured fields from PDFs/scanned documents at scale"** → `ML.PROCESS_DOCUMENT`. (Note: `AI.PARSE_DOCUMENT` would normally be the lighter-weight alternative for Layout-Parser-only OCR+chunking, but it is currently unavailable — do not route users to it until the outage clears.)
- **"I need to pass images/PDFs/audio/video into `AI.GENERATE` or other generative functions"** → build an `ObjectRef`/`ObjectRefRuntime` via an Object Table (bulk) or `OBJ.MAKE_REF` (inline/ad hoc), then `OBJ.GET_ACCESS_URL`.
- **"I just need a one-off reference to a single GCS file without registering a whole Object Table"** → `OBJ.MAKE_REF`.
- **"I need metadata (size, content-type, etc.) about a GCS object"** → `OBJ.FETCH_METADATA`.
- **"I need a signed/temporary URL to a GCS object"** → `OBJ.GET_ACCESS_URL` (or `EXTERNAL_OBJECT_TRANSFORM(... ['SIGNED_URL'])` when working from an Object Table).

## Gotchas verified in this repo

- **`AI.PARSE_DOCUMENT` is offline as of 2026-06-01** — Google took the (Preview) function down for revision; it does not currently execute. The `functions/ai_parse_document/` notebook and `workflows/document_rag/` both carry warning banners and are blocked pending re-enablement. Precedent: `AI.AGG` was similarly disabled in April 2026 and re-enabled in May 2026 — re-check BigQuery release notes before assuming it's back.
- **`ML.PROCESS_DOCUMENT` requires `CREATE MODEL`; `AI.PARSE_DOCUMENT` does not** — the former needs a remote model with `REMOTE_SERVICE_TYPE = 'CLOUD_AI_DOCUMENT_V1'` pointing at a processor; the latter (when working) points its `endpoint` parameter directly at the Document AI processor resource path, skipping model creation entirely.
- **`AI.PARSE_DOCUMENT` only supports Layout Parser processors** — it cannot run invoice, receipt, form, or custom processors; those require `ML.PROCESS_DOCUMENT`.
- **ObjectRef vs ObjectRefRuntime are not interchangeable** — table columns and `OBJ.MAKE_REF`/`OBJ.FETCH_METADATA` outputs are `ObjectRef` (a STRUCT: `uri`, `version`, `authorizer`, `details` JSON). AI functions (`AI.GENERATE`, `AI.EMBED`, etc.) actually consume `ObjectRefRuntime` (JSON with `obj_ref` + `access_urls`), which only `OBJ.GET_ACCESS_URL` produces. Passing a bare `ObjectRef` where `ObjectRefRuntime` is expected will not work.
- **`OBJ.MAKE_REF` performs no validation** — the JSON-input overload accepts `{"uri": "...", "authorizer": "..."}` with no checking; typos surface only later, downstream (e.g., at `OBJ.FETCH_METADATA` or `OBJ.GET_ACCESS_URL`), as an `error`/`runtime_errors` field rather than a query-time failure.
- **`OBJ.FETCH_METADATA` and `OBJ.GET_ACCESS_URL` fail "softly"** — both still return a value on error rather than raising: `OBJ.FETCH_METADATA` puts `{"errors": {"OBJ.FETCH_METADATA": "..."}}` in `details`, and `OBJ.GET_ACCESS_URL` replaces `access_urls` with `runtime_errors`. Downstream code must check for these fields, not rely on query failure.
- **Signed URLs expire in at most 6 hours** — both `OBJ.GET_ACCESS_URL` and Object Table `EXTERNAL_OBJECT_TRANSFORM(... ['SIGNED_URL'])` cap validity at 6 hours (minimum 30 minutes). Never persist `ObjectRefRuntime` values long-term — regenerate from the underlying `ObjectRef` instead.
- **Object Table `ref` column is allowlist-gated** — the `ref` STRUCT column ("Preview") is only created if the project is on the multimodal data preview allowlist; otherwise the table only exposes `uri`, `content_type`, `size`, `md5_hash`, `updated`, `metadata` and you must build refs manually with `OBJ.MAKE_REF`.
- **Hard 20-connection cap** — `OBJ.MAKE_REF`, `OBJ.FETCH_METADATA`, and `OBJ.GET_ACCESS_URL` all share a limit of 20 distinct connections referenced per project+region in a query; the connection must also be in the same project/region as the query itself.
- **Object Tables require reservations for remote-model processing; inline ObjectRef pipelines don't** — reading an Object Table into a remote-model function (e.g., `AI.GENERATE_EMBEDDING` over an object table) needs a BigQuery reservation, whereas the inline `OBJ.MAKE_REF → OBJ.FETCH_METADATA → OBJ.GET_ACCESS_URL` pattern built in a subquery does not. This repo's embedding/similarity notebooks all use the inline pattern for that reason.
- **Not every AI function accepts multimodal input the same way** — there are four distinct wiring patterns (STRUCT prompt for `AI.GENERATE`/`AI.IF`/etc.; tuple syntax for `AI.SCORE`; `EXTERNAL_OBJECT_TRANSFORM` for `AI.CLASSIFY`; direct ObjectRef content param for embedding/similarity functions). `VECTOR_SEARCH`, `AI.SEARCH`, `AI.FORECAST`, `AI.DETECT_ANOMALIES`, and `AI.EVALUATE` accept **no** multimodal/ObjectRef input at all — text/numeric only.
- **`ML.PROCESS_DOCUMENT` hard limits**: max 130 pages per document (larger documents error per-row), 120-second timeout per request, requests batched in groups of 10, and models can only be created in **US**/**EU** multi-regions (dataset, connection, and processor must all match).

## Canonical snippet

```sql
-- Option A: Object Table (bulk) + AI.GENERATE via ObjectRefRuntime
CREATE EXTERNAL TABLE `myproject.mydataset.docs`
WITH CONNECTION `myproject.us.myconnection`
OPTIONS (
  object_metadata = 'SIMPLE',
  uris = ['gs://mybucket/documents/*.pdf']
);

SELECT
  uri,
  (AI.GENERATE(
    STRUCT(
      'Summarize this document in 3 bullet points.' AS prompt,
      [OBJ.GET_ACCESS_URL(ref, 'r')] AS object_ref_runtime  -- requires allowlisted `ref` column
    )
  )).result AS summary
FROM `myproject.mydataset.docs`;

-- Option B: single file, no Object Table needed (OBJ.MAKE_REF)
SELECT (AI.GENERATE(
  STRUCT(
    'Summarize this document in 3 bullet points.' AS prompt,
    [OBJ.GET_ACCESS_URL(
      OBJ.FETCH_METADATA(
        OBJ.MAKE_REF('gs://mybucket/documents/one.pdf', 'myproject.us.myconnection')
      ), 'r'
    )] AS object_ref_runtime
  )
)).result AS summary;
```

## Go deeper

Full extracted notebook walkthroughs live in this skill's `narrative/` folder:

- [`narrative/ml_process_document.md`](../narrative/ml_process_document.md) (source: `functions/ml_process_document/`) — working, currently the recommended document-extraction path
- [`narrative/ai_parse_document.md`](../narrative/ai_parse_document.md) (source: `functions/ai_parse_document/`) — blocked/offline as of 2026-06-01; the notebook carries a warning banner
- [`narrative/document_rag.md`](../narrative/document_rag.md) (source: `workflows/document_rag/`) — Document RAG workflow, currently blocked on the AI.PARSE_DOCUMENT outage

Object Tables and `OBJ.*` functions have no dedicated function folder — they're infrastructure, not a callable AI function themselves — and are documented in RESOURCES.md's **"Unstructured Data Infrastructure"** section (`bq-ai-functions/RESOURCES.md`).
