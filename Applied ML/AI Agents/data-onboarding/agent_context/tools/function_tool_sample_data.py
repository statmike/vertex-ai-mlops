"""Run short read-only BigQuery queries to verify table contents."""

import logging
import re

from google.adk import tools

from agent_orchestrator.config import GOOGLE_CLOUD_PROJECT

logger = logging.getLogger(__name__)

# Maximum bytes billed per sample query (50 MB)
_MAX_BYTES_BILLED = 50_000_000

# Patterns that indicate non-read-only statements
_DML_DDL_RE = re.compile(
    r"^\s*(INSERT|UPDATE|DELETE|MERGE|CREATE|DROP|ALTER|TRUNCATE|GRANT|REVOKE)\b",
    re.IGNORECASE,
)


async def sample_data(
    query: str,
    tool_context: tools.ToolContext,
) -> str:
    """Run a short read-only BigQuery query to verify table contents.

    Use this to check categorical values, date ranges, row counts, or
    other quick verifications. Queries are capped at 50 MB bytes billed.

    Args:
        query: A SELECT query to run. Must be read-only (no DML/DDL).
            Should include LIMIT to keep results small.
        tool_context: The ADK tool context.

    Returns:
        Query results formatted as text, or an error message.

    Examples:
        - ``SELECT DISTINCT provider_type FROM `project.dataset.table` LIMIT 20``
        - ``SELECT MIN(effective_date), MAX(effective_date) FROM `project.dataset.table```
        - ``SELECT COUNT(*) FROM `project.dataset.table```
    """
    try:
        if not GOOGLE_CLOUD_PROJECT:
            return "Cannot run query: GOOGLE_CLOUD_PROJECT not set."

        # Reject DML/DDL
        if _DML_DDL_RE.match(query):
            return "Rejected: only SELECT queries are allowed. No DML or DDL statements."

        from google.cloud import bigquery

        client = bigquery.Client(project=GOOGLE_CLOUD_PROJECT)

        job_config = bigquery.QueryJobConfig(
            maximum_bytes_billed=_MAX_BYTES_BILLED,
        )

        result = client.query(query, job_config=job_config).result()
        rows = list(result)

        if not rows:
            return "Query returned no rows."

        # Format as text table
        if rows:
            fields = [field.name for field in result.schema]
            lines = [" | ".join(fields)]
            lines.append(" | ".join("---" for _ in fields))
            for row in rows[:50]:  # Cap display at 50 rows
                lines.append(" | ".join(str(row[f]) for f in fields))
            if len(rows) > 50:
                lines.append(f"... ({len(rows) - 50} more rows)")
            return "\n".join(lines)

    except Exception as e:
        return f"Error running sample query: {e}"
