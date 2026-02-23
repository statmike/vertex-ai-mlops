"""Import Zoom transcript chunks from BigQuery into Vector Search 2.0 collection."""

from google.cloud import bigquery, vectorsearch_v1beta
from google.api_core.exceptions import AlreadyExists
from config import (
    PROJECT_ID, REGION,
    BQ_PROJECT, BQ_DATASET, BQ_TABLE_PREFIX,
    VS_COLLECTION_ZOOM,
)

# --- Clients ---

bq = bigquery.Client(project=BQ_PROJECT)
do_client = vectorsearch_v1beta.DataObjectServiceClient()

# --- Read chunks from BigQuery ---

table_ref = f"{BQ_PROJECT}.{BQ_DATASET}.{BQ_TABLE_PREFIX}_zoom_chunks"
query = f"SELECT chunk_id, text_content, source_uri, speaker_list, timestamp_start, timestamp_end, topics, action_items FROM `{table_ref}`"
rows = list(bq.query(query).result())
print(f"Found {len(rows)} Zoom chunks in BigQuery")

# --- Import each chunk as a DataObject ---

parent = f"projects/{PROJECT_ID}/locations/{REGION}/collections/{VS_COLLECTION_ZOOM}"
created = 0
skipped = 0

for row in rows:
    data = {
        "chunk_id": row.chunk_id,
        "text_content": row.text_content,
        "source_uri": row.source_uri,
        "speaker_list": list(row.speaker_list),
        "timestamp_start": row.timestamp_start,
        "timestamp_end": row.timestamp_end,
        "topics": list(row.topics) if row.topics else [],
        "action_items": list(row.action_items) if row.action_items else [],
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
