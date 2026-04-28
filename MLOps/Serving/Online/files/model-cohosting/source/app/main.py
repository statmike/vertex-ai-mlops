import os
from fastapi import FastAPI, Request
from transformers import pipeline
from google.cloud import storage

app = FastAPI()

# Download model files from GCS (set by AIP_STORAGE_URI)
gcs = storage.Client()
storage_uri = os.environ['AIP_STORAGE_URI']
parts = storage_uri.replace('gs://', '').split('/', 1)
bucket = gcs.bucket(parts[0])
prefix = parts[1] if len(parts) > 1 else ''

model_dir = '/tmp/model'
os.makedirs(model_dir, exist_ok=True)
for blob in bucket.list_blobs(prefix=prefix):
    rel = blob.name[len(prefix):].lstrip('/')
    if rel:
        local = os.path.join(model_dir, rel)
        os.makedirs(os.path.dirname(local), exist_ok=True)
        blob.download_to_filename(local)

# Load the sentiment analysis pipeline
classifier = pipeline('sentiment-analysis', model=model_dir, tokenizer=model_dir)


@app.get(os.environ['AIP_HEALTH_ROUTE'], status_code=200)
def health():
    return {}


@app.post(os.environ['AIP_PREDICT_ROUTE'])
async def predict(request: Request):
    body = await request.json()
    instances = body['instances']
    results = classifier(instances)
    return {
        'predictions': [
            {'label': r['label'], 'score': round(r['score'], 6)}
            for r in results
        ]
    }
