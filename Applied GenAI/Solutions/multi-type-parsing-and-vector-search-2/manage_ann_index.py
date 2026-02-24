"""ANN index management for the combined collection.

Step 10: Check collection size, create an ANN index when the threshold is
reached, or delete an existing index. Once an ANN index exists, VS2
automatically uses it for queries (no code changes needed). kNN can still be
forced via SearchHint(use_knn=True) for recall comparison.

Usage:
    uv run python manage_ann_index.py            # check size, create if >= threshold
    uv run python manage_ann_index.py --delete    # delete the ANN index
"""

import argparse

from google.api_core import exceptions as api_exceptions
from google.cloud import vectorsearch_v1beta
from config import (
    PROJECT_ID, REGION,
    VS_COLLECTION_COMBINED,
    ANN_INDEX_THRESHOLD, ANN_INDEX_ID, ANN_DISTANCE_METRIC,
)

# --- Clients ---

vs_client = vectorsearch_v1beta.VectorSearchServiceClient()
search_client = vectorsearch_v1beta.DataObjectSearchServiceClient()

collection_name = f"projects/{PROJECT_ID}/locations/{REGION}/collections/{VS_COLLECTION_COMBINED}"

# --- Args ---

parser = argparse.ArgumentParser(description="Manage ANN index on the combined collection.")
parser.add_argument('--delete', action='store_true', help='Delete the ANN index')
args = parser.parse_args()


# =============================================================================
# Delete mode
# =============================================================================

if args.delete:
    print("=" * 60)
    print("Deleting ANN index")
    print("=" * 60)

    index_name = f"{collection_name}/indexes/{ANN_INDEX_ID}"
    try:
        operation = vs_client.delete_index(name=index_name)
        operation.result()
        print(f"  Deleted: {ANN_INDEX_ID}")
    except api_exceptions.NotFound:
        print(f"  No index found with ID '{ANN_INDEX_ID}' — nothing to delete.")
    exit(0)


# =============================================================================
# 1. Count DataObjects in combined collection
# =============================================================================

print("=" * 60)
print("1. Counting DataObjects in combined collection")
print("=" * 60)

count_response = search_client.aggregate_data_objects(
    vectorsearch_v1beta.AggregateDataObjectsRequest(
        parent=collection_name,
        aggregate='COUNT',
    )
)
data_object_count = int(count_response.aggregate_results[0]["count"])
print(f"  Collection: {VS_COLLECTION_COMBINED}")
print(f"  DataObjects: {data_object_count}")


# =============================================================================
# 2. Check if index already exists
# =============================================================================

print("\n" + "=" * 60)
print("2. Checking for existing ANN indexes")
print("=" * 60)

indexes = list(vs_client.list_indexes(parent=collection_name))

existing_index = None
for idx in indexes:
    # Index name format: .../indexes/{index_id}
    idx_id = idx.name.split("/indexes/")[-1] if "/indexes/" in idx.name else idx.name
    print(f"  Found index: {idx_id}")
    print(f"    Field: {idx.index_field}")
    print(f"    Distance metric: {idx.distance_metric}")
    print(f"    Display name: {idx.display_name}")
    if idx_id == ANN_INDEX_ID:
        existing_index = idx

if not indexes:
    print("  No indexes found.")


# =============================================================================
# 3. If exists -> print status and exit
# =============================================================================

if existing_index:
    print("\n" + "=" * 60)
    print(f"ANN index '{ANN_INDEX_ID}' already exists.")
    print("=" * 60)
    print(f"  Field: {existing_index.index_field}")
    print(f"  Distance metric: {existing_index.distance_metric}")
    print(f"  Filter fields: {list(existing_index.filter_fields)}")
    print(f"  Store fields: {list(existing_index.store_fields)}")
    print(f"  Display name: {existing_index.display_name}")
    print(f"\n  Queries automatically use this index.")
    print(f"  To force kNN: search_hint=SearchHint(use_knn=True)")
    print(f"  To delete:    uv run python manage_ann_index.py --delete")
    exit(0)


# =============================================================================
# 4. If count < threshold -> exit
# =============================================================================

if data_object_count < ANN_INDEX_THRESHOLD:
    print("\n" + "=" * 60)
    print(f"Not enough DataObjects ({data_object_count} < {ANN_INDEX_THRESHOLD})")
    print("=" * 60)
    print(f"  ANN index creation skipped.")
    print(f"  Threshold: {ANN_INDEX_THRESHOLD} (set ANN_INDEX_THRESHOLD in config.py)")
    print(f"  Current brute-force kNN works well at this scale.")
    exit(0)


# =============================================================================
# 5. Create ANN index
# =============================================================================

print("\n" + "=" * 60)
print("5. Creating ANN index")
print("=" * 60)

distance_metric = getattr(vectorsearch_v1beta.DistanceMetric, ANN_DISTANCE_METRIC)

index = vectorsearch_v1beta.Index(
    index_field="text_content_embedding",
    distance_metric=distance_metric,
    filter_fields=["source_type"],
    store_fields=["chunk_id", "text_content", "source_type", "source_uri"],
    display_name="Dense embedding ANN index",
)

print(f"  Index ID: {ANN_INDEX_ID}")
print(f"  Field: {index.index_field}")
print(f"  Distance metric: {ANN_DISTANCE_METRIC}")
print(f"  Filter fields: {list(index.filter_fields)}")
print(f"  Store fields: {list(index.store_fields)}")
print(f"  Building index (this may take a while)...")

operation = vs_client.create_index(
    parent=collection_name,
    index_id=ANN_INDEX_ID,
    index=index,
)
result = operation.result()


# =============================================================================
# 6. Print index details
# =============================================================================

print("\n" + "=" * 60)
print("ANN index created successfully!")
print("=" * 60)
print(f"  Name: {result.name}")
print(f"  Field: {result.index_field}")
print(f"  Distance metric: {result.distance_metric}")
print(f"  Filter fields: {list(result.filter_fields)}")
print(f"  Store fields: {list(result.store_fields)}")
print(f"  Display name: {result.display_name}")
print(f"\n  Queries now automatically use this ANN index.")
print(f"  To force kNN: search_hint=SearchHint(use_knn=True)")
print(f"  To delete:    uv run python manage_ann_index.py --delete")
