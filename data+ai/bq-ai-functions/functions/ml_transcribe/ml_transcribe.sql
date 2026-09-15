-- ML.TRANSCRIBE — Progressive SQL Examples
-- ========================================
-- Table-valued function that transcribes audio with the Speech-to-Text V2 API
-- through a remote model. Unlike the other Cloud AI service models it returns
-- the finished text in a STRING column, and its third argument is a named
-- argument (recognition_config => JSON) rather than a STRUCT.
--
-- Requires: Cloud Resource connection whose service account holds
--           roles/serviceusage.serviceUsageConsumer,
--           roles/bigquery.connectionUser, roles/storage.objectViewer and
--           roles/speech.client, plus a remote model with
--           REMOTE_SERVICE_TYPE = 'CLOUD_AI_SPEECH_TO_TEXT_V2'
--
-- Input:   an object table over audio files in Cloud Storage
-- Returns: the object table columns + transcripts (STRING) +
--          ml_transcribe_result (JSON) + ml_transcribe_status (per-row,
--          empty on success)
--
-- Full reference: ../../RESOURCES.md
-- Official docs: https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-transcribe


-- =============================================================================
-- Setup: the object tables and the remote model
-- =============================================================================
-- Audio only.
CREATE OR REPLACE EXTERNAL TABLE `PROJECT_ID.DATASET.ml_transcribe_audio`
  WITH CONNECTION `PROJECT_ID.US.CONNECTION_ID`
  OPTIONS (
    object_metadata = 'SIMPLE',
    uris = ['gs://BUCKET/bq_ai_functions/ml_transcribe/audio/*']
  );

-- Audio plus one file that is not audio — Example 7.
CREATE OR REPLACE EXTERNAL TABLE `PROJECT_ID.DATASET.ml_transcribe_mixed`
  WITH CONNECTION `PROJECT_ID.US.CONNECTION_ID`
  OPTIONS (
    object_metadata = 'SIMPLE',
    uris = [
      'gs://BUCKET/bq_ai_functions/ml_transcribe/audio/*',
      'gs://BUCKET/bq_ai_functions/ml_transcribe/other/*'
    ]
  );

-- Nothing trains. Leaving SPEECH_RECOGNIZER off means the model uses the
-- default recognizer, which stores no configuration — which is why every call
-- below carries a recognition_config. A recognizer is a regional resource and
-- BigQuery accepts it only from asia-southeast1, us-central1 or europe-west4.
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.ml_transcribe_model`
  REMOTE WITH CONNECTION `PROJECT_ID.US.CONNECTION_ID`
  OPTIONS (REMOTE_SERVICE_TYPE = 'CLOUD_AI_SPEECH_TO_TEXT_V2');


-- =============================================================================
-- Example 1: the whole point — a STRING column
-- =============================================================================
-- transcripts is the finished text. No JSON accessor, no UNNEST. Always select
-- ml_transcribe_status with it: failures are per row, not per job.
SELECT
  REGEXP_EXTRACT(uri, r'[^/]+$') AS audio_file,
  transcripts,
  ml_transcribe_status
FROM ML.TRANSCRIBE(
  MODEL `PROJECT_ID.DATASET.ml_transcribe_model`,
  TABLE `PROJECT_ID.DATASET.ml_transcribe_audio`,
  recognition_config => JSON '{"language_codes": ["en-US"], "model": "chirp", "auto_decoding_config": {}}'
)
ORDER BY audio_file;


-- =============================================================================
-- Example 2: the argument is named, and it is required
-- =============================================================================
-- Both of these fail. Kept as comments because they are the two mistakes the
-- signature invites:
--
--   -- "The recognition_config must be specified in ML.TRANSCRIBE when the
--   --  model uses default speech recognizer."
--   SELECT transcripts FROM ML.TRANSCRIBE(
--     MODEL `PROJECT_ID.DATASET.ml_transcribe_model`,
--     TABLE `PROJECT_ID.DATASET.ml_transcribe_audio`);
--
--   -- "No matching signature ... Signature: ML.TRANSCRIBE(MODEL, TABLE,
--   --  [recognition_config => JSON])" — the other four members of this family
--   --  take a STRUCT; this one does not.
--   SELECT transcripts FROM ML.TRANSCRIBE(
--     MODEL `PROJECT_ID.DATASET.ml_transcribe_model`,
--     TABLE `PROJECT_ID.DATASET.ml_transcribe_audio`,
--     STRUCT(JSON '{"language_codes": ["en-US"], "model": "chirp"}' AS recognition_config));


-- =============================================================================
-- Example 3: the config — chirp is the only accepted model
-- =============================================================================
-- chirp_2, long, short and telephony are all rejected with "The model
-- specified in recognition_config <name> is not supported. Supported models
-- are: chirp."
SELECT
  REGEXP_EXTRACT(uri, r'[^/]+$') AS audio_file,
  transcripts
FROM ML.TRANSCRIBE(
  MODEL `PROJECT_ID.DATASET.ml_transcribe_model`,
  (SELECT * FROM `PROJECT_ID.DATASET.ml_transcribe_audio` WHERE uri LIKE '%hello%'),
  recognition_config => JSON '{"language_codes": ["en-US"], "model": "chirp", "auto_decoding_config": {}}'
);


-- =============================================================================
-- Example 4: inside ml_transcribe_result
-- =============================================================================
-- results is an object keyed by the file's own URI, so the accessor indexes it
-- with the row's uri column. transcript and inline_result.transcript hold the
-- same object; total_billed_duration is reported under metadata and again at
-- the top of the result. Long audio arrives as several segments and the
-- transcripts column is their concatenation — taking results[0] truncates it.
SELECT
  REGEXP_EXTRACT(uri, r'[^/]+$') AS audio_file,
  ARRAY_LENGTH(JSON_QUERY_ARRAY(ml_transcribe_result.results[uri].transcript.results)) AS segments,
  STRING(ml_transcribe_result.results[uri].transcript.results[0].language_code) AS language_code,
  STRING(ml_transcribe_result.results[uri].metadata.total_billed_duration) AS billed,
  transcripts = ARRAY_TO_STRING(ARRAY(
    SELECT STRING(segment.alternatives[0].transcript)
    FROM UNNEST(JSON_QUERY_ARRAY(ml_transcribe_result.results[uri].transcript.results)) AS segment
  ), '') AS concatenation_matches
FROM ML.TRANSCRIBE(
  MODEL `PROJECT_ID.DATASET.ml_transcribe_model`,
  TABLE `PROJECT_ID.DATASET.ml_transcribe_audio`,
  recognition_config => JSON '{"language_codes": ["en-US"], "model": "chirp", "auto_decoding_config": {}}'
)
ORDER BY segments DESC, audio_file;


-- =============================================================================
-- Example 5: language_codes are echoed, "auto" detects
-- =============================================================================
-- A fixed code is not enforced: French audio sent with ["en-US"] still comes
-- back in French, with en-US reported. ["auto"] reports bare subtags (fr, es,
-- en) instead. Store which mode produced the column.
SELECT
  REGEXP_EXTRACT(uri, r'[^/]+$') AS audio_file,
  STRING(ml_transcribe_result.results[uri].transcript.results[0].language_code) AS reported,
  transcripts
FROM ML.TRANSCRIBE(
  MODEL `PROJECT_ID.DATASET.ml_transcribe_model`,
  TABLE `PROJECT_ID.DATASET.ml_transcribe_audio`,
  recognition_config => JSON '{"language_codes": ["auto"], "model": "chirp", "auto_decoding_config": {}}'
)
ORDER BY audio_file;


-- =============================================================================
-- Example 6: features — and one unsupported key voids the row
-- =============================================================================
-- enable_automatic_punctuation and enable_word_time_offsets work.
-- enable_word_confidence, diarization_config and profanity_filter each fail
-- the whole row with "INVALID_ARGUMENT: Config contains unsupported fields",
-- naming no field — the job still succeeds, transcripts comes back empty.
-- Word offsets give a start and an end for every word.
SELECT
  STRING(w.word) AS word,
  STRING(w.start_offset) AS start_offset,
  STRING(w.end_offset) AS end_offset
FROM ML.TRANSCRIBE(
  MODEL `PROJECT_ID.DATASET.ml_transcribe_model`,
  (SELECT * FROM `PROJECT_ID.DATASET.ml_transcribe_audio` WHERE uri LIKE '%brooklyn%'),
  recognition_config => JSON '{"language_codes": ["en-US"], "model": "chirp", "auto_decoding_config": {}, "features": {"enable_automatic_punctuation": true, "enable_word_time_offsets": true}}'
) AS transcribed,
UNNEST(JSON_QUERY_ARRAY(
  transcribed.ml_transcribe_result.results[transcribed.uri].transcript.results[0].alternatives[0].words
)) AS w;


-- =============================================================================
-- Example 7: a row that cannot be transcribed, and the retry pattern
-- =============================================================================
-- A non-audio object in the object table produces "INVALID_ARGUMENT: Audio
-- data does not appear to be in a supported encoding" in ml_transcribe_status
-- while the job succeeds. Persist, then re-run only the failures.
CREATE OR REPLACE TABLE `PROJECT_ID.DATASET.ml_transcribe_results` AS
SELECT uri, content_type, transcripts, ml_transcribe_status
FROM ML.TRANSCRIBE(
  MODEL `PROJECT_ID.DATASET.ml_transcribe_model`,
  TABLE `PROJECT_ID.DATASET.ml_transcribe_mixed`,
  recognition_config => JSON '{"language_codes": ["en-US"], "model": "chirp", "auto_decoding_config": {}}'
);

SELECT REGEXP_EXTRACT(uri, r'[^/]+$') AS file, ml_transcribe_status
FROM `PROJECT_ID.DATASET.ml_transcribe_results`
WHERE ml_transcribe_status != '';


-- =============================================================================
-- Example 8: billing follows audio seconds, not bytes
-- =============================================================================
-- total_billed_duration has nothing to do with file size — the codecs differ
-- by more than an order of magnitude in bytes per second of audio. Estimate a
-- transcription bill from duration.
SELECT
  REGEXP_EXTRACT(uri, r'[^/]+$') AS audio_file,
  content_type,
  size AS bytes,
  CAST(REGEXP_EXTRACT(
    STRING(ml_transcribe_result.results[uri].metadata.total_billed_duration), r'^([0-9.]+)s$'
  ) AS FLOAT64) AS billed_seconds
FROM ML.TRANSCRIBE(
  MODEL `PROJECT_ID.DATASET.ml_transcribe_model`,
  TABLE `PROJECT_ID.DATASET.ml_transcribe_audio`,
  recognition_config => JSON '{"language_codes": ["en-US"], "model": "chirp", "auto_decoding_config": {}}'
)
ORDER BY billed_seconds DESC;


-- =============================================================================
-- Example 9: AI.GENERATE over the same audio
-- =============================================================================
-- Gemini reads audio through an ObjectRef and returns capitalized, punctuated
-- text — and will answer questions ML.TRANSCRIBE refuses, such as speaker
-- count, with no status column and no confidence beside the answer.
-- AI.GENERATE through this connection also needs roles/aiplatform.user.
WITH transcribed AS (
  SELECT REGEXP_EXTRACT(uri, r'[^/]+$') AS audio_file, uri, transcripts
  FROM ML.TRANSCRIBE(
    MODEL `PROJECT_ID.DATASET.ml_transcribe_model`,
    TABLE `PROJECT_ID.DATASET.ml_transcribe_audio`,
    recognition_config => JSON '{"language_codes": ["en-US"], "model": "chirp", "auto_decoding_config": {}}')
)
SELECT
  audio_file,
  transcripts AS ml_transcribe,
  AI.GENERATE(STRUCT(
    'Transcribe this audio. Return only the words spoken.' AS prompt,
    [OBJ.MAKE_REF(uri, 'PROJECT_ID.US.CONNECTION_ID')
    ] AS object_refs)).result AS ai_generate
FROM transcribed
ORDER BY audio_file;


-- =============================================================================
-- Example 10: no reservation required
-- =============================================================================
-- Unlike the image preprocessing functions in bq-ml, ML.TRANSCRIBE runs on
-- on-demand pricing: reservation_id and edition come back NULL.
SELECT
  FORMAT_TIMESTAMP('%H:%M:%S', creation_time) AS ran_at,
  IFNULL(reservation_id, 'none — on-demand') AS reservation_id,
  IFNULL(edition, 'none') AS edition,
  total_bytes_billed,
  total_slot_ms
FROM `region-us`.INFORMATION_SCHEMA.JOBS_BY_PROJECT
WHERE creation_time > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 2 HOUR)
  AND job_type = 'QUERY'
  AND query LIKE '%ML.TRANSCRIBE%'
  AND state = 'DONE'
  AND error_result IS NULL
ORDER BY creation_time DESC
LIMIT 5;


-- =============================================================================
-- Cleanup
-- =============================================================================
DROP EXTERNAL TABLE IF EXISTS `PROJECT_ID.DATASET.ml_transcribe_audio`;
DROP EXTERNAL TABLE IF EXISTS `PROJECT_ID.DATASET.ml_transcribe_mixed`;
DROP TABLE IF EXISTS `PROJECT_ID.DATASET.ml_transcribe_results`;
DROP MODEL IF EXISTS `PROJECT_ID.DATASET.ml_transcribe_model`;
