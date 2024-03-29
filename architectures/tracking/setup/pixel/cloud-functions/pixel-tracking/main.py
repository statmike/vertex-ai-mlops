import datetime
import json
import flask
from flask import abort
from google.cloud import pubsub_v1

PROJECT_ID = 'statmike-mlops-349915'
pubsub_pubclient = pubsub_v1.PublisherClient() 

def pixel_tracking(request: flask.Request) -> flask.Response:
    
    repo_path = request.args.get('path', 'direct')
    repo_file = request.args.get('file', 'direct')
    application = request.headers.get('User-Agent')
    source = 'custom'
    
    if repo_path.startswith('statmike') and len(repo_path) < 500:
        if len(repo_file) > 5 and len(repo_file) < 500:
            data = dict(
                event_timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f %Z"),
                file_path = repo_path,
                file_name = repo_file,
                client = application,
                source = source
            )
            message = json.dumps(data).encode('utf-8')
            future = pubsub_pubclient.publish(
                f'projects/{PROJECT_ID}/topics/pixel-tracking-data',
                message,
                trigger = 'manual'
            )
        else:
            return abort(406) # not acceptable
    else:
        return abort(404) # bad request
    
    return flask.send_file('pixel.png', max_age=0)
