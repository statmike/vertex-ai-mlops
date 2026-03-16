-- ML.PROCESS_DOCUMENT — Progressive SQL Examples
-- ================================================
-- Table-valued function that processes documents from an object table
-- using Document AI. Extracts structured data from invoices, receipts,
-- forms, and other documents stored in Cloud Storage.
--
-- Requires: object table, Document AI processor, remote model with
-- REMOTE_SERVICE_TYPE = 'CLOUD_AI_DOCUMENT_V1'
--
-- Returns: processor-specific fields + ml_process_document_result (JSON),
--          ml_process_document_status, and all object table columns
--
-- Full reference: ../../RESOURCES.md
-- Official docs: https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-process-document


-- =============================================================================
-- Example 1: Process a single document — discover output columns
-- =============================================================================
-- Use SELECT * to see all columns the processor returns.
SELECT *
FROM ML.PROCESS_DOCUMENT(
  MODEL `PROJECT_ID.DATASET.ml_process_document_invoice_parser`,
  (SELECT *
   FROM `PROJECT_ID.DATASET.ml_process_document_invoices`
   ORDER BY uri
   LIMIT 1)
);


-- =============================================================================
-- Example 2: Extract specific invoice fields
-- =============================================================================
-- Select only the processor-specific columns you need.
SELECT
  uri,
  invoice_id,
  supplier_name,
  total_amount,
  currency,
  invoice_date,
  due_date
FROM ML.PROCESS_DOCUMENT(
  MODEL `PROJECT_ID.DATASET.ml_process_document_invoice_parser`,
  (SELECT *
   FROM `PROJECT_ID.DATASET.ml_process_document_invoices`
   ORDER BY uri
   LIMIT 5)
);


-- =============================================================================
-- Example 3: Process all documents
-- =============================================================================
-- Process the entire object table. Use TABLE reference (no subquery needed).
SELECT
  uri,
  invoice_id,
  supplier_name,
  total_amount,
  currency,
  invoice_date,
  due_date,
  ml_process_document_status
FROM ML.PROCESS_DOCUMENT(
  MODEL `PROJECT_ID.DATASET.ml_process_document_invoice_parser`,
  TABLE `PROJECT_ID.DATASET.ml_process_document_invoices`
)
ORDER BY uri;


-- =============================================================================
-- Example 4: Persist results to a table
-- =============================================================================
-- Save extraction output to avoid re-processing documents.
CREATE OR REPLACE TABLE `PROJECT_ID.DATASET.ml_process_document_results` AS
SELECT
  uri,
  invoice_id,
  supplier_name,
  total_amount,
  currency,
  invoice_date,
  due_date
FROM ML.PROCESS_DOCUMENT(
  MODEL `PROJECT_ID.DATASET.ml_process_document_invoice_parser`,
  TABLE `PROJECT_ID.DATASET.ml_process_document_invoices`
);


-- =============================================================================
-- Example 5: Using PROCESS_OPTIONS — page selection
-- =============================================================================
-- Process only the first page of each document.
SELECT
  uri,
  invoice_id,
  supplier_name,
  total_amount
FROM ML.PROCESS_DOCUMENT(
  MODEL `PROJECT_ID.DATASET.ml_process_document_invoice_parser`,
  (SELECT *
   FROM `PROJECT_ID.DATASET.ml_process_document_invoices`
   ORDER BY uri
   LIMIT 3),
  PROCESS_OPTIONS => JSON '{"fromStart": 1}'
);
