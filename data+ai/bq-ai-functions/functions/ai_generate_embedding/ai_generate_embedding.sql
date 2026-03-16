-- AI.GENERATE_EMBEDDING — Progressive SQL Examples
-- ==================================================
-- Table-valued function that creates embeddings via a remote model.
-- Requires CREATE MODEL. Input must have a 'content' column.
--
-- Returns: input columns + embedding ARRAY<FLOAT64>, statistics JSON, status STRING
--
-- Full reference: ../../RESOURCES.md
-- Official docs: https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-generate-embedding


-- =============================================================================
-- Example 1: Basic text embedding
-- =============================================================================
SELECT content, ARRAY_LENGTH(embedding) AS dims
FROM AI.GENERATE_EMBEDDING(
  MODEL `PROJECT_ID.DATASET.embedding_text`,
  (SELECT text AS content
   FROM UNNEST(['BigQuery is a data warehouse.', 'Cloud computing scales.']) AS text)
);


-- =============================================================================
-- Example 2: With task_type
-- =============================================================================
SELECT content, ARRAY_LENGTH(embedding) AS dims, statistics
FROM AI.GENERATE_EMBEDDING(
  MODEL `PROJECT_ID.DATASET.embedding_text`,
  (SELECT text AS content
   FROM UNNEST(['BigQuery', 'Cloud Functions', 'Cloud Storage']) AS text),
  STRUCT('RETRIEVAL_DOCUMENT' AS task_type)
);


-- =============================================================================
-- Example 3: Materializing embeddings
-- =============================================================================
CREATE OR REPLACE TABLE `PROJECT_ID.DATASET.ai_generate_embedding_docs` AS
SELECT content, embedding
FROM AI.GENERATE_EMBEDDING(
  MODEL `PROJECT_ID.DATASET.embedding_text`,
  (SELECT text AS content
   FROM UNNEST([
     'BigQuery is a serverless data warehouse.',
     'Cloud Functions runs event-driven code.',
     'Cloud Storage stores objects.',
     'Kubernetes Engine runs containers.',
     'Pub/Sub is a messaging service.'
   ]) AS text),
  STRUCT('RETRIEVAL_DOCUMENT' AS task_type)
);


-- =============================================================================
-- Example 4: Multimodal embedding model
-- =============================================================================
-- Create a remote model for image/video embeddings
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.embedding_multimodal`
  REMOTE WITH CONNECTION `PROJECT_ID.LOCATION.CONNECTION_ID`
  OPTIONS (endpoint = 'multimodalembedding@001');


-- =============================================================================
-- Example 5: Batch embed documents via inline ObjectRef
-- =============================================================================
-- Build ObjectRef values inline — no object table or reservation needed
SELECT
  doc_name,
  ARRAY_LENGTH(embedding) AS dims
FROM AI.GENERATE_EMBEDDING(
  MODEL `PROJECT_ID.DATASET.embedding_multimodal`,
  (SELECT
    doc_name,
    OBJ.GET_ACCESS_URL(
      OBJ.FETCH_METADATA(
        OBJ.MAKE_REF(
          CONCAT('gs://BUCKET/path/to/', doc_name),
          'PROJECT_ID.LOCATION.CONNECTION_ID'
        )
      ), 'r') AS content
  FROM UNNEST([
    'invoice_1.png', 'invoice_2.png', 'receipt_1.png'
  ]) AS doc_name)
);


-- =============================================================================
-- Example 6: Custom embedding dimensions
-- =============================================================================
-- Use output_dimensionality to reduce vector size (128, 256, 512, or 1408)
SELECT
  doc_name,
  ARRAY_LENGTH(embedding) AS dims
FROM AI.GENERATE_EMBEDDING(
  MODEL `PROJECT_ID.DATASET.embedding_multimodal`,
  (SELECT
    doc_name,
    OBJ.GET_ACCESS_URL(
      OBJ.FETCH_METADATA(
        OBJ.MAKE_REF(
          CONCAT('gs://BUCKET/path/to/', doc_name),
          'PROJECT_ID.LOCATION.CONNECTION_ID'
        )
      ), 'r') AS content
  FROM UNNEST(['invoice_1.png', 'invoice_2.png', 'invoice_3.png']) AS doc_name),
  STRUCT(256 AS output_dimensionality)
);
