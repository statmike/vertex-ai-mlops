import os, json, tempfile
from fastapi import FastAPI, Request
from google.cloud import storage
from transformers import AutoModelForSequenceClassification, AutoTokenizer
import torch

app = FastAPI()

# ── Load model at startup ──────────────────────────────────────────
MODEL_DIR = tempfile.mkdtemp()
ARTIFACT_URI = os.environ.get('AIP_STORAGE_URI', '')

if ARTIFACT_URI:
    # Download from GCS
    client = storage.Client()
    prefix = ARTIFACT_URI.replace('gs://', '').split('/', 1)
    bucket = client.bucket(prefix[0])
    blobs = bucket.list_blobs(prefix=prefix[1] if len(prefix) > 1 else '')
    for blob in blobs:
        dest = os.path.join(
            MODEL_DIR,
            os.path.relpath(blob.name, prefix[1] if len(prefix) > 1 else ''),
        )
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        blob.download_to_filename(dest)

model = AutoModelForSequenceClassification.from_pretrained(MODEL_DIR)
tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)
model.eval()
LABELS = list(model.config.id2label.values())


# ── Routes ──────────────────────────────────────────────────────────
@app.get(os.environ.get('AIP_HEALTH_ROUTE', '/health'), status_code=200)
def health():
    return {}


@app.post(os.environ.get('AIP_PREDICT_ROUTE', '/predict'))
async def predict(request: Request):
    body = await request.json()
    instances = body['instances']

    texts = [inst['text'] if isinstance(inst, dict) else inst for inst in instances]

    inputs = tokenizer(texts, padding=True, truncation=True, return_tensors='pt')
    with torch.no_grad():
        logits = model(**inputs).logits
    probs = torch.softmax(logits, dim=-1)
    scores, indices = probs.max(dim=-1)

    predictions = []
    for score, idx in zip(scores, indices):
        predictions.append({
            'label': LABELS[idx.item()],
            'score': round(score.item(), 6),
        })
    return {'predictions': predictions}
