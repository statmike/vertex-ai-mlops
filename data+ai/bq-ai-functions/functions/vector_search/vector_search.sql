-- VECTOR_SEARCH — Progressive SQL Examples
-- ==========================================
-- Table-valued function for top-K nearest neighbor search on pre-computed embeddings.
-- Supports vector indexes for efficient ANN search.
--
-- Returns: query STRUCT, base STRUCT, distance FLOAT64 (batch)
--          base STRUCT, distance FLOAT64 (single)
--
-- Full reference: ../../RESOURCES.md
-- Official docs: https://cloud.google.com/bigquery/docs/reference/standard-sql/search_functions#vector_search


-- =============================================================================
-- Setup: Create sample data with embeddings
-- =============================================================================
CREATE OR REPLACE TABLE `PROJECT_ID.DATASET.vector_search_products` AS
SELECT id, product, category, description,
  (AI.EMBED(content => description, endpoint => 'text-embedding-005', task_type => 'RETRIEVAL_DOCUMENT')).result AS embedding
FROM UNNEST([
  STRUCT(1 AS id, 'Laptop' AS product, 'Computing' AS category, 'High-performance laptop with 16GB RAM and SSD.' AS description),
  STRUCT(2, 'Headphones', 'Audio', 'Wireless noise-cancelling headphones with 30-hour battery.'),
  STRUCT(3, 'Standing Desk', 'Furniture', 'Electric height-adjustable standing desk with presets.'),
  STRUCT(4, 'Monitor', 'Computing', '32-inch 4K monitor with USB-C connectivity.'),
  STRUCT(5, 'Keyboard', 'Peripherals', 'Mechanical keyboard with programmable keys.')
]);


-- =============================================================================
-- Example 1: Single search (Preview)
-- =============================================================================
SELECT base.product, base.description, distance
FROM VECTOR_SEARCH(
  TABLE `PROJECT_ID.DATASET.vector_search_products`,
  'embedding',
  query_value => (AI.EMBED(content => 'comfortable work setup',
                           endpoint => 'text-embedding-005',
                           task_type => 'RETRIEVAL_QUERY')).result,
  top_k => 3,
  distance_type => 'COSINE'
);


-- =============================================================================
-- Example 2: Batch search
-- =============================================================================
SELECT query.search_term, base.product, distance
FROM VECTOR_SEARCH(
  TABLE `PROJECT_ID.DATASET.vector_search_products`,
  'embedding',
  (SELECT search_term,
    (AI.EMBED(content => search_term, endpoint => 'text-embedding-005',
              task_type => 'RETRIEVAL_QUERY')).result AS embedding
   FROM UNNEST(['audio equipment', 'computer display']) AS search_term),
  top_k => 2,
  distance_type => 'COSINE'
);


-- =============================================================================
-- Example 3: Filtered search (pre-filtering)
-- =============================================================================
-- Pass a subquery instead of TABLE to restrict the search to a subset.
-- Only matching rows are considered for nearest neighbor search.
SELECT base.product, base.category, base.description, distance
FROM VECTOR_SEARCH(
  (SELECT * FROM `PROJECT_ID.DATASET.vector_search_products` WHERE category = 'Computing'),
  'embedding',
  query_value => (AI.EMBED(content => 'display for programming',
                           endpoint => 'text-embedding-005',
                           task_type => 'RETRIEVAL_QUERY')).result,
  top_k => 3,
  distance_type => 'COSINE'
);


-- =============================================================================
-- Example 4: RAG pattern — search then generate
-- =============================================================================
WITH context AS (
  SELECT STRING_AGG(base.product || ': ' || base.description, '; ') AS docs
  FROM VECTOR_SEARCH(
    TABLE `PROJECT_ID.DATASET.vector_search_products`,
    'embedding',
    query_value => (AI.EMBED(content => 'ergonomic office',
                             endpoint => 'text-embedding-005',
                             task_type => 'RETRIEVAL_QUERY')).result,
    top_k => 3, distance_type => 'COSINE'
  )
)
SELECT (AI.GENERATE(
  CONCAT('Based on these products: ', c.docs,
         ' --- Recommend the best for a home office.')
)).result AS recommendation
FROM context c;
