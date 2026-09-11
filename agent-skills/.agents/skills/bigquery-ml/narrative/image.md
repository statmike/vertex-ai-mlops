
# Image Preprocessing — `ML.DECODE_IMAGE`, `ML.RESIZE_IMAGE`, `ML.CONVERT_COLOR_SPACE`, `ML.CONVERT_IMAGE_TYPE`

Four model-free scalar functions that turn image **bytes** into the numeric `STRUCT` a vision model consumes: decode, resize, change color space, quantize to integers. They train nothing, create no model object, and nest freely inside one another and inside a `TRANSFORM` clause.

They are also the least accurately documented family in this project, which is most of what this notebook is for. Everything below is measured here, against images this notebook builds pixel by pixel, so every claim has a cell you can read.

> **GOTCHA — these four functions require a BigQuery Editions reservation.** On-demand (per-byte) pricing fails outright. Setup demonstrates the exact error, then creates a small autoscaling `ENTERPRISE` reservation and deletes it in Cleanup. **None of the four official reference pages mentions this.** `MATRIX_FACTORIZATION` (`models/matrix_factorization` (`models/matrix_factorization/`)) is the only other thing in this project with the same requirement.

**What this notebook establishes, all measured here rather than quoted:**

1. The output `STRUCT`'s fields are named **`dimensions`** and **`values`** — not `shape`.
2. `ML.DECODE_IMAGE` takes **any** `BYTES` value, not only an object table's `data` pseudocolumn. That is what makes the rest of this notebook reproducible without a bucket.
3. **Decoding always returns 3 channels**, whatever the source had — an RGBA image's alpha is silently dropped (not composited), and a single-channel grayscale image is replicated into three identical channels. `ML.CONVERT_COLOR_SPACE(..., 'GRAYSCALE')` then takes it back down to **1**, so the channel count is set by the last function in the chain, not by the image.
4. The `[0, 1)` and `[0, 255)` ranges printed on the reference pages are wrong at the top end — a pure-white pixel is exactly `1.0`, and `ML.CONVERT_IMAGE_TYPE` returns exactly `255`.
5. `ML.CONVERT_IMAGE_TYPE` is **one-way**: there is no integer→float signature.
6. `GRAYSCALE` and `YIQ`'s Y channel are **two different lumas**, differing in the fourth decimal place.
7. `ML.RESIZE_IMAGE` is **type-preserving and float32**, while decode and color-space conversion are float64-exact.
8. A `preserve_aspect_ratio = TRUE` fit that rounds a dimension to zero raises an **internal error the client library retries for minutes** unless you turn job retry off.
9. All four are **TensorFlow image ops**. Diffed against TensorFlow directly: `HSV`, bilinear resize and the integer conversion are **bit-exact**, `YIQ`/`YUV` match to a last-place unit of a double, and the one row that misses at single precision misses because **`tf.image` computes it in float32 while BigQuery uses double**.

**When to use these:** you have image bytes in Cloud Storage and a vision model — `models/imported` (imported) or `models/remote` (remote) — that expects a fixed-size numeric tensor. These four get you from one to the other in SQL, with no data leaving BigQuery. For *generative* work on images (captioning, classification by prompt, embeddings) the path is entirely different — see **Related content** below.

**Data:** six images this notebook constructs from NumPy arrays — small enough that every pixel value is printable and checkable by hand, which is the only way the precision findings above are provable. They are uploaded to Cloud Storage so Step 8 can exercise the real object-table path.

**Related content:** `models/imported` (`models/imported/`) — how the model these features feed gets into BigQuery. `models/matrix_factorization` (`models/matrix_factorization/`) — the same reservation pattern, for the same reason. For multimodal generative AI over images (`ML.GENERATE_TEXT`, `AI.GENERATE_TABLE`, `ML.GENERATE_EMBEDDING` over an ObjectRef), see the sibling project `bq-ai-functions` (`bq-ai-functions`) — that is a foundation-model path, not this preprocessing one.

**References:** `reference/model-free-functions.md` (Full reference) | [ML.DECODE_IMAGE](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-decode-image) | [ML.RESIZE_IMAGE](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-resize-image) | [ML.CONVERT_COLOR_SPACE](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-convert-color-space) | [ML.CONVERT_IMAGE_TYPE](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-convert-image-type) | [Object tables](https://cloud.google.com/bigquery/docs/object-tables) | `setup` (Setup guide)


---
## Setup

Set your project, location, and bucket, authenticate, create the shared dataset — then deal with the reservation requirement, which is the part no other `functions/` notebook has.

```python
PROJECT_ID = 'statmike-mlops-349915'  # <-- Replace with your project ID
LOCATION = 'US'  # BigQuery dataset location
DATASET_ID = 'bq_ml'  # Shared dataset across all bq-ml notebooks
BUCKET = 'statmike-mlops-349915'  # <-- Replace with your GCS bucket (same location as DATASET_ID)
CONNECTION_ID = 'bq_ml_image_demo'  # Cloud Resource Connection for the object table in Step 8
RESERVATION_ID = 'bqml-image-temp'  # Temporary reservation name (Setup creates it, Cleanup removes it)
```


### Environment

> **Already set up the project environment?** The cell below is a no-op — packages are already in your kernel. See the `setup` (Setup Reference) for details.
>
> **Running standalone** (Colab, Colab Enterprise, Vertex AI Workbench)? The cell below installs required packages into your current kernel.

```python
from google.cloud import bigquery, storage
import pandas as pd

client = bigquery.Client(project=PROJECT_ID)
gcs_client = storage.Client(project=PROJECT_ID)
gcs_bucket = gcs_client.bucket(BUCKET)
pd.set_option('display.max_colwidth', None)

# Every image query in this notebook runs cache-off. The reservation demo two cells
# below depends on it: a cached result is served without slots and would hide the
# very failure the cell exists to show.
no_cache = bigquery.QueryJobConfig(use_query_cache=False)

# Create the shared dataset (idempotent)
dataset_ref = bigquery.DatasetReference(PROJECT_ID, DATASET_ID)
dataset = bigquery.Dataset(dataset_ref)
dataset.location = LOCATION
client.create_dataset(dataset, exists_ok=True)
print(f'Dataset {PROJECT_ID}.{DATASET_ID} ready')

# Register %%bigquery cell magic (auto-loaded in Colab, needed elsewhere)
%load_ext bigquery_magics
```


### Build the test images

Six images, defined as NumPy arrays so the ground truth is in the notebook rather than in a file. Two pixels carry most of the weight: **(200, 100, 50)**, a warm color with all three channels distinct, and **(0, 128, 255)**, which pins the low end, the middle, and the high end at once.

Each is encoded to PNG (and one to JPEG) in memory. The bytes are kept two ways: base64, so they can be inlined into SQL as a `BYTES` literal, and raw, so Step 8 can upload them to Cloud Storage.

```python
import io, base64
import numpy as np
from PIL import Image

# Ground truth, as arrays. Shape is (height, width, channels).
swatch_a   = np.array([[[200, 100, 50], [0, 128, 255]]], dtype=np.uint8)                        # 1x2 RGB
gradient_a = np.array([[[x * 32, y * 64, 128] for x in range(8)] for y in range(4)], np.uint8)  # 4x8 RGB
alpha_a    = np.array([[[200, 100, 50, 255], [0, 128, 255, 128]]], dtype=np.uint8)              # 1x2 RGBA
white_a    = np.array([[[255, 255, 255]]], dtype=np.uint8)                                      # 1x1 RGB

def encode(array, fmt='PNG', mode=None):
    image = Image.fromarray(array)
    if mode:
        image = image.convert(mode)
    buffer = io.BytesIO()
    image.save(buffer, format=fmt)
    return buffer.getvalue()

raw = {
    'swatch.png':   encode(swatch_a),
    'gradient.png': encode(gradient_a),
    'alpha.png':    encode(alpha_a),
    'gray.png':     encode(swatch_a, mode='L'),   # single-channel PNG
    'white.png':    encode(white_a),
    'swatch.jpg':   encode(swatch_a, fmt='JPEG'),
}
b64 = {name: base64.b64encode(data).decode() for name, data in raw.items()}

def img(name):
    """SQL fragment: this image's bytes as a literal, decoded."""
    return f"ML.DECODE_IMAGE(FROM_BASE64('{b64[name]}'))"

for name, data in raw.items():
    print(f'{name:14s} {len(data):5d} bytes')
```


### The undocumented prerequisite: a slot reservation

The cell below runs the simplest possible `ML.DECODE_IMAGE` call under whatever pricing model this project currently has. On a project with no reservation, it fails.

```python
from google.api_core.exceptions import BadRequest

probe = f'SELECT {img("swatch.png")}.dimensions AS dims'
try:
    print('On-demand result:', list(client.query(probe, job_config=no_cache).result())[0]['dims'])
    print('\nThis project already has a reservation assigned — the next cell will reuse or create one anyway.')
except BadRequest as e:
    print('On-demand FAILED, as expected:\n')
    print(str(e).split(';')[0])
```

That message names the requirement precisely — `job type QUERY`, this project or its parent, this location — and it appears on none of the four function reference pages, nor on the [manual preprocessing](https://cloud.google.com/bigquery/docs/manual-preprocessing) or [object table inference](https://cloud.google.com/bigquery/docs/object-table-inference) pages that tell you to use these functions.

The fix is a BigQuery Editions reservation. This notebook creates a small **autoscaling `ENTERPRISE`** one — 0 baseline slots, scaling to 100 only while a query actually runs — and deletes it in Cleanup.

> **This is not a capacity commitment.** No upfront purchase, no minimum term. It bills per-second for slot-time actually consumed and idles at zero cost. Do not substitute a commitment for it.

**Idempotent:** re-running detects and reuses an existing reservation/assignment instead of erroring or duplicating.

> **Assignment propagation is not atomic, so this cell waits on evidence rather than on a clock.** A probe query can succeed and the very next query — seconds later, same session, same project — fail again with the identical "no reservation was assigned" error. That rules out both a fixed sleep and a single successful probe as evidence, so the loop below requires several consecutive successes before continuing. How long it takes is not fixed either: watch the elapsed times it prints.

```python
import time
from google.cloud import bigquery_reservation_v1
from google.api_core.exceptions import AlreadyExists

reservation_client = bigquery_reservation_v1.ReservationServiceClient()
reservation_parent = f'projects/{PROJECT_ID}/locations/{LOCATION}'
reservation_name = f'{reservation_parent}/reservations/{RESERVATION_ID}'

try:
    reservation = reservation_client.create_reservation(
        parent=reservation_parent,
        reservation_id=RESERVATION_ID,
        reservation=bigquery_reservation_v1.Reservation(
            slot_capacity=0,
            edition=bigquery_reservation_v1.Edition.ENTERPRISE,
            autoscale=bigquery_reservation_v1.Reservation.Autoscale(max_slots=100),
            ignore_idle_slots=True,
        ),
    )
    print(f'Created {reservation.name}')
except AlreadyExists:
    reservation = reservation_client.get_reservation(name=reservation_name)
    print(f'Reservation already exists — reusing {reservation.name}')

existing_assignments = list(reservation_client.list_assignments(parent=reservation.name))
if existing_assignments:
    assignment = existing_assignments[0]
    print(f'Assignment already exists — reusing {assignment.name}')
else:
    assignment = reservation_client.create_assignment(
        parent=reservation.name,
        assignment=bigquery_reservation_v1.Assignment(
            job_type=bigquery_reservation_v1.Assignment.JobType.QUERY,
            assignee=f'projects/{PROJECT_ID}',
        ),
    )
    print(f'Created {assignment.name}')

# Wait for the reservation to answer CONSISTENTLY, not just once. A fixed sleep
# is not enough: one probe succeeded here and the next one failed.
required_streak, streak, waited = 3, 0, 0
while streak < required_streak:
    try:
        dims = list(client.query(probe, job_config=no_cache).result())[0]['dims']
        streak += 1
        print(f'  probe {streak}/{required_streak} succeeded ({waited}s elapsed): {list(dims)}')
    except BadRequest as e:
        if 'requires reservation' not in str(e):
            raise
        streak = 0
        print(f'  not propagated yet ({waited}s elapsed)')
    if streak < required_streak:
        if waited >= 600:
            raise RuntimeError('Reservation did not become usable within 10 minutes')
        time.sleep(15)
        waited += 15

print('Reservation is live.')
```


---
## Step 1 — What `ML.DECODE_IMAGE` actually returns

`[1, 2, 3]` from the cell above is already the first correction. The reference pages describe the output as `STRUCT<ARRAY<INT64> shape, ARRAY<FLOAT64> values>`. Select `.shape` and the query fails; the field is named **`dimensions`**.

Note also what the call above took as input: a `BYTES` literal built by `FROM_BASE64`. Every doc example passes an object table's `data` pseudocolumn, and the parameter is described as coming from one, but the signature is just `BYTES` — so the function is testable without a bucket, a connection, or an object table. Step 8 uses the object-table path for real; everything between here and there uses literals, which is why every value below is reproducible without any Cloud Storage setup.

```python
query = f"""
SELECT {img('swatch.png')}.dimensions AS dimensions,
       {img('swatch.png')}.values     AS values
"""
row = list(client.query(query, job_config=no_cache).result())[0]
h, w, c = row['dimensions']
print(f'dimensions = {list(row["dimensions"])}  ->  height={h}, width={w}, channels={c}')
print(f'values     = {list(row["values"])}')
print(f'len(values) = {len(row["values"])} = {h} x {w} x {c}')

# Ground truth: the array this notebook built, flattened row-major, divided by 255.
expected = swatch_a.astype(np.float64).ravel() / 255.0
print(f'\nexpected   = {list(expected)}')
print(f'max |BigQuery - expected| = {np.abs(np.array(row["values"]) - expected).max()}')
```

Three parts of the contract, all confirmed:

- **`dimensions` is `[height, width, channels]`** — the 1×2 image gives `[1, 2, 3]`, so height leads.
- **`values` is flattened row-major in HWC order** — pixel 1's three channels, then pixel 2's. Not planar (all R, then all G, then all B), which is the other convention a vision model might want and which you would have to build yourself.
- **The scaling is exactly `pixel / 255`, with no rounding error at all.** The difference from the float64 ground truth is `0.0`, not a small epsilon. `200/255` came back as the correctly-rounded double.

That last point matters more than it looks: it means these values are exact enough to reason about, and it sets up the precision comparison in Step 6, where one of the four functions behaves differently.


---
## Step 2 — Decode always returns exactly 3 channels

The reference pages say the input may be JPEG, PNG, or BMP. They do not say what happens to the channel count when the source image is not 3-channel RGB. Two cases matter in practice — a PNG with an alpha channel, and a single-channel grayscale PNG — and they resolve in opposite directions.

```python
query = f"""
SELECT {img('alpha.png')}.dimensions AS rgba_dimensions,
       {img('alpha.png')}.values     AS rgba_values,
       {img('gray.png')}.dimensions  AS gray_dimensions,
       {img('gray.png')}.values      AS gray_values
"""
row = list(client.query(query, job_config=no_cache).result())[0]

print(f'Source alpha.png is RGBA, shape {alpha_a.shape}, pixels {alpha_a.reshape(-1, 4).tolist()}')
print(f'  decoded dimensions: {list(row["rgba_dimensions"])}')
print(f'  decoded x255:       {[round(v * 255, 6) for v in row["rgba_values"]]}')

gray_source = np.array(Image.fromarray(swatch_a).convert('L'))
print(f'\nSource gray.png is single-channel L, shape {gray_source.shape}, pixels {gray_source.ravel().tolist()}')
print(f'  decoded dimensions: {list(row["gray_dimensions"])}')
print(f'  decoded x255:       {[round(v * 255, 6) for v in row["gray_values"]]}')
```

**Channels is always 3.** Both images decode to `channels = 3` regardless of what they contained.

- **The alpha channel is dropped, not applied.** The second pixel of `alpha.png` has alpha 128 — half transparent — and its RGB values come back as `0, 128, 255`, identical to the fully-opaque source values. Nothing was blended against a background and nothing was premultiplied. If your corpus mixes transparent PNGs with opaque ones, BigQuery will hand your model the raw RGB underneath the transparency, silently, and the two will not be comparable to whatever your training-time preprocessing did if that preprocessing composited. There is no flag to change this and no warning.
- **A grayscale image is replicated into three identical channels.** `gray.png` holds one value per pixel and decodes to that value three times. The size of a decoded feature vector therefore depends only on height and width, never on the source encoding — convenient for a fixed-shape model, and it means a mixed corpus of RGB, RGBA, and grayscale files needs no per-file branching. (This is a rule about *decoding*. Step 5 shows `ML.CONVERT_COLOR_SPACE(..., 'GRAYSCALE')` going the other way, back down to 1 channel.)

The format list is enforced at decode time, and the error names the accepted set:

```python
try:
    client.query("SELECT ML.DECODE_IMAGE(b'not an image at all').dimensions", job_config=no_cache).result()
except BadRequest as e:
    print(str(e).split(';')[0])
```

PNG, JPEG, BMP — no GIF, no WEBP, no TIFF, no AVIF. An object table happily lists files of any type; the failure surfaces only when a row reaches `ML.DECODE_IMAGE`, which means one stray file in a bucket fails the whole query rather than that one row.

**JPEG decodes to different numbers than PNG for the same source image**, which is worth stating explicitly because it is easy to build a corpus in mixed formats and treat the results as comparable:

```python
query = f"""
SELECT ML.CONVERT_IMAGE_TYPE({img('swatch.png')}).values AS png_ints,
       ML.CONVERT_IMAGE_TYPE({img('swatch.jpg')}).values AS jpg_ints
"""
row = list(client.query(query, job_config=no_cache).result())[0]
print(f'source pixels : {swatch_a.reshape(-1, 3).tolist()}')
print(f'via PNG       : {np.array(row["png_ints"]).reshape(-1, 3).tolist()}')
print(f'via JPEG      : {np.array(row["jpg_ints"]).reshape(-1, 3).tolist()}')
```

PNG is lossless and round-trips the source exactly. JPEG does not, and on a 2-pixel image it is not close — JPEG's 8×8 DCT blocks and chroma subsampling have nothing to work with at this size, so the reconstruction is dominated by block averaging. A photograph would survive far better. The point stands either way: **the decoded feature vector is a property of the file, not of the picture**, so re-encoding a corpus changes your features.


---
## Step 3 — The documented value ranges are wrong at the top

Every reference page states the decoded range as `[0, 1)` and the `ML.CONVERT_IMAGE_TYPE` range as `[0, 255)`. Both are written half-open, excluding the upper bound. A pure-white pixel settles it.

```python
query = f"""
SELECT {img('white.png')}.values                             AS float_values,
       ML.CONVERT_IMAGE_TYPE({img('white.png')}).values      AS int_values,
       {img('white.png')}.values[OFFSET(0)] = 1.0            AS float_is_exactly_one,
       ML.CONVERT_IMAGE_TYPE({img('white.png')}).values[OFFSET(0)] = 255 AS int_is_exactly_255
"""
row = list(client.query(query, job_config=no_cache).result())[0]
for k, v in row.items():
    print(f'{k:22s} {list(v) if isinstance(v, list) else v}')
```

Both endpoints are attainable. The decoded range is **`[0, 1]`** and the integer range is **`[0, 255]`**, both closed. The comparison is done in SQL rather than by eyeballing a printed `1.0`, because a float that prints as `1.0` need not equal `1.0`; this one does.

This is not pedantry. `[0, 255)` is how you would describe a range that a model's input validation should reject 255 from, and code written to that spec — a clamp, an assertion, a bucket boundary — is wrong on every white pixel, which is a common pixel.


---
## Step 4 — `ML.CONVERT_IMAGE_TYPE` is exact, and one-way

Its job is the float→integer direction for models that want `uint8` input. Round-tripping the swatch shows it is lossless in that direction:

```python
query = f'SELECT ML.CONVERT_IMAGE_TYPE({img("swatch.png")}).values AS ints'
ints = list(list(client.query(query, job_config=no_cache).result())[0]['ints'])
print(f'source : {swatch_a.ravel().tolist()}')
print(f'decoded -> converted back to int : {ints}')
print(f'identical: {ints == swatch_a.ravel().tolist()}')
```

`pixel / 255` then back is exact for all 256 byte values, so decode → convert is a safe round trip.

The reverse does not exist. Feeding integer image data back in is a signature error, not a runtime one — and the error text is the authoritative statement of the struct's real field names:

```python
query = f'SELECT ML.CONVERT_IMAGE_TYPE(ML.CONVERT_IMAGE_TYPE({img("swatch.png")})).values'
try:
    client.query(query, job_config=no_cache).result()
except BadRequest as e:
    print(str(e).split(';')[0])
```

`STRUCT<dimensions ARRAY<INT64>, values ARRAY<FLOAT64>>` in, `STRUCT<dimensions ARRAY<INT64>, values ARRAY<INT64>>` out. `dimensions`, from the engine itself.

The practical consequence: **`ML.CONVERT_IMAGE_TYPE` is terminal.** Once converted, the only remaining function you can apply is `ML.RESIZE_IMAGE` (Step 6 shows it accepts either value type) — `ML.CONVERT_COLOR_SPACE` also accepts integers, but nothing can put you back in the float domain. Order your pipeline accordingly: decode → resize → color space → convert type, last.


---
## Step 5 — `ML.CONVERT_COLOR_SPACE`, and the two different lumas

Four targets: `GRAYSCALE`, `HSV`, `YIQ`, `YUV`. The interesting one is that two of them compute a luminance channel, and they do not agree.

```python
spaces = ['GRAYSCALE', 'HSV', 'YIQ', 'YUV']
select = ',\n  '.join(
    f"ML.CONVERT_COLOR_SPACE({img('swatch.png')}, '{s}').dimensions AS {s.lower()}_dims,\n  "
    f"ML.CONVERT_COLOR_SPACE({img('swatch.png')}, '{s}').values     AS {s.lower()}"
    for s in spaces)
query = f'SELECT\n  {select}'
row = list(client.query(query, job_config=no_cache).result())[0]

dims = {s: list(row[f'{s.lower()}_dims']) for s in spaces}
converted = {s: np.array(row[s.lower()]).reshape(dims[s]) for s in spaces}
for s in spaces:
    print(f'{s:10s} dimensions={dims[s]}')
    for i, pixel in enumerate(converted[s].reshape(-1, dims[s][-1])):
        print(f'{"":12s}pixel {i} (RGB {swatch_a.reshape(-1, 3)[i].tolist()}): {pixel.tolist()}')
```

**`GRAYSCALE` changes the channel count — it returns 1, not 3.** That is the opposite of `ML.DECODE_IMAGE`, which in Step 2 replicated a single-channel grayscale PNG *up* to 3. So a decode-then-grayscale pipeline goes 1 → 3 → 1, and the "always 3 channels" rule from Step 2 is a rule about *decoding*, not about the family. `HSV`, `YIQ`, and `YUV` keep 3 channels and fill all three with genuinely distinct values.

`HSV`'s hue is on **`[0, 1]`, not degrees**: pixel 1's hue of ~0.0556 is 20°/360°, and pixel 2's ~0.583 is 210°/360°. A model or a threshold expecting degrees is off by a factor of 360.

Now the part worth stopping on. `GRAYSCALE`'s value and `YIQ`'s first channel are both luma, both computed from the same RGB, and they are different numbers. Which weights does each use?

```python
bt601   = np.array([0.299, 0.587, 0.114])       # the true ITU-R BT.601 luma coefficients
rounded = np.array([0.2989, 0.5870, 0.1140])     # the 4-decimal variant TensorFlow's rgb_to_grayscale uses

rgb = swatch_a.astype(np.float64).reshape(-1, 3) / 255.0
bq_grayscale = converted['GRAYSCALE'][..., 0].ravel()
bq_yiq_y     = converted['YIQ'][..., 0].ravel()

rows = []
for label, actual in [('GRAYSCALE', bq_grayscale), ('YIQ channel Y', bq_yiq_y)]:
    rows.append({
        'BigQuery output': label,
        'max diff vs [0.299, 0.587, 0.114]':    np.abs(actual - rgb @ bt601).max(),
        'max diff vs [0.2989, 0.5870, 0.1140]': np.abs(actual - rgb @ rounded).max(),
    })
display(pd.DataFrame(rows))

gap = bq_grayscale - bq_yiq_y
print(f'GRAYSCALE - YIQ.Y per pixel: {gap.tolist()}')
print(f'as 8-bit levels (x255):      {(gap * 255).tolist()}')
```

Two different lumas, each matching one weight vector to machine epsilon and neither matching the other:

- **`GRAYSCALE` uses `[0.2989, 0.5870, 0.1140]`** — the 4-decimal rounding that TensorFlow's `tf.image.rgb_to_grayscale` hardcodes.
- **`YIQ`'s Y uses `[0.299, 0.587, 0.114]`** — the actual BT.601 coefficients, exactly.

The gap is real but tiny — a fraction of one 8-bit level. It will never be visible and it will never change a classification. It matters for exactly one thing, which is worth knowing before it costs you an afternoon: **`GRAYSCALE` and `ML.CONVERT_COLOR_SPACE(..., 'YIQ')`'s Y are not interchangeable in a bit-for-bit reproducibility check.** If you are diffing a BigQuery preprocessing pipeline against a reimplementation elsewhere, you have to match the right one.

Integer-valued image data is accepted too, and is normalized on the way in rather than treated as already-scaled:

```python
query = f"""
SELECT ML.CONVERT_COLOR_SPACE({img('swatch.png')}, 'HSV').values                        AS from_float,
       ML.CONVERT_COLOR_SPACE(ML.CONVERT_IMAGE_TYPE({img('swatch.png')}), 'HSV').values AS from_int
"""
row = list(client.query(query, job_config=no_cache).result())[0]
print(f'from FLOAT64 input : {list(row["from_float"])}')
print(f'from INT64 input   : {list(row["from_int"])}')
print(f'identical: {list(row["from_float"]) == list(row["from_int"])}')
```

Identical, and the output is `FLOAT64` either way. So `ML.CONVERT_COLOR_SPACE` divides integer input by 255 before converting — it never mistakes a `200` for a value already on `[0, 1]`. That is the safe behavior, and it means the pipeline order from Step 4 is a recommendation rather than a correctness requirement for this function.

An unrecognized target is rejected by name:

```python
try:
    client.query(f"SELECT ML.CONVERT_COLOR_SPACE({img('swatch.png')}, 'LAB').values",
                 job_config=no_cache).result()
except BadRequest as e:
    print(str(e).split(';')[0])
```


---
## Step 6 — `ML.RESIZE_IMAGE`: bilinear, float32, and type-preserving

The 4×8 gradient is the test image here — big enough to have interior pixels, small enough to print. Start with what `preserve_aspect_ratio` actually does to the output dimensions.

```python
targets = [(4, 4, True), (3, 3, True), (2, 2, True), (9, 9, True), (4, 4, False)]
select = ',\n  '.join(
    f'ML.RESIZE_IMAGE({img("gradient.png")}, {h}, {w}, {str(p).upper()}).dimensions AS t{i}'
    for i, (h, w, p) in enumerate(targets))
row = list(client.query(f'SELECT\n  {select}', job_config=no_cache).result())[0]

print(f'source dimensions: {list(gradient_a.shape)}\n')
out = []
for i, (h, w, p) in enumerate(targets):
    dims = list(row[f't{i}'])
    scale = min(h / gradient_a.shape[0], w / gradient_a.shape[1]) if p else None
    out.append({'target (h, w)': f'{h} x {w}', 'preserve_aspect_ratio': p,
                'implied scale': round(scale, 4) if scale else '—',
                'unrounded h x w': f'{gradient_a.shape[0] * scale:g} x {gradient_a.shape[1] * scale:g}' if scale else '—',
                'result dimensions': dims})
display(pd.DataFrame(out))
```

With `preserve_aspect_ratio = TRUE` the two target values are a **bounding box, not a size**: the scale is `min(target_h / h, target_w / w)` and the result is the largest image inside the box at the original aspect ratio. With `FALSE` you get exactly what you asked for, distortion included.

Look at the two rows where the scaled dimension lands on a half. `4 × 8` into a `3 × 3` box scales by 0.375, giving an unrounded height of 1.5, and the result is **2**. Into a `9 × 9` box it scales by 1.125, giving an unrounded height of 4.5, and the result is **4**. Half rounds up in one case and down in the other — that is round-half-to-even, the rounding NumPy and TensorFlow use and not the one SQL's `ROUND()` uses. Step 7 shows why that is exactly what you would expect.

Now the pixel values. A 4×8 down to 2×4 is a clean 2:1 in both directions:

```python
query = f'SELECT ML.RESIZE_IMAGE({img("gradient.png")}, 2, 4, FALSE).values AS v'
resized = np.array(list(client.query(query, job_config=no_cache).result())[0]['v']).reshape(2, 4, 3)
print('red channel of the resized 2x4 (x255):')
print(np.round(resized[..., 0] * 255, 6))
print('\nred channel of the 4x8 source (x255):')
print(gradient_a[..., 0])
print(f'\nsingle value, full precision: {resized[0, 0, 0]!r}')
print(f'nearest float32:              {np.float32(resized[0, 0, 0]).item()!r}')
print(f'exactly representable in float32: {np.float64(np.float32(resized[0, 0, 0])) == resized[0, 0, 0]}')
```

Two things.

**The interpolation is bilinear with half-pixel centers.** Output pixel `[0,0]` sits between source columns 0 and 1 (red values 0 and 32) and between source rows 0 and 1, and comes back at 16/255 — the average of the four neighbors, not a copy of the top-left pixel. That is `align_corners = False` sampling, the modern default.

**The values are float32, unlike everything else in this family.** Every number `ML.DECODE_IMAGE` and `ML.CONVERT_COLOR_SPACE` returned above was float64-exact; this one is a float64 that exactly equals its float32 neighbor, which is the signature of a value computed in single precision and widened on the way out. It costs about seven significant digits. Irrelevant for feeding a model — models are float32 anyway — and decisive if you are diffing against a float64 reimplementation, which is the trap Step 5's luma finding also sets.

Resize is the one function in the family that **preserves the value type** rather than forcing float:

```python
query = f"""
SELECT ML.RESIZE_IMAGE(ML.CONVERT_IMAGE_TYPE({img('swatch.png')}), 1, 1, FALSE).values AS int_in_int_out,
       ML.RESIZE_IMAGE({img('swatch.png')}, 1, 1, FALSE).values                        AS float_in_float_out
"""
row = list(client.query(query, job_config=no_cache).result())[0]
print(f'source pixels        : {swatch_a.reshape(-1, 3).tolist()}')
print(f'exact channel means  : {swatch_a.astype(np.float64).reshape(-1, 3).mean(axis=0).tolist()}')
print(f'INT64 in -> out      : {list(row["int_in_int_out"])}')
print(f'FLOAT64 in -> out x255: {[v * 255 for v in row["float_in_float_out"]]}')
```

Integers in, integers out. The blue channel's true mean is 152.5 and it comes back as 152 — half-to-even again, consistent with the dimension rounding above. Feeding integers to resize therefore quantizes at every resize step; keep the pipeline in floats and convert last, as Step 4 concluded for a different reason.

### The failure mode worth knowing about

Ask for an aspect-preserving fit whose scale rounds a dimension down to zero — the 4×8 gradient into a 1×1 box scales by 0.125, giving a height of 0.5 — and the query fails.

> **The client library will retry this for minutes if you let it.** BigQuery reports it as a generic internal error with the standard "this is usually caused by a transient issue" advice, and `google-cloud-bigquery`'s default job-retry policy believes it: it resubmits the job, which fails identically, repeatedly. It is fully deterministic and no amount of retrying will change it. **`job_retry=None` is what makes this cell return in seconds instead of hanging.**

> **Catch the base class, and read the failure off the job.** The same deterministic failure has surfaced here as both `InternalServerError` (HTTP 500) and `BadRequest` (HTTP 400) on different runs, depending on which API call observes the dead job, and the 400 form arrives with a generic message that omits the diagnostic code. `job.error_result['message']` carries the full text either way, so catch `GoogleAPICallError` — the parent of both — and print the job's own error rather than the exception's.

```python
from google.api_core.exceptions import GoogleAPICallError

query = f'SELECT ML.RESIZE_IMAGE({img("gradient.png")}, 1, 1, TRUE).dimensions'
started = time.time()
job = client.query(query, job_config=no_cache, job_retry=None)
try:
    job.result()
    print('Unexpectedly succeeded')
except GoogleAPICallError as e:
    print(f'Failed in {time.time() - started:.1f}s as {type(e).__name__} (HTTP {e.code}).\n')
    detail = job.error_result
    if not detail:
        job.reload()
        detail = job.error_result
    print((detail or {}).get('message', str(e)))
```

The reproducible input rule is: **`preserve_aspect_ratio = TRUE` fails whenever `min(target_h / h, target_w / w)` scales either source dimension to less than 0.5**, i.e. whenever it rounds to zero. Verified on two differently-shaped sources; the `2 × 2` fit two cells up is the same target size on the same image with a non-degenerate result, so it is the rounding-to-zero and not the small target that does it.

What produces the internal error rather than a clean argument error is not observable from outside. A zero-sized dimension reaching an op that cannot accept one would explain it, and so would several other things; the message says nothing either way. What is worth carrying forward is operational, not diagnostic: **a "transient" internal error from these functions may be perfectly deterministic**, and the guard is to bound the target box so no dimension can round to zero — check `min(th/h, tw/w) * min(h, w) >= 0.5` before the query, or simply pass `FALSE` and accept the distortion.


---
## Step 7 — All four are TensorFlow image ops

Every finding above has the same shape: the behavior is not what BigQuery's documentation says, and it is exactly what TensorFlow does. Rather than infer that from a family resemblance, diff it directly — run the conversions in BigQuery, run the corresponding `tf.image` op locally, and subtract.

```python
import tensorflow as tf

query = f"""
SELECT
  ML.CONVERT_COLOR_SPACE({img('swatch.png')}, 'GRAYSCALE').values AS grayscale,
  ML.CONVERT_COLOR_SPACE({img('swatch.png')}, 'HSV').values       AS hsv,
  ML.CONVERT_COLOR_SPACE({img('swatch.png')}, 'YIQ').values       AS yiq,
  ML.CONVERT_COLOR_SPACE({img('swatch.png')}, 'YUV').values       AS yuv,
  ML.RESIZE_IMAGE({img('gradient.png')}, 2, 4, FALSE).values      AS resize_even,
  ML.RESIZE_IMAGE({img('gradient.png')}, 3, 5, FALSE).values      AS resize_odd,
  ML.CONVERT_IMAGE_TYPE({img('swatch.png')}).values               AS to_uint8
"""
row = list(client.query(query, job_config=no_cache).result())[0]

swatch_f64 = swatch_a.astype(np.float64) / 255.0
grad_f64 = gradient_a.astype(np.float64) / 255.0

# Pin the tensor dtype explicitly. BigQuery computes the color-space conversions in
# double, so the reference has to as well -- and handing tf.image a bare NumPy float64
# array does not reliably get you there (the `reference dtype` column below is the check).
swatch_t64 = tf.constant(swatch_f64, tf.float64)

cases = [
    ('ML.CONVERT_COLOR_SPACE GRAYSCALE', row['grayscale'],
        tf.image.rgb_to_grayscale(swatch_t64).numpy(),
        'tf.image.rgb_to_grayscale, called as-is'),
    ('ML.CONVERT_COLOR_SPACE GRAYSCALE', row['grayscale'],
        (swatch_f64 @ rounded)[..., None],
        'the same weights, evaluated in float64'),
    ('ML.CONVERT_COLOR_SPACE HSV', row['hsv'],
        tf.image.rgb_to_hsv(swatch_t64).numpy(), 'tf.image.rgb_to_hsv (float64)'),
    ('ML.CONVERT_COLOR_SPACE YIQ', row['yiq'],
        tf.image.rgb_to_yiq(swatch_t64).numpy(), 'tf.image.rgb_to_yiq (float64)'),
    ('ML.CONVERT_COLOR_SPACE YUV', row['yuv'],
        tf.image.rgb_to_yuv(swatch_t64).numpy(), 'tf.image.rgb_to_yuv (float64)'),
    # Resize runs in float32 (Step 6), so cast the input to match.
    ('ML.RESIZE_IMAGE 4x8 -> 2x4', row['resize_even'],
        tf.image.resize(tf.constant(grad_f64, tf.float32), [2, 4], method='bilinear').numpy(),
        'tf.image.resize bilinear (float32)'),
    ('ML.RESIZE_IMAGE 4x8 -> 3x5', row['resize_odd'],
        tf.image.resize(tf.constant(grad_f64, tf.float32), [3, 5], method='bilinear').numpy(),
        'tf.image.resize bilinear (float32)'),
    ('ML.CONVERT_IMAGE_TYPE', row['to_uint8'],
        tf.image.convert_image_dtype(swatch_t64, tf.uint8).numpy(),
        'tf.image.convert_image_dtype -> uint8'),
]

EPS64, EPS32 = np.finfo(np.float64).eps, np.finfo(np.float32).eps

def compare(bq, ref):
    """Diff, plus the precision the gap is consistent with."""
    bq, ref = np.array(bq, dtype=np.float64), ref.astype(np.float64).ravel()
    diff, scale = float(np.abs(bq - ref).max()), float(np.abs(bq).max())
    if diff == 0.0:
        return diff, 'exact'
    if diff <= 4 * EPS64 * scale:
        return diff, 'double precision (<= a few ULP)'
    if diff <= 4 * EPS32 * scale:
        return diff, 'single precision (float32 somewhere in the op)'
    return diff, 'a different answer'

table = []
for name, bq, ref, op in cases:
    diff, verdict = compare(bq, ref)
    table.append({'BigQuery function': name, 'TensorFlow op': op,
                  'reference dtype': str(ref.dtype), 'max |difference|': diff,
                  'consistent with': verdict})
display(pd.DataFrame(table))

single = [t['BigQuery function'] for t in table if t['consistent with'].startswith('single')]
print(f'TensorFlow {tf.__version__}')
print(f'single-precision rows: {", ".join(single) if single else "none"}')

# Which side is the single precision on? Compare BigQuery to BigQuery: the HSV values
# from this multi-function query against the ones Step 5 got with HSV alone.
delta = float(np.abs(np.array(row['hsv']) - np.array(converted['HSV']).ravel()).max())
print(f'BigQuery HSV here vs Step 5 (HSV alone in its query): max |difference| {delta:.6e}')
```

**`ML.CONVERT_COLOR_SPACE(..., 'HSV')` and both `ML.RESIZE_IMAGE` cases are bit-exact** — a difference of literally zero, including the 4×8 → 3×5 resize where the scale factor is not an integer ratio in either direction. `ML.CONVERT_IMAGE_TYPE` is exact too, since it produces integers.

`YIQ` and `YUV` land a last-place unit of a double away from `tf.image`'s answer — the residue of doing the same arithmetic in a different order, not a different formula.

`GRAYSCALE` is the row with a documented story. Called the ordinary way, `tf.image.rgb_to_grayscale` is eight orders of magnitude further off than `YIQ` is, and the reason is in TensorFlow's own source: it does `flt_image = convert_image_dtype(images, dtypes.float32)` before applying the weights, then converts back — so the returned tensor is still a double, but the arithmetic ran in **float32**. Apply the identical weights in float64 and the gap collapses to the same last-place residue as everything else. **BigQuery runs this in double where TensorFlow does not** — the algorithm is TensorFlow's (Step 5 pinned the weights to its 4-decimal constants), the precision is better than TensorFlow's.

That is also why the `consistent with` column is worth more than the raw magnitude: a ~1e-8 gap is not "a different formula," it is the resolution of a single-precision float, and it says only that *someone* on one side of the comparison spent a float32.

**The `reference dtype` column is there because this comparison is easy to get wrong, and the wrong version looks like a finding.** Hand `tf.image` a bare NumPy `float64` array rather than an explicitly typed tensor and the op can return **float32** — which turns the bit-exact `HSV` row into one the table classifies as single precision, at the same magnitude as the real `GRAYSCALE` result above it — an artifact of the measurement setup, indistinguishable from a property of the engine. That is why the cell pins its reference tensor with `tf.constant(..., tf.float64)` and prints the dtype it actually got. The last line of the cell is the control on the other side: BigQuery returns the **identical** `HSV` values whether the conversion sits alone in a query or beside six other image functions, so the precision of these functions is a property of the function, not of the query it lands in.

This is the practical takeaway of the whole notebook. When the reference page is silent or wrong — the channel count, the closed ranges, the rounding rule, the luma weights, the interpolation convention — **the answer is what `tf.image` does**, and `tf.image`'s documentation is specific where BigQuery's is not.


---
## Step 8 — The real path: an object table over Cloud Storage

Everything above used `BYTES` literals to keep the values reproducible. Production input is an [object table](https://cloud.google.com/bigquery/docs/object-tables): a read-only table over files in Cloud Storage whose `data` pseudocolumn is the file's bytes.

Unlike the functions themselves, an object table **does** need a Cloud Resource Connection, and the connection's service account needs read access to the bucket.

> **This changes IAM on your project** — it grants `roles/storage.objectViewer` to one newly-created, narrowly-scoped service account. The grant is checked explicitly rather than assumed: a silently-swallowed failure here surfaces as a confusing permission error on the query two cells later.

> **The bucket is never created or deleted by this notebook** — set `BUCKET` above to one you already own in the same location as `DATASET_ID`. Cleanup removes only the objects this notebook wrote, under the `bq_ml/image/` prefix.

```python
import json as _json

prefix = 'bq_ml/image/'
for name, data in raw.items():
    blob = gcs_bucket.blob(prefix + name)
    blob.upload_from_string(data, content_type='image/jpeg' if name.endswith('.jpg') else 'image/png')
print(f'Uploaded {len(raw)} objects to gs://{BUCKET}/{prefix}')

r_conn = subprocess.run(
    ['bq', 'mk', '--connection', '--location', LOCATION, '--connection_type', 'CLOUD_RESOURCE',
     '--project_id', PROJECT_ID, CONNECTION_ID],
    capture_output=True, text=True,
)
if r_conn.returncode != 0 and 'already exists' not in r_conn.stderr.lower():
    raise RuntimeError(f'Failed to create connection {CONNECTION_ID}:\n{r_conn.stderr}')

r_show = subprocess.run(
    ['bq', 'show', '--connection', '--format=json', '--project_id', PROJECT_ID, '--location', LOCATION, CONNECTION_ID],
    capture_output=True, text=True, check=True,
)
connection_sa = _json.loads(r_show.stdout)['cloudResource']['serviceAccountId']
print('Connection service account:', connection_sa)

r_iam = subprocess.run(
    ['gcloud', 'projects', 'add-iam-policy-binding', PROJECT_ID,
     f'--member=serviceAccount:{connection_sa}', '--role=roles/storage.objectViewer', '--quiet'],
    capture_output=True, text=True,
)
if r_iam.returncode != 0:
    raise RuntimeError(f'Failed to grant roles/storage.objectViewer to {connection_sa}:\n{r_iam.stderr}')
print('Granted roles/storage.objectViewer')

time.sleep(60)  # initial wait -- the query below retries further, since propagation is variable
```

```python
query = f"""
CREATE OR REPLACE EXTERNAL TABLE `{PROJECT_ID}.{DATASET_ID}.image_object_table`
WITH CONNECTION `{PROJECT_ID}.{LOCATION}.{CONNECTION_ID}`
OPTIONS (
  object_metadata = 'SIMPLE',
  uris = ['gs://{BUCKET}/{prefix}*']
)
"""
client.query(query).result()

# IAM propagation is genuinely variable -- retry on a permission error rather
# than gambling on the fixed wait above.
from google.api_core.exceptions import Forbidden

listing = f"""
SELECT REGEXP_EXTRACT(uri, r'[^/]+$') AS file, content_type, size, updated
FROM `{PROJECT_ID}.{DATASET_ID}.image_object_table`
ORDER BY file
"""
for attempt in range(1, 9):
    try:
        display(client.query(listing, job_config=no_cache).to_dataframe())
        break
    except (BadRequest, Forbidden) as e:
        if 'permission' not in str(e).lower() or attempt == 8:
            raise
        print(f'Attempt {attempt}/8: permission not yet propagated, waiting 20s...')
        time.sleep(20)
```

An object table exposes metadata columns (`uri`, `content_type`, `size`, `updated`) plus the `data` pseudocolumn holding the bytes. `data` is what `ML.DECODE_IMAGE` consumes.

Note that `content_type` is what Cloud Storage was told at upload time, not what the file is. It is metadata, not validation — filter on it if you like, but Step 2's decode error is the only thing that actually checks.

Now the whole pipeline in one statement: bytes → decode → fixed-size resize → grayscale → integers, written to a table rather than returned to the editor.

```python
query = f"""
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.image_features` AS
SELECT
  REGEXP_EXTRACT(uri, r'[^/]+$') AS file,
  ML.CONVERT_IMAGE_TYPE(
    ML.CONVERT_COLOR_SPACE(
      ML.RESIZE_IMAGE(ML.DECODE_IMAGE(data), 4, 4, FALSE),
      'GRAYSCALE')) AS features
FROM `{PROJECT_ID}.{DATASET_ID}.image_object_table`
WHERE content_type IN ('image/png', 'image/jpeg')
"""
client.query(query).result()

summary = f"""
SELECT file,
       features.dimensions      AS dimensions,
       ARRAY_LENGTH(features.values) AS n_values,
       features.values[OFFSET(0)]    AS first_value
FROM `{PROJECT_ID}.{DATASET_ID}.image_features`
ORDER BY file
"""
display(client.query(summary, job_config=no_cache).to_dataframe())
```

Six source images of four different shapes and two formats, all reduced to the same dimensions and the same value count — a uniform feature vector a vision model can take as a batch. That uniformity is the entire point of the family, and it comes from two of the rules above: a `FALSE` aspect ratio pins height and width to exactly what was asked for, and the channel count is fixed by the last function in the chain (`GRAYSCALE` here, so 1 channel, per Step 5) rather than by the source images, which arrived with 1, 3, and 4 channels between them.

> **Write to a table, don't select the struct.** The reference pages warn that referencing these functions directly can fail to display in the BigQuery editor. That is a display limit, not a data limit — these images are tiny, but a 4000×3000 photo decodes to 36 million doubles, and the resize belongs *inside* the same statement that reads `data` so the large intermediate never materializes as a result.

The two remaining size limits are worth stating together, because one behaves differently than its wording suggests: **object-table image files must be under 20 MB and the `data` value passed to `ML.DECODE_IMAGE` must be at most 10 MB** — those are hard. The decoded `STRUCT`'s 60 MB ceiling is not: an image whose decoded struct would exceed it is **automatically downscaled, preserving aspect ratio**, rather than rejected. A silently resized input is a much subtler problem than a failed query, because the model still gets a valid tensor. If your pipeline handles large images, pin the size with an explicit `ML.RESIZE_IMAGE` instead of letting the ceiling do it for you.

### Where this goes next

These features feed a model that BigQuery did not train. `CREATE MODEL ... OPTIONS(model_type = 'TENSORFLOW', model_path = 'gs://...')` imports a vision SavedModel, and `ML.PREDICT` scores the table above — see `models/imported` (`models/imported/`) for the import mechanics end to end (its examples are tabular, but the `CREATE MODEL` shape is identical). Put the four functions in a `TRANSFORM` clause instead and the preprocessing is stored with the model and re-applied automatically at prediction time, which removes the possibility of training/serving skew in this stage of the pipeline entirely.


---
## Examples — `%%bigquery` Magics

The same pipeline using IPython magic commands — write SQL directly in cells without Python string wrapping.

```sql
%%bigquery --project {PROJECT_ID}

SELECT
  REGEXP_EXTRACT(uri, r'[^/]+$')                                          AS file,
  ML.DECODE_IMAGE(data).dimensions                                        AS source_dimensions,
  ML.RESIZE_IMAGE(ML.DECODE_IMAGE(data), 4, 4, FALSE).dimensions          AS resized_dimensions,
  ML.CONVERT_IMAGE_TYPE(ML.DECODE_IMAGE(data)).values[OFFSET(0)]          AS first_pixel_red
FROM `statmike-mlops-349915.bq_ml.image_object_table`
ORDER BY file
```


---
## Examples — BigFrames

There is **no** `bigframes.ml` wrapper for any of the four. BigFrames has a multimodal `blob` accessor (`Series.blob.image_resize()`, `.image_normalize()`) that reads and writes image *files* through Cloud Storage — a different mechanism producing files, not the numeric `STRUCT` these functions produce. To reach the BigQuery functions themselves, run the SQL through `read_gbq`.

The struct comes back as a Python `dict`, so `dimensions` and `values` are ordinary keys.

```python
import bigframes.pandas as bpd

bpd.close_session()  # Reset session to apply project/location settings
bpd.options.bigquery.project = PROJECT_ID
bpd.options.bigquery.location = LOCATION

bdf = bpd.read_gbq(f"""
SELECT REGEXP_EXTRACT(uri, r'[^/]+$') AS file,
       ML.RESIZE_IMAGE(ML.DECODE_IMAGE(data), 2, 2, FALSE) AS image
FROM `{PROJECT_ID}.{DATASET_ID}.image_object_table`
ORDER BY file
""")
pdf = bdf.to_pandas()
print(type(pdf['image'].iloc[0]))
print('dimensions:', pdf['image'].iloc[0]['dimensions'])
bdf
```
