# API: https://cloud.google.com/vertex-ai/generative-ai/docs/model-reference/rag-api
# https://github.com/googleapis/python-aiplatform/tree/main/vertexai/rag
# docs: https://cloud.google.com/vertex-ai/generative-ai/docs/rag-engine/rag-overview

import os, subprocess
import requests
from google.cloud import storage
from google.api_core import exceptions
import vertexai
from vertexai.preview import rag
#from vertexai import rag

# static variable definitions
LOCATION = 'us-east4' #'us-central1'
TOPICS = ['applied-genai', 'rag-engine', 'simple']

# derived variables & client setup
PROJECT_ID = subprocess.run(['gcloud', 'config', 'get-value', 'project'], capture_output=True, text=True).stdout.strip()
vertexai.init(project = PROJECT_ID, location = LOCATION)
storage_client = storage.Client(project=PROJECT_ID)

# get the pdf: MLB Rules 2025
url = "https://mktg.mlbstatic.com/mlb/official-information/2025-official-baseball-rules.pdf"


# upload the pdf to GCS to be used by the RAG engine
file_name = os.path.basename(url)
gcs_path = '/'.join(TOPICS)
gcs_uri = f'gs://{PROJECT_ID}/{gcs_path}/{file_name}'
bucket = storage_client.bucket(PROJECT_ID)
blob = bucket.blob(f'{gcs_path}/{file_name}')

if not blob.exists():
    response = requests.get(url)
    response.raise_for_status()
    blob.upload_from_string(response.content, content_type='application/pdf')


# configs: 

# parser: rag.LlmParserConfig | rag.LayoutParserConfig
parsing_config = rag.LlmParserConfig(
    model_name = f'gemini-2.5-flash',
    max_parsing_requests_per_min = 120, # default
    custom_parsing_prompt = 'Look for white space on the page and use it to set the boundary between chunks.'
)

# chunking: optional
chunking_config = rag.TransformationConfig(
    chunking_config = rag.ChunkingConfig(
        chunk_size = 1000,
        chunk_overlap = 100
    )
)

# embedding model for parsing and retrieval
embedding_config= rag.RagEmbeddingModelConfig(
    vertex_prediction_endpoint = rag.VertexPredictionEndpoint(
        publisher_model = f'publishers/google/models/text-embedding-005'
    )
)

# vector db: defaults to RagMangedDb, options for VertexVectorSearch, Pinecone, ...
#vectorDb_config = rag.VertexVectorSearch()
#vectorDb_config = rag.Pinecone()
#vectorDb_config = rag.Weaviate()
#vectorDb_config = rag.VertexFeatureStore()
vectorDb_config = rag.RagManagedDb(
    retrieval_strategy = rag.KNN(), # preview_rag.ANN()
)

# backend: the vector database choice with settings
backend_config = rag.RagVectorDbConfig(
    rag_embedding_model_config = embedding_config,
    vector_db = vectorDb_config,
)
backend_config.rag_embedding_model_config.publisher_model = f'publishers/google/models/text-embedding-005'
backend_config.rag_embedding_model_config.endpoint = None

# setup

# retrieve/create a corpus
CORPUS_NAME = '-'.join(TOPICS)

corpora = rag.list_corpora()
corpus = next((c for c in corpora if c.display_name == CORPUS_NAME), None)
if corpus is None:
    corpus = rag.create_corpus(
        display_name = CORPUS_NAME,
        description = 'Example corpus',
        backend_config = backend_config
    )


# import file(s)
import_job = rag.import_files(
    corpus_name = corpus.name,
    paths = [gcs_uri],
    transformation_config = chunking_config,
    llm_parser = parsing_config,
    max_embedding_requests_per_min = 500,
)
print(import_job)

# manage corpus
files = rag.list_files(corpus_name = corpus.name)
for f in files:
    print(f.display_name)


# Retrieval Options
query = 'What are the dimensions of second base?'






#rag.delete_corpus(corpus.name)