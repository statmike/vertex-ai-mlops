"""DAG: Batch inference via Vertex AI Pipelines (KFP)."""
from datetime import datetime
from airflow import models
from airflow.providers.google.cloud.operators.vertex_ai.pipeline_job import RunPipelineJobOperator

PROJECT_ID = 'statmike-mlops-349915'
REGION = 'us-central1'
PIPELINE_TEMPLATE = 'gs://statmike-mlops-349915/mlops/airflow-batch/airflow/airflow_inference_pipeline.json'
SCRIPT_GCS = 'gs://statmike-mlops-349915/mlops/airflow-batch/airflow/inference.py'
MODEL_GCS = 'gs://statmike-mlops-349915/mlops/airflow-batch/models/v1'
BQ_DATASET = 'mlops_airflow_batch'
SOURCE_TABLE = 'input_data'

with models.DAG(
    'batch_inference_kfp',
    schedule_interval=None,
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=['batch-inference', 'kfp'],
) as dag:

    run_pipeline = RunPipelineJobOperator(
        task_id='run_kfp_pipeline',
        project_id=PROJECT_ID,
        region=REGION,
        display_name='airflow-kfp-inference',
        template_path=PIPELINE_TEMPLATE,
        parameter_values={
            'project': PROJECT_ID,
            'region': REGION,
            'script_gcs_path': SCRIPT_GCS,
            'model_gcs_uri': MODEL_GCS,
            'model_name': 'distilbert',
            'bq_dataset': BQ_DATASET,
            'source_table': SOURCE_TABLE,
            'output_table': 'kfp_predictions',
            'temp_bucket': PROJECT_ID,
        },
    )
