import os
from google.adk import tools
from google.cloud import bigquery

bq = bigquery.Client(project = os.getenv('GOOGLE_CLOUD_PROJECT'))

async def function_tool_bq_hurricanes_per_year_filtered(min_year: int, max_year: int, tool_context: tools.ToolContext) -> str:
    """
    Queries the BigQuery NOAA public dataset to count hurricanes per year within a specified range.

    This function executes a SQL query that counts the number of distinct hurricanes
    in the North Atlantic basin for each year, filtered to a specific year range.
    The results are ordered by the hurricane count in descending order, and the
    final output is formatted as a markdown table.

    Args:
        min_year: The first year in the range to include in the filter.
        max_year: The last year in the range to include in the filter.
        tool_context: The execution context for the tool, provided by the ADK framework.

    Returns:
        A markdown-formatted string containing a table of years and their
        corresponding hurricane counts for the specified period, or an
        error message if the query fails.
    """

    try:

        # 1. Setup the query for BigQuery
        query = f"""
            SELECT
                EXTRACT(YEAR FROM iso_time) AS report_year,
                COUNT(DISTINCT sid) AS number_of_hurricanes
            FROM `bigquery-public-data.noaa_hurricanes.hurricanes`
            WHERE
                iso_time IS NOT NULL
                AND basin = 'NA' -- North Atlantic Basin
                AND EXTRACT(YEAR FROM iso_time) >= @min_year
                AND EXTRACT(YEAR FROM iso_time) <= @max_year
            GROUP BY report_year
            ORDER BY number_of_hurricanes DESC
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("min_year", "INT64", min_year),
                bigquery.ScalarQueryParameter("max_year", "INT64", max_year),
            ]
        )

        # 2. Execute the BigQuery Query and retrieve results to local dataframe
        results = bq.query(query, job_config = job_config).to_dataframe()

        # 3. Convert the dataframe to Markdown
        results = results.to_markdown(index=False)

        # 4. Return the results
        return results

    except Exception as e:
        return f"Error with tool `function_tool_bq_hurricanes_per_year_filtered` during the query. Error: {str(e)}"