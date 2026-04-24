"""DAG: Batch inference via Dataflow (Beam RunInference)."""
from datetime import datetime
from airflow import models
from airflow.providers.apache.beam.operators.beam import BeamRunPythonPipelineOperator
from airflow.providers.google.cloud.operators.dataflow import DataflowConfiguration

PROJECT_ID = 'statmike-mlops-349915'
REGION = 'us-central1'
PIPELINE_GCS = 'gs://statmike-mlops-349915/mlops/airflow-batch/airflow/pipeline.py'
MODEL_GCS = 'gs://statmike-mlops-349915/mlops/airflow-batch/models/v1'
BQ_DATASET = 'mlops_airflow_batch'
SOURCE_TABLE = 'input_data'
OUTPUT_TABLE = 'dataflow_predictions'
GCS_BUCKET = 'statmike-mlops-349915'
SDK_CONTAINER = 'us-central1-docker.pkg.dev/statmike-mlops-349915/mlops-docker/beam-ml-sdk'

with models.DAG(
    'batch_inference_dataflow',
    schedule_interval=None,
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=['batch-inference', 'dataflow'],
) as dag:

    run_inference = BeamRunPythonPipelineOperator(
        task_id='run_dataflow_inference',
        runner='DataflowRunner',
        py_file=PIPELINE_GCS,
        pipeline_options={
            'bq_dataset': BQ_DATASET,
            'source_table': SOURCE_TABLE,
            'output_table': OUTPUT_TABLE,
            'model_gcs_uri': MODEL_GCS,
            'sdk_container_image': SDK_CONTAINER,
            'temp_location': f'gs://{GCS_BUCKET}/dataflow/temp',
            'staging_location': f'gs://{GCS_BUCKET}/dataflow/staging',
            'project': PROJECT_ID,
            'region': REGION,
            'machine_type': 'n1-standard-4',
            'num_workers': '2',
            'max_num_workers': '4',
        },
        dataflow_config=DataflowConfiguration(
            project_id=PROJECT_ID,
            location=REGION,
            job_name='airflow-dataflow-inference',
            wait_until_finished=True,
        ),
    )
