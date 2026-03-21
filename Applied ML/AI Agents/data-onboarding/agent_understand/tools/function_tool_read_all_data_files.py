import logging
import posixpath

from google.adk import tools

from agent_acquire.tools.util_common import log_tool_error
from agent_acquire.tools.util_gcs import download_bytes

from .util_file_readers import read_file

logger = logging.getLogger(__name__)


async def read_all_data_files(
    tool_context: tools.ToolContext,
) -> str:
    """Read ALL classified data files and populate schemas_analyzed in state.

    Iterates over every file in ``files_classified`` with classification "data",
    downloads it from GCS, parses it with the appropriate reader, and stores the
    schema summary in ``schemas_analyzed``.  Call this once instead of calling
    ``read_data_file`` individually for each file.

    Args:
        tool_context: The ADK tool context for accessing shared state.

    Returns:
        Summary of files read successfully and any errors.
    """
    try:
        classified = tool_context.state.get("files_classified", [])
        if not classified:
            return "No classified files. Run classify_files first."

        data_files = [f for f in classified if f.get("classification") == "data"]
        if not data_files:
            return "No data files found in classified files."

        schemas = dict(tool_context.state.get("schemas_analyzed", {}))
        succeeded = []
        failed = []

        for f in data_files:
            gcs_path = f.get("gcs_path", "")
            filename = f.get("filename", posixpath.basename(gcs_path))
            extension = f.get("extension", "")

            if not gcs_path:
                failed.append(f"{filename}: no gcs_path")
                continue

            # Skip if already analyzed (idempotent)
            if gcs_path in schemas:
                succeeded.append(f"{filename} (cached)")
                continue

            try:
                data = download_bytes(gcs_path)
                summary = read_file(data, filename, extension)

                if summary.get("error"):
                    failed.append(f"{filename}: {summary['error']}")
                    continue

                if summary.get("type") == "multi_sheet":
                    # Store each sheet as a separate schema with virtual path
                    for sheet_name, sheet_summary in summary.get("sheets", {}).items():
                        virtual_path = f"{gcs_path}#{sheet_name}"
                        schemas[virtual_path] = sheet_summary
                        succeeded.append(
                            f"{filename}#{sheet_name}: {sheet_summary['rows']} rows, "
                            f"{len(sheet_summary['columns'])} columns"
                        )
                elif summary.get("type") == "tabular":
                    schemas[gcs_path] = summary
                    succeeded.append(
                        f"{filename}: {summary['rows']} rows, "
                        f"{len(summary['columns'])} columns"
                    )
                else:
                    failed.append(
                        f"{filename}: not tabular (type={summary.get('type')})"
                    )
            except Exception as e:
                logger.warning("Failed to read %s: %s", filename, e)
                failed.append(f"{filename}: {e}")

        tool_context.state["schemas_analyzed"] = schemas

        result = (
            f"Read all data files: {len(succeeded)} succeeded, "
            f"{len(failed)} failed (out of {len(data_files)} data files)\n"
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
        return log_tool_error("read_all_data_files", e)
