import io
import logging
import posixpath
import re
import zipfile
from urllib.parse import urlparse

import httpx
from google.adk import tools

from agent_orchestrator.config import (
    CONTEXT_FILE_EXTENSIONS,
    CRAWL_MAX_FILES,
    DATA_FILE_EXTENSIONS,
    gcs_bucket_name,
)
from agent_orchestrator.util_metadata import write_processing_log, write_source_manifest

from .util_common import compute_hash, log_tool_error
from .util_gcs import list_blobs, upload_bytes

logger = logging.getLogger(__name__)

_SUPPORTED_EXTENSIONS = DATA_FILE_EXTENSIONS + CONTEXT_FILE_EXTENSIONS

# Content-Type values that indicate a zip archive.
_ZIP_CONTENT_TYPES = {
    "application/zip",
    "application/x-zip-compressed",
    "application/x-zip",
    "application/octet-stream",  # generic binary — checked alongside magic bytes
}

# Zip-based container formats that should NOT be extracted as archives.
_ZIP_CONTAINER_EXTENSIONS = {
    "xlsx", "xlsm", "xlsb", "xls", "docx", "docm", "pptx", "pptm",
}

# Office Open XML internal paths/files — safety net for true zip archives
# that happen to contain Office XML internals.
_OOXML_INTERNAL_PREFIXES = ("xl/", "docProps/", "word/", "ppt/", "_rels/")
_OOXML_INTERNAL_FILES = {"[Content_Types].xml"}


def _resolve_filename(url: str, response: httpx.Response) -> tuple[str, str]:
    """Determine the real filename and extension for a downloaded file.

    Tries the ``Content-Disposition`` header first, then the URL path.
    If neither provides a useful extension, falls back to Content-Type
    heuristics.

    Returns (filename, extension) where extension is lowercase without dot.
    """
    filename = ""

    # 1. Try Content-Disposition header (e.g. 'attachment; filename="data.zip"')
    cd = response.headers.get("content-disposition", "")
    if cd:
        # RFC 6266 filename*= (UTF-8) or filename=
        match = re.search(r"filename\*?=['\"]?([^;'\"]+)", cd, re.IGNORECASE)
        if match:
            filename = posixpath.basename(match.group(1).strip())

    # 2. Fall back to URL path
    if not filename:
        parsed = urlparse(url)
        filename = posixpath.basename(parsed.path) or "unknown_file"

    ext = posixpath.splitext(filename)[1].lstrip(".").lower()

    # 3. If still no extension, infer from Content-Type
    if not ext:
        ct = response.headers.get("content-type", "").split(";")[0].strip().lower()
        if ct in ("application/zip", "application/x-zip-compressed", "application/x-zip"):
            ext = "zip"
            filename = f"{filename}.zip"
        elif ct == "text/csv":
            ext = "csv"
            filename = f"{filename}.csv"
        elif ct == "application/json":
            ext = "json"
            filename = f"{filename}.json"

    return filename, ext


def _is_zip_response(ext: str, response: httpx.Response) -> bool:
    """Check if a response is a zip archive by extension, Content-Type, or magic bytes."""
    if ext in _ZIP_CONTAINER_EXTENSIONS:
        return False  # zip-based format, treat as single file
    if ext == "zip":
        return True
    ct = response.headers.get("content-type", "").split(";")[0].strip().lower()
    if ct in ("application/zip", "application/x-zip-compressed", "application/x-zip"):
        return True
    # Check zip magic bytes (PK\x03\x04)
    if response.content[:4] == b"PK\x03\x04":
        return True
    return False


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

            # Skip macOS resource fork files (._* prefix)
            base_check = posixpath.basename(member.filename)
            if base_check.startswith("._"):
                skipped.append(member.filename)
                continue

            # Skip Office Open XML internal files (e.g. xl/worksheets/sheet1.xml)
            if (any(member.filename.startswith(p) for p in _OOXML_INTERNAL_PREFIXES)
                    or base_check in _OOXML_INTERNAL_FILES):
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
            file_hash = compute_hash(data)
            parent_url = url_to_parent.get(archive_url, "")
            gcs_uri = upload_bytes(data, gcs_path, metadata={
                "sha256": file_hash,
                "url": archive_url,
                "parent_url": parent_url,
                "archive_url": archive_url,
                "archive_member_path": member.filename,
            })

            extracted.append({
                "url": archive_url,
                "parent_url": parent_url,
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
        cached = []
        errors = []
        zip_extractions = 0
        bucket = gcs_bucket_name()

        # Pre-index existing GCS blobs for fast idempotency checks
        existing_files = {
            b["name"]: b for b in list_blobs(f"{staging_path}/files/")
        }
        existing_archives = {
            b["name"]: b for b in list_blobs(f"{staging_path}/archives/")
        }
        if existing_files or existing_archives:
            logger.info(
                "Idempotency check: %d existing files, %d existing archives in GCS",
                len(existing_files), len(existing_archives),
            )

        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=60.0,
            headers={"User-Agent": "data-onboarding-agent/1.0"},
        ) as client:
            for url in file_urls[:CRAWL_MAX_FILES]:
                try:
                    # Pre-resolve filename from URL for idempotency check.
                    # The real filename may change after download (via headers).
                    parsed = urlparse(url)
                    url_filename = posixpath.basename(parsed.path) or "unknown_file"
                    url_ext = posixpath.splitext(url_filename)[1].lstrip(".").lower()

                    # Quick idempotency check using URL-based filename
                    if url_ext == "zip":
                        pre_archive_path = f"{staging_path}/archives/{url_filename}"
                        if pre_archive_path in existing_archives:
                            recovered = []
                            for blob_name, blob_info in existing_files.items():
                                meta = blob_info.get("metadata", {})
                                if meta.get("archive_url") == url:
                                    entry = {
                                        "url": url,
                                        "parent_url": meta.get("parent_url", ""),
                                        "gcs_uri": f"gs://{bucket}/{blob_name}",
                                        "gcs_path": blob_name,
                                        "filename": posixpath.basename(blob_name),
                                        "size_bytes": blob_info["size"],
                                        "hash": meta.get("sha256", ""),
                                        "archive_url": url,
                                        "archive_member_path": meta.get(
                                            "archive_member_path", ""
                                        ),
                                        "archive_gcs_uri": f"gs://{bucket}/{pre_archive_path}",
                                    }
                                    recovered.append(entry)
                            cached.extend(recovered)
                            logger.info(
                                "Skipped zip %s (cached, %d extracted files)",
                                url_filename, len(recovered),
                            )
                            continue
                    else:
                        pre_file_path = f"{staging_path}/files/{url_filename}"
                        if pre_file_path in existing_files:
                            blob_info = existing_files[pre_file_path]
                            meta = blob_info.get("metadata", {})
                            cached.append({
                                "url": url,
                                "parent_url": meta.get(
                                    "parent_url", url_to_parent.get(url, "")
                                ),
                                "gcs_uri": f"gs://{bucket}/{pre_file_path}",
                                "gcs_path": pre_file_path,
                                "filename": url_filename,
                                "size_bytes": blob_info["size"],
                                "hash": meta.get("sha256", ""),
                                "archive_url": None,
                                "archive_member_path": None,
                                "archive_gcs_uri": None,
                            })
                            logger.info("Skipped %s (cached in GCS)", url_filename)
                            continue

                    # Download the file
                    response = await client.get(url)
                    response.raise_for_status()
                    data = response.content

                    # Resolve the real filename from response headers
                    filename, file_ext = _resolve_filename(url, response)
                    parent_url = url_to_parent.get(url, "")

                    # Check if this is a zip archive (by ext, content-type, or magic bytes)
                    if _is_zip_response(file_ext, response):
                        archive_path = f"{staging_path}/archives/{filename}"

                        # Check again with resolved name (may differ from URL name)
                        if archive_path in existing_archives:
                            recovered = []
                            for blob_name, blob_info in existing_files.items():
                                meta = blob_info.get("metadata", {})
                                if meta.get("archive_url") == url:
                                    recovered.append({
                                        "url": url,
                                        "parent_url": meta.get("parent_url", ""),
                                        "gcs_uri": f"gs://{bucket}/{blob_name}",
                                        "gcs_path": blob_name,
                                        "filename": posixpath.basename(blob_name),
                                        "size_bytes": blob_info["size"],
                                        "hash": meta.get("sha256", ""),
                                        "archive_url": url,
                                        "archive_member_path": meta.get(
                                            "archive_member_path", ""
                                        ),
                                        "archive_gcs_uri": f"gs://{bucket}/{archive_path}",
                                    })
                            if recovered:
                                cached.extend(recovered)
                                logger.info(
                                    "Skipped zip %s (cached, %d extracted files)",
                                    filename, len(recovered),
                                )
                                continue

                        archive_hash = compute_hash(data)
                        upload_bytes(data, archive_path, metadata={
                            "sha256": archive_hash,
                            "url": url,
                        })

                        extracted, skipped = _extract_zip(
                            data, url, staging_path, url_to_parent,
                        )
                        archive_gcs_uri = f"gs://{bucket}/{archive_path}"
                        for f in extracted:
                            f["archive_gcs_uri"] = archive_gcs_uri
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
                        file_hash = compute_hash(data)

                        gcs_uri = upload_bytes(data, gcs_path, metadata={
                            "sha256": file_hash,
                            "url": url,
                            "parent_url": parent_url,
                        })

                        downloaded.append({
                            "url": url,
                            "parent_url": parent_url,
                            "gcs_uri": gcs_uri,
                            "gcs_path": gcs_path,
                            "filename": filename,
                            "size_bytes": len(data),
                            "hash": file_hash,
                            "archive_url": None,
                            "archive_member_path": None,
                            "archive_gcs_uri": None,
                        })

                except Exception as e:
                    logger.warning(f"Failed to download {url}: {e}")
                    errors.append({"url": url, "error": str(e)})

        # Combine newly downloaded and cached files
        all_files = downloaded + cached
        tool_context.state["files_acquired"] = all_files

        # Write source manifest to BQ (classification filled later by classify_files)
        source_id = tool_context.state.get("source_id", "")
        if source_id and all_files:
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
                for f in all_files
            ]
            write_source_manifest(manifest_rows)
            write_processing_log(
                source_id, "acquire", "download_files", "completed",
                details={
                    "downloaded": len(downloaded),
                    "cached": len(cached),
                    "errors": len(errors),
                },
            )

        summary = (
            f"Download complete.\n"
            f"  Files newly downloaded: {len(downloaded)}\n"
            f"  Files cached (skipped): {len(cached)}\n"
            f"  Zip archives extracted: {zip_extractions}\n"
            f"  Errors: {len(errors)}\n"
            f"  Total files: {len(all_files)}\n"
            f"  Total size: {sum(f['size_bytes'] for f in all_files) / 1024:.1f} KB\n"
        )

        if cached:
            summary += f"\nSkipped {len(cached)} files already in GCS.\n"

        if downloaded:
            summary += "\nNewly downloaded:\n"
            for f in downloaded[:20]:
                summary += f"  - {f['filename']} ({f['size_bytes']} bytes) → {f['gcs_uri']}\n"
            if len(downloaded) > 20:
                summary += f"  ... and {len(downloaded) - 20} more\n"

        if errors:
            summary += "\nErrors:\n"
            for e in errors[:5]:
                summary += f"  - {e['url']}: {e['error']}\n"

        return summary

    except Exception as e:
        return log_tool_error("download_files", e)
