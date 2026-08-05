"""ADK tool: answer questions about theLook sales data via the CA API.

Thin wrapper — it supplies the fixed set of in-scope theLook tables (from
config) so the model never has to name datasets, then delegates to the shared
`call_conversational_api` core.
"""

from google.adk import tools

from config import THELOOK_DATASET, THELOOK_PROJECT, THELOOK_TABLES

from .util_conversational_api import call_conversational_api

_SYSTEM_INSTRUCTION = (
    "You are a retail analyst for theLook e-commerce. Answer questions about "
    "products, orders, customers, and sales using the provided BigQuery tables. "
    "Prefer concise, quantified answers."
)


async def analyze_sales(question: str, tool_context: tools.ToolContext) -> str:
    """Answer a question about theLook sales/transaction data.

    Use this for anything backed by the numbers: revenue, order counts, top
    products or categories, customer demographics, returns rates, trends, etc.

    Args:
        question: The user's natural-language question about the data.
        tool_context: ADK tool execution context.

    Returns:
        A text answer, optionally including a small data table.
    """
    bigquery_tables = [
        {"project_id": THELOOK_PROJECT, "dataset_id": THELOOK_DATASET, "table_id": t}
        for t in THELOOK_TABLES
    ]
    return await call_conversational_api(
        question=question,
        bigquery_tables=bigquery_tables,
        tool_context=tool_context,
        system_instruction=_SYSTEM_INSTRUCTION,
    )
