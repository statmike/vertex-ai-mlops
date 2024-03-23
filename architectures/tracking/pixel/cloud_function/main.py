import flask
from flask import abort

def tracking_pixel(request: flask.Request) -> flask.Response:
    
    repo_path = request.args.get('path', 'direct')
    repo_file = request.args.get('file', 'direct')
    
    if repo_path.startswith('statmike') and len(repo_path) < 500:
        if len(repo_file) < 500:
            print('This is where the values can be streamed to BQ with timestamp')
        else:
            return abort(406) # not acceptable
    else:
        return abort(404) # bad request
    
    return flask.send_file('pixel.png')
