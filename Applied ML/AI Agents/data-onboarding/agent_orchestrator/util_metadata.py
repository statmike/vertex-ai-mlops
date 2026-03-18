"""BQ metadata table management for data onboarding lineage tracking.

Manages 5 tables in the {BQ_BRONZE_META_DATASET} dataset:
  - source_manifest: Every file tracked (path, hash, type, classification)
  - processing_log: Every pipeline action (phase, status, timestamps)
  - table_lineage: BQ table → source file mappings
  - schema_decisions: Design proposals, approval status, reasoning
  - web_provenance: URL crawl graph, page metadata

Auto-creates dataset and tables on first import.
"""

import datetime
import json
import logging
import uuid

from .config import BQ_BRONZE_META_DATASET, BQ_DATASET_LOCATION, GOOGLE_CLOUD_PROJECT

logger = logging.getLogger(__name__)

FULL_DATASET_ID = (
    f"{GOOGLE_CLOUD_PROJECT}.{BQ_BRONZE_META_DATASET}" if GOOGLE_CLOUD_PROJECT else None
)

# --- Table DDLs ---

TABLE_DDLS = {}

if FULL_DATASET_ID:
    TABLE_DDLS = {
        "source_manifest": f"""
CREATE TABLE IF NOT EXISTS `{FULL_DATASET_ID}.source_manifest`
(
  source_id STRING NOT NULL OPTIONS(description="Unique identifier for the onboarding source."),
  file_path STRING NOT NULL OPTIONS(description="GCS path to the staged file."),
  file_hash STRING OPTIONS(description="SHA-256 hash of the file contents."),
  file_size_bytes INT64 OPTIONS(description="File size in bytes."),
  file_type STRING OPTIONS(description="File extension (e.g., csv, json, pdf)."),
  classification STRING OPTIONS(description="'data' or 'context'."),
  original_url STRING OPTIONS(description="Original URL if acquired from the web."),
  discovered_at TIMESTAMP NOT NULL OPTIONS(description="When the file was first discovered."),
  updated_at TIMESTAMP NOT NULL OPTIONS(description="Last update timestamp.")
)
PARTITION BY DATE(discovered_at)
CLUSTER BY source_id, classification;
""",
        "processing_log": f"""
CREATE TABLE IF NOT EXISTS `{FULL_DATASET_ID}.processing_log`
(
  log_id STRING NOT NULL OPTIONS(description="Unique log entry ID."),
  source_id STRING NOT NULL OPTIONS(description="Source being processed."),
  phase STRING NOT NULL OPTIONS(description="Pipeline phase (acquire, discover, understand, design, implement, validate)."),
  action STRING NOT NULL OPTIONS(description="Specific action taken."),
  status STRING NOT NULL OPTIONS(description="'started', 'completed', 'failed'."),
  details JSON OPTIONS(description="Action-specific details."),
  started_at TIMESTAMP NOT NULL OPTIONS(description="When the action started."),
  completed_at TIMESTAMP OPTIONS(description="When the action completed.")
)
PARTITION BY DATE(started_at)
CLUSTER BY source_id, phase;
""",
        "table_lineage": f"""
CREATE TABLE IF NOT EXISTS `{FULL_DATASET_ID}.table_lineage`
(
  lineage_id STRING NOT NULL OPTIONS(description="Unique lineage entry ID."),
  source_id STRING NOT NULL OPTIONS(description="Source identifier."),
  bq_table STRING NOT NULL OPTIONS(description="Fully qualified BQ table name."),
  external_table STRING OPTIONS(description="Fully qualified BQ external table name (ext_*)."),
  source_file STRING NOT NULL OPTIONS(description="GCS path of the source file."),
  column_mappings JSON OPTIONS(description="Source column to BQ column mapping."),
  created_at TIMESTAMP NOT NULL OPTIONS(description="When the lineage was recorded.")
)
PARTITION BY DATE(created_at)
CLUSTER BY source_id, bq_table;
""",
        "schema_decisions": f"""
CREATE TABLE IF NOT EXISTS `{FULL_DATASET_ID}.schema_decisions`
(
  decision_id STRING NOT NULL OPTIONS(description="Unique decision ID."),
  source_id STRING NOT NULL OPTIONS(description="Source identifier."),
  table_name STRING NOT NULL OPTIONS(description="Proposed BQ table name."),
  proposal JSON NOT NULL OPTIONS(description="Full table schema proposal."),
  reasoning STRING OPTIONS(description="Why this design was chosen."),
  status STRING NOT NULL OPTIONS(description="'proposed', 'approved', 'rejected', 'modified'."),
  approved_by STRING OPTIONS(description="Who approved (user or auto)."),
  created_at TIMESTAMP NOT NULL OPTIONS(description="When proposed."),
  decided_at TIMESTAMP OPTIONS(description="When approved/rejected.")
)
PARTITION BY DATE(created_at)
CLUSTER BY source_id, status;
""",
        "web_provenance": f"""
CREATE TABLE IF NOT EXISTS `{FULL_DATASET_ID}.web_provenance`
(
  provenance_id STRING NOT NULL OPTIONS(description="Unique provenance ID."),
  source_id STRING NOT NULL OPTIONS(description="Source identifier."),
  url STRING NOT NULL OPTIONS(description="The URL that was crawled."),
  parent_url STRING OPTIONS(description="URL that linked to this one."),
  page_title STRING OPTIONS(description="HTML title of the page."),
  content_type STRING OPTIONS(description="HTTP content-type header."),
  status_code INT64 OPTIONS(description="HTTP response status code."),
  links_found INT64 OPTIONS(description="Number of links extracted from this page."),
  files_downloaded INT64 OPTIONS(description="Number of files downloaded from this page."),
  crawled_at TIMESTAMP NOT NULL OPTIONS(description="When the URL was crawled.")
)
PARTITION BY DATE(crawled_at)
CLUSTER BY source_id;
""",
    }


def _ensure_metadata_setup():
    """Create the metadata dataset and all 5 tables if they don't exist."""
    if not GOOGLE_CLOUD_PROJECT:
        logger.warning("Metadata: GOOGLE_CLOUD_PROJECT not set, skipping auto-setup.")
        return

    try:
        from google.cloud import bigquery

        client = bigquery.Client(project=GOOGLE_CLOUD_PROJECT)

        # Check/create dataset
        try:
            client.get_dataset(FULL_DATASET_ID)
            logger.info(f"Metadata: Dataset '{FULL_DATASET_ID}' exists.")
        except Exception as e:
            if "Not found" in str(e):
                logger.info(f"Metadata: Creating dataset '{FULL_DATASET_ID}'...")
                dataset = bigquery.Dataset(FULL_DATASET_ID)
                dataset.location = BQ_DATASET_LOCATION
                dataset.description = "Data Onboarding metadata — lineage, provenance, decisions"
                client.create_dataset(dataset, exists_ok=True)
                logger.info(f"Metadata: Dataset '{FULL_DATASET_ID}' created.")
            else:
                raise

        # Check/create each table
        for table_name, ddl in TABLE_DDLS.items():
            full_table = f"{FULL_DATASET_ID}.{table_name}"
            try:
                client.get_table(full_table)
                logger.info(f"Metadata: Table '{full_table}' exists.")
            except Exception as e:
                if "Not found" in str(e):
                    logger.info(f"Metadata: Creating table '{full_table}'...")
                    query_job = client.query(ddl)
                    query_job.result()
                    logger.info(f"Metadata: Table '{full_table}' created.")
                else:
                    raise

        # Schema migration: add external_table column to table_lineage if missing
        try:
            migrate_ddl = (
                f"ALTER TABLE `{FULL_DATASET_ID}.table_lineage` "
                "ADD COLUMN IF NOT EXISTS external_table STRING "
                'OPTIONS(description="Fully qualified BQ external table name (ext_*).")'
            )
            client.query(migrate_ddl).result()
        except Exception as e:
            logger.debug(f"Metadata: table_lineage migration skipped ({e})")

    except Exception as e:
        logger.warning(f"Metadata: Auto-setup failed ({e}).")


# Run auto-setup on import
_ensure_metadata_setup()


def write_source_manifest(rows: list[dict]) -> int:
    """Insert file records into the source_manifest table.

    Each row should contain: source_id, file_path, file_hash, file_size_bytes,
    file_type, classification, original_url.

    Returns the number of rows inserted, or 0 on failure.
    """
    if not GOOGLE_CLOUD_PROJECT:
        logger.warning("write_source_manifest: GOOGLE_CLOUD_PROJECT not set, skipping.")
        return 0

    try:
        from google.cloud import bigquery

        client = bigquery.Client(project=GOOGLE_CLOUD_PROJECT)
        table_id = f"{FULL_DATASET_ID}.source_manifest"

        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        rows_to_insert = []
        for row in rows:
            rows_to_insert.append({
                "source_id": row.get("source_id", ""),
                "file_path": row.get("file_path", ""),
                "file_hash": row.get("file_hash", ""),
                "file_size_bytes": row.get("file_size_bytes", 0),
                "file_type": row.get("file_type", ""),
                "classification": row.get("classification", ""),
                "original_url": row.get("original_url", ""),
                "discovered_at": now,
                "updated_at": now,
            })

        if not rows_to_insert:
            return 0

        errors = client.insert_rows_json(table_id, rows_to_insert)
        if errors:
            logger.warning(f"write_source_manifest insert errors: {errors}")
            return 0
        return len(rows_to_insert)

    except Exception as e:
        logger.warning(f"write_source_manifest failed: {e}")
        return 0


def write_processing_log(
    source_id: str,
    phase: str,
    action: str,
    status: str,
    details: dict | None = None,
) -> str:
    """Insert a single processing log entry.

    Returns the generated log_id, or "" on failure.
    """
    if not GOOGLE_CLOUD_PROJECT:
        logger.warning("write_processing_log: GOOGLE_CLOUD_PROJECT not set, skipping.")
        return ""

    try:
        from google.cloud import bigquery

        client = bigquery.Client(project=GOOGLE_CLOUD_PROJECT)
        table_id = f"{FULL_DATASET_ID}.processing_log"

        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        log_id = str(uuid.uuid4())
        row = {
            "log_id": log_id,
            "source_id": source_id,
            "phase": phase,
            "action": action,
            "status": status,
            "started_at": now,
        }
        if details is not None:
            row["details"] = json.dumps(details)

        errors = client.insert_rows_json(table_id, [row])
        if errors:
            logger.warning(f"write_processing_log insert errors: {errors}")
            return ""
        return log_id

    except Exception as e:
        logger.warning(f"write_processing_log failed: {e}")
        return ""


def write_table_lineage(rows: list[dict]) -> int:
    """Insert BQ table → source file lineage mappings.

    Each row should contain: source_id, bq_table, source_file, column_mappings (dict),
    and optionally external_table.

    Returns the number of rows inserted, or 0 on failure.
    """
    if not GOOGLE_CLOUD_PROJECT:
        logger.warning("write_table_lineage: GOOGLE_CLOUD_PROJECT not set, skipping.")
        return 0

    try:
        from google.cloud import bigquery

        client = bigquery.Client(project=GOOGLE_CLOUD_PROJECT)
        table_id = f"{FULL_DATASET_ID}.table_lineage"

        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        rows_to_insert = []
        for row in rows:
            lineage_id = str(uuid.uuid4())
            entry = {
                "lineage_id": lineage_id,
                "source_id": row.get("source_id", ""),
                "bq_table": row.get("bq_table", ""),
                "source_file": row.get("source_file", ""),
                "created_at": now,
            }
            ext_table = row.get("external_table")
            if ext_table:
                entry["external_table"] = ext_table
            col_mappings = row.get("column_mappings")
            if col_mappings is not None:
                entry["column_mappings"] = json.dumps(col_mappings)
            rows_to_insert.append(entry)

        if not rows_to_insert:
            return 0

        errors = client.insert_rows_json(table_id, rows_to_insert)
        if errors:
            logger.warning(f"write_table_lineage insert errors: {errors}")
            return 0
        return len(rows_to_insert)

    except Exception as e:
        logger.warning(f"write_table_lineage failed: {e}")
        return 0


def write_web_provenance(rows: list[dict]) -> int:
    """Insert crawl graph edges into the web_provenance table.

    Each row should contain: source_id, url, parent_url, page_title,
    content_type, status_code, links_found, files_downloaded.

    Returns the number of rows inserted, or 0 on failure.
    """
    if not GOOGLE_CLOUD_PROJECT:
        logger.warning("write_web_provenance: GOOGLE_CLOUD_PROJECT not set, skipping.")
        return 0

    try:
        from google.cloud import bigquery

        client = bigquery.Client(project=GOOGLE_CLOUD_PROJECT)
        table_id = f"{FULL_DATASET_ID}.web_provenance"

        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        rows_to_insert = []
        for row in rows:
            provenance_id = str(uuid.uuid4())
            rows_to_insert.append({
                "provenance_id": provenance_id,
                "source_id": row.get("source_id", ""),
                "url": row.get("url", ""),
                "parent_url": row.get("parent_url"),
                "page_title": row.get("page_title"),
                "content_type": row.get("content_type"),
                "status_code": row.get("status_code"),
                "links_found": row.get("links_found"),
                "files_downloaded": row.get("files_downloaded"),
                "crawled_at": now,
            })

        if not rows_to_insert:
            return 0

        errors = client.insert_rows_json(table_id, rows_to_insert)
        if errors:
            logger.warning(f"write_web_provenance insert errors: {errors}")
            return 0
        return len(rows_to_insert)

    except Exception as e:
        logger.warning(f"write_web_provenance failed: {e}")
        return 0
