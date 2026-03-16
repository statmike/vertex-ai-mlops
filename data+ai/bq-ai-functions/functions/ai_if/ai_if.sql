-- AI.IF — Progressive SQL Examples
-- ===================================
-- Managed scalar function that evaluates natural language conditions.
-- Returns BOOL directly. BigQuery auto-optimizes prompts and Gemini calls.
-- Supports multimodal input via ObjectRef (documents, images, video).
--
-- Returns: BOOL (TRUE/FALSE) — NULL on error
--
-- Full reference: ../../RESOURCES.md
-- Official docs: https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-if


-- =============================================================================
-- Example 1: Boolean evaluation
-- =============================================================================
SELECT
  city,
  AI.IF(CONCAT(city, ' is in Asia')) AS is_in_asia
FROM UNNEST(['Tokyo', 'Paris', 'Nairobi', 'Bangkok', 'Sydney']) AS city;


-- =============================================================================
-- Example 2: Filtering in WHERE
-- =============================================================================
SELECT review
FROM UNNEST([
  'Amazing product, fast delivery!',
  'Terrible quality. Broke after one day.',
  'Average, nothing special.',
  'Great value for the price!'
]) AS review
WHERE AI.IF(CONCAT(review, ' is a positive review'));


-- =============================================================================
-- Example 3: Combining AI and non-AI filters
-- =============================================================================
-- BigQuery evaluates non-AI conditions first to reduce Gemini calls.
WITH articles AS (
  SELECT *
  FROM UNNEST([
    STRUCT('tech' AS category, 'New AI chip sets speed record' AS title),
    STRUCT('tech', 'Best smartphones of the year'),
    STRUCT('sports', 'Olympic records broken in swimming'),
    STRUCT('tech', 'Cloud computing market grows 30%')
  ])
)
SELECT category, title
FROM articles
WHERE category = 'tech'
  AND AI.IF(CONCAT(title, ' is about artificial intelligence'));


-- =============================================================================
-- Example 4: Content moderation
-- =============================================================================
SELECT
  comment,
  AI.IF(CONCAT(comment, ' contains inappropriate language or personal attacks')) AS needs_review
FROM UNNEST([
  'Great article, very informative!',
  'This is completely wrong and the author is incompetent.',
  'I disagree but appreciate the research.'
]) AS comment;


-- =============================================================================
-- Example 5: Specifying an endpoint
-- =============================================================================
SELECT
  statement,
  AI.IF(CONCAT(statement, ' is factually accurate'), endpoint => 'gemini-2.5-flash') AS is_accurate
FROM UNNEST([
  'The Earth orbits the Sun.',
  'Water boils at 50 degrees Celsius.',
  'Python is a programming language.'
]) AS statement;


-- =============================================================================
-- Example 6: Evaluate a condition on a document (ObjectRef)
-- =============================================================================
-- Pass a document via ObjectRef in a STRUCT prompt.
-- Requires: Cloud resource connection with roles/storage.objectViewer
SELECT
  AI.IF(
    STRUCT(
      'This document is a financial invoice' AS prompt,
      [OBJ.GET_ACCESS_URL(
        OBJ.FETCH_METADATA(
          OBJ.MAKE_REF(
            'gs://BUCKET/path/to/invoice.pdf',
            'PROJECT_ID.LOCATION.CONNECTION_ID'
          )
        ), 'r'
      )] AS object_ref_runtime
    )
  ) AS is_invoice;
