"""ModelHandler implementations for local GPU and Vertex AI inference."""

import threading
import time
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Sequence

import requests
import torch
from apache_beam.ml.inference.base import ModelHandler, PredictionResult
from google.auth.transport.requests import Request as GoogleAuthRequest
import google.auth
from transformers import AutoTokenizer

from benchmark.model import BertModelWrapper, download_model_from_gcs


@dataclass
class ModelBundle:
    """Container for model + tokenizer + device."""
    model: BertModelWrapper
    tokenizer: AutoTokenizer
    device: torch.device


@dataclass
class EndpointSession:
    """Container for Vertex AI endpoint credentials and session."""
    credentials: Any
    session: requests.Session
    url: str


class LocalGPUHandler(ModelHandler):
    """Loads BERT on the worker GPU. RunInference batches and calls run_inference()."""

    def __init__(self, config):
        self.config = config
        device_str = (config.device.lower() if hasattr(config, 'device') else 'cuda')
        if device_str == 'gpu':
            device_str = 'cuda'
        self.device = torch.device(device_str)
        self._gpu_lock = threading.Lock()

    def load_model(self) -> ModelBundle:
        local_path = download_model_from_gcs(self.config.model_path)
        model = BertModelWrapper(local_path, self.config.num_labels)
        model.to(self.device).eval().half()
        tokenizer = AutoTokenizer.from_pretrained(local_path)
        # Warmup
        with torch.no_grad():
            dummy = tokenizer(["warmup"], return_tensors="pt", padding=True, truncation=True)
            input_tensor = torch.stack(
                [dummy["input_ids"], dummy["attention_mask"]], dim=1
            ).to(self.device)
            model(input_tensor)
        return ModelBundle(model, tokenizer, self.device)

    def run_inference(
        self,
        batch: Sequence[str],
        model: ModelBundle,
        inference_args: Optional[Dict[str, Any]] = None,
    ) -> Iterable[PredictionResult]:
        inference_start_ms = int(time.time() * 1000)

        encoding = model.tokenizer(
            list(batch), padding=True, truncation=True,
            max_length=self.config.max_seq_length, return_tensors="pt",
        )
        input_tensor = torch.stack(
            [encoding["input_ids"], encoding["attention_mask"]], dim=1
        ).to(model.device)

        with self._gpu_lock:
            with torch.no_grad():
                logits, gpu_time_ms = model.model(input_tensor)

        avg_ms = gpu_time_ms / len(batch)
        probs = torch.softmax(logits.float(), dim=-1)

        return [
            PredictionResult(
                example=batch[i],
                inference={
                    "class_idx": torch.argmax(probs[i]).item(),
                    "confidence": probs[i].max().item(),
                    "pure_inference_time_ms": avg_ms,
                    "inference_start_ms": inference_start_ms,
                },
            )
            for i in range(len(batch))
        ]

    def batch_elements_kwargs(self) -> Dict[str, int]:
        return {
            "min_batch_size": getattr(self.config, "min_batch_size", 1),
            "max_batch_size": getattr(self.config, "max_batch_size", 64),
        }


class VertexAIHandler(ModelHandler):
    """Sends batches to a Vertex AI endpoint. Same interface, same batching."""

    def __init__(self, config):
        self.config = config
        region = config.vertex_region
        project = config.project
        endpoint_id = config.vertex_endpoint_id
        method = "rawPredict" if getattr(config, "raw_predict", False) else "predict"
        # Dedicated endpoints must use their own DNS hostname
        dns = getattr(config, "vertex_endpoint_dns", "")
        host = dns if dns else f"{region}-aiplatform.googleapis.com"
        self.endpoint_url = (
            f"https://{host}/v1/"
            f"projects/{project}/locations/{region}/"
            f"endpoints/{endpoint_id}:{method}"
        )

    def load_model(self) -> EndpointSession:
        scopes = ["https://www.googleapis.com/auth/cloud-platform"]
        credentials, _ = google.auth.default(scopes=scopes)
        credentials.refresh(GoogleAuthRequest())
        session = requests.Session()
        return EndpointSession(credentials, session, self.endpoint_url)

    def run_inference(
        self,
        batch: Sequence[str],
        model: EndpointSession,
        inference_args: Optional[Dict[str, Any]] = None,
    ) -> Iterable[PredictionResult]:
        # Refresh credentials before timing starts to avoid counting
        # token refresh latency (100-500ms) as inference time
        if not model.credentials.valid:
            model.credentials.refresh(GoogleAuthRequest())

        inference_start_ms = int(time.time() * 1000)

        payload = {"instances": [{"text": t} for t in batch]}
        resp = model.session.post(
            model.url,
            json=payload,
            headers={
                "Authorization": f"Bearer {model.credentials.token}",
                "Content-Type": "application/json",
            },
            timeout=30,
        )
        resp.raise_for_status()
        preds = resp.json()["predictions"]

        return [
            PredictionResult(
                example=batch[i],
                inference={
                    "class_idx": preds[i].get("predicted_class"),
                    "confidence": preds[i]["confidence"],
                    "pure_inference_time_ms": preds[i]["pure_inference_time_ms"],
                    "inference_start_ms": inference_start_ms,
                },
            )
            for i in range(len(batch))
        ]

    def batch_elements_kwargs(self) -> Dict[str, int]:
        return {
            "min_batch_size": getattr(self.config, "min_batch_size", 1),
            "max_batch_size": getattr(self.config, "max_batch_size", 64),
        }
