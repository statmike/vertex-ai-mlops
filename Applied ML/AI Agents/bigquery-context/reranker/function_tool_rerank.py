"""Shared reranker tool used by all three discovery agents.

Takes candidate table metadata (as a string) from any discovery approach
and produces a ranked RerankerResponse via Gemini structured output.
"""

from google.adk import tools

from config import TOP_K
from .util_rerank import call_reranker


async def rerank_tables(
    question: str,
    candidate_metadata: str,
    discovery_method: str,
    tool_context: tools.ToolContext,
) -> str:
    """Rank candidate BigQuery tables by relevance to the user's question.

    Call this tool after gathering table metadata to produce a ranked list.
    Pass all discovered table metadata as a single string in candidate_metadata.

    Args:
        question: The user's original question about their data.
        candidate_metadata: All table metadata gathered during discovery,
            formatted as a readable string (schemas, descriptions, etc.).
        discovery_method: Which discovery approach produced the candidates.
            One of: "bq_tools", "catalog_search", "knowledge_context".

    Returns:
        A JSON string containing the ranked tables with confidence scores,
        reasoning, column hints, and SQL suggestions.
    """
    top_k = tool_context.state.get("top_k", TOP_K)

    result = call_reranker(
        question=question,
        candidate_metadata=candidate_metadata,
        discovery_method=discovery_method,
        top_k=top_k,
    )

    # Store result in state for the orchestrator to compare
    state_key = f"reranker_result_{discovery_method}"
    tool_context.state[state_key] = result.model_dump_json()

    return result.model_dump_json(indent=2)
