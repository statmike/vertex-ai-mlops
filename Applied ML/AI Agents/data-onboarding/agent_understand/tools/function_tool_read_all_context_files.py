import logging
import posixpath

from google.adk import tools

from agent_acquire.tools.util_common import log_tool_error
from agent_acquire.tools.util_gcs import download_bytes

from .util_file_readers import read_pdf, read_text

logger = logging.getLogger(__name__)


async def read_all_context_files(
    tool_context: tools.ToolContext,
) -> str:
    """Read ALL classified context files and populate context_documents in state.

    Iterates over every file in ``files_classified`` with classification
    "context", downloads it from GCS, parses it with the appropriate reader
    (PDF or plain text), and stores the extracted content in
    ``context_documents``.  Call this once instead of calling
    ``read_context_file`` individually for each file.

    Args:
        tool_context: The ADK tool context for accessing shared state.

    Returns:
        Summary of context files read successfully and any errors.
    """
    try:
        classified = tool_context.state.get("files_classified", [])
        if not classified:
            return "No classified files. Run classify_files first."

        context_files = [f for f in classified if f.get("classification") == "context"]
        if not context_files:
            return "No context files found in classified files."

        contexts = dict(tool_context.state.get("context_documents", {}))
        succeeded = []
        failed = []

        for f in context_files:
            gcs_path = f.get("gcs_path", "")
            filename = f.get("filename", posixpath.basename(gcs_path))
            extension = f.get("extension", "")

            if not gcs_path:
                failed.append(f"{filename}: no gcs_path")
                continue

            # Skip if already read (idempotent)
            if gcs_path in contexts:
                succeeded.append(f"{filename} (cached)")
                continue

            try:
                data = download_bytes(gcs_path)

                summary = read_pdf(data, filename) if extension == "pdf" else read_text(data, filename)
                content = summary.get("content", "")

                contexts[gcs_path] = {
                    "filename": filename,
                    "content": content[:20000],  # Keep first 20K chars in state
                    "size_chars": summary.get("size_chars", len(content)),
                }

                succeeded.append(
                    f"{filename}: {summary.get('size_chars', len(content))} chars"
                )
            except Exception as e:
                logger.warning("Failed to read context file %s: %s", filename, e)
                failed.append(f"{filename}: {e}")

        tool_context.state["context_documents"] = contexts

        result = (
            f"Read all context files: {len(succeeded)} succeeded, "
            f"{len(failed)} failed (out of {len(context_files)} context files)\n"
        )

        if succeeded:
            result += "\nSucceeded:\n"
            for s in succeeded:
                result += f"  - {s}\n"

        if failed:
            result += "\nFailed:\n"
            for f in failed:
                result += f"  - {f}\n"

        return result

    except Exception as e:
        return log_tool_error("read_all_context_files", e)
