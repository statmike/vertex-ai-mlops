-- AI.PARSE_DOCUMENT — Progressive SQL Examples
-- ================================================
-- Table-valued function that parses documents using the Document AI
-- Layout Parser. Combines OCR, layout parsing, and chunking in a single
-- SQL function — no CREATE MODEL step required.
--
-- Requires: object table OR ObjectRef subquery, Document AI Layout Parser processor
-- (no remote model creation needed — endpoint points directly to processor)
--
-- Returns: chunk_id, start_page, end_page, content, plus all object table columns
-- Limit: 130 pages per document
--
-- Full reference: ../../RESOURCES.md
-- Official docs: https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-parse-document


-- =============================================================================
-- Example 1: Parse a single document — discover output columns
-- =============================================================================
-- Use SELECT * to see all columns AI.PARSE_DOCUMENT returns.
SELECT *
FROM AI.PARSE_DOCUMENT(
  TABLE `PROJECT_ID.DATASET.OBJECT_TABLE`,
  endpoint => 'projects/PROJECT_NUM/locations/us/processors/PROCESSOR_ID'
)
LIMIT 5;


-- =============================================================================
-- Example 2: Select specific output fields
-- =============================================================================
-- The key output columns: chunk_id, start_page, end_page, content.
SELECT
  uri,
  chunk_id,
  start_page,
  end_page,
  LEFT(content, 200) AS content_preview
FROM AI.PARSE_DOCUMENT(
  TABLE `PROJECT_ID.DATASET.OBJECT_TABLE`,
  endpoint => 'projects/PROJECT_NUM/locations/us/processors/PROCESSOR_ID'
)
ORDER BY uri, chunk_id;


-- =============================================================================
-- Example 3: Custom chunk_size — smaller chunks for RAG
-- =============================================================================
-- Smaller chunks improve retrieval precision in RAG pipelines.
-- Default is 1000; use 250 for more granular retrieval.
SELECT
  uri,
  chunk_id,
  start_page,
  end_page,
  content
FROM AI.PARSE_DOCUMENT(
  TABLE `PROJECT_ID.DATASET.OBJECT_TABLE`,
  endpoint => 'projects/PROJECT_NUM/locations/us/processors/PROCESSOR_ID',
  chunk_size => 250
)
ORDER BY uri, chunk_id;


-- =============================================================================
-- Example 4: Subquery filtering — parse specific documents
-- =============================================================================
-- Use a subquery to filter which documents to process.
SELECT
  uri,
  chunk_id,
  content
FROM AI.PARSE_DOCUMENT(
  (SELECT * FROM `PROJECT_ID.DATASET.OBJECT_TABLE`
   WHERE uri LIKE '%invoice_001%'),
  endpoint => 'projects/PROJECT_NUM/locations/us/processors/PROCESSOR_ID'
);


-- =============================================================================
-- Example 5: Persist results to avoid re-parsing
-- =============================================================================
-- Save parsed output to a regular table for repeated queries.
CREATE OR REPLACE TABLE `PROJECT_ID.DATASET.parsed_documents` AS
SELECT
  uri,
  chunk_id,
  start_page,
  end_page,
  content
FROM AI.PARSE_DOCUMENT(
  TABLE `PROJECT_ID.DATASET.OBJECT_TABLE`,
  endpoint => 'projects/PROJECT_NUM/locations/us/processors/PROCESSOR_ID'
);


-- =============================================================================
-- Example 6: Using connection_id — service account credentials
-- =============================================================================
-- Use a Cloud resource connection instead of end-user credentials.
SELECT
  uri,
  chunk_id,
  content
FROM AI.PARSE_DOCUMENT(
  TABLE `PROJECT_ID.DATASET.OBJECT_TABLE`,
  endpoint => 'projects/PROJECT_NUM/locations/us/processors/PROCESSOR_ID',
  connection_id => 'PROJECT_ID.LOCATION.CONNECTION_ID'
)
LIMIT 5;


-- =============================================================================
-- Example 7: ObjectRef — parse a single document without an object table
-- =============================================================================
-- Use OBJ.MAKE_REF to construct the required 'ref' column inline.
-- No object table creation needed — just a GCS URI and connection.
SELECT
  uri,
  chunk_id,
  start_page,
  end_page,
  LEFT(content, 200) AS content_preview
FROM AI.PARSE_DOCUMENT(
  (SELECT
    'gs://BUCKET/path/to/document.pdf' AS uri,
    OBJ.MAKE_REF(
      'gs://BUCKET/path/to/document.pdf',
      'PROJECT_ID.LOCATION.CONNECTION_ID'
    ) AS ref
  ),
  endpoint => 'projects/PROJECT_NUM/locations/us/processors/PROCESSOR_ID'
);


-- =============================================================================
-- Example 8: ObjectRef — parse multiple documents without an object table
-- =============================================================================
-- Use UNNEST to create rows from an array of URIs, then add a ref column.
SELECT
  uri,
  chunk_id,
  content
FROM AI.PARSE_DOCUMENT(
  (SELECT
    uri,
    OBJ.MAKE_REF(uri, 'PROJECT_ID.LOCATION.CONNECTION_ID') AS ref
  FROM UNNEST([
    'gs://BUCKET/path/to/doc1.pdf',
    'gs://BUCKET/path/to/doc2.pdf',
    'gs://BUCKET/path/to/doc3.pdf'
  ]) AS uri),
  endpoint => 'projects/PROJECT_NUM/locations/us/processors/PROCESSOR_ID'
)
ORDER BY uri, chunk_id;


-- =============================================================================
-- Example 9: ObjectRef — parse documents from a regular table of URIs
-- =============================================================================
-- If you have a table with GCS URIs, use ObjectRef to parse without
-- creating a separate object table.
SELECT
  uri,
  chunk_id,
  content
FROM AI.PARSE_DOCUMENT(
  (SELECT
    uri,
    OBJ.MAKE_REF(uri, 'PROJECT_ID.LOCATION.CONNECTION_ID') AS ref
  FROM `PROJECT_ID.DATASET.TABLE_WITH_URIS`),
  endpoint => 'projects/PROJECT_NUM/locations/us/processors/PROCESSOR_ID'
)
ORDER BY uri, chunk_id;
