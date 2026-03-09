import logging
import re

import httpx
from google.adk import tools

from .util_common import log_tool_error
from .util_gcs import upload_string

logger = logging.getLogger(__name__)


def _html_to_markdown(html: str, url: str) -> str:
    """Convert HTML to a simple markdown representation.

    Extracts title, headings, paragraphs, lists, and tables.
    Not a full converter — just enough to capture page context.
    """
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")

    # Remove script and style elements
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    lines = [f"# Source: {url}\n"]

    # Title
    title = soup.find("title")
    if title:
        lines.append(f"## {title.get_text(strip=True)}\n")

    # Process body content
    body = soup.find("body") or soup
    for element in body.find_all(["h1", "h2", "h3", "h4", "p", "li", "td", "th", "pre", "code"]):
        text = element.get_text(strip=True)
        if not text:
            continue

        tag = element.name
        if tag == "h1":
            lines.append(f"\n## {text}\n")
        elif tag == "h2":
            lines.append(f"\n### {text}\n")
        elif tag in ("h3", "h4"):
            lines.append(f"\n#### {text}\n")
        elif tag == "li":
            lines.append(f"- {text}")
        elif tag in ("pre", "code"):
            lines.append(f"\n```\n{text}\n```\n")
        else:
            lines.append(text)

    content = "\n".join(lines)
    # Collapse multiple blank lines
    content = re.sub(r"\n{3,}", "\n\n", content)
    return content


async def extract_page_content(
    tool_context: tools.ToolContext,
) -> str:
    """
    Extract content from discovered HTML pages and store as markdown context files.

    Reads `discovered_page_urls` and `gcs_staging_path` from state,
    fetches each page, converts to markdown, and uploads to GCS
    under the context/ subdirectory.

    Args:
        tool_context: The ADK tool context for accessing shared state.

    Returns:
        A summary of extracted context files, or an error message.
    """
    try:
        page_urls = tool_context.state.get("discovered_page_urls", [])
        staging_path = tool_context.state.get("gcs_staging_path", "")

        if not page_urls:
            return "No page URLs to extract. Run crawl_url first."
        if not staging_path:
            return "Error: gcs_staging_path not set in state."

        extracted = []

        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=30.0,
            headers={"User-Agent": "data-onboarding-agent/1.0"},
        ) as client:
            for i, url in enumerate(page_urls):
                try:
                    response = await client.get(url)
                    response.raise_for_status()

                    markdown = _html_to_markdown(response.text, url)

                    # Upload to GCS
                    filename = f"page_{i:03d}.md"
                    gcs_path = f"{staging_path}/context/{filename}"
                    gcs_uri = upload_string(
                        markdown, gcs_path, content_type="text/markdown"
                    )

                    extracted.append({
                        "url": url,
                        "gcs_uri": gcs_uri,
                        "gcs_path": gcs_path,
                        "filename": filename,
                        "size_chars": len(markdown),
                    })

                except Exception as e:
                    logger.warning(f"Failed to extract content from {url}: {e}")

        tool_context.state["context_files_acquired"] = extracted

        # Merge into files_acquired for downstream
        existing = list(tool_context.state.get("files_acquired", []))
        for ctx_file in extracted:
            existing.append({
                "gcs_uri": ctx_file["gcs_uri"],
                "gcs_path": ctx_file["gcs_path"],
                "filename": ctx_file["filename"],
                "size_bytes": ctx_file["size_chars"],
                "hash": "",
                "url": ctx_file["url"],
            })
        tool_context.state["files_acquired"] = existing

        return (
            f"Page content extraction complete.\n"
            f"  Pages processed: {len(extracted)}\n"
            f"  Context files created: {len(extracted)}\n"
            + "\n".join(
                f"  - {e['filename']} ({e['size_chars']} chars) from {e['url']}"
                for e in extracted[:10]
            )
        )

    except Exception as e:
        return log_tool_error("extract_page_content", e)
