"""DAG: Batch inference via Dataproc Serverless."""
from datetime import datetime
from airflow import models
from airflow.providers.google.cloud.operators.dataproc import DataprocCreateBatchOperator

PROJECT_ID = 'statmike-mlops-349915'
REGION = 'us-central1'
SCRIPT_GCS = 'gs://statmike-mlops-349915/mlops/airflow-batch/airflow/inference.py'
MODEL_GCS = 'gs://statmike-mlops-349915/mlops/airflow-batch/models/v1'
BQ_DATASET = 'mlops_airflow_batch'
SOURCE_TABLE = 'input_data'
OUTPUT_TABLE = 'dataproc_predictions'

with models.DAG(
    'batch_inference_dataproc',
    schedule_interval=None,
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=['batch-inference', 'dataproc'],
) as dag:

    run_inference = DataprocCreateBatchOperator(
        task_id='run_dataproc_inference',
        region=REGION,
        project_id=PROJECT_ID,
        batch={
            'pyspark_batch': {
                'main_python_file_uri': SCRIPT_GCS,
                'args': [
                    '--project', PROJECT_ID,
                    '--bq_dataset', BQ_DATASET,
                    '--source_table', SOURCE_TABLE,
                    '--output_table', OUTPUT_TABLE,
                    '--model_gcs_uri', MODEL_GCS,
                    '--model_name', 'distilbert',
                    '--temp_bucket', PROJECT_ID,
                ],
            },
            'runtime_config': {'version': '2.2'},
        },
        batch_id='airflow-dp-' + '{{ ts_nodash | lower }}',
    )
