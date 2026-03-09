import logging

from google.adk import tools

from agent_acquire.tools.util_common import log_tool_error

from .util_quality import get_column_null_rates, get_column_types

logger = logging.getLogger(__name__)


async def validate_types(
    tool_context: tools.ToolContext,
) -> str:
    """
    Validate that BQ column types match the designed schema.

    Checks each column's actual BQ type against the proposed type,
    and reports null rates for quality assessment.

    Args:
        tool_context: The ADK tool context for accessing shared state.

    Returns:
        Validation results for column types, or an error message.
    """
    try:
        proposals = tool_context.state.get("proposed_tables", {})
        if not proposals:
            return "No proposed tables to validate."

        results = {}
        all_passed = True

        for table_name, proposal in proposals.items():
            columns = proposal.get("enriched_columns", proposal.get("columns", []))
            actual_types = get_column_types(table_name)
            null_rates = get_column_null_rates(table_name)

            if not actual_types:
                results[table_name] = {
                    "status": "SKIP",
                    "message": "Table does not exist or cannot be queried",
                    "columns": {},
                }
                all_passed = False
                continue

            col_results = {}
            table_passed = True

            for col in columns:
                col_name = col.get("name", "")
                expected_type = col.get("bq_type", "STRING")
                actual_type = actual_types.get(col_name)
                null_rate = null_rates.get(col_name, 0)

                if actual_type is None:
                    status = "FAIL"
                    message = "Column not found in table"
                    table_passed = False
                elif actual_type == expected_type:
                    status = "PASS"
                    message = f"{actual_type} (null: {null_rate}%)"
                else:
                    status = "WARN"
                    message = f"Expected {expected_type}, got {actual_type} (null: {null_rate}%)"

                col_results[col_name] = {
                    "status": status,
                    "expected": expected_type,
                    "actual": actual_type,
                    "null_rate": null_rate,
                    "message": message,
                }

            results[table_name] = {
                "status": "PASS" if table_passed else "FAIL",
                "columns": col_results,
            }
            if not table_passed:
                all_passed = False

        # Store results
        validation = dict(tool_context.state.get("validation_results", {}))
        validation["types"] = results
        tool_context.state["validation_results"] = validation

        summary = "Column type validation:\n"
        for table, result in results.items():
            summary += f"\n  {table} [{result['status']}]:\n"
            if "columns" in result:
                for col, info in result["columns"].items():
                    icon = {"PASS": "OK", "FAIL": "FAIL", "WARN": "WARN"}[info["status"]]
                    summary += f"    [{icon}] {col}: {info['message']}\n"
            else:
                summary += f"    {result.get('message', '')}\n"

        summary += f"\nOverall: {'PASSED' if all_passed else 'ISSUES FOUND'}\n"
        return summary

    except Exception as e:
        return log_tool_error("validate_types", e)
