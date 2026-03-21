import datetime
import json
import logging
import uuid

from google.adk import tools

from agent_acquire.tools.util_common import log_tool_error
from agent_orchestrator.config import (
    BQ_META_DATASET,
    GOOGLE_CLOUD_PROJECT,
)
from agent_orchestrator.util_metadata import write_processing_log

logger = logging.getLogger(__name__)


async def record_decisions(
    tool_context: tools.ToolContext,
) -> str:
    """
    Record schema design decisions to the BQ metadata tables.

    Writes each proposed table design to the schema_decisions table
    with status 'proposed', for later approval tracking.

    Args:
        tool_context: The ADK tool context for accessing shared state.

    Returns:
        Confirmation of recorded decisions, or an error message.
    """
    try:
        proposals = tool_context.state.get("proposed_tables", {})
        source_id = tool_context.state.get("source_id", "")

        if not proposals:
            return "No proposals to record."

        if not GOOGLE_CLOUD_PROJECT:
            return "Decisions recorded in state only (GOOGLE_CLOUD_PROJECT not set)."

        from google.cloud import bigquery

        client = bigquery.Client(project=GOOGLE_CLOUD_PROJECT)
        table_id = f"{GOOGLE_CLOUD_PROJECT}.{BQ_META_DATASET}.schema_decisions"

        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        rows_to_insert = []
        for table_name, proposal in proposals.items():
            decision_id = str(uuid.uuid4())
            rows_to_insert.append({
                "decision_id": decision_id,
                "source_id": source_id,
                "table_name": table_name,
                "proposal": json.dumps(proposal),
                "reasoning": proposal.get("description", ""),
                "status": "proposed",
                "created_at": now,
            })

        if rows_to_insert:
            errors = client.insert_rows_json(table_id, rows_to_insert)
            if errors:
                logger.warning(f"BQ insert errors: {errors}")
                return f"Warning: Some records failed to insert: {errors}"

        write_processing_log(
            source_id, "design", "record_decisions", "completed",
            details={"tables": list(proposals.keys())},
        )

        return (
            f"Recorded {len(rows_to_insert)} design decision(s) to BQ.\n"
            f"  Table: {table_id}\n"
            f"  Status: proposed (awaiting human approval)\n"
            + "\n".join(f"  - {name}" for name in proposals)
        )

    except Exception as e:
        return log_tool_error("record_decisions", e)
