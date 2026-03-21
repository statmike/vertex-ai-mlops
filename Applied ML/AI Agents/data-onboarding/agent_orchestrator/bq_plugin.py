# BigQuery Agent Analytics Plugin
#
# Configures the BigQuery Agent Analytics Plugin for logging agent events
# (LLM calls, tool usage, etc.) to BigQuery with optional GCS offloading
# for multimodal content.
#
# Auto-setup: On import, checks if the BigQuery dataset and table exist
# and creates them if needed. No manual setup required —
# just configure .env and run the agent.
#
# Configuration is imported from agent_orchestrator.config for naming consistency.
#
# Reference: https://google.github.io/adk-docs/observability/bigquery-agent-analytics/

import logging

from .config import (
    BQ_ANALYTICS_DATASET,
    BQ_ANALYTICS_TABLE,
    BQ_DATASET_LOCATION,
    GOOGLE_CLOUD_PROJECT,
)

logger = logging.getLogger(__name__)

# Configuration from centralized config
PROJECT_ID = GOOGLE_CLOUD_PROJECT

# Only compute FULL_TABLE_ID when PROJECT_ID is set
FULL_TABLE_ID = f"{PROJECT_ID}.{BQ_ANALYTICS_DATASET}.{BQ_ANALYTICS_TABLE}" if PROJECT_ID else None

# Table DDL (only used when PROJECT_ID is set)
CREATE_TABLE_DDL = (
    f"""
CREATE TABLE IF NOT EXISTS `{FULL_TABLE_ID}`
(
  timestamp TIMESTAMP NOT NULL OPTIONS(description="The UTC time at which the event was logged."),
  event_type STRING OPTIONS(description="Indicates the type of event being logged (e.g., 'LLM_REQUEST', 'TOOL_COMPLETED')."),
  agent STRING OPTIONS(description="The name of the ADK agent or author associated with the event."),
  session_id STRING OPTIONS(description="A unique identifier to group events within a single conversation or user session."),
  invocation_id STRING OPTIONS(description="A unique identifier for each individual agent execution or turn within a session."),
  user_id STRING OPTIONS(description="The identifier of the user associated with the current session."),
  trace_id STRING OPTIONS(description="OpenTelemetry trace ID for distributed tracing."),
  span_id STRING OPTIONS(description="OpenTelemetry span ID for this specific operation."),
  parent_span_id STRING OPTIONS(description="OpenTelemetry parent span ID to reconstruct hierarchy."),
  content JSON OPTIONS(description="The event-specific data (payload) stored as JSON."),
  content_parts ARRAY<STRUCT<
    mime_type STRING,
    uri STRING,
    object_ref STRUCT<
      uri STRING,
      version STRING,
      authorizer STRING,
      details JSON
    >,
    text STRING,
    part_index INT64,
    part_attributes STRING,
    storage_mode STRING
  >> OPTIONS(description="Detailed content parts for multi-modal data."),
  attributes JSON OPTIONS(description="Arbitrary key-value pairs for additional metadata."),
  latency_ms JSON OPTIONS(description="Latency measurements (e.g., total_ms)."),
  status STRING OPTIONS(description="The outcome of the event, typically 'OK' or 'ERROR'."),
  error_message STRING OPTIONS(description="Populated if an error occurs."),
  is_truncated BOOLEAN OPTIONS(description="Flag indicates if content was truncated.")
)
PARTITION BY DATE(timestamp)
CLUSTER BY event_type, agent, user_id;
"""
    if FULL_TABLE_ID
    else ""
)


def _ensure_setup():
    """Check for and create the BigQuery dataset and table if they don't exist."""
    if not PROJECT_ID:
        logger.warning("BQ Analytics: GOOGLE_CLOUD_PROJECT not set, skipping auto-setup.")
        return

    try:
        from google.cloud import bigquery

        client = bigquery.Client(project=PROJECT_ID)
        dataset_ref = f"{PROJECT_ID}.{BQ_ANALYTICS_DATASET}"

        # Check/create dataset
        try:
            client.get_dataset(dataset_ref)
            logger.info(f"BQ Analytics: Dataset '{dataset_ref}' exists.")
        except Exception as e:
            if "Not found" in str(e):
                logger.info(f"BQ Analytics: Creating dataset '{dataset_ref}'...")
                dataset = bigquery.Dataset(dataset_ref)
                dataset.location = BQ_DATASET_LOCATION
                dataset.description = "ADK Agent Analytics - Data Onboarding agent event logs"
                client.create_dataset(dataset, exists_ok=True)
                logger.info(f"BQ Analytics: Dataset '{dataset_ref}' created.")
            else:
                raise

        # Check/create table
        try:
            client.get_table(FULL_TABLE_ID)
            logger.info(f"BQ Analytics: Table '{FULL_TABLE_ID}' exists.")
        except Exception as e:
            if "Not found" in str(e):
                logger.info(f"BQ Analytics: Creating table '{FULL_TABLE_ID}'...")
                query_job = client.query(CREATE_TABLE_DDL)
                query_job.result()
                logger.info(f"BQ Analytics: Table '{FULL_TABLE_ID}' created.")
            else:
                raise

    except Exception as e:
        logger.warning(
            f"BQ Analytics: Auto-setup failed ({e}). Plugin may still work if resources exist."
        )


# Run auto-setup on import
_ensure_setup()

# Create plugin conditionally — None when PROJECT_ID is unset or on error.
# Wrapped in try/except so a plugin failure never crashes the agent.
bq_analytics_plugin = None
if PROJECT_ID:
    try:
        from google.adk.plugins.bigquery_agent_analytics_plugin import (
            BigQueryAgentAnalyticsPlugin,
            BigQueryLoggerConfig,
        )

        bq_config = BigQueryLoggerConfig(
            enabled=True,
            log_multi_modal_content=True,
            max_content_length=32 * 1024,  # 32 KB — keep batches well under BQ Write API 10 MB limit
            batch_size=5,  # smaller batches to avoid "Message size exceed" errors
            shutdown_timeout=30.0,
            log_session_metadata=False,  # session state contains large crawl data with non-serializable keys
        )

        bq_analytics_plugin = BigQueryAgentAnalyticsPlugin(
            project_id=PROJECT_ID,
            dataset_id=BQ_ANALYTICS_DATASET,
            table_id=BQ_ANALYTICS_TABLE,
            config=bq_config,
            location=BQ_DATASET_LOCATION,
        )
    except Exception as e:
        logger.warning(f"BQ Analytics: Plugin creation failed ({e}). Agent will run without analytics.")
else:
    logger.info("BQ Analytics: GOOGLE_CLOUD_PROJECT not set, plugin disabled.")
