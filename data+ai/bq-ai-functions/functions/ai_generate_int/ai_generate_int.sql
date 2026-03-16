-- AI.GENERATE_INT — Progressive SQL Examples
-- ============================================
-- Scalar function returning STRUCT<result INT64, full_response JSON, status STRING>.
-- For integer estimation, counting, and classification.
-- Supports multimodal input via ObjectRef (documents, images, video).
-- Preview status.
--
-- Full reference: ../../RESOURCES.md
-- Official docs: https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-generate-int


-- =============================================================================
-- Example 1: Numeric fact retrieval
-- =============================================================================
SELECT
  country,
  (AI.GENERATE_INT(
    CONCAT('How many states/provinces does ', country, ' have?')
  )).result AS num_divisions
FROM UNNEST(['United States', 'Canada', 'Brazil', 'India', 'Australia']) AS country;


-- =============================================================================
-- Example 2: Integer scoring
-- =============================================================================
SELECT
  review,
  (AI.GENERATE_INT(
    CONCAT('Rate this review 1-5 stars: ', review)
  )).result AS stars
FROM UNNEST([
  'Best purchase ever!', 'Complete waste of money.',
  'Decent product.', 'Exceeded expectations!'
]) AS review
ORDER BY stars DESC;


-- =============================================================================
-- Example 3: Counting
-- =============================================================================
SELECT
  sentence,
  (AI.GENERATE_INT(
    CONCAT('How many words? Just the number: ', sentence)
  )).result AS word_count
FROM UNNEST([
  'The quick brown fox jumps over the lazy dog.',
  'Hello world.',
  'BigQuery is a fully managed data warehouse.'
]) AS sentence;


-- =============================================================================
-- Example 4: Count items in a document (ObjectRef)
-- =============================================================================
-- Pass a document via ObjectRef in a STRUCT prompt.
-- Requires: Cloud resource connection with roles/storage.objectViewer
SELECT
  (AI.GENERATE_INT(
    STRUCT(
      'How many line items are on this invoice?' AS prompt,
      [OBJ.GET_ACCESS_URL(
        OBJ.FETCH_METADATA(
          OBJ.MAKE_REF(
            'gs://BUCKET/path/to/invoice.pdf',
            'PROJECT_ID.LOCATION.CONNECTION_ID'
          )
        ), 'r'
      )] AS object_ref_runtime
    )
  )).result AS line_item_count;
