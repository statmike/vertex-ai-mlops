"""Centralized project configuration. Update these values for your environment."""

import google.auth

# --- Google Cloud ---

_, PROJECT_ID = google.auth.default()
REGION = "us-central1"


# --- NAMES ---
PARTS = [
    'applied-genai-solutions',
    'multi-type-parsing'
]

# --- BigQuery ---

BQ_PROJECT = PROJECT_ID
BQ_DATASET = PARTS[0].replace('-', '_')
BQ_TABLE_PREFIX = PARTS[1].replace('-', '_')
BQ_CONNECTION = '-'.join(PARTS)
BQ_LOCATION = "US"

# --- Google Cloud Storage ---

GCS_BUCKET = PROJECT_ID
GCS_ROOT = '/'.join(PARTS[0:2])

# --- Document AI ---

DOCAI_LOCATION = "us"
DOCAI_PROCESSOR_DISPLAY_NAME = '-'.join(PARTS) + '-layout-parser'
DOCAI_PROCESSOR_TYPE = "LAYOUT_PARSER_PROCESSOR"
DOCAI_PROCESSOR_VERSION = "pretrained-layout-parser-v1.5-pro-2025-08-25"

# --- Vertex AI Vector Search 2.0 ---

VS_COLLECTION_REDDIT = '-'.join(PARTS) + '-reddit'
VS_COLLECTION_ZOOM = '-'.join(PARTS) + '-zoom'
VS_COLLECTION_PDF = '-'.join(PARTS) + '-pdf'
VS_COLLECTION_COMBINED = '-'.join(PARTS) + '-combined'

# --- Gemini ---

GEMINI_MODEL = "gemini-2.5-pro"
FAST_GEMINI_MODEL = "gemini-2.5-flash"
EMBEDDING_MODEL = "gemini-embedding-001"
EMBEDDING_DIMENSIONS = 768  # must match dimensions in collection vector_schema

# --- BM25 ---

BM25_K1 = 1.2          # term frequency saturation
BM25_B = 0.6           # document length normalization
BM25_EPSILON = 0.25    # IDF smoothing floor
BM25_NGRAMS = 2        # unigrams + bigrams
BM25_MODEL_VERSION = 1 # increment on retrain

# BM25 maintenance thresholds (step 9)
BM25_OOV_THRESHOLD = 0.10    # 10% new terms triggers rebuild
BM25_STALE_THRESHOLD = 0.15  # 15% stale terms triggers rebuild
BM25_CORPUS_DELTA = 0.20     # 20% corpus size change triggers rebuild

# --- ANN Index (step 10) ---

ANN_INDEX_THRESHOLD = 1000          # minimum DataObjects before triggering index build
ANN_INDEX_ID = 'dense-embedding'    # index resource ID (RFC1035: lowercase, hyphens)
ANN_DISTANCE_METRIC = 'DOT_PRODUCT' # DOT_PRODUCT (default) or COSINE_DISTANCE
