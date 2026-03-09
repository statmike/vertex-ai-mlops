import logging

from google.adk import tools

from agent_acquire.tools.util_common import log_tool_error
from agent_acquire.tools.util_gcs import download_bytes

from .util_file_readers import read_file

logger = logging.getLogger(__name__)


async def read_data_file(
    gcs_path: str,
    extension: str,
    tool_context: tools.ToolContext,
) -> str:
    """
    Read a data file from GCS and return its schema summary.

    Downloads the file, reads it with the appropriate parser, and returns
    column names, types, sample values, and null statistics.

    Args:
        gcs_path: The GCS path (without gs:// prefix) of the data file.
        extension: The file extension (csv, json, xlsx, parquet, etc.).
        tool_context: The ADK tool context for accessing shared state.

    Returns:
        A formatted schema summary, or an error message.
    """
    try:
        data = download_bytes(gcs_path)
        filename = gcs_path.split("/")[-1]

        summary = read_file(data, filename, extension)

        if "error" in summary and summary["error"]:
            return f"Error reading {filename}: {summary['error']}"

        if summary.get("type") == "tabular":
            result = f"Data file: {filename}\n"
            result += f"  Rows: {summary['rows']}\n"
            result += f"  Columns: {len(summary['columns'])}\n\n"
            result += "Column details:\n"

            for col in summary["columns"]:
                result += (
                    f"  {col['name']}:\n"
                    f"    dtype: {col['dtype']}\n"
                    f"    nulls: {col['null_count']} ({col['null_pct']}%)\n"
                    f"    unique: {col['unique_count']}\n"
                    f"    samples: {col['sample_values'][:3]}\n"
                )

            # Store for downstream
            schemas = dict(tool_context.state.get("schemas_analyzed", {}))
            schemas[gcs_path] = summary
            tool_context.state["schemas_analyzed"] = schemas

            return result
        else:
            return f"File {filename} is not tabular (type: {summary.get('type', 'unknown')})"

    except Exception as e:
        return log_tool_error("read_data_file", e)
