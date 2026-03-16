-- ML.GENERATE_TEXT — Progressive SQL Examples
-- =============================================
-- Legacy predecessor to AI.GENERATE_TEXT.
-- Same capabilities but with ml_generate_text_ column name prefixes.
-- Google recommends AI.GENERATE_TEXT for new queries.
--
-- Key difference: flatten_json_output parameter and column naming.
--
-- Full reference: ../../RESOURCES.md
-- Official docs: https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-generate-text


-- =============================================================================
-- Example 1: Flattened output
-- =============================================================================
SELECT ml_generate_text_llm_result
FROM ML.GENERATE_TEXT(
  MODEL `PROJECT_ID.DATASET.gemini_flash`,
  (SELECT 'What is BigQuery?' AS prompt),
  STRUCT(TRUE AS flatten_json_output)
);


-- =============================================================================
-- Example 2: JSON output (default)
-- =============================================================================
SELECT ml_generate_text_result, ml_generate_text_status
FROM ML.GENERATE_TEXT(
  MODEL `PROJECT_ID.DATASET.gemini_flash`,
  (SELECT 'Write a haiku about SQL.' AS prompt)
);


-- =============================================================================
-- Example 3: With generation parameters
-- =============================================================================
SELECT prompt, ml_generate_text_llm_result AS result
FROM ML.GENERATE_TEXT(
  MODEL `PROJECT_ID.DATASET.gemini_flash`,
  (SELECT CONCAT('What country is ', city, ' in? One word.') AS prompt, city
   FROM UNNEST(['Tokyo', 'Paris', 'Nairobi']) AS city),
  STRUCT(TRUE AS flatten_json_output, 0.0 AS temperature)
);
