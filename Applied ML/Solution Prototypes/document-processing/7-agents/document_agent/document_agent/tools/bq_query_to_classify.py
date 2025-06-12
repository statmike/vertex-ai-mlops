from google.adk import tools
from google.cloud import bigquery
from ..config import GCP_PROJECT

bq = bigquery.Client(project = GCP_PROJECT)

async def bq_query_to_classify(tool_context: tools.ToolContext) -> str:
    """
    Classifies a document by querying a BigQuery table with a document embedding.

    This function retrieves a pre-computed document embedding from the ADK's tool
    context state. It then uses this embedding to perform a vector search (similarity
    search) against a BigQuery table containing known vendor embeddings. The function
    returns a list of vendors and their similarity scores, ordered by relevance.

    Args:
        tool_context: The execution context for the tool, which must contain the
                      'document_embedding' in its state.

    Returns:
        A markdown-formatted string listing the vendors and their corresponding
        similarity distances, or an error message if the query fails.
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