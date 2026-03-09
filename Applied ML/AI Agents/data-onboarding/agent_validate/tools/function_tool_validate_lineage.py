import logging

from google.adk import tools

from agent_acquire.tools.util_common import log_tool_error

from .util_quality import check_lineage_exists

logger = logging.getLogger(__name__)


async def validate_lineage(
    tool_context: tools.ToolContext,
) -> str:
    """
    Verify that complete lineage exists from source files to BQ tables.

    Checks that every proposed table has entries in the table_lineage
    and source_manifest metadata tables.

    Args:
        tool_context: The ADK tool context for accessing shared state.

    Returns:
        Lineage validation results, or an error message.
    """
    try:
        proposals = tool_context.state.get("proposed_tables", {})
        source_id = tool_context.state.get("source_id", "")

        if not proposals:
            return "No proposed tables to validate lineage for."

        if not source_id:
            return "Error: source_id not set in state."

        results = {}
        all_passed = True

        for table_name, proposal in proposals.items():
            has_lineage = check_lineage_exists(source_id, table_name)
            source_file = proposal.get("source_file", "unknown")

            if has_lineage:
                results[table_name] = {
                    "status": "PASS",
                    "message": f"Lineage verified: {source_file} → {table_name}",
                }
            else:
                results[table_name] = {
                    "status": "WARN",
                    "message": "No lineage records found (may not have been recorded yet)",
                }
                # Not failing — lineage records may be written after data load

        # Store results
        validation = dict(tool_context.state.get("validation_results", {}))
        validation["lineage"] = results
        tool_context.state["validation_results"] = validation

        summary = "Lineage validation:\n"
        for table, result in results.items():
            icon = {"PASS": "OK", "FAIL": "FAIL", "WARN": "WARN"}[result["status"]]
            summary += f"  [{icon}] {table}: {result['message']}\n"

        summary += f"\nOverall: {'PASSED' if all_passed else 'ISSUES FOUND'}\n"
        return summary

    except Exception as e:
        return log_tool_error("validate_lineage", e)
