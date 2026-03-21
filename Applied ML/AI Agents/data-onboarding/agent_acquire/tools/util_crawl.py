"""URL parsing, scope checking, and link extraction utilities."""

import logging
import posixpath
import re
from urllib.parse import urljoin, urlparse

from agent_orchestrator.config import ACQUIRE_FILE_EXTENSIONS, CRAWL_SAME_ORIGIN_ONLY

logger = logging.getLogger(__name__)


def normalize_url(url: str) -> str:
    """Normalize a URL by removing fragments and trailing slashes."""
    parsed = urlparse(url)
    # Remove fragment, normalize path
    path = parsed.path.rstrip("/") or "/"
    return parsed._replace(fragment="", path=path).geturl()


def is_same_origin(base_url: str, candidate_url: str) -> bool:
    """Check if candidate_url has the same origin (scheme + host) as base_url."""
    base = urlparse(base_url)
    candidate = urlparse(candidate_url)
    return base.scheme == candidate.scheme and base.netloc == candidate.netloc


def should_follow_link(base_url: str, candidate_url: str) -> bool:
    """Determine if a link should be followed during crawling."""
    if not candidate_url or candidate_url.startswith(("#", "mailto:", "javascript:", "tel:")):
        return False

    parsed = urlparse(candidate_url)
    if parsed.scheme and parsed.scheme not in ("http", "https"):
        return False

    return not (CRAWL_SAME_ORIGIN_ONLY and not is_same_origin(base_url, candidate_url))


def is_downloadable_file(url: str) -> bool:
    """Check if a URL points to a downloadable file based on extension."""
    parsed = urlparse(url)
    path = parsed.path.lower()
    ext = posixpath.splitext(path)[1].lstrip(".")
    return ext in ACQUIRE_FILE_EXTENSIONS


# URL path segments and link text that hint at a download even without
# a file extension.  Matched case-insensitively.
_DOWNLOAD_PATH_KEYWORDS = {"download", "export", "dl"}
_DOWNLOAD_TEXT_KEYWORDS = {"download", "export", "sample download", "download sample"}


def _looks_like_download(url: str, link_text: str) -> bool:
    """Heuristic: does this URL or link text suggest a file download?

    Catches links like ``/download/sample/245`` where the path contains
    download-related segments but has no file extension.
    """
    parsed = urlparse(url)
    path_parts = set(parsed.path.lower().strip("/").split("/"))
    if path_parts & _DOWNLOAD_PATH_KEYWORDS:
        return True
    if link_text and any(kw in link_text.lower() for kw in _DOWNLOAD_TEXT_KEYWORDS):
        return True
    return False


def get_file_extension(url: str) -> str:
    """Extract file extension from a URL path."""
    parsed = urlparse(url)
    ext = posixpath.splitext(parsed.path)[1].lstrip(".")
    return ext.lower()


def extract_links(html: str, base_url: str) -> list[dict]:
    """Extract and categorize links from HTML content.

    Finds links from standard ``<a href>`` tags as well as elements with
    custom ``url`` or ``data-url`` attributes (used by some sites for
    download buttons rendered as ``<div>`` or ``<button>`` elements).

    Returns a list of dicts with keys: url, is_file, text.
    """
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    links = []
    seen = set()

    def _add_link(raw_url: str, tag) -> None:
        absolute_url = urljoin(base_url, raw_url)
        normalized = normalize_url(absolute_url)

        if normalized in seen:
            return
        seen.add(normalized)

        if not should_follow_link(base_url, normalized):
            return

        link_text = tag.get_text(strip=True)[:200]
        is_file = is_downloadable_file(normalized) or _looks_like_download(
            normalized, link_text
        )

        links.append({
            "url": normalized,
            "is_file": is_file,
            "text": link_text,
        })

    # Standard <a href="..."> links
    for tag in soup.find_all("a", href=True):
        _add_link(tag["href"].strip(), tag)

    # Elements with custom url or data-url attributes (e.g. download divs)
    for attr in ("url", "data-url", "data-href"):
        for tag in soup.find_all(attrs={attr: True}):
            raw_url = tag[attr].strip()
            if raw_url:
                _add_link(raw_url, tag)

    return links


# ---------------------------------------------------------------------------
# JSON API discovery — finds AJAX endpoints in <script> tags that return
# product/download data rendered client-side by JavaScript.
# ---------------------------------------------------------------------------

# Regex for inline AJAX URLs like `/some-path/json` or `/api/products`.
# Handles single quotes, double quotes, and backtick template literals.
# For template literals, captures up to the first `${` interpolation.
_JSON_API_PATTERN = re.compile(
    r"""(?:['"`])((?:/[a-z0-9_-]+)+/json(?:\?[^'"`$]*)?)(?:['"`$])""",
    re.IGNORECASE,
)

# Keys in JSON responses that typically hold download URLs
_DOWNLOAD_URL_KEYS = {"downloadUrl", "download_url", "downloadLink", "sampleUrl"}


def discover_json_api_urls(html: str) -> list[str]:
    """Scan ``<script>`` tags for AJAX endpoints that return JSON data.

    Returns a list of relative URL paths (e.g. ``/data-products/json?categoryId=39``).
    """
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    urls: list[str] = []
    seen: set[str] = set()

    for script in soup.find_all("script"):
        text = script.string or ""
        for match in _JSON_API_PATTERN.finditer(text):
            path = match.group(1)
            if path not in seen:
                seen.add(path)
                urls.append(path)

    return urls


def extract_download_urls_from_json(data: object, base_url: str) -> list[dict]:
    """Extract download URLs from a JSON API response.

    Walks the JSON structure looking for download-related keys.
    Returns a list of dicts with keys: url, is_file, text.
    """
    results: list[dict] = []
    seen: set[str] = set()

    def _walk(obj: object) -> None:
        if isinstance(obj, dict):
            # Check for download URL keys
            for key in _DOWNLOAD_URL_KEYS:
                raw = obj.get(key, "")
                if raw and isinstance(raw, str) and not raw.startswith("javascript:"):
                    absolute = urljoin(base_url, raw)
                    normalized = normalize_url(absolute)
                    if normalized not in seen and should_follow_link(base_url, normalized):
                        seen.add(normalized)
                        title = obj.get("title", obj.get("name", ""))
                        results.append({
                            "url": normalized,
                            "is_file": True,
                            "text": str(title)[:200] if title else "",
                        })
            # Recurse into values
            for v in obj.values():
                _walk(v)
        elif isinstance(obj, list):
            for item in obj:
                _walk(item)

    _walk(data)
    return results
