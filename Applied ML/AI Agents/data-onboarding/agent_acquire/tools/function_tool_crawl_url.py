import json
import logging

import httpx
from google.adk import tools

from agent_orchestrator.config import CRAWL_MAX_DEPTH, CRAWL_MAX_FILES
from agent_orchestrator.util_metadata import write_processing_log, write_web_provenance

from .util_common import log_tool_error
from .util_crawl import extract_links, is_downloadable_file, normalize_url
from .util_gcs import upload_string

logger = logging.getLogger(__name__)


async def crawl_url(
    url: str,
    tool_context: tools.ToolContext,
) -> str:
    """
    Crawl a URL to discover linked pages and downloadable file URLs.

    Starting from the given URL, follows links up to CRAWL_MAX_DEPTH levels deep,
    collecting downloadable file URLs and page URLs. Respects same-origin policy
    and file extension filters from configuration.

    Args:
        url: The starting URL to crawl.
        tool_context: The ADK tool context for accessing shared state.

    Returns:
        A summary of discovered pages and files, or an error message.
    """
    try:
        normalized_start = normalize_url(url)
        visited = set()
        file_urls = []
        page_urls = []
        crawl_graph = []

        # BFS queue: (url, depth, parent_url)
        queue = [(normalized_start, 0, None)]

        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=30.0,
            headers={"User-Agent": "data-onboarding-agent/1.0"},
        ) as client:
            while queue and len(file_urls) < CRAWL_MAX_FILES:
                current_url, depth, parent_url = queue.pop(0)

                if current_url in visited:
                    continue
                visited.add(current_url)

                # If it's a downloadable file, just record it
                if is_downloadable_file(current_url):
                    file_urls.append(current_url)
                    crawl_graph.append({
                        "url": current_url,
                        "parent_url": parent_url,
                        "type": "file",
                        "depth": depth,
                    })
                    continue

                # Fetch the page
                try:
                    response = await client.get(current_url)
                    response.raise_for_status()
                except httpx.HTTPError as e:
                    logger.warning(f"Failed to fetch {current_url}: {e}")
                    continue

                content_type = response.headers.get("content-type", "")
                if "text/html" not in content_type:
                    # Not an HTML page — might be a direct file download
                    file_urls.append(current_url)
                    crawl_graph.append({
                        "url": current_url,
                        "parent_url": parent_url,
                        "type": "file",
                        "depth": depth,
                    })
                    continue

                page_urls.append(current_url)
                crawl_graph.append({
                    "url": current_url,
                    "parent_url": parent_url,
                    "type": "page",
                    "depth": depth,
                    "title": "",
                    "status_code": response.status_code,
                })

                # Extract links and queue them if within depth
                if depth < CRAWL_MAX_DEPTH:
                    links = extract_links(response.text, current_url)
                    for link in links:
                        if link["url"] not in visited:
                            queue.append((link["url"], depth + 1, current_url))

        # Store in state
        tool_context.state["crawl_graph"] = crawl_graph
        tool_context.state["discovered_file_urls"] = file_urls
        tool_context.state["discovered_page_urls"] = page_urls

        # Write web provenance to BQ
        source_id = tool_context.state.get("source_id", "")
        if source_id and crawl_graph:
            provenance_rows = [
                {
                    "source_id": source_id,
                    "url": edge["url"],
                    "parent_url": edge.get("parent_url"),
                    "page_title": edge.get("title"),
                    "content_type": None,
                    "status_code": edge.get("status_code"),
                    "links_found": None,
                    "files_downloaded": None,
                }
                for edge in crawl_graph
            ]
            write_web_provenance(provenance_rows)

            # Persist provenance.json to GCS
            staging_path = tool_context.state.get("gcs_staging_path", "")
            if staging_path:
                provenance_doc = {
                    "source_id": source_id,
                    "starting_url": url,
                    "crawl_graph": crawl_graph,
                    "file_urls": file_urls,
                    "page_urls": page_urls,
                }
                upload_string(
                    json.dumps(provenance_doc, indent=2),
                    f"{staging_path}/provenance.json",
                    content_type="application/json",
                )

            write_processing_log(
                source_id, "acquire", "crawl_url", "completed",
                details={"pages": len(page_urls), "files": len(file_urls)},
            )

        return (
            f"Crawl complete.\n"
            f"  Starting URL: {url}\n"
            f"  Pages visited: {len(page_urls)}\n"
            f"  Files discovered: {len(file_urls)}\n"
            f"  Max depth reached: {max((e['depth'] for e in crawl_graph), default=0)}\n"
            f"\nFile URLs:\n"
            + "\n".join(f"  - {u}" for u in file_urls[:20])
            + (f"\n  ... and {len(file_urls) - 20} more" if len(file_urls) > 20 else "")
            + "\n\nPage URLs:\n"
            + "\n".join(f"  - {u}" for u in page_urls[:10])
            + (f"\n  ... and {len(page_urls) - 10} more" if len(page_urls) > 10 else "")
        )

    except Exception as e:
        return log_tool_error("crawl_url", e)
