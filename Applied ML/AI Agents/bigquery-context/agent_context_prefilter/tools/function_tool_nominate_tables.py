"""Tool for the LLM to nominate relevant table candidates for reranking."""

from google.adk import tools


async def nominate_tables(
    table_ids: list[str],
    tool_context: tools.ToolContext,
) -> str:
    """Nominate tables as relevant candidates for detailed reranking.

    Call this tool with the fully qualified table IDs (project.dataset.table)
    of tables you believe are relevant to the user's question. The nominated
    tables will be sent to the reranker with their full detailed metadata.

    Args:
        table_ids: List of fully qualified table IDs to nominate.

    Returns:
        Confirmation of how many tables were nominated.
    """
    tool_context.state["nominated_tables"] = table_ids
    return (
        f"Nominated {len(table_ids)} table(s) for detailed reranking: "
        f"{', '.join(table_ids)}. "
        "Nomination complete — do NOT call this tool again. "
        "Provide your final summary now."
    )
