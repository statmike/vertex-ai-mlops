"""Analytics agent tools — BigQuery Q&A via the Conversational Analytics API."""

from .function_tool_analyze_sales import analyze_sales

TOOLS = [analyze_sales]
