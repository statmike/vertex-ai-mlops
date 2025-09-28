# API: https://cloud.google.com/vertex-ai/generative-ai/docs/model-reference/rag-api
# https://github.com/googleapis/python-aiplatform/tree/main/vertexai/rag
# docs: https://cloud.google.com/vertex-ai/generative-ai/docs/rag-engine/rag-overview

import subprocess
import vertexai
from vertexai import rag
from vertexai.preview import rag as preview_rag

# static variable definitions
LOCATION = 'us-central1'
TOPICS = ['applied-genai', 'rag-engine', 'simple']

# derived variables & client setup
PROJECT_ID = subprocess.run(['gcloud', 'config', 'get-value', 'project'], capture_output=True, text=True).stdout.strip()
vertexai.init(project = PROJECT_ID, location = LOCATION)


# get the pdf: MLB Rules 2025
url = "https://mktg.mlbstatic.com/mlb/official-information/2025-official-baseball-rules.pdf"


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
        publisher_model = 'publishers/google/models/gemini-embedding-001'
    )
)

# vector db: defaults to RagMangedDb, options for VertexVectorSearch, Pinecone, ...
#vectorDb_config = rag.VertexVectorSearch()
#vectorDb_config = rag.Pinecone()
#vectorDb_config = preview_rag.Weaviate()
#vectorDb_config = preview_rag.VertexFeatureStore()
vectorDb_config = rag.RagManagedDb(
    retrieval_strategy = preview_rag.KNN(), # preview_rag.ANN()
)

# backend: the vector database choice with settings
backend_config = rag.RagVectorDbConfig(
    rag_embedding_model_config = embedding_config,
    vector_db = vectorDb_config,
)

# setup

# retrieve/create a corpus
corpus = rag.create_corpus(
    display_name = '-'.join(TOPICS),
    backend_config = 
)


