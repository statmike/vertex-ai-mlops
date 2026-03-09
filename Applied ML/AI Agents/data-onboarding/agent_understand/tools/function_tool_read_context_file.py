import logging

from google.adk import tools

from agent_acquire.tools.util_common import log_tool_error
from agent_acquire.tools.util_gcs import download_bytes

from .util_file_readers import read_pdf, read_text

logger = logging.getLogger(__name__)


async def read_context_file(
    gcs_path: str,
    extension: str,
    tool_context: tools.ToolContext,
) -> str:
    """
    Read a context file (PDF, TXT, MD, HTML) from GCS and return its content.

    Downloads the file and extracts text content for cross-referencing
    with data file schemas.

    Args:
        gcs_path: The GCS path (without gs:// prefix) of the context file.
        extension: The file extension (pdf, txt, md, html).
        tool_context: The ADK tool context for accessing shared state.

    Returns:
        The extracted text content, or an error message.
    """
    try:
        data = download_bytes(gcs_path)
        filename = gcs_path.split("/")[-1]

        summary = read_pdf(data, filename) if extension == "pdf" else read_text(data, filename)

        content = summary.get("content", "")

        # Store for downstream
        contexts = dict(tool_context.state.get("context_documents", {}))
        contexts[gcs_path] = {
            "filename": filename,
            "content": content[:20000],  # Keep first 20K chars in state
            "size_chars": summary.get("size_chars", len(content)),
        }
        tool_context.state["context_documents"] = contexts

        # Return truncated content for the LLM
        preview = content[:5000]
        return (
            f"Context file: {filename}\n"
            f"  Size: {summary.get('size_chars', len(content))} chars\n"
            f"  Lines: {summary.get('line_count', 0)}\n"
            + (f"  Pages: {summary.get('page_count', 'N/A')}\n" if "page_count" in summary else "")
            + f"\nContent preview:\n{preview}"
            + ("\n... (truncated)" if len(content) > 5000 else "")
        )

    except Exception as e:
        return log_tool_error("read_context_file", e)
