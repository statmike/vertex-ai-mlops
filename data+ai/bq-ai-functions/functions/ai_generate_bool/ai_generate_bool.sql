-- AI.GENERATE_BOOL — Progressive SQL Examples
-- =============================================
-- Scalar function returning STRUCT<result BOOL, full_response JSON, status STRING>.
-- More control than AI.IF but less managed (no auto-optimization).
-- Supports multimodal input via ObjectRef (documents, images, video).
-- Preview status.
--
-- Full reference: ../../RESOURCES.md
-- Official docs: https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-generate-bool


-- =============================================================================
-- Example 1: Basic boolean evaluation
-- =============================================================================
SELECT
  city,
  (AI.GENERATE_BOOL(CONCAT(city, ' is in Europe'))).result AS is_in_europe
FROM UNNEST(['London', 'Tokyo', 'Berlin', 'Sydney', 'Rome']) AS city;


-- =============================================================================
-- Example 2: Filtering
-- =============================================================================
SELECT review
FROM UNNEST([
  'Amazing product!', 'Terrible quality.', 'Pretty good.', 'Would not recommend.'
]) AS review
WHERE (AI.GENERATE_BOOL(CONCAT(review, ' is a positive review'))).result = TRUE;


-- =============================================================================
-- Example 3: With endpoint and model_params
-- =============================================================================
SELECT
  statement,
  (AI.GENERATE_BOOL(
    CONCAT(statement, ' is factually accurate'),
    endpoint => 'gemini-2.5-flash'
  )).result AS is_accurate
FROM UNNEST([
  'The Earth is the third planet from the Sun.',
  'Water boils at 50 degrees Celsius.',
  'Python was created by Guido van Rossum.'
]) AS statement;


-- =============================================================================
-- Example 4: Boolean question about a document (ObjectRef)
-- =============================================================================
-- Pass a document via ObjectRef in a STRUCT prompt.
-- Requires: Cloud resource connection with roles/storage.objectViewer
SELECT
  (AI.GENERATE_BOOL(
    STRUCT(
      'Does this invoice total exceed $5,000?' AS prompt,
      [OBJ.GET_ACCESS_URL(
        OBJ.FETCH_METADATA(
          OBJ.MAKE_REF(
            'gs://BUCKET/path/to/invoice.pdf',
            'PROJECT_ID.LOCATION.CONNECTION_ID'
          )
        ), 'r'
      )] AS object_ref_runtime
    )
  )).result AS exceeds_5000;
