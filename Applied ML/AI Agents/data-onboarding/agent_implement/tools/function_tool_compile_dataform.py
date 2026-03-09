import logging
import os

from google.adk import tools

from agent_acquire.tools.util_common import log_tool_error

logger = logging.getLogger(__name__)


async def compile_dataform(
    tool_context: tools.ToolContext,
) -> str:
    """
    Validate that generated Dataform SQLX files are syntactically correct.

    Checks that all SQLX files in the Dataform project have valid config blocks
    and SQL. This is a lightweight validation — not a full Dataform compilation.

    Args:
        tool_context: The ADK tool context for accessing shared state.

    Returns:
        Validation results, or an error message.
    """
    try:
        project_path = tool_context.state.get("dataform_project_path", "")
        if not project_path:
            return "Error: No Dataform project path. Run generate_dataform first."

        definitions_dir = os.path.join(project_path, "definitions")
        if not os.path.isdir(definitions_dir):
            return f"Error: definitions directory not found at {definitions_dir}"

        # Check dataform.json exists
        config_path = os.path.join(project_path, "dataform.json")
        if not os.path.isfile(config_path):
            return "Error: dataform.json not found."

        import json

        with open(config_path) as f:
            try:
                config = json.load(f)
            except json.JSONDecodeError as e:
                return f"Error: Invalid dataform.json: {e}"

        # Validate each SQLX file
        issues = []
        valid_files = []

        for fname in sorted(os.listdir(definitions_dir)):
            if not fname.endswith(".sqlx"):
                continue

            fpath = os.path.join(definitions_dir, fname)
            with open(fpath) as f:
                content = f.read()

            # Check for config block
            if "config {" not in content:
                issues.append(f"{fname}: Missing config block")
                continue

            # Check for SELECT statement
            if "SELECT" not in content.upper():
                issues.append(f"{fname}: Missing SELECT statement")
                continue

            # Check config block has required fields
            if 'type:' not in content:
                issues.append(f"{fname}: Config missing 'type' field")
                continue

            valid_files.append(fname)

        result = "Dataform compilation check:\n"
        result += f"  Project: {project_path}\n"
        result += f"  Config: {'valid' if config else 'empty'}\n"
        result += f"  SQLX files: {len(valid_files)} valid\n"

        if issues:
            result += f"  Issues: {len(issues)}\n"
            for issue in issues:
                result += f"    - {issue}\n"
        else:
            result += "  All files passed validation.\n"

        return result

    except Exception as e:
        return log_tool_error("compile_dataform", e)
