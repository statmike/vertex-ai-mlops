-- AI.SCORE — Progressive SQL Examples
-- =====================================
-- Managed scalar function that rates inputs on a scale you describe.
-- Returns FLOAT64 directly. Auto-generates a scoring rubric.
-- Supports multimodal input via ObjectRef (documents, images, video).
--
-- Returns: FLOAT64 — NULL on error
--
-- Full reference: ../../RESOURCES.md
-- Official docs: https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-score


-- =============================================================================
-- Example 1: Basic scoring
-- =============================================================================
-- Always specify a range in your prompt.
SELECT
  review,
  AI.SCORE(CONCAT('Rate the positivity of this review on a scale of 1 to 10: ', review)) AS positivity_score
FROM UNNEST([
  'Amazing product, exceeded all my expectations!',
  'It was okay, nothing special.',
  'Terrible quality. Completely disappointed.',
  'Good value for the price. Would buy again.'
]) AS review;


-- =============================================================================
-- Example 2: Ranking with ORDER BY
-- =============================================================================
SELECT
  resume,
  AI.SCORE(CONCAT(
    'Rate this resume for a data engineer role on a scale of 1 to 10: ', resume
  )) AS qualification_score
FROM UNNEST([
  '5 years Python, SQL, Spark. Built pipelines at scale. AWS certified.',
  'Junior developer, 1 year JavaScript. No data engineering.',
  '10 years data engineering. Expert in BigQuery, Dataflow, Airflow.',
  '3 years analytics, some Python. Interested in engineering.'
]) AS resume
ORDER BY qualification_score DESC;


-- =============================================================================
-- Example 3: Filter and rank
-- =============================================================================
WITH scored AS (
  SELECT
    review,
    AI.SCORE(CONCAT('Rate urgency on a scale of 1 to 5: ', review)) AS urgency
  FROM UNNEST([
    'My order arrived damaged and I need a replacement ASAP.',
    'Just wondering about your return policy.',
    'Your product caused a safety hazard!',
    'The color is slightly different from the photo.',
    'I was charged twice and need an immediate refund!'
  ]) AS review
)
SELECT review, urgency
FROM scored
WHERE urgency >= 3
ORDER BY urgency DESC;


-- =============================================================================
-- Example 4: Score a document (ObjectRef)
-- =============================================================================
-- Use the tuple syntax to pass both scoring criteria and a document reference.
-- Requires: Object table + Cloud resource connection with roles/storage.objectViewer
SELECT
  uri,
  AI.SCORE(
    ('Rate the professionalism and formality of this document on a scale of 0 to 1',
     OBJ.GET_ACCESS_URL(ref, 'r'))
  ) AS professionalism
FROM
  `PROJECT_ID.DATASET.ai_score_docs`;
