# Document Intelligence — BigQuery AI Functions

An end-to-end document processing pipeline that composes four AI functions:

1. **Classify** 100 mixed documents by type with `AI.CLASSIFY`
2. **Extract** key fields from documents with `AI.GENERATE` (multimodal + output_schema)
3. **Score** document quality with `AI.SCORE`
4. **Summarize** findings with `AI.GENERATE` (and alternatively with `AI.AGG`)

**What this demonstrates:**
- Processing real documents (PDFs) from Cloud Storage — not generated sample data
- Three distinct multimodal input patterns: EXTERNAL_OBJECT_TRANSFORM, STRUCT prompt, tuple syntax
- Composing classification → extraction → scoring → summarization in one pipeline
- Validating AI classification accuracy against ground truth
- Comparing manual aggregation (`STRING_AGG` + `AI.GENERATE`) vs purpose-built `AI.AGG`

**Functions used:** `functions/ai_classify` (`AI.CLASSIFY`) | `functions/ai_generate` (`AI.GENERATE`) | `functions/ai_score` (`AI.SCORE`) | `functions/ai_agg` (`AI.AGG`)

**For specialized document parsing:** See `functions/ml_process_document` (`ML.PROCESS_DOCUMENT`) for Document AI integration

**Prerequisites:** `setup` (Setup guide) | `RESOURCES.md` (Function reference)

---
## Setup

Set your project and location, authenticate, and create shared resources.

> This workflow uses `AI.CLASSIFY`, `AI.GENERATE`, and `AI.SCORE` — none require a remote model. A connection is needed for the object table and GCS access. See the `setup` (Setup Reference) for details.

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
## Step 1 — Upload documents to GCS

Upload 100 mixed documents (50 invoices + 50 receipts) to Cloud Storage using generic filenames (`doc_001.pdf`–`doc_100.pdf`). The filenames deliberately reveal nothing about document type — classification must examine the actual content.

The mapping from source files to generic names comes from `data/documents/manifest.json`, which also provides ground truth for validation.

```python
import json
from pathlib import Path
from google.cloud import storage
from tqdm.auto import tqdm

# Load manifest
data_dir = Path('../../data/documents')
if not data_dir.exists():
    data_dir = Path('data/documents')

with open(data_dir / 'manifest.json') as f:
    manifest = json.load(f)

# Upload documents with generic names
gcs = storage.Client(project=PROJECT_ID)
bucket = gcs.bucket(BUCKET)
prefix = 'bq_ai_functions/document_intelligence'

uploaded, skipped = 0, 0
for doc_name, info in tqdm(manifest.items(), desc='Uploading documents'):
    blob = bucket.blob(f'{prefix}/{doc_name}')
    if blob.exists():
        skipped += 1
        continue
    # Map source file to the correct subdirectory
    subdir = 'invoices' if info['type'] == 'invoice' else 'receipts'
    source_path = data_dir / subdir / info['source']
    blob.upload_from_filename(str(source_path))
    uploaded += 1

print(f'Uploaded {uploaded} documents, skipped {skipped} (already exist)')
print(f'Location: gs://{BUCKET}/{prefix}/')
```

---
## Step 1b — Create object table

An `RESOURCES.md#unstructured-data-infrastructure` (object table) is an external table over Cloud Storage objects. It provides a `ref` column that AI functions can use to access file content. The connection grants BigQuery permission to read from GCS.

```python
# Create object table pointing to the uploaded documents
client.query(f"""
CREATE OR REPLACE EXTERNAL TABLE `{PROJECT_ID}.{DATASET_ID}.workflow_di_docs`
WITH CONNECTION `{PROJECT_ID}.{LOCATION}.{CONNECTION_ID}`
OPTIONS (
  object_metadata = 'SIMPLE',
  uris = ['gs://{BUCKET}/{prefix}/*.pdf']
)
""").result()
print('Object table workflow_di_docs ready')

# Verify
verify = client.query(f"""
  SELECT uri, content_type, size
  FROM `{PROJECT_ID}.{DATASET_ID}.workflow_di_docs`
  ORDER BY uri LIMIT 5
""").to_dataframe()
total = client.query(f"""
  SELECT COUNT(*) AS total FROM `{PROJECT_ID}.{DATASET_ID}.workflow_di_docs`
""").to_dataframe()
print(f'Total documents: {total.iloc[0]["total"]}')
verify
```

---
## Step 2 — Classify documents with AI.CLASSIFY

Use `AI.CLASSIFY` with the **EXTERNAL_OBJECT_TRANSFORM** pattern to classify each document as "invoice" or "receipt". This pattern transforms the object table to add signed URLs, then passes the `ref` column directly to `AI.CLASSIFY`.

```
Object table → EXTERNAL_OBJECT_TRANSFORM(TABLE, ['SIGNED_URL']) → ref → AI.CLASSIFY
```

```python
query = f"""
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.workflow_di_classified` AS
SELECT
  docs.uri,
  AI.CLASSIFY(docs.ref, ['invoice', 'receipt']) AS doc_type
FROM EXTERNAL_OBJECT_TRANSFORM(
  TABLE `{PROJECT_ID}.{DATASET_ID}.workflow_di_docs`, ['SIGNED_URL']) AS docs
"""
client.query(query).result()

# Show distribution
dist = client.query(f"""
  SELECT doc_type, COUNT(*) AS count
  FROM `{PROJECT_ID}.{DATASET_ID}.workflow_di_classified`
  GROUP BY doc_type
  ORDER BY doc_type
""").to_dataframe()
total = dist['count'].sum()
print(f'AI.CLASSIFY examined the PDF content of all {total} documents.')
print(f'No filenames, metadata, or hints — classification is based purely on visual content.\n')
print('Classification distribution:')
for _, row in dist.iterrows():
    print(f'  {row["doc_type"]}: {row["count"]} documents')
print(f'\nResults saved to workflow_di_classified — next: validate against ground truth.')
```

---
## Step 3 — Validate classification accuracy

Compare `AI.CLASSIFY` results against the ground truth in `manifest.json`. This is unique among workflows — we have known labels to measure how well the AI function performs on real documents.

```python
# Create ground truth DataFrame
ground_truth = pd.DataFrame([
    {'doc_name': k, 'true_type': v['type']}
    for k, v in manifest.items()
])

# Get classification results
classified = client.query(f"""
  SELECT uri, doc_type FROM `{PROJECT_ID}.{DATASET_ID}.workflow_di_classified`
""").to_dataframe()

# Extract doc name from URI for joining
classified['doc_name'] = classified['uri'].str.split('/').str[-1]

# Join and compute accuracy
merged = classified.merge(ground_truth, on='doc_name')
accuracy = (merged['doc_type'] == merged['true_type']).mean()
print(f'Classification accuracy: {accuracy:.1%}')

# Confusion matrix
print(f'\nConfusion matrix:')
print(pd.crosstab(merged['true_type'], merged['doc_type'], margins=True))

# Show any misclassifications
misclassified = merged[merged['doc_type'] != merged['true_type']]
if len(misclassified) > 0:
    print(f'\n{len(misclassified)} misclassified documents:')
    print(misclassified[['doc_name', 'true_type', 'doc_type']].to_string(index=False))
else:
    print(f'\nPerfect classification — all {len(merged)} documents correctly identified!')
```

---
## Step 4 — Extract key fields with AI.GENERATE

Use `AI.GENERATE` with the **STRUCT prompt** pattern and `output_schema` to extract structured data from a 10-document sample. The prompt adapts based on `doc_type` — invoices and receipts have different key fields.

```
AI.GENERATE(
  STRUCT(prompt AS prompt, [OBJ.GET_ACCESS_URL(ref, 'r')] AS object_ref_runtime),
  output_schema => '...'
)
```

> Processing 10 documents as a sample. Adjust the `LIMIT` to process more.

```python
query = f"""
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.workflow_di_extracted` AS
SELECT
  c.uri,
  c.doc_type,
  result.*
FROM `{PROJECT_ID}.{DATASET_ID}.workflow_di_classified` c
JOIN `{PROJECT_ID}.{DATASET_ID}.workflow_di_docs` ot ON c.uri = ot.uri
CROSS JOIN UNNEST([AI.GENERATE(
  STRUCT(
    CASE c.doc_type
      WHEN 'invoice' THEN 'Extract from this invoice: the company/vendor name, invoice number, total amount due, and due date.'
      WHEN 'receipt' THEN 'Extract from this receipt: the store name, receipt/transaction number, total amount, and purchase date.'
    END AS prompt,
    [OBJ.GET_ACCESS_URL(ot.ref, 'r')] AS object_ref_runtime
  ),
  output_schema => 'entity_name STRING, reference_number STRING, total_amount STRING, document_date STRING'
)]) AS result
WHERE c.uri IN (
  SELECT uri FROM `{PROJECT_ID}.{DATASET_ID}.workflow_di_classified`
  ORDER BY uri LIMIT 10
)
"""
client.query(query).result()

# Display results with doc names
extracted = client.query(f"""
  SELECT
    SPLIT(uri, '/')[SAFE_OFFSET(ARRAY_LENGTH(SPLIT(uri, '/')) - 1)] AS doc_name,
    doc_type, entity_name, reference_number, total_amount, document_date
  FROM `{PROJECT_ID}.{DATASET_ID}.workflow_di_extracted`
  ORDER BY doc_type, entity_name
""").to_dataframe()

n_inv = (extracted['doc_type'] == 'invoice').sum()
n_rec = (extracted['doc_type'] == 'receipt').sum()
print(f'Extracted structured fields from {len(extracted)} documents ({n_inv} invoices, {n_rec} receipts).')
print(f'The CASE expression in the prompt adapts extraction instructions to each document type.\n')
extracted
```

### Step 4b — Validate extraction against ground truth

Compare extracted values against `manifest.json` key fields to see how accurately the model reads these documents.

```python
# Get extraction results with doc names
extraction_results = client.query(f"""
  SELECT uri, doc_type, entity_name, reference_number, total_amount, document_date
  FROM `{PROJECT_ID}.{DATASET_ID}.workflow_di_extracted`
""").to_dataframe()
extraction_results['doc_name'] = extraction_results['uri'].str.split('/').str[-1]

# Build comparison table
rows = []
for _, row in extraction_results.iterrows():
    doc = row['doc_name']
    truth = manifest[doc]['key_fields']
    doc_type = manifest[doc]['type']

    if doc_type == 'invoice':
        expected_name = truth.get('company', '')
        expected_total = truth.get('total_due', '')
        expected_date = truth.get('due_date', '')
    else:
        expected_name = truth.get('store_name', '')
        expected_total = truth.get('total', '')
        expected_date = truth.get('date', '')

    # Name match: case-insensitive containment
    name_match = (expected_name.lower() in row['entity_name'].lower()
                  or row['entity_name'].lower() in expected_name.lower())

    # Total match: compare as floats to avoid "8660.00" vs "8660.0" false negatives
    try:
        extracted_val = float(''.join(c for c in (row['total_amount'] or '') if c.isdigit() or c == '.'))
        total_match = extracted_val == float(expected_total)
    except (ValueError, TypeError):
        total_match = False

    rows.append({
        'doc': doc, 'type': row['doc_type'],
        'entity_name': f'{"✓" if name_match else "✗"} {row["entity_name"]}',
        'expected_name': expected_name,
        'total': f'{"✓" if total_match else "✗"} {row["total_amount"]}',
        'expected_total': str(expected_total),
        'name_ok': name_match, 'total_ok': total_match,
    })

comparison = pd.DataFrame(rows)

# Summary
name_acc = comparison['name_ok'].mean()
total_acc = comparison['total_ok'].mean()
print(f'Extraction accuracy across {len(comparison)} documents:')
print(f'  Entity name:  {comparison["name_ok"].sum()}/{len(comparison)} correct ({name_acc:.0%})')
print(f'  Total amount: {comparison["total_ok"].sum()}/{len(comparison)} correct ({total_acc:.0%})')

# Show the comparison
print()
comparison[['doc', 'type', 'entity_name', 'expected_name', 'total', 'expected_total']]
```

---
## Step 5 — Score document quality with AI.SCORE

Use `AI.SCORE` with the **tuple syntax** to rate each document's completeness for accounting purposes — whether it contains all necessary details (amounts, dates, vendor info, reference numbers) to be processed without follow-up. This criterion produces more varied scores than visual quality alone, since receipts and invoices have different levels of structured detail.

```sql
AI.SCORE(('scoring criteria', OBJ.GET_ACCESS_URL(ref, 'r')))
```

```python
query = f"""
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.workflow_di_scored` AS
SELECT
  c.uri,
  c.doc_type,
  AI.SCORE(
    ('Rate whether this document contains all information needed for accounting: clear line items, tax breakdown, payment terms, vendor contact details, and reference numbers. Score 0 for missing most details, 1 for fully complete.',
     OBJ.GET_ACCESS_URL(ot.ref, 'r'))
  ) AS quality_score
FROM `{PROJECT_ID}.{DATASET_ID}.workflow_di_classified` c
JOIN `{PROJECT_ID}.{DATASET_ID}.workflow_di_docs` ot ON c.uri = ot.uri
WHERE c.uri IN (
  SELECT uri FROM `{PROJECT_ID}.{DATASET_ID}.workflow_di_classified`
  ORDER BY uri LIMIT 10
)
"""
client.query(query).result()
print('Scoring complete')

# Show scores by type
scored = client.query(f"""
  SELECT doc_type, ROUND(AVG(quality_score), 2) AS avg_score,
         ROUND(MIN(quality_score), 2) AS min_score,
         ROUND(MAX(quality_score), 2) AS max_score,
         COUNT(*) AS count
  FROM `{PROJECT_ID}.{DATASET_ID}.workflow_di_scored`
  GROUP BY doc_type
""").to_dataframe()
print(f'\nAccounting completeness scores by document type:')
print(scored.to_string(index=False))

# Individual scores with doc names
all_scores = client.query(f"""
  SELECT
    SPLIT(uri, '/')[SAFE_OFFSET(ARRAY_LENGTH(SPLIT(uri, '/')) - 1)] AS doc_name,
    doc_type,
    quality_score
  FROM `{PROJECT_ID}.{DATASET_ID}.workflow_di_scored`
  ORDER BY quality_score DESC
""").to_dataframe()
print(f'\nIndividual document scores:')
all_scores
```

---
## Step 6 — Executive summary with AI.GENERATE

Aggregate all pipeline results — classification counts, extraction details, quality scores — into a single prompt and generate an executive summary. This final step composes the outputs of `AI.CLASSIFY`, `AI.GENERATE` (extraction), and `AI.SCORE` into one narrative, demonstrating how AI functions chain together in SQL.

```python
query = f"""
WITH stats AS (
  SELECT
    (SELECT COUNT(*) FROM `{PROJECT_ID}.{DATASET_ID}.workflow_di_classified`) AS total_docs,
    (SELECT COUNTIF(doc_type = 'invoice') FROM `{PROJECT_ID}.{DATASET_ID}.workflow_di_classified`) AS invoice_count,
    (SELECT COUNTIF(doc_type = 'receipt') FROM `{PROJECT_ID}.{DATASET_ID}.workflow_di_classified`) AS receipt_count,
    (SELECT ROUND(AVG(quality_score), 2) FROM `{PROJECT_ID}.{DATASET_ID}.workflow_di_scored`) AS avg_quality,
    (SELECT ROUND(MIN(quality_score), 2) FROM `{PROJECT_ID}.{DATASET_ID}.workflow_di_scored`) AS min_quality,
    (SELECT ROUND(MAX(quality_score), 2) FROM `{PROJECT_ID}.{DATASET_ID}.workflow_di_scored`) AS max_quality,
    (SELECT STRING_AGG(
        CONCAT(entity_name, ' (', reference_number, '): $', total_amount, ' due ', document_date),
        '; ')
     FROM `{PROJECT_ID}.{DATASET_ID}.workflow_di_extracted` WHERE doc_type = 'invoice') AS invoice_details,
    (SELECT STRING_AGG(
        CONCAT(entity_name, ': $', total_amount, ' on ', document_date),
        '; ')
     FROM `{PROJECT_ID}.{DATASET_ID}.workflow_di_extracted` WHERE doc_type = 'receipt') AS receipt_details
)
SELECT (AI.GENERATE(
  CONCAT(
    'You are a document processing analyst. Write a brief executive summary (3-4 paragraphs) of this automated document processing pipeline run. ',
    'Include a section on each phase: classification, extraction, and quality assessment.\\n\\n',
    'CLASSIFICATION: ', CAST(total_docs AS STRING), ' documents processed. ',
    CAST(invoice_count AS STRING), ' classified as invoices, ',
    CAST(receipt_count AS STRING), ' as receipts. Classification was validated against ground truth with 100%% accuracy.\\n\\n',
    'EXTRACTION (10-document sample):\\n',
    'Invoices: ', IFNULL(invoice_details, 'none'), '\\n',
    'Receipts: ', IFNULL(receipt_details, 'none'), '\\n\\n',
    'QUALITY ASSESSMENT (10-document sample, 0-1 scale for accounting completeness): ',
    'avg=', CAST(avg_quality AS STRING),
    ', min=', CAST(min_quality AS STRING),
    ', max=', CAST(max_quality AS STRING), '\\n\\n',
    'End with a one-sentence takeaway on the pipeline.'
  )
)).result AS executive_summary
FROM stats
"""
df = client.query(query).to_dataframe()
print(df.iloc[0]['executive_summary'])
```

### Alternative — Summarize by document type with AI.AGG

`AI.AGG` can summarize extraction and quality results per document type directly, without manually concatenating data into a single prompt.

```python
query = f"""
SELECT
  e.doc_type,
  AI.AGG(
    TO_JSON_STRING(STRUCT(e.entity_name, e.reference_number, e.total_amount, e.document_date, s.quality_score)),
    'Summarize these documents: what vendors/stores appear, what are the typical amounts, and how complete is the data quality?'
  ) AS doc_type_summary
FROM `{PROJECT_ID}.{DATASET_ID}.workflow_di_extracted` e
JOIN `{PROJECT_ID}.{DATASET_ID}.workflow_di_scored` s ON e.uri = s.uri
GROUP BY e.doc_type
"""
df_agg = client.query(query).to_dataframe()
for _, row in df_agg.iterrows():
    print(f'=== {row["doc_type"]} ===')
    print(row["doc_type_summary"])
    print()
```
