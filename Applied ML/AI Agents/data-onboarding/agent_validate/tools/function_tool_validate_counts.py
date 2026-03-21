import logging

from google.adk import tools

from agent_acquire.tools.util_common import log_tool_error
from agent_understand.tools.util_file_readers import MAX_SAMPLE_ROWS

from .util_quality import get_table_row_count

logger = logging.getLogger(__name__)


async def validate_counts(
    tool_context: tools.ToolContext,
) -> str:
    """
    Validate that BQ table row counts match expected counts from source files.

    Compares the number of rows in each BQ table against the row count
    recorded during the understand phase.

    Args:
        tool_context: The ADK tool context for accessing shared state.

    Returns:
        Validation results for row counts, or an error message.
    """
    try:
        proposals = tool_context.state.get("proposed_tables", {})
        if not proposals:
            return "No proposed tables to validate."

        bronze_dataset = tool_context.state.get("bq_bronze_dataset", "")
        results = {}
        all_passed = True

        for table_name, proposal in proposals.items():
            expected_rows = proposal.get("row_count", 0)
            actual_rows = get_table_row_count(table_name, bronze_dataset)

            if actual_rows is None:
                status = "SKIP"
                message = "Table does not exist or cannot be queried"
                all_passed = False
            elif expected_rows == 0:
                status = "WARN"
                message = "Expected row count unknown"
            elif actual_rows == expected_rows:
                status = "PASS"
                message = f"{actual_rows} rows (exact match)"
            elif abs(actual_rows - expected_rows) <= 1:
                # Allow off-by-one for header row differences
                status = "PASS"
                message = f"{actual_rows} rows (within 1 of expected {expected_rows})"
            elif expected_rows == MAX_SAMPLE_ROWS and actual_rows > expected_rows:
                # Expected count was capped at the sample limit during schema
                # inference — the full file has more rows, which is expected.
                status = "PASS"
                message = (
                    f"{actual_rows} rows (expected was sample-capped at "
                    f"{MAX_SAMPLE_ROWS}; full file is larger)"
                )
            else:
                status = "FAIL"
                message = f"Expected {expected_rows}, got {actual_rows}"
                all_passed = False

            results[table_name] = {
                "status": status,
                "expected": expected_rows,
                "actual": actual_rows,
                "message": message,
            }

        # Store results
        validation = dict(tool_context.state.get("validation_results", {}))
        validation["counts"] = results
        tool_context.state["validation_results"] = validation

        summary = "Row count validation:\n"
        for table, result in results.items():
            icon = {"PASS": "OK", "FAIL": "FAIL", "WARN": "WARN", "SKIP": "SKIP"}[result["status"]]
            summary += f"  [{icon}] {table}: {result['message']}\n"

        summary += f"\nOverall: {'PASSED' if all_passed else 'ISSUES FOUND'}\n"
        return summary

    except Exception as e:
        return log_tool_error("validate_counts", e)
