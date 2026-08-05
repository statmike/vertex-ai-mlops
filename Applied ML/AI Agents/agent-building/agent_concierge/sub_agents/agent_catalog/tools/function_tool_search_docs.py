"""Search the unstructured retail-policy corpus with BigQuery AI functions.

The demo corpus (return policy, sizing/care guides, product FAQs) is seeded to
GCS and exposed to BigQuery as an **object table** by scripts/setup.py. An object
table has an automatic `ref` column (an ObjectRef pointing at each file) and a
`uri` column. This tool reads the files directly with `AI.GENERATE` — passing
`OBJ.GET_ACCESS_URL(ref, 'r')` so the model sees the document content — and
returns a grounded answer per relevant document.

A real company would point BQ_* at its own object table over its document
warehouse — the tool is unchanged.
"""

import os

from google.adk import tools
from google.cloud import bigquery

from config import (
    BQ_DATASET,
    BQ_LOCATION,
    BQ_OBJECT_TABLE,
    GOOGLE_CLOUD_PROJECT,
)

# Marker the model returns for a document that can't answer the question, so we
# can filter irrelevant files out cheaply in one pass over the small corpus.
_NONE = "NONE"

# Cached BigQuery client — avoid re-establishing the connection per call.
_bq_client: bigquery.Client | None = None


def _client() -> bigquery.Client:
    global _bq_client
    if _bq_client is None:
        _bq_client = bigquery.Client(project=GOOGLE_CLOUD_PROJECT)
    return _bq_client


async def search_docs(question: str, tool_context: tools.ToolContext) -> str:
    """Search retail policy/help documents for passages relevant to a question.

    Use this for anything about policies, procedures, or guidance that lives in
    documents rather than transaction data: returns, exchanges, shipping,
    sizing, product care, warranties, membership perks, etc.

    Args:
        question: The user's natural-language question.
        tool_context: ADK tool execution context.

    Returns:
        Grounded answers drawn from the relevant documents, or a message if none
        match.
    """
    table = f"`{GOOGLE_CLOUD_PROJECT}.{BQ_DATASET}.{BQ_OBJECT_TABLE}`"
    # AI.GENERATE requires connection_id as a *string literal* — it cannot be a
    # query parameter (BigQuery rejects @connection with a 400). The value is
    # built from trusted config constants, not user input, so inlining is safe;
    # the user's question stays a bound parameter.
    connection = f"{GOOGLE_CLOUD_PROJECT}.{BQ_LOCATION.lower()}.{BQ_DATASET}_ai"

    # One pass over the small corpus: read each file and answer from it, or
    # return the NONE marker when the document is irrelevant.
    query = f"""
    SELECT
      uri,
      AI.GENERATE(
        (
          'Answer the question using ONLY this document. If the document does '
          'not address the question, reply with exactly "{_NONE}". Question: ',
          @question,
          ' Document: ',
          OBJ.GET_ACCESS_URL(ref, 'r')
        ),
        connection_id => '{connection}',
        endpoint => 'gemini-2.5-flash'
      ).result AS answer
    FROM {table}
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("question", "STRING", question),
        ]
    )

    try:
        rows = list(_client().query(query, job_config=job_config).result())
    except Exception as e:  # noqa: BLE001 — surface a clean message to the model
        return (
            f"Error searching documents: {e}. "
            "Has scripts/setup.py been run to create the object table and "
            "BigQuery AI connection?"
        )

    # Keep only documents that actually answered the question.
    matches = [
        (r["uri"], r["answer"].strip())
        for r in rows
        if r["answer"] and r["answer"].strip().upper() != _NONE
    ]
    if not matches:
        return "No policy or help documents matched that question."

    # Record sources (file names) so the agent can cite them.
    titles = [os.path.basename(uri) for uri, _ in matches]
    tool_context.state["catalog_last_sources"] = titles

    passages = [f"### {os.path.basename(uri)}\n{answer}" for uri, answer in matches]
    return "\n\n".join(passages)
