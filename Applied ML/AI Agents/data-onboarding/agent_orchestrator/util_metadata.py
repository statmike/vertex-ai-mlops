"""BQ metadata table management for data onboarding lineage tracking.

Manages 5 tables in the {BQ_BRONZE_META_DATASET} dataset:
  - source_manifest: Every file tracked (path, hash, type, classification)
  - processing_log: Every pipeline action (phase, status, timestamps)
  - table_lineage: BQ table → source file mappings
  - schema_decisions: Design proposals, approval status, reasoning
  - web_provenance: URL crawl graph, page metadata

Auto-creates dataset and tables on first import.
"""

import logging

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
  discovered_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP() OPTIONS(description="When the file was first discovered."),
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP() OPTIONS(description="Last update timestamp.")
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
  started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP() OPTIONS(description="When the action started."),
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
  source_file STRING NOT NULL OPTIONS(description="GCS path of the source file."),
  column_mappings JSON OPTIONS(description="Source column to BQ column mapping."),
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP() OPTIONS(description="When the lineage was recorded.")
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
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP() OPTIONS(description="When proposed."),
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
  crawled_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP() OPTIONS(description="When the URL was crawled.")
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

    except Exception as e:
        logger.warning(f"Metadata: Auto-setup failed ({e}).")


# Run auto-setup on import
_ensure_metadata_setup()
