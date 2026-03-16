-- AI.SIMILARITY — Progressive SQL Examples
-- ==========================================
-- Scalar function that computes cosine similarity between two inputs.
-- Generates embeddings at runtime. No pre-computed embeddings needed.
--
-- Returns: FLOAT64 (cosine similarity, closer to 1 = more similar)
--
-- Full reference: ../../RESOURCES.md
-- Official docs: https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-similarity


-- =============================================================================
-- Example 1: Basic text similarity
-- =============================================================================
SELECT
  AI.SIMILARITY(
    content1 => 'BigQuery is a data warehouse',
    content2 => 'BigQuery stores and analyzes data',
    endpoint => 'text-embedding-005'
  ) AS similarity;


-- =============================================================================
-- Example 2: Comparing multiple pairs
-- =============================================================================
SELECT
  text_a,
  text_b,
  AI.SIMILARITY(
    content1 => text_a,
    content2 => text_b,
    endpoint => 'text-embedding-005'
  ) AS similarity
FROM
  UNNEST(['machine learning', 'deep learning', 'cooking recipes']) AS text_a,
  UNNEST(['artificial intelligence', 'neural networks', 'baking bread']) AS text_b
ORDER BY similarity DESC;


-- =============================================================================
-- Example 3: Finding the best match
-- =============================================================================
SELECT product,
  AI.SIMILARITY(
    content1 => 'comfortable typing device',
    content2 => product,
    endpoint => 'text-embedding-005'
  ) AS similarity
FROM UNNEST([
  'mechanical keyboard with ergonomic design',
  'wireless mouse with adjustable DPI',
  'standing desk with memory presets'
]) AS product
ORDER BY similarity DESC
LIMIT 1;


-- =============================================================================
-- Example 4: Document-to-document similarity (multimodal)
-- =============================================================================
-- Requires: connection with aiplatform.user + storage.objectViewer roles
-- Uses inline ObjectRef pipeline with multimodalembedding@001
-- Same-type documents should score higher than cross-type pairs
SELECT
  AI.SIMILARITY(
    content1 => OBJ.GET_ACCESS_URL(
      OBJ.FETCH_METADATA(
        OBJ.MAKE_REF('gs://BUCKET/path/to/invoice_1.png', 'PROJECT_ID.LOCATION.CONNECTION_ID')
      ), 'r'),
    content2 => OBJ.GET_ACCESS_URL(
      OBJ.FETCH_METADATA(
        OBJ.MAKE_REF('gs://BUCKET/path/to/receipt_1.png', 'PROJECT_ID.LOCATION.CONNECTION_ID')
      ), 'r'),
    endpoint => 'multimodalembedding@001',
    connection_id => 'PROJECT_ID.LOCATION.CONNECTION_ID'
  ) AS similarity;


-- =============================================================================
-- Example 5: Cross-modal similarity (text to document)
-- =============================================================================
-- Compare text descriptions against document images — multimodal embeddings share a vector space
SELECT
  description,
  doc_name,
  ROUND(AI.SIMILARITY(
    content1 => description,
    content2 => OBJ.GET_ACCESS_URL(
      OBJ.FETCH_METADATA(
        OBJ.MAKE_REF(
          CONCAT('gs://BUCKET/path/to/', doc_name),
          'PROJECT_ID.LOCATION.CONNECTION_ID'
        )
      ), 'r'),
    endpoint => 'multimodalembedding@001',
    connection_id => 'PROJECT_ID.LOCATION.CONNECTION_ID'
  ), 4) AS similarity
FROM
  UNNEST(['a business invoice', 'a store receipt']) AS description,
  UNNEST(['invoice_1.png', 'receipt_1.png']) AS doc_name
ORDER BY description, similarity DESC;
