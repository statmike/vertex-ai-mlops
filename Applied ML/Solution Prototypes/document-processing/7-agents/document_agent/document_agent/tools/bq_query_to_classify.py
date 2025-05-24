from google.adk import tools
from google.cloud import bigquery
from ..config import GCP_PROJECT

bq = bigquery.Client(project = GCP_PROJECT)

async def bq_query_to_classify(tool_context: tools.ToolContext) -> str:
    """
    
    """

    try:
        # 1. Retrieve document embedding from context for the session
        embedding = tool_context.state.get('document_embedding')

        # 2. Setup the query for BigQuery
        query = f"""
            SELECT 
                base.vendor,
                distance
            FROM VECTOR_SEARCH(
                # The base table and column to search for neighbors in:
                (SELECT vendor, average_embedding FROM `statmike-mlops-349915.solution_prototype_document_processing.known_authenticity_vendor_info`),
                'average_embedding',
                # The query table and column to search with
                (SELECT @query_embedding as embedding),
                'embedding',
                # options
                top_k => -1,
                distance_type => 'DOT_PRODUCT'
            )
            ORDER BY distance ASC
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters = [
                bigquery.ArrayQueryParameter(
                    'query_embedding', 'FLOAT64', embedding
                )
            ]
        )

        # 3. Execute the BigQuery Query and retrieve results to local dataframe
        results = bq.query(query, job_config=job_config).to_dataframe()

        # 4. Convert the dataframe to Markdown
        results = results.to_markdown(index=False)

        # 5. Return the results
        return results

    except Exception as e:
        return f"Error with tool `bq_query_to_classify` during the classification query. Error: {str(e)}"