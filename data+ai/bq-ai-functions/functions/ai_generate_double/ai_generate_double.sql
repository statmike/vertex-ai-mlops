-- AI.GENERATE_DOUBLE — Progressive SQL Examples
-- ===============================================
-- Scalar function returning STRUCT<result FLOAT64, full_response JSON, status STRING>.
-- More control than AI.SCORE but less managed (no auto-rubric).
-- Supports multimodal input via ObjectRef (documents, images, video).
-- Preview status.
--
-- Full reference: ../../RESOURCES.md
-- Official docs: https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-generate-double


-- =============================================================================
-- Example 1: Numeric estimation
-- =============================================================================
SELECT
  city,
  (AI.GENERATE_DOUBLE(
    CONCAT('Estimate the population of ', city, ' in millions.')
  )).result AS population_millions
FROM UNNEST(['Tokyo', 'Paris', 'Nairobi', 'Lima', 'Sydney']) AS city;


-- =============================================================================
-- Example 2: Scoring
-- =============================================================================
SELECT
  review,
  (AI.GENERATE_DOUBLE(
    CONCAT('Rate the positivity of this review on a scale of 0.0 to 1.0: ', review)
  )).result AS positivity
FROM UNNEST([
  'Best product ever!', 'Terrible.', 'Average quality.', 'Good value.'
]) AS review
ORDER BY positivity DESC;


-- =============================================================================
-- Example 3: With endpoint
-- =============================================================================
SELECT
  text,
  (AI.GENERATE_DOUBLE(
    CONCAT('Rate reading difficulty 1.0-10.0: ', text),
    endpoint => 'gemini-2.5-flash'
  )).result AS difficulty
FROM UNNEST([
  'The cat sat on the mat.',
  'Quantum entanglement demonstrates non-local correlations.',
  'Machine learning models improve with data.'
]) AS text;


-- =============================================================================
-- Example 4: Extract a numeric value from a document (ObjectRef)
-- =============================================================================
-- Pass a document via ObjectRef in a STRUCT prompt.
-- Requires: Cloud resource connection with roles/storage.objectViewer
SELECT
  (AI.GENERATE_DOUBLE(
    STRUCT(
      'What is the total dollar amount on this invoice?' AS prompt,
      [OBJ.GET_ACCESS_URL(
        OBJ.FETCH_METADATA(
          OBJ.MAKE_REF(
            'gs://BUCKET/path/to/invoice.pdf',
            'PROJECT_ID.LOCATION.CONNECTION_ID'
          )
        ), 'r'
      )] AS object_ref_runtime
    )
  )).result AS total_amount;
