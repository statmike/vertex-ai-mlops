import io
import logging

import pandas as pd
from google.adk import tools

from agent_acquire.tools.util_common import log_tool_error
from agent_acquire.tools.util_gcs import download_bytes
from agent_orchestrator.config import (
    BQ_BRONZE_DATASET,
    BQ_DATASET_LOCATION,
    GOOGLE_CLOUD_PROJECT,
    gcs_bucket_name,
)
from agent_orchestrator.util_metadata import write_processing_log

from .util_sql import GCS_FORMAT_MAP

# Extensions that need pandas-based loading (no BQ external table support).
_PANDAS_LOAD_EXTENSIONS = {"xlsx", "xls", "xml"}

logger = logging.getLogger(__name__)


async def create_external_tables(
    tool_context: tools.ToolContext,
) -> str:
    """Create BigQuery external tables pointing to GCS source files.

    For each proposed table, creates an external table named ``ext_{table_name}``
    in a separate staging dataset. The external table uses ``autodetect=True``
    so BQ infers the schema from the source file. Keeping external tables in
    the staging dataset keeps the bronze dataset clean for downstream consumers.

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

        # Read staging dataset from state (set by initialize_source)
        staging_dataset = tool_context.state.get("bq_staging_dataset", "")
        if not staging_dataset:
            # Fallback: derive from bronze dataset name
            bronze_dataset = tool_context.state.get("bq_bronze_dataset", BQ_BRONZE_DATASET)
            staging_dataset = bronze_dataset.replace("_bronze", "_staging")

        # Ensure staging dataset exists
        dataset_ref = f"{GOOGLE_CLOUD_PROJECT}.{staging_dataset}"
        dataset = bigquery.Dataset(dataset_ref)
        dataset.location = BQ_DATASET_LOCATION
        client.create_dataset(dataset, exists_ok=True)

        external_tables = {}
        created = []
        skipped = []
        source_id = tool_context.state.get("source_id", "")
        bucket = gcs_bucket_name()

        for table_name, proposal in proposals.items():
            # Support grouped tables with source_paths (list) or legacy source_path (string)
            source_paths = proposal.get("source_paths", [])
            if not source_paths:
                sp = proposal.get("source_path", "")
                source_paths = [sp] if sp else []

            if not source_paths:
                skipped.append(f"{table_name}: no source_path(s)")
                continue

            # Determine file extension from first file (strip #SheetName suffix)
            first_path = source_paths[0].split("#")[0] if "#" in source_paths[0] else source_paths[0]
            ext = first_path.rsplit(".", 1)[-1].lower() if "." in first_path else ""

            # Headerless CSVs need the pandas path because BQ autodetect
            # assigns different generic column names than our schema uses.
            # CSVs with special chars in column names also need the pandas path
            # because BQ autodetect normalizes names (e.g. spaces → underscores)
            # which causes "Unrecognized name" errors in the SQL.
            is_headerless = proposal.get("headerless", False)
            enriched = proposal.get("enriched_columns", proposal.get("columns", []))
            has_special_chars = any(
                not col.get("source_name", col["name"]).replace("_", "").isalnum()
                for col in enriched
            )

            if ext in _PANDAS_LOAD_EXTENSIONS or is_headerless or has_special_chars:
                # Pandas load path for formats BQ external tables can't handle
                # (xlsx/xls/xml) and headerless CSVs (BQ autodetect assigns
                # different generic column names than our schema uses).
                try:
                    frames = []
                    for source_path in source_paths:
                        # Parse optional #SheetName suffix for multi-sheet xlsx
                        sheet_name = 0  # default: first sheet
                        actual_path = source_path
                        if "#" in source_path and ext in ("xlsx", "xls", "xlsm", "xlsb"):
                            actual_path, sheet_name = source_path.rsplit("#", 1)

                        clean_path = actual_path
                        if clean_path.startswith("gs://"):
                            parts = clean_path.split("/", 3)
                            clean_path = parts[3] if len(parts) > 3 else clean_path
                        if clean_path.startswith(bucket + "/"):
                            clean_path = clean_path[len(bucket) + 1:]
                        data = download_bytes(clean_path)
                        if ext == "xml":
                            df = pd.read_xml(io.BytesIO(data), parser="etree")
                        elif ext in ("xlsx", "xls", "xlsm", "xlsb"):
                            df = pd.read_excel(io.BytesIO(data), sheet_name=sheet_name)
                        elif is_headerless:
                            sep = "\t" if ext == "tsv" else ","
                            df = pd.read_csv(io.BytesIO(data), sep=sep, header=None)
                            df.columns = [f"col_{i}" for i in range(len(df.columns))]
                        else:
                            sep = "\t" if ext == "tsv" else ","
                            df = pd.read_csv(io.BytesIO(data), sep=sep)
                        frames.append(df)

                    combined = pd.concat(frames, ignore_index=True) if len(frames) > 1 else frames[0]

                    # Rename DataFrame columns to sanitized names from proposal
                    # so the staging table matches what build_select_sql expects.
                    enriched = proposal.get("enriched_columns", proposal.get("columns", []))
                    rename_map = {}
                    for col in enriched:
                        src = col.get("source_name", col["name"])
                        tgt = col["name"]
                        if src in combined.columns and src != tgt:
                            rename_map[src] = tgt
                    if rename_map:
                        combined = combined.rename(columns=rename_map)
                        for col in enriched:
                            if col.get("source_name") in rename_map:
                                col["source_name"] = rename_map[col["source_name"]]

                    # Deduplicate DataFrame column names (xlsx files can have
                    # duplicate headers, and rename_map can produce duplicates).
                    cols = list(combined.columns)
                    seen: dict[str, int] = {}
                    deduped = []
                    for c in cols:
                        if c in seen:
                            seen[c] += 1
                            deduped.append(f"{c}_{seen[c]}")
                        else:
                            seen[c] = 0
                            deduped.append(c)
                    if deduped != cols:
                        combined.columns = deduped

                    stg_table_name = f"ext_{table_name}"
                    stg_table_id = f"{GOOGLE_CLOUD_PROJECT}.{staging_dataset}.{stg_table_name}"

                    job_config = bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE")

                    # Resilient load: if pyarrow serialization fails, identify
                    # problematic columns, coerce to string, and retry. If still
                    # failing, drop the column entirely and document the omission.
                    omitted_columns = []
                    coerced_columns = []
                    try:
                        load_job = client.load_table_from_dataframe(
                            combined, stg_table_id, job_config=job_config,
                        )
                        load_job.result()
                    except Exception as load_err:
                        load_err_msg = str(load_err)
                        logger.info(
                            f"Initial load failed for {table_name}, "
                            f"attempting column-level recovery: {load_err}"
                        )
                        # Identify problematic columns by trying pyarrow conversion
                        import pyarrow as pa
                        for col_name in list(combined.columns):
                            try:
                                pa.array(combined[col_name])
                            except Exception:
                                # Try coercing to string first
                                try:
                                    combined[col_name] = combined[col_name].astype(str)
                                    pa.array(combined[col_name])
                                    coerced_columns.append(col_name)
                                    logger.info(f"  Coerced {col_name} to STRING")
                                except Exception:
                                    omitted_columns.append(col_name)
                                    combined = combined.drop(columns=[col_name])
                                    logger.warning(f"  Omitted unparseable column {col_name}")

                        # Also update enriched_columns to reflect omissions
                        if omitted_columns:
                            enriched[:] = [
                                c for c in enriched
                                if c["name"] not in omitted_columns
                            ]

                        # Retry load with cleaned DataFrame
                        load_job = client.load_table_from_dataframe(
                            combined, stg_table_id, job_config=job_config,
                        )
                        load_job.result()

                    external_tables[table_name] = stg_table_id
                    status_parts = [f"{stg_table_name} → loaded from .{ext} ({len(combined)} rows)"]
                    if coerced_columns:
                        status_parts.append(f"coerced to STRING: {coerced_columns}")
                    if omitted_columns:
                        status_parts.append(f"OMITTED columns: {omitted_columns}")
                    created.append("; ".join(status_parts))

                    # Store recovery info on the proposal for downstream
                    # documentation and surface in processing_log.
                    if omitted_columns or coerced_columns:
                        proposal["column_recovery"] = {
                            "coerced_to_string": coerced_columns,
                            "omitted": omitted_columns,
                        }
                        if source_id:
                            write_processing_log(
                                source_id, "implement", "column_recovery", "completed",
                                details={
                                    "table": table_name,
                                    "coerced_to_string": coerced_columns,
                                    "omitted": omitted_columns,
                                    "reason": load_err_msg,
                                },
                            )

                except Exception as e:
                    logger.warning(f"Failed to load table for {table_name}: {e}")
                    skipped.append(f"{table_name}: {e}")

            elif ext in GCS_FORMAT_MAP:
                # Standard formats: create BQ external table
                try:
                    bq_format, format_options = GCS_FORMAT_MAP[ext]

                    # Build GCS URIs for all source files
                    gcs_uris = []
                    for source_path in source_paths:
                        clean_path = source_path
                        if clean_path.startswith("gs://"):
                            parts = clean_path.split("/", 3)
                            clean_path = parts[3] if len(parts) > 3 else clean_path
                        if clean_path.startswith(bucket + "/"):
                            clean_path = clean_path[len(bucket) + 1:]
                        gcs_uris.append(f"gs://{bucket}/{clean_path}")

                    # Configure external table with all source URIs
                    external_config = bigquery.ExternalConfig(bq_format)
                    external_config.source_uris = gcs_uris
                    external_config.autodetect = True

                    # Apply format-specific options
                    if bq_format == "CSV":
                        csv_opts = external_config.options
                        if "skip_leading_rows" in format_options:
                            csv_opts.skip_leading_rows = format_options["skip_leading_rows"]
                        if "field_delimiter" in format_options:
                            csv_opts.field_delimiter = format_options["field_delimiter"]

                    ext_table_name = f"ext_{table_name}"
                    ext_table_id = f"{GOOGLE_CLOUD_PROJECT}.{staging_dataset}.{ext_table_name}"

                    table_obj = bigquery.Table(ext_table_id)
                    table_obj.external_data_configuration = external_config

                    client.create_table(table_obj, exists_ok=True)

                    external_tables[table_name] = ext_table_id
                    uri_summary = gcs_uris[0] if len(gcs_uris) == 1 else f"{gcs_uris[0]} (+{len(gcs_uris)-1} more)"
                    created.append(f"{ext_table_name} → {uri_summary}")
                except Exception as e:
                    logger.warning(f"Failed to create external table for {table_name}: {e}")
                    skipped.append(f"{table_name}: {e}")

            else:
                skipped.append(f"{table_name}: unsupported format '.{ext}'")

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
