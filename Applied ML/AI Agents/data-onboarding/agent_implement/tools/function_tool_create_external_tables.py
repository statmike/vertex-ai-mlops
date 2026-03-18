import logging

from google.adk import tools

from agent_acquire.tools.util_common import log_tool_error
from agent_orchestrator.config import (
    BQ_BRONZE_DATASET,
    BQ_DATASET_LOCATION,
    GOOGLE_CLOUD_PROJECT,
    gcs_bucket_name,
)
from agent_orchestrator.util_metadata import write_processing_log

from .util_sql import GCS_FORMAT_MAP

logger = logging.getLogger(__name__)


async def create_external_tables(
    tool_context: tools.ToolContext,
) -> str:
    """Create BigQuery external tables pointing to GCS source files.

    For each proposed table, creates an external table named ``ext_{table_name}``
    in the bronze dataset. The external table uses ``autodetect=True`` so BQ
    infers the schema from the source file.

    Args:
        tool_context: The ADK tool context for accessing shared state.

    Returns:
        Summary of created external tables, or an error message.
    """
    try:
        proposals = tool_context.state.get("proposed_tables", {})
        if not proposals:
            return "No proposed tables. Run the design phase first."

        if not GOOGLE_CLOUD_PROJECT:
            return "Cannot create external tables: GOOGLE_CLOUD_PROJECT not set."

        from google.cloud import bigquery

        client = bigquery.Client(project=GOOGLE_CLOUD_PROJECT)

        # Ensure bronze dataset exists
        dataset_ref = f"{GOOGLE_CLOUD_PROJECT}.{BQ_BRONZE_DATASET}"
        dataset = bigquery.Dataset(dataset_ref)
        dataset.location = BQ_DATASET_LOCATION
        client.create_dataset(dataset, exists_ok=True)

        external_tables = {}
        created = []
        skipped = []
        source_id = tool_context.state.get("source_id", "")
        bucket = gcs_bucket_name()

        for table_name, proposal in proposals.items():
            source_path = proposal.get("source_path", "")
            if not source_path:
                skipped.append(f"{table_name}: no source_path")
                continue

            # Determine file extension
            ext = source_path.rsplit(".", 1)[-1].lower() if "." in source_path else ""
            if ext not in GCS_FORMAT_MAP:
                skipped.append(f"{table_name}: unsupported format '.{ext}'")
                continue

            bq_format, format_options = GCS_FORMAT_MAP[ext]

            # Build full GCS URI
            if source_path.startswith("gs://"):
                gcs_uri = source_path
            else:
                gcs_uri = f"gs://{bucket}/{source_path}"

            # Configure external table
            external_config = bigquery.ExternalConfig(bq_format)
            external_config.source_uris = [gcs_uri]
            external_config.autodetect = True

            # Apply format-specific options
            if bq_format == "CSV":
                csv_opts = external_config.options
                if "skip_leading_rows" in format_options:
                    csv_opts.skip_leading_rows = format_options["skip_leading_rows"]
                if "field_delimiter" in format_options:
                    csv_opts.field_delimiter = format_options["field_delimiter"]

            ext_table_name = f"ext_{table_name}"
            ext_table_id = f"{GOOGLE_CLOUD_PROJECT}.{BQ_BRONZE_DATASET}.{ext_table_name}"

            table_obj = bigquery.Table(ext_table_id)
            table_obj.external_data_configuration = external_config

            client.create_table(table_obj, exists_ok=True)

            external_tables[table_name] = ext_table_id
            created.append(f"{ext_table_name} → {gcs_uri}")

        tool_context.state["external_tables"] = external_tables

        # Write processing log
        if source_id:
            write_processing_log(
                source_id, "implement", "create_external_tables", "completed",
                details={"created": len(created), "skipped": len(skipped)},
            )

        result = f"External tables created: {len(created)}, skipped: {len(skipped)}\n"
        if created:
            result += "\nCreated:\n"
            for c in created:
                result += f"  - {c}\n"
        if skipped:
            result += "\nSkipped:\n"
            for s in skipped:
                result += f"  - {s}\n"

        return result

    except Exception as e:
        return log_tool_error("create_external_tables", e)
