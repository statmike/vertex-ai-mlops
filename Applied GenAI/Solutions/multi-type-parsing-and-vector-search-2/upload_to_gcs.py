"""Upload generated files to GCS with content-specific metadata."""

from google.cloud import storage
from pathlib import Path
from config import PROJECT_ID, GCS_BUCKET, GCS_ROOT
import json

# --- GCS client ---

client = storage.Client(project=PROJECT_ID)
bucket = client.bucket(GCS_BUCKET)

# --- Metadata builders per file type ---

def reddit_metadata(file_path: Path) -> dict:
    data = json.loads(file_path.read_text())
    return {
        "source-type": "reddit",
        "file-format": "json",
        "content-domain": "forecasting",
        "subreddit": data.get("subreddit", ""),
        "thread-title": data.get("title", ""),
        "comment-count": str(len(data.get("comments", []))),
    }

def zoom_metadata(file_path: Path) -> dict:
    lines = file_path.read_text().splitlines()
    cue_count = sum(1 for l in lines if "-->" in l)
    return {
        "source-type": "zoom-transcript",
        "file-format": "vtt",
        "content-domain": "forecasting",
        "cue-count": str(cue_count),
    }

def pdf_metadata(file_path: Path) -> dict:
    return {
        "source-type": "web-documentation",
        "file-format": "pdf",
        "content-domain": "forecasting",
    }

# --- Upload files with metadata ---

file_configs = [
    {"folder": "generated_reddit", "content_type": "application/json", "metadata_fn": reddit_metadata},
    {"folder": "generated_zoom",   "content_type": "text/vtt",         "metadata_fn": zoom_metadata},
    {"folder": "generated_pdf",    "content_type": "application/pdf",  "metadata_fn": pdf_metadata},
]

for fc in file_configs:
    folder = Path(fc["folder"])
    if not folder.exists():
        print(f"Skipping {folder} (not found)")
        continue

    for file_path in sorted(folder.iterdir()):
        if file_path.is_dir():
            continue

        gcs_path = f"{GCS_ROOT}/{fc['folder']}/{file_path.name}"
        blob = bucket.blob(gcs_path)
        blob.metadata = fc["metadata_fn"](file_path)
        blob.upload_from_filename(str(file_path), content_type=fc["content_type"])
        print(f"Uploaded: gs://{GCS_BUCKET}/{gcs_path}  metadata={blob.metadata}")
