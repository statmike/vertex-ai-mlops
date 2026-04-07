-- AI.AGG — Progressive SQL Examples
-- ====================================
-- Aggregate function that uses Gemini to aggregate data based on natural
-- language instructions. Automatically handles multi-level batching so it
-- can analyze data exceeding the Gemini context window.
--
-- Type: Aggregate function (use with GROUP BY)
-- Returns: STRING — one result per group (NULL on total failure, partial on partial failure)
-- Output cap: 10,000 tokens per group
-- Recommended limits: 20M rows per query, 1,000 distinct groups
-- Multimodal: Supports images via ObjectRef in STRUCT input (see examples 7-8)
--
-- Full reference: ../../RESOURCES.md
-- Official docs: https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-agg


-- =============================================================================
-- Example 1: Simplest possible call — aggregate without GROUP BY
-- =============================================================================
-- Without GROUP BY, AI.AGG aggregates all rows into a single result.
SELECT
  AI.AGG(
    review,
    'What is the overall sentiment of these reviews?'
  ) AS sentiment_summary
FROM UNNEST([
  'Absolutely love this product! Best purchase ever.',
  'Terrible quality, broke after one week.',
  'Pretty decent for the price. Nothing fancy.',
  'Would not recommend. Waste of money.',
  'Exceeded my expectations in every way!'
]) AS review;


-- =============================================================================
-- Example 2: GROUP BY — one summary per group
-- =============================================================================
-- AI.AGG returns one STRING per group, making it perfect for
-- summarizing data by category.
SELECT
  category,
  AI.AGG(
    feedback,
    'Summarize the main themes in this feedback.'
  ) AS themes
FROM UNNEST([
  STRUCT('product' AS category, 'The battery life is incredible' AS feedback),
  STRUCT('product', 'Screen quality is outstanding'),
  STRUCT('product', 'Too heavy to carry around comfortably'),
  STRUCT('shipping', 'Arrived two days early, great packaging'),
  STRUCT('shipping', 'Package was damaged during transit'),
  STRUCT('shipping', 'Delivery took three weeks instead of five days'),
  STRUCT('support', 'Agent resolved my issue in minutes'),
  STRUCT('support', 'Was on hold for over an hour before getting help'),
  STRUCT('support', 'Very knowledgeable and patient support team')
]) AS t
GROUP BY category;


-- =============================================================================
-- Example 3: DISTINCT — deduplicate before aggregating
-- =============================================================================
-- Use DISTINCT to remove duplicate inputs before sending to the model.
SELECT
  AI.AGG(
    DISTINCT comment,
    'What topics do these comments discuss?'
  ) AS topics
FROM UNNEST([
  'Great performance on the new update',
  'Great performance on the new update',  -- duplicate
  'Battery drain is still an issue',
  'Battery drain is still an issue',      -- duplicate
  'Love the new camera features',
  'UI feels sluggish after the patch'
]) AS comment;


-- =============================================================================
-- Example 4: TO_JSON_STRING — aggregate structured rows
-- =============================================================================
-- Use TO_JSON_STRING to pass multiple columns as context.
-- The model sees each row's full structure.
WITH tickets AS (
  SELECT *
  FROM UNNEST([
    STRUCT('Alice' AS agent, 'password reset' AS issue, 2 AS resolution_minutes),
    STRUCT('Alice', 'account locked', 5),
    STRUCT('Bob', 'billing error', 15),
    STRUCT('Bob', 'refund request', 30),
    STRUCT('Bob', 'subscription cancel', 8),
    STRUCT('Carol', 'login failure', 3),
    STRUCT('Carol', 'two-factor setup', 7)
  ])
)
SELECT
  agent,
  AI.AGG(
    TO_JSON_STRING(STRUCT(agent, issue, resolution_minutes)),
    'Analyze this support agent performance. What types of issues do they handle and how quickly?'
  ) AS performance_summary
FROM tickets
GROUP BY agent;


-- =============================================================================
-- Example 5: Finding common patterns across data
-- =============================================================================
-- AI.AGG excels at identifying patterns, trends, and common themes.
WITH error_logs AS (
  SELECT *
  FROM UNNEST([
    STRUCT('2025-01-15 08:23:01' AS timestamp, 'auth-service' AS service, 'Connection timeout to user DB' AS message),
    STRUCT('2025-01-15 08:23:05', 'auth-service', 'Failed to validate token: DB unavailable'),
    STRUCT('2025-01-15 08:23:12', 'api-gateway', 'Upstream auth-service returned 503'),
    STRUCT('2025-01-15 08:23:15', 'api-gateway', 'Circuit breaker opened for auth-service'),
    STRUCT('2025-01-15 08:24:00', 'payment-service', 'Transaction failed: auth token invalid'),
    STRUCT('2025-01-15 08:24:02', 'notification-service', 'Unable to send email: rate limit exceeded'),
    STRUCT('2025-01-15 08:25:00', 'auth-service', 'Connection to user DB restored'),
    STRUCT('2025-01-15 08:25:01', 'api-gateway', 'Circuit breaker closed for auth-service')
  ])
)
SELECT
  AI.AGG(
    TO_JSON_STRING(STRUCT(timestamp, service, message)),
    'Analyze these error logs. What was the root cause, which services were affected, and what was the sequence of events?'
  ) AS incident_analysis
FROM error_logs;


-- =============================================================================
-- Example 6: Specifying an endpoint
-- =============================================================================
-- Override the default model with any Gemini model (no thinking budget models).
SELECT
  AI.AGG(
    review,
    'What do customers like and dislike? Be concise.',
    endpoint => 'gemini-2.5-flash'
  ) AS summary
FROM UNNEST([
  'Fast delivery but the box was crushed.',
  'Product works great, very happy with it.',
  'Instructions were confusing but the item itself is solid.'
]) AS review;


-- =============================================================================
-- Example 7: Multimodal — summarize image contents with ObjectRef
-- =============================================================================
-- Use a STRUCT with ObjectRefRuntime to aggregate image data.
-- Requires: Object table with Cloud resource connection

-- CREATE OR REPLACE EXTERNAL TABLE `PROJECT_ID.DATASET.ai_agg_images`
-- WITH CONNECTION `PROJECT_ID.LOCATION.CONNECTION_ID`
-- OPTIONS (
--   object_metadata = 'SIMPLE',
--   uris = ['gs://BUCKET/path/to/images/*.png']
-- );

SELECT
  AI.AGG(
    STRUCT(OBJ.GET_ACCESS_URL(ref, 'r')),
    'What are the major categories of items shown in these images?'
  ) AS category_summary
FROM
  `PROJECT_ID.DATASET.ai_agg_images`;


-- =============================================================================
-- Example 8: Multimodal with GROUP BY
-- =============================================================================
-- Summarize images grouped by a metadata column.
-- This example assumes an object table with a content_type or folder-based grouping.

-- SELECT
--   REGEXP_EXTRACT(uri, r'gs://[^/]+/([^/]+)/') AS folder,
--   AI.AGG(
--     STRUCT(OBJ.GET_ACCESS_URL(ref, 'r')),
--     'Describe the common visual themes in these images.'
--   ) AS visual_themes
-- FROM
--   EXTERNAL_OBJECT_TRANSFORM(TABLE `PROJECT_ID.DATASET.ai_agg_images`,
--                             ['SIGNED_URL']) AS docs
-- GROUP BY folder;
