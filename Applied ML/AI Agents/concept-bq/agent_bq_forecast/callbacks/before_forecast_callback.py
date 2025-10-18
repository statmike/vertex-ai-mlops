import os
from typing import Dict, Any
from google.adk import tools
from google.adk.tools import bigquery as bq_tools

# Create the toolset at module level
bq_toolset = bq_tools.BigQueryToolset(
    bigquery_tool_config=bq_tools.config.BigQueryToolConfig(
        write_mode=bq_tools.config.WriteMode.BLOCKED,
        compute_project_id=os.getenv('GOOGLE_CLOUD_PROJECT')
    ),
    tool_filter=['execute_sql']
)

# Cache the execute_sql tool to avoid re-fetching on every callback
_execute_sql_tool = None

async def before_forecast_callback(tool: tools.BaseTool, args: Dict[str, Any], tool_context: tools.ToolContext) -> None:
    """
    Callback executed before the forecast tool runs.

    This callback intercepts the forecast tool call, extracts the SQL query
    from the 'history_data' parameter, and executes it using the execute_sql tool
    to retrieve the historical data before forecasting. The query results are
    stored in tool_context.state['forecast_history'] for access by other components.

    The callback validates that 'history_data' contains a SQL query (checking for
    SELECT, WITH, or FROM keywords) before executing it against BigQuery.

    Args:
        tool: The tool being called (only processes 'forecast' tool)
        args: The arguments passed to the tool, expecting 'history_data' (SQL query)
              and 'project_id' (GCP project)
        tool_context: The tool execution context containing shared state

    Returns:
        None
    """
    global _execute_sql_tool

    if tool.name != 'forecast':
        return

    history_sql = args.get('history_data')
    if not history_sql:
        print("Warning: No 'history_data' parameter found in forecast tool arguments")
        return

    # Validate that history_data is a SQL query
    if not isinstance(history_sql, str) or not any(
        keyword in history_sql.strip().upper()
        for keyword in ['SELECT', 'WITH', 'FROM']
    ):
        print(f"Warning: 'history_data' doesn't appear to be a valid SQL query")
        return

    try:
        print(f"Executing history SQL query before forecast:\n{history_sql}")

        # Cache the tool on first use to avoid repeated lookups
        if _execute_sql_tool is None:
            bq_tools_list = await bq_toolset.get_tools(readonly_context=tool_context)
            _execute_sql_tool = next(
                (t for t in bq_tools_list if t.name == 'execute_sql'),
                None
            )

            if _execute_sql_tool is None:
                print("Error: execute_sql tool not found in toolset")
                return

        # Execute the SQL query
        result = await _execute_sql_tool.run_async(
            args={
                'project_id': args.get('project_id'),
                'query': history_sql
            },
            tool_context=tool_context
        )

        print(f"History query executed successfully. Result: {result}")
        tool_context.state['forecast_history'] = result
        tool_context.state['forecast_history']['args'] = args

    except Exception as e:
        print(f"Error executing history SQL query: {e}")
        import traceback
        traceback.print_exc()