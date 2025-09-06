import os
from google.adk import tools
from google.cloud import bigquery
from dotenv import load_dotenv

# Load environment variables from .env file located in the parent directory
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

bq = bigquery.Client(project = os.getenv('GOOGLE_CLOUD_PROJECT'))
MAX_BYTES = int(os.getenv('max_bq_bytes', 10000))

async def function_tool_bq_hurricanes_per_year(tool_context: tools.ToolContext) -> str:
    """
    Queries the BigQuery NOAA public dataset to count hurricanes per year.

    This function executes a SQL query that counts the number of distinct hurricanes
    in the North Atlantic basin for each year. The results are ordered by the
    hurricane count in descending order. The final output is formatted as a
    markdown table.

    Args:
        tool_context: The execution context for the tool, provided by the ADK framework.
                      (This argument is not used in the function body).

    Returns:
        A markdown-formatted string containing a table of years and their
        corresponding hurricane counts, or an error message if the query fails.
    """

    try:
        query = f"""
            SELECT
                EXTRACT(YEAR FROM iso_time) AS report_year,
                COUNT(DISTINCT sid) AS number_of_hurricanes
            FROM `bigquery-public-data.noaa_hurricanes.hurricanes`
            WHERE
                iso_time IS NOT NULL
                AND basin = 'NA' -- North Atlantic Basin
            GROUP BY report_year
            ORDER BY number_of_hurricanes DESC
        """
        
        job_config = bigquery.QueryJobConfig(maximum_bytes_billed=MAX_BYTES, use_query_cache=False)
        query_job = bq.query(query, job_config=job_config)

        if query_job.error_result:
            if 'maximumBytesBilled' in str(query_job.error_result):
                return f"Error: Query would process {query_job.total_bytes_processed} bytes, which exceeds the limit of {MAX_BYTES} bytes."
            else:
                return f"Error: {query_job.error_result}"

        results = query_job.to_dataframe()
        bytes_processed_message = f"\n*Query successful. Bytes processed: {query_job.total_bytes_processed}*"
        return results.to_markdown(index=False) + bytes_processed_message

    except Exception as e:
        return f"Error with tool `function_tool_bq_hurricanes_per_year` during the query. Error: {str(e)}"