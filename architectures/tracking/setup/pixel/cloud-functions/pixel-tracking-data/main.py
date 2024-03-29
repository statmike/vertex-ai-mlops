import base64
import json
from google.cloud import bigquery

PROJECT_ID = 'statmike-mlops-349915'
bq = bigquery.Client(project = PROJECT_ID)

# Triggered from a message on pubsub topic, which is sent by cloud function that collect events
def pixel_tracking_data(event, context):
    
    # decode the data input, convert to python dictionary
    function_input = json.loads(
        base64.b64decode(event['data']).decode('utf-8')
    )
    
    load_job = bq.load_table_from_json(
        json_rows = [function_input],
        destination = bigquery.TableReference(
            dataset_ref = bigquery.DatasetReference(PROJECT_ID, 'pixel_tracking'),
            table_id = f'pixel-tracking-data'
        ),
        job_config = bigquery.LoadJobConfig(
            source_format = bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
            write_disposition = bigquery.WriteDisposition.WRITE_APPEND
        )
    )
    load_job.result()
