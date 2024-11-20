# this version:
# - inputs to be json like {'instances': [[list],[list], ...]}
# - outputs in json like {'predictions': [{'classes': list, 'scores': list, 'predicted_class': str}, ...]}
# trying to adhere to Vetex Endpoints Requirements:
# - https://cloud.google.com/vertex-ai/docs/predictions/get-online-predictions

# packages
import os
from fastapi import FastAPI, Request
import catboost
import numpy as np
from google.cloud import storage
from google.cloud import aiplatform
from vertexai.resources.preview import feature_store

# NAMES
PROJECT_ID = 'statmike-mlops-349915'
REGION = 'us-central1'
FS_NAME = 'statmike_mlops_349915'
FV_NAME = 'frameworks_catboost_prediction_feature_store'

# clients
app = FastAPI()
gcs = storage.Client()
aiplatform.init(project = PROJECT_ID, location = REGION)

# feature store
online_store = feature_store.FeatureOnlineStore(
    name = f"projects/{PROJECT_ID}/locations/{REGION}/featureOnlineStores/{FS_NAME}"
)
feature_view = feature_store.FeatureView(
    name = FV_NAME,
    feature_online_store_id = online_store.resource_name
)

# download the model file from GCS
paths = os.environ['AIP_STORAGE_URI'].split('/') + ['model.cbm']
bucket = gcs.bucket(paths[2])
blob = bucket.blob('/'.join(paths[3:]))
blob.download_to_filename('model.cbm')

# Load the catboost model
_model = catboost.CatBoostClassifier().load_model('model.cbm')

# get model classification levels and feature names
_classes = [str(c) for c in list(_model.classes_)]
_features = _model.feature_names_

# function to retrieve from feature store
def fs_retriever(entities):
    instances = []
    for entity_id in entities:
        features = feature_view.read(key = [entity_id]).to_dict()['features']
        feature_dict = {item['name']: list(item['value'].values())[0] for item in features}
        ordered_features = [feature_dict[name] for name in _features]
        instances.append(ordered_features)
    return instances

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
    entities = body["instances"]
    
    # get predicted probabilities
    predictions = _model.predict_proba(fs_retriever(entities)).tolist()
    
    # format predictions:
    preds = [
        dict(
            classes = _classes,
            entity_id = entities[p],
            scores = probs,
            predicted_class = _classes[np.argmax(probs)]
        ) for p, probs in enumerate(predictions)
    ]
    
    # following outputs detail prediction info for classification:
    return {"predictions": preds}
