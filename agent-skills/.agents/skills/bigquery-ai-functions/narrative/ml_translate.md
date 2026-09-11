# ML.TRANSLATE — BigQuery AI Functions

`ML.TRANSLATE` sends text from a BigQuery table to the [Cloud Translation API](https://cloud.google.com/translate/docs) and returns the translation — or, in its other mode, the detected source language — as a JSON column. It is a table-valued function that runs through a **remote model**, so there is a `CREATE MODEL` step, but nothing trains: the model object is a handle on a pre-trained Google API.

**One of five Cloud AI service models.** `ML.TRANSLATE` belongs to a small family of BigQuery ML functions that call a pre-trained Cloud AI service through `CREATE MODEL … REMOTE WITH CONNECTION … OPTIONS(REMOTE_SERVICE_TYPE = …)`. The five members and their service types:

| Function | `REMOTE_SERVICE_TYPE` | Service | Input |
|---|---|---|---|
| `ML.TRANSLATE` *(this notebook)* | `CLOUD_AI_TRANSLATE_V3` | Cloud Translation | A table or query with a `text_content` column |
| `functions/ml_understand_text` (`ML.UNDERSTAND_TEXT`) | `CLOUD_AI_NATURAL_LANGUAGE_V1` | Cloud Natural Language | A table or query with a `text_content` column |
| `functions/ml_annotate_image` (`ML.ANNOTATE_IMAGE`) | `CLOUD_AI_VISION_V1` | Cloud Vision | An object table of images |
| `functions/ml_transcribe` (`ML.TRANSCRIBE`) | `CLOUD_AI_SPEECH_TO_TEXT_V2` | Speech-to-Text | An object table of audio files |
| `functions/ml_process_document` (`ML.PROCESS_DOCUMENT`) | `CLOUD_AI_DOCUMENT_V1` | Document AI | An object table of documents |

The shared setup — connection, service account roles, `CREATE MODEL` — is written once in `reference/cloud-ai-service-models.md` (Cloud AI Service Models). This notebook repeats the parts you need to run it standalone.

**When to use it:**
- You need stable, per-language machine translation over a column of text, at a published per-character price
- You want the source language detected rather than declared
- You want translation behavior that does not change when a model default moves

**Alternative:** `functions/ai_generate` (`AI.GENERATE`) with a translation prompt. Example 8 runs both over the same rows. The tradeoff is real in both directions and the notebook takes a position at the end.

**Two modes, one function:** `TRANSLATE_TEXT` (requires `target_language_code`) and `DETECT_LANGUAGE` (takes no target). The mode is a string inside the `STRUCT` argument.

**The input-shape rule to know before you start:** the function reads a column named exactly `text_content`. A table without one errors. Example 3 shows the error and the one-line fix.

---
## Setup

This function needs two resources: a **Cloud Resource connection** whose service account may call the Cloud Translation API, and a **remote model** that names the service. Both are created below and both are idempotent.

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

Three services are involved: BigQuery itself, the BigQuery Connection service that owns the connection, and the Cloud Translation API that does the work. The cell enables any that are off.

```python
import subprocess as _sp

REQUIRED_APIS = [
    'bigquery.googleapis.com',
    'bigqueryconnection.googleapis.com',
    'translate.googleapis.com',
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

### The connection, and the role that is easy to miss

The connection's service account — not your user account — is what calls the Cloud Translation API. `ML.TRANSLATE` itself needs three grants at the project level, and [this function's setup page](https://cloud.google.com/bigquery/docs/translate-text) names only the first two. A fourth belongs to the `AI.GENERATE` comparisons later on, not to this function:

| Role | Why | Named in the setup docs |
|---|---|---|
| `roles/serviceusage.serviceUsageConsumer` | Lets the service account consume an API in this project. **Without it every call fails**, even though `CREATE MODEL` succeeds. | Yes |
| `roles/bigquery.connectionUser` | Lets the service account use the connection it belongs to. | Yes |
| `roles/cloudtranslate.user` | Lets it call the Cloud Translation API itself. | **No — found by running it** |
| `roles/aiplatform.user` | Only for Examples 7 and 8, which call `AI.GENERATE` through the same connection to compare against Cloud Translation. | Not part of `ML.TRANSLATE` |

> **`CREATE MODEL` succeeding tells you nothing about permissions.** Model creation for this family does not contact the service, so it completes against a connection that cannot call anything. Measured on this project, with the model created and the `serviceusage` role withheld, the first `ML.TRANSLATE` call failed with:
>
> ```
> bqcx-...@gcp-sa-bigquery-condel.iam.gserviceaccount.com does not have required permission to use
> the project. Please grant it the roles/serviceusage.serviceUsageConsumer role, or a custom role
> with the serviceusage.services.use permission and retry.
> ```
>
> The message names the role, which is more than most IAM failures give you — but it arrives at call time, not at setup time.
>
> **Granting both documented roles is not enough.** With `serviceUsageConsumer` and `connectionUser` in place, the next call failed differently:
>
> ```
> Permission denied: Cloud IAM permission 'cloudtranslate.languageDetectionModels.predict' denied.
> ```
>
> That is the Cloud Translation API refusing the caller, and clearing it takes a third role — `roles/cloudtranslate.user` — that the setup page does not mention. The shape generalizes across this family: the BigQuery-side roles get the request to the service, and then the service applies its own IAM.

The cell below prints which roles the service account already had and which it granted, so the run is auditable. It needs project-level IAM admin rights; if you do not have them, hand the four role names to someone who does.

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
    'roles/cloudtranslate.user',
    'roles/aiplatform.user',   # only for the AI.GENERATE comparisons in Examples 7 and 8
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

Nothing trains here. `CREATE MODEL` writes a model object that records the connection and the service type; the Cloud Translation API is called later, per row, by `ML.TRANSLATE`. There is no `ML.EVALUATE`, no weights, and no training data — the model's own metadata says so, and Example 9 reads it.

```python
client.query(f'''
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.ml_translate_model`
  REMOTE WITH CONNECTION `{PROJECT_ID}.{LOCATION}.{CONNECTION_ID}`
  OPTIONS (REMOTE_SERVICE_TYPE = 'CLOUD_AI_TRANSLATE_V3')
''').result()
print('Model ml_translate_model ready')
```

### The data — eight product reviews in eight languages

Deliberately built with a column named `comment`, not `text_content`, because that is what a real table looks like.

```python
client.query(f'''
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.ml_translate_reviews` AS
SELECT * FROM UNNEST([
  STRUCT(1 AS review_id, 'La batería dura todo el día, pero el cargador se calienta demasiado.' AS comment),
  STRUCT(2, 'Livraison rapide et emballage soigné, je recommande ce vendeur.'),
  STRUCT(3, '画面はとても綺麗ですが、アプリの動作が少し遅いです。'),
  STRUCT(4, 'Die Verarbeitung wirkt hochwertig, allerdings ist das Kabel zu kurz.'),
  STRUCT(5, 'O produto chegou com um arranhão na tampa, mas o suporte resolveu rápido.'),
  STRUCT(6, 'Great sound quality for the price, though the case feels flimsy.'),
  STRUCT(7, 'Il montaggio è stato semplice, le istruzioni però sono poco chiare.'),
  STRUCT(8, '가격 대비 성능은 훌륭하지만 배송이 너무 오래 걸렸습니다.')
])
''').result()

client.query(f'''
SELECT review_id, comment
FROM `{PROJECT_ID}.{DATASET_ID}.ml_translate_reviews`
ORDER BY review_id
''').to_dataframe()
```

### Wait for the grants to take effect

A role binding is not usable the instant `gcloud` returns. On a fresh grant the first call still fails with the permission error above, so this cell probes with the smallest possible translation and waits on evidence rather than on a clock. It prints how long it took — on a project where the roles were already in place, that is zero seconds.

```python
import time
from google.api_core.exceptions import BadRequest, Forbidden

probe_sql = f'''
SELECT STRING(ml_translate_result.translations[0].translated_text) AS out
FROM ML.TRANSLATE(
  MODEL `{PROJECT_ID}.{DATASET_ID}.ml_translate_model`,
  (SELECT 'hello' AS text_content),
  STRUCT('TRANSLATE_TEXT' AS translate_mode, 'es' AS target_language_code)
)
'''

waited = 0
while True:
    try:
        print(f"Probe succeeded after {waited}s: hello -> {list(client.query(probe_sql).result())[0]['out']}")
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

### 1. `DETECT_LANGUAGE` — what language is this?

The simpler of the two modes: no `target_language_code`, and the JSON result carries the detected language and a confidence. The `comment` column is aliased to `text_content` in the subquery, which is the calling convention for every table that does not happen to have that column name.

```python
query = f'''
SELECT
  review_id,
  text_content,
  ml_translate_result,
  ml_translate_status
FROM ML.TRANSLATE(
  MODEL `{PROJECT_ID}.{DATASET_ID}.ml_translate_model`,
  (SELECT review_id, comment AS text_content
   FROM `{PROJECT_ID}.{DATASET_ID}.ml_translate_reviews`),
  STRUCT('DETECT_LANGUAGE' AS translate_mode)
)
ORDER BY review_id
'''
detected = client.query(query).to_dataframe()
detected
```

The result is a JSON blob, not columns. Unpack it with the JSON accessor functions — `STRING()` and `FLOAT64()` — the same way the documentation's examples do.

```python
query = f'''
SELECT
  review_id,
  text_content,
  STRING(ml_translate_result.languages[0].language_code) AS detected_language,
  FLOAT64(ml_translate_result.languages[0].confidence) AS confidence
FROM ML.TRANSLATE(
  MODEL `{PROJECT_ID}.{DATASET_ID}.ml_translate_model`,
  (SELECT review_id, comment AS text_content
   FROM `{PROJECT_ID}.{DATASET_ID}.ml_translate_reviews`),
  STRUCT('DETECT_LANGUAGE' AS translate_mode)
)
ORDER BY review_id
'''
client.query(query).to_dataframe()
```

### 2. `TRANSLATE_TEXT` — translate everything to English

`target_language_code` is required in this mode. The detected source language comes back alongside the translation, so a `TRANSLATE_TEXT` call answers the `DETECT_LANGUAGE` question too.

```python
query = f'''
SELECT
  review_id,
  text_content AS original,
  STRING(ml_translate_result.translations[0].detected_language_code) AS detected,
  STRING(ml_translate_result.translations[0].translated_text) AS english,
  ml_translate_status
FROM ML.TRANSLATE(
  MODEL `{PROJECT_ID}.{DATASET_ID}.ml_translate_model`,
  (SELECT review_id, comment AS text_content
   FROM `{PROJECT_ID}.{DATASET_ID}.ml_translate_reviews`),
  STRUCT('TRANSLATE_TEXT' AS translate_mode, 'en' AS target_language_code)
)
ORDER BY review_id
'''
to_english = client.query(query).to_dataframe()
to_english
```

`ml_translate_status` is empty on success. It is a **per-row** column, not a job-level one: the query job can finish successfully while individual rows carry an error string, which is why every example here selects it or checks it.

### 3. The `text_content` rule, and what breaks without it

Pass the table directly — `TABLE \`…ml_translate_reviews\`` — and the call fails, because the table's text column is named `comment`. The error is caught and printed rather than allowed to stop the notebook.

```python
try:
    client.query(f'''
    SELECT *
    FROM ML.TRANSLATE(
      MODEL `{PROJECT_ID}.{DATASET_ID}.ml_translate_model`,
      TABLE `{PROJECT_ID}.{DATASET_ID}.ml_translate_reviews`,
      STRUCT('TRANSLATE_TEXT' AS translate_mode, 'en' AS target_language_code)
    )
    ''').result()
    print('No error — this table has a text_content column after all.')
except BadRequest as e:
    print('Failed, as expected:\n')
    print(str(e).split(';')[0])
```

Two fixes, and they are not equivalent:

1. **Alias in a subquery** — `(SELECT comment AS text_content FROM …)`. What every other example here does. Carry along any other columns you want in the output; they pass through untouched.
2. **Name the column `text_content` in the table itself.** Then `TABLE …` works directly. This is worth doing only if the table exists to be translated.

Anything the subquery selects is returned beside the result columns, which is how `review_id` survives the call.

### 4. The raw JSON, both modes

The unpacking in Examples 1 and 2 skipped past the full response. Here it is, one row, both modes — including the two fields that are always present and always empty unless you use a glossary or a translation memory.

```python
query = f'''
SELECT 'TRANSLATE_TEXT' AS mode, TO_JSON_STRING(ml_translate_result) AS raw_json
FROM ML.TRANSLATE(
  MODEL `{PROJECT_ID}.{DATASET_ID}.ml_translate_model`,
  (SELECT comment AS text_content
   FROM `{PROJECT_ID}.{DATASET_ID}.ml_translate_reviews` WHERE review_id = 1),
  STRUCT('TRANSLATE_TEXT' AS translate_mode, 'en' AS target_language_code)
)
UNION ALL
SELECT 'DETECT_LANGUAGE', TO_JSON_STRING(ml_translate_result)
FROM ML.TRANSLATE(
  MODEL `{PROJECT_ID}.{DATASET_ID}.ml_translate_model`,
  (SELECT comment AS text_content
   FROM `{PROJECT_ID}.{DATASET_ID}.ml_translate_reviews` WHERE review_id = 1),
  STRUCT('DETECT_LANGUAGE' AS translate_mode)
)
'''
for row in client.query(query).result():
    print(f"{row['mode']}:")
    print(f"  {row['raw_json']}\n")
```

### 5. One target language per call

`target_language_code` is a scalar inside the `STRUCT`, evaluated once for the whole call — not per row. Passing a column reference is a compile-time error, shown first. To fan out over several target languages you issue several calls, which is what the loop below does.

```python
# (a) A per-row target language is not available
try:
    client.query(f'''
    SELECT review_id, ml_translate_status
    FROM ML.TRANSLATE(
      MODEL `{PROJECT_ID}.{DATASET_ID}.ml_translate_model`,
      (SELECT review_id, comment AS text_content, 'fr' AS want
       FROM `{PROJECT_ID}.{DATASET_ID}.ml_translate_reviews`),
      STRUCT('TRANSLATE_TEXT' AS translate_mode, want AS target_language_code)
    )
    ''').result()
    print('(a) Accepted a column as target_language_code.')
except BadRequest as e:
    print('(a) Rejected, as expected:\n')
    print(str(e).split(';')[0], '\n')

# (b) Fan out: one call per target language, unioned into a single result
targets = ['es', 'fr', 'ja']
union = '\nUNION ALL\n'.join(f'''
SELECT '{t}' AS target, review_id,
       STRING(ml_translate_result.translations[0].translated_text) AS translated
FROM ML.TRANSLATE(
  MODEL `{PROJECT_ID}.{DATASET_ID}.ml_translate_model`,
  (SELECT review_id, comment AS text_content
   FROM `{PROJECT_ID}.{DATASET_ID}.ml_translate_reviews` WHERE review_id = 6),
  STRUCT('TRANSLATE_TEXT' AS translate_mode, '{t}' AS target_language_code)
)''' for t in targets)

print('(b) One English review, three target languages:')
client.query(union).to_dataframe().sort_values('target').reset_index(drop=True)
```

### 6. Round trip — English → Japanese → English

Calls nest: the output of one `ML.TRANSLATE` can be the input relation of the next, as long as the inner query aliases its translated column to `text_content`. A round trip is the cheapest sanity check on a translation pipeline you cannot read — the meaning should survive even though the wording will not.

```python
query = f'''
WITH out_and_back AS (
  SELECT
    review_id,
    STRING(ml_translate_result.translations[0].translated_text) AS text_content
  FROM ML.TRANSLATE(
    MODEL `{PROJECT_ID}.{DATASET_ID}.ml_translate_model`,
    (SELECT review_id, comment AS text_content
     FROM `{PROJECT_ID}.{DATASET_ID}.ml_translate_reviews` WHERE review_id IN (6)),
    STRUCT('TRANSLATE_TEXT' AS translate_mode, 'ja' AS target_language_code)
  )
)
SELECT
  text_content AS japanese,
  STRING(ml_translate_result.translations[0].translated_text) AS back_to_english
FROM ML.TRANSLATE(
  MODEL `{PROJECT_ID}.{DATASET_ID}.ml_translate_model`,
  TABLE out_and_back,
  STRUCT('TRANSLATE_TEXT' AS translate_mode, 'en' AS target_language_code)
)
'''
try:
    trip = client.query(query).to_dataframe()
except BadRequest as e:
    print('TABLE on a CTE was rejected — using a subquery instead:\n')
    print(str(e).split(';')[0], '\n')
    query = query.replace('TABLE out_and_back', '(SELECT * FROM out_and_back)')
    trip = client.query(query).to_dataframe()

original = client.query(f'''
SELECT comment FROM `{PROJECT_ID}.{DATASET_ID}.ml_translate_reviews` WHERE review_id = 6
''').to_dataframe()['comment'][0]

print(f'original:        {original}')
print(f'japanese:        {trip["japanese"][0]}')
print(f'back to english: {trip["back_to_english"][0]}')
print(f'\nidentical to the original: {trip["back_to_english"][0] == original}')
```

### 7. Is it deterministic?

Worth knowing before you build a pipeline on it, and not documented either way. The same call runs twice with the query cache **off** — a cached result would answer the wrong question — and the two sets of strings are compared. For contrast the same comparison runs against `AI.GENERATE`, which does the same job with an LLM.

```python
no_cache = bigquery.QueryJobConfig(use_query_cache=False)

translate_sql = f'''
SELECT review_id, STRING(ml_translate_result.translations[0].translated_text) AS out
FROM ML.TRANSLATE(
  MODEL `{PROJECT_ID}.{DATASET_ID}.ml_translate_model`,
  (SELECT review_id, comment AS text_content
   FROM `{PROJECT_ID}.{DATASET_ID}.ml_translate_reviews`),
  STRUCT('TRANSLATE_TEXT' AS translate_mode, 'en' AS target_language_code)
)
ORDER BY review_id
'''

generate_sql = f'''
SELECT review_id,
  AI.GENERATE(
    ('Translate this product review to English. Return only the translation: ', comment)
  ).result AS out
FROM `{PROJECT_ID}.{DATASET_ID}.ml_translate_reviews`
ORDER BY review_id
'''

def run_twice(sql, label):
    a = client.query(sql, job_config=no_cache).to_dataframe()['out'].tolist()
    b = client.query(sql, job_config=no_cache).to_dataframe()['out'].tolist()
    same = sum(x == y for x, y in zip(a, b))
    print(f'{label}: {same} of {len(a)} rows identical across two cache-disabled runs')
    return a, b

ml_a, ml_b = run_twice(translate_sql, 'ML.TRANSLATE ')
ai_a, ai_b = run_twice(generate_sql, 'AI.GENERATE  ')

pd.DataFrame({'ML.TRANSLATE run 1': ml_a, 'ML.TRANSLATE run 2': ml_b,
              'AI.GENERATE run 1': ai_a, 'AI.GENERATE run 2': ai_b})
```

### 8. The same job, side by side

`ML.TRANSLATE` and `AI.GENERATE` over the same eight rows, in one query, so the difference is visible rather than argued.

```python
query = f'''
WITH api AS (
  SELECT review_id,
         text_content AS original,
         STRING(ml_translate_result.translations[0].translated_text) AS translation_api
  FROM ML.TRANSLATE(
    MODEL `{PROJECT_ID}.{DATASET_ID}.ml_translate_model`,
    (SELECT review_id, comment AS text_content
     FROM `{PROJECT_ID}.{DATASET_ID}.ml_translate_reviews`),
    STRUCT('TRANSLATE_TEXT' AS translate_mode, 'en' AS target_language_code)
  )
),
llm AS (
  SELECT review_id,
         AI.GENERATE(
           ('Translate this product review to English. Return only the translation: ', comment)
         ).result AS gemini
  FROM `{PROJECT_ID}.{DATASET_ID}.ml_translate_reviews`
)
SELECT api.review_id, api.original, api.translation_api, llm.gemini
FROM api JOIN llm USING (review_id)
ORDER BY review_id
'''
client.query(query).to_dataframe()
```

### 9. What the model object actually is

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
model = client.get_model(f'{PROJECT_ID}.{DATASET_ID}.ml_translate_model')
print(json.dumps(model.to_api_repr(), indent=2))
print()

try:
    client.query(f'''
    SELECT * FROM ML.EVALUATE(MODEL `{PROJECT_ID}.{DATASET_ID}.ml_translate_model`)
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
  review_id,
  STRING(ml_translate_result.translations[0].detected_language_code) AS detected,
  STRING(ml_translate_result.translations[0].translated_text) AS english
FROM ML.TRANSLATE(
  MODEL `statmike-mlops-349915.bq_ai_functions.ml_translate_model`,
  (SELECT review_id, comment AS text_content
   FROM `statmike-mlops-349915.bq_ai_functions.ml_translate_reviews`),
  STRUCT('TRANSLATE_TEXT' AS translate_mode, 'en' AS target_language_code)
)
ORDER BY review_id
```

---
## Examples — BigFrames

BigFrames has no `ML.TRANSLATE` wrapper. Run the SQL through `read_gbq_query()` and get a BigFrames DataFrame back.

```python
import bigframes.pandas as bpd

bpd.options.bigquery.project = PROJECT_ID
bpd.options.bigquery.location = LOCATION

session = bpd.get_global_session()
df_bf = session.read_gbq_query(f'''
SELECT
  review_id,
  STRING(ml_translate_result.translations[0].detected_language_code) AS detected,
  STRING(ml_translate_result.translations[0].translated_text) AS english
FROM ML.TRANSLATE(
  MODEL `{PROJECT_ID}.{DATASET_ID}.ml_translate_model`,
  (SELECT review_id, comment AS text_content
   FROM `{PROJECT_ID}.{DATASET_ID}.ml_translate_reviews`),
  STRUCT('TRANSLATE_TEXT' AS translate_mode, 'en' AS target_language_code)
)
''')
df_bf.to_pandas().sort_values('review_id').reset_index(drop=True)
```

---
## Which one should you reach for?

**Reach for `ML.TRANSLATE`** when translation is the whole job and you want it to behave the same way tomorrow: a fixed API, a published per-character price, a detected source language for free, and no prompt to maintain or re-test when a model default moves.

**Reach for `AI.GENERATE`** when the job is not really translation — translate *and* summarize, translate *and* keep the brand voice, translate *and* extract the complaint — or when you need to steer register, formality or terminology. One call does what would otherwise be a translation plus a second pass.

**What the notebook measured, not argued:** Example 7 compares run-to-run stability of the two under a disabled query cache, and Example 8 puts their outputs on the same eight rows so you can read them against each other.
