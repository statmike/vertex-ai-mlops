# this version:
# - inputs to be json like {'instances': [[list],[list], ...]}
# - outputs in json like {'predictions': [[list],[list], ...]}
# trying to adhere to Vetex Endpoints Requirements:
# - https://cloud.google.com/vertex-ai/docs/predictions/get-online-predictions

# packages
import os
from fastapi import FastAPI, Request
import catboost
import numpy as np
from google.cloud import storage

# clients
app = FastAPI()
gcs = storage.Client()

# download the model file from GCS
paths = os.environ['AIP_STORAGE_URI'].split('/') + ['model.cbm']
bucket = gcs.bucket(paths[2])
blob = bucket.blob('/'.join(paths[3:]))
blob.download_to_filename('model.cbm')

# Load the catboost model
_model = catboost.CatBoostClassifier().load_model('model.cbm')

# get model classification levels
classes = [str(c) for c in list(_model.classes_)]

# Define function for health route
@app.get(os.environ['AIP_HEALTH_ROUTE'], status_code=200)
def health():
    return {}

# Define function for prediction route
@app.post(os.environ['AIP_PREDICT_ROUTE'])
async def predict(request: Request):
    # await the request
    body = await request.json()
    
    # parse the request
    instances = body["instances"]
    
    # get predicted probabilities
    predictions = _model.predict_proba(instances).tolist()
    
    # format predictions:
    preds = [dict(classes = classes, scores = p, predicted_class = classes[np.argmax(p)]) for p in predictions]
    
    # following outputs detail prediction info for classification:
    return {"predictions": preds}
