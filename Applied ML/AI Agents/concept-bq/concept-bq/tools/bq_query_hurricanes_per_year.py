import os
from google.adk import tools
from google.cloud import bigquery

bq = bigquery.Client(project = os.getenv('GOOGLE_CLOUD_PROJECT'))

async def bq_query_hurricanes_per_year(tool_context: tools.ToolContext) -> str:
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

        # 1. Setup the query for BigQuery
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

        # 2. Execute the BigQuery Query and retrieve results to local dataframe
        results = bq.query(query).to_dataframe()

        # 3. Convert the dataframe to Markdown
        results = results.to_markdown(index=False)

        # 4. Return the results
        return results

    except Exception as e:
        return f"Error with tool `bq_query_hurricanes_per_year` during the query. Error: {str(e)}"