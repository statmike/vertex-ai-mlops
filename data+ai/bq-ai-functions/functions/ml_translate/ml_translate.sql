-- ML.TRANSLATE — Progressive SQL Examples
-- ========================================
-- Table-valued function that translates text — or detects its language —
-- by calling the Cloud Translation API through a remote model.
--
-- Requires: Cloud Resource connection whose service account holds
--           roles/serviceusage.serviceUsageConsumer, roles/bigquery.connectionUser
--           and roles/cloudtranslate.user, plus a remote model with
--           REMOTE_SERVICE_TYPE = 'CLOUD_AI_TRANSLATE_V3'
--
-- Input:   a table or query with a column named exactly text_content
-- Returns: the input columns + ml_translate_result (JSON) + ml_translate_status
--          (per-row, empty on success)
--
-- Full reference: ../../RESOURCES.md
-- Official docs: https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-translate


-- =============================================================================
-- Setup: the remote model
-- =============================================================================
-- Nothing trains. The model object records the connection and the service type.
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.ml_translate_model`
  REMOTE WITH CONNECTION `PROJECT_ID.US.CONNECTION_ID`
  OPTIONS (REMOTE_SERVICE_TYPE = 'CLOUD_AI_TRANSLATE_V3');


-- =============================================================================
-- Example 1: DETECT_LANGUAGE — what language is this?
-- =============================================================================
-- No target_language_code in this mode. The source column is aliased to
-- text_content, which is the calling convention for any table without one.
SELECT
  review_id,
  text_content,
  STRING(ml_translate_result.languages[0].language_code) AS detected_language,
  FLOAT64(ml_translate_result.languages[0].confidence) AS confidence,
  ml_translate_status
FROM ML.TRANSLATE(
  MODEL `PROJECT_ID.DATASET.ml_translate_model`,
  (SELECT review_id, comment AS text_content
   FROM `PROJECT_ID.DATASET.ml_translate_reviews`),
  STRUCT('DETECT_LANGUAGE' AS translate_mode)
)
ORDER BY review_id;


-- =============================================================================
-- Example 2: TRANSLATE_TEXT — translate everything to English
-- =============================================================================
-- target_language_code is required in this mode, and the detected source
-- language comes back with the translation.
SELECT
  review_id,
  text_content AS original,
  STRING(ml_translate_result.translations[0].detected_language_code) AS detected,
  STRING(ml_translate_result.translations[0].translated_text) AS english,
  ml_translate_status
FROM ML.TRANSLATE(
  MODEL `PROJECT_ID.DATASET.ml_translate_model`,
  (SELECT review_id, comment AS text_content
   FROM `PROJECT_ID.DATASET.ml_translate_reviews`),
  STRUCT('TRANSLATE_TEXT' AS translate_mode, 'en' AS target_language_code)
)
ORDER BY review_id;


-- =============================================================================
-- Example 3: The text_content rule
-- =============================================================================
-- Passing a table whose text column is named something else fails with:
--   ML.TRANSLATE expects the input table to contain a column named
--   text_content of type STRING.
-- Fix it by aliasing in a subquery (Examples 1 and 2), or by naming the
-- column text_content in the table itself — then TABLE works directly.
SELECT review_id, STRING(ml_translate_result.translations[0].translated_text) AS english
FROM ML.TRANSLATE(
  MODEL `PROJECT_ID.DATASET.ml_translate_model`,
  TABLE `PROJECT_ID.DATASET.ml_translate_text_content`,
  STRUCT('TRANSLATE_TEXT' AS translate_mode, 'en' AS target_language_code)
)
ORDER BY review_id;


-- =============================================================================
-- Example 4: The raw JSON, both modes
-- =============================================================================
-- DETECT_LANGUAGE returns {"languages":[{"confidence":…,"language_code":…}]}
-- TRANSLATE_TEXT returns {"translations":[{"detected_language_code":…,
--                         "translated_text":…}]} plus empty glossary and
-- translation-memory arrays unless those features are in use.
SELECT ml_translate_result
FROM ML.TRANSLATE(
  MODEL `PROJECT_ID.DATASET.ml_translate_model`,
  (SELECT comment AS text_content
   FROM `PROJECT_ID.DATASET.ml_translate_reviews`
   WHERE review_id = 1),
  STRUCT('TRANSLATE_TEXT' AS translate_mode, 'en' AS target_language_code)
);


-- =============================================================================
-- Example 5: One target language per call
-- =============================================================================
-- target_language_code is a scalar evaluated once for the whole call, not per
-- row — a column reference is a compile-time error. Fan out with one call per
-- target and UNION ALL.
SELECT 'es' AS target, review_id,
       STRING(ml_translate_result.translations[0].translated_text) AS translated
FROM ML.TRANSLATE(
  MODEL `PROJECT_ID.DATASET.ml_translate_model`,
  (SELECT review_id, comment AS text_content
   FROM `PROJECT_ID.DATASET.ml_translate_reviews`
   WHERE review_id = 6),
  STRUCT('TRANSLATE_TEXT' AS translate_mode, 'es' AS target_language_code))
UNION ALL
SELECT 'fr', review_id,
       STRING(ml_translate_result.translations[0].translated_text)
FROM ML.TRANSLATE(
  MODEL `PROJECT_ID.DATASET.ml_translate_model`,
  (SELECT review_id, comment AS text_content
   FROM `PROJECT_ID.DATASET.ml_translate_reviews`
   WHERE review_id = 6),
  STRUCT('TRANSLATE_TEXT' AS translate_mode, 'fr' AS target_language_code))
ORDER BY target;


-- =============================================================================
-- Example 6: Round trip — English → Japanese → English
-- =============================================================================
-- Calls nest: the inner result becomes the input relation of the outer call,
-- as long as the inner query aliases its translated column to text_content.
SELECT
  text_content AS japanese,
  STRING(ml_translate_result.translations[0].translated_text) AS back_to_english
FROM ML.TRANSLATE(
  MODEL `PROJECT_ID.DATASET.ml_translate_model`,
  (SELECT STRING(ml_translate_result.translations[0].translated_text) AS text_content
   FROM ML.TRANSLATE(
     MODEL `PROJECT_ID.DATASET.ml_translate_model`,
     (SELECT comment AS text_content
      FROM `PROJECT_ID.DATASET.ml_translate_reviews`
      WHERE review_id = 6),
     STRUCT('TRANSLATE_TEXT' AS translate_mode, 'ja' AS target_language_code))),
  STRUCT('TRANSLATE_TEXT' AS translate_mode, 'en' AS target_language_code));


-- =============================================================================
-- Example 7: Side by side with AI.GENERATE
-- =============================================================================
-- The same job through the Translation API and through an LLM.
-- AI.GENERATE through this connection also needs roles/aiplatform.user.
WITH api AS (
  SELECT review_id, text_content AS original,
         STRING(ml_translate_result.translations[0].translated_text) AS translation_api
  FROM ML.TRANSLATE(
    MODEL `PROJECT_ID.DATASET.ml_translate_model`,
    (SELECT review_id, comment AS text_content
     FROM `PROJECT_ID.DATASET.ml_translate_reviews`),
    STRUCT('TRANSLATE_TEXT' AS translate_mode, 'en' AS target_language_code))
),
llm AS (
  SELECT review_id,
         AI.GENERATE(
           ('Translate this product review to English. Return only the translation: ', comment)
         ).result AS gemini
  FROM `PROJECT_ID.DATASET.ml_translate_reviews`
)
SELECT api.review_id, api.original, api.translation_api, llm.gemini
FROM api JOIN llm USING (review_id)
ORDER BY review_id;


-- =============================================================================
-- Example 8: Reprocess rows that failed
-- =============================================================================
-- ml_translate_status is per row: the job can succeed while individual rows
-- carry an error (the documented RESOURCE EXHAUSTED case). Feed those rows back.
SELECT
  review_id,
  STRING(ml_translate_result.translations[0].translated_text) AS english,
  ml_translate_status
FROM ML.TRANSLATE(
  MODEL `PROJECT_ID.DATASET.ml_translate_model`,
  (SELECT review_id, original AS text_content
   FROM `PROJECT_ID.DATASET.ml_translate_results`
   WHERE ml_translate_status != ''),
  STRUCT('TRANSLATE_TEXT' AS translate_mode, 'en' AS target_language_code))
ORDER BY review_id;
