-- AI.GENERATE_TEXT — Progressive SQL Examples
-- =============================================
-- Table-valued function that generates text using a remote model.
-- Supports Gemini, Claude, Llama, Mistral, and open models.
-- Supports multimodal input via ObjectRef (documents, images, video).
-- Requires CREATE MODEL first.
--
-- Returns: input columns + result, full_response, status, rai_result, grounding_result, statistics
--
-- Full reference: ../../RESOURCES.md
-- Official docs: https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-generate-text


-- =============================================================================
-- Example 1: Simplest call — single prompt
-- =============================================================================
-- Input must have a `prompt` column. Returns all input columns plus result.
SELECT result
FROM AI.GENERATE_TEXT(
  MODEL `PROJECT_ID.DATASET.gemini_flash`,
  (SELECT 'What is BigQuery?' AS prompt)
);


-- =============================================================================
-- Example 2: Processing multiple rows
-- =============================================================================
SELECT city, result
FROM AI.GENERATE_TEXT(
  MODEL `PROJECT_ID.DATASET.gemini_flash`,
  (SELECT CONCAT('What country is ', city, ' in? Answer in one word.') AS prompt, city
   FROM UNNEST(['Tokyo', 'Paris', 'Nairobi']) AS city)
);


-- =============================================================================
-- Example 3: Controlling generation parameters
-- =============================================================================
-- Pass parameters as named arguments in a STRUCT.
SELECT result
FROM AI.GENERATE_TEXT(
  MODEL `PROJECT_ID.DATASET.gemini_flash`,
  (SELECT 'Write a haiku about cloud computing.' AS prompt),
  STRUCT(0.8 AS temperature, 100 AS max_output_tokens)
);


-- =============================================================================
-- Example 4: Google Search grounding
-- =============================================================================
SELECT result
FROM AI.GENERATE_TEXT(
  MODEL `PROJECT_ID.DATASET.gemini_flash`,
  (SELECT 'What is the current population of Tokyo?' AS prompt),
  STRUCT(TRUE AS ground_with_google_search)
);


-- =============================================================================
-- Example 5: Safety settings
-- =============================================================================
SELECT result
FROM AI.GENERATE_TEXT(
  MODEL `PROJECT_ID.DATASET.gemini_flash`,
  (SELECT 'Explain the science of fireworks.' AS prompt),
  STRUCT(
    [STRUCT('HARM_CATEGORY_DANGEROUS_CONTENT' AS category, 'BLOCK_ONLY_HIGH' AS threshold)] AS safety_settings
  )
);


-- =============================================================================
-- Example 6: Using model_params (JSON)
-- =============================================================================
-- model_params cannot be used simultaneously with top-level params.
SELECT result
FROM AI.GENERATE_TEXT(
  MODEL `PROJECT_ID.DATASET.gemini_flash`,
  (SELECT 'What is the sum of all prime numbers less than 20?' AS prompt),
  STRUCT(JSON '{"generation_config": {"thinking_config": {"thinking_budget": 1024}}}' AS model_params)
);


-- =============================================================================
-- Example 7: Processing table data at scale
-- =============================================================================
WITH reviews AS (
  SELECT *
  FROM UNNEST([
    STRUCT('r1' AS id, 'Amazing product, fast delivery!' AS review),
    STRUCT('r2', 'Terrible quality. Broke after one day.'),
    STRUCT('r3', 'Average product, nothing special.'),
    STRUCT('r4', 'Great value for the price!')
  ])
)
SELECT id, review, result AS sentiment
FROM AI.GENERATE_TEXT(
  MODEL `PROJECT_ID.DATASET.gemini_flash`,
  (SELECT id, review,
   CONCAT('Classify this review as positive, negative, or neutral. Return only the label: ', review) AS prompt
   FROM reviews)
);


-- =============================================================================
-- Example 8: Summarize a document (ObjectRef)
-- =============================================================================
-- Pass a document via ObjectRef using a STRUCT prompt.
-- Requires: Cloud resource connection with roles/storage.objectViewer
SELECT result
FROM AI.GENERATE_TEXT(
  MODEL `PROJECT_ID.DATASET.gemini_flash`,
  (SELECT STRUCT(
    'Summarize this document in 2-3 sentences.' AS prompt,
    [OBJ.GET_ACCESS_URL(
      OBJ.FETCH_METADATA(
        OBJ.MAKE_REF(
          'gs://BUCKET/path/to/invoice.pdf',
          'PROJECT_ID.LOCATION.CONNECTION_ID'
        )
      ), 'r'
    )] AS object_ref_runtime
  ) AS prompt)
);
