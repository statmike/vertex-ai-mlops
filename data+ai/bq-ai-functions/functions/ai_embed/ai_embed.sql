-- AI.EMBED — Progressive SQL Examples
-- =====================================
-- Scalar function that creates text or image embeddings.
-- Specify endpoint directly — no CREATE MODEL required.
--
-- Returns: STRUCT<result ARRAY<FLOAT64>, status STRING>
--
-- Full reference: ../../RESOURCES.md
-- Official docs: https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-embed


-- =============================================================================
-- Example 1: Basic text embedding
-- =============================================================================
SELECT
  text,
  ARRAY_LENGTH((AI.EMBED(
    content => text,
    endpoint => 'text-embedding-005'
  )).result) AS embedding_dimensions
FROM UNNEST(['BigQuery is a data warehouse.', 'Cloud computing scales on demand.']) AS text;


-- =============================================================================
-- Example 2: Viewing the embedding vector
-- =============================================================================
SELECT
  (AI.EMBED(
    content => 'What is machine learning?',
    endpoint => 'text-embedding-005'
  )).result AS embedding;


-- =============================================================================
-- Example 3: Using task_type
-- =============================================================================
SELECT
  text,
  (AI.EMBED(
    content => text,
    endpoint => 'text-embedding-005',
    task_type => 'RETRIEVAL_DOCUMENT'
  )).result AS embedding
FROM UNNEST([
  'BigQuery is a serverless data warehouse.',
  'Cloud Functions runs event-driven code.',
  'Cloud Storage stores objects in buckets.'
]) AS text;


-- =============================================================================
-- Example 4: Cosine similarity between texts
-- =============================================================================
WITH embeddings AS (
  SELECT
    text,
    (AI.EMBED(content => text, endpoint => 'text-embedding-005')).result AS vec
  FROM UNNEST([
    'BigQuery is a data warehouse',
    'BigQuery stores and analyzes large datasets',
    'I enjoy hiking in the mountains'
  ]) AS text
)
SELECT
  a.text AS text_a,
  b.text AS text_b,
  1 - ML.DISTANCE(a.vec, b.vec, 'COSINE') AS cosine_similarity
FROM embeddings a
CROSS JOIN embeddings b
WHERE a.text < b.text
ORDER BY cosine_similarity DESC;


-- =============================================================================
-- Example 5: Saving embeddings to a table
-- =============================================================================
CREATE OR REPLACE TABLE `PROJECT_ID.DATASET.ai_embed_documents` AS
SELECT
  id,
  text,
  (AI.EMBED(content => text, endpoint => 'text-embedding-005', task_type => 'RETRIEVAL_DOCUMENT')).result AS embedding
FROM UNNEST([
  STRUCT(1 AS id, 'BigQuery is a serverless data warehouse.' AS text),
  STRUCT(2, 'Cloud Functions runs event-driven code.'),
  STRUCT(3, 'Cloud Storage provides object storage.'),
  STRUCT(4, 'Kubernetes Engine runs containerized apps.'),
  STRUCT(5, 'Pub/Sub is a messaging service.')
]);


-- =============================================================================
-- Example 6: Embed a document image (multimodal)
-- =============================================================================
-- Requires: connection with aiplatform.user + storage.objectViewer roles
-- Uses inline ObjectRef pipeline: OBJ.MAKE_REF → OBJ.FETCH_METADATA → OBJ.GET_ACCESS_URL
-- Returns 1408-dimension vectors by default with multimodalembedding@001
SELECT
  'invoice_1.png' AS document,
  ARRAY_LENGTH((AI.EMBED(
    content => OBJ.GET_ACCESS_URL(
      OBJ.FETCH_METADATA(
        OBJ.MAKE_REF('gs://BUCKET/bq_ai_functions/ai_embed/invoice_1.png', 'PROJECT_ID.LOCATION.CONNECTION_ID')
      ), 'r'),
    endpoint => 'multimodalembedding@001',
    connection_id => 'PROJECT_ID.LOCATION.CONNECTION_ID'
  )).result) AS embedding_dimensions;


-- =============================================================================
-- Example 7: Compare document embeddings
-- =============================================================================
-- Embed invoices and receipts, compute pairwise cosine similarity
-- Documents of the same type should cluster together
WITH doc_embeddings AS (
  SELECT
    doc_name,
    (AI.EMBED(
      content => OBJ.GET_ACCESS_URL(
        OBJ.FETCH_METADATA(
          OBJ.MAKE_REF(
            CONCAT('gs://BUCKET/bq_ai_functions/ai_embed/', doc_name),
            'PROJECT_ID.LOCATION.CONNECTION_ID'
          )
        ), 'r'),
      endpoint => 'multimodalembedding@001',
      connection_id => 'PROJECT_ID.LOCATION.CONNECTION_ID'
    )).result AS vec
  FROM UNNEST([
    'invoice_1.png', 'invoice_2.png', 'invoice_3.png',
    'receipt_1.png', 'receipt_2.png', 'receipt_3.png'
  ]) AS doc_name
)
SELECT
  a.doc_name AS doc_a,
  b.doc_name AS doc_b,
  ROUND(1 - ML.DISTANCE(a.vec, b.vec, 'COSINE'), 4) AS cosine_similarity
FROM doc_embeddings a
CROSS JOIN doc_embeddings b
WHERE a.doc_name < b.doc_name
ORDER BY cosine_similarity DESC;
