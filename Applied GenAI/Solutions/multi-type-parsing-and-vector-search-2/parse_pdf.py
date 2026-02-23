"""Parse PDFs from GCS: Document AI Layout Parser v1.5 batch processing → BigQuery."""

from google.cloud import bigquery, documentai, storage
from config import (
    PROJECT_ID, BQ_PROJECT, BQ_DATASET, BQ_TABLE_PREFIX,
    GCS_BUCKET, GCS_ROOT,
    DOCAI_LOCATION, DOCAI_PROCESSOR_DISPLAY_NAME, DOCAI_PROCESSOR_TYPE, DOCAI_PROCESSOR_VERSION,
)
import re
import hashlib
from datetime import datetime, timezone

# --- Clients ---

bq = bigquery.Client(project=BQ_PROJECT)
gcs = storage.Client(project=PROJECT_ID)
docai_client = documentai.DocumentProcessorServiceClient(
    client_options=dict(api_endpoint=f"{DOCAI_LOCATION}-documentai.googleapis.com")
)

# --- Config ---

# Layout Parser chunking options (applied during batch processing)
CHUNK_SIZE = 500  # target tokens per chunk
INCLUDE_ANCESTOR_HEADINGS = True  # prepend heading hierarchy to each chunk for self-contained context

# GCS paths for batch I/O
GCS_PDF_PREFIX = f"gs://{GCS_BUCKET}/{GCS_ROOT}/generated_pdf/"
GCS_DOCAI_OUTPUT = f"gs://{GCS_BUCKET}/{GCS_ROOT}/docai_output"

# --- Get or create Layout Parser processor ---

parent = f"projects/{PROJECT_ID}/locations/{DOCAI_LOCATION}"

processor = None
for p in docai_client.list_processors(parent=parent):
    if p.display_name == DOCAI_PROCESSOR_DISPLAY_NAME:
        processor = p
        print(f"Found existing processor: {processor.name}")
        break

if processor is None:
    processor = docai_client.create_processor(
        parent=parent,
        processor=dict(
            display_name=DOCAI_PROCESSOR_DISPLAY_NAME,
            type_=DOCAI_PROCESSOR_TYPE,
            default_processor_version=DOCAI_PROCESSOR_VERSION,
        ),
    )
    print(f"Created processor: {processor.name}")

# --- Target table ---

table_ref = f"{BQ_PROJECT}.{BQ_DATASET}.{BQ_TABLE_PREFIX}_pdf_chunks"

schema = [
    bigquery.SchemaField("chunk_id", "STRING"),
    bigquery.SchemaField("source_uri", "STRING"),
    bigquery.SchemaField("text_content", "STRING"),
    bigquery.SchemaField("page_start", "INTEGER"),
    bigquery.SchemaField("page_end", "INTEGER"),
    bigquery.SchemaField("processed_at", "TIMESTAMP"),
]

# Create table if it doesn't exist
table = bigquery.Table(table_ref, schema=schema)
bq.create_table(table, exists_ok=True)

# --- Get PDF source files, detect which need (re)processing ---

source_query = f"""
SELECT s.uri, s.updated AS source_updated
FROM `{BQ_PROJECT}.{BQ_DATASET}.{BQ_TABLE_PREFIX}_source` s
WHERE s.content_type = 'application/pdf'
"""
source_rows = list(bq.query(source_query).result())

# Check which files already have up-to-date chunks
try:
    processed_query = f"""
    SELECT source_uri, MAX(processed_at) as last_processed
    FROM `{table_ref}`
    GROUP BY source_uri
    """
    processed = {row.source_uri: row.last_processed for row in bq.query(processed_query).result()}
except Exception:
    processed = {}

# Only process files that are new or updated since last processing
files_to_process = []
for row in source_rows:
    last = processed.get(row.uri)
    if last is None or row.source_updated > last:
        files_to_process.append(row.uri)
    else:
        print(f"Skipping (up to date): {row.uri.split('/')[-1]}")

print(f"Found {len(source_rows)} PDF files, {len(files_to_process)} need processing")

if not files_to_process:
    total = bq.query(f"SELECT COUNT(*) as n FROM `{table_ref}`").result()
    print(f"\nTotal rows in {table_ref}: {list(total)[0].n}")
    exit()

# --- Submit batch job for files that need processing ---

print(f"\nSubmitting batch job for {len(files_to_process)} PDF files...")

batch_job = docai_client.batch_process_documents(
    request=documentai.BatchProcessRequest(
        name=processor.name,
        input_documents=documentai.BatchDocumentsInputConfig(
            gcs_documents=documentai.GcsDocuments(
                documents=[
                    documentai.GcsDocument(gcs_uri=uri, mime_type="application/pdf")
                    for uri in files_to_process
                ]
            )
        ),
        document_output_config=documentai.DocumentOutputConfig(
            gcs_output_config=documentai.DocumentOutputConfig.GcsOutputConfig(
                gcs_uri=GCS_DOCAI_OUTPUT,
            )
        ),
        process_options=documentai.ProcessOptions(
            layout_config=documentai.ProcessOptions.LayoutConfig(
                chunking_config=documentai.ProcessOptions.LayoutConfig.ChunkingConfig(
                    chunk_size=CHUNK_SIZE,
                    include_ancestor_headings=INCLUDE_ANCESTOR_HEADINGS,
                )
            )
        ),
    )
)

print(f"Batch job: {batch_job.operation.name}")
print("Waiting for completion...")
batch_job.result()

metadata = documentai.BatchProcessMetadata(batch_job.metadata)
print(f"Batch job state: {metadata.state}")

# --- Read batch results from GCS and load into BigQuery ---

bucket = gcs.bucket(GCS_BUCKET)
now = datetime.now(timezone.utc).isoformat()

for process in metadata.individual_process_statuses:
    input_uri = process.input_gcs_source
    output_dest = process.output_gcs_destination
    filename = input_uri.split("/")[-1].replace(".pdf", "")

    print(f"\nProcessing result: {filename}")

    if process.status.code != 0:
        print(f"  Error: {process.status.message}")
        continue

    # Read parsed document from the GCS output location
    output_match = re.match(r"gs://[^/]+/(.*)", output_dest)
    output_prefix = output_match.group(1)
    # Ensure trailing slash so prefix "…/1/" doesn't match "…/10/" and "…/11/"
    if not output_prefix.endswith("/"):
        output_prefix += "/"

    # Hash filename to stay within the 64-char DataObjectId limit for Vector Search
    file_hash = hashlib.md5(filename.encode()).hexdigest()[:10]

    rows = []
    for blob in bucket.list_blobs(prefix=output_prefix):
        if not blob.name.endswith(".json"):
            continue
        doc = documentai.Document.from_json(
            blob.download_as_bytes(), ignore_unknown_fields=True
        )
        for chunk in doc.chunked_document.chunks:
            rows.append({
                "chunk_id": f"pdf_{file_hash}_{chunk.chunk_id}",
                "source_uri": input_uri,
                "text_content": chunk.content,
                "page_start": chunk.page_span.page_start if chunk.page_span else None,
                "page_end": chunk.page_span.page_end if chunk.page_span else None,
                "processed_at": now,
            })

    # Delete existing chunks for this file, then insert new ones
    delete_query = f"DELETE FROM `{table_ref}` WHERE source_uri = '{input_uri}'"
    bq.query(delete_query).result()

    if rows:
        job = bq.load_table_from_json(rows, table_ref, job_config=bigquery.LoadJobConfig(schema=schema))
        job.result()
    print(f"  {len(rows)} chunks loaded")

# --- Summary ---
total = bq.query(f"SELECT COUNT(*) as n FROM `{table_ref}`").result()
print(f"\nTotal rows in {table_ref}: {list(total)[0].n}")
