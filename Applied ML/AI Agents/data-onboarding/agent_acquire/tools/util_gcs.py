"""GCS upload/download/list utilities."""

import logging

from google.cloud import storage

from agent_orchestrator.config import gcs_bucket_name

logger = logging.getLogger(__name__)


def _get_client() -> storage.Client:
    """Create a GCS client."""
    return storage.Client()


def upload_bytes(data: bytes, gcs_path: str) -> str:
    """Upload bytes to a GCS path. Returns the full gs:// URI."""
    client = _get_client()
    bucket = client.bucket(gcs_bucket_name())
    blob = bucket.blob(gcs_path)
    blob.upload_from_string(data)
    return f"gs://{gcs_bucket_name()}/{gcs_path}"


def upload_string(text: str, gcs_path: str, content_type: str = "text/plain") -> str:
    """Upload a string to a GCS path. Returns the full gs:// URI."""
    client = _get_client()
    bucket = client.bucket(gcs_bucket_name())
    blob = bucket.blob(gcs_path)
    blob.upload_from_string(text, content_type=content_type)
    return f"gs://{gcs_bucket_name()}/{gcs_path}"


def download_bytes(gcs_path: str) -> bytes:
    """Download bytes from a GCS path (without gs:// prefix)."""
    client = _get_client()
    bucket = client.bucket(gcs_bucket_name())
    blob = bucket.blob(gcs_path)
    return blob.download_as_bytes()


def list_blobs(prefix: str) -> list[dict]:
    """List blobs under a GCS prefix. Returns list of dicts with name, size, updated."""
    client = _get_client()
    bucket = client.bucket(gcs_bucket_name())
    blobs = bucket.list_blobs(prefix=prefix)
    results = []
    for blob in blobs:
        results.append({
            "name": blob.name,
            "size": blob.size,
            "updated": blob.updated.isoformat() if blob.updated else None,
            "content_type": blob.content_type,
        })
    return results


def blob_exists(gcs_path: str) -> bool:
    """Check if a blob exists at the given GCS path."""
    client = _get_client()
    bucket = client.bucket(gcs_bucket_name())
    blob = bucket.blob(gcs_path)
    return blob.exists()


def copy_blob(source_path: str, dest_path: str) -> str:
    """Copy a blob from source to dest within the same bucket. Returns dest gs:// URI."""
    client = _get_client()
    bucket = client.bucket(gcs_bucket_name())
    source_blob = bucket.blob(source_path)
    bucket.copy_blob(source_blob, bucket, dest_path)
    return f"gs://{gcs_bucket_name()}/{dest_path}"
