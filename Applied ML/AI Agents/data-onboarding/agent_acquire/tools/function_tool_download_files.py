import logging
import posixpath
from urllib.parse import urlparse

import httpx
from google.adk import tools

from agent_orchestrator.config import CRAWL_MAX_FILES

from .util_common import compute_hash, log_tool_error
from .util_gcs import upload_bytes

logger = logging.getLogger(__name__)


async def download_files(
    tool_context: tools.ToolContext,
) -> str:
    """
    Download discovered file URLs to GCS staging.

    Reads `discovered_file_urls` and `gcs_staging_path` from state,
    downloads each file via HTTP, and uploads to GCS under the staging path.
    Computes SHA-256 hashes for change detection.

    Args:
        tool_context: The ADK tool context for accessing shared state.

    Returns:
        A summary of downloaded files, or an error message.
    """
    try:
        file_urls = tool_context.state.get("discovered_file_urls", [])
        staging_path = tool_context.state.get("gcs_staging_path", "")
        if not file_urls:
            return "No file URLs to download. Run crawl_url first."
        if not staging_path:
            return "Error: gcs_staging_path not set in state."

        downloaded = []
        errors = []

        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=60.0,
            headers={"User-Agent": "data-onboarding-agent/1.0"},
        ) as client:
            for url in file_urls[:CRAWL_MAX_FILES]:
                try:
                    response = await client.get(url)
                    response.raise_for_status()
                    data = response.content

                    # Determine filename from URL
                    parsed = urlparse(url)
                    filename = posixpath.basename(parsed.path) or "unknown_file"

                    # Upload to GCS
                    gcs_path = f"{staging_path}/files/{filename}"
                    gcs_uri = upload_bytes(data, gcs_path)
                    file_hash = compute_hash(data)

                    downloaded.append({
                        "url": url,
                        "gcs_uri": gcs_uri,
                        "gcs_path": gcs_path,
                        "filename": filename,
                        "size_bytes": len(data),
                        "hash": file_hash,
                    })

                except Exception as e:
                    logger.warning(f"Failed to download {url}: {e}")
                    errors.append({"url": url, "error": str(e)})

        # Store in state
        tool_context.state["files_acquired"] = downloaded

        summary = (
            f"Download complete.\n"
            f"  Files downloaded: {len(downloaded)}\n"
            f"  Errors: {len(errors)}\n"
            f"  Total size: {sum(f['size_bytes'] for f in downloaded) / 1024:.1f} KB\n"
        )

        if downloaded:
            summary += "\nDownloaded files:\n"
            for f in downloaded[:20]:
                summary += f"  - {f['filename']} ({f['size_bytes']} bytes) → {f['gcs_uri']}\n"

        if errors:
            summary += "\nErrors:\n"
            for e in errors[:5]:
                summary += f"  - {e['url']}: {e['error']}\n"

        return summary

    except Exception as e:
        return log_tool_error("download_files", e)
