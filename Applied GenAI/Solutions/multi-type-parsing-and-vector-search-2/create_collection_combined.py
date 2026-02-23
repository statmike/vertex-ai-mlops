"""Create Vector Search 2.0 collection for combined cross-type search."""

from google.cloud import vectorsearch_v1beta
from google.api_core.exceptions import AlreadyExists
from config import PROJECT_ID, REGION, EMBEDDING_MODEL, VS_COLLECTION_COMBINED

# --- Client ---

vs_client = vectorsearch_v1beta.VectorSearchServiceClient()

# --- Collection schema ---

# Union of all metadata fields across all data types plus a source_type discriminator.
# Fields not relevant to a given source type are left empty/null at import time.
data_schema = {
    "type": "object",
    "properties": {
        # Common fields (all types)
        "chunk_id": {"type": "string"},
        "text_content": {"type": "string"},
        "source_uri": {"type": "string"},
        "source_type": {"type": "string"},  # "reddit", "zoom", or "pdf"
        # Reddit fields
        "subreddit": {"type": "string"},
        "timestamp_unix": {"type": "number"},
        "karma": {"type": "number"},
        "is_image_description": {"type": "boolean"},
        # Zoom fields
        "speaker_list": {"type": "array", "items": {"type": "string"}},
        "timestamp_start": {"type": "number"},
        "timestamp_end": {"type": "number"},
        # PDF fields
        "page_start": {"type": "number"},
        "page_end": {"type": "number"},
        # Enrichment fields (step 4 — all types)
        "topics": {"type": "array", "items": {"type": "string"}},
        # Reddit enrichment
        "methods_mentioned": {"type": "array", "items": {"type": "string"}},
        # Zoom enrichment
        "action_items": {"type": "array", "items": {"type": "string"}},
        # PDF enrichment
        "functions_referenced": {"type": "array", "items": {"type": "string"}},
    },
}

# Auto-embed text_content using the configured embedding model.
# task_type="RETRIEVAL_DOCUMENT" tells the model this text is reference material being indexed.
# At query time, use the asymmetric counterpart (e.g. QUESTION_ANSWERING or RETRIEVAL_QUERY).
# See: https://cloud.google.com/vertex-ai/generative-ai/docs/embeddings/task-types
vector_schema = {
    "text_content_embedding": {
        "dense_vector": {
            "dimensions": 768,
            "vertex_embedding_config": {
                "model_id": EMBEDDING_MODEL,
                "text_template": "{text_content}",
                "task_type": "RETRIEVAL_DOCUMENT",
            },
        },
    },
}

# --- Create collection ---

print(f"Creating collection: {VS_COLLECTION_COMBINED}")

request = vectorsearch_v1beta.CreateCollectionRequest(
    parent=f"projects/{PROJECT_ID}/locations/{REGION}",
    collection_id=VS_COLLECTION_COMBINED,
    collection={
        "data_schema": data_schema,
        "vector_schema": vector_schema,
    },
)

try:
    operation = vs_client.create_collection(request=request)
    print("Waiting for collection creation...")
    result = operation.result()
    print(f"Created: {result.name}")
except AlreadyExists:
    print(f"Collection already exists: {VS_COLLECTION_COMBINED}")

# --- Verify ---

get_request = vectorsearch_v1beta.GetCollectionRequest(
    name=f"projects/{PROJECT_ID}/locations/{REGION}/collections/{VS_COLLECTION_COMBINED}"
)
collection = vs_client.get_collection(get_request)
print(f"\nCollection: {collection.name}")
