# imports
from google import genai
from pydantic import BaseModel, Field
from typing import List
import os
import subprocess
import pandas as pd
import json
from google.cloud import storage
from google.cloud import bigquery
from google.cloud import aiplatform
from vertexai.resources.preview import feature_store
import time
import datetime

# static variable definitions
LOCATION = 'us-central1'

# derived variables
PROJECT_ID = subprocess.run(['gcloud', 'config', 'get-value', 'project'], capture_output=True, text=True).stdout.strip()
SERIES = 'feature-store'
EXPERIMENT = 'fs-data-types'
TOPICS = ['mlops', 'feature-store', 'data-sources']

# client setup
genai_client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)
aiplatform.init(project=PROJECT_ID, location=LOCATION)

# Example Data Creation

class MLRecord(BaseModel):
    """
    Pydantic schema for a single ML data record with generic feature names.
    """
    feature_1: int = Field(..., description="Integer feature with a range of 0 to 100.", ge=0, le=100)
    feature_2: float = Field(..., description="Float feature with a range of 0.0 to 1.0.", ge=0.0, le=1.0)
    feature_3: str = Field(..., description="String feature with possible values 'a', 'b', 'c'.", enum=['a', 'b', 'c'])
    feature_4: bool = Field(..., description="Boolean feature.")

class MLData(BaseModel):
    """
    Pydantic schema for a list of MLRecord objects.
    """
    records: List[MLRecord]

# Generate data using the genai client
response = genai_client.models.generate_content(
    model='gemini-2.5-flash',
    contents = ["Generate a list of 10 records."],
    config = {
        "response_mime_type": "application/json",
        "response_schema": MLData,
    }
)

data = json.loads(response.text)['records']

# Manually assign unique entity_key
for i, record in enumerate(data):
    record['entity_key'] = f'entity-{i+1}'

# Create a Pandas DataFrame
df = pd.DataFrame(data)

print("Generated Data:\n", df)

# Store Data in GCS and BigQuery

# Convert data to JSONL format
jsonl_data = "\n".join([json.dumps(record) for record in data])

# GCS client
storage_client = storage.Client(project=PROJECT_ID)
bucket_name = PROJECT_ID
bucket = storage_client.bucket(bucket_name)

if not bucket.exists():
    print(f"Bucket {bucket_name} does not exist. Creating bucket.")
    storage_client.create_bucket(bucket_name, location=LOCATION)

blob_path = f"{SERIES}/{EXPERIMENT}/data.jsonl"
blob = bucket.blob(blob_path)
blob.upload_from_string(jsonl_data)

gcs_uri = f"gs://{bucket_name}/{blob_path}"
print(f"Data uploaded to {gcs_uri}")

# BigQuery client
bq_client = bigquery.Client(project=PROJECT_ID)

# Create dataset if it doesn't exist
dataset_name = "-".join(TOPICS[0:2]).replace('-', '_')
dataset_id = f"{PROJECT_ID}.{dataset_name}"
dataset = bigquery.Dataset(dataset_id)
dataset.location = LOCATION
try:
    bq_client.get_dataset(dataset_id)
    print(f"Dataset {dataset_name} already exists.")
except Exception:
    bq_client.create_dataset(dataset, timeout=30)
    print(f"Created dataset {dataset_name}.")

# Define table schema with descriptions
schema = [
    bigquery.SchemaField("feature_1", "INTEGER", description="Integer feature with range 0-100"),
    bigquery.SchemaField("feature_2", "FLOAT", description="Float feature with range 0.0-1.0"),
    bigquery.SchemaField("feature_3", "STRING", description="String feature with values 'a', 'b', or 'c'"),
    bigquery.SchemaField("feature_4", "BOOLEAN", description="Boolean feature flag"),
    bigquery.SchemaField("entity_key", "STRING", description="Unique identifier for each entity"),
]

# Create internal table
internal_table_id = f"{dataset_id}.example_internal_table"
job_config = bigquery.LoadJobConfig(
    schema=schema,
    source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
    write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE
)
load_job = bq_client.load_table_from_uri(
    gcs_uri, internal_table_id, job_config=job_config
)
load_job.result()

# Add table description after loading
internal_table = bq_client.get_table(internal_table_id)
internal_table.description = "Internal table containing ML feature data imported from GCS"
bq_client.update_table(internal_table, ["description"])

print(f"Loaded data into internal table {internal_table_id}")

# Create external table
external_table_id = f"{dataset_id}.example_external_table"
external_config = bigquery.ExternalConfig(bigquery.SourceFormat.NEWLINE_DELIMITED_JSON)
external_config.source_uris = [gcs_uri]
external_table = bigquery.Table(external_table_id)
external_table.external_data_configuration = external_config
external_table.schema = schema
external_table.description = "External table referencing ML feature data stored in GCS"
try:
    bq_client.get_table(external_table_id)
    print(f"External table {external_table_id} already exists. Overwriting.")
    bq_client.delete_table(external_table_id)
except Exception:
    pass
bq_client.create_table(external_table)
print(f"Created external table {external_table_id}")


# Create Materialized View
mview_id = f"{dataset_id}.example_materialized_view"

# Drop the materialized view if it exists
drop_mview_query = f"DROP MATERIALIZED VIEW IF EXISTS `{mview_id}`"
bq_client.query(drop_mview_query).result()
print(f"Dropped materialized view {mview_id} if it existed.")

# Create the materialized view with OPTIONS for description
# Column descriptions are defined in the view definition header
create_mview_query = f"""
CREATE MATERIALIZED VIEW `{mview_id}`
OPTIONS(
    description = "Materialized view of ML features with transformed feature_2 (divided by 2)"
)
AS SELECT
    feature_1,
    feature_2/2 AS feature_2,
    feature_3,
    feature_4,
    entity_key
FROM `{internal_table_id}`
"""
bq_client.query(create_mview_query).result()

print(f"Created materialized view {mview_id}")

# Create a logical view from the materialized view
logical_view_id = f"{dataset_id}.example_logical_view"
create_logical_view_query = f"""
CREATE OR REPLACE VIEW `{logical_view_id}` (
    feature_1 OPTIONS(DESCRIPTION='Integer feature with range 0-100'),
    feature_2 OPTIONS(DESCRIPTION='Float feature with range 0.0-1.0 (multiplied by 2 from materialized view)'),
    feature_3 OPTIONS(DESCRIPTION='String feature with values a, b, or c'),
    feature_4 OPTIONS(DESCRIPTION='Boolean feature flag'),
    entity_key OPTIONS(DESCRIPTION='Unique identifier for each entity')
)
OPTIONS(
    description = "Logical view of materialized view with feature_2 transformed back (multiplied by 2)"
)
AS SELECT
    feature_1,
    feature_2*2 AS feature_2,
    feature_3,
    feature_4,
    entity_key
FROM `{mview_id}`
"""
bq_client.query(create_logical_view_query).result()

print(f"Created logical view {logical_view_id}")

# Get/Create Feature Store
FEATURE_STORE_NAME = PROJECT_ID.replace('-', '_') + '_bigtable'
try:
    online_store = feature_store.FeatureOnlineStore(name = FEATURE_STORE_NAME)
    # Check if it's a BigTable serving type
    if online_store.feature_online_store_type == 'bigtable':
        print(f"Found the BigTable feature store:\n{online_store.resource_name}")
    else:
        raise Exception(f"Existing store is {online_store.feature_online_store_type}, not bigtable")
except Exception as e:
    print(f"Creating BigTable feature store... (reason: {e})")
    online_store = feature_store.FeatureOnlineStore.create_bigtable_store(
        name = FEATURE_STORE_NAME,
        min_node_count = 1,
        max_node_count = 2
    )
    print(f"Created the BigTable feature store:\n{online_store.resource_name}")

online_store.feature_online_store_type






# function to get/create a feature view in the store
def get_or_create_feature_view(feature_view_name: str, bq_table_id: str, online_store: feature_store.FeatureOnlineStore) -> feature_store.FeatureView:
    try:
        feature_view = feature_store.FeatureView(
            name = feature_view_name,
            feature_online_store_id = online_store.resource_name
        )
        print(f"Feature View {feature_view_name} already exists.")
    except Exception:
        print(f"Creating Feature View {feature_view_name}.")
        feature_view = online_store.create_feature_view(
            name = feature_view_name,
            source = feature_store.utils.FeatureViewBigQuerySource(
                uri = f"bq://{bq_table_id}",
                entity_id_columns = ["entity_key"]
            ),
            sync_config = 'TZ=America/New_York 0 0 1 * *' # Ex: first day of every month at 00:00
        )
        print(f"Feature View {feature_view_name} created.")
    return feature_view

# get/create feature view for internal table
internal_table_feature_view = get_or_create_feature_view('example_internal_table', internal_table_id, online_store)
external_table_feature_view = get_or_create_feature_view('example_external_table', external_table_id, online_store)
logical_view_feature_view = get_or_create_feature_view('example_logical_view', logical_view_id, online_store)

# review feature view names
print(internal_table_feature_view.name)
print(external_table_feature_view.name)
print(logical_view_feature_view.name)

# manually sync feature views
internal_sync = internal_table_feature_view.sync()
external_sync = external_table_feature_view.sync()
logical_sync = logical_view_feature_view.sync()

sync_jobs = {
    'internal': {'job': internal_sync, 'view': internal_table_feature_view, 'completed': False},
    'external': {'job': external_sync, 'view': external_table_feature_view, 'completed': False},
    'logical': {'job': logical_sync, 'view': logical_view_feature_view, 'completed': False},
}

waited = 0
while True:
    all_completed = True
    for job_name, job_info in sync_jobs.items():
        if not job_info['completed']:
            all_completed = False
            sync_status = job_info['view'].get_sync(name = job_info['job'].name).to_dict()
            if 'endTime' in list(sync_status['runTime'].keys()):
                job_info['completed'] = True
                seconds = (
                    datetime.datetime.fromisoformat(sync_status['runTime']['endTime'].replace('Z', '+00:00'))
                    -
                    datetime.datetime.fromisoformat(sync_status['runTime']['startTime'].replace('Z', '+00:00'))
                ).total_seconds()
                rows = sync_status['syncSummary']['rowSynced']
                print(f"Sync for {job_name} completed in {seconds} seconds and synced {rows} rows.")

    if all_completed:
        print("All sync jobs completed.")
        break
    else:
        print(f"Waited {waited} seconds, Update again in 30 seconds...")
        time.sleep(30)
        waited += 30






# retrieve features from feature view for an entity:
def features_to_dict(features_list):
    """Converts a list of feature objects to a simple dictionary."""
    if not features_list:
        return {}
    return {feature['name']: list(feature['value'].values())[0] for feature in features_list}

# retrieve from each feature view
key = ['entity-1']
print("\nInternal Table Feature View:")
features_list = internal_table_feature_view.read(key = key).to_dict()['features']
print(features_to_dict(features_list))

print("\nExternal Table Feature View:")
features_list = external_table_feature_view.read(key = key).to_dict()['features']
print(features_to_dict(features_list))

print("\nLogical View Feature View:")
features_list = logical_view_feature_view.read(key = key).to_dict()['features']
print(features_to_dict(features_list))







# retrive for multiple entities - requires bigtable serving:
from google.cloud.aiplatform_v1beta1 import FeatureOnlineStoreServiceClient
from google.cloud.aiplatform_v1beta1.types import feature_online_store_service as feature_online_store_service_pb2

data_client = FeatureOnlineStoreServiceClient(
  client_options={"api_endpoint": f"{LOCATION}-aiplatform.googleapis.com"}
)

# which entities to request:
keys = [['entity-1'], ['entity-2'], ['entity-3']]

# prepare the request:
requests = []

for key in keys:
  requests.append(
    feature_online_store_service_pb2.StreamingFetchFeatureValuesRequest(
      feature_view=internal_table_feature_view.resource_name,
      data_keys=[
          feature_online_store_service_pb2.FeatureViewDataKey(key=k)
          for k in key
      ]
    )
  )

# retrieve the responses:
responses = data_client.streaming_fetch_feature_values(
    requests=iter(requests)
)


# process streaming responses
print("\nMultiple Entity Fetch Results:")
print("-" * 50)

for i, response in enumerate(responses):
    print(f"\nResponse {i+1}:")

    # Handle errors
    if response.status and response.status.code != 0:
        print(f"  Error: {response.status.message}")
        continue

    # Process each entity's data
    for data_item in response.data:
        entity_id = data_item.data_key.key if data_item.data_key else 'unknown'

        # Extract features
        features = {
            feature.name: (feature.value.string_value or
                            feature.value.int64_value or
                            feature.value.double_value or
                            feature.value.bool_value or
                            None
                        )
            for feature in data_item.key_values.features
        } if data_item.key_values else {}

        print(f"  Entity: {entity_id}")
        print(f"  Features: {features}")

print("\n" + "-" * 50)



