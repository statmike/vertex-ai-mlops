"""Flask endpoint for Vertex AI serving. Uses the same BertModelWrapper as Dataflow workers."""

import os
import threading

import torch
from flask import Flask, jsonify, request
from transformers import AutoTokenizer

from benchmark.model import BertModelWrapper, download_model_from_gcs

app = Flask(__name__)

# Globals loaded lazily in the worker process (not at import time to avoid CUDA fork issues)
MODEL = None
TOKENIZER = None
DEVICE = None
CATEGORY_NAMES = None
_model_lock = threading.Lock()


def _ensure_model_loaded():
    """Lazy-load model on first request (inside the worker process, not the master)."""
    global MODEL, TOKENIZER, DEVICE, CATEGORY_NAMES

    if MODEL is not None:
        return

    with _model_lock:
        if MODEL is not None:
            return

        # Vertex AI sets AIP_STORAGE_URI to GCS path of artifact-uri contents
        model_path = os.environ.get("AIP_STORAGE_URI", os.environ.get("MODEL_PATH", "/model"))
        if model_path.startswith("gs://"):
            print(f"Downloading model from {model_path}...", flush=True)
            model_path = download_model_from_gcs(model_path, "/tmp/bert_model")

        num_labels = int(os.environ.get("NUM_LABELS", "3"))
        category_str = os.environ.get("CATEGORY_NAMES", "INCOME_WAGE,INCOME_GIG,EXPENSE")
        CATEGORY_NAMES = category_str.split(",")

        DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        MODEL = BertModelWrapper(model_path, num_labels)
        MODEL.to(DEVICE).eval().half()
        TOKENIZER = AutoTokenizer.from_pretrained(model_path)

        # Warmup
        with torch.no_grad():
            dummy = TOKENIZER(["warmup"], return_tensors="pt", padding=True, truncation=True)
            input_tensor = torch.stack(
                [dummy["input_ids"], dummy["attention_mask"]], dim=1
            ).to(DEVICE)
            MODEL(input_tensor)

        print(f"Model loaded on {DEVICE}, num_labels={num_labels}, categories={CATEGORY_NAMES}", flush=True)


@app.route("/predict", methods=["POST"])
def predict():
    _ensure_model_loaded()

    data = request.get_json()
    instances = data.get("instances", [])
    texts = [inst["text"] for inst in instances]

    max_seq_length = int(os.environ.get("MAX_SEQ_LENGTH", "128"))
    encoding = TOKENIZER(
        texts, padding=True, truncation=True,
        max_length=max_seq_length, return_tensors="pt",
    )
    input_tensor = torch.stack(
        [encoding["input_ids"], encoding["attention_mask"]], dim=1
    ).to(DEVICE)

    with torch.no_grad():
        logits, gpu_time_ms = MODEL(input_tensor)

    avg_ms = gpu_time_ms / len(texts)
    probs = torch.softmax(logits.float(), dim=-1)

    predictions = []
    for i in range(len(texts)):
        class_idx = torch.argmax(probs[i]).item()
        predictions.append({
            "predicted_class": CATEGORY_NAMES[class_idx] if class_idx < len(CATEGORY_NAMES) else str(class_idx),
            "confidence": round(probs[i].max().item(), 4),
            "pure_inference_time_ms": round(avg_ms, 2),
        })

    return jsonify({"predictions": predictions})


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy"})


# Vertex AI custom container uses AIP_HTTP_PORT
if __name__ == "__main__":
    _ensure_model_loaded()
    port = int(os.environ.get("AIP_HTTP_PORT", "8080"))
    app.run(host="0.0.0.0", port=port)
