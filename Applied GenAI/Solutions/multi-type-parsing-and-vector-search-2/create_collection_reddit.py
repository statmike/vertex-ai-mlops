"""Create Vector Search 2.0 collection for Reddit thread chunks."""

from google.cloud import vectorsearch_v1beta
from google.api_core.exceptions import AlreadyExists
from config import PROJECT_ID, REGION, EMBEDDING_MODEL, VS_COLLECTION_REDDIT

# --- Client ---

vs_client = vectorsearch_v1beta.VectorSearchServiceClient()

# --- Collection schema ---

# Data schema mirrors the BQ reddit_chunks table (minus processed_at)
data_schema = {
    "type": "object",
    "properties": {
        "chunk_id": {"type": "string"},
        "text_content": {"type": "string"},
        "source_uri": {"type": "string"},
        "subreddit": {"type": "string"},
        "timestamp_unix": {"type": "number"},
        "karma": {"type": "number"},
        "is_image_description": {"type": "boolean"},
        # Enrichment fields (step 4)
        "topics": {"type": "array", "items": {"type": "string"}},
        "methods_mentioned": {"type": "array", "items": {"type": "string"}},
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

print(f"Creating collection: {VS_COLLECTION_REDDIT}")

request = vectorsearch_v1beta.CreateCollectionRequest(
    parent=f"projects/{PROJECT_ID}/locations/{REGION}",
    collection_id=VS_COLLECTION_REDDIT,
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
    print(f"Collection already exists: {VS_COLLECTION_REDDIT}")

# --- Verify ---

get_request = vectorsearch_v1beta.GetCollectionRequest(
    name=f"projects/{PROJECT_ID}/locations/{REGION}/collections/{VS_COLLECTION_REDDIT}"
)
collection = vs_client.get_collection(get_request)
print(f"\nCollection: {collection.name}")
