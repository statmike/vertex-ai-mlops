![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2Fdata%2Bai%2Fbq-ai-functions%2Freference&file=document-processing.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/data%2Bai/bq-ai-functions/reference/document-processing.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-ai-functions/reference/document-processing.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-ai-functions/reference/document-processing.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-ai-functions/reference/document-processing.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-ai-functions/reference/document-processing.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
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
    <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/data%2Bai/bq-ai-functions/reference/document-processing.md"><img src="https://www.svgrepo.com/download/5445/download-button.svg" alt="Download icon" width="20px"></a> <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/data%2Bai/bq-ai-functions/reference/document-processing.md">Download File</a> <i>(right-click and "Save As")</i>
  </td>
</tr>
</table><br/><br/>

---
# Document Processing

> Part of the [BigQuery AI Functions Resources](../RESOURCES.md) · [Project README](../README.md)

These functions process unstructured documents (PDFs, images, forms, invoices) using Document AI processors, returning structured extraction results directly as BigQuery columns.

**Key relationships:**
- `ML.PROCESS_DOCUMENT` requires a Document AI processor **and** a remote model (`CREATE MODEL` with `REMOTE_SERVICE_TYPE = 'CLOUD_AI_DOCUMENT_V1'`). Supports all processor types (invoice, receipt, form, OCR, custom).
- `AI.PARSE_DOCUMENT` requires a Document AI Layout Parser processor but **no `CREATE MODEL`** — the `endpoint` parameter points directly to the processor. Layout Parser only (OCR + chunking).

---

## `ML.PROCESS_DOCUMENT`
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

## `AI.PARSE_DOCUMENT`
- **⚠️ Status (as of 2026-09-01): OFFLINE, and reference documentation now WITHDRAWN.** The function (Preview) was taken offline by Google for revision on 2026-06-01 and does not execute. As of this audit the situation has escalated: the reference page `.../bigqueryml-syntax-ai-parse-document` returns **HTTP 404**, the function no longer appears in the BigQuery docs navigation tree, and it is absent from the generative AI overview page. Google has published no release note explaining the withdrawal.
  - **Interim alternative:** use [`ML.PROCESS_DOCUMENT`](#mlprocess_document) for OCR and document extraction. It reaches the same Document AI processors but requires a remote model and a `CREATE MODEL` step — precisely the setup AI.PARSE_DOCUMENT was introduced to remove.
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
