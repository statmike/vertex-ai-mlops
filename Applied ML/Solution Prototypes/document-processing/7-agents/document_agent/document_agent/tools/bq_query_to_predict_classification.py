from google.adk import tools
from google.cloud import bigquery
from ..config import GCP_PROJECT

bq = bigquery.Client(project = GCP_PROJECT)

async def bq_query_to_predict_classification(tool_context: tools.ToolContext) -> str:
    """
    Predicts the vendor classification for a document using a BigQuery ML model.

    This function retrieves a document embedding from the ADK tool context state.
    It then invokes a pre-trained BigQuery ML model (`rf_classifier`) to predict
    the vendor. The function formats and returns the top prediction along with the
    probabilities for all possible classes.

    Args:
        tool_context: The execution context for the tool, which must contain the
                      'document_embedding' in its state.

    Returns:
        A string containing the predicted vendor and a list of the prediction
        probabilities for each vendor class, or an error message if the
        prediction query fails.
    """

    try:
        # 1. Retrieve document embedding from context for the session
        embedding = tool_context.state.get('document_embedding')

        # 2. Setup the query for BigQuery
        query = f"""
            SELECT *
            FROM ML.PREDICT(
                MODEL `statmike-mlops-349915.solution_prototype_document_processing.rf_classifier`,
                (SELECT @query_embedding as embedding)
            )
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

        # 4. Get Prediction Data From result
        response = f"""
            The predicted vendor is: {results['predicted_vendor'].iloc[0]}
            The predicted probability for each vendor is:
            {str(results['predicted_vendor_probs'].iloc[0])}
        """

        # 5. Return the results
        return response
    
    except Exception as e:
       return f"Error with tool `bq_query_to_predict_classification` during the prediction query. Error: {str(e)}" 
