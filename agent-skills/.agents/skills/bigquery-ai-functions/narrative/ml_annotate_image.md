# ML.ANNOTATE_IMAGE — BigQuery AI Functions

`ML.ANNOTATE_IMAGE` sends images referenced by a BigQuery [object table](https://cloud.google.com/bigquery/docs/object-table-introduction) to the [Cloud Vision API](https://cloud.google.com/vision/docs) and returns its annotations as JSON. One call can ask for several kinds of annotation at once — labels, objects, text, landmarks, logos, faces, colors. It is a table-valued function that runs through a **remote model**, so there is a `CREATE MODEL` step, but nothing trains: the model object is a handle on a pre-trained Google API.

**One of five Cloud AI service models.** `ML.ANNOTATE_IMAGE` belongs to a small family of BigQuery ML functions that call a pre-trained Cloud AI service through `CREATE MODEL … REMOTE WITH CONNECTION … OPTIONS(REMOTE_SERVICE_TYPE = …)`. The five members and their service types:

| Function | `REMOTE_SERVICE_TYPE` | Service | Input |
|---|---|---|---|
| `ML.ANNOTATE_IMAGE` *(this notebook)* | `CLOUD_AI_VISION_V1` | Cloud Vision | An object table of images |
| `functions/ml_transcribe` (`ML.TRANSCRIBE`) | `CLOUD_AI_SPEECH_TO_TEXT_V2` | Speech-to-Text | An object table of audio files |
| `functions/ml_process_document` (`ML.PROCESS_DOCUMENT`) | `CLOUD_AI_DOCUMENT_V1` | Document AI | An object table of documents |
| `functions/ml_translate` (`ML.TRANSLATE`) | `CLOUD_AI_TRANSLATE_V3` | Cloud Translation | A table or query with a `text_content` column |
| `functions/ml_understand_text` (`ML.UNDERSTAND_TEXT`) | `CLOUD_AI_NATURAL_LANGUAGE_V1` | Cloud Natural Language | A table or query with a `text_content` column |

The shared setup — connection, service account roles, `CREATE MODEL` — is written once in `reference/cloud-ai-service-models.md` (Cloud AI Service Models). This notebook repeats the parts you need to run it standalone.

**The documented features**, passed as an array in one `STRUCT` argument:

| Feature | What comes back |
|---|---|
| `LABEL_DETECTION` | General labels for the whole image, with confidence |
| `OBJECT_LOCALIZATION` | Named objects with normalized bounding boxes |
| `TEXT_DETECTION` | OCR text plus a box per word |
| `DOCUMENT_TEXT_DETECTION` | The same text with a page/block/paragraph/word structure and confidences |
| `LANDMARK_DETECTION` | Recognized landmarks with latitude and longitude |
| `LOGO_DETECTION` | Recognized brand logos with a box |
| `FACE_DETECTION` | Face boxes with expression *likelihoods* — not identity |
| `IMAGE_PROPERTIES` | Dominant colors with pixel fractions |

**When to use it:** you want a priced, fixed-vocabulary read on images — the same label set and the same coordinates every quarter — or you need OCR boxes, geographic landmark coordinates, or dominant colors that a text model cannot give you.

**Alternative:** `functions/ai_generate` (`AI.GENERATE`) with an image `ObjectRef`. Example 9 runs both over the same images, and the difference is sharper than in the text functions: Vision returns taxonomy terms, the LLM names the specific thing.

**The input-shape rule to know before you start:** this member takes an **object table**, not a text column. Images live in Cloud Storage and the object table points at them.

---
## Setup

This function needs three resources: a **Cloud Resource connection** whose service account may call the Cloud Vision API and read Cloud Storage, an **object table** over the images, and a **remote model** that names the service. All are created below and all are idempotent.

> See the `setup` (Setup Reference) for connections, object tables and remote models in general, and `reference/cloud-ai-service-models.md` (Cloud AI Service Models) for this family in particular.

```python
PROJECT_ID = 'statmike-mlops-349915'  # <-- Replace with your project ID
LOCATION = 'US'  # BigQuery dataset location — this family runs in US or EU
DATASET_ID = 'bq_ai_functions'  # Shared dataset across all notebooks
CONNECTION_ID = 'bq_ai_functions'  # Shared connection
BUCKET = PROJECT_ID  # GCS bucket for the sample images (same name as project)
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

Four services are involved: BigQuery, the BigQuery Connection service that owns the connection, Cloud Storage where the images live, and the Cloud Vision API that does the work. The cell enables any that are off.

```python
import subprocess as _sp

REQUIRED_APIS = [
    'bigquery.googleapis.com',
    'bigqueryconnection.googleapis.com',
    'storage.googleapis.com',
    'vision.googleapis.com',
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

The connection's service account — not your user account — is what calls the Cloud Vision API **and** what reads the images out of Cloud Storage. Four grants at the project level:

| Role | Why | Named in the setup docs |
|---|---|---|
| `roles/serviceusage.serviceUsageConsumer` | Lets the service account consume an API in this project. **Without it every call fails**, even though `CREATE MODEL` succeeds. | Yes |
| `roles/bigquery.connectionUser` | Lets the service account use the connection it belongs to. | Yes |
| `roles/storage.objectViewer` | Lets it read the image bytes behind the object table. Object tables are how this half of the family takes input. | Yes |
| `roles/aiplatform.user` | Only for Example 9, which calls `AI.GENERATE` through the same connection to compare against Vision. | Not part of `ML.ANNOTATE_IMAGE` |

> **The Cloud Vision API has no predefined IAM role of its own** — `serviceusage.services.use` is what gates it, so no fourth Vision-specific grant exists to miss. That is not uniform across the family: `functions/ml_translate` (`ML.TRANSLATE`) needs `roles/cloudtranslate.user` and `functions/ml_transcribe` (`ML.TRANSCRIBE`) needs `roles/speech.client`. The BigQuery-side roles get the request to the service; the service then applies whatever IAM it has.

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

### The images

Eight public sample images from `gs://cloud-samples-data/vision/`, copied into this project's bucket so the object table and its teardown stay inside one project. Each was chosen for a different feature: a street scene for labels, a toy scene for object localization, the Eiffel Tower for landmarks, a logo, two images with text (printed and handwritten), a landscape for colors, and a face.

```python
from google.cloud import storage

storage_client = storage.Client(project=PROJECT_ID)
source_bucket = storage_client.bucket('cloud-samples-data')
target_bucket = storage_client.bucket(BUCKET)

SAMPLES = [
    'label/setagaya.jpeg',                        # street scene at night
    'object_localization/duck_and_truck.jpg',     # toys
    'landmark/eiffel_tower.jpg',                  # landmark
    'logo/google_logo.jpg',                       # logo
    'text/screen.jpg',                            # printed text on a screen
    'handwritten.jpg',                            # handwriting
    'image_properties/bali.jpeg',                 # landscape, for colors
    'face/face_no_surprise.jpg',                  # a face
]

copied = 0
for sample in SAMPLES:
    name = sample.split('/')[-1]
    target = target_bucket.blob(f'bq_ai_functions/ml_annotate_image/{name}')
    if not target.exists():
        source_bucket.copy_blob(source_bucket.blob(f'vision/{sample}'), target_bucket, f'bq_ai_functions/ml_annotate_image/{name}')
        copied += 1

print(f'{copied} newly copied, {len(SAMPLES)} total in gs://{BUCKET}/bq_ai_functions/ml_annotate_image/')
```

### The object table

An object table is an external table whose rows are files, not records: `uri`, `content_type`, `size`, `updated`, and a `ref` the `OBJ.*` functions understand. It reads through the same connection, which is why the service account needed `roles/storage.objectViewer`.

Object tables have **metadata caching** to think about. `object_metadata = 'SIMPLE'` with no cache options means the file list is refreshed when the table is queried, which is what a notebook wants. A production table over millions of objects usually sets `max_staleness` and a refresh interval instead.

```python
client.query(f'''
CREATE OR REPLACE EXTERNAL TABLE `{PROJECT_ID}.{DATASET_ID}.ml_annotate_image_photos`
  WITH CONNECTION `{PROJECT_ID}.{LOCATION}.{CONNECTION_ID}`
  OPTIONS (
    object_metadata = 'SIMPLE',
    uris = ['gs://{BUCKET}/bq_ai_functions/ml_annotate_image/*']
  )
''').result()
print('Object table ml_annotate_image_photos ready')

client.query(f'''
SELECT REGEXP_EXTRACT(uri, r'[^/]+$') AS image, content_type, size
FROM `{PROJECT_ID}.{DATASET_ID}.ml_annotate_image_photos`
ORDER BY image
''').to_dataframe()
```

### The remote model

Nothing trains here. `CREATE MODEL` writes a model object that records the connection and the service type; the Cloud Vision API is called later, per image, by `ML.ANNOTATE_IMAGE`. There is no `ML.EVALUATE`, no weights, and no training data — the model's own metadata says so, and Example 10 reads it.

One model serves every feature. The feature list is an argument to the function, not an option on the model.

```python
client.query(f'''
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.ml_annotate_image_model`
  REMOTE WITH CONNECTION `{PROJECT_ID}.{LOCATION}.{CONNECTION_ID}`
  OPTIONS (REMOTE_SERVICE_TYPE = 'CLOUD_AI_VISION_V1')
''').result()
print('Model ml_annotate_image_model ready')
```

### Wait for the grants to take effect

A role binding is not usable the instant `gcloud` returns. On a fresh grant the first call still fails with a permission error, so this cell probes with a single image and waits on evidence rather than on a clock. It prints how long it took — on a project where the roles were already in place, that is zero seconds.

```python
import time
from google.api_core.exceptions import BadRequest, Forbidden

probe_sql = f'''
SELECT STRING(ml_annotate_image_result.label_annotations[0].description) AS top_label
FROM ML.ANNOTATE_IMAGE(
  MODEL `{PROJECT_ID}.{DATASET_ID}.ml_annotate_image_model`,
  (SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.ml_annotate_image_photos` WHERE uri LIKE '%duck_and_truck%'),
  STRUCT(['LABEL_DETECTION'] AS vision_features)
)
'''

waited = 0
while True:
    try:
        print(f"Probe succeeded after {waited}s: top label {list(client.query(probe_sql).result())[0]['top_label']}")
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

### 1. `LABEL_DETECTION` — what is in this picture?

The output is the object table's columns plus `ml_annotate_image_result` (JSON) and a per-row `ml_annotate_image_status`. `label_annotations` is an array, so `JSON_QUERY_ARRAY` plus `UNNEST` gives one row per label.

```python
query = f'''
SELECT
  REGEXP_EXTRACT(uri, r'[^/]+$') AS image,
  STRING(annotation.description) AS label,
  ROUND(FLOAT64(annotation.score), 3) AS score
FROM ML.ANNOTATE_IMAGE(
  MODEL `{PROJECT_ID}.{DATASET_ID}.ml_annotate_image_model`,
  TABLE `{PROJECT_ID}.{DATASET_ID}.ml_annotate_image_photos`,
  STRUCT(['LABEL_DETECTION'] AS vision_features)
) AS annotated,
UNNEST(JSON_QUERY_ARRAY(annotated.ml_annotate_image_result.label_annotations)) AS annotation
QUALIFY ROW_NUMBER() OVER (PARTITION BY image ORDER BY FLOAT64(annotation.score) DESC) <= 3
ORDER BY image, score DESC
'''
client.query(query).to_dataframe()
```

### 2. Many features in one call — and what comes back

Ask for seven features at once — everything except `DOCUMENT_TEXT_DETECTION`, which Example 4 holds back so it can be compared against `TEXT_DETECTION` on its own. The interesting part is not the payload, it is which keys are **present**: a feature that found nothing does not return an empty array, it returns nothing at all, so code that assumes a key exists breaks on the first image without a logo.

```python
query = f'''
SELECT
  REGEXP_EXTRACT(uri, r'[^/]+$') AS image,
  LENGTH(TO_JSON_STRING(ml_annotate_image_result)) AS result_bytes,
  ARRAY_TO_STRING(
    ARRAY(SELECT key FROM UNNEST(JSON_KEYS(ml_annotate_image_result, 1)) AS key ORDER BY key),
    ', ') AS keys_returned,
  ml_annotate_image_status
FROM ML.ANNOTATE_IMAGE(
  MODEL `{PROJECT_ID}.{DATASET_ID}.ml_annotate_image_model`,
  TABLE `{PROJECT_ID}.{DATASET_ID}.ml_annotate_image_photos`,
  STRUCT(['LABEL_DETECTION', 'OBJECT_LOCALIZATION', 'LANDMARK_DETECTION', 'LOGO_DETECTION',
          'TEXT_DETECTION', 'IMAGE_PROPERTIES', 'FACE_DETECTION'] AS vision_features)
)
ORDER BY image
'''
pd.set_option('display.max_colwidth', 200)
client.query(query).to_dataframe()
```

Two things in that output are worth keeping:

- **`crop_hints_annotation` arrives without being asked for.** It is not in the documented feature list, and no feature above requests it. Budget for the payload you get, not the payload you asked for.
- **The result size varies by more than an order of magnitude** across these eight images, and the amount of writing in the picture is what drives it: `TEXT_DETECTION` returns a bounding box per word, so the screenshot and the handwritten page cost more than ten times the JSON of the landscape with nothing to read. The face image sits in between on its own account — `FACE_DETECTION` returns a landmark per facial feature. Budget by content, not by image count.

### 3. `OBJECT_LOCALIZATION` — named things, with boxes

Object localization returns **normalized** vertices: fractions of the image width and height, so they survive resizing. Four vertices, clockwise from the top left.

```python
query = f'''
SELECT
  REGEXP_EXTRACT(uri, r'[^/]+$') AS image,
  STRING(object.name) AS object_name,
  ROUND(FLOAT64(object.score), 3) AS score,
  ROUND(FLOAT64(object.bounding_poly.normalized_vertices[0].x), 3) AS x0,
  ROUND(FLOAT64(object.bounding_poly.normalized_vertices[0].y), 3) AS y0,
  ROUND(FLOAT64(object.bounding_poly.normalized_vertices[2].x), 3) AS x1,
  ROUND(FLOAT64(object.bounding_poly.normalized_vertices[2].y), 3) AS y1
FROM ML.ANNOTATE_IMAGE(
  MODEL `{PROJECT_ID}.{DATASET_ID}.ml_annotate_image_model`,
  (SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.ml_annotate_image_photos` WHERE uri LIKE '%duck_and_truck%'),
  STRUCT(['OBJECT_LOCALIZATION'] AS vision_features)
) AS annotated,
UNNEST(JSON_QUERY_ARRAY(annotated.ml_annotate_image_result.localized_object_annotations)) AS object
ORDER BY score DESC
'''
boxes = client.query(query).to_dataframe()
boxes
```

Drawn on the image, so the coordinates can be checked rather than trusted:

```python
import io
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from PIL import Image

blob = target_bucket.blob(f'bq_ai_functions/ml_annotate_image/duck_and_truck.jpg')
img = Image.open(io.BytesIO(blob.download_as_bytes()))
width, height = img.size

fig, ax = plt.subplots(figsize=(7, 5))
ax.imshow(img)

# Several names can share one box, so group by geometry and label each box once
for coords, group in boxes.groupby(['x0', 'y0', 'x1', 'y1'], sort=False):
    x0, y0, x1, y1 = coords
    ax.add_patch(patches.Rectangle(
        (x0 * width, y0 * height), (x1 - x0) * width, (y1 - y0) * height,
        fill=False, linewidth=2, edgecolor='#4285F4'))
    ax.text(x0 * width, y0 * height - 4,
            '\n'.join(f"{row['object_name']} {row['score']:.2f}" for _, row in group.iterrows()),
            color='white', fontsize=9, va='bottom',
            bbox=dict(facecolor='#4285F4', pad=1, edgecolor='none'))
ax.set_title(f'OBJECT_LOCALIZATION — {len(boxes)} annotations on '
             f'{boxes.groupby(["x0", "y0", "x1", "y1"]).ngroups} boxes ({width}x{height} px)')
ax.axis('off')
plt.tight_layout()
plt.show()
```

The rows are annotations, not objects. One box here carries three names at three confidences, because the model is telling you what it might be rather than committing to one label — and the box drawn for the toy truck does not include the wheels it also found, which get boxes of their own inside it. Count distinct boxes, not rows, if you are counting things in the picture.

### 4. `TEXT_DETECTION` vs `DOCUMENT_TEXT_DETECTION`

Both read text and both fill `full_text_annotation.text`. The difference is what surrounds it: `DOCUMENT_TEXT_DETECTION` is built for dense pages and adds a `confidence` at every level of the page/block/paragraph/word/symbol hierarchy, which is what makes its payload larger for the same words.

The cell runs both over the two images that contain text and compares what came back.

```python
frames = {}
for feature in ['TEXT_DETECTION', 'DOCUMENT_TEXT_DETECTION']:
    frames[feature] = client.query(f'''
    SELECT
      REGEXP_EXTRACT(uri, r'[^/]+$') AS image,
      LENGTH(STRING(ml_annotate_image_result.full_text_annotation.text)) AS characters,
      ARRAY_LENGTH(JSON_QUERY_ARRAY(ml_annotate_image_result.text_annotations)) AS text_annotations,
      LENGTH(TO_JSON_STRING(ml_annotate_image_result)) AS result_bytes
    FROM ML.ANNOTATE_IMAGE(
      MODEL `{PROJECT_ID}.{DATASET_ID}.ml_annotate_image_model`,
      (SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.ml_annotate_image_photos`
       WHERE uri LIKE '%handwritten%' OR uri LIKE '%screen%'),
      STRUCT(['{feature}'] AS vision_features)
    )
    ORDER BY image
    ''').to_dataframe().set_index('image')

pd.concat(frames, axis=1)
```

And the text itself, from the handwritten sample:

```python
query = f'''
SELECT STRING(ml_annotate_image_result.full_text_annotation.text) AS extracted_text
FROM ML.ANNOTATE_IMAGE(
  MODEL `{PROJECT_ID}.{DATASET_ID}.ml_annotate_image_model`,
  (SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.ml_annotate_image_photos` WHERE uri LIKE '%handwritten%'),
  STRUCT(['DOCUMENT_TEXT_DETECTION'] AS vision_features)
)
'''
print(client.query(query).to_dataframe()['extracted_text'][0])
```

### 5. `LANDMARK_DETECTION` — and a JSON trap worth knowing

Landmarks come back with coordinates, which is the thing no language model gives you reliably: a latitude and longitude you can join to other geography.

The bounding box here is in **absolute pixels**, not normalized fractions, and it exposes a JSON detail that will bite: **a zero-valued field is omitted from the response entirely**. A vertex at the origin is `{}`, so `INT64(vertex.x)` returns NULL and not `0`. Coalesce it.

```python
query = f'''
SELECT
  STRING(landmark.description) AS landmark,
  ROUND(FLOAT64(landmark.score), 3) AS score,
  ROUND(FLOAT64(landmark.locations[0].lat_lng.latitude), 5) AS latitude,
  ROUND(FLOAT64(landmark.locations[0].lat_lng.longitude), 5) AS longitude,
  TO_JSON_STRING(landmark.bounding_poly.vertices[0]) AS first_vertex_raw,
  INT64(landmark.bounding_poly.vertices[0].x) AS x_naive,
  IFNULL(INT64(landmark.bounding_poly.vertices[0].x), 0) AS x_coalesced
FROM ML.ANNOTATE_IMAGE(
  MODEL `{PROJECT_ID}.{DATASET_ID}.ml_annotate_image_model`,
  (SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.ml_annotate_image_photos` WHERE uri LIKE '%eiffel%'),
  STRUCT(['LANDMARK_DETECTION'] AS vision_features)
) AS annotated,
UNNEST(JSON_QUERY_ARRAY(annotated.ml_annotate_image_result.landmark_annotations)) AS landmark
ORDER BY score DESC
'''
client.query(query).to_dataframe()
```

### 6. `LOGO_DETECTION` and `FACE_DETECTION`

Two features in one call, over two images.

`FACE_DETECTION` finds faces and rates expressions on a **likelihood scale** — `VERY_UNLIKELY` through `VERY_LIKELY` as strings, not numbers. It does not identify anyone: there is no name, no ID, and nothing to join against. Read the likelihoods as the model's guess about an expression, and note that a guess about an expression is not a measurement of an emotion.

```python
query = f'''
SELECT
  REGEXP_EXTRACT(uri, r'[^/]+$') AS image,
  STRING(annotation.description) AS logo,
  ROUND(FLOAT64(annotation.score), 3) AS logo_score
FROM ML.ANNOTATE_IMAGE(
  MODEL `{PROJECT_ID}.{DATASET_ID}.ml_annotate_image_model`,
  (SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.ml_annotate_image_photos` WHERE uri LIKE '%logo%'),
  STRUCT(['LOGO_DETECTION'] AS vision_features)
) AS annotated,
UNNEST(JSON_QUERY_ARRAY(annotated.ml_annotate_image_result.logo_annotations)) AS annotation
'''
display(client.query(query).to_dataframe())

query = f'''
SELECT
  ROUND(FLOAT64(face.detection_confidence), 3) AS detection_confidence,
  STRING(face.joy_likelihood) AS joy,
  STRING(face.sorrow_likelihood) AS sorrow,
  STRING(face.anger_likelihood) AS anger,
  STRING(face.surprise_likelihood) AS surprise,
  STRING(face.headwear_likelihood) AS headwear,
  ROUND(FLOAT64(face.roll_angle), 1) AS roll_angle
FROM ML.ANNOTATE_IMAGE(
  MODEL `{PROJECT_ID}.{DATASET_ID}.ml_annotate_image_model`,
  (SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.ml_annotate_image_photos` WHERE uri LIKE '%face%'),
  STRUCT(['FACE_DETECTION'] AS vision_features)
) AS annotated,
UNNEST(JSON_QUERY_ARRAY(annotated.ml_annotate_image_result.face_annotations)) AS face
'''
client.query(query).to_dataframe()
```

The sample file is named `face_no_surprise.jpg` and the API returns `surprise: LIKELY`. Whoever named the file and the model looking at it read the same expression two different ways, which is the whole caution in one row: a likelihood is the model's guess at an expression, an expression is not an emotion, and neither party here has access to what the person was feeling. Treat these columns as image features, not as a measurement of a state of mind — and think about who is in the picture before you store them.

### 7. `IMAGE_PROPERTIES` — dominant colors

Each dominant color carries an RGB triple, a `score`, and a `pixel_fraction` — the share of the image that color covers. The two are different questions: `score` ranks importance, `pixel_fraction` measures area, and they do not agree.

```python
query = f'''
SELECT
  ROUND(FLOAT64(color.score), 4) AS score,
  ROUND(FLOAT64(color.pixel_fraction), 4) AS pixel_fraction,
  IFNULL(INT64(color.color.red), 0) AS red,
  IFNULL(INT64(color.color.green), 0) AS green,
  IFNULL(INT64(color.color.blue), 0) AS blue
FROM ML.ANNOTATE_IMAGE(
  MODEL `{PROJECT_ID}.{DATASET_ID}.ml_annotate_image_model`,
  (SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.ml_annotate_image_photos` WHERE uri LIKE '%bali%'),
  STRUCT(['IMAGE_PROPERTIES'] AS vision_features)
) AS annotated,
UNNEST(JSON_QUERY_ARRAY(annotated.ml_annotate_image_result.image_properties_annotation.dominant_colors.colors)) AS color
ORDER BY score DESC
'''
colors = client.query(query).to_dataframe()
display(colors)

blob = target_bucket.blob(f'bq_ai_functions/ml_annotate_image/bali.jpeg')
img = Image.open(io.BytesIO(blob.download_as_bytes()))

hexes = [f"#{int(r):02x}{int(g):02x}{int(b):02x}"
         for r, g, b in zip(colors['red'], colors['green'], colors['blue'])]

fig, axes = plt.subplots(1, 3, figsize=(13, 4), gridspec_kw={'width_ratios': [1.1, 1, 1]})
axes[0].imshow(img)
axes[0].axis('off')
axes[0].set_title('bali.jpeg')

for ax, column in zip(axes[1:], ['score', 'pixel_fraction']):
    ax.barh(range(len(colors)), colors[column], color=hexes, edgecolor='#333333')
    ax.set_yticks(range(len(colors)))
    ax.set_yticklabels(hexes if column == 'score' else [])
    ax.invert_yaxis()
    ax.set_xlabel(column)
    ax.set_title(f'{column} — bars drawn in the color they report')

plt.tight_layout()
plt.show()
```

Both panels are ordered by `score`, so the second one being out of order is the finding: the color the API ranks first covers barely more than one percent of the pixels, and the color covering the largest share of the image sits in the middle of the ranking. `score` is a judgment about which colors characterize the image; `pixel_fraction` is arithmetic on the pixels. Pick the one that matches your question — "what color is this product" is usually the first, "is this photo mostly sky" the second.

### 8. What the feature list will and will not accept

The syntax page lists eight features. That list is what is supported; it is not the same as what the function parses. The cell tries three names that are Vision API features but are **not** on the BigQuery list, and one that is not a Vision feature at all, and prints what each does.

```python
for feature in ['SAFE_SEARCH_DETECTION', 'CROP_HINTS', 'WEB_DETECTION', 'BANANA_DETECTION']:
    try:
        df = client.query(f'''
        SELECT
          ARRAY_TO_STRING(ARRAY(SELECT key FROM UNNEST(JSON_KEYS(ml_annotate_image_result, 1)) AS key ORDER BY key), ', ') AS keys_returned
        FROM ML.ANNOTATE_IMAGE(
          MODEL `{PROJECT_ID}.{DATASET_ID}.ml_annotate_image_model`,
          (SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.ml_annotate_image_photos` WHERE uri LIKE '%eiffel%'),
          STRUCT(['{feature}'] AS vision_features)
        )
        ''').to_dataframe()
        print(f'{feature}: accepted, keys returned -> {df["keys_returned"][0] or "(none)"}')
    except BadRequest as e:
        print(f'{feature}: rejected -> {str(e).split(chr(10))[1]}')
```

Three names outside the documented eight are accepted and one is rejected by name, so the parser has a list of its own. Take the documented eight as the supported surface — an undocumented feature that parses today is not a commitment, and one of the three returns nothing here even though it parses.

### 9. Vision against `AI.GENERATE` on the same images

`AI.GENERATE` reads an image through an `ObjectRef` — `OBJ.MAKE_REF` names the file and the connection, `OBJ.FETCH_METADATA` resolves it, `OBJ.GET_ACCESS_URL` gives the model a readable URL. Both halves of this query run through the same connection.

Ask both for the same thing — five labels — and read the two columns against each other.

```python
query = f'''
WITH vision AS (
  SELECT
    REGEXP_EXTRACT(uri, r'[^/]+$') AS image,
    uri,
    ARRAY_TO_STRING(ARRAY(
      SELECT STRING(label.description)
      FROM UNNEST(JSON_QUERY_ARRAY(ml_annotate_image_result.label_annotations)) AS label
      LIMIT 5), ', ') AS vision_labels
  FROM ML.ANNOTATE_IMAGE(
    MODEL `{PROJECT_ID}.{DATASET_ID}.ml_annotate_image_model`,
    TABLE `{PROJECT_ID}.{DATASET_ID}.ml_annotate_image_photos`,
    STRUCT(['LABEL_DETECTION'] AS vision_features))
)
SELECT
  image,
  vision_labels,
  AI.GENERATE(STRUCT(
    'List the five most prominent labels for this image, comma separated, no other text.' AS prompt,
    [OBJ.GET_ACCESS_URL(
       OBJ.FETCH_METADATA(OBJ.MAKE_REF(uri, '{PROJECT_ID}.{LOCATION}.{CONNECTION_ID}')), 'r')
    ] AS object_ref_runtime
  )).result AS gemini_labels
FROM vision
ORDER BY image
'''
client.query(query).to_dataframe()
```

The split in that table is the whole argument for keeping both functions around. Vision answers *what kind of thing is this* from a fixed vocabulary; the LLM answers *what is this*, naming specific places, products and brands. One is a classifier with a stable label set you can group by across quarters; the other is a describer whose vocabulary is unbounded and whose wording moves.

### 10. What the model object actually is

Models are not part of `INFORMATION_SCHEMA` — the `TABLES` view below lists the dataset's tables, including the object table, and the model is not among them — so the model's metadata is read through the client API. What comes back is the clearest statement that nothing trained: `model_type` is unspecified, the single training run carries an empty `trainingOptions` and an empty `evaluationMetrics`, and the only substance in the record is `remoteModelInfo`. `ML.EVALUATE` refuses outright.

```python
import json

display(client.query(f'''
SELECT table_name, table_type
FROM `{PROJECT_ID}.{DATASET_ID}`.INFORMATION_SCHEMA.TABLES
ORDER BY table_name
''').to_dataframe())

model = client.get_model(f'{PROJECT_ID}.{DATASET_ID}.ml_annotate_image_model')
print(json.dumps(model.to_api_repr(), indent=2))
print()

try:
    client.query(f'''
    SELECT * FROM ML.EVALUATE(MODEL `{PROJECT_ID}.{DATASET_ID}.ml_annotate_image_model`)
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
  REGEXP_EXTRACT(uri, r'[^/]+$') AS image,
  STRING(annotation.description) AS label,
  ROUND(FLOAT64(annotation.score), 3) AS score
FROM ML.ANNOTATE_IMAGE(
  MODEL `statmike-mlops-349915.bq_ai_functions.ml_annotate_image_model`,
  TABLE `statmike-mlops-349915.bq_ai_functions.ml_annotate_image_photos`,
  STRUCT(['LABEL_DETECTION'] AS vision_features)) AS annotated,
UNNEST(JSON_QUERY_ARRAY(annotated.ml_annotate_image_result.label_annotations)) AS annotation
QUALIFY ROW_NUMBER() OVER (PARTITION BY image ORDER BY FLOAT64(annotation.score) DESC) = 1
ORDER BY image
```

---
## Examples — BigFrames

BigFrames has no `ML.ANNOTATE_IMAGE` wrapper. Run the SQL through `read_gbq_query()` and get a BigFrames DataFrame back.

```python
import bigframes.pandas as bpd

bpd.options.bigquery.project = PROJECT_ID
bpd.options.bigquery.location = LOCATION

session = bpd.get_global_session()
df_bf = session.read_gbq_query(f'''
SELECT
  REGEXP_EXTRACT(uri, r'[^/]+$') AS image,
  ARRAY_LENGTH(JSON_QUERY_ARRAY(ml_annotate_image_result.label_annotations)) AS labels_returned,
  STRING(ml_annotate_image_result.label_annotations[0].description) AS top_label
FROM ML.ANNOTATE_IMAGE(
  MODEL `{PROJECT_ID}.{DATASET_ID}.ml_annotate_image_model`,
  TABLE `{PROJECT_ID}.{DATASET_ID}.ml_annotate_image_photos`,
  STRUCT(['LABEL_DETECTION'] AS vision_features)
)
''')
df_bf.to_pandas().sort_values('image').reset_index(drop=True)
```

---
## Which one should you reach for?

**Reach for `ML.ANNOTATE_IMAGE`** when you want image annotation that behaves the same way next quarter: a fixed label vocabulary you can group by, bounding boxes in a documented coordinate system, landmark latitude and longitude, OCR with a box per word, and dominant colors with pixel fractions. None of that moves when a generative model default changes, and it is priced per image per feature.

**Reach for `functions/ai_generate` (`AI.GENERATE`)** when you need the specific thing named rather than categorized, when the question is compound — *is this photo usable for the catalog, and why not* — or when you want the answer in a schema you define. Example 9 shows the difference on the same eight images.

**A note on the two OCR paths.** For a photo with words in it, `TEXT_DETECTION` here is the right tool. For a scanned form or invoice, `functions/ml_process_document` (`ML.PROCESS_DOCUMENT`) and Document AI are: they return the *fields*, not just the text.
