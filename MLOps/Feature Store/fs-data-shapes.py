# imports
from google import genai
from pydantic import BaseModel, Field, create_model
from typing import List, Literal, Type, Union, get_type_hints, get_args, get_origin
from datetime import datetime, timedelta
import random
import subprocess
import pandas as pd
import json
from google.cloud import storage
from google.cloud import bigquery
from google.cloud import aiplatform

# static variable definitions
LOCATION = 'us-central1'

# derived variables
PROJECT_ID = subprocess.run(['gcloud', 'config', 'get-value', 'project'], capture_output=True, text=True).stdout.strip()
TOPICS = ['mlops', 'feature-store', 'data-shapes']

# client setup
genai_client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)
aiplatform.init(project=PROJECT_ID, location=LOCATION)

# GCS and BigQuery clients
storage_client = storage.Client(project=PROJECT_ID)
bq_client = bigquery.Client(project=PROJECT_ID)

# Ensure bucket exists
bucket_name = PROJECT_ID
bucket = storage_client.bucket(bucket_name)
if not bucket.exists():
    print(f"Bucket {bucket_name} does not exist. Creating bucket.")
    storage_client.create_bucket(bucket_name, location=LOCATION)

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


# ============================================================================
# UNIVERSAL FUNCTION TO CREATE TABLE FROM PYDANTIC SCHEMA
# ============================================================================

def pydantic_to_bq_field(field_name: str, field_type: Type, field_info) -> bigquery.SchemaField:
    """Convert a Pydantic field to BigQuery SchemaField"""
    type_mapping = {
        str: "STRING", int: "INTEGER", float: "FLOAT",
        bool: "BOOLEAN", datetime: "TIMESTAMP"
    }

    # Extract base type if Optional
    if get_origin(field_type) is Union:
        field_type = next((t for t in get_args(field_type) if t is not type(None)), field_type)

    # Determine BigQuery type
    bq_type = "STRING" if get_origin(field_type) is Literal else type_mapping.get(field_type, "STRING")

    return bigquery.SchemaField(
        field_name, bq_type, mode="NULLABLE",
        description=getattr(field_info, 'description', f"{field_name} field")
    )

def apply_sparseness(df: pd.DataFrame, make_sparse: bool) -> pd.DataFrame:
    """Apply sparseness to a DataFrame by randomly deleting values."""
    if not make_sparse:
        return df

    # Add timestamp column with random times in first half of 2025
    base_date = pd.Timestamp('2025-01-01')
    end_date = pd.Timestamp('2025-06-30')
    timestamps = []

    for _ in range(len(df)):
        random_days = random.uniform(0, (end_date - base_date).days)
        random_hours = random.uniform(0, 24)
        timestamp = base_date + timedelta(days=random_days, hours=random_hours)
        timestamps.append(timestamp)

    df.insert(0, 'timestamp', timestamps)

    # Apply sparseness - skip entity_key and timestamp columns
    cols_to_sparse = [col for col in df.columns if col not in ['entity_key', 'timestamp']]

    for idx in range(len(df)):
        # Dynamic probability: early records less sparse, later records more sparse
        entity_key = df.loc[idx, 'entity_key']
        entity_rows = df[df['entity_key'] == entity_key].index
        position = list(entity_rows).index(idx)

        # Probability increases from 0.1 to 0.7 based on position within entity
        if len(entity_rows) > 1:
            delete_prob = 0.1 + (0.6 * position / (len(entity_rows) - 1))
        else:
            delete_prob = 0.3

        # Randomly delete values based on probability
        for col in cols_to_sparse:
            if random.random() < delete_prob:
                df.loc[idx, col] = None

    return df

def create_table_from_schema(
    table_name: str,
    record_schema: Type[BaseModel],
    num_records: int = 1,
    num_entity: int = 10,
    table_description: str = None,
    make_sparse: bool = False
) -> pd.DataFrame:
    """Create a BigQuery table from a Pydantic schema."""
    total_records = num_entity * num_records
    print(f"\nCreating table: {table_name} ({total_records} total records: {num_entity} entities × {num_records} records each)")

    # Create list schema for Gemini
    list_schema = create_model(
        f"{record_schema.__name__}List",
        records=(List[record_schema], ...)
    )

    # Generate data
    total_records = num_entity * num_records
    prompt = f"Generate exactly {total_records} diverse and realistic records."
    if num_records > 1:
        prompt += f" Create {num_entity} groups with {num_records} records each."

    response = genai_client.models.generate_content(
        model='gemini-2.5-flash-lite',
        contents=[prompt],
        config={"response_mime_type": "application/json", "response_schema": list_schema}
    )

    data = json.loads(response.text)['records']

    # check record numbers:
    if len(data) > total_records:
        data = data[:total_records]
    elif len(data) < total_records:
        print(f"Warning: Generated {len(data)} records, requested {total_records}")


    # Add entity_key (always add, never part of input schema)
    for i, record in enumerate(data):
        # Assign entity keys in round-robin fashion for proper distribution
        entity_id = (i % num_entity) + 1
        record['entity_key'] = f'entity-{entity_id}'

    df = pd.DataFrame(data)

    # Apply sparseness if requested
    df = apply_sparseness(df, make_sparse)

    print(f"Generated {len(df)} records{'(sparse)' if make_sparse else ''}")

    # Save to GCS - convert NaN to None and handle data types
    records = []
    for _, row in df.iterrows():
        record = {}
        for key, value in row.items():
            if pd.isna(value):
                record[key] = None
            elif isinstance(value, pd.Timestamp):
                record[key] = value.isoformat()
            elif isinstance(value, float) and value.is_integer():
                record[key] = int(value)
            else:
                record[key] = value
        records.append(record)
    jsonl_data = "\n".join([json.dumps(record) for record in records])
    blob_path = '/'.join(TOPICS) + f"/{table_name}.jsonl"
    blob = bucket.blob(blob_path)
    blob.upload_from_string(jsonl_data)
    gcs_uri = f"gs://{bucket_name}/{blob_path}"
    print(f"Saved to GCS: {gcs_uri}")

    # Create BigQuery schema from Pydantic
    type_hints = get_type_hints(record_schema)
    bq_schema = []

    for field_name, field_type in type_hints.items():
        field_info = record_schema.model_fields.get(field_name)
        bq_field = pydantic_to_bq_field(field_name, field_type, field_info)
        bq_schema.append(bq_field)

    # Add entity_key field if not in schema
    if 'entity_key' not in type_hints:
        bq_schema.append(
            bigquery.SchemaField("entity_key", "STRING", mode="NULLABLE", description="Unique identifier for each entity")
        )

    # Add timestamp field if sparse
    if make_sparse:
        bq_schema.insert(0,
            bigquery.SchemaField("timestamp", "TIMESTAMP", mode="NULLABLE", description="Timestamp for the observation")
        )

    # Load into BigQuery
    table_id = f"{dataset_id}.{table_name}"

    job_config = bigquery.LoadJobConfig(
        schema=bq_schema,
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE
    )

    load_job = bq_client.load_table_from_uri(
        gcs_uri, table_id, job_config=job_config
    )
    load_job.result()

    # Add table description
    table = bq_client.get_table(table_id)
    table.description = table_description or f"Table {table_name} created from {record_schema.__name__}"
    bq_client.update_table(table, ["description"])

    print(f"Created BigQuery table: {table_id}")
    return df

# ============================================================================
# CREATE TABLES
# do not request the entity_Key column
# enttiy_key will be added based on the values of num_entity and num_records
# when num_records > num_entity there will be multiple records per unique entity_key
# ============================================================================

# Create first dense table
class DenseRecord1(BaseModel):
    """First dense table with features 1-5"""
    feature_1: bool = Field(..., description="Boolean feature from table 1")
    feature_2: int = Field(..., description="Integer feature (0-100) from table 1", ge=0, le=100)
    feature_3: Literal['High', 'Low'] = Field(..., description="String feature (High/Low) from table 1")
    feature_4: float = Field(..., description="Float feature (0.0-1.0) from table 1", ge=0.0, le=1.0)
    feature_5: bool = Field(..., description="Boolean feature from table 1")

df1 = create_table_from_schema(
    table_name="ex_shape_dense_1",
    record_schema=DenseRecord1,
    num_records=1, #per entity
    num_entity=10,
    table_description="Dense feature table 1 with features 1-5"
)

# Create second dense table
class DenseRecord2(BaseModel):
    """Second dense table with features 6-10"""
    feature_6: bool = Field(..., description="Boolean feature from table 2")
    feature_7: int = Field(..., description="Integer feature (0-10) from table 2", ge=0, le=10)
    feature_8: Literal['High', 'Medium', 'Low'] = Field(..., description="String feature (High/Medium/Low) from table 2")
    feature_9: float = Field(..., description="Float feature (0.0-1.0) from table 2", ge=0.0, le=1.0)
    feature_10: bool = Field(..., description="Boolean feature from table 2")

df2 = create_table_from_schema(
    table_name="ex_shape_dense_2",
    record_schema=DenseRecord2,
    num_records=1, # per entity
    num_entity=10,
    table_description="Dense feature table 2 with features 6-10"
)

# Create third table (will be made sparse)
class SparseRecord(BaseModel):
    """Table 3 with features 11-15 (will be made sparse)"""
    feature_11: bool = Field(..., description="Boolean feature from table 3")
    feature_12: int = Field(..., description="Integer feature (0-100) from table 3", ge=0, le=100)
    feature_13: Literal['High', 'Medium', 'Low'] = Field(..., description="String feature from table 3")
    feature_14: float = Field(..., description="Float feature (0.0-1.0) from table 3", ge=0.0, le=1.0)
    feature_15: bool = Field(..., description="Boolean feature from table 3")

df3 = create_table_from_schema(
    table_name="ex_shape_sparse_1",
    record_schema=SparseRecord,
    num_records=5,  # per entity
    num_entity=10,
    table_description="Temporal sparse table with features 11-15, multiple timestamps per entity",
    make_sparse=True
)

# Create fourth table (second sparse table)
class SparseRecord2(BaseModel):
    """Table 4 with features 16-20 (will be made sparse)"""
    feature_16: bool = Field(..., description="Boolean feature from table 4")
    feature_17: int = Field(..., description="Integer feature (0-50) from table 4", ge=0, le=50)
    feature_18: Literal['Excellent', 'Good', 'Fair', 'Poor'] = Field(..., description="String feature from table 4")
    feature_19: float = Field(..., description="Float feature (0.0-100.0) from table 4", ge=0.0, le=100.0)
    feature_20: bool = Field(..., description="Boolean feature from table 4")

df4 = create_table_from_schema(
    table_name="ex_shape_sparse_2",
    record_schema=SparseRecord2,
    num_records=5,  # per entity (different from sparse_1)
    num_entity=10,
    table_description="Temporal sparse table with features 16-20, multiple timestamps per entity",
    make_sparse=True
)

print("\n" + "="*60)
print("All tables created successfully!")
print(f"Table 1: {dataset_id}.ex_shape_dense_1")
print(f"Table 2: {dataset_id}.ex_shape_dense_2")
print(f"Table 3: {dataset_id}.ex_shape_sparse_1")
print(f"Table 4: {dataset_id}.ex_shape_sparse_2")
print("="*60)

