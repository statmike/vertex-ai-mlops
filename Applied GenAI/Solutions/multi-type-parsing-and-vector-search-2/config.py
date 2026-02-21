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
EMBEDDING_MODEL = "gemini-embedding-001"
