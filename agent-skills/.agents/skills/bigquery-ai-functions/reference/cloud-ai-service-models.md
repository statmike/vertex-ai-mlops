# Cloud AI Service Models (pre-trained Cloud AI services, not Gemini) in BigQuery

Five functions call a **pre-trained Google Cloud AI service** through a remote model instead of a Gemini endpoint. They are the oldest AI surface in BigQuery, and the only one where the answer comes from a fixed, versioned API rather than a generative model. `ML.PROCESS_DOCUMENT` belongs to this family too — it is covered in depth in `reference/document-processing.md` beside `AI.PARSE_DOCUMENT`, and everything on this page applies to it identically.

## Options

| Function | `REMOTE_SERVICE_TYPE` | Service | Input shape | Third argument |
|---|---|---|---|---|
| `ML.TRANSLATE` | `CLOUD_AI_TRANSLATE_V3` | Cloud Translation V3 | table/query with a column named exactly `text_content` | `STRUCT('TRANSLATE_TEXT' AS translate_mode, 'en' AS target_language_code)` |
| `ML.UNDERSTAND_TEXT` | `CLOUD_AI_NATURAL_LANGUAGE_V1` | Cloud Natural Language | table/query with a column named exactly `text_content` | `STRUCT('ANALYZE_SENTIMENT' AS nlu_option, TRUE AS flatten_json_output)` |
| `ML.ANNOTATE_IMAGE` | `CLOUD_AI_VISION_V1` | Cloud Vision | object table of images | `STRUCT(['LABEL_DETECTION'] AS vision_features)` |
| `ML.TRANSCRIBE` | `CLOUD_AI_SPEECH_TO_TEXT_V2` | Speech-to-Text V2 | object table of audio | `recognition_config => JSON '{...}'` — a **named argument**, not a STRUCT |
| `ML.PROCESS_DOCUMENT` | `CLOUD_AI_DOCUMENT_V1` | Document AI | object table of documents | none — the processor carries the configuration; see `reference/document-processing.md` |

`ML.UNDERSTAND_TEXT`'s five `nlu_option` values: `ANALYZE_SENTIMENT`, `ANALYZE_ENTITIES`, `ANALYZE_ENTITY_SENTIMENT`, `ANALYZE_SYNTAX`, `CLASSIFY_TEXT`. `ML.ANNOTATE_IMAGE`'s eight documented `vision_features`: `LABEL_DETECTION`, `OBJECT_LOCALIZATION`, `TEXT_DETECTION`, `DOCUMENT_TEXT_DETECTION`, `LANDMARK_DETECTION`, `LOGO_DETECTION`, `FACE_DETECTION`, `IMAGE_PROPERTIES`.

## Choosing among them — and against `AI.*`

Every member has a generative alternative: `AI.GENERATE` over an `ObjectRef` reads audio and images directly, and a prompt can translate, score sentiment, or extract entities. This repo runs both over the same rows in each notebook.

- **Reach for a Cloud AI service model when the output is a record** — a fixed API version, a published per-unit price, a closed vocabulary, and behavior that does not move when a Gemini default does. When the service cannot do something it *says so*, in a status column.
- **Reach for an `AI.*` function when the deliverable is not the service's output** — a summary rather than a transcript, your categories rather than the taxonomy's, translate-and-rewrite rather than translate. The trade: no status column, no confidence, and the same fluent tone whether or not it is right.
- **Use both** when the record and the analysis are different artifacts: the service output as the durable priced column, then the generative function over *that column* — text you can read instead of media you cannot.
- **These are not "cheaper Gemini."** The BigQuery bill is bytes scanned; the service bill is separate and priced in the service's own unit — characters (Translation, Natural Language), images and features-per-image (Vision), **seconds of audio** (Speech-to-Text), pages (Document AI).

## Gotchas verified in this repo

- **The model object is a handle, not a model.** `CREATE MODEL ... REMOTE WITH CONNECTION ... OPTIONS(REMOTE_SERVICE_TYPE = '...')` trains nothing and reads no data — `model_type` comes back unspecified, `trainingOptions` and `evaluationMetrics` are empty, and only `remoteModelInfo` has substance. There is no cost or duration to a create.
- **`ML.EVALUATE` is rejected outright**: *"ML.EVALUATE is not supported for remote models on Cloud AI APIs."* The service is the model; its quality is Google's version number.
- **These models are absent from `INFORMATION_SCHEMA`** — object tables show up in `INFORMATION_SCHEMA.TABLES`, but there is no `INFORMATION_SCHEMA.MODELS` view. Read metadata via `client.get_model(...).to_api_repr()` or `bq show --model`.
- **`CREATE MODEL` succeeding tells you nothing about permissions.** Creation never contacts the service, so it completes happily against a connection that cannot call anything. The first failure arrives at call time — which is why this repo's notebooks end setup with a probe on the smallest possible input, in a wait loop (a fresh IAM binding can take a minute to become usable).
- **`roles/serviceusage.serviceUsageConsumer` is the role people miss** — without it every call fails, whichever service. Grant it, plus `roles/bigquery.connectionUser`, to the *connection's* auto-provisioned service account (not your user account), at project level.
- **The service-specific role is not uniform, and two of the five have none.** Cloud Vision and Cloud Natural Language have **no predefined IAM role** — `serviceusage.services.use` is what gates them. Translation adds `roles/cloudtranslate.user`, Speech-to-Text adds `roles/speech.client`, Document AI adds **two** (`roles/documentai.apiUser` + `roles/documentai.viewer`). Object-table members also need `roles/storage.objectViewer`. Copying one member's setup to another either over-grants or fails at call time. `roles/aiplatform.user` is **not** needed by any of them — only by the `AI.*` comparison queries.
- **APIs to enable, beyond `bigquery` + `bigqueryconnection`:** `translate`, `language`, `vision` (+`storage`), `speech` (+`storage`), `documentai` (+`storage`).
- **Failures are per row and the job still succeeds.** Each function returns `<function>_result` (JSON) and `<function>_status` (STRING, empty on success). A pipeline that does not select the status column records a failure as a result. Persist the output, then `WHERE <function>_status != ''` to find and re-run failures — but read the status first: `RESOURCE EXHAUSTED` will likely pass on retry, an unsupported language or encoding will fail identically forever.
- **`ML.TRANSCRIBE` alone returns a finished answer** in a fourth column, `transcripts` (STRING); everything else needs a JSON accessor.
- **No reservation required** — measured in `INFORMATION_SCHEMA.JOBS_BY_PROJECT`, every call reports no `reservation_id` and `edition = none`. This is the opposite of the sibling `bigquery-ml` skill's four image-preprocessing functions, which fail outright on on-demand pricing.
- **Stable ≠ deterministic.** Nothing here moves when a Gemini default changes — that is the reason to pick these. But measured with the cache off, `ML.TRANSCRIBE` disagrees with itself across identical calls, while `ML.TRANSLATE` and `ML.UNDERSTAND_TEXT` do not. Transcribe once, persist, treat the text as data rather than as a key.
- **`ML.TRANSLATE`: one target language per call, and it cannot come from a column** — `target_language_code` is a scalar evaluated once for the whole call; a column reference fails to compile with `Unrecognized name`. Three languages means three calls unioned, each re-reading and re-billing the source. The source language is detected *for free* in `TRANSLATE_TEXT` mode (`detected_language_code` sits beside `translated_text`), so never run `DETECT_LANGUAGE` first just to route rows.
- **`ML.UNDERSTAND_TEXT`: language support differs per analysis, and an unsupported language fails the row, not the job.** Measured: `ANALYZE_ENTITY_SENTIMENT` returns `INVALID_ARGUMENT: The language ko is not supported for entity_sentiment analysis.` for Korean and Vietnamese while the same call succeeds for every other row — entity sentiment supports fewer languages than sentiment does. Also: an empty sentiment object reads as `NULL`, not `0`; and `encoding_type` defaults to `NONE`, so `begin_offset` is simply not computed unless you ask — and when you do, UTF-8 and UTF-16 offsets disagree on any accented text.
- **`ML.ANNOTATE_IMAGE`: accepted is not the same as supported.** Beyond the eight documented features, `SAFE_SEARCH_DETECTION` and `CROP_HINTS` are accepted and return real keys; `WEB_DETECTION` is accepted and returns **no keys at all**; an invented name is rejected with `Found unsupported value ... of setting field vision_features`. The silent-empty case is the one to guard against. Also: a zero-valued JSON field is *omitted* from the response, so a landmark vertex at the origin arrives as `{}` and `INT64(vertex.x)` returns `NULL` rather than `0` — coalesce it.
- **`ML.TRANSCRIBE` breaks the family's argument convention** — `recognition_config => JSON '...'` is a named argument, and it is **required** unless the model was created with `SPEECH_RECOGNIZER`. Both mistakes print the signature: `ML.TRANSCRIBE(MODEL, TABLE, [recognition_config => JSON])`. Then: **`chirp` is the only accepted `model`** (`chirp_2`, `long`, `short`, `telephony` all rejected with *"Supported models are: chirp."*); a `SPEECH_RECOGNIZER` is accepted only from `asia-southeast1`, `us-central1`, or `europe-west4`; **`language_codes` is echoed, not enforced** (forcing `["en-US"]` on French audio returns French and still reports `en-US`; `["auto"]` detects and reports bare subtags); and `enable_word_confidence`, `diarization_config`, and `profanity_filter` each void the row with *"Config contains unsupported fields"*, naming no field — you find the culprit by bisecting the JSON. The result JSON is keyed by URI (`ml_transcribe_result.results[uri]`), and long audio arrives as several segments that the `transcripts` column concatenates for you.

## Canonical snippet

```sql
-- 1. The handle. Nothing trains; this says nothing about whether the connection can call the service.
CREATE OR REPLACE MODEL `myproject.mydataset.translator`
  REMOTE WITH CONNECTION `myproject.us.myconnection`
  OPTIONS (REMOTE_SERVICE_TYPE = 'CLOUD_AI_TRANSLATE_V3');

-- 2. The call. `text_content` is a required column name — alias in a subquery rather than renaming your table.
CREATE OR REPLACE TABLE `myproject.mydataset.translated` AS
SELECT * FROM ML.TRANSLATE(
  MODEL `myproject.mydataset.translator`,
  (SELECT review_id, comment AS text_content FROM `myproject.mydataset.reviews`),
  STRUCT('TRANSLATE_TEXT' AS translate_mode, 'en' AS target_language_code));

-- 3. Always read the status column. The job succeeded even if rows did not.
SELECT review_id, ml_translate_status
FROM `myproject.mydataset.translated`
WHERE ml_translate_status != '';

-- 4. The payload.
SELECT review_id,
       STRING(ml_translate_result.translations[0].translated_text)        AS translated,
       STRING(ml_translate_result.translations[0].detected_language_code) AS source_language
FROM `myproject.mydataset.translated`
WHERE ml_translate_status = '';
```

## Go deeper

Full extracted notebook walkthroughs live in this skill's `narrative/` folder:

- [`narrative/ml_translate.md`](../narrative/ml_translate.md) (source: `functions/ml_translate/`)
- [`narrative/ml_understand_text.md`](../narrative/ml_understand_text.md) (source: `functions/ml_understand_text/`)
- [`narrative/ml_annotate_image.md`](../narrative/ml_annotate_image.md) (source: `functions/ml_annotate_image/`)
- [`narrative/ml_transcribe.md`](../narrative/ml_transcribe.md) (source: `functions/ml_transcribe/`)
- [`narrative/ml_process_document.md`](../narrative/ml_process_document.md) (source: `functions/ml_process_document/`) — the fifth member; see also `reference/document-processing.md`

Object tables — the input shape for three of the five — are documented in `reference/document-processing.md` and, in the source repo, at `bq-ai-functions/reference/unstructured-data-infrastructure.md`. The family page in the source repo is `bq-ai-functions/reference/cloud-ai-service-models.md`.

The sibling `bigquery-ml` skill covers the *other* kind of remote model — `CREATE MODEL ... REMOTE ... OPTIONS(endpoint = 'https://...')` against a Vertex AI Endpoint you deployed and pay for by the hour, consumed with `ML.PREDICT`. See its `narrative/remote.md`. Same connection and IAM mechanics; everything else differs.
