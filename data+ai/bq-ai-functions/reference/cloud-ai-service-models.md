![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2Fdata%2Bai%2Fbq-ai-functions%2Freference&file=cloud-ai-service-models.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/data%2Bai/bq-ai-functions/reference/cloud-ai-service-models.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-ai-functions/reference/cloud-ai-service-models.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-ai-functions/reference/cloud-ai-service-models.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-ai-functions/reference/cloud-ai-service-models.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-ai-functions/reference/cloud-ai-service-models.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Connect With Author On: </b> 
    <a href="https://www.linkedin.com/in/statmike"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a>
    <a href="https://www.github.com/statmike"><img src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub Logo" width="20px"></a> 
    <a href="https://www.youtube.com/@statmike-channel"><img src="https://upload.wikimedia.org/wikipedia/commons/f/fd/YouTube_full-color_icon_%282024%29.svg" alt="YouTube Logo" width="20px"></a>
    <a href="https://bsky.app/profile/statmike.bsky.social"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://x.com/statmike"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/data%2Bai/bq-ai-functions/reference/cloud-ai-service-models.md"><img src="https://www.svgrepo.com/download/5445/download-button.svg" alt="Download icon" width="20px"></a> <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/data%2Bai/bq-ai-functions/reference/cloud-ai-service-models.md">Download File</a> <i>(right-click and "Save As")</i>
  </td>
</tr>
</table><br/><br/>

# Cloud AI Service Models

> Part of the [BigQuery AI Functions Resources](../RESOURCES.md) · [Project README](../README.md)

Five BigQuery ML functions call a **pre-trained Google Cloud AI service** — not a Gemini endpoint — through a remote model. They are the oldest AI surface in BigQuery and the only one where the answer comes from a fixed, versioned API rather than a generative model.

| Function | `REMOTE_SERVICE_TYPE` | Service | Input | Examples |
|---|---|---|---|---|
| `ML.TRANSLATE` | `CLOUD_AI_TRANSLATE_V3` | [Cloud Translation](https://cloud.google.com/translate/docs) | Table/query with a `text_content` column | [notebook](../functions/ml_translate/ml_translate.ipynb) · [sql](../functions/ml_translate/ml_translate.sql) |
| `ML.UNDERSTAND_TEXT` | `CLOUD_AI_NATURAL_LANGUAGE_V1` | [Cloud Natural Language](https://cloud.google.com/natural-language/docs) | Table/query with a `text_content` column | [notebook](../functions/ml_understand_text/ml_understand_text.ipynb) · [sql](../functions/ml_understand_text/ml_understand_text.sql) |
| `ML.ANNOTATE_IMAGE` | `CLOUD_AI_VISION_V1` | [Cloud Vision](https://cloud.google.com/vision/docs) | Object table of images | [notebook](../functions/ml_annotate_image/ml_annotate_image.ipynb) · [sql](../functions/ml_annotate_image/ml_annotate_image.sql) |
| `ML.TRANSCRIBE` | `CLOUD_AI_SPEECH_TO_TEXT_V2` | [Speech-to-Text V2](https://cloud.google.com/speech-to-text/v2/docs) | Object table of audio | [notebook](../functions/ml_transcribe/ml_transcribe.ipynb) · [sql](../functions/ml_transcribe/ml_transcribe.sql) |
| `ML.PROCESS_DOCUMENT` | `CLOUD_AI_DOCUMENT_V1` | [Document AI](https://cloud.google.com/document-ai/docs) | Object table of documents | [notebook](../functions/ml_process_document/ml_process_document.ipynb) · [sql](../functions/ml_process_document/ml_process_document.sql) · [reference](document-processing.md#mlprocess_document) |

`ML.PROCESS_DOCUMENT` is documented in full on the [Document Processing](document-processing.md) page, beside `AI.PARSE_DOCUMENT`, which solves the same problem without a model object. It is listed here because everything on this page about setup, permissions, per-row failures and the model object applies to it identically.

---

## What the five have in common

**A model object that is a handle, not a model.** Every member needs `CREATE MODEL … REMOTE WITH CONNECTION … OPTIONS(REMOTE_SERVICE_TYPE = …)` first. Nothing trains and no data is read:

```sql
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.MODEL_NAME`
  REMOTE WITH CONNECTION `PROJECT_ID.REGION.CONNECTION_ID`
  OPTIONS (REMOTE_SERVICE_TYPE = 'CLOUD_AI_VISION_V1');
```

The model's own metadata says as much: `model_type` is unspecified, the single training run carries an empty `trainingOptions` and an empty `evaluationMetrics`, and the only substance in the record is `remoteModelInfo`. Each notebook prints it in its last SQL example.

**`ML.EVALUATE` is rejected.** Asking for it returns *"ML.EVALUATE is not supported for remote models on Cloud AI APIs."* There is nothing to evaluate — the service is the model, and its quality is Google's version number, not your training run.

**Models are not in `INFORMATION_SCHEMA`.** `INFORMATION_SCHEMA.TABLES` lists object tables but no models, and this project has no `INFORMATION_SCHEMA.MODELS` view. Read model metadata through the client library (`client.get_model(...).to_api_repr()`) or `bq show --model`.

**Three output columns, named after the function.** Each returns the input columns plus `<function>_result` (`JSON`) and `<function>_status` (`STRING`, empty on success). `ML.TRANSCRIBE` adds a fourth, `transcripts` (`STRING`) — the only member that hands back a finished answer without a JSON accessor.

**Failures are per row.** A row that the service rejects fills `<function>_status` and leaves the result empty **while the job succeeds**. A pipeline that does not select the status column records the failure as a result. See [Per-row failures](#per-row-failures-and-the-retry-pattern).

**They run on on-demand pricing.** Measured for `ML.TRANSCRIBE` in `INFORMATION_SCHEMA.JOBS_BY_PROJECT`: every call reports no `reservation_id` and an `edition` of `none` — on-demand. No BigQuery Editions reservation is required — unlike the [image preprocessing functions](../../bq-ml/reference/model-free-functions.md#image-preprocessing-functions-mldecode_image-mlresize_image-mlconvert_image_type-mlconvert_color_space) in the sibling `bq-ml` project, which fail outright without one. The BigQuery bill is bytes scanned; the service bill is separate and is priced by the service's own unit — characters for Translation and Natural Language, images (and features per image) for Vision, **seconds of audio** for Speech-to-Text, pages for Document AI.

**They are the stable option.** Nothing about their output moves when a Gemini default changes. That is the reason to choose them over an `AI.*` function with a prompt, and it is not the same as being deterministic — `ML.TRANSCRIBE` disagrees with itself across identical calls, while `ML.TRANSLATE` and `ML.UNDERSTAND_TEXT` do not. Each notebook measures this directly with the query cache off.

---

## Setup: APIs, connection, roles

All five run through a **Cloud Resource connection**. The connection's auto-provisioned service account — not your user account — is the identity that calls the service and reads Cloud Storage.

**The APIs to enable**, beyond `bigquery.googleapis.com` and `bigqueryconnection.googleapis.com`:

| Function | Service API | Also needs |
|---|---|---|
| `ML.TRANSLATE` | `translate.googleapis.com` | — |
| `ML.UNDERSTAND_TEXT` | `language.googleapis.com` | — |
| `ML.ANNOTATE_IMAGE` | `vision.googleapis.com` | `storage.googleapis.com` |
| `ML.TRANSCRIBE` | `speech.googleapis.com` | `storage.googleapis.com` |
| `ML.PROCESS_DOCUMENT` | `documentai.googleapis.com` | `storage.googleapis.com` |

**The roles to grant the connection's service account**, at project level:

| Role | `TRANSLATE` | `UNDERSTAND_TEXT` | `ANNOTATE_IMAGE` | `TRANSCRIBE` | `PROCESS_DOCUMENT` |
|---|---|---|---|---|---|
| `roles/serviceusage.serviceUsageConsumer` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `roles/bigquery.connectionUser` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `roles/storage.objectViewer` (object tables) | — | — | ✅ | ✅ | ✅ |
| Service-specific role | `roles/cloudtranslate.user` | *none exists* | *none exists* | `roles/speech.client` | `roles/documentai.apiUser` + `roles/documentai.viewer` |
| `roles/aiplatform.user` | comparison examples only | comparison examples only | comparison examples only | comparison examples only | comparison examples only |

Three things this table is for:

- **The service-specific role is not uniform, and its absence is not an oversight.** Cloud Vision and Cloud Natural Language have no predefined IAM role — `serviceusage.services.use` is the permission that gates them, so their column stops at the BigQuery-side rows. Translation and Speech-to-Text each add one; Document AI adds two. Copying one member's setup to another either over-grants or fails at call time.
- **`roles/serviceusage.serviceUsageConsumer` is the one people miss.** Without it every call fails, no matter which service. The `ML.TRANSLATE` notebook shows the exact message, which names the missing role — more than most IAM failures give you, but it arrives at call time.
- **`roles/aiplatform.user` is not part of any of these functions.** Each notebook ends by running an `AI.*` function over the same rows for comparison, and *that* is what needs it. A deployment that only calls the Cloud AI service model can leave it off.

**`CREATE MODEL` succeeding tells you nothing about permissions.** Model creation does not contact the service, so it completes happily against a connection that cannot call anything. The first failure arrives at call time.

**Grants do not take effect instantly.** A freshly granted binding can take a minute to become usable. Each of the four notebooks on this page ends its setup with a probe on the smallest possible input, in a wait loop, so the first real example runs against a connection that has been shown to work — worth copying into any script that creates the connection and then uses it.

See the [Setup Reference](../setup/) for connection creation, and each notebook's Setup section for a runnable, idempotent version that also prints which roles it granted.

---

## Two input shapes

**Object tables** — `ML.ANNOTATE_IMAGE`, `ML.TRANSCRIBE`, `ML.PROCESS_DOCUMENT`. An [object table](unstructured-data-infrastructure.md) is an external table whose rows are files. It reads through the same connection, which is why the service account needs `roles/storage.objectViewer`:

```sql
CREATE OR REPLACE EXTERNAL TABLE `PROJECT_ID.DATASET.OBJECT_TABLE`
  WITH CONNECTION `PROJECT_ID.REGION.CONNECTION_ID`
  OPTIONS (object_metadata = 'SIMPLE', uris = ['gs://BUCKET/PREFIX/*']);
```

**A `text_content` column** — `ML.TRANSLATE`, `ML.UNDERSTAND_TEXT`. Both read a column named exactly `text_content`. A table without one errors, and the fix is an alias in a subquery rather than a rename of your table:

```sql
FROM ML.TRANSLATE(
  MODEL `PROJECT_ID.DATASET.MODEL_NAME`,
  (SELECT review_id, comment AS text_content FROM `PROJECT_ID.DATASET.reviews`),
  STRUCT('TRANSLATE_TEXT' AS translate_mode, 'en' AS target_language_code))
```

---

## `ML.TRANSLATE`

- **Description:** Table-valued function that translates a text column, or detects its language, using the Cloud Translation V3 API.
- [documentation](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-translate) · [notebook](../functions/ml_translate/ml_translate.ipynb) · [sql](../functions/ml_translate/ml_translate.sql)

```sql
SELECT * FROM ML.TRANSLATE(
  MODEL `PROJECT_ID.DATASET.MODEL_NAME`,
  { TABLE `PROJECT_ID.DATASET.TABLE` | (QUERY_STATEMENT) },
  STRUCT('TRANSLATE_TEXT' AS translate_mode, 'LANGUAGE_CODE' AS target_language_code));
```

| Argument | Values | Notes |
|---|---|---|
| `translate_mode` | `'TRANSLATE_TEXT'`, `'DETECT_LANGUAGE'` | Two modes in one function |
| `target_language_code` | ISO-639 code | **Required** for `TRANSLATE_TEXT`; `DETECT_LANGUAGE` does not take one |

**Output:** `ml_translate_result` (JSON), `ml_translate_status`, plus the input columns including `text_content`.

**Worth knowing:**
- **One target language per call, and it cannot come from a column.** `target_language_code` is a scalar in the `STRUCT`, evaluated once for the whole call; a column reference fails to compile with `Unrecognized name`. Fanning out over three languages is three calls unioned together, each re-reading and re-billing the source text.
- **The source language is detected for free** in `TRANSLATE_TEXT` mode — the result carries `detected_language_code` beside `translated_text`, so there is no reason to run `DETECT_LANGUAGE` first just to route rows. The two modes return different JSON shapes: `translations[]` versus `languages[]` with a confidence.
- **It is stable across runs.** The notebook compares run-to-run output with the query cache off, and puts `AI.GENERATE` on the same rows for contrast.

---

## `ML.UNDERSTAND_TEXT`

- **Description:** Table-valued function that runs one of five Cloud Natural Language analyses over a text column.
- [documentation](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-understand-text) · [notebook](../functions/ml_understand_text/ml_understand_text.ipynb) · [sql](../functions/ml_understand_text/ml_understand_text.sql)

```sql
SELECT * FROM ML.UNDERSTAND_TEXT(
  MODEL `PROJECT_ID.DATASET.MODEL_NAME`,
  { TABLE `PROJECT_ID.DATASET.TABLE` | (QUERY_STATEMENT) },
  STRUCT('ANALYZE_SENTIMENT' AS nlu_option, TRUE AS flatten_json_output));
```

| `nlu_option` | What comes back |
|---|---|
| `ANALYZE_SENTIMENT` | Document and per-sentence sentiment, as a score and a magnitude |
| `ANALYZE_ENTITIES` | Named things in the text, with a type and a salience |
| `ANALYZE_ENTITY_SENTIMENT` | The same entities, each carrying its own sentiment |
| `ANALYZE_SYNTAX` | Tokens with part of speech, lemma and dependency edges |
| `CLASSIFY_TEXT` | Categories from a published, fixed taxonomy |

Two more arguments: `flatten_json_output` (`BOOL`) adds unpacked columns beside the JSON, and `encoding_type` (`'UTF8'`, `'UTF16'`, `'UTF32'`) turns on the text-span offsets. Its default is `NONE`, which means `begin_offset` is simply not computed — and when you do ask, the offsets are measured in that encoding's units, so UTF-8 and UTF-16 disagree on any accented text.

**Output:** `ml_understand_text_result` (JSON), `ml_understand_text_status`, the input columns, and — with `flatten_json_output` — the flattened columns.

**Worth knowing:**
- **Language support differs per analysis**, and an unsupported language fails **the row**, not the job. Measured: `ANALYZE_ENTITY_SENTIMENT` returns `INVALID_ARGUMENT: The language ko is not supported for entity_sentiment analysis.` for Korean and Vietnamese rows while the same call succeeds for the rest — entity sentiment supports fewer languages than sentiment does.
- **An empty sentiment object reads as `NULL`, not `0`.** An entity can come back with no sentiment, and the accessor cannot tell that apart from neutral unless you coalesce.
- **The taxonomy and the entity types are closed vocabularies.** That is the feature — the same text yields the same category next quarter — and the limit: if your business needs a category the taxonomy does not have, this is the wrong function.

---

## `ML.ANNOTATE_IMAGE`

- **Description:** Table-valued function that annotates images in an object table with the Cloud Vision API. One model serves every feature; the feature list is an argument to the function, not an option on the model.
- [documentation](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-annotate-image) · [notebook](../functions/ml_annotate_image/ml_annotate_image.ipynb) · [sql](../functions/ml_annotate_image/ml_annotate_image.sql)

```sql
SELECT * FROM ML.ANNOTATE_IMAGE(
  MODEL `PROJECT_ID.DATASET.MODEL_NAME`,
  { TABLE `PROJECT_ID.DATASET.OBJECT_TABLE` | (QUERY_STATEMENT) },
  STRUCT(['LABEL_DETECTION', 'OBJECT_LOCALIZATION'] AS vision_features));
```

The syntax page lists eight features: `LABEL_DETECTION`, `OBJECT_LOCALIZATION`, `TEXT_DETECTION`, `DOCUMENT_TEXT_DETECTION`, `LANDMARK_DETECTION`, `LOGO_DETECTION`, `FACE_DETECTION` and `IMAGE_PROPERTIES`.

**Output:** `ml_annotate_image_result` (JSON), `ml_annotate_image_status`, plus the object table columns.

**Worth knowing:**
- **One call, many features.** Requesting several features in one call is one pass over the image; the result JSON gains a top-level key per feature.
- **What the documented list covers and what the function parses are different sets.** Measured against the undocumented names: `SAFE_SEARCH_DETECTION` and `CROP_HINTS` are accepted and return `safe_search_annotation` and `crop_hints_annotation`; `WEB_DETECTION` is accepted and returns no keys at all; an invented name is rejected outright with `Found unsupported value … of setting field vision_features`. Accepted is not the same as supported — the silent-empty case is the one to guard against.
- **A zero-valued JSON field is omitted from the response.** Landmark bounding boxes are in absolute pixels, and a vertex at the origin arrives as `{}`, so `INT64(vertex.x)` returns `NULL` rather than `0`. Coalesce it.

---

## `ML.TRANSCRIBE`

- **Description:** Table-valued function that transcribes audio in an object table with Speech-to-Text V2, returning the finished text in a `STRING` column.
- [documentation](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-transcribe) · [notebook](../functions/ml_transcribe/ml_transcribe.ipynb) · [sql](../functions/ml_transcribe/ml_transcribe.sql)

```sql
SELECT * FROM ML.TRANSCRIBE(
  MODEL `PROJECT_ID.DATASET.MODEL_NAME`,
  { TABLE `PROJECT_ID.DATASET.OBJECT_TABLE` | (QUERY_STATEMENT) },
  recognition_config => JSON '{"language_codes": ["en-US"], "model": "chirp", "auto_decoding_config": {}}');
```

**Output:** `transcripts` (`STRING` — the full transcript), `ml_transcribe_result` (JSON), `ml_transcribe_status`, plus the object table columns.

**Worth knowing:**
- **The third argument is a named argument, not a `STRUCT`** — the only member of the family that breaks the convention. It is also **required** unless the model was created with `SPEECH_RECOGNIZER`. Both mistakes produce errors that print the signature: `ML.TRANSCRIBE(MODEL, TABLE, [recognition_config => JSON])`.
- **`chirp` is the only accepted `model`.** `chirp_2`, `long`, `short` and `telephony` are all rejected with *"Supported models are: chirp."*
- **`SPEECH_RECOGNIZER` is regional.** BigQuery accepts a recognizer only from `asia-southeast1`, `us-central1` or `europe-west4` — a constraint to weigh against a multi-region dataset before choosing a recognizer over a per-call config.
- **`language_codes` is echoed, not enforced.** Forcing `["en-US"]` on French audio still returns French, still reporting `en-US`. `["auto"]` detects and reports bare subtags (`fr`, `es`, `en`).
- **Some `features` keys void the row.** `enable_automatic_punctuation` and `enable_word_time_offsets` work; `enable_word_confidence`, `diarization_config` and `profanity_filter` each fail the row with *"Config contains unsupported fields"* — naming no field, so you find the culprit by bisecting the object.
- **The result JSON is keyed by URI.** `ml_transcribe_result.results[uri]…` — the accessor has to index the JSON with the row's own `uri` column, and long audio arrives as several segments, which the `transcripts` column concatenates for you.
- **It is not reproducible.** Identical calls with the cache off can return different transcripts. Transcribe once, persist, and treat the text as data rather than as a key.

---

## Per-row failures and the retry pattern

Every member reports failure in a status column while the **job succeeds**. Measured examples: a non-audio file in a `ML.TRANSCRIBE` object table, and an unsupported language in `ML.UNDERSTAND_TEXT`. The standard shape is to persist results and re-run only the failures:

```sql
CREATE OR REPLACE TABLE `PROJECT_ID.DATASET.results` AS
SELECT * FROM ML.TRANSCRIBE(MODEL ..., TABLE ..., recognition_config => JSON '...');

-- what failed, and why
SELECT uri, ml_transcribe_status
FROM `PROJECT_ID.DATASET.results`
WHERE ml_transcribe_status != '';
```

Whether the retry can succeed depends on the cause: a `RESOURCE EXHAUSTED` row failed for load and will likely pass on a second attempt; a row that failed for an unsupported language or an unsupported encoding will fail identically forever. Read the status before retrying.

---

## Choosing between these and the `AI.*` functions

Every member has a generative alternative — [`AI.GENERATE`](general-purpose-functions.md) over an `ObjectRef` reads audio and images directly, and a prompt can translate, score sentiment or extract entities. Each notebook runs both over the same rows so the comparison is measured rather than argued. What the comparisons keep showing:

**Reach for a Cloud AI service model** when the output is a record: a fixed API version, a published per-unit price, a closed vocabulary, and behavior that does not move when a model default does. When the service cannot do something, it says so — an unsupported language, an unsupported feature, an unreadable file all arrive as errors in a status column.

**Reach for an `AI.*` function** when the deliverable is not the service's output: a summary rather than a transcript, your categories rather than the taxonomy's, translate-and-rewrite rather than translate. It will also answer questions the service refuses — and that is the trade, because it answers them the same confident way whether or not it is right, with no status column and no confidence beside the answer. A refusal is information; a fluent guess is not.

**Use both** when the record and the analysis are different artifacts: the service output as the durable, priced, inspectable column, and the generative function over *that column* — where the input is text you can read instead of media you cannot.
