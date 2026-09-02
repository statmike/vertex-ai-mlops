-- VECTOR_SEARCH — Progressive SQL Examples
-- ==========================================
-- Table-valued function for top-K nearest neighbor search on pre-computed embeddings.
-- Supports vector indexes for efficient ANN search.
--
-- Returns: query STRUCT, base STRUCT, distance FLOAT64 (batch)
--          base STRUCT, distance FLOAT64 (single)
--
-- Note: lexical_search_columns + lexical_search_query_value make the search hybrid
--       (semantic fused with keyword). Hybrid requires the single-query form and
--       cannot batch. Under hybrid, distance is a fused rank score, not a distance:
--       1 - ( 1/(60 + rank_vector) + 1/(61 + rank_lexical) ). See example 8.
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
  STRUCT(4, 'Monitor', 'Computing', '32-inch 4K monitor with USB-C connectivity and built-in KVM switch.'),
  STRUCT(5, 'Keyboard', 'Peripherals', 'Mechanical keyboard with programmable keys.'),
  STRUCT(6, 'Dock', 'Computing', 'Thunderbolt 4 docking station with dual 4K display support.')
]);


-- =============================================================================
-- Example 1: Single search (Preview)
-- =============================================================================
-- The single-query form is also the only form that supports hybrid search.
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
-- Batch and hybrid are mutually exclusive: lexical_search_columns is only accepted
-- alongside query_value, so a batch call can never be hybrid. Passing it here fails
-- with "lexical_search_columns is not supported when query_value is not specified."
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
-- Example 3: Using EUCLIDEAN distance
-- =============================================================================
-- Options: COSINE, EUCLIDEAN (default), DOT_PRODUCT.
SELECT base.product, base.description, distance
FROM VECTOR_SEARCH(
  TABLE `PROJECT_ID.DATASET.vector_search_products`,
  'embedding',
  query_value => (AI.EMBED(content => 'typing device', endpoint => 'text-embedding-005',
                           task_type => 'RETRIEVAL_QUERY')).result,
  top_k => 3,
  distance_type => 'EUCLIDEAN'
);


-- =============================================================================
-- Example 4: Filtered search (pre-filtering)
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
-- Example 5: RAG pattern — search then generate
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


-- =============================================================================
-- Example 6: Hybrid search (Preview) — semantic plus keyword
-- =============================================================================
-- A non-empty lexical_search_columns list is what makes the search hybrid, and
-- lexical_search_query_value is required whenever it is set. Both are accepted only
-- with the single-query form (query_value =>) — hybrid cannot batch.
-- The lexical columns need not be the column the embeddings came from, and the
-- lexical query text need not match query_value. No vector index is required.
SELECT base.product, base.category, base.description, distance
FROM VECTOR_SEARCH(
  TABLE `PROJECT_ID.DATASET.vector_search_products`,
  'embedding',
  query_value => (AI.EMBED(content => 'connect two external displays to a laptop',
                           endpoint => 'text-embedding-005',
                           task_type => 'RETRIEVAL_QUERY')).result,
  lexical_search_columns => ['product', 'description'],
  lexical_search_query_value => 'Thunderbolt 4 docking station',
  top_k => 3,
  distance_type => 'COSINE'
);


-- =============================================================================
-- Setup: a larger catalog with part numbers
-- =============================================================================
-- Examples 7 and 8 need a corpus where the semantic leg can plausibly be wrong,
-- and a top_k smaller than the row count. A top_k equal to the row count returns
-- the whole table on both legs, so the two rankings can only be reordered, never
-- differ in membership — the six-row table above can never show a recall change.
-- This catalog holds 24 products, a dense cluster of display-connectivity items
-- among them, plus a sku column carrying manufacturer part codes. The embedding is
-- generated from description only, so the part code never enters the vector: a
-- buyer who knows an exact part number, searching a catalog whose vectors know
-- only prose.
CREATE OR REPLACE TABLE `PROJECT_ID.DATASET.vector_search_catalog` AS
SELECT id, sku, product, description,
  (AI.EMBED(content => description, endpoint => 'text-embedding-005', task_type => 'RETRIEVAL_DOCUMENT')).result AS embedding
FROM UNNEST([
  STRUCT(1 AS id, 'TBT-8841' AS sku, 'Thunderbolt Dock' AS product, 'Thunderbolt 4 docking station with dual 4K display support and 90W laptop charging.' AS description),
  STRUCT(2, 'DCK-2210', 'USB-C Hub', 'Seven-port USB-C hub with HDMI output, card reader, and gigabit ethernet.'),
  STRUCT(3, 'MON-3240', 'Ultrawide Monitor', '32-inch 4K monitor with USB-C connectivity and a built-in KVM switch.'),
  STRUCT(4, 'MON-2711', 'Portable Monitor', '15-inch portable travel monitor powered over a single USB-C cable.'),
  STRUCT(5, 'CBL-4417', 'DisplayPort Cable', 'DisplayPort 2.1 cable rated for 8K at 60Hz, two meters, braided jacket.'),
  STRUCT(6, 'CBL-9032', 'HDMI Splitter', 'One-in two-out HDMI 2.1 splitter that mirrors a source to two screens.'),
  STRUCT(7, 'ADP-5567', 'Display Adapter', 'USB-C to dual HDMI adapter using DisplayLink for extended desktops on any laptop.'),
  STRUCT(8, 'KVM-7788', 'KVM Switch', 'Two-computer KVM switch sharing one keyboard, mouse, and monitor.'),
  STRUCT(9, 'LAP-1120', 'Developer Laptop', 'High-performance laptop with 32GB RAM and NVMe storage for data science.'),
  STRUCT(10, 'KBD-6310', 'Mechanical Keyboard', 'Mechanical keyboard with programmable keys and RGB backlighting.'),
  STRUCT(11, 'MSE-4402', 'Vertical Mouse', 'Ergonomic vertical mouse designed to reduce wrist strain.'),
  STRUCT(12, 'HDS-2077', 'Wireless Headset', 'Wireless noise-cancelling headset with 30-hour battery life.'),
  STRUCT(13, 'CAM-9911', 'Conference Camera', '4K conference camera with auto-framing and beamforming microphones.'),
  STRUCT(14, 'DSK-1450', 'Standing Desk', 'Electric height-adjustable standing desk with memory presets.'),
  STRUCT(15, 'CHR-3390', 'Task Chair', 'Mesh task chair with adjustable lumbar support and 4D armrests.'),
  STRUCT(16, 'ARM-8123', 'Monitor Arm', 'Gas-spring dual monitor arm clamping to desks up to 90mm thick.'),
  STRUCT(17, 'HUB-5540', 'Travel Hub', 'Slim aluminum travel hub with pass-through power, HDMI, and gigabit ethernet.'),
  STRUCT(18, 'PWR-7702', 'GaN Charger', '100W GaN wall charger with two USB-C ports and one USB-A port.'),
  STRUCT(19, 'SSD-6604', 'Portable SSD', 'Two-terabyte portable NVMe SSD in a rugged USB-C enclosure.'),
  STRUCT(20, 'NAS-3318', 'Desktop NAS', 'Four-bay desktop NAS with 2.5 gigabit ethernet and hardware transcoding.'),
  STRUCT(21, 'RTR-2205', 'Mesh Router', 'Tri-band mesh router covering 5,000 square feet with wired backhaul.'),
  STRUCT(22, 'SWT-1180', 'Network Switch', 'Eight-port managed network switch with power over ethernet.'),
  STRUCT(23, 'UPS-4406', 'Battery Backup', 'Line-interactive UPS with 1500VA capacity and pure sine wave output.'),
  STRUCT(24, 'PRN-8890', 'Label Printer', 'Thermal label printer for shipping labels, no ink required.')
]);


-- =============================================================================
-- Example 7: Semantic-only vs hybrid, head to head
-- =============================================================================
-- Same query text, same top_k, run twice. The first call is pure semantic. The
-- second adds lexical_search_columns => ['sku'] and puts an exact part code in
-- lexical_search_query_value — a token the vector leg cannot see, because sku was
-- never embedded.
-- vector_rank_overall ranks the entire 24-row catalog on the vector leg alone, so
-- you can see how deep the part-code row sits before the lexical leg lifts it.
-- The reach of a lexical match is set by top_k: at top_k => 5 it lifts a row from
-- semantic rank 10 at the deepest, and a row below that stays out however exact
-- the token is. Example 8 derives the two gates that set that number.
WITH semantic AS (
  SELECT base.id, ROW_NUMBER() OVER (ORDER BY distance) AS semantic_rank
  FROM VECTOR_SEARCH(
    TABLE `PROJECT_ID.DATASET.vector_search_catalog`,
    'embedding',
    query_value => (AI.EMBED(content => 'run two external monitors from one laptop port',
                             endpoint => 'text-embedding-005',
                             task_type => 'RETRIEVAL_QUERY')).result,
    top_k => 5,
    distance_type => 'COSINE'
  )
),
hybrid AS (
  SELECT base.id, ROW_NUMBER() OVER (ORDER BY distance) AS hybrid_rank
  FROM VECTOR_SEARCH(
    TABLE `PROJECT_ID.DATASET.vector_search_catalog`,
    'embedding',
    query_value => (AI.EMBED(content => 'run two external monitors from one laptop port',
                             endpoint => 'text-embedding-005',
                             task_type => 'RETRIEVAL_QUERY')).result,
    lexical_search_columns => ['sku'],
    lexical_search_query_value => 'DCK-2210',
    top_k => 5,
    distance_type => 'COSINE'
  )
),
whole_catalog AS (
  SELECT base.id, base.sku, base.product,
         ROW_NUMBER() OVER (ORDER BY distance) AS vector_rank_overall
  FROM VECTOR_SEARCH(
    TABLE `PROJECT_ID.DATASET.vector_search_catalog`,
    'embedding',
    query_value => (AI.EMBED(content => 'run two external monitors from one laptop port',
                             endpoint => 'text-embedding-005',
                             task_type => 'RETRIEVAL_QUERY')).result,
    top_k => 24,
    distance_type => 'COSINE'
  )
)
SELECT c.sku, c.product, c.vector_rank_overall, s.semantic_rank, h.hybrid_rank
FROM whole_catalog c
LEFT JOIN semantic s USING (id)
LEFT JOIN hybrid h USING (id)
WHERE s.semantic_rank IS NOT NULL OR h.hybrid_rank IS NOT NULL
ORDER BY h.hybrid_rank NULLS LAST;


-- =============================================================================
-- Example 8: Reading the hybrid score — reciprocal rank fusion
-- =============================================================================
-- Under hybrid, distance is a fused RANK score, not a distance. Every returned
-- value is reproduced from the two integer ranks alone, to within 1e-12:
--   distance = 1 - ( 1/(60 + rank_vector) + 1/(61 + rank_lexical) ), ranks from 1.
-- The two legs do not share a rank base: 60 for the semantic leg, 61 for the
-- lexical leg. The asymmetry is determined, not cosmetic — a row first on the
-- vector leg and second on the lexical leg returns 0.9677335415040333, which is
-- 1 - (1/61 + 1/63). Neither shared base reproduces it:
--
--   reading             expression at rank_vector 1, rank_lexical 2   value
--   60 on both legs     1 - (1/61 + 1/62)                             0.9674775251189847
--   measured (60 / 61)  1 - (1/61 + 1/63)                             0.9677335415040333
--   61 on both legs     1 - (1/62 + 1/63)                             0.9679979518689196
--
-- The returned value falls BETWEEN the two shared-base readings, which is the
-- signature of mixed bases: a single shared base cannot straddle its own
-- prediction. Note that the same arithmetic, 1 - (1/61 + 1/62) =
-- 0.9674775251189847, carries two separate meanings here. In the table it is the
-- shared-base-60 prediction for a rank-1 / rank-2 row, which BigQuery does not
-- return. Under the real law it is the score of a row first on BOTH legs, and
-- that is the best attainable hybrid score, not 0. Hybrid scores cluster just
-- under 1, lower is still better, and they are not comparable to the distances a
-- semantic-only search returns.
--
-- THE LEXICAL LEG RANKS THE ENTIRE CANDIDATE POOL. BigQuery hands BM25 only the top
-- 10 * top_k rows by semantic rank; that pool is all it ever sees. Inside the pool it
-- ranks everything: matches take lexical ranks 1..m and every remaining pooled row
-- falls back to its semantic order behind them, so no pooled row forfeits a term. The
-- rank_lexical_nomatch column below shows it: with a lexical value nothing in the
-- catalog matches, rank_lexical equals rank_vector for every row and the hybrid
-- ordering is exactly the semantic ordering. (top_k => 24 over 24 rows pools 240, so
-- the whole catalog is inside the pool here.)
--
-- A matched row therefore has TWO gates to clear:
--   Gate 1 (candidate pool):  rank_vector <= 10 * top_k
--   Gate 2 (fusion score):    1/(60 + rank_vector) + 1/(61 + rank_lexical)
--                               must beat the row holding the last slot
--
-- Gate 2 is arithmetic: promotion to lexical rank 1 contributes 1/62 ~ 0.0161, while
-- the row holding the last returned slot sits at semantic rank top_k and — pushed down
-- one by the match — lexical rank top_k + 1, scoring 1/(60 + top_k) + 1/(62 + top_k).
-- Gate 1 is a hard ceiling above it: a row deeper than 10 * top_k gets no lexical rank
-- at all, so no score can rescue it. Effective reach is the smaller of the two,
-- min( score reach, 10 * top_k ). The score gate binds below top_k = 51, the pool gate
-- from 51 up.
--
--   top_k                              2  3   5  10  20   30   40   50   51   64    100    208    300
--   deepest semantic rank retrievable  3  6  10  23  56  110  212  468  510  640  1,000  2,080  3,000
--
-- So hybrid re-ranks AND widens: it does pull rows in from outside the semantic top-k,
-- but only in proportion to top_k. At top_k => 64 the reach is semantic rank 640 and no
-- deeper — the pool ends there and rank 641 is invisible to BM25. Measured: a target at
-- semantic rank 3,000 in a 3,000-row table flips in at top_k = 300 exactly (299 returns
-- nothing); at rank 1,500 in a 1,500-row table it flips at 150; at rank 500 in a 500-row
-- table the pool never binds and the score gate sets the flip at 51. All three probe
-- tables sit below the 5,000-row CREATE VECTOR INDEX floor, so they are brute-force
-- scanned and no index exists to restrict anything. The 7,275-row product catalog is
-- the opposite case: it carries a hybrid TREE_AH index with lexical_search_columns,
-- ACTIVE at 100% coverage, and the pool gate shows up there identically. The gate is
-- therefore neither an index artifact nor something an index can avoid.
--
-- Diagnostic signature: a target outside the pool looks exactly like a token matching
-- nothing — rank_lexical equals rank_vector across the whole result set, every distance
-- is 1 - ( 1/(60 + r) + 1/(61 + r) ), and the top of the page reads 0.967478. A page
-- whose best value is 0.967734 had a match fire.
--
-- To retrieve a row at semantic rank R by exact token, top_k >= R/10 is NECESSARY but
-- not SUFFICIENT — it clears the pool gate only. Below R of about 500 the score gate is
-- the binding one and R/10 falls short: a row at semantic rank 100 needs top_k = 29,
-- not 10; at rank 200, 40, not 20; at rank 500, 51, not 50. So size top_k to at least
-- R/10 and above that to whatever the reach table above requires; the two gates cross at
-- top_k = 51. With a small top_k (<= ~30) an exact token only nudges rows already near
-- the top; do not expect recall from it. A 7,275-row catalog makes the cost concrete:
-- with the wanted row at semantic rank 2,072, top_k => 64 returns nothing because the
-- pool reached only 640 rows deep — that row needs top_k >= 208. When the identifier is
-- the entire query and you want certainty, use WHERE sku = @sku — a predicate cannot be
-- outranked by a fusion score, and it has no pool.
--
-- Reverse-engineered, not documented: no Google reference page states the fusion
-- algorithm, no rank or score column is returned, and the constants can change
-- without notice. Production code should treat a hybrid distance as an opaque
-- ordering.
--
-- Below: take rank_vector from a semantic-only pass, subtract its contribution from
-- 1 - distance, invert the remainder to recover the lexical rank, then rebuild the
-- returned score from the two integer ranks. The fusion runs twice — once with the
-- exact part code, once with a token nothing matches.
WITH vector_leg AS (
  SELECT base.id, base.sku, base.product,
         ROW_NUMBER() OVER (ORDER BY distance) AS rank_vector
  FROM VECTOR_SEARCH(
    TABLE `PROJECT_ID.DATASET.vector_search_catalog`,
    'embedding',
    query_value => (AI.EMBED(content => 'run two external monitors from one laptop port',
                             endpoint => 'text-embedding-005',
                             task_type => 'RETRIEVAL_QUERY')).result,
    top_k => 24,
    distance_type => 'COSINE'
  )
),
hybrid_exact AS (
  SELECT base.id, distance AS hybrid_distance
  FROM VECTOR_SEARCH(
    TABLE `PROJECT_ID.DATASET.vector_search_catalog`,
    'embedding',
    query_value => (AI.EMBED(content => 'run two external monitors from one laptop port',
                             endpoint => 'text-embedding-005',
                             task_type => 'RETRIEVAL_QUERY')).result,
    lexical_search_columns => ['sku'],
    lexical_search_query_value => 'DCK-2210',
    top_k => 24,
    distance_type => 'COSINE'
  )
),
hybrid_nomatch AS (
  SELECT base.id, distance AS nomatch_distance
  FROM VECTOR_SEARCH(
    TABLE `PROJECT_ID.DATASET.vector_search_catalog`,
    'embedding',
    query_value => (AI.EMBED(content => 'run two external monitors from one laptop port',
                             endpoint => 'text-embedding-005',
                             task_type => 'RETRIEVAL_QUERY')).result,
    lexical_search_columns => ['sku'],
    lexical_search_query_value => 'NOSUCHTOKEN',
    top_k => 24,
    distance_type => 'COSINE'
  )
),
solved AS (
  SELECT v.sku, v.product, v.rank_vector, h.hybrid_distance,
    CAST(ROUND(1 / ((1 - h.hybrid_distance) - 1 / (60 + v.rank_vector)) - 61) AS INT64) AS rank_lexical,
    CAST(ROUND(1 / ((1 - n.nomatch_distance) - 1 / (60 + v.rank_vector)) - 61) AS INT64) AS rank_lexical_nomatch
  FROM vector_leg v
  JOIN hybrid_exact h USING (id)
  JOIN hybrid_nomatch n USING (id)
)
SELECT sku, product, rank_vector, rank_lexical, rank_lexical_nomatch, hybrid_distance,
       1 - (1 / (60 + rank_vector) + 1 / (61 + rank_lexical)) AS rebuilt_distance,
       ABS(hybrid_distance - (1 - (1 / (60 + rank_vector) + 1 / (61 + rank_lexical)))) < 1e-12 AS formula_holds
FROM solved
ORDER BY rank_vector;


-- =============================================================================
-- Example 9: CREATE VECTOR INDEX for hybrid — accelerating the lexical leg
-- =============================================================================
-- Hybrid search needs no index. An index only speeds up the lexical leg, and lets
-- AI.SEARCH choose hybrid on its own in AUTO mode. Two rules the DDL enforces:
--   1. Every lexical_search_columns entry must also appear in STORING(...), or the
--      statement fails: "Lexical search column product must be in the list of
--      stored columns."
--   2. A lexical column may not also be the index key: "Column product found
--      multiple times in ...". The key is the embedding column.
-- IVF and TREE_AH both support lexical_search_columns. An autonomous-embedding
-- STRUCT<result ARRAY<FLOAT64>, status STRING> column cannot be an index key at all,
-- so such tables need a second table holding the projected ARRAY<FLOAT64>.
-- Left commented out: BigQuery populates a vector index only once the base table
-- reaches 5,000 rows and 10 MB, so the sample table above can never carry one.
-- CREATE VECTOR INDEX vector_search_products_hybrid_index
-- ON `PROJECT_ID.DATASET.vector_search_products`(embedding)
-- STORING (product, description, category)
-- OPTIONS (
--   index_type = 'TREE_AH',
--   distance_type = 'COSINE',
--   lexical_search_columns = ['product', 'description']
-- );
