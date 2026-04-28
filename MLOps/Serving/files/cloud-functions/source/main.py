import json
import os
import functions_framework
from google.cloud import storage
import tempfile

# Global scope — loaded once on cold start, reused for warm invocations
model = None
tokenizer = None

def load_model():
    """Load model from GCS on first invocation."""
    global model, tokenizer
    if model is not None:
        return

    from transformers import AutoModelForSequenceClassification, AutoTokenizer
    import torch

    # Download model from GCS
    bucket_name = os.environ['MODEL_BUCKET']
    model_prefix = os.environ['MODEL_PREFIX']

    client = storage.Client()
    bucket = client.bucket(bucket_name)

    tmpdir = tempfile.mkdtemp()
    blobs = bucket.list_blobs(prefix=model_prefix)
    for blob in blobs:
        local_path = os.path.join(tmpdir, os.path.relpath(blob.name, model_prefix))
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        blob.download_to_filename(local_path)

    model = AutoModelForSequenceClassification.from_pretrained(tmpdir)
    tokenizer = AutoTokenizer.from_pretrained(tmpdir)
    model.eval()
    print(f'Model loaded from gs://{bucket_name}/{model_prefix}')

# Load model eagerly at startup so that min-instances keeps it warm.
# With lazy loading (only inside predict()), min-instances keeps the
# container alive but the model isn't loaded until the first request —
# giving the same ~30s latency as a cold start.
if os.environ.get('MODEL_BUCKET'):
    load_model()

@functions_framework.http
def predict(request):
    """HTTP Cloud Function for sentiment prediction."""
    load_model()

    import torch

    request_json = request.get_json(silent=True)
    if not request_json or 'instances' not in request_json:
        return json.dumps({'error': 'Request must include "instances" field'}), 400

    instances = request_json['instances']
    texts = [inst.get('text', '') for inst in instances]

    inputs = tokenizer(texts, return_tensors='pt', padding=True, truncation=True, max_length=128)

    with torch.no_grad():
        outputs = model(**inputs)

    probs = torch.nn.functional.softmax(outputs.logits, dim=1)
    id2label = model.config.id2label

    predictions = []
    for prob in probs:
        idx = prob.argmax().item()
        predictions.append({
            'label': id2label[idx],
            'score': round(prob[idx].item(), 4),
        })

    return json.dumps({'predictions': predictions})
