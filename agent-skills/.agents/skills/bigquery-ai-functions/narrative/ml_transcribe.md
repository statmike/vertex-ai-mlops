# ML.TRANSCRIBE — BigQuery AI Functions

`ML.TRANSCRIBE` sends audio files referenced by a BigQuery [object table](https://cloud.google.com/bigquery/docs/object-table-introduction) to [Speech-to-Text V2](https://cloud.google.com/speech-to-text/v2/docs) and returns the transcript. It is a table-valued function that runs through a **remote model**, so there is a `CREATE MODEL` step, but nothing trains: the model object is a handle on a pre-trained Google API.

**One of five Cloud AI service models.** `ML.TRANSCRIBE` belongs to a small family of BigQuery ML functions that call a pre-trained Cloud AI service through `CREATE MODEL … REMOTE WITH CONNECTION … OPTIONS(REMOTE_SERVICE_TYPE = …)`. The five members and their service types:

| Function | `REMOTE_SERVICE_TYPE` | Service | Input |
|---|---|---|---|
| `ML.TRANSCRIBE` *(this notebook)* | `CLOUD_AI_SPEECH_TO_TEXT_V2` | Speech-to-Text | An object table of audio files |
| `functions/ml_annotate_image` (`ML.ANNOTATE_IMAGE`) | `CLOUD_AI_VISION_V1` | Cloud Vision | An object table of images |
| `functions/ml_process_document` (`ML.PROCESS_DOCUMENT`) | `CLOUD_AI_DOCUMENT_V1` | Document AI | An object table of documents |
| `functions/ml_translate` (`ML.TRANSLATE`) | `CLOUD_AI_TRANSLATE_V3` | Cloud Translation | A table or query with a `text_content` column |
| `functions/ml_understand_text` (`ML.UNDERSTAND_TEXT`) | `CLOUD_AI_NATURAL_LANGUAGE_V1` | Cloud Natural Language | A table or query with a `text_content` column |

The shared setup — connection, service account roles, `CREATE MODEL` — is written once in `reference/cloud-ai-service-models.md` (Cloud AI Service Models). This notebook repeats the parts you need to run it standalone.

**Two things make this member different from its four siblings:**

1. **It returns a plain `STRING` column.** Every other member hands back JSON you have to dig through. `ML.TRANSCRIBE` returns `transcripts` — the finished text — next to the JSON. Example 1 is one `SELECT` with nothing to unpack.
2. **Its third argument is a named argument, not a `STRUCT`.** The others take `STRUCT(… AS option)`. This one takes `recognition_config => JSON '…'`, and it is **required** unless the model was created with a recognizer. Example 2 measures both halves of that.

**When to use it:** you have audio in Cloud Storage and you want the words, in a table, at a price per second of audio. Example 10 runs `functions/ai_generate` (`AI.GENERATE`) over the same files for comparison — the difference in what each returns, and in what each will claim, is the reason to know both.

---
## Setup

This function needs a **Cloud Resource connection** whose service account may call Speech-to-Text and read Cloud Storage, an **object table** over the audio, and a **remote model** that names the service. All are created below and all are idempotent.

> See the `setup` (Setup Reference) for connections, object tables and remote models in general, and `reference/cloud-ai-service-models.md` (Cloud AI Service Models) for this family in particular.

```python
PROJECT_ID = 'statmike-mlops-349915'  # <-- Replace with your project ID
LOCATION = 'US'  # BigQuery dataset location — this family runs in US or EU
DATASET_ID = 'bq_ai_functions'  # Shared dataset across all notebooks
CONNECTION_ID = 'bq_ai_functions'  # Shared connection
BUCKET = PROJECT_ID  # GCS bucket for the sample audio (same name as project)
```

### Environment

> **Already set up the project environment?** The cell below is a no-op — packages are already in your kernel. See the `setup` (Setup Reference) for details.
>
> **Running standalone** (Colab, Colab Enterprise, Vertex AI Workbench)? The cell below installs required packages into your current kernel.

```python
from google.cloud import bigquery
import pandas as pd

client = bigquery.Client(project=PROJECT_ID)
pd.set_option('display.max_colwidth', None)

# Create the shared dataset (idempotent)
dataset_ref = bigquery.DatasetReference(PROJECT_ID, DATASET_ID)
dataset = bigquery.Dataset(dataset_ref)
dataset.location = LOCATION
client.create_dataset(dataset, exists_ok=True)
print(f'Dataset {PROJECT_ID}.{DATASET_ID} ready')

# Register %%bigquery cell magic (auto-loaded in Colab, needed elsewhere)
%load_ext bigquery_magics
```

### The APIs

Four services are involved: BigQuery, the BigQuery Connection service that owns the connection, Cloud Storage where the audio lives, and Speech-to-Text, which does the work. The cell enables any that are off.

```python
import subprocess as _sp

REQUIRED_APIS = [
    'bigquery.googleapis.com',
    'bigqueryconnection.googleapis.com',
    'storage.googleapis.com',
    'speech.googleapis.com',
]

enabled = set(_sp.run(['gcloud', 'services', 'list', '--enabled',
                       '--format=value(config.name)', f'--project={PROJECT_ID}'],
                      capture_output=True, text=True, check=True).stdout.split())
missing = [api for api in REQUIRED_APIS if api not in enabled]
for api in missing:
    _sp.run(['gcloud', 'services', 'enable', api, f'--project={PROJECT_ID}'],
            capture_output=True, text=True, check=True)

print(f'Already enabled: {", ".join(sorted(set(REQUIRED_APIS) & enabled)) or "none"}')
print(f'Enabled now:     {", ".join(missing) or "none"}')
```

### The connection and its service account

The connection's service account — not your user account — is what calls Speech-to-Text **and** what reads the audio out of Cloud Storage. Five grants at the project level:

| Role | Why |
|---|---|
| `roles/serviceusage.serviceUsageConsumer` | Lets the service account consume an API in this project. **Without it every call fails**, even though `CREATE MODEL` succeeds. |
| `roles/bigquery.connectionUser` | Lets the service account use the connection it belongs to. |
| `roles/storage.objectViewer` | Lets it read the audio bytes behind the object table. |
| `roles/speech.client` | The Speech-to-Text side of the ladder. |
| `roles/aiplatform.user` | Only for Example 10, which calls `AI.GENERATE` through the same connection to compare against Speech-to-Text. |

> **The service-specific role differs across the family.** Speech-to-Text has `roles/speech.client`; `functions/ml_translate` (`ML.TRANSLATE`) needs `roles/cloudtranslate.user`; `functions/ml_annotate_image` (`ML.ANNOTATE_IMAGE`) needs no service role at all, because Cloud Vision has no predefined one. The BigQuery-side roles get the request to the service; the service then applies whatever IAM it has.

> **`CREATE MODEL` succeeding tells you nothing about permissions.** Model creation for this family does not contact the service, so it completes against a connection that cannot call anything. The first failure arrives at call time.

The cell below prints which roles the service account already had and which it granted, so the run is auditable. It needs project-level IAM admin rights.

```python
import subprocess as _sp, json as _json

# Create the Cloud Resource connection (idempotent — an existing one is left alone)
_sp.run(['bq', 'mk', '--connection', '--location', LOCATION,
         '--connection_type', 'CLOUD_RESOURCE',
         '--project_id', PROJECT_ID, CONNECTION_ID],
        capture_output=True, text=True)

# The connection's auto-provisioned service account is the identity that calls the Cloud AI service
r = _sp.run(['bq', 'show', '--connection', '--format=json',
             '--project_id', PROJECT_ID, '--location', LOCATION, CONNECTION_ID],
            capture_output=True, text=True, check=True)
sa = _json.loads(r.stdout)['cloudResource']['serviceAccountId']
print(f'Connection service account: {sa}')

REQUIRED_ROLES = [
    'roles/serviceusage.serviceUsageConsumer',
    'roles/bigquery.connectionUser',
    'roles/storage.objectViewer',
    'roles/speech.client',
    'roles/aiplatform.user',
]

def roles_held():
    out = _sp.run(['gcloud', 'projects', 'get-iam-policy', PROJECT_ID,
                   '--flatten=bindings[].members',
                   f'--filter=bindings.members:{sa}',
                   '--format=value(bindings.role)'],
                  capture_output=True, text=True, check=True)
    return set(out.stdout.split())

held = roles_held()
missing = [role for role in REQUIRED_ROLES if role not in held]
for role in missing:
    _sp.run(['gcloud', 'projects', 'add-iam-policy-binding', PROJECT_ID,
             f'--member=serviceAccount:{sa}', f'--role={role}', '--condition=None', '--quiet'],
            capture_output=True, text=True, check=True)

print(f'Already held: {", ".join(sorted(set(REQUIRED_ROLES) & held)) or "none"}')
print(f'Granted now:  {", ".join(missing) or "none"}')
```

### The audio

Eight public samples from `gs://cloud-samples-data/speech/`, copied into this project's bucket so the object table and its teardown stay inside one project. They cover three container formats, three languages, single utterances and conversations, and clips from one second to a minute.

A ninth file — a **text** file — goes into a second folder. Example 7 points an object table at both folders to show what a row that cannot be transcribed does to the job.

```python
from google.cloud import storage

storage_client = storage.Client(project=PROJECT_ID)
source_bucket = storage_client.bucket('cloud-samples-data')
target_bucket = storage_client.bucket(BUCKET)

SAMPLES = [
    'hello.wav',              # one word
    'brooklyn_bridge.flac',   # one short question
    'time.mp3',               # mp3 container
    'multi.wav',              # a short English exchange
    'multi_es.flac',          # Spanish
    'corbeau_renard.flac',    # French, a fable read aloud
    'commercial_mono.wav',    # a sales conversation
    'Google_Gnome.wav',       # a minute of advertisement
]

copied = 0
for sample in SAMPLES:
    target = target_bucket.blob(f'bq_ai_functions/ml_transcribe/audio/{sample}')
    if not target.exists():
        source_bucket.copy_blob(source_bucket.blob(f'speech/{sample}'), target_bucket,
                                f'bq_ai_functions/ml_transcribe/audio/{sample}')
        copied += 1

# Not audio — used in Example 7
if not target_bucket.blob('bq_ai_functions/ml_transcribe/other/audio.txt').exists():
    source_bucket.copy_blob(source_bucket.blob('speech/audio.txt'), target_bucket,
                            'bq_ai_functions/ml_transcribe/other/audio.txt')

print(f'{copied} newly copied, {len(SAMPLES)} audio files in gs://{BUCKET}/bq_ai_functions/ml_transcribe/audio/')
```

### The object tables

An object table is an external table whose rows are files, not records: `uri`, `content_type`, `size`, `updated`, and a `ref` the `OBJ.*` functions understand. It reads through the same connection, which is why the service account needed `roles/storage.objectViewer`.

Two of them: one over the audio folder, one over both folders.

```python
for table, uris in [
    ('ml_transcribe_audio', f"['gs://{BUCKET}/bq_ai_functions/ml_transcribe/audio/*']"),
    ('ml_transcribe_mixed', f"['gs://{BUCKET}/bq_ai_functions/ml_transcribe/audio/*', 'gs://{BUCKET}/bq_ai_functions/ml_transcribe/other/*']"),
]:
    client.query(f'''
    CREATE OR REPLACE EXTERNAL TABLE `{PROJECT_ID}.{DATASET_ID}.{table}`
      WITH CONNECTION `{PROJECT_ID}.{LOCATION}.{CONNECTION_ID}`
      OPTIONS (object_metadata = 'SIMPLE', uris = {uris})
    ''').result()
    print(f'Object table {table} ready')

client.query(f'''
SELECT REGEXP_EXTRACT(uri, r'[^/]+$') AS audio_file, content_type, size
FROM `{PROJECT_ID}.{DATASET_ID}.ml_transcribe_audio`
ORDER BY size
''').to_dataframe()
```

### The remote model

Nothing trains here. `CREATE MODEL` writes a model object that records the connection and the service type; Speech-to-Text is called later, per file, by `ML.TRANSCRIBE`. There is no `ML.EVALUATE`, no weights, and no training data — Example 12 reads the model's own metadata to show it.

There is one model option worth knowing: **`SPEECH_RECOGNIZER`**. A [recognizer](https://cloud.google.com/speech-to-text/v2/docs/recognizers) is a Speech-to-Text resource that stores a configuration — language, model, features — so callers do not have to repeat it. Attach one to the model and the configuration comes from it. Leave it off, as here, and the model uses the *default* recognizer, which stores nothing, which is why every call must carry a `recognition_config`. Example 3 measures the trade the option makes.

```python
client.query(f'''
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.ml_transcribe_model`
  REMOTE WITH CONNECTION `{PROJECT_ID}.{LOCATION}.{CONNECTION_ID}`
  OPTIONS (REMOTE_SERVICE_TYPE = 'CLOUD_AI_SPEECH_TO_TEXT_V2')
''').result()
print('Model ml_transcribe_model ready')
```

### Wait for the grants to take effect

A role binding is not usable the instant `gcloud` returns. On a fresh grant the first call still fails with a permission error, so this cell probes with the one-second sample and waits on evidence rather than on a clock. It prints how long it took — on a project where the roles were already in place, that is zero seconds.

```python
import time
from google.api_core.exceptions import BadRequest, Forbidden

probe_sql = f'''
SELECT transcripts
FROM ML.TRANSCRIBE(
  MODEL `{PROJECT_ID}.{DATASET_ID}.ml_transcribe_model`,
  (SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.ml_transcribe_audio` WHERE uri LIKE '%hello%'),
  recognition_config => JSON '{{"language_codes": ["en-US"], "model": "chirp", "auto_decoding_config": {{}}}}'
)
'''

waited = 0
while True:
    try:
        transcript = list(client.query(probe_sql).result())[0]['transcripts']
        print(f'Probe succeeded after {waited}s: {transcript!r}')
        break
    except (BadRequest, Forbidden) as e:
        if 'denied' not in str(e) and 'permission' not in str(e):
            raise
        if waited >= 300:
            raise RuntimeError('IAM grants did not become usable within 5 minutes')
        print(f'  not usable yet ({waited}s elapsed)')
        time.sleep(15)
        waited += 15
```

---
## Examples — SQL

### 1. The whole point: a `STRING` column

`ML.TRANSCRIBE` returns the object table's columns plus three of its own: **`transcripts`** (`STRING`), `ml_transcribe_result` (`JSON`) and `ml_transcribe_status` (`STRING`, empty on success). The first one is the finished text. No `JSON_QUERY_ARRAY`, no `UNNEST`, no accessor — the rest of this family gives you JSON and lets you find the answer in it.

```python
query = f'''
SELECT
  REGEXP_EXTRACT(uri, r'[^/]+$') AS audio_file,
  transcripts,
  ml_transcribe_status
FROM ML.TRANSCRIBE(
  MODEL `{PROJECT_ID}.{DATASET_ID}.ml_transcribe_model`,
  TABLE `{PROJECT_ID}.{DATASET_ID}.ml_transcribe_audio`,
  recognition_config => JSON '{{"language_codes": ["en-US"], "model": "chirp", "auto_decoding_config": {{}}}}'
)
ORDER BY audio_file
'''
pd.set_option('display.max_colwidth', 300)
client.query(query).to_dataframe()
```

Read the transcripts before reading on. They are lowercase, unpunctuated, and the proper nouns are approximate — this is a speech model returning words, not a writer returning prose. Example 6 turns punctuation on; Example 10 shows what a generative model does with the same audio.

### 2. The argument that is not a `STRUCT`

Two things about the third argument are easy to get wrong, and both produce errors that tell you exactly what to do — if you read them.

First: it is **required** when the model has no recognizer attached. Second: it is a **named argument** taking a `JSON` value, not the `STRUCT(value AS option)` that the other four members of this family take. The cell provokes both errors and prints them.

```python
base = f'''
FROM ML.TRANSCRIBE(
  MODEL `{PROJECT_ID}.{DATASET_ID}.ml_transcribe_model`,
  (SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.ml_transcribe_audio` WHERE uri LIKE '%hello%')'''

attempts = {
    'no third argument': base + ')',
    'STRUCT, like the other four': base + ''',
  STRUCT(JSON '{"language_codes": ["en-US"], "model": "chirp"}' AS recognition_config))''',
    'named argument': base + f''',
  recognition_config => JSON '{{"language_codes": ["en-US"], "model": "chirp", "auto_decoding_config": {{}}}}')''',
}

for label, tail in attempts.items():
    try:
        result = client.query('SELECT transcripts ' + tail).to_dataframe()['transcripts'][0]
        print(f'{label}: OK -> {result!r}')
    except BadRequest as e:
        print(f'{label}: rejected ->')
        for line in [ln.strip() for ln in str(e).split('\n') if ln.strip()][:3]:
            print(f'    {line}')
    print()
```

The second error prints the signature: `ML.TRANSCRIBE(MODEL, TABLE, [recognition_config => JSON])`. The brackets say optional and the `=>` says named-only — the parser will not take it positionally even inside a `STRUCT`. When a call in this family will not compile, the *"No matching signature"* error is the reference page you want, because it prints what the engine will actually accept.

### 3. What goes in the config, and what the recognizer option costs

The config is a [`RecognitionConfig`](https://cloud.google.com/speech-to-text/v2/docs/reference/rest/v2/projects.locations.recognizers/recognize#recognitionconfig) resource in JSON — the same object the Speech-to-Text API takes directly. Through BigQuery, though, its `model` field has exactly one accepted value. The cell tries five.

```python
for speech_model in ['chirp', 'chirp_2', 'long', 'short', 'telephony']:
    config = ('{"language_codes": ["en-US"], "model": "' + speech_model
              + '", "auto_decoding_config": {}}')
    try:
        result = client.query(f'''
        SELECT transcripts
        FROM ML.TRANSCRIBE(
          MODEL `{PROJECT_ID}.{DATASET_ID}.ml_transcribe_model`,
          (SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.ml_transcribe_audio` WHERE uri LIKE '%hello%'),
          recognition_config => JSON '{config}')
        ''').to_dataframe()['transcripts'][0]
        print(f'{speech_model:10} OK -> {result!r}')
    except BadRequest as e:
        message = ' '.join([ln.strip() for ln in str(e).split(chr(10)) if ln.strip()][:2])
        print(f'{speech_model:10} rejected -> {message[:170]}')
```

The alternative to repeating a config on every call is `SPEECH_RECOGNIZER` on the model, which points at a stored Speech-to-Text recognizer. It carries a constraint the model option itself will tell you about: the recognizer is a regional resource, and BigQuery accepts it from a short list of regions — none of which is the multi-region your BigQuery dataset is probably in. The cell asks for a recognizer in `US` and prints what comes back. It creates nothing: the statement fails before a model exists.

```python
try:
    client.query(f'''
    CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.tmp_recognizer_demo`
      REMOTE WITH CONNECTION `{PROJECT_ID}.{LOCATION}.{CONNECTION_ID}`
      OPTIONS (
        REMOTE_SERVICE_TYPE = 'CLOUD_AI_SPEECH_TO_TEXT_V2',
        SPEECH_RECOGNIZER = 'projects/{PROJECT_ID}/locations/us/recognizers/does-not-exist'
      )
    ''').result()
    print('Model created.')
except BadRequest as e:
    print([ln.strip() for ln in str(e).split('\n') if ln.strip()][0])

print('\nModels in the dataset now:',
      [m.model_id for m in client.list_models(f'{PROJECT_ID}.{DATASET_ID}')])
```

So a recognizer lives in a single region while the transcription runs against a multi-region dataset, and the two are configured in different places. For a notebook — and for anything where the config changes per query — `recognition_config` is the simpler half of the trade. A recognizer earns its keep when one configuration is shared by many callers who should not each be maintaining a JSON literal.

### 4. Inside `ml_transcribe_result`

The `transcripts` column is a convenience over the JSON. The JSON has two properties worth knowing before you rely on it.

**It is keyed by URI.** `results` is not an array — it is an object whose single key is the file's own `uri`, so the accessor has to index it with the row's own column: `ml_transcribe_result.results[uri]`. That is unusual enough to be worth writing down; every other member of this family returns a result whose shape does not depend on the row's data.

**The transcript is in there twice.** `results[uri].transcript` and `results[uri].inline_result.transcript` hold the same object.

The one-second sample produces a small enough result to print whole:

```python
import json

raw = client.query(f'''
SELECT TO_JSON_STRING(ml_transcribe_result) AS result_json
FROM ML.TRANSCRIBE(
  MODEL `{PROJECT_ID}.{DATASET_ID}.ml_transcribe_model`,
  (SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.ml_transcribe_audio` WHERE uri LIKE '%hello%'),
  recognition_config => JSON '{{"language_codes": ["en-US"], "model": "chirp", "auto_decoding_config": {{}}}}'
)
''').to_dataframe()['result_json'][0]

print(json.dumps(json.loads(raw), indent=2))
```

The single key under `results` is the file's own URI — that is the accessor you have to write, and it is why the query below has to index the JSON with the row's own `uri` column. Below it, `transcript` and `inline_result.transcript` carry the same object, and `total_billed_duration` is reported twice: once under `metadata` and once at the top of the result.

The accessors, applied to every file:

```python
query = f'''
SELECT
  REGEXP_EXTRACT(uri, r'[^/]+$') AS audio_file,
  STRING(ml_transcribe_result.results[uri].transcript.results[0].alternatives[0].transcript) AS first_segment,
  ARRAY_LENGTH(JSON_QUERY_ARRAY(ml_transcribe_result.results[uri].transcript.results)) AS segments,
  STRING(ml_transcribe_result.results[uri].transcript.results[0].language_code) AS language_code,
  STRING(ml_transcribe_result.results[uri].metadata.total_billed_duration) AS billed,
  TO_JSON_STRING(ml_transcribe_result.results[uri].transcript)
    = TO_JSON_STRING(ml_transcribe_result.results[uri].inline_result.transcript) AS duplicated
FROM ML.TRANSCRIBE(
  MODEL `{PROJECT_ID}.{DATASET_ID}.ml_transcribe_model`,
  TABLE `{PROJECT_ID}.{DATASET_ID}.ml_transcribe_audio`,
  recognition_config => JSON '{{"language_codes": ["en-US"], "model": "chirp", "auto_decoding_config": {{}}}}'
)
ORDER BY audio_file
'''
pd.set_option('display.max_colwidth', 90)
client.query(query).to_dataframe()
```

Long audio comes back as **several segments**, and `transcripts` is their concatenation — which the cell below checks rather than assumes. If you take `results[0]` because a short file only ever had one, you will silently truncate the first long one.

```python
query = f'''
SELECT
  REGEXP_EXTRACT(uri, r'[^/]+$') AS audio_file,
  ARRAY_LENGTH(JSON_QUERY_ARRAY(ml_transcribe_result.results[uri].transcript.results)) AS segments,
  LENGTH(transcripts) AS transcript_length,
  transcripts = ARRAY_TO_STRING(ARRAY(
    SELECT STRING(segment.alternatives[0].transcript)
    FROM UNNEST(JSON_QUERY_ARRAY(ml_transcribe_result.results[uri].transcript.results)) AS segment
  ), '') AS concatenation_matches
FROM ML.TRANSCRIBE(
  MODEL `{PROJECT_ID}.{DATASET_ID}.ml_transcribe_model`,
  TABLE `{PROJECT_ID}.{DATASET_ID}.ml_transcribe_audio`,
  recognition_config => JSON '{{"language_codes": ["en-US"], "model": "chirp", "auto_decoding_config": {{}}}}'
)
ORDER BY segments DESC, audio_file
'''
client.query(query).to_dataframe()
```

### 5. `language_codes` — asked for, or detected

`language_codes` takes a list of BCP-47 codes, and the literal `"auto"` asks the service to detect. The cell runs the French, Spanish and English samples both ways: once forced to `en-US`, once on `auto`.

```python
frames = {}
for label, codes in [('forced en-US', '["en-US"]'), ('auto', '["auto"]')]:
    config = ('{"language_codes": ' + codes
              + ', "model": "chirp", "auto_decoding_config": {}}')
    frames[label] = client.query(f'''
    SELECT
      REGEXP_EXTRACT(uri, r'[^/]+$') AS audio_file,
      STRING(ml_transcribe_result.results[uri].transcript.results[0].language_code) AS reported,
      transcripts
    FROM ML.TRANSCRIBE(
      MODEL `{PROJECT_ID}.{DATASET_ID}.ml_transcribe_model`,
      (SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.ml_transcribe_audio`
       WHERE uri LIKE '%corbeau%' OR uri LIKE '%multi_es%' OR uri LIKE '%hello%'),
      recognition_config => JSON '{config}')
    ORDER BY audio_file
    ''').to_dataframe().set_index('audio_file')

pd.set_option('display.max_colwidth', 80)
pd.concat(frames, axis=1)
```

Two findings in one table.

**Asking for `en-US` does not make the French audio come back in English** — it comes back in French, correctly, with `en-US` echoed in the `language_code` field. The code you send is not a constraint the model enforces and the code you get back is not a detection result; on a fixed list it is the value you supplied.

**`auto` reports a different alphabet of codes** — bare language subtags rather than the language-region codes you passed in. If you store this column, store which mode produced it, because `en` and `en-US` mean different things here: one is a detection, the other is an echo.

### 6. `features` — and one unsupported key voids the row

`RecognitionConfig` has a `features` object. Through BigQuery, with `chirp`, some of it works and some of it fails, and the failure mode is the part to plan for. The cell tries seven configurations and prints the transcript and the per-row status for each.

```python
feature_sets = {
    'none': '{}',
    'punctuation': '{"enable_automatic_punctuation": true}',
    'word offsets': '{"enable_word_time_offsets": true}',
    'punctuation + offsets': '{"enable_automatic_punctuation": true, "enable_word_time_offsets": true}',
    'word confidence': '{"enable_word_confidence": true}',
    'diarization': '{"diarization_config": {"min_speaker_count": 2, "max_speaker_count": 2}}',
    'profanity filter': '{"profanity_filter": true}',
}

rows = []
for label, features in feature_sets.items():
    config = ('{"language_codes": ["en-US"], "model": "chirp", "auto_decoding_config": {}, '
              '"features": ' + features + '}')
    df = client.query(f'''
    SELECT transcripts, ml_transcribe_status,
           LENGTH(TO_JSON_STRING(ml_transcribe_result)) AS result_bytes
    FROM ML.TRANSCRIBE(
      MODEL `{PROJECT_ID}.{DATASET_ID}.ml_transcribe_model`,
      (SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.ml_transcribe_audio` WHERE uri LIKE '%hello%'),
      recognition_config => JSON '{config}')
    ''').to_dataframe()
    rows.append({'features': label, 'transcripts': repr(df['transcripts'][0]),
                 'result_bytes': df['result_bytes'][0],
                 'status': df['ml_transcribe_status'][0]})

pd.set_option('display.max_colwidth', 100)
pd.DataFrame(rows)
```

Punctuation works and rewrites the text. Word offsets work and grow the JSON. Word confidence, diarization and the profanity filter are rejected — and rejected in a way worth planning around:

- **The row fails, not the query.** `ml_transcribe_status` carries `INVALID_ARGUMENT`, `transcripts` is the empty string, and the job succeeds. A pipeline that does not select the status column records an empty transcript as a transcript.
- **The message does not name the offending key.** *"Config contains unsupported fields"* points at an `error_details_ext` extension that the BigQuery path does not surface, so there is nothing to read. Combine a working key with an unsupported one and the whole row still fails — which means when a config that used to work stops working, you find the culprit by bisecting the `features` object, not by reading the error.

Nothing here says these features are unavailable in Speech-to-Text; it says this model, through this path, refuses them. `chirp` is the only model BigQuery accepts, and the supported feature set follows the model.

Word offsets are the one feature with real structure behind them — a start and end for every word, which is what you need to line a transcript up against the audio:

```python
query = f'''
SELECT
  STRING(w.word) AS word,
  STRING(w.start_offset) AS start_offset,
  STRING(w.end_offset) AS end_offset
FROM ML.TRANSCRIBE(
  MODEL `{PROJECT_ID}.{DATASET_ID}.ml_transcribe_model`,
  (SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.ml_transcribe_audio` WHERE uri LIKE '%brooklyn%'),
  recognition_config => JSON '{{"language_codes": ["en-US"], "model": "chirp", "auto_decoding_config": {{}}, "features": {{"enable_word_time_offsets": true}}}}'
) AS transcribed,
UNNEST(JSON_QUERY_ARRAY(
  transcribed.ml_transcribe_result.results[transcribed.uri].transcript.results[0].alternatives[0].words
)) AS w
'''
client.query(query).to_dataframe()
```

### 7. A row that cannot be transcribed

The second object table includes a text file. Nothing stops you pointing an object table at a folder that has one — and nothing stops the query, either.

```python
query = f'''
SELECT
  REGEXP_EXTRACT(uri, r'[^/]+$') AS audio_file,
  content_type,
  LENGTH(transcripts) AS transcript_length,
  ml_transcribe_status
FROM ML.TRANSCRIBE(
  MODEL `{PROJECT_ID}.{DATASET_ID}.ml_transcribe_model`,
  TABLE `{PROJECT_ID}.{DATASET_ID}.ml_transcribe_mixed`,
  recognition_config => JSON '{{"language_codes": ["en-US"], "model": "chirp", "auto_decoding_config": {{}}}}'
)
ORDER BY ml_transcribe_status DESC, audio_file
'''
pd.set_option('display.max_colwidth', 140)
client.query(query).to_dataframe()
```

The job succeeds. Eight rows carry transcripts and one carries an error, and the only way to tell them apart is the status column. The standard recovery is to persist the results and re-run the failures — the same pattern as the rest of the family, because the failures here are per row rather than per job.

```python
client.query(f'''
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.ml_transcribe_results` AS
SELECT uri, content_type, transcripts, ml_transcribe_status
FROM ML.TRANSCRIBE(
  MODEL `{PROJECT_ID}.{DATASET_ID}.ml_transcribe_model`,
  TABLE `{PROJECT_ID}.{DATASET_ID}.ml_transcribe_mixed`,
  recognition_config => JSON '{{"language_codes": ["en-US"], "model": "chirp", "auto_decoding_config": {{}}}}'
)
''').result()

client.query(f'''
SELECT
  REGEXP_EXTRACT(uri, r'[^/]+$') AS file,
  ml_transcribe_status
FROM `{PROJECT_ID}.{DATASET_ID}.ml_transcribe_results`
WHERE ml_transcribe_status != ''
''').to_dataframe()
```

### 8. What you are billed for is seconds, not bytes

`total_billed_duration` comes back with every result. It is the one number in the response that maps to the invoice, and it has nothing to do with how large the file is — a minute of mp3 and a minute of wav are the same minute. The cell puts file size and billed duration side by side.

```python
query = f'''
SELECT
  REGEXP_EXTRACT(uri, r'[^/]+$') AS audio_file,
  content_type,
  size AS bytes,
  CAST(REGEXP_EXTRACT(
    STRING(ml_transcribe_result.results[uri].metadata.total_billed_duration), r'^([0-9.]+)s$'
  ) AS FLOAT64) AS billed_seconds
FROM ML.TRANSCRIBE(
  MODEL `{PROJECT_ID}.{DATASET_ID}.ml_transcribe_model`,
  TABLE `{PROJECT_ID}.{DATASET_ID}.ml_transcribe_audio`,
  recognition_config => JSON '{{"language_codes": ["en-US"], "model": "chirp", "auto_decoding_config": {{}}}}'
)
ORDER BY billed_seconds DESC
'''
billing = client.query(query).to_dataframe()
billing['kb_per_second'] = (billing['bytes'] / 1024 / billing['billed_seconds']).round(1)
display(billing)

import matplotlib.pyplot as plt

fig, axes = plt.subplots(1, 2, figsize=(11, 4), sharey=True)
axes[0].barh(billing['audio_file'], billing['bytes'] / 1024, color='#4285F4')
axes[0].set_xlabel('file size (KB)')
axes[1].barh(billing['audio_file'], billing['billed_seconds'], color='#EA4335')
axes[1].set_xlabel('billed seconds')
axes[0].invert_yaxis()
fig.suptitle('Bytes are the storage bill; seconds are the transcription bill')
plt.tight_layout()
plt.show()
```

The two panels rank the same files differently, and `kb_per_second` says why: the codecs differ by more than an order of magnitude in how many bytes they spend on a second of audio. Estimate a transcription bill from **duration**; a file-size estimate will be wrong by whatever your encoder chose.

### 9. Is it reproducible?

The other members of this family return the same answer for the same input: a translation, a label set, an entity list. A speech model is doing something different — decoding a waveform under a beam search — and the family's reproducibility does not automatically extend to it.

The cell calls the same file several times, with the query cache off so each call really reaches the service, and counts how many distinct transcripts came back.

```python
no_cache = bigquery.QueryJobConfig(use_query_cache=False)
sql = f'''
SELECT transcripts
FROM ML.TRANSCRIBE(
  MODEL `{PROJECT_ID}.{DATASET_ID}.ml_transcribe_model`,
  (SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.ml_transcribe_audio` WHERE uri LIKE '%corbeau%'),
  recognition_config => JSON '{{"language_codes": ["en-US"], "model": "chirp", "auto_decoding_config": {{}}}}'
)
'''

transcripts = [client.query(sql, job_config=no_cache).to_dataframe()['transcripts'][0]
               for _ in range(4)]

for i, transcript in enumerate(transcripts, 1):
    print(f'{i}: …{transcript[-55:]}')
print(f'\n{len(set(transcripts))} distinct transcript(s) across {len(transcripts)} calls')
```

Whether this particular run happens to return one string or several, the count is not something to design around: it is not fixed by the input, and the query cache will hide it from you unless you turn the cache off. Two consequences:

- **Do not join transcripts to anything as a key**, and do not diff two runs of a pipeline expecting the text to match. Store the transcript with the file's URI and a timestamp, and treat the text as data, not as an identifier.
- **Transcribe once and persist**, as Example 7 does. Re-running is not free and it is not idempotent.

### 10. Speech-to-Text against `AI.GENERATE` on the same audio

Gemini reads audio through an `ObjectRef` — `OBJ.MAKE_REF` names the file and the connection, `OBJ.FETCH_METADATA` resolves it, `OBJ.GET_ACCESS_URL` gives the model a readable URL. Both halves of this query run through the same connection.

Ask it for the same thing `ML.TRANSCRIBE` produces, and then for something `ML.TRANSCRIBE` cannot produce at all — with `chirp`, diarization is one of the rejected features from Example 6.

```python
query = f'''
WITH transcribed AS (
  SELECT REGEXP_EXTRACT(uri, r'[^/]+$') AS audio_file, uri, transcripts
  FROM ML.TRANSCRIBE(
    MODEL `{PROJECT_ID}.{DATASET_ID}.ml_transcribe_model`,
    (SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.ml_transcribe_audio`
     WHERE uri LIKE '%brooklyn%' OR uri LIKE '%corbeau%' OR uri LIKE '%commercial_mono%'),
    recognition_config => JSON '{{"language_codes": ["en-US"], "model": "chirp", "auto_decoding_config": {{}}}}')
)
SELECT
  audio_file,
  transcripts AS ml_transcribe,
  AI.GENERATE(STRUCT(
    'Transcribe this audio. Return only the words spoken.' AS prompt,
    [OBJ.GET_ACCESS_URL(
       OBJ.FETCH_METADATA(OBJ.MAKE_REF(uri, '{PROJECT_ID}.{LOCATION}.{CONNECTION_ID}')), 'r')
    ] AS object_ref_runtime)).result AS ai_generate,
  AI.GENERATE(STRUCT(
    'How many distinct speakers are in this recording? Answer with a number and nothing else.' AS prompt,
    [OBJ.GET_ACCESS_URL(
       OBJ.FETCH_METADATA(OBJ.MAKE_REF(uri, '{PROJECT_ID}.{LOCATION}.{CONNECTION_ID}')), 'r')
    ] AS object_ref_runtime)).result AS ai_speaker_count
FROM transcribed
ORDER BY audio_file
'''
pd.set_option('display.max_colwidth', 250)
client.query(query).to_dataframe()
```

The transcripts differ in a way that is easy to mistake for quality. The generative model returns capitalized, punctuated sentences and spells proper nouns as a writer would; the speech model returns a lowercase stream of words. For reading, one is obviously nicer. For anything downstream, notice what the nicer one is doing: it is *writing*, and a writer that corrects "chrome cast" to "Chromecast" is a writer that can also correct something you needed left alone.

The speaker-count column is the sharper contrast. `ML.TRANSCRIBE` cannot answer that question at all through this path — Example 6 shows diarization rejected — while `AI.GENERATE` returns a bare number for every row, in the requested format, with no status column and no confidence beside it.

Ask the same question of the same file several times, with the cache off:

```python
no_cache = bigquery.QueryJobConfig(use_query_cache=False)
sql = f'''
SELECT AI.GENERATE(STRUCT(
  'How many distinct speakers are in this recording? Answer with a number and nothing else.' AS prompt,
  [OBJ.GET_ACCESS_URL(
     OBJ.FETCH_METADATA(OBJ.MAKE_REF(uri, '{PROJECT_ID}.{LOCATION}.{CONNECTION_ID}')), 'r')
  ] AS object_ref_runtime)).result AS speaker_count
FROM `{PROJECT_ID}.{DATASET_ID}.ml_transcribe_audio`
WHERE uri LIKE '%commercial_mono%'
'''

answers = [client.query(sql, job_config=no_cache).to_dataframe()['speaker_count'][0].strip()
           for _ in range(4)]
print('answers:', answers)
print(f'{len(set(answers))} distinct answer(s) across {len(answers)} asks')
```

The answer does not move. That is worth noticing precisely because it is not evidence: a model asked the same question about the same audio returns the same answer whether or not the answer is right, so agreement across asks measures the model's consistency and nothing about the recording. Example 9 caught `ML.TRANSCRIBE` disagreeing with itself on one file — and the disagreement was visible. A stable wrong answer is the harder failure to catch.

What `ML.TRANSCRIBE` does with this question instead is refuse it: through this path the diarization option is rejected outright, and a rejection is information. If a downstream decision depends on how many people are speaking, take the number from something that can report uncertainty — a diarization service with confidences, or a person — and keep `AI.GENERATE` for the questions where the answer is a draft.

### 11. Does this need a reservation?

Some BigQuery ML functions do not run on on-demand pricing at all: the `bq-ml/functions/image` (image preprocessing functions) in the sibling `bq-ml` project fail outright without a BigQuery Editions reservation, and so does `MATRIX_FACTORIZATION`. It is a fair question for a function that calls out to a service, and it is answerable from this project's own job history rather than from documentation.

`reservation_id` and `edition` on a query job say which slots ran it. `NULL` in both means on-demand.

```python
query = '''
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
LIMIT 5
'''
client.query(query).to_dataframe()
```

Those are this notebook's own calls, and they ran with no reservation and no edition — on-demand, billed by bytes scanned like any other query, with the audio priced separately by Speech-to-Text. The slot requirement that applies to the image preprocessing functions does not apply here.

Two things this does not say. It does not say a reservation is *pointless* — a reservation is how you cap and share slot spend, and these queries would use it if the project had one. And it is a statement about this project today: if a call of yours fails asking for a reservation, the message will say so plainly, the way the image functions' does.

### 12. What the model object actually is

Models are not part of `INFORMATION_SCHEMA` — the `TABLES` view below lists the dataset's tables, including both object tables, and no model is among them — so the model's metadata is read through the client API. What comes back is the clearest statement that nothing trained: `model_type` is unspecified, the single training run carries an empty `trainingOptions` and an empty `evaluationMetrics`, and the only substance in the record is `remoteModelInfo`. `ML.EVALUATE` refuses outright.

```python
import json

display(client.query(f'''
SELECT table_name, table_type
FROM `{PROJECT_ID}.{DATASET_ID}`.INFORMATION_SCHEMA.TABLES
ORDER BY table_name
''').to_dataframe())

model = client.get_model(f'{PROJECT_ID}.{DATASET_ID}.ml_transcribe_model')
print(json.dumps(model.to_api_repr(), indent=2))
print()

try:
    client.query(f'''
    SELECT * FROM ML.EVALUATE(MODEL `{PROJECT_ID}.{DATASET_ID}.ml_transcribe_model`)
    ''').result()
    print('ML.EVALUATE returned a result.')
except Exception as e:
    print('ML.EVALUATE on a Cloud AI service model:\n')
    print(str(e).split(';')[0])
```

---
## Examples — `%%bigquery` Magics

`%%bigquery` cannot interpolate Python variables into the SQL body, so model and table references are written out in full.

```sql
%%bigquery --project {PROJECT_ID}

SELECT
  REGEXP_EXTRACT(uri, r'[^/]+$') AS audio_file,
  transcripts
FROM ML.TRANSCRIBE(
  MODEL `statmike-mlops-349915.bq_ai_functions.ml_transcribe_model`,
  (SELECT * FROM `statmike-mlops-349915.bq_ai_functions.ml_transcribe_audio` WHERE uri LIKE '%time%'),
  recognition_config => JSON '{"language_codes": ["en-US"], "model": "chirp", "auto_decoding_config": {}}')
```

---
## Examples — BigFrames

BigFrames has no `ML.TRANSCRIBE` wrapper. Run the SQL through `read_gbq_query()` and get a BigFrames DataFrame back.

```python
import bigframes.pandas as bpd

bpd.options.bigquery.project = PROJECT_ID
bpd.options.bigquery.location = LOCATION

session = bpd.get_global_session()
df_bf = session.read_gbq_query(f'''
SELECT
  REGEXP_EXTRACT(uri, r'[^/]+$') AS audio_file,
  LENGTH(transcripts) AS characters,
  transcripts
FROM ML.TRANSCRIBE(
  MODEL `{PROJECT_ID}.{DATASET_ID}.ml_transcribe_model`,
  TABLE `{PROJECT_ID}.{DATASET_ID}.ml_transcribe_audio`,
  recognition_config => JSON '{{"language_codes": ["en-US"], "model": "chirp", "auto_decoding_config": {{}}}}'
)
''')
df_bf.to_pandas().sort_values('characters', ascending=False).reset_index(drop=True)
```

---
## Which one should you reach for?

**Reach for `ML.TRANSCRIBE`** when you want the words, at a price per second of audio, in a column you can query — a backlog of call recordings, voice notes, or podcast episodes turned into text you can search and join. It gives you word-level timing, it tells you what it billed, and it fails per row so one bad file does not take down a batch.

**Reach for `functions/ai_generate` (`AI.GENERATE`)** when the transcript is not the deliverable: a summary, a sentiment, an extracted order number, an answer to a question about the recording. It reads audio directly, so it can do in one call what would otherwise be transcribe-then-analyze — and Example 10 is the reason to check its answers rather than store them.

**Reach for both** when the transcript is a record and the analysis is a product: `ML.TRANSCRIBE` for the durable text with its timings and its per-row status, then any of the `functions` (generative functions) over that text — where the input is a column you can inspect, instead of audio you cannot.
