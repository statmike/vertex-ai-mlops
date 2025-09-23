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
from vertexai.resources.preview import feature_store
import bigframes
import bigframes.pandas
from vertexai.resources.preview.feature_store import offline_store

# static variable definitions
LOCATION = 'us-central1'
TOPICS = ['mlops', 'feature-store', 'data-shapes']

# derived variables & client setup
PROJECT_ID = subprocess.run(['gcloud', 'config', 'get-value', 'project'], capture_output=True, text=True).stdout.strip()
aiplatform.init(project=PROJECT_ID, location=LOCATION)
genai_client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)
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
bq_client.create_dataset(dataset, exists_ok=True)
print(f"Dataset {dataset_name} is ready.")


# ============================================================================ 
# UNIVERSAL FUNCTION TO CREATE TABLE FROM PYDANTIC SCHEMA
# ============================================================================ 

def _pydantic_to_bq_field(field_name: str, field_type: Type, field_info) -> bigquery.SchemaField:
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

def _transform_to_eav(df: pd.DataFrame, make_eav: bool) -> pd.DataFrame:
    """Transform DataFrame to Entity-Attribute-Value format using pandas.melt."""
    if not make_eav:
        return df

    # Identify columns to keep as is (id_vars)
    id_vars = ['entity_key']
    if 'feature_timestamp' in df.columns:
        id_vars.append('feature_timestamp')

    # Use pandas.melt to unpivot from wide to long format, then drop nulls
    eav_df = df.melt(
        id_vars=id_vars,
        var_name='feature_name',
        value_name='value'
    ).dropna(subset=['value'])

    # A helper function to create the BigQuery-compatible feature_value struct
    def create_value_struct(value):
        # Order is important as isinstance(True, int) is True in Python
        if isinstance(value, bool):
            return {'bool_value': value}
        # Handle integers that pandas may have cast to float due to NaNs
        if isinstance(value, float) and value.is_integer():
            return {'int_value': int(value)}
        if isinstance(value, int):
            return {'int_value': value}
        if isinstance(value, float):
            return {'float_value': value}
        return {'string_value': str(value)}

    # Apply the function to create the new 'feature_value' column
    eav_df['feature_value'] = eav_df['value'].apply(create_value_struct)

    # Return the final EAV DataFrame, dropping the temporary 'value' column
    return eav_df.drop(columns='value')

def _add_timestamps(df: pd.DataFrame, make_sparse: bool) -> pd.DataFrame:
    """Add feature_timestamp column to DataFrame."""
    if make_sparse:
        # Add random timestamps for sparse tables using a list comprehension
        base_date = pd.Timestamp('2025-01-01')
        end_date = pd.Timestamp('2025-06-30')
        total_days = (end_date - base_date).days
        timestamps = [
            base_date + timedelta(days=random.uniform(0, total_days), hours=random.uniform(0, 24))
            for _ in range(len(df))
        ]
    else:
        # Add current timestamp for dense tables
        timestamps = [pd.Timestamp.now()] * len(df)

    df.insert(0, 'feature_timestamp', timestamps)
    return df

def _apply_sparseness(df: pd.DataFrame, make_sparse: bool) -> pd.DataFrame:
    """Apply sparseness to a DataFrame by randomly deleting values."""
    if not make_sparse:
        return df

    cols_to_sparse = [col for col in df.columns if col not in ['entity_key', 'feature_timestamp']]

    # Iterate over each entity group to apply dynamic probability efficiently
    for entity_key, group in df.groupby('entity_key'):
        n_rows = len(group)
        # Iterate over the rows of the group to get their position
        for i, (idx, row) in enumerate(group.iterrows()):
            # Probability increases from 0.1 to 0.7 based on position within the entity group
            if n_rows > 1:
                delete_prob = 0.1 + (0.6 * i / (n_rows - 1))
            else:
                delete_prob = 0.3

            # Randomly set feature values to None based on the calculated probability
            for col in cols_to_sparse:
                if random.random() < delete_prob:
                    df.loc[idx, col] = None # Modify the original DataFrame

    return df

# Helper functions for create_table_from_schema

def _clean_df_for_bq(df: pd.DataFrame, record_schema: Type[BaseModel]) -> pd.DataFrame:
    """
    Cleans a DataFrame to align with the Pydantic schema for BigQuery loading.
    Specifically, it handles integer columns that may have been cast to float
    due to the presence of NaN values by converting them to pandas' nullable
    integer type ('Int64').
    """
    type_hints = get_type_hints(record_schema)
    for name, ftype in type_hints.items():
        if name in df.columns:
            # Resolve Optional[type] to type
            if get_origin(ftype) is Union:
                field_type = next((t for t in get_args(ftype) if t is not type(None)), ftype)
            else:
                field_type = ftype

            # If schema expects an integer but the DataFrame column is float, convert it
            if field_type is int and pd.api.types.is_float_dtype(df[name].dtype):
                # Convert to nullable integer type to correctly handle NaNs
                df[name] = df[name].astype('Int64')
                
    return df


def _generate_synthetic_data(record_schema: Type[BaseModel], num_entity: int, num_records: int) -> List[dict]:
    """Generates synthetic data using a GenAI model based on a Pydantic schema."""
    total_records = num_entity * num_records
    list_schema = create_model(f"{record_schema.__name__}List", records=(List[record_schema], ...))
    
    prompt = f"Generate exactly {total_records} diverse and realistic records."
    if num_records > 1:
        prompt += f" Create {num_entity} groups with {num_records} records each."

    try:
        response = genai_client.models.generate_content(
            model='gemini-2.5-flash-lite',
            contents=[prompt],
            config={"response_mime_type": "application/json", "response_schema": list_schema}
        )
        data = json.loads(response.text)['records']
        
        if len(data) > total_records:
            data = data[:total_records]
        elif len(data) < total_records:
            print(f"Warning: Generated {len(data)} records, but requested {total_records}")
            
        return data
    except Exception as e:
        print(f"Error during data generation: {e}")
        return []

def _process_data_frame(data: List[dict], num_entity: int, make_sparse: bool, make_eav: bool) -> pd.DataFrame:
    """Converts raw data to a DataFrame and applies all processing steps."""
    for i, record in enumerate(data):
        record['entity_key'] = f'entity-{(i % num_entity) + 1}'
        
    df = pd.DataFrame(data)
    df = _add_timestamps(df, make_sparse)
    df = _apply_sparseness(df, make_sparse)
    df = _transform_to_eav(df, make_eav)
    
    return df

def _upload_df_to_gcs(df: pd.DataFrame, table_name: str) -> str:
    """Uploads a DataFrame to GCS as a JSONL file."""
    # Corrected df.to_json to use 'records' orient and 'lines=True' for JSONL format
    # Also ensuring date_format is 'iso' for timestamps
    jsonl_data = df.to_json(orient='records', lines=True, date_format='iso')
    
    blob_path = '/'.join(TOPICS) + f"/{table_name}.jsonl"
    blob = bucket.blob(blob_path)
    blob.upload_from_string(jsonl_data)
    
    gcs_uri = f"gs://{bucket_name}/{blob_path}"
    print(f"Saved to GCS: {gcs_uri}")
    return gcs_uri

def _create_bq_schema(record_schema: Type[BaseModel], make_eav: bool, make_sparse: bool) -> List[bigquery.SchemaField]:
    """Creates a BigQuery schema based on the data shape (EAV or regular)."""
    if make_eav:
        bq_schema = [
            bigquery.SchemaField("entity_key", "STRING", mode="NULLABLE", description="Unique identifier for each entity"),
            bigquery.SchemaField("feature_name", "STRING", mode="NULLABLE", description="Name of the feature"),
            bigquery.SchemaField(
                "feature_value", "RECORD", mode="NULLABLE", description="Feature value as struct",
                fields=[
                    bigquery.SchemaField("bool_value", "BOOLEAN", mode="NULLABLE", description="Boolean value"),
                    bigquery.SchemaField("int_value", "INTEGER", mode="NULLABLE", description="Integer value"),
                    bigquery.SchemaField("float_value", "FLOAT", mode="NULLABLE", description="Float value"),
                    bigquery.SchemaField("string_value", "STRING", mode="NULLABLE", description="String value")
                ]
            )
        ]
        if make_sparse:
            bq_schema.insert(1, bigquery.SchemaField("feature_timestamp", "TIMESTAMP", mode="NULLABLE", description="Timestamp for the observation"))
    else:
        type_hints = get_type_hints(record_schema)
        bq_schema = [_pydantic_to_bq_field(name, ftype, record_schema.model_fields.get(name)) for name, ftype in type_hints.items()]
        bq_schema.insert(0, bigquery.SchemaField("feature_timestamp", "TIMESTAMP", mode="NULLABLE", description="Timestamp for the observation"))
        bq_schema.append(bigquery.SchemaField("entity_key", "STRING", mode="NULLABLE", description="Unique identifier for each entity"))
        
    return bq_schema

def _load_gcs_to_bq(gcs_uri: str, table_id: str, bq_schema: List[bigquery.SchemaField], table_description):
    """Loads data from a GCS JSONL file into a BigQuery table."""
    job_config = bigquery.LoadJobConfig(
        schema=bq_schema,
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE
    )
    
    load_job = bq_client.load_table_from_uri(gcs_uri, table_id, job_config=job_config)
    load_job.result()

    table = bq_client.get_table(table_id)
    table.description = table_description
    bq_client.update_table(table, ["description"])
    print(f"Created BigQuery table: {table_id}")


def create_table_from_schema(
    table_name: str,
    record_schema: Type[BaseModel],
    num_records: int = 1,
    num_entity: int = 10,
    table_description: str = None,
    make_sparse: bool = False,
    make_eav: bool = False
) -> pd.DataFrame:
    """Orchestrates the creation of a BigQuery table from a Pydantic schema."""
    total_records = num_entity * num_records
    print(f"\nCreating table: {table_name} ({total_records} total records: {num_entity} entities × {num_records} records each)")

    # 1. Generate synthetic data
    data = _generate_synthetic_data(record_schema, num_entity, num_records)
    if not data:
        print(f"Data generation failed for {table_name}. Aborting.")
        return None

    # 2. Process data and apply transformations
    df = _process_data_frame(data, num_entity, make_sparse, make_eav)
    print(f"Generated {len(df)} records{'(sparse)' if make_sparse else ''}{'(EAV)' if make_eav else ''}")

    # Cleanse data before upload for non-EAV tables to handle types correctly
    if not make_eav:
        df = _clean_df_for_bq(df, record_schema)

    # 3. Upload processed DataFrame to GCS
    gcs_uri = _upload_df_to_gcs(df, table_name)

    # 4. Create BigQuery schema
    bq_schema = _create_bq_schema(record_schema, make_eav, make_sparse)

    # 5. Load data from GCS into BigQuery
    table_id = f"{dataset_id}.{table_name}"
    _load_gcs_to_bq(
        gcs_uri=gcs_uri,
        table_id=table_id,
        bq_schema=bq_schema,
        table_description=table_description or f"Table {table_name} created from {record_schema.__name__}"
    )
    
    return df


# ============================================================================ 
# CREATE TABLES
# This section defines the schemas and configurations for creating multiple BigQuery tables.
# The process is data-driven, using a list of configurations to loop through,
# making it easy to add or modify table creation requests.
# ============================================================================ 

# Pydantic Schemas for Table Records
class DenseRecord1(BaseModel):
    """First dense table with features 1-5"""
    feature_1: bool = Field(..., description="Boolean feature from table 1")
    feature_2: int = Field(..., description="Integer feature (0-100) from table 1", ge=0, le=100)
    feature_3: Literal['High', 'Low'] = Field(..., description="String feature (High/Low) from table 1")
    feature_4: float = Field(..., description="Float feature (0.0-1.0) from table 1", ge=0.0, le=1.0)
    feature_5: bool = Field(..., description="Boolean feature from table 1")

class DenseRecord2(BaseModel):
    """Second dense table with features 6-10"""
    feature_6: bool = Field(..., description="Boolean feature from table 2")
    feature_7: int = Field(..., description="Integer feature (0-10) from table 2", ge=0, le=10)
    feature_8: Literal['High', 'Medium', 'Low'] = Field(..., description="String feature (High/Medium/Low) from table 2")
    feature_9: float = Field(..., description="Float feature (0.0-1.0) from table 2", ge=0.0, le=1.0)
    feature_10: bool = Field(..., description="Boolean feature from table 2")

class SparseRecord(BaseModel):
    """Table 3 with features 11-15 (will be made sparse)"""
    feature_11: bool = Field(..., description="Boolean feature from table 3")
    feature_12: int = Field(..., description="Integer feature (0-100) from table 3", ge=0, le=100)
    feature_13: Literal['High', 'Medium', 'Low'] = Field(..., description="String feature from table 3")
    feature_14: float = Field(..., description="Float feature (0.0-1.0) from table 3", ge=0.0, le=1.0)
    feature_15: bool = Field(..., description="Boolean feature from table 3")

class SparseRecord2(BaseModel):
    """Table 4 with features 16-20 (will be made sparse)"""
    feature_16: bool = Field(..., description="Boolean feature from table 4")
    feature_17: int = Field(..., description="Integer feature (0-50) from table 4", ge=0, le=50)
    feature_18: Literal['Excellent', 'Good', 'Fair', 'Poor'] = Field(..., description="String feature from table 4")
    feature_19: float = Field(..., description="Float feature (0.0-100.0) from table 4", ge=0.0, le=100.0)
    feature_20: bool = Field(..., description="Boolean feature from table 4")

class EAVRecord(BaseModel):
    """Table 5 with features 21-25 (will be made sparse and EAV)"""
    feature_21: bool = Field(..., description="Boolean feature from table 5")
    feature_22: int = Field(..., description="Integer feature (0-200) from table 5", ge=0, le=200)
    feature_23: Literal['Alpha', 'Beta', 'Gamma', 'Delta'] = Field(..., description="String feature from table 5")
    feature_24: float = Field(..., description="Float feature (0.0-10.0) from table 5", ge=0.0, le=10.0)
    feature_25: bool = Field(..., description="Boolean feature from table 5")

class EAVRecord2(BaseModel):
    """Table 6 with features 26-30 (will be made sparse and EAV)"""
    feature_26: bool = Field(..., description="Boolean feature from table 6")
    feature_27: int = Field(..., description="Integer feature (0-500) from table 6", ge=0, le=500)
    feature_28: Literal['Red', 'Blue', 'Green', 'Yellow', 'Purple'] = Field(..., description="String feature from table 6")
    feature_29: float = Field(..., description="Float feature (-1.0-1.0) from table 6", ge=-1.0, le=1.0)
    feature_30: bool = Field(..., description="Boolean feature from table 6")

# Configuration for each table to be created
table_configs = [
    {
        "table_name": "ex_shape_dense_1", "record_schema": DenseRecord1, "num_records": 1, "num_entity": 10,
        "table_description": "Dense feature table 1 with features 1-5",
    },
    {
        "table_name": "ex_shape_dense_2", "record_schema": DenseRecord2, "num_records": 1, "num_entity": 10,
        "table_description": "Dense feature table 2 with features 6-10",
    },
    {
        "table_name": "ex_shape_sparse_1", "record_schema": SparseRecord, "num_records": 5, "num_entity": 10,
        "table_description": "Temporal sparse table with features 11-15, multiple timestamps per entity",
        "make_sparse": True,
    },
    {
        "table_name": "ex_shape_sparse_2", "record_schema": SparseRecord2, "num_records": 5, "num_entity": 10,
        "table_description": "Temporal sparse table with features 16-20, multiple timestamps per entity",
        "make_sparse": True,
    },
    {
        "table_name": "ex_shape_eav_1", "record_schema": EAVRecord, "num_records": 5, "num_entity": 10,
        "table_description": "EAV format sparse table with features 21-25",
        "make_sparse": True, "make_eav": True,
    },
    {
        "table_name": "ex_shape_eav_2", "record_schema": EAVRecord2, "num_records": 5, "num_entity": 10,
        "table_description": "EAV format sparse table with features 26-30",
        "make_sparse": True, "make_eav": True,
    },
]

# Create all tables from the configuration
dataframes = {config["table_name"]: create_table_from_schema(**config) for config in table_configs}

print("\n" + "="*60)
print("All tables created successfully!")
for table_name in dataframes.keys():
    print(f"Table: {dataset_id}.{table_name}")
print("="*60)

# ============================================================================ 
# CREATE VIEWS
# ============================================================================ 

print("\nCreating BigQuery views...")

def create_view(view_name: str, view_query: str, description: str):
    """Creates or replaces a BigQuery view and sets its description."""
    view_id = f"{dataset_id}.{view_name}"
    
    # Add the view_id to the query
    query = view_query.format(view_id=view_id, dataset_id=dataset_id)

    print(f"Creating view: {view_id}")
    bq_client.query(query).result()
    
    view = bq_client.get_table(view_id)
    view.description = description
    bq_client.update_table(view, ["description"])
    print(f"Successfully created view: {view_id}")

def _get_bq_column_definitions(record_schema: Type[BaseModel], include_timestamp: bool = True, include_entity_key: bool = True) -> str:
    """Generates BigQuery column definitions from a Pydantic schema for use in DDL."""
    defs = []
    type_hints = get_type_hints(record_schema)
    
    if include_timestamp:
        defs.append("feature_timestamp OPTIONS(DESCRIPTION='Timestamp for the observation')")

    for name, ftype in type_hints.items():
        field_info = record_schema.model_fields.get(name)
        description = getattr(field_info, 'description', f"{name} field")
        defs.append(f"{name} OPTIONS(DESCRIPTION='{description}')")

    if include_entity_key:
        defs.append("entity_key OPTIONS(DESCRIPTION='Unique identifier for each entity')")
        
    return ",\n    ".join(defs)

def _get_eav_pivot_expressions(record_schema: Type[BaseModel]) -> str:
    """Generates pivot expressions for EAV to wide format conversion."""
    expressions = []
    type_mapping = {
        str: "string_value",
        int: "int_value",
        float: "float_value",
        bool: "bool_value",
    }

    for name, ftype in get_type_hints(record_schema).items():
        if get_origin(ftype) is Union:
            py_type = next((t for t in get_args(ftype) if t is not type(None)), ftype)
        else:
            py_type = ftype
        
        if get_origin(py_type) is Literal:
            py_type = str

        value_field = type_mapping.get(py_type, "string_value")
        expressions.append(f"MAX(IF(feature_name = '{name}', feature_value.{value_field}, NULL)) AS {name}")
    
    return ",\n  ".join(expressions)

# Create dense view from sparse table
view_name = "ex_shape_sparse_2_dense"
# Simplified: Let BigQuery handle column naming naturally
view_query = f"""
CREATE OR REPLACE VIEW `{{view_id}}`
OPTIONS(
    description = "Dense view of sparse table using ML.FEATURES_AT_TIME to get latest feature values"
)
AS
SELECT * EXCEPT (entity_id),
    entity_id AS entity_key
FROM ML.FEATURES_AT_TIME(
    (SELECT * EXCEPT(entity_key), entity_key AS entity_id FROM `{{dataset_id}}.ex_shape_sparse_2`),
    time => CURRENT_TIMESTAMP(),
    num_rows => 1,
    ignore_feature_nulls => TRUE
)
"""
create_view(view_name, view_query, "Dense view of sparse table using ML.FEATURES_AT_TIME to get latest feature values")
print("="*60)

# Create sparse view from EAV table
view_name = "ex_shape_eav_1_sparse"
pivot_expressions = _get_eav_pivot_expressions(EAVRecord)
# Simplified: Let BigQuery infer column names from SELECT, avoiding position mismatch
view_query = f"""
CREATE OR REPLACE VIEW `{{view_id}}`
OPTIONS(
    description = "Sparse wide format view of EAV table, pivoted from entity-attribute-value to columnar format"
)
AS
SELECT
  entity_key,
  feature_timestamp,
  {pivot_expressions}
FROM `{{dataset_id}}.ex_shape_eav_1`
GROUP BY entity_key, feature_timestamp
ORDER BY entity_key, feature_timestamp
"""
create_view(view_name, view_query, "Sparse wide format view of EAV table, pivoted from entity-attribute-value to columnar format")
print("="*60)

# This procedural SQL block dynamically creates a separate view for each feature in the EAV table.
# It introspects the table to determine the data type for each feature and then generates
# a CREATE VIEW statement for each one, resulting in one view per feature.
print("\nCreating individual feature views for ex_shape_eav_2...")
create_views_sql = f"""
DECLARE feature_list ARRAY<STRUCT<feature_name STRING, value_field STRING>>;
DECLARE i INT64 DEFAULT 0;
DECLARE current_feature STRING;
DECLARE current_value_field STRING;
DECLARE view_sql STRING;

-- Determine the data type for each feature by checking which field is populated
SET feature_list = ARRAY(
  SELECT AS STRUCT
    feature_name,
    CASE
      WHEN COUNT(feature_value.bool_value) > 0 THEN 'bool_value'
      WHEN COUNT(feature_value.int_value) > 0 THEN 'int_value'
      WHEN COUNT(feature_value.float_value) > 0 THEN 'float_value'
      WHEN COUNT(feature_value.string_value) > 0 THEN 'string_value'
    END AS value_field
  FROM `{dataset_id}.ex_shape_eav_2`
  GROUP BY feature_name
  ORDER BY feature_name
);

-- Loop through each feature and create a view
WHILE i < ARRAY_LENGTH(feature_list) DO
  SET current_feature = feature_list[OFFSET(i)].feature_name;
  SET current_value_field = feature_list[OFFSET(i)].value_field;

  -- Build and execute the CREATE VIEW statement
  SET view_sql = FORMAT('''
    CREATE OR REPLACE VIEW `{dataset_id}.ex_shape_eav_2_%s` (
      entity_key OPTIONS(DESCRIPTION="Unique identifier for each entity"),
      feature_timestamp OPTIONS(DESCRIPTION="Timestamp for the observation"),
      %s OPTIONS(DESCRIPTION="Feature %s from table 6")
    )
    OPTIONS(description="Sparse view for %s from EAV table ex_shape_eav_2")
    AS
    SELECT
      entity_key,
      feature_timestamp,
      feature_value.%s AS %s
    FROM `{dataset_id}.ex_shape_eav_2`
    WHERE feature_name = '%s'
    ORDER BY entity_key, feature_timestamp
  ''', current_feature, current_feature, current_feature, current_feature, current_value_field, current_feature, current_feature);

  EXECUTE IMMEDIATE view_sql;

  SET i = i + 1;
END WHILE;

-- Return list of created views
SELECT CONCAT('Created view: {dataset_id}.ex_shape_eav_2_', feature_name) as result
FROM UNNEST(feature_list);
"""

results = bq_client.query(create_views_sql).to_dataframe()
for result in results['result']:
    print(result)

print("="*60)




# ============================================================================
# FEATURE GROUP AND FEATURE REGISTRATION
# ============================================================================

def register_source_as_feature_group(source_id: str, dataset_id: str) -> tuple[feature_store.FeatureGroup, dict]:
    """
    Creates a Feature Group for a given BigQuery source (table/view) and
    registers its columns as Features.

    Args:
        source_id (str): The name of the BigQuery table or view.
        dataset_id (str): The BigQuery dataset ID (e.g., 'project.dataset').

    Returns:
        tuple: A tuple containing:
            - The created or retrieved feature_store.FeatureGroup object.
            - A dictionary of all features for this group (both new and existing).
            Returns (None, None) if the source can't be processed.
    """
    full_table_id = f"{dataset_id}.{source_id}"
    bq_source_uri = f"bq://{full_table_id}"

    try:
        table = bq_client.get_table(full_table_id)
        description = table.description or f"Feature group for {source_id}"
    except Exception as e:
        print(f"  Warning: Could not retrieve metadata for {source_id}. Skipping. Error: {e}")
        return None, None

    # 1. Create or Get Feature Group
    print(f"\nProcessing source: {source_id}")
    try:
        fg = feature_store.FeatureGroup(name=source_id)
        print(f"  Feature Group '{source_id}' already exists.")
    except Exception:
        print(f"  Creating Feature Group '{source_id}'...")
        fg = feature_store.FeatureGroup.create(
            name=source_id,
            description=description,
            source=feature_store.utils.FeatureGroupBigQuerySource(
                uri=bq_source_uri,
                entity_id_columns=['entity_key']
            )
        )
        print(f"  Created Feature Group '{source_id}'")

    # 2. Register Features from table schema
    newly_registered_features = {}
    all_group_features = {}
    for field in table.schema:
        feature_name = field.name
        # Skip columns that are not features
        if feature_name in ['entity_key', 'feature_timestamp', 'feature_name', 'feature_value']:
            continue

        feature_description = field.description or f"Feature: {feature_name}"
        try:
            feature = fg.get_feature(feature_id=feature_name)
            print(f"    - Feature '{feature_name}' already exists.")
        except Exception:
            print(f"    - Registering feature '{feature_name}'...")
            feature = fg.create_feature(
                name=feature_name,
                description=feature_description
            )
            newly_registered_features[feature_name] = feature
        
        all_group_features[feature_name] = feature
    
    if newly_registered_features:
        print(f"  Registered {len(newly_registered_features)} new features for group '{source_id}'.")
    else:
        print(f"  No new features to register for group '{source_id}'.")

    return fg, all_group_features

print("\n" + "="*60)
print("Starting Feature Group and Feature Registration...")
print("="*60)

# Define the list of sources (tables and views) to register.
# This list matches the sources that have a direct columnar feature representation.
sources_to_register = [
    "ex_shape_dense_1",
    "ex_shape_dense_2",
    "ex_shape_sparse_1",
    "ex_shape_sparse_2_dense",
    "ex_shape_eav_1_sparse",
]
# Add the dynamically created views for ex_shape_eav_2
for feature_num in range(26, 31):
    sources_to_register.append(f"ex_shape_eav_2_feature_{feature_num}")

all_features = {}
feature_groups = {}

# Loop through the sources and register them
for source_id in sources_to_register:
    fg, features = register_source_as_feature_group(source_id, dataset_id)
    if fg:
        feature_groups[source_id] = fg
        if features:
            all_features[source_id] = features

print("\n" + "="*60)
print(f"Registration complete!")
total_groups = len(feature_groups)
total_features = sum(len(features) for features in all_features.values())
print(f"Total Feature Groups processed: {total_groups}")
print(f"Total Features registered: {total_features}")
print("="*60)












# Get/Create Feature Store
FEATURE_STORE_NAME = PROJECT_ID.replace('-', '_') + '_bigtable'
try:
    online_store = feature_store.FeatureOnlineStore(name=FEATURE_STORE_NAME)
    # If the store exists, verify it's the correct type
    if online_store.feature_online_store_type.name == 'BIGTABLE':
        print(f"Found the BigTable feature store:\n{online_store.resource_name}")
    else:
        # If it's the wrong type, raise an error as the script cannot proceed.
        raise TypeError(
            f"Store '{FEATURE_STORE_NAME}' exists but is type "
            f"'{online_store.feature_online_store_type.name}', not 'BIGTABLE'."
        )
except Exception as e:
    # Re-raise the specific TypeError to halt execution.
    if isinstance(e, TypeError):
        raise
    
    # Otherwise, assume the store was not found and create it.
    # A more specific exception catch (e.g., for google.api_core.exceptions.NotFound)
    # would be better if the specific exception class were known and importable.
    print(f"Creating BigTable feature store '{FEATURE_STORE_NAME}'... (Reason: {e})")
    online_store = feature_store.FeatureOnlineStore.create_bigtable_store(
        name=FEATURE_STORE_NAME,
        min_node_count=1,
        max_node_count=2
    )
    print(f"Created the BigTable feature store:\n{online_store.resource_name}")






# function to sync a feature view in the store
def sync_feature_view(
    feature_view_name: str,
    features_list: list,
    online_store: feature_store.FeatureOnlineStore,
    sync_config: str
) -> feature_store.FeatureView:
    """
    Ensures a Feature View is synced with the provided feature list.

    This function is idempotent. It checks if a view exists. If it does, it
    compares its feature list with the desired list. If different, it recreates
    the view. If the view does not exist, it creates it.
    """
    desired_features = sorted(features_list)

    try:
        feature_view = feature_store.FeatureView(
            name=feature_view_name,
            feature_online_store_id=online_store.resource_name
        )

        # View exists, get its current features to check for drift
        current_features = []
        source = feature_view.gca_resource.feature_registry_source
        if source:
            for group in source.feature_groups:
                for feature_id in group.feature_ids:
                    current_features.append(f"{group.feature_group_id}.{feature_id}")
        current_features = sorted(current_features)

        # If the features are the same, no update is needed
        if current_features == desired_features:
            print(f"Feature View '{feature_view_name}' already exists and is up-to-date.")
            return feature_view
        
        # Otherwise, recreate the view to update the feature list
        print(f"Feature View '{feature_view_name}' is outdated. Recreating...")
        feature_view.delete()
        
        # Create the view again with the updated feature list
        new_view = online_store.create_feature_view(
            name=feature_view_name,
            source=feature_store.utils.FeatureViewRegistrySource(features=desired_features),
            sync_config=sync_config
        )
        print(f"Feature View '{feature_view_name}' recreated successfully.")
        return new_view

    except Exception:
        # This block is triggered if the view is not found initially.
        print(f"Creating Feature View '{feature_view_name}'...")
        feature_view = online_store.create_feature_view(
            name=feature_view_name,
            source=feature_store.utils.FeatureViewRegistrySource(features=desired_features),
            sync_config=sync_config
        )
        print(f"Feature View '{feature_view_name}' created successfully.")
        return feature_view

# Create feature views for different feature combinations
print("\n" + "="*60)
print("Syncing Feature Views...")
print("="*60)

# Build lists of features in 'featuregroup.feature' format using list comprehensions
all_features_list = [
    f"{group_name}.{feature_name}"
    for group_name, features in all_features.items()
    for feature_name in features.keys()
]
odd_features_list = [
    f for f in all_features_list if int(f.split('.')[-1].split('_')[1]) % 2 != 0
]
even_features_list = [
    f for f in all_features_list if int(f.split('.')[-1].split('_')[1]) % 2 == 0
]

# Define the feature views to be created or updated
SYNC_CONFIG = 'TZ=America/New_York 0 0 1 * *' # Ex: first day of every month at 00:00
feature_view_definitions = {
    "all_features": all_features_list,
    "odd_features": odd_features_list,
    "even_features": even_features_list,
}

# Sync each feature view
feature_views = {}
for view_name, features in feature_view_definitions.items():
    print(f"\nSyncing view: {view_name} ({len(features)} features)")
    if features:
        print(f"  Sample features: {', '.join(sorted(features)[:5])}...")
    feature_views[view_name] = sync_feature_view(
        feature_view_name=view_name,
        features_list=features,
        online_store=online_store,
        sync_config=SYNC_CONFIG
    )

# Unpack views into the original variables for downstream compatibility
all_features_view = feature_views['all_features']
odd_features_view = feature_views['odd_features']
even_features_view = feature_views['even_features']

print("\n" + "="*60)
print("Feature Views updated successfully!")
print("="*60)



# function to start and monitor sync jobs for a set of feature views
def wait_for_sync_jobs(feature_views: dict):
    """
    Starts sync jobs for all given feature views and polls until they complete.

    Args:
        feature_views (dict): A dictionary mapping view names to FeatureView objects.
    """
    import time
    import datetime as dt

    # Start a sync job for each view and store the job object
    active_jobs = {
        view_name: view.sync() for view_name, view in feature_views.items()
    }
    print(f"Started {len(active_jobs)} sync jobs: {list(active_jobs.keys())}")

    while active_jobs:
        # Iterate over a copy of keys since we modify the dict in the loop
        for view_name in list(active_jobs.keys()):
            job = active_jobs[view_name]
            view = feature_views[view_name]
            
            try:
                # Fetch the latest status of the sync job
                sync_status = view.get_sync(name=job.name).to_dict()
                
                # Check for completion by looking for an 'endTime'
                if 'endTime' in sync_status.get('runTime', {}):
                    start_time = dt.datetime.fromisoformat(sync_status['runTime']['startTime'].replace('Z', '+00:00'))
                    end_time = dt.datetime.fromisoformat(sync_status['runTime']['endTime'].replace('Z', '+00:00'))
                    duration_sec = (end_time - start_time).total_seconds()
                    rows_synced = sync_status.get('syncSummary', {}).get('rowSynced', 'N/A')
                    
                    print(f"✓ Sync for '{view_name}' completed in {duration_sec:.2f}s ({rows_synced} rows).")
                    del active_jobs[view_name] # Remove completed job from tracking
            except Exception as e:
                print(f"✗ Error checking status for '{view_name}': {e}. Removing from watch list.")
                del active_jobs[view_name]
                
        if active_jobs:
            print(f"Waiting for {len(active_jobs)} jobs to complete: {list(active_jobs.keys())}. Checking again in 10s...")
            time.sleep(10)

    print("\nAll sync jobs have been processed.")

# Start and wait for all feature view sync jobs to complete
print("\n" + "="*60)
print("Starting and monitoring sync jobs for all feature views...")
print("="*60)
# Create the dictionary of views to pass to the monitoring function
views_to_sync = {
    'all_features': all_features_view,
    'odd_features': odd_features_view,
    'even_features': even_features_view,
}
wait_for_sync_jobs(views_to_sync)
print("="*60)











# Helper function to parse the inner value of a feature struct
def _parse_feature_value(feature_struct: dict):
    """Extracts the typed value from a feature's value dictionary."""
    value_dict = feature_struct.get('value', {})
    if not value_dict:
        return None
    
    # The original code casts int64 from string to int.
    if 'int64_value' in value_dict:
        return int(value_dict['int64_value'])
    
    # For other types, just return the first value found in the dictionary.
    try:
        return next(iter(value_dict.values()))
    except StopIteration:
        return None

# Retrieve features from feature view for a single entity:
def features_to_dict(features_list: list):
    """Converts a list of raw feature structs to a simple name:value dictionary."""
    if not features_list:
        return {}
    
    return {
        f.get('name'): _parse_feature_value(f)
        for f in features_list
        if f.get('name') and f.get('name') != 'feature_timestamp'
    }

# --- Main retrieval and display logic ---
print("\n" + "="*60)
print("Single Entity Feature Retrieval...")
print("="*60)

key = ['entity-1']
views_to_read = {
    "All Features": all_features_view,
    "Odd Features": odd_features_view,
    "Even Features": even_features_view,
}

for view_name, view_obj in views_to_read.items():
    print(f"\n{view_name} View (for entity: '{key[0]}'):")
    
    try:
        # Read features from the view and get the list of feature structs
        raw_features = view_obj.read(key=key).to_dict().get('features', [])
        
        # Parse into a simple dictionary
        parsed_features = features_to_dict(raw_features)
        
        print(f"  Total features retrieved: {len(parsed_features)}")
        
        # Display all features for smaller views, and a sample for the large one
        if 'All' in view_name:
            print(f"  Sample features: {dict(list(parsed_features.items())[:5])}...")
        else:
            print(f"  Features: {parsed_features}")
            
    except Exception as e:
        print(f"  Could not retrieve features for this view. Error: {e}")

print("="*60)



# Retrieve features for multiple entities - requires bigtable serving:

# This client uses the lower-level GAPIC library for streaming performance.
# Note: The imports for these clients are assumed to be in the environment, e.g.:
# from google.cloud.aiplatform_v1.services.feature_online_store_service.client import FeatureOnlineStoreServiceClient
# from google.cloud.aiplatform_v1.types import feature_online_store_service as feature_online_store_service_pb2

from google.cloud.aiplatform_v1beta1 import FeatureOnlineStoreServiceClient
from google.cloud.aiplatform_v1beta1.types import feature_online_store_service as feature_online_store_service_pb2

data_client = FeatureOnlineStoreServiceClient(
    client_options={"api_endpoint": f"{LOCATION}-aiplatform.googleapis.com"}
)

# Define entities to request
entity_keys = [['entity-1'], ['entity-2'], ['entity-3']]

print("\n" + "="*60)
print(f"Streaming Feature Retrieval for entities: {[k[0] for k in entity_keys]}...")
print("="*60)

# Define which views to test
views_to_test = {
    'all_features': all_features_view,
    'odd_features': odd_features_view,
    'even_features': even_features_view
}

for view_name, view_obj in views_to_test.items():
    print(f"\n--- Fetching from {view_name} view ---")
    
    try:
        # Prepare one request for each entity key
        requests = [
            feature_online_store_service_pb2.StreamingFetchFeatureValuesRequest(
                feature_view=view_obj.resource_name,
                data_keys=[feature_online_store_service_pb2.FeatureViewDataKey(key=k) for k in key_list]
            )
            for key_list in entity_keys
        ]

        # Retrieve and process the streaming responses
        responses = data_client.streaming_fetch_feature_values(requests=iter(requests))
        
        print(f"Results from {view_name}:")
        for i, response in enumerate(responses):
            if response.status and response.status.code != 0:
                print(f"  Request for entity {entity_keys[i]} failed: {response.status.message}")
                continue

            for data_item in response.data:
                entity_id = data_item.data_key.key
                
                # Parse features from the response
                features = {
                    feature.name: (feature.value.string_value or
                                  feature.value.int64_value or
                                  feature.value.double_value or
                                  feature.value.bool_value or
                                  None)
                    for feature in data_item.key_values.features
                } if data_item.key_values else {}

                print(f"  Entity: {entity_id}, Features retrieved: {len(features)}")
                if features:
                    sample = dict(list(features.items())[:3])
                    print(f"    Sample features: {sample}...")
                    
    except Exception as e:
        print(f"  An error occurred while fetching from '{view_name}': {e}")

print("\n" + "="*60)







# fetch historical features - this works very poortly

features = []
for g in all_features_view.gca_resource.feature_registry_source.feature_groups:
    print(g.feature_group_id, len(g.feature_ids))
    fg = feature_store.FeatureGroup(name = g.feature_group_id)
    for f in g.feature_ids:
        print(f)
        features.append(fg.get_feature(f))

entity_df = pd.DataFrame(
    data = {
        'entity_key': ['entity-1', 'entity-2', 'entity-3'],
        'timestamp': [pd.Timestamp('2025-06-18T12:00:00')]*3
    }
)

test = offline_store.fetch_historical_feature_values(
    entity_df = entity_df,
    features = features
)
test








# Retrieve Training Data Using Feature Registry
# need: online_store, view name

# list views in feature store
for v in online_store.list_feature_views():
    print(v.name)

# retrieve view from feature store by name
target_feature_view = feature_store.FeatureView(
    name='all_features',
    feature_online_store_id=online_store.resource_name
)
print(target_feature_view.name)

# get feature groups and features for feature view
for g in target_feature_view.gca_resource.feature_registry_source.feature_groups:
    print(g.feature_group_id, len(g.feature_ids))
    # group has key attributes: gca_resource.big_query.big_query_source.input_uri, gca_resource.big_query.entity_id_columns, gca_resource.big_query.time_series.timestamp_column
    group = feature_store.FeatureGroup(name = g.feature_group_id)
    for f in g.feature_ids:
        # feature has key attributes: description, version_column_name
        feature = group.get_feature(feature_id = f)
        print(feature.gca_resource.version_column_name)













#group.gca_resource
#feature.gca_resource 







def get_training_data_from_view(
    online_store: feature_store.FeatureOnlineStore,
    feature_view_name: str,
    timestamp: str = None,
    entity_df: pd.DataFrame = None
) -> pd.DataFrame:
    """
    Fetches feature values for entities in a feature view using ML.FEATURES_AT_TIME or ML.ENTITY_FEATURES_AT_TIME.

    Args:
        online_store: The feature online store instance
        feature_view_name: Name of the feature view to retrieve data from
        timestamp: Optional timestamp in BigQuery format (e.g., '2022-06-11 10:00:00+00').
                  If not provided, uses current timestamp. Ignored if entity_df is provided.
        entity_df: Optional DataFrame with 'entity_id' and 'time' columns.
                  If provided, uses ML.ENTITY_FEATURES_AT_TIME for entity-specific timestamps.
    """
    # Determine which mode to use
    use_entity_mode = entity_df is not None

    if use_entity_mode:
        # Validate entity_df has required columns
        if 'entity_id' not in entity_df.columns or 'time' not in entity_df.columns:
            raise ValueError("entity_df must have 'entity_id' and 'time' columns")
        print(f"Building training data query for feature view: '{feature_view_name}' with {len(entity_df)} entity/timestamp pairs")
    else:
        # If no timestamp provided, use current time in BigQuery format
        if timestamp is None:
            from datetime import datetime, timezone
            current_time = datetime.now(timezone.utc)
            timestamp = current_time.strftime('%Y-%m-%d %H:%M:%S+00')
        print(f"Building training data query for feature view: '{feature_view_name}' at timestamp: {timestamp}")

    # 1. Get the feature view
    try:
        target_view = feature_store.FeatureView(
            name=feature_view_name,
            feature_online_store_id=online_store.resource_name
        )
        print(f"  Successfully retrieved feature view: {target_view.name}")
    except Exception as e:
        print(f"  Error: Could not retrieve feature view '{feature_view_name}': {e}")
        return pd.DataFrame()

    # 2. Get feature groups from the view
    feature_groups = target_view.gca_resource.feature_registry_source.feature_groups
    if not feature_groups:
        print("  No feature groups found in the view.")
        return pd.DataFrame()

    print(f"  Found {len(feature_groups)} feature group(s)")

    # 3. Build CTEs for each feature group
    cte_queries = []
    all_features = []
    entity_cte_queries = []  # Separate list for entity CTE

    # Get entity columns from first feature group (should be same for all)
    first_fg = feature_store.FeatureGroup(name=feature_groups[0].feature_group_id)
    entity_columns = first_fg.gca_resource.big_query.entity_id_columns

    # If using entity mode, create the entity table CTE
    if use_entity_mode:
        # Convert DataFrame to SQL VALUES clause
        entity_structs = []
        for _, row in entity_df.iterrows():
            # Format timestamp properly for BigQuery
            ts = pd.to_datetime(row['time'])
            ts_str = ts.strftime('%Y-%m-%d %H:%M:%S')
            # ML.ENTITY_FEATURES_AT_TIME expects 'time' column
            entity_structs.append(f"STRUCT('{row['entity_id']}' AS entity_id, TIMESTAMP '{ts_str}' AS time)")

        entity_array = ',\n      '.join(entity_structs)
        entity_cte = f"""entity_table AS (
  SELECT entity_id, time
  FROM UNNEST([
    {entity_array}
  ])
)"""
        entity_cte_queries.append(entity_cte)

    for idx, group_spec in enumerate(feature_groups):
        # Get source table/view
        fg = feature_store.FeatureGroup(name=group_spec.feature_group_id)
        table_uri = fg.gca_resource.big_query.big_query_source.input_uri
        table_id = table_uri.replace('bq://', '')

        # Build entity_id expression (concatenate if multiple columns)
        if len(entity_columns) > 1:
            entity_id_expr = "CONCAT(" + ", '-', ".join([f"CAST({col} AS STRING)" for col in entity_columns]) + ")"
        else:
            entity_id_expr = f"CAST({entity_columns[0]} AS STRING)"

        # Map feature IDs to actual BigQuery column names
        feature_mappings = []
        feature_select_list = []
        for feature_id in group_spec.feature_ids:
            try:
                feature = fg.get_feature(feature_id=feature_id)
                bq_column = feature.gca_resource.version_column_name
                # If version_column_name is set and different from feature_id, create alias
                if bq_column and bq_column != feature_id:
                    feature_select_list.append(f"{bq_column} AS {feature_id}")
                else:
                    # No mapping needed, use feature_id directly
                    feature_select_list.append(feature_id)
            except Exception:
                # If we can't get the feature metadata, assume column name matches feature_id
                feature_select_list.append(feature_id)

        # Build the feature selection string for the inner query
        features_inner = ', '.join(feature_select_list)
        # Build the feature list for the outer SELECT (just the feature IDs)
        features_outer = ', '.join(group_spec.feature_ids)

        # Build the CTE using ML.FEATURES_AT_TIME or ML.ENTITY_FEATURES_AT_TIME
        # This works for both tables and views, handles all deduplication
        # Note: Both functions return a feature_timestamp column
        if use_entity_mode:
            # Use ML.ENTITY_FEATURES_AT_TIME with entity table
            cte = f"""fg{idx} AS (
  SELECT entity_id, feature_timestamp, {features_outer}
  FROM ML.ENTITY_FEATURES_AT_TIME(
    (SELECT
       {entity_id_expr} AS entity_id,
       CAST(feature_timestamp AS TIMESTAMP) AS feature_timestamp,
       {features_inner}
     FROM `{table_id}`),
    TABLE entity_table,
    num_rows => 1,
    ignore_feature_nulls => TRUE
  )
)"""
        else:
            # Use ML.FEATURES_AT_TIME with single timestamp
            cte = f"""fg{idx} AS (
  SELECT entity_id, feature_timestamp, {features_outer}
  FROM ML.FEATURES_AT_TIME(
    (SELECT
       {entity_id_expr} AS entity_id,
       CAST(feature_timestamp AS TIMESTAMP) AS feature_timestamp,
       {features_inner}
     FROM `{table_id}`),
    time => TIMESTAMP '{timestamp}',
    num_rows => 1,
    ignore_feature_nulls => TRUE
  )
)"""
        cte_queries.append(cte)

        # Track all features for final SELECT
        all_features.extend([f"fg{idx}.{fid}" for fid in group_spec.feature_ids])

        print(f"    - Prepared CTE for group {idx}: {group_spec.feature_group_id}")

    # 4. Build final query
    # Combine entity CTE (if exists) with feature CTEs
    all_ctes = entity_cte_queries + cte_queries

    if len(cte_queries) == 1:
        # Single CTE - need to handle entity column naming even here
        if len(entity_columns) > 1:
            # Split concatenated entity_id back into original columns
            entity_select = [f"SPLIT(entity_id, '-')[OFFSET({i})] AS {col}" for i, col in enumerate(entity_columns)]
            entity_cols_str = ', '.join(entity_select)
        else:
            # Single entity column - just rename
            entity_cols_str = f"entity_id AS {entity_columns[0]}"

        # Select with renamed entity columns and feature_timestamp
        final_query = f"""
WITH {','.join(all_ctes)}
SELECT {entity_cols_str}, feature_timestamp, {', '.join(group_spec.feature_ids)}
FROM fg0
ORDER BY entity_id
"""
    else:
        # Join all CTEs on entity_id AND feature_timestamp when using entity mode
        if use_entity_mode:
            # Must join on both entity_id and feature_timestamp to maintain the entity-time relationship
            joins = ' '.join([f"FULL OUTER JOIN fg{i} USING (entity_id, feature_timestamp)" for i in range(1, len(cte_queries))])
        else:
            # For single timestamp mode, just join on entity_id
            joins = ' '.join([f"FULL OUTER JOIN fg{i} USING (entity_id)" for i in range(1, len(cte_queries))])

        # Build timestamp expression
        if use_entity_mode:
            # When joining on feature_timestamp, we can just use it directly
            timestamp_expr = "feature_timestamp"
        else:
            # For single timestamp mode, get minimum across all CTEs, ignoring NULLs
            timestamp_expressions = [f"fg{i}.feature_timestamp" for i in range(len(cte_queries))]
            # Create an array of all timestamps, filter out NULLs, and get the minimum
            timestamp_array = f"[{', '.join(timestamp_expressions)}]"
            timestamp_expr = f"""(
  SELECT MIN(ts)
  FROM UNNEST({timestamp_array}) AS ts
  WHERE ts IS NOT NULL
) AS feature_timestamp"""

        # Prepare entity column selection with split logic if needed
        if len(entity_columns) > 1:
            # Split concatenated entity_id back into original columns
            entity_select = [f"SPLIT(entity_id, '-')[OFFSET({i})] AS {col}" for i, col in enumerate(entity_columns)]
            entity_cols_str = ', '.join(entity_select)
        else:
            # Single entity column - just rename
            entity_cols_str = f"entity_id AS {entity_columns[0]}"

        # Build ORDER BY clause based on mode
        order_by = "ORDER BY entity_id, feature_timestamp" if use_entity_mode else "ORDER BY entity_id"

        final_query = f"""
WITH {','.join(all_ctes)}
SELECT {entity_cols_str}, {timestamp_expr}, {', '.join(all_features)}
FROM fg0 {joins}
{order_by}
"""

    # 5. Execute query
    try:
        df = bq_client.query(final_query).to_dataframe()
        print(f"✓ Retrieved {len(df)} rows with {len(df.columns)} columns")
        return df

    except Exception as e:
        print(f"Error executing query: {e}")
        return pd.DataFrame()

# all entities for current timestamp:
training_data = get_training_data_from_view(online_store, 'all_features')
training_data

# all entities for specific timestamp:
training_data = get_training_data_from_view(online_store, 'all_features', timestamp='2025-04-01 10:00:00+00')
training_data

# specific entities at specic timestamps:
entity_df = pd.DataFrame({
    'entity_id': ['entity-1', 'entity-1', 'entity-1', 'entity-1', 'entity-1', 'entity-1'],
    'time': ['2025-01-15 10:00:00', '2025-02-15 11:00:00', '2025-03-15 12:00:00', '2025-04-15 12:00:00', '2025-05-15 12:00:00', '2025-09-23 22:00:00']
})
training_data = get_training_data_from_view(online_store, 'all_features', entity_df=entity_df)
training_data