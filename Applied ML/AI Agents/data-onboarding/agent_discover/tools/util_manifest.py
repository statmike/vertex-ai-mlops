"""BQ manifest queries and hash comparison utilities."""

import logging

from agent_orchestrator.config import (
    BQ_META_DATASET,
    GOOGLE_CLOUD_PROJECT,
)

logger = logging.getLogger(__name__)


def get_prior_manifest(source_id: str) -> list[dict]:
    """Query the source_manifest table for prior file records for this source.

    Returns a list of dicts with keys: file_path, file_hash, classification.
    Returns empty list if table doesn't exist or source has no prior records.
    """
    if not GOOGLE_CLOUD_PROJECT:
        return []

    try:
        from google.cloud import bigquery

        client = bigquery.Client(project=GOOGLE_CLOUD_PROJECT)
        table = f"{GOOGLE_CLOUD_PROJECT}.{BQ_META_DATASET}.source_manifest"

        query = f"""
        SELECT file_path, file_hash, file_type, classification, file_size_bytes
        FROM `{table}`
        WHERE source_id = @source_id
        ORDER BY file_path
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("source_id", "STRING", source_id),
            ]
        )
        results = client.query(query, job_config=job_config).result()
        return [dict(row) for row in results]

    except Exception as e:
        logger.warning(f"Failed to query prior manifest: {e}")
        return []


def compute_changes(
    current_files: list[dict],
    prior_files: list[dict],
) -> dict:
    """Compare current files against prior manifest to detect changes.

    Args:
        current_files: List of dicts with keys: gcs_path, hash, filename.
        prior_files: List of dicts from get_prior_manifest.

    Returns:
        Dict with keys: new, modified, unchanged, removed (each a list of file paths).
    """
    prior_by_path = {f["file_path"]: f for f in prior_files}
    current_by_path = {f.get("gcs_path", ""): f for f in current_files}

    new = []
    modified = []
    unchanged = []

    for path, current in current_by_path.items():
        if path in prior_by_path:
            prior = prior_by_path[path]
            if current.get("hash") and prior.get("file_hash"):
                if current["hash"] != prior["file_hash"]:
                    modified.append(path)
                else:
                    unchanged.append(path)
            else:
                modified.append(path)  # Can't compare, assume modified
        else:
            new.append(path)

    removed = [p for p in prior_by_path if p not in current_by_path]

    return {
        "new": new,
        "modified": modified,
        "unchanged": unchanged,
        "removed": removed,
    }
