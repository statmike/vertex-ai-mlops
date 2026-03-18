import io
import logging
import posixpath
import zipfile
from urllib.parse import urlparse

import httpx
from google.adk import tools

from agent_orchestrator.config import (
    CONTEXT_FILE_EXTENSIONS,
    CRAWL_MAX_FILES,
    DATA_FILE_EXTENSIONS,
)
from agent_orchestrator.util_metadata import write_processing_log, write_source_manifest

from .util_common import compute_hash, log_tool_error
from .util_gcs import upload_bytes

logger = logging.getLogger(__name__)

_SUPPORTED_EXTENSIONS = DATA_FILE_EXTENSIONS + CONTEXT_FILE_EXTENSIONS


def _extract_zip(
    zip_data: bytes,
    archive_url: str,
    staging_path: str,
    url_to_parent: dict[str, str],
) -> tuple[list[dict], list[str]]:
    """Extract supported files from a zip archive and upload each to GCS.

    Returns (extracted, skipped) where *extracted* is a list of file-info dicts
    compatible with ``files_acquired`` and *skipped* lists member paths that
    were ignored (unsupported extension, directory, nested zip).
    """
    extracted: list[dict] = []
    skipped: list[str] = []
    used_names: dict[str, int] = {}

    try:
        zf = zipfile.ZipFile(io.BytesIO(zip_data))
    except zipfile.BadZipFile as exc:
        logger.warning("Bad zip from %s: %s", archive_url, exc)
        return [], [f"ERROR: bad zip – {exc}"]

    try:
        for member in zf.infolist():
            if member.is_dir():
                skipped.append(member.filename)
                continue

            ext = posixpath.splitext(member.filename)[1].lstrip(".").lower()
            if ext not in _SUPPORTED_EXTENSIONS:
                skipped.append(member.filename)
                continue

            # Flatten to basename, resolving collisions
            base = posixpath.basename(member.filename)
            if base in used_names:
                used_names[base] += 1
                stem, dot_ext = posixpath.splitext(base)
                base = f"{stem}_{used_names[base]}{dot_ext}"
            else:
                used_names[base] = 0

            try:
                data = zf.read(member)
            except RuntimeError as exc:
                # e.g. password-protected entry
                logger.warning("Cannot read %s in %s: %s", member.filename, archive_url, exc)
                skipped.append(member.filename)
                continue

            gcs_path = f"{staging_path}/files/{base}"
            gcs_uri = upload_bytes(data, gcs_path)
            file_hash = compute_hash(data)

            extracted.append({
                "url": archive_url,
                "parent_url": url_to_parent.get(archive_url, ""),
                "gcs_uri": gcs_uri,
                "gcs_path": gcs_path,
                "filename": base,
                "size_bytes": len(data),
                "hash": file_hash,
                "archive_url": archive_url,
                "archive_member_path": member.filename,
            })
    finally:
        zf.close()

    return extracted, skipped


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

        # Build URL → parent_url lookup from crawl_graph
        crawl_graph = tool_context.state.get("crawl_graph", [])
        url_to_parent = {
            edge["url"]: edge.get("parent_url", "")
            for edge in crawl_graph
        }

        downloaded = []
        errors = []
        zip_extractions = 0

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

                    # Determine filename and extension from URL
                    parsed = urlparse(url)
                    filename = posixpath.basename(parsed.path) or "unknown_file"
                    file_ext = posixpath.splitext(filename)[1].lstrip(".").lower()

                    if file_ext == "zip":
                        extracted, skipped = _extract_zip(
                            data, url, staging_path, url_to_parent,
                        )
                        downloaded.extend(extracted)
                        if extracted:
                            zip_extractions += 1
                        if skipped:
                            logger.info(
                                "Zip %s: extracted %d, skipped %d (%s)",
                                url, len(extracted), len(skipped),
                                ", ".join(skipped[:5]),
                            )
                    else:
                        # Regular file
                        gcs_path = f"{staging_path}/files/{filename}"
                        gcs_uri = upload_bytes(data, gcs_path)
                        file_hash = compute_hash(data)

                        downloaded.append({
                            "url": url,
                            "parent_url": url_to_parent.get(url, ""),
                            "gcs_uri": gcs_uri,
                            "gcs_path": gcs_path,
                            "filename": filename,
                            "size_bytes": len(data),
                            "hash": file_hash,
                            "archive_url": None,
                            "archive_member_path": None,
                        })

                except Exception as e:
                    logger.warning(f"Failed to download {url}: {e}")
                    errors.append({"url": url, "error": str(e)})

        # Store in state
        tool_context.state["files_acquired"] = downloaded

        # Write source manifest to BQ (classification filled later by classify_files)
        source_id = tool_context.state.get("source_id", "")
        if source_id and downloaded:
            manifest_rows = [
                {
                    "source_id": source_id,
                    "file_path": f["gcs_path"],
                    "file_hash": f["hash"],
                    "file_size_bytes": f["size_bytes"],
                    "file_type": posixpath.splitext(f["filename"])[1].lstrip("."),
                    "classification": "",
                    "original_url": f.get("archive_url") or f["url"],
                }
                for f in downloaded
            ]
            write_source_manifest(manifest_rows)
            write_processing_log(
                source_id, "acquire", "download_files", "completed",
                details={"downloaded": len(downloaded), "errors": len(errors)},
            )

        summary = (
            f"Download complete.\n"
            f"  Files downloaded: {len(downloaded)}\n"
            f"  Zip archives extracted: {zip_extractions}\n"
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
