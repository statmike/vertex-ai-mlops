"""Batch import all chunk types from BigQuery into the combined Vector Search 2.0 collection."""

from google.cloud import bigquery, vectorsearch_v1beta
from config import (
    PROJECT_ID, REGION,
    BQ_PROJECT, BQ_DATASET, BQ_TABLE_PREFIX,
    VS_COLLECTION_COMBINED,
)

# --- Clients ---

bq = bigquery.Client(project=BQ_PROJECT)
do_client = vectorsearch_v1beta.DataObjectServiceClient()

# --- Read chunks from all three BigQuery tables ---

# Each source defines its BQ table, source_type label, and a function to extract type-specific fields
sources = [
    {
        "table": f"{BQ_TABLE_PREFIX}_reddit_chunks",
        "source_type": "reddit",
        "query": "SELECT chunk_id, text_content, source_uri, subreddit, timestamp_unix, karma, is_image_description, topics, methods_mentioned",
        "extra": lambda row: {
            "subreddit": row.subreddit,
            "timestamp_unix": row.timestamp_unix,
            "karma": row.karma,
            "is_image_description": row.is_image_description,
            "topics": list(row.topics) if row.topics else [],
            "methods_mentioned": list(row.methods_mentioned) if row.methods_mentioned else [],
        },
    },
    {
        "table": f"{BQ_TABLE_PREFIX}_zoom_chunks",
        "source_type": "zoom",
        "query": "SELECT chunk_id, text_content, source_uri, speaker_list, timestamp_start, timestamp_end, topics, action_items",
        "extra": lambda row: {
            "speaker_list": list(row.speaker_list),
            "timestamp_start": row.timestamp_start,
            "timestamp_end": row.timestamp_end,
            "topics": list(row.topics) if row.topics else [],
            "action_items": list(row.action_items) if row.action_items else [],
        },
    },
    {
        "table": f"{BQ_TABLE_PREFIX}_pdf_chunks",
        "source_type": "pdf",
        "query": "SELECT chunk_id, text_content, source_uri, page_start, page_end, topics, functions_referenced",
        "extra": lambda row: {
            "page_start": row.page_start,
            "page_end": row.page_end,
            "topics": list(row.topics) if row.topics else [],
            "functions_referenced": list(row.functions_referenced) if row.functions_referenced else [],
        },
    },
]

parent = f"projects/{PROJECT_ID}/locations/{REGION}/collections/{VS_COLLECTION_COMBINED}"

all_requests = []
seen_ids = {}  # chunk_id -> source_type of first occurrence
duplicate_warnings = []
for src in sources:
    table_ref = f"{BQ_PROJECT}.{BQ_DATASET}.{src['table']}"
    query = f"{src['query']} FROM `{table_ref}`"
    rows = list(bq.query(query).result())
    for row in rows:
        if row.chunk_id in seen_ids:
            duplicate_warnings.append(
                f"  WARNING: duplicate chunk_id '{row.chunk_id}' in {src['source_type']} "
                f"table (first seen in {seen_ids[row.chunk_id]})"
            )
            continue
        seen_ids[row.chunk_id] = src["source_type"]
        data = {
            "chunk_id": row.chunk_id,
            "text_content": row.text_content,
            "source_uri": row.source_uri,
            "source_type": src["source_type"],
        }
        data.update(src["extra"](row))
        all_requests.append(
            vectorsearch_v1beta.CreateDataObjectRequest(
                parent=parent,
                data_object_id=data["chunk_id"],
                data_object={"data": data, "vectors": {}},
            )
        )
    print(f"Found {len(rows)} {src['source_type']} chunks")

if duplicate_warnings:
    print(f"\nERROR: Found {len(duplicate_warnings)} duplicate chunk_ids in source tables:")
    for w in duplicate_warnings:
        print(w)
    print("Fix the source data before importing — duplicates indicate a bug in the parse scripts.")
    exit(1)

print(f"Total: {len(all_requests)} unique chunks to import")

# --- Batch import (max 1000 per batch) ---

BATCH_SIZE = 1000
sent = 0

for i in range(0, len(all_requests), BATCH_SIZE):
    batch = all_requests[i : i + BATCH_SIZE]
    batch_num = i // BATCH_SIZE + 1
    print(f"\nBatch {batch_num}: sending {len(batch)} DataObjects...")

    do_client.batch_create_data_objects(
        vectorsearch_v1beta.BatchCreateDataObjectsRequest(
            parent=parent,
            requests=batch,
        )
    )
    sent += len(batch)
    print(f"  Sent: {len(batch)} DataObjects")

print(f"\nDone: {sent} DataObjects sent via batch import")
