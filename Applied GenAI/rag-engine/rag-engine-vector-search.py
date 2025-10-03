# modification of: rag-engine-simple.py
# Using Vector Search as the Db: https://cloud.google.com/vertex-ai/generative-ai/docs/rag-engine/use-vertexai-vector-search

import os, subprocess
import requests
from google.cloud import storage
from google.cloud import aiplatform
import vertexai
from vertexai.preview import rag
#from vertexai import rag
from google import genai

# static variable definitions
LOCATION = 'us-east4' #'us-central1'
TOPICS = ['applied-genai', 'rag-engine', 'vertex-vector-search']

# derived variables & client setup
PROJECT_ID = subprocess.run(['gcloud', 'config', 'get-value', 'project'], capture_output=True, text=True).stdout.strip()
aiplatform.init(project=PROJECT_ID, location=LOCATION)
vertexai.init(project = PROJECT_ID, location = LOCATION)
storage_client = storage.Client(project=PROJECT_ID)
genai_client = genai.Client(vertexai = True, project = PROJECT_ID, location = LOCATION)

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

# Setup Vertex AI Vector Search: Index, Endpoint, Deploy (Index > Endpoint)

# create vertex vector search streaming index - empty index to start
INDEX_NAME = '-'.join(TOPICS + ['streaming-index'])
indexes = aiplatform.MatchingEngineIndex.list(filter=f'display_name="{INDEX_NAME}"')
if indexes:
    vvs_index = indexes[0]
    print(f'Found existing index with name {vvs_index.display_name}')
else:
    print('Not Found. Creating Index ...')
    vvs_index = aiplatform.MatchingEngineIndex.create_brute_force_index(
        display_name = INDEX_NAME,
        dimensions = 768,
        distance_measure_type = 'DOT_PRODUCT_DISTANCE',
        index_update_method = 'STREAM_UPDATE',
    )
    print(f'Index Created with name {vvs_index.display_name}')
    
# create vertex vector search endpoint
ENDPOINT_NAME = '-'.join(TOPICS + ['endpoint'])
endpoints = aiplatform.MatchingEngineIndexEndpoint.list(filter=f'display_name="{ENDPOINT_NAME}"')
if endpoints:
    vvs_endpoint = aiplatform.MatchingEngineIndexEndpoint(endpoints[0].resource_name)
    print(f"Found existing endpoint: {vvs_endpoint.display_name}")
else:
    print('Not Found. Creating endpoint...')
    vvs_endpoint = aiplatform.MatchingEngineIndexEndpoint.create(
        display_name = ENDPOINT_NAME,
        public_endpoint_enabled = True
    )
    print(f"Endpoint created: {vvs_endpoint.display_name}")


# deploy index to endpoint - this takes awhile!
if vvs_index and vvs_endpoint:
    deployed_index_id = vvs_index.display_name.replace('-', '_')

    if deployed_index_id not in [i.id for i in vvs_endpoint.deployed_indexes]:
        print(f"Deploying index '{vvs_index.display_name}' to endpoint '{vvs_endpoint.display_name}'.")
        print("This can take a while...")
        
        vvs_endpoint = vvs_endpoint.deploy_index(
            index=vvs_index,
            deployed_index_id=deployed_index_id,
            min_replica_count=2,
            max_replica_count=2,
        )
        
        print("Deployment finished.")
    else:
        print(f"Index '{vvs_index.display_name}' is already deployed to endpoint '{vvs_endpoint.display_name}'.")

    print("\nDeployment Details:")
    print(f"\tIndex: {vvs_index.resource_name}")
    print(f"\tEndpoint: {vvs_endpoint.resource_name}")
    print(f"\tDeployed Index ID: {deployed_index_id}")

else:
    if not vvs_index:
        print("Index not found, skipping deployment.")
    if not vvs_endpoint:
        print("Endpoint not found, skipping deployment.")

# RAG Engine Setup

# configs: 

# parser: rag.LlmParserConfig | rag.LayoutParserConfig
# parsing_config = rag.LlmParserConfig(
#     model_name = f'gemini-2.5-flash',
#     max_parsing_requests_per_min = 120, # default
#     custom_parsing_prompt = 'Look for white space on the page and use it to set the boundary between chunks.'
# )
# https://cloud.google.com/vertex-ai/generative-ai/docs/rag-engine/layout-parser-integration
parsing_config = rag.LayoutParserConfig(
    processor_name = f"projects/{PROJECT_ID}/locations/us/processors/519de454053ea980/processorVersions/pretrained",
    max_parsing_requests_per_min = 120, # default
)

# chunking: optional
chunking_config = rag.TransformationConfig(
    chunking_config = rag.ChunkingConfig(
        chunk_size = 300, # smaller for technical documents were concepts are like compact 
        chunk_overlap = 60 # 20% of chunk size, range of 15-25 is common
    )
)

# embedding model for parsing and retrieval
embedding_config= rag.RagEmbeddingModelConfig(
    vertex_prediction_endpoint = rag.VertexPredictionEndpoint(
        publisher_model = f'publishers/google/models/text-embedding-005'
    )
)

# vector db: defaults to RagMangedDb, options for VertexVectorSearch, Pinecone, ...
#vectorDb_config = rag.Pinecone()
#vectorDb_config = rag.Weaviate()
#vectorDb_config = rag.VertexFeatureStore()
#vectorDb_config = rag.RagManagedDb(retrieval_strategy = rag.KNN(), # preview_rag.ANN())
vectorDb_config = rag.VertexVectorSearch(
    index = vvs_index.resource_name,
    index_endpoint = vvs_endpoint.resource_name
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
    #llm_parser = parsing_config,
    layout_parser = parsing_config,
    max_embedding_requests_per_min = 500,
)
print(import_job)

# manage corpus
files = rag.list_files(corpus_name = corpus.name)
for f in files:
    print(f.display_name)


# Retrieval Options
query = "How big is second?"


# Context Retrieval - Chunks
matches = rag.retrieval_query(
    rag_resources = [
        rag.RagResource(rag_corpus = corpus.name)
    ],
    text = query
).contexts.contexts
print(len(matches), matches[0].distance, matches[-1].distance)
# defaults to k=10, distance: higher is better, lower is worse

matches = rag.retrieval_query(
    rag_resources = [
        rag.RagResource(rag_corpus = corpus.name)
    ],
    text = query,
    rag_retrieval_config = rag.RagRetrievalConfig(
        top_k = 20,  # Optional
    )
).contexts.contexts
print(len(matches), matches[0].distance, matches[-1].distance)
# while 20 are requested and returned

matches = rag.retrieval_query(
    rag_resources = [
        rag.RagResource(rag_corpus = corpus.name)
    ],
    text = query,
    rag_retrieval_config = rag.RagRetrievalConfig(
        top_k = 20,  # Optional
        filter = rag.Filter(vector_distance_threshold = 0)
    )
).contexts.contexts
print(len(matches), matches[0].distance, matches[-1].distance)
print(matches[0].text)
# set a lower threshold of 0 to prevent any filtering

try:
    matches = rag.retrieval_query(
        rag_resources = [
            rag.RagResource(rag_corpus = corpus.name)
        ],
        text = query,
        rag_retrieval_config = rag.RagRetrievalConfig(
            top_k = 200,  # Optional
            filter = rag.Filter(vector_distance_threshold = 1)
        )
    ).contexts.contexts
    print(len(matches), matches[0].distance, matches[-1].distance)
    # top_k max is 100 so asking for more returns an error
except Exception as e:
    print(e)


matches = rag.retrieval_query(
    rag_resources = [
        rag.RagResource(rag_corpus = corpus.name)
    ],
    text = query,
    rag_retrieval_config = rag.RagRetrievalConfig(
        top_k = 20,  # Optional
        filter = rag.Filter(vector_distance_threshold = 1),
        hybrid_search = rag.HybridSearch(alpha = 0) # [0, 1], [all sparse, all dense] - ONLY WORKS WITH WEAVIATE
    )
).contexts.contexts
print(len(matches))#, matches[0].distance, matches[-1].distance)
# tying hybrid search out of the box - nothing returned



# directly query the endpoint using Vertex AI Vector Search SDK
query_embedding = (
    genai_client.models.embed_content(
        model = 'text-embedding-005',
        contents = [query]
    )
).embeddings[0].values

matches = vvs_endpoint.find_neighbors(
    deployed_index_id = deployed_index_id,
    num_neighbors = 20,
    #embedding_ids = [''],
    queries = [query_embedding],
    return_full_datapoint = True # chunk text is in the restricts!
)[0]
print(len(matches), matches[0].distance, matches[-1].distance)
matches[0]

# Re-Ranked Context Retrieval - Chunks
matches = rag.retrieval_query(
    rag_resources = [
        rag.RagResource(rag_corpus = corpus.name)
    ],
    text = query,
    rag_retrieval_config = rag.RagRetrievalConfig(
        top_k = 20,  # Optional
        filter = rag.Filter(vector_distance_threshold = 0),
        ranking = rag.Ranking(
            rank_service = rag.RankService(
                model_name = 'semantic-ranker-default@latest'
            )
        )
    )
).contexts.contexts
print(len(matches), matches[0].distance, matches[-1].distance)
print(matches[0].text)

# Response With Context Retrieval
rag_tool = vertexai.generative_models.Tool.from_retrieval(
    retrieval = rag.Retrieval(
        source = rag.VertexRagStore(
            rag_resources = [
                rag.RagResource(rag_corpus = corpus.name)
            ],
            rag_retrieval_config = rag.RagRetrievalConfig(
                top_k = 20,  # Optional
                filter = rag.Filter(vector_distance_threshold = 0),
            )
        )
    )
)

response = vertexai.generative_models.GenerativeModel(
    model_name = 'gemini-2.5-flash',
    tools = [rag_tool]
).generate_content(query)
print(response.text)



# Response With Re-Ranked Context Retrieval
rag_tool = vertexai.generative_models.Tool.from_retrieval(
    retrieval = rag.Retrieval(
        source = rag.VertexRagStore(
            rag_resources = [
                rag.RagResource(rag_corpus = corpus.name)
            ],
            rag_retrieval_config = rag.RagRetrievalConfig(
                top_k = 20,  # Optional
                filter = rag.Filter(vector_distance_threshold = 0),
                ranking = rag.Ranking(
                    rank_service = rag.RankService(
                        model_name = 'semantic-ranker-default@latest'
                    )
                )
            )
        )
    )
)

response = vertexai.generative_models.GenerativeModel(
    model_name = 'gemini-2.5-flash',
    tools = [rag_tool]
).generate_content(query)
print(response.text)


# Response With Re-Ranked Context Retrieval (LLM as Reranker)
rag_tool = vertexai.generative_models.Tool.from_retrieval(
    retrieval = rag.Retrieval(
        source = rag.VertexRagStore(
            rag_resources = [
                rag.RagResource(rag_corpus = corpus.name)
            ],
            rag_retrieval_config = rag.RagRetrievalConfig(
                top_k = 20,  # Optional
                filter = rag.Filter(vector_distance_threshold = 0),
                ranking = rag.Ranking(
                    llm_ranker = rag.LlmRanker(
                        model_name = 'gemini-2.5-flash'
                    )
                )
            )
        )
    )
)

response = vertexai.generative_models.GenerativeModel(
    model_name = 'gemini-2.5-flash',
    tools = [rag_tool]
).generate_content(query)
print(response.text)

# try to import the file(s) again without any changes:
import_job = rag.import_files(
    corpus_name = corpus.name,
    paths = [gcs_uri],
    transformation_config = chunking_config,
    layout_parser = parsing_config,
    max_embedding_requests_per_min = 500,
)
print(import_job)



#rag.delete_corpus(corpus.name)