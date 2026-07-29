# Image Deduplication — BigQuery AI Functions

Group near-duplicate images using embedding similarity to maintain train/test split integrity:

1. **Render & Transform** — Convert document PDFs to PNGs, create transformed variants (crop, rotate, brightness, noise, JPEG compression, color shift) to simulate same-source frames
2. **Visualize** — Display originals and variants side-by-side to see what "near-duplicate" looks like
3. **Embed** — Create multimodal embeddings with `AI.EMBED` using `gemini-embedding-2-preview`
4. **Find Similar Pairs** — Use `VECTOR_SEARCH` to identify near-duplicates by cosine distance
5. **Analyze Threshold** — Plot distance distributions and sensitivity to pick the right threshold
6. **Group Images** — Compare two approaches: direct grouping (single-pass) vs connected components (transitive)
7. **Validate** — Measure grouping accuracy with precision and recall against known ground truth
8. **Train/Test Split** — Demonstrate group-level splitting to prevent data leakage

**The Problem:** When training a classification model on images extracted from videos, frames from the same video are nearly identical. If some land in training and others in test, the model appears to generalize but is actually recognizing scenes it already saw. The solution: group similar images together, then assign entire groups to train or test — never both.

**What this demonstrates:**
- Multimodal embeddings with `gemini-embedding-2-preview` (images + PDFs, 3072 dims)
- Batch similarity detection with `VECTOR_SEARCH`
- Threshold selection via distance distribution analysis
- Two grouping algorithms: single-pass direct assignment vs iterative connected components
- BigQuery scripting (`WHILE` loop) for graph traversal
- Precision/recall evaluation of grouping quality
- Proper ML dataset splitting at the group level to prevent data leakage

**Functions used:** `functions/ai_embed` (`AI.EMBED`) | `functions/vector_search` (`VECTOR_SEARCH`)

**Prerequisites:** `setup` (Setup guide) | `RESOURCES.md` (Function reference)

---
## Setup

Set your project and location, authenticate, and create shared resources.

> This workflow uses `AI.EMBED` with `gemini-embedding-2-preview` (multimodal, Preview) and `VECTOR_SEARCH`. A connection is required for GCS access and the embedding endpoint. See the `setup` (Setup Reference) for details.

```python
PROJECT_ID = 'statmike-mlops-349915'  # <-- Replace with your project ID
LOCATION = 'US'  # BigQuery dataset location
DATASET_ID = 'bq_ai_functions'  # Shared dataset across all notebooks
CONNECTION_ID = 'bq_ai_functions'  # Shared connection
BUCKET = PROJECT_ID  # GCS bucket (same name as project)
```

### Environment

> **Already set up the project environment?** The cell below is a no-op — packages are already in your kernel. See the `setup` (Setup Reference) for details.
>
> **Running standalone** (Colab, Colab Enterprise, Vertex AI Workbench)? The cell below installs required packages into your current kernel.

```python
from google.cloud import bigquery
import pandas as pd
import matplotlib.pyplot as plt

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

```python
import subprocess as _sp, json as _json

# Create connection (idempotent)
_sp.run(['bq', 'mk', '--connection', '--location', LOCATION,
         '--connection_type', 'CLOUD_RESOURCE',
         '--project_id', PROJECT_ID, CONNECTION_ID],
        capture_output=True, text=True)

# Get service account and grant required roles
r = _sp.run(['bq', 'show', '--connection', '--format=json',
             '--project_id', PROJECT_ID, '--location', LOCATION, CONNECTION_ID],
            capture_output=True, text=True, check=True)
sa = _json.loads(r.stdout)['cloudResource']['serviceAccountId']

for role in ['roles/aiplatform.user', 'roles/storage.objectViewer']:
    _sp.run(['gcloud', 'projects', 'add-iam-policy-binding', PROJECT_ID,
             f'--member=serviceAccount:{sa}', f'--role={role}', '--quiet'],
            capture_output=True, text=True)
print(f'Connection {CONNECTION_ID} ready (SA: {sa})')
```

---
## Step 1 — Render PDFs to images

Render invoice and receipt PDFs to PNG images. Each PDF represents a distinct source document — analogous to different videos in the customer use case. We use 10 invoices and 10 receipts to create a realistic dataset.

```python
import shutil

if not shutil.which('pdftoppm'):
    import subprocess
    subprocess.check_call(['sudo', 'apt-get', 'install', '-y', '-qq', 'poppler-utils'])
    print('Installed poppler-utils (provides pdftoppm)')
else:
    print('pdftoppm already available')
```

```python
import subprocess as sp
from pathlib import Path
from google.cloud import storage

data_dir = Path('../../data/documents')
if not data_dir.exists():
    data_dir = Path('data/documents')

# 10 invoices + 10 receipts = 20 originals
docs_to_render = (
    [(f'invoice_{i:03d}.pdf', 'invoices') for i in range(1, 11)] +
    [(f'receipt_{i:03d}.pdf', 'receipts') for i in range(1, 11)]
)

PREFIX = 'bq_ai_functions/image_deduplication'
gcs = storage.Client(project=PROJECT_ID)
bucket = gcs.bucket(BUCKET)

rendered = []
original_bytes = {}  # Keep in memory for transforms + display
for pdf_name, subdir in docs_to_render:
    pdf_path = data_dir / subdir / pdf_name
    base_name = pdf_name.replace('.pdf', '')
    png_name = f'{base_name}_original.png'

    result = sp.run(
        ['pdftoppm', '-png', '-f', '1', '-l', '1', '-r', '150', str(pdf_path)],
        capture_output=True
    )
    blob = bucket.blob(f'{PREFIX}/{png_name}')
    blob.upload_from_string(result.stdout, content_type='image/png')
    rendered.append(png_name)
    original_bytes[png_name] = result.stdout

print(f'Rendered and uploaded {len(rendered)} original images to gs://{BUCKET}/{PREFIX}/')
```

---
## Step 2 — Create transformed image variants

For half the originals, create transformed variants that simulate frames extracted from the same video source. Six transform types cover common real-world variations:

| Transform | Simulates |
|-----------|-----------|
| **Crop** (5% edges) | Camera zoom or reframing |
| **Rotate** (2°) | Slight camera tilt |
| **Brightness** (+10%) | Lighting change |
| **Noise** (Gaussian) | Sensor noise or compression |
| **JPEG compression** (quality=50) | Re-encoding artifacts |
| **Color shift** (hue +10°) | White balance drift |

Each transformed image should be grouped with its source — they're near-duplicates from different "frames" of the same scene.

```python
from PIL import Image, ImageEnhance, ImageFilter
import io, numpy as np

# Create variants for 5 invoices and 5 receipts (10 source images, 6 variants each = 60 variants)
images_to_transform = [
    f'invoice_{i:03d}_original.png' for i in range(1, 6)
] + [
    f'receipt_{i:03d}_original.png' for i in range(1, 6)
]

variant_count = 0
for original_name in images_to_transform:
    img = Image.open(io.BytesIO(original_bytes[original_name]))
    base_name = original_name.replace('_original.png', '')
    width, height = img.size

    # Crop — remove 5% from edges
    cropped = img.crop((
        int(width * 0.05), int(height * 0.05),
        width - int(width * 0.05), height - int(height * 0.05)
    ))

    # Rotate — 2 degrees
    rotated = img.rotate(2, expand=True, fillcolor='white')

    # Brightness — 10% brighter
    brighter = ImageEnhance.Brightness(img).enhance(1.1)

    # Noise — Gaussian noise
    arr = np.array(img).astype(np.float32)
    noise = np.random.normal(0, 8, arr.shape)
    noisy = Image.fromarray(np.clip(arr + noise, 0, 255).astype(np.uint8))

    # JPEG compression — re-encoding artifacts
    jpeg_buf = io.BytesIO()
    img.save(jpeg_buf, format='JPEG', quality=50)
    jpeg_buf.seek(0)
    jpeg_compressed = Image.open(jpeg_buf).convert('RGB')

    # Color shift — shift hue by ~10 degrees
    hsv = img.convert('HSV')
    h, s, v = hsv.split()
    h_arr = np.array(h).astype(np.int16)
    h_shifted = Image.fromarray(((h_arr + 7) % 256).astype(np.uint8))
    color_shifted = Image.merge('HSV', (h_shifted, s, v)).convert('RGB')

    variants = {
        f'{base_name}_crop.png': cropped,
        f'{base_name}_rotate.png': rotated,
        f'{base_name}_bright.png': brighter,
        f'{base_name}_noise.png': noisy,
        f'{base_name}_jpeg.png': jpeg_compressed,
        f'{base_name}_color.png': color_shifted,
    }

    for name, variant_img in variants.items():
        buf = io.BytesIO()
        variant_img.save(buf, format='PNG')
        bucket.blob(f'{PREFIX}/{name}').upload_from_string(buf.getvalue(), content_type='image/png')
        variant_count += 1

total = len(rendered) + variant_count
print(f'Created {variant_count} transformed variants from {len(images_to_transform)} source images')
print(f'Total dataset: {total} images ({len(rendered)} originals + {variant_count} variants)')
print(f'Expected: {len(images_to_transform)} groups of 7 + {len(rendered) - len(images_to_transform)} singletons = {len(rendered)} groups')
```

### Visualize: originals are distinct documents

A sample of original images — each is a different invoice or receipt. These should **not** be grouped together.

```python
from IPython.display import display
from PIL import Image
import io

fig, axes = plt.subplots(2, 5, figsize=(18, 8))
fig.suptitle('Sample Originals — Each is a distinct source document', fontsize=14, y=1.02)

samples = [f'invoice_{i:03d}_original.png' for i in range(1, 6)] + \
          [f'receipt_{i:03d}_original.png' for i in range(1, 6)]

for ax, name in zip(axes.flat, samples):
    img = Image.open(io.BytesIO(original_bytes[name]))
    ax.imshow(img)
    label = name.replace('_original.png', '')
    ax.set_title(label, fontsize=10)
    ax.axis('off')

plt.tight_layout()
plt.show()
```

### Visualize: one original and its six variants

These images are near-duplicates of the same source — they should all land in the **same group**. Notice how each transform introduces subtle but realistic differences.

```python
sample_source = 'invoice_001'
variant_names = ['original', 'crop', 'rotate', 'bright', 'noise', 'jpeg', 'color']

fig, axes = plt.subplots(1, 7, figsize=(21, 4))
fig.suptitle(f'Near-Duplicates of {sample_source} — All should be in the same group', fontsize=13, y=1.05)

for ax, vtype in zip(axes, variant_names):
    name = f'{sample_source}_{vtype}.png'
    blob = bucket.blob(f'{PREFIX}/{name}')
    img = Image.open(io.BytesIO(blob.download_as_bytes()))
    ax.imshow(img)
    ax.set_title(vtype, fontsize=10)
    ax.axis('off')

plt.tight_layout()
plt.show()
```

---
## Step 3 — Create object table

Create a BigQuery object table pointing to the GCS folder. This lets BigQuery reference all images directly for embedding.

```python
client.query(f'''
CREATE OR REPLACE EXTERNAL TABLE `{PROJECT_ID}.{DATASET_ID}.workflow_dedup_images`
WITH CONNECTION `{PROJECT_ID}.{LOCATION}.{CONNECTION_ID}`
OPTIONS (
  object_metadata = 'SIMPLE',
  uris = ['gs://{BUCKET}/{PREFIX}/*.png']
)
''').result()

total = client.query(f'''
  SELECT COUNT(*) AS n FROM `{PROJECT_ID}.{DATASET_ID}.workflow_dedup_images`
''').to_dataframe().iloc[0]['n']
print(f'Object table ready: {total} images')
```

---
## Step 4 — Embed images with AI.EMBED

Create embeddings for all images using `gemini-embedding-2-preview`. This multimodal model supports images and PDFs directly, returning 3072-dimension vectors.

> **Note:** `gemini-embedding-2-preview` does not support the `task_type` parameter. The embeddings are general-purpose and work well for similarity-based grouping without explicit clustering configuration.

```python
query = f'''
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.workflow_dedup_embeddings` AS
SELECT
  uri,
  REGEXP_EXTRACT(uri, r'/([^/]+)$') AS image_name,
  (AI.EMBED(
    content => OBJ.GET_ACCESS_URL(
      OBJ.FETCH_METADATA(OBJ.MAKE_REF(uri, '{PROJECT_ID}.{LOCATION}.{CONNECTION_ID}')),
      'r'),
    endpoint => 'gemini-embedding-2-preview',
    connection_id => '{PROJECT_ID}.{LOCATION}.{CONNECTION_ID}'
  )).result AS embedding
FROM `{PROJECT_ID}.{DATASET_ID}.workflow_dedup_images`
'''
client.query(query).result()

df = client.query(f'''
  SELECT image_name, ARRAY_LENGTH(embedding) AS dims
  FROM `{PROJECT_ID}.{DATASET_ID}.workflow_dedup_embeddings`
  ORDER BY image_name LIMIT 5
''').to_dataframe()
total = client.query(f'''
  SELECT COUNT(*) AS n FROM `{PROJECT_ID}.{DATASET_ID}.workflow_dedup_embeddings`
''').to_dataframe().iloc[0]['n']
print(f'Embedded {total} images ({df.iloc[0]["dims"]} dimensions each)')
df
```

---
## Step 5 — Find similar pairs with VECTOR_SEARCH

Use `VECTOR_SEARCH` in batch mode — search the embeddings table against itself — to find all pairwise distances. We initially retrieve a broad set of neighbors and analyze the distance distribution before choosing a threshold.

```python
query = f'''
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.workflow_dedup_all_distances` AS
SELECT
  query.image_name AS image_a,
  base.image_name AS image_b,
  distance
FROM VECTOR_SEARCH(
  TABLE `{PROJECT_ID}.{DATASET_ID}.workflow_dedup_embeddings`,
  'embedding',
  (SELECT image_name, embedding FROM `{PROJECT_ID}.{DATASET_ID}.workflow_dedup_embeddings`),
  top_k => 80,
  distance_type => 'COSINE'
)
WHERE query.image_name < base.image_name  -- deduplicate pairs, exclude self-matches
ORDER BY distance
'''
client.query(query).result()

total_pairs = client.query(f'''
  SELECT COUNT(*) AS n FROM `{PROJECT_ID}.{DATASET_ID}.workflow_dedup_all_distances`
''').to_dataframe().iloc[0]['n']
print(f'Computed {total_pairs} pairwise distances')
```

### Analyze the distance distribution

Before choosing a threshold, look at the data. We know the ground truth — which images are variants of the same source — so we can label each pair as **same-source** (should be grouped) or **different-source** (should not).

The histogram reveals the separation — and overlap — between these distributions. In practice, some same-source pairs (especially aggressive transforms) can drift into the different-source range, and structurally similar documents (e.g., receipts from the same template) can appear closer than expected. A perfect threshold rarely exists; the goal is to find the best tradeoff for your data.

```python
distances = client.query(f'''
  SELECT
    image_a,
    image_b,
    distance,
    REGEXP_EXTRACT(image_a, r'^(.+?)_(?:original|crop|rotate|bright|noise|jpeg|color)') AS source_a,
    REGEXP_EXTRACT(image_b, r'^(.+?)_(?:original|crop|rotate|bright|noise|jpeg|color)') AS source_b
  FROM `{PROJECT_ID}.{DATASET_ID}.workflow_dedup_all_distances`
''').to_dataframe()

distances['same_source'] = distances['source_a'] == distances['source_b']

same = distances[distances['same_source']]['distance']
diff = distances[~distances['same_source']]['distance']

fig, axes = plt.subplots(1, 2, figsize=(14, 4))

# Left: overlapping histograms
ax = axes[0]
ax.hist(same, bins=50, alpha=0.7, label=f'Same source ({len(same)} pairs)', color='#2ca02c')
ax.hist(diff, bins=50, alpha=0.7, label=f'Different source ({len(diff)} pairs)', color='#d62728')
ax.set_xlabel('Cosine Distance')
ax.set_ylabel('Pair Count')
ax.set_title('Distance Distribution: Same vs Different Source')
ax.legend()

# Right: zoomed into the gap
ax = axes[1]
ax.hist(same, bins=50, alpha=0.7, label='Same source', color='#2ca02c')
ax.hist(diff[diff < 0.3], bins=50, alpha=0.7, label='Different source', color='#d62728')
ax.axvline(x=0.05, color='black', linestyle='--', linewidth=2, label='Threshold = 0.05')
ax.set_xlabel('Cosine Distance')
ax.set_ylabel('Pair Count')
ax.set_title('Zoomed — Finding the Threshold Gap')
ax.legend()

plt.tight_layout()
plt.show()

print(f'Same-source distances:  min={same.min():.4f}  max={same.max():.4f}  mean={same.mean():.4f}')
print(f'Diff-source distances:  min={diff.min():.4f}  max={diff.max():.4f}  mean={diff.mean():.4f}')
```

### Threshold sensitivity

How does the number of groups change with different thresholds? The ground truth is **20 groups** (one per source document). The chart below shows how the group count changes — look for a plateau or elbow near the target. With real data, you won't have ground truth, so the shape of this curve is your guide: a stable region suggests the threshold is capturing natural clusters rather than artifacts.

```python
thresholds = [0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.08, 0.10, 0.15, 0.20, 0.30]
group_counts = []

for t in thresholds:
    count = client.query(f'''
      WITH pairs AS (
        SELECT image_a, image_b FROM `{PROJECT_ID}.{DATASET_ID}.workflow_dedup_all_distances`
        WHERE distance < {t}
      ),
      all_edges AS (
        SELECT image_a AS image, image_b AS neighbor FROM pairs
        UNION ALL
        SELECT image_b AS image, image_a AS neighbor FROM pairs
        UNION ALL
        SELECT image_name AS image, image_name AS neighbor FROM `{PROJECT_ID}.{DATASET_ID}.workflow_dedup_embeddings`
      ),
      grouped AS (
        SELECT image, MIN(neighbor) AS group_id FROM all_edges GROUP BY image
      )
      SELECT COUNT(DISTINCT group_id) AS group_count FROM grouped
    ''').to_dataframe().iloc[0]['group_count']
    group_counts.append(count)

fig, ax = plt.subplots(figsize=(10, 4))
ax.plot(thresholds, group_counts, 'o-', linewidth=2, markersize=8, color='#1f77b4')
ax.axhline(y=20, color='green', linestyle='--', alpha=0.7, label='Target: 20 groups (ground truth)')
ax.set_xlabel('Distance Threshold')
ax.set_ylabel('Number of Groups')
ax.set_title('Threshold Sensitivity — How Group Count Changes with Distance Cutoff')
ax.legend()
ax.set_xticks(thresholds)
ax.set_xticklabels([str(t) for t in thresholds], rotation=45)
ax.grid(axis='y', alpha=0.3)

for t, c in zip(thresholds, group_counts):
    ax.annotate(str(c), (t, c), textcoords="offset points", xytext=(0, 10), ha='center', fontsize=9)

plt.tight_layout()
plt.show()

print('Threshold → Groups:')
for t, c in zip(thresholds, group_counts):
    marker = ' ← target' if c == 20 else ''
    print(f'  {t:.2f} → {c} groups{marker}')
```

### Apply the chosen threshold

We use **0.05** as the distance threshold. This value sits in the conservative region of the curve above — tight enough to avoid merging unrelated documents (high precision), while still catching most same-source variants (good recall). Looser thresholds risk chaining: connected components propagates similarity transitively, so even a few cross-source edges at higher thresholds can collapse distinct groups into mega-clusters.

In practice, threshold selection requires experimentation with your data. The sensitivity chart above is a diagnostic tool — look for a stable region where the group count plateaus near your expected number of clusters. When in doubt, err on the side of a tighter threshold: it's better to miss a few variants (lower recall) than to incorrectly merge different sources (lower precision).

```python
THRESHOLD = 0.05

query = f'''
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.workflow_dedup_pairs` AS
SELECT image_a, image_b, distance
FROM `{PROJECT_ID}.{DATASET_ID}.workflow_dedup_all_distances`
WHERE distance < {THRESHOLD}
ORDER BY distance
'''
client.query(query).result()

total_pairs = client.query(f'''
  SELECT COUNT(*) AS n FROM `{PROJECT_ID}.{DATASET_ID}.workflow_dedup_pairs`
''').to_dataframe().iloc[0]['n']
print(f'Threshold: {THRESHOLD} → {total_pairs} similar pairs')
```

---
## Step 6 — Approach 1: Direct grouping

**Single-pass grouping:** For each image, assign it to the group with the minimum image name among itself and all its direct neighbors. Simple and efficient — one query, no iteration.

This works well when all same-source images are directly similar to each other. It can miss indirect connections: if A↔B and B↔C are similar but A↔C are not (below threshold), direct grouping keeps them in separate groups.

```python
query = f'''
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.workflow_dedup_groups_direct` AS
WITH all_edges AS (
  SELECT image_a AS image, image_b AS neighbor FROM `{PROJECT_ID}.{DATASET_ID}.workflow_dedup_pairs`
  UNION ALL
  SELECT image_b, image_a FROM `{PROJECT_ID}.{DATASET_ID}.workflow_dedup_pairs`
  UNION ALL
  SELECT image_name, image_name FROM `{PROJECT_ID}.{DATASET_ID}.workflow_dedup_embeddings`
)
SELECT
  image AS image_name,
  MIN(neighbor) AS group_id
FROM all_edges
GROUP BY image
ORDER BY group_id, image
'''
client.query(query).result()

groups_direct = client.query(f'''
  SELECT
    group_id,
    COUNT(*) AS image_count,
    STRING_AGG(image_name, ', ' ORDER BY image_name) AS images
  FROM `{PROJECT_ID}.{DATASET_ID}.workflow_dedup_groups_direct`
  GROUP BY group_id
  ORDER BY image_count DESC, group_id
''').to_dataframe()
print(f'Direct grouping: {len(groups_direct)} groups')
groups_direct
```

---
## Step 7 — Approach 2: Connected components (transitive grouping)

**Iterative propagation:** Use BigQuery scripting with a `WHILE` loop to propagate group membership through chains of similarity. If A↔B are similar and B↔C are similar, then A/B/C form one group — even if A↔C are not directly similar.

This handles "chain" connections that direct grouping misses. For video frames, this matters when frame 1 is similar to frame 50, and frame 50 is similar to frame 100, but frame 1 and frame 100 have drifted apart.

```python
query = f'''
DECLARE changes INT64 DEFAULT 1;
DECLARE iterations INT64 DEFAULT 0;

CREATE TEMP TABLE components AS
SELECT image_name, image_name AS component_id
FROM `{PROJECT_ID}.{DATASET_ID}.workflow_dedup_embeddings`;

CREATE TEMP TABLE edges AS
SELECT image_a AS src, image_b AS dst FROM `{PROJECT_ID}.{DATASET_ID}.workflow_dedup_pairs`
UNION ALL
SELECT image_b, image_a FROM `{PROJECT_ID}.{DATASET_ID}.workflow_dedup_pairs`;

WHILE changes > 0 AND iterations < 100 DO
  SET iterations = iterations + 1;

  CREATE OR REPLACE TEMP TABLE new_components AS
  SELECT
    c.image_name,
    LEAST(
      c.component_id,
      IFNULL(
        (SELECT MIN(c2.component_id)
         FROM edges e
         JOIN components c2 ON e.dst = c2.image_name
         WHERE e.src = c.image_name),
        c.component_id
      )
    ) AS component_id
  FROM components c;

  SET changes = (
    SELECT COUNTIF(o.component_id != n.component_id)
    FROM components o
    JOIN new_components n USING (image_name)
  );

  CREATE OR REPLACE TEMP TABLE components AS
  SELECT * FROM new_components;
END WHILE;

CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.workflow_dedup_groups_connected` AS
SELECT image_name, component_id AS group_id
FROM components
ORDER BY group_id, image_name;

SELECT iterations AS total_iterations, changes AS final_changes;
'''
client.query(query).result()

groups_cc = client.query(f'''
  SELECT
    group_id,
    COUNT(*) AS image_count,
    STRING_AGG(image_name, ', ' ORDER BY image_name) AS images
  FROM `{PROJECT_ID}.{DATASET_ID}.workflow_dedup_groups_connected`
  GROUP BY group_id
  ORDER BY image_count DESC, group_id
''').to_dataframe()
print(f'Connected components: {len(groups_cc)} groups')
groups_cc
```

---
## Step 8 — Compare grouping approaches

Compare the two approaches: how many groups does each produce, and where do they differ?

Neither approach is guaranteed to match ground truth perfectly — structurally similar documents may merge, and aggressive transforms may not be recovered. The comparison highlights when transitive closure matters: connected components will always produce ≤ the number of groups from direct grouping, since it can merge groups that share indirect connections.

```python
direct_count = client.query(f'''
  SELECT COUNT(DISTINCT group_id) AS n FROM `{PROJECT_ID}.{DATASET_ID}.workflow_dedup_groups_direct`
''').to_dataframe().iloc[0]['n']

cc_count = client.query(f'''
  SELECT COUNT(DISTINCT group_id) AS n FROM `{PROJECT_ID}.{DATASET_ID}.workflow_dedup_groups_connected`
''').to_dataframe().iloc[0]['n']

print(f'Direct grouping:      {direct_count} groups')
print(f'Connected components: {cc_count} groups')
print(f'Ground truth:         20 groups')
diff = direct_count - cc_count
if diff > 0:
    print(f'\nConnected components merged {diff} additional group(s) via transitive closure')
else:
    print(f'\nBoth approaches produced identical groupings')

comparison = client.query(f'''
  SELECT
    d.image_name,
    d.group_id AS direct_group,
    c.group_id AS connected_group
  FROM `{PROJECT_ID}.{DATASET_ID}.workflow_dedup_groups_direct` d
  JOIN `{PROJECT_ID}.{DATASET_ID}.workflow_dedup_groups_connected` c USING (image_name)
  WHERE d.group_id != c.group_id
  ORDER BY c.group_id, d.image_name
''').to_dataframe()

if len(comparison) > 0:
    print(f'\n{len(comparison)} images assigned to different groups:')
    print(comparison.to_string(index=False))
else:
    print('No differences — for this dataset, both approaches are equivalent.')
```

---
## Step 9 — Validate: precision and recall against ground truth

Since we know which images are variants of which source, we can measure grouping quality:

- **Precision:** Of all image pairs placed in the same group, what fraction are truly from the same source? (High precision = few false merges)
- **Recall:** Of all true same-source pairs, what fraction did we correctly group together? (High recall = few missed connections)

In practice, perfect scores are rare. Template-based documents (like invoices from the same vendor) may look similar enough to merge across sources (lowering precision), while aggressive transforms may push variants beyond the threshold (lowering recall). The threshold controls this tradeoff — tighter thresholds favor precision, looser thresholds favor recall.

```python
pr = client.query(f'''
  WITH ground_truth AS (
    SELECT
      a.image_name AS image_a,
      b.image_name AS image_b,
      REGEXP_EXTRACT(a.image_name, r'^(.+?)_(?:original|crop|rotate|bright|noise|jpeg|color)') AS source_a,
      REGEXP_EXTRACT(b.image_name, r'^(.+?)_(?:original|crop|rotate|bright|noise|jpeg|color)') AS source_b
    FROM `{PROJECT_ID}.{DATASET_ID}.workflow_dedup_groups_connected` a
    CROSS JOIN `{PROJECT_ID}.{DATASET_ID}.workflow_dedup_groups_connected` b
    WHERE a.image_name < b.image_name
  ),
  predictions AS (
    SELECT
      a.image_name AS image_a,
      b.image_name AS image_b,
      (a.group_id = b.group_id) AS predicted_same
    FROM `{PROJECT_ID}.{DATASET_ID}.workflow_dedup_groups_connected` a
    CROSS JOIN `{PROJECT_ID}.{DATASET_ID}.workflow_dedup_groups_connected` b
    WHERE a.image_name < b.image_name
  )
  SELECT
    COUNTIF(p.predicted_same AND g.source_a = g.source_b) AS true_positives,
    COUNTIF(p.predicted_same AND g.source_a != g.source_b) AS false_positives,
    COUNTIF(NOT p.predicted_same AND g.source_a = g.source_b) AS false_negatives,
    COUNTIF(NOT p.predicted_same AND g.source_a != g.source_b) AS true_negatives
  FROM ground_truth g
  JOIN predictions p ON g.image_a = p.image_a AND g.image_b = p.image_b
''').to_dataframe()

tp = pr.iloc[0]['true_positives']
fp = pr.iloc[0]['false_positives']
fn = pr.iloc[0]['false_negatives']
tn = pr.iloc[0]['true_negatives']

precision = tp / (tp + fp) if (tp + fp) > 0 else 0
recall = tp / (tp + fn) if (tp + fn) > 0 else 0
f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

print(f'Grouping quality (threshold = {THRESHOLD}):')
print(f'  True positives:  {tp} (correctly grouped same-source pairs)')
print(f'  False positives: {fp} (incorrectly merged different-source pairs)')
print(f'  False negatives: {fn} (missed same-source pairs)')
print(f'  True negatives:  {tn} (correctly separated different-source pairs)')
print()
print(f'  Precision: {precision:.4f} — {"no false merges" if fp == 0 else f"{fp} pairs incorrectly merged"}')
print(f'  Recall:    {recall:.4f} — {"all same-source pairs grouped" if fn == 0 else f"{fn} pairs missed"}')
print(f'  F1 Score:  {f1:.4f}')
```

---
## Step 10 — Train/test split: naive vs correct

Demonstrate the critical difference between naive image-level splitting and correct group-level splitting.

- **Naive (image-level):** Randomly assign each image to train or test. Near-duplicates from the same source can end up in both sets — data leakage.
- **Correct (group-level):** Assign entire groups to train or test. All variants of the same source stay together, preventing leakage.

```python
split_results = client.query(f'''
  WITH image_splits AS (
    SELECT
      image_name,
      group_id,
      IF(MOD(ABS(FARM_FINGERPRINT(group_id)), 10) < 7, 'train', 'test') AS correct_split,
      IF(MOD(ABS(FARM_FINGERPRINT(image_name)), 10) < 7, 'train', 'test') AS naive_split
    FROM `{PROJECT_ID}.{DATASET_ID}.workflow_dedup_groups_connected`
  ),
  leakage_check AS (
    SELECT
      group_id,
      COUNT(*) AS images_in_group,
      COUNT(DISTINCT correct_split) AS correct_split_count,
      COUNT(DISTINCT naive_split) AS naive_split_count,
      STRING_AGG(CONCAT(image_name, ' [', naive_split, ']'), ', ' ORDER BY image_name) AS naive_detail
    FROM image_splits
    GROUP BY group_id
    HAVING images_in_group > 1
  )
  SELECT * FROM leakage_check
  ORDER BY naive_split_count DESC, images_in_group DESC
''').to_dataframe()

leaked = split_results[split_results['naive_split_count'] > 1]
clean = split_results[split_results['naive_split_count'] == 1]

print(f'Multi-image groups: {len(split_results)}')
print(f'  Correct approach: all {len(split_results)} groups kept intact (no leakage)')
print()

if len(leaked) > 0:
    print(f'  Naive approach: {len(leaked)} group(s) leaked across train/test:')
    for _, row in leaked.iterrows():
        print(f"    {row['group_id']} ({row['images_in_group']} images)")
    print()

stats = client.query(f'''
  SELECT
    'Correct (group-level)' AS approach,
    COUNTIF(split = 'train') AS train_images,
    COUNTIF(split = 'test') AS test_images
  FROM (
    SELECT IF(MOD(ABS(FARM_FINGERPRINT(group_id)), 10) < 7, 'train', 'test') AS split
    FROM `{PROJECT_ID}.{DATASET_ID}.workflow_dedup_groups_connected`
  )
  UNION ALL
  SELECT
    'Naive (image-level)',
    COUNTIF(split = 'train'),
    COUNTIF(split = 'test')
  FROM (
    SELECT IF(MOD(ABS(FARM_FINGERPRINT(image_name)), 10) < 7, 'train', 'test') AS split
    FROM `{PROJECT_ID}.{DATASET_ID}.workflow_dedup_groups_connected`
  )
''').to_dataframe()
print('Split statistics:')
print(stats.to_string(index=False))
```
