import threading
import datetime
import flask
from flask import abort
from google.cloud import bigquery

PROJECT_ID = 'statmike-mlops-349915'
bq = bigquery.Client(project = PROJECT_ID)

def loadBQ(repo_path, repo_file):
    
    rows = [dict(
        event_timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f %Z"),
        file_path = repo_path,
        file_name = repo_file
    )]
    
    load_job = bq.load_table_from_json(
        json_rows = rows,
        destination = bigquery.TableReference(
            dataset_ref = bigquery.DatasetReference(PROJECT_ID, 'tracking'),
            table_id = f'pixel_event_capture'
        ),
        job_config = bigquery.LoadJobConfig(
            source_format = bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
            write_disposition = bigquery.WriteDisposition.WRITE_APPEND
        )
    )
    load_job.result()

def tracking_pixel(request: flask.Request) -> flask.Response:
    
    repo_path = request.args.get('path', 'direct')
    repo_file = request.args.get('file', 'direct')
    
    if repo_path.startswith('statmike') and len(repo_path) < 500:
        if len(repo_file) > 5 and len(repo_file) < 500:
            thread = threading.Thread(target = loadBQ, args = (repo_path, repo_file))
            thread.start()
        else:
            return abort(406) # not acceptable
    else:
        return abort(404) # bad request
    
    return flask.send_file('pixel.png')
