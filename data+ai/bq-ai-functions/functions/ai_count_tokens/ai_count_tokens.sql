-- AI.COUNT_TOKENS — Progressive SQL Examples
-- ===========================================
-- Utility scalar function that estimates the INPUT token count of a text
-- prompt. Token counting happens in BigQuery and incurs NO Vertex AI charges.
-- Use it to estimate the cost/size of prompts before calling other AI functions.
--
-- No connection, no CREATE MODEL, no ObjectRef required.
--
-- Signature: AI.COUNT_TOKENS(INPUT [, endpoint => ENDPOINT])
-- Returns: STRUCT<result INT64, full_response JSON>
--   result        — total INPUT token count (NULL if input is NULL or API error)
--   full_response — JSON with per-modality token detail
-- Note: counts INPUT tokens only — not thinking or output tokens.
--
-- Full reference: ../../RESOURCES.md
-- Official docs: https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-count-tokens


-- =============================================================================
-- Example 1: Simplest call — count tokens in a literal string
-- =============================================================================
-- .result is the integer token count. (This returns approximately 11.)
SELECT AI.COUNT_TOKENS("Token count isn't always equal to word count.").result AS num_tokens;


-- =============================================================================
-- Example 2: See the full STRUCT — result + full_response
-- =============================================================================
-- Use .* to return both fields; full_response shows per-modality detail.
SELECT AI.COUNT_TOKENS('Summarize the quarterly earnings report.').*;


-- =============================================================================
-- Example 3: Count tokens over a table column
-- =============================================================================
-- Apply per row to real text data.
SELECT
  review,
  AI.COUNT_TOKENS(review).result AS num_tokens
FROM `bigquery-public-data.imdb.reviews`
LIMIT 5;


-- =============================================================================
-- Example 4: Specify a model endpoint for tokenization rules
-- =============================================================================
-- endpoint selects the model whose tokenizer is used. If omitted, the default
-- model used by AI.GENERATE is used.
SELECT
  review,
  AI.COUNT_TOKENS(review, endpoint => 'gemini-2.5-pro').result AS num_tokens
FROM `bigquery-public-data.imdb.reviews`
LIMIT 5;


-- =============================================================================
-- Example 5: Estimate cost/size before a batch AI job
-- =============================================================================
-- Aggregate token counts across a column to size a prompt workload before
-- running AI.GENERATE / AI.GENERATE_TABLE over it.
WITH counts AS (
  SELECT AI.COUNT_TOKENS(review).result AS tokens
  FROM `bigquery-public-data.imdb.reviews`
  LIMIT 100
)
SELECT
  COUNT(*) AS num_documents,
  SUM(tokens) AS total_input_tokens,
  ROUND(AVG(tokens), 1) AS avg_tokens_per_doc,
  MAX(tokens) AS max_tokens
FROM counts;
