import os
from google.adk import tools
from google.cloud import bigquery

bq = bigquery.Client(project=os.getenv('GOOGLE_CLOUD_PROJECT'))

async def sql_dry_run_callback(tool, args, tool_context: tools.ToolContext) -> None:
    """
    A before-tool callback that performs a dry run of a SQL query.
    Raises a ValueError if the query is invalid or uses disallowed statements.
    """
    if tool.name != "mcp_tool_execute_dynamic_sql":
        return

    sql_query = args.get("sql") or args.get("statement")

    if not sql_query:
        raise ValueError(f"Could not find SQL query in tool parameters. Available keys: {list(args.keys())}")

    # 1. Check for disallowed statements
    disallowed_keywords = ["DELETE", "DROP", "UPDATE"]
    if any(keyword in sql_query.upper() for keyword in disallowed_keywords):
        raise ValueError(
            "This agent is not allowed to execute DELETE, DROP, or UPDATE statements."
        )

    # 2. Perform a dry run
    try:
        job_config = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
        bq.query(sql_query, job_config=job_config)
    except Exception as e:
        # Re-raise the exception with a more informative message
        raise ValueError(
            f"The generated SQL query is invalid and will fail. Error: {str(e)}"
        ) from e

    return