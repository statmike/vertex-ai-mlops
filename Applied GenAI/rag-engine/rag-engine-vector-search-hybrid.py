# build on the vector search index created by rag-engine-vector-search.py

import os, subprocess
import requests
from google.cloud import storage
from google.cloud import aiplatform
import vertexai
from vertexai.preview import rag
#from vertexai import rag
import pandas as pd
from google import genai
from sklearn.feature_extraction.text import TfidfVectorizer

# static variable definitions
LOCATION = 'us-east4' #'us-central1'
TOPICS = ['applied-genai', 'rag-engine', 'vertex-vector-search']

# derived variables & client setup
PROJECT_ID = subprocess.run(['gcloud', 'config', 'get-value', 'project'], capture_output=True, text=True).stdout.strip()
aiplatform.init(project=PROJECT_ID, location=LOCATION)
vertexai.init(project = PROJECT_ID, location = LOCATION)
storage_client = storage.Client(project=PROJECT_ID)
genai_client = genai.Client(vertexai = True, project = PROJECT_ID, location = LOCATION)

# Vertex Vector Search

# retrieve vertex vector search streaming index 
INDEX_NAME = '-'.join(TOPICS + ['streaming-index'])
indexes = aiplatform.MatchingEngineIndex.list(filter=f'display_name="{INDEX_NAME}"')
vvs_index = None
if indexes:
    vvs_index = indexes[0]
    print(f'Found existing index with name {vvs_index.display_name}')
else:
    print(f'Warning: Index "{INDEX_NAME}" not found. Please create it first using rag-engine-vector-search.py.')
    
# retrieve vertex vector search endpoint
ENDPOINT_NAME = '-'.join(TOPICS + ['endpoint'])
endpoints = aiplatform.MatchingEngineIndexEndpoint.list(filter=f'display_name="{ENDPOINT_NAME}"')
vvs_endpoint = None
if endpoints:
    vvs_endpoint = aiplatform.MatchingEngineIndexEndpoint(endpoints[0].resource_name)
    print(f"Found existing endpoint: {vvs_endpoint.display_name}")
else:
    print(f'Warning: Endpoint "{ENDPOINT_NAME}" not found. Please create it first using rag-engine-vector-search.py.')


# Get deployed index
deployed_index_id = None
is_deployed = False
if vvs_index and vvs_endpoint:
    deployed_index_id = vvs_index.display_name.replace('-', '_')

    if deployed_index_id in [i.id for i in vvs_endpoint.deployed_indexes]:
        is_deployed = True
        print(f"Index '{vvs_index.display_name}' is already deployed to endpoint '{vvs_endpoint.display_name}'.")
        print("\nDeployment Details:")
        print(f"\tIndex: {vvs_index.resource_name}")
        print(f"\tEndpoint: {vvs_endpoint.resource_name}")
        print(f"\tDeployed Index ID: {deployed_index_id}")
    else:
        print(f"Warning: Index '{vvs_index.display_name}' is not deployed to endpoint '{vvs_endpoint.display_name}'. Please deploy it first using rag-engine-vector-search.py.")

else:
    if not vvs_index:
        print("Index not found, skipping deployment check.")
    if not vvs_endpoint:
        print("Endpoint not found, skipping deployment check.")

# RAG Engine: retrieve/create a corpus
CORPUS_NAME = '-'.join(TOPICS)

corpora = rag.list_corpora()
corpus = next((c for c in corpora if c.display_name == CORPUS_NAME), None)
if corpus:
    print(f"Found existing corpus: {corpus.display_name}")
else:
    print(f'Warning: Corpus "{CORPUS_NAME}" not found. Please create it first using rag-engine-vector-search.py.')

# Retrieval Options
query = 'How big is second?'


# Context Retrieval - Chunks
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




# Retrieve all the text chunk with ids from the index:
print(f'The index size is currently: {vvs_index.gca_resource.index_stats}')

# get full index:
index_data = vvs_endpoint.find_neighbors(
    deployed_index_id = deployed_index_id,
    num_neighbors = vvs_index.gca_resource.index_stats.vectors_count,
    queries = [query_embedding],
    return_full_datapoint = True # chunk text is in the restricts!
)[0]
print(f'Retrieved {len(index_data)} chunks from the index.')

# extract chunk data and id to dataframe:
chunk_data = [{
    'id': n.id,
    'chunk_text': next((r.allow_tokens[0] for r in n.restricts if r.name == 'chunk_data'), None)
    } for n in index_data]
print(chunk_data[:5])

# create tf-idf vectorizer
vectorizer = TfidfVectorizer()
vectorizer.fit_transform([d['chunk_text'] for d in chunk_data if d['chunk_text']])

# embedder function: sparse and dense
def embedder(query):
    dense = genai_client.models.embed_content(
        model = 'text-embedding-005',
        contents = [query]
    ).embeddings[0].values
    tfidf_vector = vectorizer.transform([query])
    sparse = dict(
        values = [float(tfidf_value) for tfidf_value in tfidf_vector.data],
        dimensions = [int(tfidf_vector.indices[i]) for i, tfidf_value in enumerate(tfidf_vector.data)]
    )
    return dict(dense = dense, sparse = sparse)

# example                
embedder(query)

# Get the ID and text for the first chunk
datapoint_id = chunk_data[0]['id']
chunk_text = chunk_data[0]['chunk_text']

if datapoint_id and chunk_text:
    # 1. Read the full datapoint
    print("Reading datapoint to update...")
    before_upsert = vvs_endpoint.read_index_datapoints(
        deployed_index_id = deployed_index_id,
        ids = [datapoint_id]
    )
    
    if before_upsert:
        mod_upsert = before_upsert[0]
        print("Datapoint before update:", mod_upsert)

        # 2. Modify it by adding the sparse embedding
        embedding = embedder(chunk_text)
        
        # Convert to dict to safely modify
        mod_upsert_dict = type(mod_upsert).to_dict(mod_upsert)
        mod_upsert_dict['sparse_embedding'] = embedding['sparse']

        # 3. Upsert the modified full datapoint
        print("\nUpserting datapoint with sparse embedding...")
        vvs_index.upsert_datapoints(datapoints = [mod_upsert_dict])#, update_mask = [])
        print("Upsert complete.")


        # 4. Retrieve again to verify the change
        print("\nRetrieving datapoint after upsert to verify...")
        after_upsert = vvs_endpoint.read_index_datapoints(
            deployed_index_id = deployed_index_id,
            ids = [datapoint_id]
        )
        if after_upsert:
            print("Datapoint after update:", after_upsert[0])
        else:
            print("Could not retrieve datapoint after upsert.")
    else:
        print(f"Could not read datapoint with ID: {datapoint_id}")







# now upsert all entries with sparse embeddings
print("Reading all datapoints to add sparse embeddings...")
all_datapoint_ids = [c['id'] for c in chunk_data if c['id']]
existing_datapoints = vvs_endpoint.read_index_datapoints(
    deployed_index_id = deployed_index_id,
    ids = all_datapoint_ids
)
print(f"Read {len(existing_datapoints)} datapoints.")

# Create a map of ID to chunk_text for easier lookup
id_to_text_map = {c['id']: c['chunk_text'] for c in chunk_data if c['id']}

print("Preparing datapoints for upsert with sparse embeddings...")
datapoints_to_upsert = []
for dp in existing_datapoints:
    dp_dict = type(dp).to_dict(dp)
    chunk_text = id_to_text_map.get(dp.datapoint_id)
    if chunk_text:
        embedding = embedder(chunk_text)
        dp_dict['sparse_embedding'] = embedding['sparse']
    datapoints_to_upsert.append(dp_dict)

# make the upserts
print(f"Upserting {len(datapoints_to_upsert)} datapoints...")
vvs_index.upsert_datapoints(datapoints_to_upsert)
print("Upsert of all datapoints with sparse embeddings is complete.")






