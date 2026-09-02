-- AI.SEARCH — Progressive SQL Examples
-- ======================================
-- Simplified search for tables with autonomous embedding generation.
-- Embeds the query at runtime — no manual embedding step needed.
-- The mode argument picks the strategy: VECTOR, HYBRID, or AUTO (default).
--
-- AI.SEARCH is GA. Only the mode argument is Preview (verified 2026-09-01).
-- There is no HYBRID_SEARCH function — hybrid retrieval ships as mode here
-- and as lexical_search_columns on VECTOR_SEARCH.
--
-- Returns: base STRUCT (all columns), distance FLOAT64
--   distance — a real distance in VECTOR mode. In HYBRID mode it is a fused
--              rank score, not a distance, and is not comparable to
--              VECTOR-mode distances. See Example 5.
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


-- =============================================================================
-- Example 3: Hybrid search — mode => 'HYBRID' (Preview)
-- =============================================================================
-- Fuses the semantic search with a lexical (keyword) search over the same
-- column named in column_to_search. AI.SEARCH takes no lexical arguments —
-- use VECTOR_SEARCH with lexical_search_columns to search other columns.
-- No vector index is required.
--
-- top_k gates hybrid twice. First the pool: the lexical (BM25) leg is handed
-- only the top 10 * top_k rows by semantic rank, and a row deeper than that
-- gets no lexical rank at all. Then the score: a rank-1 lexical match is worth
-- 1/62 = 0.0161, which has to beat the row holding the last slot. Effective
-- reach is the smaller of the two gates:
--
--   top_k                              2  3  5  10  20   30   40   50   51
--   deepest semantic rank retrievable  3  6 10  23  56  110  212  468  510
--
--   top_k                               64    100    208    300
--   deepest semantic rank retrievable  640  1,000  2,080  3,000
--
-- The score gate binds below top_k = 51; from 51 up the pool binds and reach
-- is simply 10 * top_k. To retrieve a row at semantic rank R by exact token,
-- top_k >= R/10 is necessary but not sufficient: while the score gate binds,
-- R/10 falls short — a target at semantic rank 100 needs top_k = 29, not 10,
-- and one at rank 200 needs top_k 40, not 20. Take R/10 as the floor and
-- read the real requirement off the reach table above; only from top_k = 51
-- up, where the pool gate binds, is R/10 the whole answer. The gate holds
-- with or without a vector index — the same 10 * top_k pool shows on an
-- indexed corpus and on a brute-force-scanned one, so an index neither causes
-- it nor avoids it. Below ~30 a keyword only nudges rows already near the
-- top — expect reordering, not recall. When an identifier is the whole query
-- and the answer must be certain, use WHERE col = @value: a predicate cannot
-- be outranked by a fusion score, and it has no pool.
SELECT base.title, base.content, distance
FROM AI.SEARCH(
  TABLE `PROJECT_ID.DATASET.ai_search_knowledge_base`,
  'content',
  'serverless messaging between services',
  top_k => 3,
  mode => 'HYBRID'
);


-- =============================================================================
-- Example 4: The default — mode => 'AUTO' and its silent fallback
-- =============================================================================
-- AUTO performs a hybrid search only if a hybrid index exists (a vector index
-- created with lexical_search_columns). If none exists it performs a
-- semantic-only search — with no error and no warning. A reader who assumes
-- AUTO means hybrid gets a clean result set that proves nothing.
SELECT base.title, base.content, distance
FROM AI.SEARCH(
  TABLE `PROJECT_ID.DATASET.ai_search_knowledge_base`,
  'content',
  'serverless messaging between services',
  top_k => 3,
  mode => 'AUTO'
);


-- =============================================================================
-- Example 5: mode => 'VECTOR' and the three-way comparison
-- =============================================================================
-- VECTOR forces a semantic-only search. Running all three modes over one query
-- text shows how distance changes meaning:
--   VECTOR — a real distance in the distance_type space, and a self-match
--            is 0.
--   HYBRID — 1 minus a Reciprocal Rank Fusion score over the vector and
--            lexical rank lists, with 1-based ranks:
--              distance = 1 - ( 1/(60 + rank_vector) + 1/(61 + rank_lexical) )
--            Only rank_vector is ever observed, so what this pins is a set of
--            denominators, not a pair of constants: 1/(61 + r) and
--            1/(60 + (r + 1)) are the same number, so k = 60 / k = 61 over
--            1-based ranks and a shared k = 60 with lexical ranks starting at
--            2 fit identically. The latter is likelier — k = 60 over 1-based
--            ranks is canonical RRF and 61 is used as the constant in no
--            published implementation — but the 60/61 form above is the
--            shortest expression that reproduces every observed value.
--            A row first in both lists scores 1 - (1/61 + 1/62) = 0.96747753,
--            the best score attainable. A self-match is ~0.967, never 0, and
--            the value is NOT comparable to a VECTOR-mode distance.
--            The lexical leg ranks the ENTIRE candidate pool — the top
--            10 * top_k rows by semantic rank: BM25 matches take ranks 1..m
--            and every remaining pooled row falls back to its semantic order
--            behind them, so no pooled row is ever missing a term. A row
--            outside the pool gets no lexical rank at all.
--   AUTO   — identical to VECTOR whenever no hybrid index exists.
-- The RRF decomposition is reverse-engineered from observed output, not
-- documented by Google, and can change without notice.
SELECT 'VECTOR' AS search_mode, base.title, distance
FROM AI.SEARCH(
  TABLE `PROJECT_ID.DATASET.ai_search_knowledge_base`,
  'content', 'serverless messaging between services',
  top_k => 3, mode => 'VECTOR'
)
UNION ALL
SELECT 'AUTO', base.title, distance
FROM AI.SEARCH(
  TABLE `PROJECT_ID.DATASET.ai_search_knowledge_base`,
  'content', 'serverless messaging between services',
  top_k => 3, mode => 'AUTO'
)
UNION ALL
SELECT 'HYBRID', base.title, distance
FROM AI.SEARCH(
  TABLE `PROJECT_ID.DATASET.ai_search_knowledge_base`,
  'content', 'serverless messaging between services',
  top_k => 3, mode => 'HYBRID'
)
ORDER BY search_mode, distance;


-- =============================================================================
-- Reference: the hybrid index AUTO looks for — and why it cannot exist here
-- =============================================================================
-- A hybrid index is a vector index created with lexical_search_columns. Every
-- lexical column must also appear in STORING, and no lexical column may be the
-- index key. Illustrative only — not runnable against the table above:
--
-- CREATE VECTOR INDEX kb_hybrid_index
-- ON `PROJECT_ID.DATASET.some_table`(embedding)
-- STORING (content)
-- OPTIONS (index_type = 'IVF', distance_type = 'COSINE',
--          lexical_search_columns = ['content']);
--
-- It cannot be built on an AI.SEARCH base table. Autonomous embedding
-- generation stores its vectors in a generated
-- STRUCT<result ARRAY<FLOAT64>, status STRING> column, and a vector index is
-- not supported on that column:
--   CREATE VECTOR INDEX ... ON tbl(content_embedding)
--   -->  Vector index is not supported on column: 'content_embedding'
-- Nor on a field of it (ON tbl(content_embedding.result) --> "does not yet
-- support expressions to define index keys"), and the generated column cannot
-- be declared as a plain ARRAY<FLOAT64>. The DDL passes a dry run and fails at
-- execution (verified 2026-09-01). A vector index also only populates at
-- 5,000+ rows and 10 MB.
--
-- Consequence: on an AI.SEARCH base table, AUTO is always semantic-only and
-- HYBRID must be requested by name. For an indexed hybrid search, project
-- content_embedding.result into a second table as a plain ARRAY<FLOAT64>
-- column, index that table, and query it with VECTOR_SEARCH.
