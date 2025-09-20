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
column_defs = _get_bq_column_definitions(SparseRecord2)
view_query = f"""
CREATE OR REPLACE VIEW `{{view_id}}` (
    {column_defs}
)
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
column_defs = _get_bq_column_definitions(EAVRecord)
pivot_expressions = _get_eav_pivot_expressions(EAVRecord)
view_query = f"""
CREATE OR REPLACE VIEW `{{view_id}}` (
    {column_defs}
)
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








# create Feature Groups

def create_feature_group(name: str, bq_table_id: str, description: str) -> feature_store.FeatureGroup:
    """Create or get a feature group for a BigQuery table or view."""
    try:
        # Try to get existing feature group
        fg = feature_store.FeatureGroup(name=name)
        print(f"Feature Group '{name}' already exists.")
    except Exception:
        # Create new feature group
        print(f"Creating Feature Group '{name}'...")
        fg = feature_store.FeatureGroup.create(
            name=name,
            description=description,
            source=feature_store.utils.FeatureGroupBigQuerySource(
                uri=f"bq://{bq_table_id}",
                entity_id_columns=['entity_key']
            )
        )
        print(f"Created Feature Group '{name}'")
    return fg

print("\n" + "="*60)
print("Creating Feature Groups for tables and views...")
print("="*60)

# Create feature groups for all tables
feature_groups = {}

# Tables
feature_groups['ex_shape_dense_1'] = create_feature_group(
    'ex_shape_dense_1', f"{dataset_id}.ex_shape_dense_1",
    'Dense feature table 1 with features 1-5 (boolean, integer 0-100, string High/Low, float 0.0-1.0, boolean)'
)

feature_groups['ex_shape_dense_2'] = create_feature_group(
    'ex_shape_dense_2', f"{dataset_id}.ex_shape_dense_2",
    'Dense feature table 2 with features 6-10 (boolean, integer 0-10, string High/Medium/Low, float 0.0-1.0, boolean)'
)

feature_groups['ex_shape_sparse_1'] = create_feature_group(
    'ex_shape_sparse_1', f"{dataset_id}.ex_shape_sparse_1",
    'Temporal sparse table with features 11-15, multiple timestamps per entity with increasing sparseness over time'
)

# Views
feature_groups['ex_shape_sparse_2_dense'] = create_feature_group(
    'ex_shape_sparse_2_dense', f"{dataset_id}.ex_shape_sparse_2_dense",
    'Dense view of sparse table using ML.FEATURES_AT_TIME to get latest feature values for all entities'
)

feature_groups['ex_shape_eav_1_sparse'] = create_feature_group(
    'ex_shape_eav_1_sparse', f"{dataset_id}.ex_shape_eav_1_sparse",
    'Sparse wide format view of EAV table, pivoted from entity-attribute-value to columnar format with features 21-25'
)

# Individual feature views from ex_shape_eav_2
for feature_num in range(26, 31):
    view_name = f"ex_shape_eav_2_feature_{feature_num}"
    feature_types = {
        26: 'boolean',
        27: 'integer (0-500)',
        28: 'string (Red/Blue/Green/Yellow/Purple)',
        29: 'float (-1.0 to 1.0)',
        30: 'boolean'
    }
    feature_groups[view_name] = create_feature_group(
        view_name, f"{dataset_id}.{view_name}",
        f'Individual sparse view for feature_{feature_num} ({feature_types[feature_num]}) extracted from EAV table ex_shape_eav_2'
    )

print("\n" + "="*60)
print(f"Created {len(feature_groups)} Feature Groups")
print("="*60)




# Get column descriptions from BigQuery tables/views
def get_column_descriptions(table_id: str) -> dict:
    """Retrieve column descriptions from BigQuery table schema."""
    descriptions = {}
    try:
        table = bq_client.get_table(table_id)
        for field in table.schema:
            descriptions[field.name] = field.description or f"{field.name} field"
    except Exception as e:
        print(f"  Warning: Could not retrieve schema for {table_id}: {e}")
    return descriptions

# Register features within each feature group
def register_features(feature_group, feature_names: list, descriptions: dict = None) -> dict:
    """Register features for a feature group, checking if they exist first."""
    registered_features = {}
    descriptions = descriptions or {}

    for feature_name in feature_names:
        # Skip entity_key and feature_timestamp as they are not features
        if feature_name in ['entity_key', 'feature_timestamp']:
            continue

        feature_description = descriptions.get(feature_name, f"{feature_name} feature")

        try:
            # Try to get existing feature
            feature = feature_group.get_feature(feature_id=feature_name)
            print(f"  Feature '{feature_name}' already exists in group '{feature_group.name}'")
        except Exception:
            # Create new feature with description
            feature = feature_group.create_feature(
                name=feature_name,
                description=feature_description
            )
            print(f"  Created feature '{feature_name}' in group '{feature_group.name}'")

        registered_features[feature_name] = feature

    return registered_features

print("\n" + "="*60)
print("Registering features in Feature Groups...")
print("="*60)

# Define features for each group based on their source tables
feature_definitions = {
    'ex_shape_dense_1': ['feature_1', 'feature_2', 'feature_3', 'feature_4', 'feature_5'],
    'ex_shape_dense_2': ['feature_6', 'feature_7', 'feature_8', 'feature_9', 'feature_10'],
    'ex_shape_sparse_1': ['feature_11', 'feature_12', 'feature_13', 'feature_14', 'feature_15'],
    'ex_shape_sparse_2_dense': ['feature_16', 'feature_17', 'feature_18', 'feature_19', 'feature_20'],
    'ex_shape_eav_1_sparse': ['feature_21', 'feature_22', 'feature_23', 'feature_24', 'feature_25']
}

# Add individual feature views from ex_shape_eav_2 (features 26-30)
for feature_num in range(26, 31):
    view_name = f"ex_shape_eav_2_feature_{feature_num}"
    feature_definitions[view_name] = [f'feature_{feature_num}']

# Map feature groups to their source tables/views for description retrieval
source_tables = {
    'ex_shape_dense_1': f"{dataset_id}.ex_shape_dense_1",
    'ex_shape_dense_2': f"{dataset_id}.ex_shape_dense_2",
    'ex_shape_sparse_1': f"{dataset_id}.ex_shape_sparse_1",
    'ex_shape_sparse_2_dense': f"{dataset_id}.ex_shape_sparse_2_dense",
    'ex_shape_eav_1_sparse': f"{dataset_id}.ex_shape_eav_1_sparse"
}

# Add individual feature view sources
for feature_num in range(26, 31):
    view_name = f"ex_shape_eav_2_feature_{feature_num}"
    source_tables[view_name] = f"{dataset_id}.{view_name}"

# Register features for each group with descriptions from source
all_features = {}
for group_name, feature_list in feature_definitions.items():
    if group_name in feature_groups:
        print(f"\nRegistering features for {group_name}:")

        # Get descriptions from the source table/view
        source_table = source_tables.get(group_name)
        if source_table:
            descriptions = get_column_descriptions(source_table)
        else:
            descriptions = {}

        all_features[group_name] = register_features(
            feature_groups[group_name],
            feature_list,
            descriptions
        )

print("\n" + "="*60)
print(f"Feature registration complete!")
print(f"Total features registered: {sum(len(features) for features in all_features.values())}")
print("="*60)





# Get/Create Feature Store
FEATURE_STORE_NAME = PROJECT_ID.replace('-', '_') + '_bigtable'
try:
    online_store = feature_store.FeatureOnlineStore(name = FEATURE_STORE_NAME)
    # Check if it's a BigTable serving type
    if online_store.feature_online_store_type.name == 'BIGTABLE':
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






# function to get/create a feature view in the store
def get_or_create_feature_view(feature_view_name: str, features_list: list, online_store: feature_store.FeatureOnlineStore) -> feature_store.FeatureView:
    """Create or get a feature view using registry source with format 'featuregroup.feature'."""
    try:
        feature_view = feature_store.FeatureView(
            name = feature_view_name,
            feature_online_store_id = online_store.resource_name
        )
        print(f"Feature View '{feature_view_name}' already exists.")
    except Exception:
        print(f"Creating Feature View '{feature_view_name}'...")
        feature_view = online_store.create_feature_view(
            name = feature_view_name,
            source = feature_store.utils.FeatureViewRegistrySource(
                features = features_list
            ),
            sync_config = 'TZ=America/New_York 0 0 1 * *' # Ex: first day of every month at 00:00
        )
        print(f"Feature View '{feature_view_name}' created.")
    return feature_view

# Create feature views for different feature combinations
print("\n" + "="*60)
print("Creating Feature Views...")
print("="*60)

# Build lists of features in 'featuregroup.feature' format
all_features_list = []
odd_features_list = []
even_features_list = []

# Iterate through all registered features to build the lists
for group_name, features in all_features.items():
    for feature_name in features.keys():
        feature_ref = f"{group_name}.{feature_name}"
        all_features_list.append(feature_ref)

        # Extract feature number from feature_name (e.g., 'feature_1' -> 1)
        feature_num = int(feature_name.split('_')[1])

        if feature_num % 2 == 0:
            even_features_list.append(feature_ref)
        else:
            odd_features_list.append(feature_ref)

# Create the three feature views
print(f"\nAll features list ({len(all_features_list)} features):")
print(f"  Features: {', '.join(sorted(all_features_list)[:5])}... (showing first 5)")

all_features_view = get_or_create_feature_view(
    feature_view_name="all_features",
    features_list=all_features_list,
    online_store=online_store
)

print(f"\nOdd features list ({len(odd_features_list)} features):")
print(f"  Features: {', '.join(sorted(odd_features_list)[:5])}... (showing first 5)")

odd_features_view = get_or_create_feature_view(
    feature_view_name="odd_features",
    features_list=odd_features_list,
    online_store=online_store
)

print(f"\nEven features list ({len(even_features_list)} features):")
print(f"  Features: {', '.join(sorted(even_features_list)[:5])}... (showing first 5)")

even_features_view = get_or_create_feature_view(
    feature_view_name="even_features",
    features_list=even_features_list,
    online_store=online_store
)

print("\n" + "="*60)
print("Feature Views created successfully!")
print("="*60)




# Manually sync the three feature views
print("\n" + "="*60)
print("Syncing Feature Views...")
print("="*60)

all_sync = all_features_view.sync()
odd_sync = odd_features_view.sync()
even_sync = even_features_view.sync()

sync_jobs = {
    'all_features': {'job': all_sync, 'view': all_features_view, 'completed': False},
    'odd_features': {'job': odd_sync, 'view': odd_features_view, 'completed': False},
    'even_features': {'job': even_sync, 'view': even_features_view, 'completed': False},
}

import time
import datetime as dt

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
                    dt.datetime.fromisoformat(sync_status['runTime']['endTime'].replace('Z', '+00:00'))
                    -
                    dt.datetime.fromisoformat(sync_status['runTime']['startTime'].replace('Z', '+00:00'))
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

print("="*60)




# Retrieve features from feature view for a single entity:
def features_to_dict(features_list):
    """Converts a list of feature objects to a simple dictionary."""
    if not features_list:
        return {}

    result = {}
    for feature in features_list:
        name = feature.get('name')
        if not name:
            continue

        # Skip metadata fields
        if name == 'feature_timestamp':
            continue

        # Handle features that might not have a value
        if 'value' not in feature:
            result[name] = None
            continue

        # Extract the actual value from the typed value dict
        value_dict = feature['value']
        if 'bool_value' in value_dict:
            result[name] = value_dict['bool_value']
        elif 'int64_value' in value_dict:
            result[name] = int(value_dict['int64_value'])
        elif 'double_value' in value_dict:
            result[name] = value_dict['double_value']
        elif 'string_value' in value_dict:
            result[name] = value_dict['string_value']
        else:
            result[name] = None

    return result

print("\n" + "="*60)
print("Single Entity Feature Retrieval...")
print("="*60)

# Retrieve from each of the three feature views
key = ['entity-1']

print("\nAll Features View:")
features_list = all_features_view.read(key = key).to_dict()['features']
all_features_dict = features_to_dict(features_list)
print(f"  Total features: {len(all_features_dict)}")
print(f"  Sample features: {dict(list(all_features_dict.items())[:5])}...")

print("\nOdd Features View:")
features_list = odd_features_view.read(key = key).to_dict()['features']
odd_features_dict = features_to_dict(features_list)
print(f"  Total features: {len(odd_features_dict)}")
print(f"  Features: {odd_features_dict}")

print("\nEven Features View:")
features_list = even_features_view.read(key = key).to_dict()['features']
even_features_dict = features_to_dict(features_list)
print(f"  Total features: {len(even_features_dict)}")
print(f"  Features: {even_features_dict}")

print("="*60)




# Retrieve features for multiple entities - requires bigtable serving:

data_client = FeatureOnlineStoreServiceClient(
    client_options={"api_endpoint": f"{LOCATION}-aiplatform.googleapis.com"}
)

# Which entities to request:
keys = [['entity-1'], ['entity-2'], ['entity-3']]

print("\n" + "="*60)
print("Retrieving features from Feature Views...")
print("="*60)

# Test retrieval from each of the three feature views
feature_views_to_test = {
    'all_features': all_features_view,
    'odd_features': odd_features_view,
    'even_features': even_features_view
}

for view_name, feature_view in feature_views_to_test.items():
    print(f"\n--- Fetching from {view_name} view ---")

    # Prepare the request for this feature view
    requests = []
    for key in keys:
        requests.append(
            feature_online_store_service_pb2.StreamingFetchFeatureValuesRequest(
                feature_view=feature_view.resource_name,
                data_keys=[
                    feature_online_store_service_pb2.FeatureViewDataKey(key=k)
                    for k in key
                ]
            )
        )

    # Retrieve the responses
    responses = data_client.streaming_fetch_feature_values(
        requests=iter(requests)
    )

    # Process streaming responses
    print(f"Results from {view_name}:")

    for i, response in enumerate(responses):
        # Handle errors
        if response.status and response.status.code != 0:
            print(f"  Entity {i+1} Error: {response.status.message}")
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
                              None)
                for feature in data_item.key_values.features
            } if data_item.key_values else {}

            # Show entity and feature count (full features would be too verbose)
            print(f"  Entity: {entity_id}, Features retrieved: {len(features)}")

            # Show first 3 features as sample
            if features:
                sample_features = dict(list(features.items())[:3])
                print(f"    Sample features: {sample_features}...")

print("\n" + "="*60)




# fetch historical features


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

