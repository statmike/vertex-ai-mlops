-- ML.GENERATE_EMBEDDING — Progressive SQL Examples
-- ==================================================
-- Legacy predecessor to AI.GENERATE_EMBEDDING.
-- Same capabilities but with ml_generate_embedding_ column prefixes.
-- Google recommends AI.GENERATE_EMBEDDING for new queries.
--
-- Full reference: ../../RESOURCES.md
-- Official docs: https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-generate-embedding


-- =============================================================================
-- Example 1: Basic text embedding
-- =============================================================================
SELECT content,
  ARRAY_LENGTH(ml_generate_embedding_result) AS dims
FROM ML.GENERATE_EMBEDDING(
  MODEL `PROJECT_ID.DATASET.embedding_text`,
  (SELECT text AS content
   FROM UNNEST(['BigQuery is a data warehouse.', 'Cloud computing scales.']) AS text)
);


-- =============================================================================
-- Example 2: With task_type
-- =============================================================================
SELECT content, ARRAY_LENGTH(ml_generate_embedding_result) AS dims
FROM ML.GENERATE_EMBEDDING(
  MODEL `PROJECT_ID.DATASET.embedding_text`,
  (SELECT text AS content
   FROM UNNEST(['BigQuery', 'Cloud Functions', 'Cloud Storage']) AS text),
  STRUCT('RETRIEVAL_DOCUMENT' AS task_type)
);
