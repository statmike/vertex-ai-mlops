"""URL parsing, scope checking, and link extraction utilities."""

import logging
import posixpath
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


def get_file_extension(url: str) -> str:
    """Extract file extension from a URL path."""
    parsed = urlparse(url)
    ext = posixpath.splitext(parsed.path)[1].lstrip(".")
    return ext.lower()


def extract_links(html: str, base_url: str) -> list[dict]:
    """Extract and categorize links from HTML content.

    Returns a list of dicts with keys: url, is_file, text.
    """
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    links = []
    seen = set()

    for tag in soup.find_all("a", href=True):
        raw_href = tag["href"].strip()
        absolute_url = urljoin(base_url, raw_href)
        normalized = normalize_url(absolute_url)

        if normalized in seen:
            continue
        seen.add(normalized)

        if not should_follow_link(base_url, normalized):
            continue

        links.append({
            "url": normalized,
            "is_file": is_downloadable_file(normalized),
            "text": tag.get_text(strip=True)[:200],
        })

    return links
