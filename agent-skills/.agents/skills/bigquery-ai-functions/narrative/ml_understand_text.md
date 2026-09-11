# ML.UNDERSTAND_TEXT — BigQuery AI Functions

`ML.UNDERSTAND_TEXT` sends text from a BigQuery table to the [Cloud Natural Language API](https://cloud.google.com/natural-language/docs) and returns its analysis as JSON. One function covers five different analyses — sentiment, entities, entity sentiment, syntax, and content classification — selected by a string option. It is a table-valued function that runs through a **remote model**, so there is a `CREATE MODEL` step, but nothing trains: the model object is a handle on a pre-trained Google API.

**One of five Cloud AI service models.** `ML.UNDERSTAND_TEXT` belongs to a small family of BigQuery ML functions that call a pre-trained Cloud AI service through `CREATE MODEL … REMOTE WITH CONNECTION … OPTIONS(REMOTE_SERVICE_TYPE = …)`. The five members and their service types:

| Function | `REMOTE_SERVICE_TYPE` | Service | Input |
|---|---|---|---|
| `ML.UNDERSTAND_TEXT` *(this notebook)* | `CLOUD_AI_NATURAL_LANGUAGE_V1` | Cloud Natural Language | A table or query with a `text_content` column |
| `functions/ml_translate` (`ML.TRANSLATE`) | `CLOUD_AI_TRANSLATE_V3` | Cloud Translation | A table or query with a `text_content` column |
| `functions/ml_annotate_image` (`ML.ANNOTATE_IMAGE`) | `CLOUD_AI_VISION_V1` | Cloud Vision | An object table of images |
| `functions/ml_transcribe` (`ML.TRANSCRIBE`) | `CLOUD_AI_SPEECH_TO_TEXT_V2` | Speech-to-Text | An object table of audio files |
| `functions/ml_process_document` (`ML.PROCESS_DOCUMENT`) | `CLOUD_AI_DOCUMENT_V1` | Document AI | An object table of documents |

The shared setup — connection, service account roles, `CREATE MODEL` — is written once in `reference/cloud-ai-service-models.md` (Cloud AI Service Models). This notebook repeats the parts you need to run it standalone.

**The five analyses, all through one function:**

| `nlu_option` | What comes back |
|---|---|
| `ANALYZE_SENTIMENT` | Document and per-sentence sentiment, as a score and a magnitude |
| `ANALYZE_ENTITIES` | Named things in the text, with a type and a salience |
| `ANALYZE_ENTITY_SENTIMENT` | The same entities, each carrying its own sentiment |
| `ANALYZE_SYNTAX` | Tokens with part of speech, lemma and dependency edges |
| `CLASSIFY_TEXT` | Content categories from a fixed taxonomy, with confidences |

**When to use it:** you want a fixed, priced, non-generative read on text — sentiment scores that mean the same thing every quarter, entity types from a closed vocabulary, categories from a published taxonomy.

**Alternative:** `functions/ai_generate_double` (`AI.GENERATE_DOUBLE`), `functions/ai_generate_table` (`AI.GENERATE_TABLE`) or `functions/ai_score` (`AI.SCORE`) with a prompt. Example 9 runs sentiment both ways over the same rows.

**Two rules to know before you start:**
- The function reads a column named exactly `text_content`. A table without one errors. Example 8 shows the error and the one-line fix.
- Language support differs **per analysis**, and an unsupported language fails the row, not the job. Example 4 catches that live.

---
## Setup

This function needs two resources: a **Cloud Resource connection** whose service account may call the Cloud Natural Language API, and a **remote model** that names the service. Both are created below and both are idempotent.

> See the `setup` (Setup Reference) for connections and remote models in general, and `reference/cloud-ai-service-models.md` (Cloud AI Service Models) for this family in particular.

```python
PROJECT_ID = 'statmike-mlops-349915'  # <-- Replace with your project ID
LOCATION = 'US'  # BigQuery dataset location — this family runs in US or EU
DATASET_ID = 'bq_ai_functions'  # Shared dataset across all notebooks
CONNECTION_ID = 'bq_ai_functions'  # Shared connection
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

Three services are involved: BigQuery itself, the BigQuery Connection service that owns the connection, and the Cloud Natural Language API that does the work. The cell enables any that are off.

```python
import subprocess as _sp

REQUIRED_APIS = [
    'bigquery.googleapis.com',
    'bigqueryconnection.googleapis.com',
    'language.googleapis.com',
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

The connection's service account — not your user account — is what calls the Cloud Natural Language API. `ML.UNDERSTAND_TEXT` itself needs two grants at the project level, both named on [this function's setup page](https://cloud.google.com/bigquery/docs/analyze-text). A third belongs to the `AI.GENERATE_DOUBLE` comparison later on, not to this function:

| Role | Why |
|---|---|
| `roles/serviceusage.serviceUsageConsumer` | Lets the service account consume an API in this project. **Without it every call fails**, even though `CREATE MODEL` succeeds. |
| `roles/bigquery.connectionUser` | Lets the service account use the connection it belongs to. |
| `roles/aiplatform.user` | Only for Example 9, which calls `AI.GENERATE_DOUBLE` through the same connection to compare against Cloud Natural Language. Not part of `ML.UNDERSTAND_TEXT`. |

> **Two roles is the whole list for this function, and that is not true across the family.** The Cloud Natural Language API has no predefined IAM role of its own — `serviceusage.services.use` is the permission that gates it — so the documented pair is sufficient. `functions/ml_translate` (`ML.TRANSLATE`) needs a third role (`roles/cloudtranslate.user`) that its setup page does not mention, and `functions/ml_transcribe` (`ML.TRANSCRIBE`) needs `roles/speech.client`. The pattern to carry: the BigQuery-side roles get the request to the service, and then the service applies whatever IAM it has of its own.

> **`CREATE MODEL` succeeding tells you nothing about permissions.** Model creation for this family does not contact the service, so it completes against a connection that cannot call anything. The first failure arrives at call time, not at setup time.

The cell below prints which roles the service account already had and which it granted, so the run is auditable. It needs project-level IAM admin rights; if you do not have them, hand the three role names to someone who does.

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
    'roles/aiplatform.user',   # only for the AI.GENERATE_DOUBLE comparison in Example 9
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

### The remote model

Nothing trains here. `CREATE MODEL` writes a model object that records the connection and the service type; the Cloud Natural Language API is called later, per row, by `ML.UNDERSTAND_TEXT`. There is no `ML.EVALUATE`, no weights, and no training data — the model's own metadata says so, and Example 10 reads it.

One model serves all five analyses. The `nlu_option` is an argument to the function, not an option on the model.

```python
client.query(f'''
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.ml_understand_text_model`
  REMOTE WITH CONNECTION `{PROJECT_ID}.{LOCATION}.{CONNECTION_ID}`
  OPTIONS (REMOTE_SERVICE_TYPE = 'CLOUD_AI_NATURAL_LANGUAGE_V1')
''').result()
print('Model ml_understand_text_model ready')
```

### The data — eight pieces of customer feedback in five languages

The languages are deliberate: they are how Example 4 and Example 5 show that support is per analysis, not per API. The text column is named `body`, not `text_content`, because that is what a real table looks like.

```python
client.query(f'''
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.ml_understand_text_feedback` AS
SELECT * FROM UNNEST([
  STRUCT(1 AS feedback_id, 'en' AS expected_language, 'The battery lasts all day but the charger gets far too hot to touch.' AS body),
  STRUCT(2, 'en', 'Shipping from Acme Logistics in Denver was fast and the packaging was perfect.'),
  STRUCT(3, 'es', 'La batería dura todo el día, pero el cargador se calienta demasiado.'),
  STRUCT(4, 'ja', '画面はとても綺麗ですが、アプリの動作が少し遅いです。'),
  STRUCT(5, 'en', 'That actor on TV makes movies in Hollywood and also stars in a variety of popular new TV shows about cooking competitions and travel documentaries filmed across Europe.'),
  STRUCT(6, 'ko', '가격 대비 성능은 훌륭하지만 배송이 너무 오래 걸렸습니다.'),
  STRUCT(7, 'vi', 'Pin dùng được cả ngày nhưng bộ sạc quá nóng.'),
  STRUCT(8, 'en', 'The Northwind Audio team in Seattle replaced my headphones within two days of my email.')
])
''').result()

client.query(f'''
SELECT feedback_id, expected_language, body
FROM `{PROJECT_ID}.{DATASET_ID}.ml_understand_text_feedback`
ORDER BY feedback_id
''').to_dataframe()
```

### Wait for the grants to take effect

A role binding is not usable the instant `gcloud` returns. On a fresh grant the first call still fails with the permission error, so this cell probes with the smallest possible analysis and waits on evidence rather than on a clock. It prints how long it took — on a project where the roles were already in place, that is zero seconds.

```python
import time
from google.api_core.exceptions import BadRequest, Forbidden

probe_sql = f'''
SELECT FLOAT64(ml_understand_text_result.document_sentiment.score) AS score
FROM ML.UNDERSTAND_TEXT(
  MODEL `{PROJECT_ID}.{DATASET_ID}.ml_understand_text_model`,
  (SELECT 'This is wonderful.' AS text_content),
  STRUCT('ANALYZE_SENTIMENT' AS nlu_option)
)
'''

waited = 0
while True:
    try:
        print(f"Probe succeeded after {waited}s: sentiment score {list(client.query(probe_sql).result())[0]['score']}")
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

### 1. `ANALYZE_SENTIMENT` — the raw shape, then the columns

Every analysis returns one JSON column, `ml_understand_text_result`, plus a per-row `ml_understand_text_status`. Here is the JSON for one row before any unpacking.

```python
query = f'''
SELECT feedback_id, ml_understand_text_result, ml_understand_text_status
FROM ML.UNDERSTAND_TEXT(
  MODEL `{PROJECT_ID}.{DATASET_ID}.ml_understand_text_model`,
  (SELECT feedback_id, body AS text_content
   FROM `{PROJECT_ID}.{DATASET_ID}.ml_understand_text_feedback`
   WHERE feedback_id = 1),
  STRUCT('ANALYZE_SENTIMENT' AS nlu_option)
)
'''
print(client.query(query).to_dataframe()['ml_understand_text_result'][0])
```

Two numbers describe the sentiment and they are not the same measurement:

- **`score`** runs from −1 to 1 and says which way the text leans.
- **`magnitude`** is unbounded and says how much emotion is present regardless of direction. A long, evenly mixed review has a high magnitude and a score near zero; a short flat statement has both near zero.

Every row in this table is a single sentence, so magnitude comes back as the absolute value of the score below; the two separate as documents get longer and mix directions.

The API also reports the language it detected, which is worth selecting — it is the input to knowing whether the *next* analysis you want supports this row.

```python
query = f'''
SELECT
  feedback_id,
  text_content,
  STRING(ml_understand_text_result.language) AS detected_language,
  FLOAT64(ml_understand_text_result.document_sentiment.score) AS score,
  FLOAT64(ml_understand_text_result.document_sentiment.magnitude) AS magnitude,
  ml_understand_text_status
FROM ML.UNDERSTAND_TEXT(
  MODEL `{PROJECT_ID}.{DATASET_ID}.ml_understand_text_model`,
  (SELECT feedback_id, body AS text_content
   FROM `{PROJECT_ID}.{DATASET_ID}.ml_understand_text_feedback`),
  STRUCT('ANALYZE_SENTIMENT' AS nlu_option)
)
ORDER BY feedback_id
'''
sentiment = client.query(query).to_dataframe()
sentiment
```

### 2. `flatten_json_output` — let the function do the unpacking

Set `flatten_json_output` to `TRUE` and the JSON column is replaced by separate columns. Which columns you get depends on the analysis, so the flattened shape is not stable across `nlu_option` values — the cell prints the column list for two of them.

```python
for option in ['ANALYZE_SENTIMENT', 'CLASSIFY_TEXT']:
    df = client.query(f'''
    SELECT *
    FROM ML.UNDERSTAND_TEXT(
      MODEL `{PROJECT_ID}.{DATASET_ID}.ml_understand_text_model`,
      (SELECT feedback_id, body AS text_content
       FROM `{PROJECT_ID}.{DATASET_ID}.ml_understand_text_feedback`
       WHERE feedback_id = 5),
      STRUCT('{option}' AS nlu_option, TRUE AS flatten_json_output)
    )
    ''').to_dataframe()
    print(f'{option}:')
    print(f'  columns: {list(df.columns)}')
    print()
```

The flattened columns are still JSON *values* where the content is nested — `sentences` and `categories` come back as JSON arrays, not as rows. Flattening saves you the top-level accessor, not the `UNNEST`.

```python
query = f'''
SELECT feedback_id, language, sentiment, sentences
FROM ML.UNDERSTAND_TEXT(
  MODEL `{PROJECT_ID}.{DATASET_ID}.ml_understand_text_model`,
  (SELECT feedback_id, body AS text_content
   FROM `{PROJECT_ID}.{DATASET_ID}.ml_understand_text_feedback`
   WHERE feedback_id = 1),
  STRUCT('ANALYZE_SENTIMENT' AS nlu_option, TRUE AS flatten_json_output)
)
'''
client.query(query).to_dataframe()
```

### 3. `ANALYZE_ENTITIES` — one row per thing mentioned

`entities` is a JSON array, so `JSON_QUERY_ARRAY` plus `UNNEST` turns one row of feedback into one row per entity. Each carries a `type` from a closed vocabulary and a `salience` — how central the entity is to the text, summing to roughly 1 across the entities of a document.

```python
query = f'''
SELECT
  feedback_id,
  STRING(entity.name) AS entity,
  STRING(entity.type) AS entity_type,
  ROUND(FLOAT64(entity.salience), 3) AS salience
FROM ML.UNDERSTAND_TEXT(
  MODEL `{PROJECT_ID}.{DATASET_ID}.ml_understand_text_model`,
  (SELECT feedback_id, body AS text_content
   FROM `{PROJECT_ID}.{DATASET_ID}.ml_understand_text_feedback`
   WHERE feedback_id IN (2, 8)),
  STRUCT('ANALYZE_ENTITIES' AS nlu_option)
),
UNNEST(JSON_QUERY_ARRAY(ml_understand_text_result.entities)) AS entity
ORDER BY feedback_id, salience DESC
'''
client.query(query).to_dataframe()
```

Read the `entity_type` column before you build on it. The type is the model's guess from context, not a lookup against a registry of companies and places: one of the two company names above comes back as `ORGANIZATION` and the other does not. Salience can also be absent for an entity that is not really *about* anything, which arrives as NULL rather than zero. Treat the types as a signal to filter on, not as ground truth to key a join on.

### 4. `ANALYZE_ENTITY_SENTIMENT`, and the per-row failure that does not fail the job

Same entities, each with its own sentiment — useful when one review praises the battery and condemns the charger.

This is also the example where `ml_understand_text_status` earns its place. Entity sentiment supports fewer languages than sentiment analysis does. The rows in an unsupported language come back **empty with an error string**, while the job itself succeeds. If you select only the result column you will never see it.

```python
query = f'''
SELECT
  feedback_id,
  expected_language,
  ml_understand_text_status,
  ARRAY_LENGTH(JSON_QUERY_ARRAY(ml_understand_text_result.entities)) AS entity_count
FROM ML.UNDERSTAND_TEXT(
  MODEL `{PROJECT_ID}.{DATASET_ID}.ml_understand_text_model`,
  (SELECT feedback_id, expected_language, body AS text_content
   FROM `{PROJECT_ID}.{DATASET_ID}.ml_understand_text_feedback`),
  STRUCT('ANALYZE_ENTITY_SENTIMENT' AS nlu_option)
)
ORDER BY feedback_id
'''
entity_sentiment = client.query(query).to_dataframe()
entity_sentiment
```

The rows that did work carry a sentiment per entity — and an entity can still come back with an empty sentiment object, which surfaces as NULL rather than as zero:

```python
query = f'''
SELECT
  feedback_id,
  STRING(entity.name) AS entity,
  ROUND(FLOAT64(entity.sentiment.score), 2) AS entity_score,
  ROUND(FLOAT64(entity.sentiment.magnitude), 2) AS entity_magnitude
FROM ML.UNDERSTAND_TEXT(
  MODEL `{PROJECT_ID}.{DATASET_ID}.ml_understand_text_model`,
  (SELECT feedback_id, body AS text_content
   FROM `{PROJECT_ID}.{DATASET_ID}.ml_understand_text_feedback`
   WHERE feedback_id = 1),
  STRUCT('ANALYZE_ENTITY_SENTIMENT' AS nlu_option)
),
UNNEST(JSON_QUERY_ARRAY(ml_understand_text_result.entities)) AS entity
ORDER BY entity_score
'''
client.query(query).to_dataframe()
```

**The retry pattern.** Because failures are per row, the fix is to select the failed rows back out and call again — the same shape the documentation recommends for the `RESOURCE EXHAUSTED` case, where a row failed for load rather than for language. For an unsupported language the retry will fail identically, which is itself the answer: check the status column, then decide whether to retry the row or route it somewhere else.

```python
failed = entity_sentiment[entity_sentiment['ml_understand_text_status'] != '']
print(f'{len(failed)} of {len(entity_sentiment)} rows carry an error while the job succeeded:')
for _, row in failed.iterrows():
    print(f"  feedback_id {row['feedback_id']} ({row['expected_language']}): {row['ml_understand_text_status']}")
```

### 5. `ANALYZE_SYNTAX` — tokens, parts of speech, dependencies

The most granular analysis: every token with its lemma, part of speech and dependency edge. The dependency edge is what makes it more than a tokenizer — `head_token_index` points at the token this one attaches to, so the sentence's grammatical structure is recoverable.

Language support does not nest neatly between the analyses: the Korean row that entity sentiment refused is analyzed here without complaint, and the Vietnamese row is refused by both. Per analysis, per row — read the status column.

```python
query = f'''
SELECT
  feedback_id,
  expected_language,
  STRING(ml_understand_text_result.language) AS detected_language,
  ARRAY_LENGTH(JSON_QUERY_ARRAY(ml_understand_text_result.tokens)) AS token_count,
  ml_understand_text_status
FROM ML.UNDERSTAND_TEXT(
  MODEL `{PROJECT_ID}.{DATASET_ID}.ml_understand_text_model`,
  (SELECT feedback_id, expected_language, body AS text_content
   FROM `{PROJECT_ID}.{DATASET_ID}.ml_understand_text_feedback`),
  STRUCT('ANALYZE_SYNTAX' AS nlu_option)
)
ORDER BY feedback_id
'''
client.query(query).to_dataframe()
```

```python
query = f'''
SELECT
  STRING(token.text.content) AS token,
  STRING(token.part_of_speech.tag) AS part_of_speech,
  STRING(token.lemma) AS lemma,
  STRING(token.dependency_edge.label) AS dependency,
  INT64(token.dependency_edge.head_token_index) AS head_index
FROM ML.UNDERSTAND_TEXT(
  MODEL `{PROJECT_ID}.{DATASET_ID}.ml_understand_text_model`,
  (SELECT body AS text_content
   FROM `{PROJECT_ID}.{DATASET_ID}.ml_understand_text_feedback`
   WHERE feedback_id = 1),
  STRUCT('ANALYZE_SYNTAX' AS nlu_option)
),
UNNEST(JSON_QUERY_ARRAY(ml_understand_text_result.tokens)) AS token
'''
client.query(query).to_dataframe()
```

### 6. `CLASSIFY_TEXT` — categories from a fixed taxonomy

Content categories from [a published taxonomy](https://cloud.google.com/natural-language/docs/categories), returned as a path with a confidence. Several can come back for one document, ordered by confidence, and short text can produce a single low-confidence guess where a longer passage produces a ranked list.

```python
query = f'''
SELECT
  feedback_id,
  STRING(category.name) AS category,
  ROUND(FLOAT64(category.confidence), 3) AS confidence
FROM ML.UNDERSTAND_TEXT(
  MODEL `{PROJECT_ID}.{DATASET_ID}.ml_understand_text_model`,
  (SELECT feedback_id, body AS text_content
   FROM `{PROJECT_ID}.{DATASET_ID}.ml_understand_text_feedback`),
  STRUCT('CLASSIFY_TEXT' AS nlu_option)
),
UNNEST(JSON_QUERY_ARRAY(ml_understand_text_result.categories)) AS category
ORDER BY feedback_id, confidence DESC
'''
client.query(query).to_dataframe()
```

`CLASSIFY_TEXT` is the one analysis that rejects `encoding_type`, which is a compile-time error rather than a row-level one.

```python
try:
    client.query(f'''
    SELECT *
    FROM ML.UNDERSTAND_TEXT(
      MODEL `{PROJECT_ID}.{DATASET_ID}.ml_understand_text_model`,
      (SELECT body AS text_content
       FROM `{PROJECT_ID}.{DATASET_ID}.ml_understand_text_feedback`
       WHERE feedback_id = 5),
      STRUCT('CLASSIFY_TEXT' AS nlu_option, 'UTF8' AS encoding_type)
    )
    ''').result()
    print('No error — encoding_type was accepted.')
except BadRequest as e:
    print('Failed, as expected:\n')
    print(str(e).split(';')[0])
```

### 7. `encoding_type` — the option that turns offsets on

Every analysis that returns text spans reports a `begin_offset`, and the default `encoding_type` of `NONE` means those offsets are not computed. Ask for an encoding and the offsets appear — measured **in that encoding's units**, which is the part worth seeing rather than reading about. The text below is Spanish, so accented characters make UTF-8 bytes and UTF-16 code units diverge.

```python
rows = []
for encoding in ['NONE', 'UTF8', 'UTF16', 'UTF32']:
    df = client.query(f'''
    SELECT
      STRING(entity.name) AS entity,
      INT64(entity.mentions[0].text.begin_offset) AS begin_offset
    FROM ML.UNDERSTAND_TEXT(
      MODEL `{PROJECT_ID}.{DATASET_ID}.ml_understand_text_model`,
      (SELECT body AS text_content
       FROM `{PROJECT_ID}.{DATASET_ID}.ml_understand_text_feedback`
       WHERE feedback_id = 3),
      STRUCT('ANALYZE_ENTITIES' AS nlu_option, '{encoding}' AS encoding_type)
    ),
    UNNEST(JSON_QUERY_ARRAY(ml_understand_text_result.entities)) AS entity
    ''').to_dataframe()
    rows.append(df.drop_duplicates('entity').set_index('entity')['begin_offset'].rename(encoding))

text = client.query(f'''
SELECT body FROM `{PROJECT_ID}.{DATASET_ID}.ml_understand_text_feedback` WHERE feedback_id = 3
''').to_dataframe()['body'][0]
print(text)
print()
pd.concat(rows, axis=1)
```

`NONE` returns `-1` for every offset: not "position zero" but "not computed". Where the encodings differ, the difference is the accented characters ahead of the entity — each one costs an extra byte in UTF-8 and nothing in UTF-16 or UTF-32. If you plan to slice the original string using these offsets, the encoding you ask for has to match the units your slicing code counts in.

### 8. The `text_content` rule, and what breaks without it

Pass the table directly and the call fails, because the table's text column is named `body`. The error is caught and printed rather than allowed to stop the notebook.

```python
try:
    client.query(f'''
    SELECT *
    FROM ML.UNDERSTAND_TEXT(
      MODEL `{PROJECT_ID}.{DATASET_ID}.ml_understand_text_model`,
      TABLE `{PROJECT_ID}.{DATASET_ID}.ml_understand_text_feedback`,
      STRUCT('ANALYZE_SENTIMENT' AS nlu_option)
    )
    ''').result()
    print('No error — this table has a text_content column after all.')
except BadRequest as e:
    print('Failed, as expected:\n')
    print(str(e).split(';')[0])
```

Two fixes, and they are not equivalent:

1. **Alias in a subquery** — `(SELECT body AS text_content FROM …)`. What every other example here does. Anything else the subquery selects passes through to the output, which is how `feedback_id` and `expected_language` survive the call.
2. **Name the column `text_content` in the table itself.** Then `TABLE …` works directly. Worth doing only if the table exists to be analyzed.

### 9. Is it deterministic, and how does an LLM compare?

Worth knowing before you build a pipeline on it, and not documented either way. The same sentiment call runs twice with the query cache **off** — a cached result would answer the wrong question — and the scores are compared. The same comparison runs against `AI.GENERATE_DOUBLE` asked for a sentiment score on the same scale.

```python
no_cache = bigquery.QueryJobConfig(use_query_cache=False)

nlu_sql = f'''
SELECT feedback_id, FLOAT64(ml_understand_text_result.document_sentiment.score) AS score
FROM ML.UNDERSTAND_TEXT(
  MODEL `{PROJECT_ID}.{DATASET_ID}.ml_understand_text_model`,
  (SELECT feedback_id, body AS text_content
   FROM `{PROJECT_ID}.{DATASET_ID}.ml_understand_text_feedback`),
  STRUCT('ANALYZE_SENTIMENT' AS nlu_option)
)
ORDER BY feedback_id
'''

llm_sql = f'''
SELECT
  feedback_id,
  (AI.GENERATE_DOUBLE(
    CONCAT('Rate the sentiment of this customer feedback from -1.0 (negative) to 1.0 (positive): ', body)
  )).result AS score
FROM `{PROJECT_ID}.{DATASET_ID}.ml_understand_text_feedback`
ORDER BY feedback_id
'''

frames = {}
for label, sql in [('ML.UNDERSTAND_TEXT', nlu_sql), ('AI.GENERATE_DOUBLE', llm_sql)]:
    run1 = client.query(sql, job_config=no_cache).to_dataframe()
    run2 = client.query(sql, job_config=no_cache).to_dataframe()
    same = (run1['score'] == run2['score']).sum()
    print(f'{label:<19}: {same} of {len(run1)} scores identical across two cache-disabled runs')
    frames[f'{label} run 1'] = run1.set_index('feedback_id')['score']
    frames[f'{label} run 2'] = run2.set_index('feedback_id')['score']

print()
pd.concat(frames, axis=1)
```

The two do not answer quite the same question even when they agree on direction. `ML.UNDERSTAND_TEXT` returns a calibrated score from a fixed model with a companion magnitude; `AI.GENERATE_DOUBLE` returns whatever number the prompt talks the model into, on whatever scale you asked for, with no magnitude and no per-sentence breakdown.

### 10. What the model object actually is

Models are not part of `INFORMATION_SCHEMA` — the `TABLES` view below lists the dataset's tables and the model is not among them — so the model's metadata is read through the client API. What comes back is the clearest statement that nothing trained: `model_type` is unspecified, the single training run carries an empty `trainingOptions` and an empty `evaluationMetrics`, and the only substance in the record is `remoteModelInfo`, holding the service type and the connection. `ML.EVALUATE`, the function every trained BigQuery ML model answers, refuses outright.

```python
import json

# INFORMATION_SCHEMA covers tables — models are not listed here
display(client.query(f'''
SELECT table_name, table_type
FROM `{PROJECT_ID}.{DATASET_ID}`.INFORMATION_SCHEMA.TABLES
ORDER BY table_name
''').to_dataframe())

# Model metadata comes from the client API instead
model = client.get_model(f'{PROJECT_ID}.{DATASET_ID}.ml_understand_text_model')
print(json.dumps(model.to_api_repr(), indent=2))
print()

try:
    client.query(f'''
    SELECT * FROM ML.EVALUATE(MODEL `{PROJECT_ID}.{DATASET_ID}.ml_understand_text_model`)
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
  feedback_id,
  STRING(ml_understand_text_result.language) AS detected_language,
  ROUND(FLOAT64(ml_understand_text_result.document_sentiment.score), 2) AS score,
  ROUND(FLOAT64(ml_understand_text_result.document_sentiment.magnitude), 2) AS magnitude
FROM ML.UNDERSTAND_TEXT(
  MODEL `statmike-mlops-349915.bq_ai_functions.ml_understand_text_model`,
  (SELECT feedback_id, body AS text_content
   FROM `statmike-mlops-349915.bq_ai_functions.ml_understand_text_feedback`),
  STRUCT('ANALYZE_SENTIMENT' AS nlu_option)
)
ORDER BY feedback_id
```

---
## Examples — BigFrames

BigFrames has no `ML.UNDERSTAND_TEXT` wrapper. Run the SQL through `read_gbq_query()` and get a BigFrames DataFrame back.

```python
import bigframes.pandas as bpd

bpd.options.bigquery.project = PROJECT_ID
bpd.options.bigquery.location = LOCATION

session = bpd.get_global_session()
df_bf = session.read_gbq_query(f'''
SELECT
  feedback_id,
  STRING(category.name) AS category,
  ROUND(FLOAT64(category.confidence), 3) AS confidence
FROM ML.UNDERSTAND_TEXT(
  MODEL `{PROJECT_ID}.{DATASET_ID}.ml_understand_text_model`,
  (SELECT feedback_id, body AS text_content
   FROM `{PROJECT_ID}.{DATASET_ID}.ml_understand_text_feedback`),
  STRUCT('CLASSIFY_TEXT' AS nlu_option)
),
UNNEST(JSON_QUERY_ARRAY(ml_understand_text_result.categories)) AS category
''')
df_bf.to_pandas().sort_values(['feedback_id', 'confidence'], ascending=[True, False]).reset_index(drop=True)
```

---
## Which one should you reach for?

**Reach for `ML.UNDERSTAND_TEXT`** when you want the same answer next quarter: a fixed model behind a versioned API, sentiment on a stated scale, entity types and category paths from closed vocabularies, and a per-character price you can forecast. Nothing about the output moves when a generative model default changes.

**Reach for the `AI.*` functions** when the analysis you want is not one of the five — aspect-level summaries, your own category list, extraction into a schema you define — or when the taxonomy here does not match your business. `AI.GENERATE_TABLE` will produce columns you specify; `ML.UNDERSTAND_TEXT` produces the columns it has.

**What the notebook measured, not argued:** Example 9 runs both under a disabled query cache and prints run-to-run stability for each. Examples 4 and 5 show the coverage limit you inherit with the fixed model — per-analysis language support, reported per row.
