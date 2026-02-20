"""Create BigQuery dataset, connection, and object table over GCS source files."""

from google.cloud import bigquery
from google.cloud import bigquery_connection_v1
from config import BQ_PROJECT, BQ_DATASET, BQ_TABLE_PREFIX, BQ_CONNECTION, BQ_LOCATION, GCS_BUCKET, GCS_ROOT

# --- BigQuery client ---

bq = bigquery.Client(project=BQ_PROJECT)

# --- Create dataset if needed ---

dataset_ref = f"{BQ_PROJECT}.{BQ_DATASET}"
dataset = bigquery.Dataset(dataset_ref)
dataset.location = BQ_LOCATION
dataset = bq.create_dataset(dataset, exists_ok=True)
print(f"Dataset: {dataset_ref}")

# --- Create connection if needed ---

conn_client = bigquery_connection_v1.ConnectionServiceClient()
parent = f"projects/{BQ_PROJECT}/locations/{BQ_LOCATION.lower()}"
connection_ref = f"{parent}/connections/{BQ_CONNECTION}"

try:
    conn = conn_client.get_connection(name=connection_ref)
    print(f"Connection exists: {BQ_CONNECTION}")
except Exception:
    conn = conn_client.create_connection(
        parent=parent,
        connection_id=BQ_CONNECTION,
        connection=bigquery_connection_v1.Connection(
            friendly_name=BQ_CONNECTION,
            cloud_resource=bigquery_connection_v1.CloudResourceProperties(),
        ),
    )
    print(f"Connection created: {BQ_CONNECTION}")

# Service account for the connection (needs GCS read access)
sa = conn.cloud_resource.service_account_id
print(f"Connection service account: {sa}")

# --- Grant the connection's service account read access to the GCS bucket ---

from google.cloud import storage
storage_client = storage.Client(project=BQ_PROJECT)
bucket = storage_client.bucket(GCS_BUCKET)
policy = bucket.get_iam_policy(requested_policy_version=3)
policy.version = 3
binding = {"role": "roles/storage.objectViewer", "members": {f"serviceAccount:{sa}"}}
if binding not in policy.bindings:
    policy.bindings.append(binding)
    bucket.set_iam_policy(policy)
    print(f"Granted objectViewer on gs://{GCS_BUCKET} to {sa}")
else:
    print(f"objectViewer already granted on gs://{GCS_BUCKET}")

# --- Create object table ---

table_name = f"{BQ_TABLE_PREFIX}_source"
table_ref = f"{dataset_ref}.{table_name}"
gcs_uri = f"gs://{GCS_BUCKET}/{GCS_ROOT}/*"

query = f"""
CREATE OR REPLACE EXTERNAL TABLE `{table_ref}`
WITH CONNECTION `{BQ_PROJECT}.{BQ_LOCATION.lower()}.{BQ_CONNECTION}`
OPTIONS (
    object_metadata = 'SIMPLE',
    uris = ['{gcs_uri}'],
    metadata_cache_mode = 'AUTOMATIC',
    max_staleness = INTERVAL 1 HOUR
)
"""

bq.query(query).result()
print(f"Object table: {table_ref}")
print(f"GCS source: {gcs_uri}")

# --- Quick preview ---

preview = bq.query(f"SELECT uri, content_type, metadata FROM `{table_ref}` LIMIT 5").result()
for row in preview:
    print(f"  {row.uri}  type={row.content_type}  metadata={row.metadata}")
