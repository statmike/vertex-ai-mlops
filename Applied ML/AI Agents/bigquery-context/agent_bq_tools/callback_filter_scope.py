"""After-tool callback: prune BQ tool results to in-scope resources.

The ADK BigQueryToolset has no built-in dataset/table filtering, so this
callback intercepts ``list_dataset_ids`` and ``list_table_ids`` responses
and removes any entries not defined in ``config.SCOPE``.
"""

from google.adk.tools import ToolContext
from google.adk.tools.base_tool import BaseTool

from config import get_datasets, get_scoped_tables


def filter_scope(
    tool: BaseTool,
    args: dict,
    tool_context: ToolContext,
    tool_response: dict,
) -> dict | None:
    """Filter list_dataset_ids and list_table_ids to SCOPE entries only.

    Returns:
        Filtered dict when pruning is needed, None otherwise (keeps original).
    """
    if not isinstance(tool_response, dict) or "result" not in tool_response:
        return None  # error response or unexpected shape — pass through

    if tool.name == "list_dataset_ids":
        allowed = set(get_datasets())
        filtered = [d for d in tool_response["result"] if d in allowed]
        return {"result": filtered}

    if tool.name == "list_table_ids":
        dataset_id = args.get("dataset_id", "")
        scoped_tables = get_scoped_tables(dataset_id)
        if scoped_tables is None:
            return None  # bare dataset in SCOPE — all tables allowed
        allowed = set(scoped_tables)
        filtered = [t for t in tool_response["result"] if t in allowed]
        return {"result": filtered}

    return None  # other tools — pass through
