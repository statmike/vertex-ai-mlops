"""DAG: Batch inference via Vertex AI Batch Prediction."""
from datetime import datetime
from airflow import models
from airflow.providers.google.cloud.operators.vertex_ai.batch_prediction_job import (
    CreateBatchPredictionJobOperator,
)

PROJECT_ID = 'statmike-mlops-349915'
REGION = 'us-central1'
MODEL_RESOURCE = 'projects/1026793852137/locations/us-central1/models/4993857568544653312'
BQ_DATASET = 'mlops_airflow_batch'
SOURCE_TABLE = 'input_data'

with models.DAG(
    'batch_inference_vertex_batch',
    schedule_interval=None,
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=['batch-inference', 'vertex-ai'],
) as dag:

    batch_predict = CreateBatchPredictionJobOperator(
        task_id='run_vertex_batch',
        project_id=PROJECT_ID,
        region=REGION,
        model_name=MODEL_RESOURCE,
        job_display_name='airflow-vertex-batch',
        bigquery_source=f'bq://{PROJECT_ID}.{BQ_DATASET}.{SOURCE_TABLE}',
        bigquery_destination_prefix=f'bq://{PROJECT_ID}.{BQ_DATASET}',
        machine_type='n1-standard-4',
        starting_replica_count=1,
        max_replica_count=1,
    )
