-- Text — Progressive SQL Examples (BigQuery ML model-free functions)
-- =============================================================
-- Three functions that turn tokenized text (ARRAY<STRING>) into ML features:
-- ML.NGRAMS (scalar, builds n-grams from tokens), ML.TF_IDF and
-- ML.BAG_OF_WORDS (both analytic -- require OVER(), build a dictionary
-- across the whole document window). ML.TF_IDF/ML.BAG_OF_WORDS had NO
-- example anywhere in this repo before this notebook.
--
-- GOTCHA: GoogleSQL also has same-named non-ML text-analysis functions
-- (TF_IDF, BAG_OF_WORDS) with DIFFERENT semantics (term-string dictionary
-- index, frequency-ordered). The ML.* versions here use integer dictionary
-- indices, order the dictionary alphabetically, and reserve index 0 for
-- the unknown term. Always call them as ML.TF_IDF / ML.BAG_OF_WORDS.
--
-- Data: bigquery-public-data.thelook_ecommerce.products.name (short, real
--       product-name strings; also used in workflows/embeddings_classification/)
--
-- Full reference: ../../RESOURCES.md
-- Official docs:
--   ML.NGRAMS:       https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ngrams
--   ML.TF_IDF:        https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-tf-idf
--   ML.BAG_OF_WORDS:  https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-bag-of-words


-- =============================================================================
-- Example 1: Tokenize first -- all three functions operate on ARRAY<STRING>
-- =============================================================================
SELECT name, SPLIT(LOWER(name), ' ') AS tokens
FROM `bigquery-public-data.thelook_ecommerce.products`
LIMIT 3;


-- =============================================================================
-- Example 2: ML.NGRAMS -- scalar, builds n-grams within a size range
-- =============================================================================
SELECT tokens, ML.NGRAMS(tokens, [2, 3]) AS bigrams_trigrams
FROM (SELECT SPLIT(LOWER('Low Profile Dyed Cotton Cap'), ' ') AS tokens);


-- =============================================================================
-- Example 3: ML.BAG_OF_WORDS and ML.TF_IDF on real product-name tokens
-- =============================================================================
WITH docs AS (
  SELECT id, SPLIT(LOWER(REGEXP_REPLACE(name, r'[^a-zA-Z0-9 ]', ' ')), ' ') AS tokens
  FROM `bigquery-public-data.thelook_ecommerce.products`
  WHERE category = 'Accessories'
  LIMIT 500
)
SELECT id, tokens,
  ML.BAG_OF_WORDS(tokens) OVER() AS bow_default,
  ML.TF_IDF(tokens) OVER() AS tfidf_default
FROM docs
LIMIT 5;


-- =============================================================================
-- Example 4: MAJOR GOTCHA (verified live, first time tested anywhere in this
-- repo) -- ML.TF_IDF/ML.BAG_OF_WORDS share the SAME frequency_threshold=5
-- default gotcha already found for the encoders (functions/encoding/)
-- =============================================================================
-- 6 tiny "documents", each with 'common_word' (appears in all 6, >=5) plus
-- one other word that appears in only 1-2 documents (<5).
WITH docs AS (
  SELECT * FROM UNNEST([
    STRUCT(1 AS doc_id, ['common_word', 'apple'] AS tokens),
    STRUCT(2 AS doc_id, ['common_word', 'banana'] AS tokens),
    STRUCT(3 AS doc_id, ['common_word', 'rare_word'] AS tokens),
    STRUCT(4 AS doc_id, ['common_word', 'cherry'] AS tokens),
    STRUCT(5 AS doc_id, ['common_word', 'date'] AS tokens),
    STRUCT(6 AS doc_id, ['common_word', 'rare_word'] AS tokens)
  ])
)
SELECT doc_id, tokens,
  ML.BAG_OF_WORDS(tokens) OVER() AS bow_default_freq5,          -- only 'common_word' survives
  ML.BAG_OF_WORDS(tokens, 100, 1) OVER() AS bow_freqthresh1     -- every word gets its own index
FROM docs
ORDER BY doc_id;
-- Verified: under the default frequency_threshold=5, EVERY word except
-- 'common_word' collapses to index 0 -- even 'rare_word', which appears
-- in 2 different documents, is indistinguishable from 'apple' (1
-- occurrence) or the unknown/unseen term. With frequency_threshold=1, all
-- 6 distinct words get their own index. Same practical consequence as the
-- encoder gotcha in functions/encoding/: on a small corpus, almost
-- everything except the most common terms silently disappears by default.


-- =============================================================================
-- Example 5: Embedded in a real CREATE MODEL TRANSFORM -- text classification
-- =============================================================================
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.text_downstream_logistic_regression`
TRANSFORM(
  category,
  ML.BAG_OF_WORDS(SPLIT(LOWER(REGEXP_REPLACE(name, r'[^a-zA-Z0-9 ]', ' ')), ' '), 200, 3) OVER() AS name_bow
)
OPTIONS(model_type = 'LOGISTIC_REG', input_label_cols = ['category']) AS
SELECT category, name
FROM `bigquery-public-data.thelook_ecommerce.products`
WHERE category IN ('Accessories', 'Jeans');

-- Verified accuracy ~0.95 -- bag-of-words features from the product name
-- alone strongly separate these two categories.
SELECT * FROM ML.EVALUATE(MODEL `PROJECT_ID.DATASET.text_downstream_logistic_regression`);


-- =============================================================================
-- Cleanup
-- =============================================================================
-- DROP MODEL IF EXISTS `PROJECT_ID.DATASET.text_downstream_logistic_regression`;
