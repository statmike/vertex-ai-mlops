"""Utility for calling Gemini with structured output to produce a ranked table list."""

import json

from google import genai
from google.genai import types

from agent_context.schemas import RerankerResponse
from agent_orchestrator.config import GOOGLE_CLOUD_PROJECT, TOOL_MODEL, TOOL_MODEL_LOCATION

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
    top_k: int = 10,
) -> RerankerResponse:
    """Call Gemini with structured output to rank candidate tables.

    Args:
        question: The user's original question.
        candidate_metadata: String containing table metadata (schemas,
            descriptions, profiles, etc.) from discovery.
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
table_documentation

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

    return RerankerResponse.model_validate(json.loads(response.text))


def format_reranker_markdown(result: RerankerResponse) -> str:
    """Format a RerankerResponse as readable markdown for agent output.

    Args:
        result: The reranker result to format.
    """
    lines = ["**[Reranker Results]**", ""]

    if not result.ranked_tables:
        lines.append(result.notes or "No relevant tables found.")
        return "\n".join(lines)

    lines.append(
        f"Found **{len(result.ranked_tables)}** relevant table(s):"
    )
    lines.append("")

    for t in result.ranked_tables:
        lines.append(f"**#{t.rank}. `{t.table_id}`** — confidence: {t.confidence:.2f}")
        lines.append(f"> {t.reasoning}")
        if t.key_columns:
            col_strs = []
            for c in t.key_columns:
                tags = []
                if c.useful_for_filtering:
                    tags.append("filter")
                if c.useful_for_aggregation:
                    tags.append("aggregate")
                if c.is_key:
                    tags.append("key")
                tag_str = f" ({', '.join(tags)})" if tags else ""
                col_strs.append(f"`{c.name}` {c.data_type}{tag_str}")
            lines.append(f"- **Key columns:** {', '.join(col_strs)}")
        if t.sql_hints:
            lines.append(f"- **SQL hints:** {t.sql_hints}")
        if t.join_suggestions:
            for j in t.join_suggestions:
                lines.append(
                    f"- **Join:** → `{j.target_table}` "
                    f"ON {', '.join(j.join_keys)} ({j.relationship})"
                )
        lines.append("")

    if result.notes:
        lines.append(f"**Notes:** {result.notes}")

    return "\n".join(lines)
