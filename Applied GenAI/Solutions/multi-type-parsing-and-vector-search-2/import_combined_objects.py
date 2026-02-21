"""Import all chunk types from BigQuery into the combined Vector Search 2.0 collection."""

from google.cloud import bigquery, vectorsearch_v1beta
from google.api_core.exceptions import AlreadyExists
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
        "query": "SELECT chunk_id, text_content, source_uri, subreddit, timestamp_unix, karma, is_image_description",
        "extra": lambda row: {
            "subreddit": row.subreddit,
            "timestamp_unix": row.timestamp_unix,
            "karma": row.karma,
            "is_image_description": row.is_image_description,
        },
    },
    {
        "table": f"{BQ_TABLE_PREFIX}_zoom_chunks",
        "source_type": "zoom",
        "query": "SELECT chunk_id, text_content, source_uri, speaker_list, timestamp_start, timestamp_end",
        "extra": lambda row: {
            "speaker_list": list(row.speaker_list),
            "timestamp_start": row.timestamp_start,
            "timestamp_end": row.timestamp_end,
        },
    },
    {
        "table": f"{BQ_TABLE_PREFIX}_pdf_chunks",
        "source_type": "pdf",
        "query": "SELECT chunk_id, text_content, source_uri, page_start, page_end",
        "extra": lambda row: {
            "page_start": row.page_start,
            "page_end": row.page_end,
        },
    },
]

all_rows = []
for src in sources:
    table_ref = f"{BQ_PROJECT}.{BQ_DATASET}.{src['table']}"
    query = f"{src['query']} FROM `{table_ref}`"
    rows = list(bq.query(query).result())
    for row in rows:
        data = {
            "chunk_id": row.chunk_id,
            "text_content": row.text_content,
            "source_uri": row.source_uri,
            "source_type": src["source_type"],
        }
        data.update(src["extra"](row))
        all_rows.append(data)
    print(f"Found {len(rows)} {src['source_type']} chunks")

print(f"\nTotal: {len(all_rows)} chunks across all types")

# --- Import each chunk as a DataObject ---

parent = f"projects/{PROJECT_ID}/locations/{REGION}/collections/{VS_COLLECTION_COMBINED}"
created = 0
skipped = 0

for data in all_rows:
    request = vectorsearch_v1beta.CreateDataObjectRequest(
        parent=parent,
        data_object_id=data["chunk_id"],
        data_object={"data": data, "vectors": {}},
    )

    try:
        do_client.create_data_object(request=request)
        created += 1
        print(f"  Created: {data['chunk_id']}")
    except AlreadyExists:
        skipped += 1
        print(f"  Skipped (exists): {data['chunk_id']}")

print(f"\nDone: {created} created, {skipped} skipped")
