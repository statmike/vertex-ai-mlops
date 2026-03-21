from .function_tool_apply_bq_metadata import apply_bq_metadata
from .function_tool_create_external_tables import create_external_tables
from .function_tool_execute_sql import execute_sql
from .function_tool_generate_documentation import generate_documentation
from .function_tool_publish_lineage import publish_lineage
from .function_tool_update_changelog import update_changelog

TOOLS = [
    create_external_tables,
    execute_sql,
    publish_lineage,
    apply_bq_metadata,
    generate_documentation,
    update_changelog,
]
