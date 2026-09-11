-- ML.UNDERSTAND_TEXT — Progressive SQL Examples
-- ==============================================
-- Table-valued function that analyzes text with the Cloud Natural Language
-- API through a remote model. One model, five analyses, selected by the
-- nlu_option argument.
--
-- Requires: Cloud Resource connection whose service account holds
--           roles/serviceusage.serviceUsageConsumer and
--           roles/bigquery.connectionUser, plus a remote model with
--           REMOTE_SERVICE_TYPE = 'CLOUD_AI_NATURAL_LANGUAGE_V1'
--
-- Input:   a table or query with a column named exactly text_content
-- Returns: the input columns + ml_understand_text_result (JSON) +
--          ml_understand_text_status (per-row, empty on success)
--
-- Full reference: ../../RESOURCES.md
-- Official docs: https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-understand-text


-- =============================================================================
-- Setup: the remote model
-- =============================================================================
-- Nothing trains. One model serves all five analyses.
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.ml_understand_text_model`
  REMOTE WITH CONNECTION `PROJECT_ID.US.CONNECTION_ID`
  OPTIONS (REMOTE_SERVICE_TYPE = 'CLOUD_AI_NATURAL_LANGUAGE_V1');


-- =============================================================================
-- Example 1: ANALYZE_SENTIMENT — score and magnitude
-- =============================================================================
-- score runs -1 to 1 (direction); magnitude is unbounded (how much emotion,
-- regardless of direction). The source column is aliased to text_content.
SELECT
  feedback_id,
  text_content,
  STRING(ml_understand_text_result.language) AS detected_language,
  FLOAT64(ml_understand_text_result.document_sentiment.score) AS score,
  FLOAT64(ml_understand_text_result.document_sentiment.magnitude) AS magnitude,
  ml_understand_text_status
FROM ML.UNDERSTAND_TEXT(
  MODEL `PROJECT_ID.DATASET.ml_understand_text_model`,
  (SELECT feedback_id, body AS text_content
   FROM `PROJECT_ID.DATASET.ml_understand_text_feedback`),
  STRUCT('ANALYZE_SENTIMENT' AS nlu_option)
)
ORDER BY feedback_id;


-- =============================================================================
-- Example 2: flatten_json_output — let the function unpack the top level
-- =============================================================================
-- The column set depends on the analysis: ANALYZE_SENTIMENT returns
-- sentiment/language/sentences, CLASSIFY_TEXT returns categories. Nested
-- content is still JSON — flattening replaces the top-level accessor, not
-- the UNNEST.
SELECT feedback_id, language, sentiment, sentences
FROM ML.UNDERSTAND_TEXT(
  MODEL `PROJECT_ID.DATASET.ml_understand_text_model`,
  (SELECT feedback_id, body AS text_content
   FROM `PROJECT_ID.DATASET.ml_understand_text_feedback`),
  STRUCT('ANALYZE_SENTIMENT' AS nlu_option, TRUE AS flatten_json_output)
)
ORDER BY feedback_id;


-- =============================================================================
-- Example 3: ANALYZE_ENTITIES — one row per thing mentioned
-- =============================================================================
-- salience is how central the entity is to the document, summing to about 1
-- across a document's entities. Entity types are the model's guess from
-- context, not a registry lookup.
SELECT
  feedback_id,
  STRING(entity.name) AS entity,
  STRING(entity.type) AS entity_type,
  ROUND(FLOAT64(entity.salience), 3) AS salience
FROM ML.UNDERSTAND_TEXT(
  MODEL `PROJECT_ID.DATASET.ml_understand_text_model`,
  (SELECT feedback_id, body AS text_content
   FROM `PROJECT_ID.DATASET.ml_understand_text_feedback`),
  STRUCT('ANALYZE_ENTITIES' AS nlu_option)
),
UNNEST(JSON_QUERY_ARRAY(ml_understand_text_result.entities)) AS entity
ORDER BY feedback_id, salience DESC;


-- =============================================================================
-- Example 4: ANALYZE_ENTITY_SENTIMENT — per-entity sentiment, per-row status
-- =============================================================================
-- Entity sentiment supports fewer languages than sentiment analysis does.
-- Unsupported rows come back empty with an error string while the job
-- succeeds — always select the status column.
SELECT
  feedback_id,
  ml_understand_text_status,
  ARRAY_LENGTH(JSON_QUERY_ARRAY(ml_understand_text_result.entities)) AS entity_count
FROM ML.UNDERSTAND_TEXT(
  MODEL `PROJECT_ID.DATASET.ml_understand_text_model`,
  (SELECT feedback_id, body AS text_content
   FROM `PROJECT_ID.DATASET.ml_understand_text_feedback`),
  STRUCT('ANALYZE_ENTITY_SENTIMENT' AS nlu_option)
)
ORDER BY feedback_id;

SELECT
  feedback_id,
  STRING(entity.name) AS entity,
  ROUND(FLOAT64(entity.sentiment.score), 2) AS entity_score,
  ROUND(FLOAT64(entity.sentiment.magnitude), 2) AS entity_magnitude
FROM ML.UNDERSTAND_TEXT(
  MODEL `PROJECT_ID.DATASET.ml_understand_text_model`,
  (SELECT feedback_id, body AS text_content
   FROM `PROJECT_ID.DATASET.ml_understand_text_feedback`),
  STRUCT('ANALYZE_ENTITY_SENTIMENT' AS nlu_option)
),
UNNEST(JSON_QUERY_ARRAY(ml_understand_text_result.entities)) AS entity
ORDER BY feedback_id, entity_score;


-- =============================================================================
-- Example 5: ANALYZE_SYNTAX — tokens, parts of speech, dependencies
-- =============================================================================
-- head_token_index points at the token this one attaches to, so the sentence
-- structure is recoverable.
SELECT
  STRING(token.text.content) AS token,
  STRING(token.part_of_speech.tag) AS part_of_speech,
  STRING(token.lemma) AS lemma,
  STRING(token.dependency_edge.label) AS dependency,
  INT64(token.dependency_edge.head_token_index) AS head_index
FROM ML.UNDERSTAND_TEXT(
  MODEL `PROJECT_ID.DATASET.ml_understand_text_model`,
  (SELECT body AS text_content
   FROM `PROJECT_ID.DATASET.ml_understand_text_feedback`
   WHERE feedback_id = 1),
  STRUCT('ANALYZE_SYNTAX' AS nlu_option)
),
UNNEST(JSON_QUERY_ARRAY(ml_understand_text_result.tokens)) AS token;


-- =============================================================================
-- Example 6: CLASSIFY_TEXT — categories from a fixed taxonomy
-- =============================================================================
-- Several categories can come back per document, ordered by confidence.
-- CLASSIFY_TEXT is the one analysis that rejects encoding_type.
SELECT
  feedback_id,
  STRING(category.name) AS category,
  ROUND(FLOAT64(category.confidence), 3) AS confidence
FROM ML.UNDERSTAND_TEXT(
  MODEL `PROJECT_ID.DATASET.ml_understand_text_model`,
  (SELECT feedback_id, body AS text_content
   FROM `PROJECT_ID.DATASET.ml_understand_text_feedback`),
  STRUCT('CLASSIFY_TEXT' AS nlu_option)
),
UNNEST(JSON_QUERY_ARRAY(ml_understand_text_result.categories)) AS category
ORDER BY feedback_id, confidence DESC;


-- =============================================================================
-- Example 7: encoding_type — the option that turns offsets on
-- =============================================================================
-- The default (NONE) returns begin_offset = -1: not computed. Ask for an
-- encoding and offsets are reported in that encoding's units — UTF8 counts
-- bytes, UTF16/UTF32 count code units, so accented text diverges.
SELECT
  STRING(entity.name) AS entity,
  INT64(entity.mentions[0].text.begin_offset) AS begin_offset
FROM ML.UNDERSTAND_TEXT(
  MODEL `PROJECT_ID.DATASET.ml_understand_text_model`,
  (SELECT body AS text_content
   FROM `PROJECT_ID.DATASET.ml_understand_text_feedback`
   WHERE feedback_id = 3),
  STRUCT('ANALYZE_ENTITIES' AS nlu_option, 'UTF8' AS encoding_type)
),
UNNEST(JSON_QUERY_ARRAY(ml_understand_text_result.entities)) AS entity;


-- =============================================================================
-- Example 8: Reprocess rows that failed
-- =============================================================================
-- Per-row failures — an unsupported language, or the documented
-- RESOURCE EXHAUSTED case — are selected back out and called again.
CREATE OR REPLACE TABLE `PROJECT_ID.DATASET.ml_understand_text_results` AS
SELECT
  feedback_id,
  text_content,
  ml_understand_text_result,
  ml_understand_text_status
FROM ML.UNDERSTAND_TEXT(
  MODEL `PROJECT_ID.DATASET.ml_understand_text_model`,
  (SELECT feedback_id, body AS text_content
   FROM `PROJECT_ID.DATASET.ml_understand_text_feedback`),
  STRUCT('ANALYZE_ENTITY_SENTIMENT' AS nlu_option)
);

SELECT
  feedback_id,
  ml_understand_text_result,
  ml_understand_text_status
FROM ML.UNDERSTAND_TEXT(
  MODEL `PROJECT_ID.DATASET.ml_understand_text_model`,
  (SELECT feedback_id, text_content
   FROM `PROJECT_ID.DATASET.ml_understand_text_results`
   WHERE ml_understand_text_status != ''),
  STRUCT('ANALYZE_ENTITY_SENTIMENT' AS nlu_option)
)
ORDER BY feedback_id;
