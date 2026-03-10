"""BertModelWrapper and GCS model download utility."""

import os
import subprocess
import time
from pathlib import Path

import torch
import torch.nn as nn
from transformers import DistilBertModel


class BertModelWrapper(nn.Module):
    """DistilBERT with a classification head. Times forward pass for benchmarking."""

    def __init__(self, model_path: str, num_labels: int):
        super().__init__()
        self.bert = DistilBertModel.from_pretrained(model_path)
        hidden_size = self.bert.config.hidden_size
        self.classifier = nn.Linear(hidden_size, num_labels)
        # Load fine-tuned classifier head if available
        classifier_path = os.path.join(model_path, "classifier_head.pt")
        if os.path.exists(classifier_path):
            self.classifier.load_state_dict(torch.load(classifier_path, map_location="cpu"))

    def forward(self, input_tensor: torch.Tensor):
        """Run inference and return (logits, gpu_time_ms).

        Args:
            input_tensor: shape (batch, 2, seq_len) where dim 1 is [input_ids, attention_mask]

        Returns:
            Tuple of (logits, gpu_time_ms) where gpu_time_ms is the pure inference time.
        """
        input_ids = input_tensor[:, 0, :].long()
        attention_mask = input_tensor[:, 1, :].long()

        start = time.perf_counter()
        outputs = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        cls_output = outputs.last_hidden_state[:, 0, :]
        logits = self.classifier(cls_output)
        if input_tensor.is_cuda:
            torch.cuda.synchronize()
        gpu_time_ms = (time.perf_counter() - start) * 1000.0

        return logits, gpu_time_ms


def download_model_from_gcs(gcs_path: str, local_dir: str = "/tmp/bert_model") -> str:
    """Download model artifacts from GCS to a local directory.

    Args:
        gcs_path: GCS path like gs://bucket/bert-model/
        local_dir: Local directory to download to.

    Returns:
        Local path to the downloaded model.
    """
    if os.path.exists(os.path.join(local_dir, "config.json")):
        return local_dir

    Path(local_dir).mkdir(parents=True, exist_ok=True)

    from google.cloud import storage

    # Parse gs://bucket/prefix/
    path = gcs_path.replace("gs://", "")
    bucket_name = path.split("/")[0]
    prefix = "/".join(path.split("/")[1:]).rstrip("/")

    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blobs = list(bucket.list_blobs(prefix=prefix))

    for blob in blobs:
        if blob.name.endswith("/"):
            continue
        # Get just the filename (strip the prefix)
        rel_path = blob.name[len(prefix):].lstrip("/")
        if not rel_path:
            continue
        local_path = os.path.join(local_dir, rel_path)
        Path(os.path.dirname(local_path)).mkdir(parents=True, exist_ok=True)
        blob.download_to_filename(local_path)

    return local_dir
