"""Populate context chunks for semantic search from generated documentation.

Reads ``generated_docs`` from state (set by ``generate_documentation``),
chunks each table's documentation, and inserts into the
``context_chunks`` table for the Catalog Explorer agent.
"""

import logging

from google.adk import tools

from agent_orchestrator.config import BQ_BRONZE_DATASET, GOOGLE_CLOUD_PROJECT
from agent_orchestrator.util_context_chunks import (
    chunk_table_documentation,
    ensure_context_dataset,
    insert_context_chunks,
)
from agent_orchestrator.util_metadata import write_processing_log

logger = logging.getLogger(__name__)


async def populate_context_chunks(
    tool_context: tools.ToolContext,
) -> str:
    """Chunk generated documentation and insert into the context_chunks table.

    Reads ``generated_docs`` from state (set by ``generate_documentation``)
    and ``bq_bronze_dataset`` to create searchable chunks for the Catalog
    Explorer agent's semantic search.

    Must be called after ``generate_documentation`` has completed.

    Args:
        tool_context: The ADK tool context for accessing shared state.

    Returns:
        Summary of chunks created, or an error message.
    """
    try:
        generated_docs = tool_context.state.get("generated_docs", {})
        if not generated_docs:
            return "No generated documentation found. Run generate_documentation first."

        if not GOOGLE_CLOUD_PROJECT:
            return "Cannot populate context: GOOGLE_CLOUD_PROJECT not set."

        bronze_dataset = tool_context.state.get("bq_bronze_dataset", BQ_BRONZE_DATASET)

        # Ensure context dataset and table exist
        ensure_context_dataset()

        # Chunk all table documentation
        all_chunks = []
        for table_name, doc_info in generated_docs.items():
            chunks = chunk_table_documentation(
                dataset_name=bronze_dataset,
                table_name=table_name,
                documentation_md=doc_info.get("documentation_md", ""),
                column_details=doc_info.get("column_details", []),
                related_tables=doc_info.get("related_tables"),
            )
            all_chunks.extend(chunks)

        # Insert all chunks
        inserted = insert_context_chunks(all_chunks)

        # Log to processing_log
        source_id = tool_context.state.get("source_id", "")
        if source_id:
            write_processing_log(
                source_id, "implement", "populate_context_chunks", "completed",
                details={
                    "tables_chunked": len(generated_docs),
                    "chunks_created": len(all_chunks),
                    "chunks_inserted": inserted,
                },
            )

        return (
            f"Context chunks populated.\n"
            f"  Tables chunked: {len(generated_docs)}\n"
            f"  Chunks created: {len(all_chunks)}\n"
            f"  Chunks inserted: {inserted}\n"
        )

    except Exception as e:
        return f"Error populating context chunks: {e}"
