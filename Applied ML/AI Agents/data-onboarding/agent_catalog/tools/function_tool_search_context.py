"""Semantic search over chunked table documentation using BigQuery AI.SEARCH."""

import logging

from google.adk import tools

from agent_orchestrator.config import BQ_CONTEXT_DATASET, GOOGLE_CLOUD_PROJECT

logger = logging.getLogger(__name__)


async def search_context(
    query: str,
    top_k: int = 10,
    tool_context: tools.ToolContext = None,
) -> str:
    """Search indexed documentation chunks for relevant context.

    Uses BigQuery ``AI.SEARCH`` for semantic retrieval over the
    ``context_chunks`` table, which contains chunked table documentation
    with autonomous embeddings.

    Args:
        query: The search query (e.g., "What does PRVDR_NUM mean?").
        top_k: Number of results to return (default 10).
        tool_context: The ADK tool context (unused but required by ADK).

    Returns:
        Formatted search results with chunk type, source info, and content.
    """
    if not GOOGLE_CLOUD_PROJECT:
        return "Cannot search: GOOGLE_CLOUD_PROJECT not set."

    try:
        from google.cloud import bigquery

        client = bigquery.Client(project=GOOGLE_CLOUD_PROJECT)

        sql = f"""
            SELECT
                base.chunk_id,
                base.source_dataset,
                base.source_table,
                base.chunk_type,
                base.chunk_text,
                distance
            FROM AI.SEARCH(
                TABLE `{GOOGLE_CLOUD_PROJECT}.{BQ_CONTEXT_DATASET}.context_chunks`,
                'chunk_text',
                @query,
                top_k => @top_k,
                options => '{{"use_brute_force":true}}'
            )
            ORDER BY distance ASC
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("query", "STRING", query),
                bigquery.ScalarQueryParameter("top_k", "INT64", top_k),
            ]
        )

        results = client.query(sql, job_config=job_config).result()
        rows = list(results)

        if not rows:
            return (
                "No matching documentation found. Try rephrasing your query "
                "or using different terms."
            )

        parts = [f"Found {len(rows)} relevant chunk(s):\n"]
        for row in rows:
            parts.append("---")
            parts.append(f"**[{row.chunk_type}]** {row.source_dataset}.{row.source_table}")
            parts.append(f"Distance: {row.distance:.4f}")
            parts.append(f"{row.chunk_text}")
            parts.append("")

        return "\n".join(parts)

    except Exception as e:
        return f"Error searching context: {e}"
