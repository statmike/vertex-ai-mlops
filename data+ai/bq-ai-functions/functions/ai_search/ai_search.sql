-- AI.SEARCH — Progressive SQL Examples
-- ======================================
-- Simplified semantic search for tables with autonomous embedding generation.
-- Embeds the query at runtime — no manual embedding step needed.
--
-- Returns: base STRUCT (all columns), distance FLOAT64
--
-- Full reference: ../../RESOURCES.md
-- Official docs: https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-search


-- =============================================================================
-- Setup: Create table with autonomous embedding generation
-- The embedding column uses GENERATED ALWAYS AS with AI.EMBED.
-- OPTIONS(asynchronous = TRUE) lets BigQuery generate embeddings in the background.
-- =============================================================================
CREATE OR REPLACE TABLE `PROJECT_ID.DATASET.ai_search_knowledge_base` (
  id INT64,
  title STRING,
  content STRING,
  content_embedding STRUCT<result ARRAY<FLOAT64>, status STRING>
    GENERATED ALWAYS AS (
      AI.EMBED(content,
        connection_id => 'PROJECT_ID.LOCATION.CONNECTION_ID',
        endpoint => 'text-embedding-005')
    ) STORED OPTIONS (asynchronous = TRUE)
);

-- Insert data — embeddings are generated automatically in the background
INSERT INTO `PROJECT_ID.DATASET.ai_search_knowledge_base` (id, title, content)
VALUES
  (1, 'BigQuery', 'BigQuery is a serverless data warehouse.'),
  (2, 'Cloud Functions', 'Cloud Functions runs event-driven code.'),
  (3, 'Cloud Storage', 'Cloud Storage stores objects.');


-- =============================================================================
-- Example 1: Basic semantic search
-- =============================================================================
SELECT base.title, base.content, distance
FROM AI.SEARCH(
  TABLE `PROJECT_ID.DATASET.ai_search_knowledge_base`,
  'content',
  'serverless compute for running code'
);


-- =============================================================================
-- Example 2: Limiting results
-- =============================================================================
SELECT base.title, base.content, distance
FROM AI.SEARCH(
  TABLE `PROJECT_ID.DATASET.ai_search_knowledge_base`,
  'content',
  'data storage and analytics',
  top_k => 2
);
