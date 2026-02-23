"""Import Reddit chunks from BigQuery into Vector Search 2.0 collection."""

from google.cloud import bigquery, vectorsearch_v1beta
from google.api_core.exceptions import AlreadyExists
from config import (
    PROJECT_ID, REGION,
    BQ_PROJECT, BQ_DATASET, BQ_TABLE_PREFIX,
    VS_COLLECTION_REDDIT,
)

# --- Clients ---

bq = bigquery.Client(project=BQ_PROJECT)
do_client = vectorsearch_v1beta.DataObjectServiceClient()

# --- Read chunks from BigQuery ---

table_ref = f"{BQ_PROJECT}.{BQ_DATASET}.{BQ_TABLE_PREFIX}_reddit_chunks"
query = f"SELECT chunk_id, text_content, source_uri, subreddit, timestamp_unix, karma, is_image_description, topics, methods_mentioned FROM `{table_ref}`"
rows = list(bq.query(query).result())
print(f"Found {len(rows)} Reddit chunks in BigQuery")

# --- Check for duplicate chunk_ids in source data ---

from collections import Counter
chunk_id_counts = Counter(row.chunk_id for row in rows)
duplicates = {cid: cnt for cid, cnt in chunk_id_counts.items() if cnt > 1}
if duplicates:
    print(f"\nERROR: Found {len(duplicates)} duplicate chunk_ids in source table:")
    for cid, cnt in duplicates.items():
        print(f"  {cid}: {cnt} copies")
    print("Fix the source data before importing — duplicates indicate a bug in the parse script.")
    exit(1)

# --- Import each chunk as a DataObject ---

parent = f"projects/{PROJECT_ID}/locations/{REGION}/collections/{VS_COLLECTION_REDDIT}"
created = 0
skipped = 0

for row in rows:
    data = {
        "chunk_id": row.chunk_id,
        "text_content": row.text_content,
        "source_uri": row.source_uri,
        "subreddit": row.subreddit,
        "timestamp_unix": row.timestamp_unix,
        "karma": row.karma,
        "is_image_description": row.is_image_description,
        "topics": list(row.topics) if row.topics else [],
        "methods_mentioned": list(row.methods_mentioned) if row.methods_mentioned else [],
    }

    request = vectorsearch_v1beta.CreateDataObjectRequest(
        parent=parent,
        data_object_id=row.chunk_id,
        data_object={"data": data, "vectors": {}},
    )

    try:
        do_client.create_data_object(request=request)
        created += 1
        print(f"  Created: {row.chunk_id}")
    except AlreadyExists:
        skipped += 1
        print(f"  Skipped (exists): {row.chunk_id}")

print(f"\nDone: {created} created, {skipped} skipped")
