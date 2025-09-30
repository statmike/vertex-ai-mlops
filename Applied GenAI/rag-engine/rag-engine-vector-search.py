# modification of: rag-engine-simple.py
# Using Vector Search as the Db: https://cloud.google.com/vertex-ai/generative-ai/docs/rag-engine/use-vertexai-vector-search

import os, subprocess
import requests
from google.cloud import storage
from google.cloud import aiplatform
import vertexai
from vertexai.preview import rag
#from vertexai import rag
#from google import genai

# static variable definitions
LOCATION = 'us-east4' #'us-central1'
TOPICS = ['applied-genai', 'rag-engine', 'vertex-vector-search']

# derived variables & client setup
PROJECT_ID = subprocess.run(['gcloud', 'config', 'get-value', 'project'], capture_output=True, text=True).stdout.strip()
aiplatform.init(project=PROJECT_ID, location=LOCATION)
vertexai.init(project = PROJECT_ID, location = LOCATION)
storage_client = storage.Client(project=PROJECT_ID)
#genai_client = genai.Client(vertexai = True, project = PROJECT_ID, location = LOCATION)

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
    vvs_endpoint = endpoints[0]
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



