"""Utility for calling Gemini with structured output to produce a ranked table list."""

import json

from google import genai
from google.genai import types

from config import GOOGLE_CLOUD_PROJECT, TOOL_MODEL, TOOL_MODEL_LOCATION
from schemas import RerankerResponse


RERANKER_SYSTEM_PROMPT = """\
You are a BigQuery table relevance ranker. Given a user's question and metadata
about candidate BigQuery tables, you rank the tables by relevance.

For each table, evaluate:
1. How directly the table's columns and description answer the question
2. Which specific columns would be used in a SQL query to answer it
3. Whether joins to other candidate tables would help
4. What SQL patterns (WHERE filters, GROUP BY, aggregations) would be needed

Return tables ranked by relevance (most relevant first). Only include tables
that are genuinely relevant — do not pad the list. Set confidence scores
honestly: 0.9+ for highly relevant, 0.5-0.8 for partially relevant,
below 0.5 for tangentially relevant.

For table_id, always use the standard BigQuery fully-qualified format:
`project.dataset.table` (e.g., `my-project.my_dataset.my_table`).
Extract the project, dataset, and table name from whatever identifier
format appears in the metadata.

For key_columns, identify the most important columns for answering the question
and flag which are useful for filtering vs aggregation.

For sql_hints, provide concrete SQL guidance like:
- "Filter on weather_date for time-based questions"
- "GROUP BY subscriber_type to compare rider categories"
- "JOIN to stations table on start_station_id = station_id"
"""


def call_reranker(
    question: str,
    candidate_metadata: str,
    discovery_method: str,
    top_k: int,
) -> RerankerResponse:
    """Call Gemini with structured output to rank candidate tables.

    Args:
        question: The user's original question.
        candidate_metadata: String containing table metadata (schemas,
            descriptions, profiles, etc.) from the discovery approach.
        discovery_method: Which approach produced the candidates
            ("bq_tools", "catalog_search", "knowledge_context").
        top_k: Maximum number of tables to return.

    Returns:
        RerankerResponse with ranked tables.
    """
    client = genai.Client(
        vertexai=True,
        project=GOOGLE_CLOUD_PROJECT,
        location=TOOL_MODEL_LOCATION or "us-central1",
    )

    user_prompt = f"""\
## User Question
{question}

## Discovery Method
{discovery_method}

## Top K
Return at most {top_k} tables.

## Candidate Table Metadata
{candidate_metadata}
"""

    response = client.models.generate_content(
        model=TOOL_MODEL,
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=RERANKER_SYSTEM_PROMPT,
            response_mime_type="application/json",
            response_schema=RerankerResponse.model_json_schema(),
            temperature=0.1,
        ),
    )

    result = RerankerResponse.model_validate(json.loads(response.text))
    return result
