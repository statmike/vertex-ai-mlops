# BigQuery Agent Analytics Plugin Configuration
#
# This module configures the BigQuery Agent Analytics Plugin for logging
# agent events (LLM calls, tool usage, etc.) to BigQuery with optional
# GCS offloading for multimodal content (images, large text).
#
# Configuration is read from environment variables (set in .env):
#   - GOOGLE_CLOUD_PROJECT: GCP project ID
#   - GOOGLE_CLOUD_LOCATION: GCP location (default: US)
#   - BQ_ANALYTICS_DATASET: BigQuery dataset name
#   - BQ_ANALYTICS_TABLE: BigQuery table name
#   - BQ_ANALYTICS_GCS_BUCKET: GCS bucket for multimodal content
#   - BQ_ANALYTICS_GCS_PATH: Path prefix within the GCS bucket
#
# Reference: https://google.github.io/adk-docs/observability/bigquery-agent-analytics/

import os
from google.adk.plugins.bigquery_agent_analytics_plugin import (
    BigQueryAgentAnalyticsPlugin,
    BigQueryLoggerConfig,
)

# Configuration from environment variables
PROJECT_ID = os.getenv('GOOGLE_CLOUD_PROJECT')
LOCATION = os.getenv('GOOGLE_CLOUD_LOCATION', 'US')
BQ_ANALYTICS_DATASET = os.getenv('BQ_ANALYTICS_DATASET', 'applied_ml_concept_bq')
BQ_ANALYTICS_TABLE = os.getenv('BQ_ANALYTICS_TABLE', 'agent_events')
BQ_ANALYTICS_GCS_BUCKET = os.getenv('BQ_ANALYTICS_GCS_BUCKET')
BQ_ANALYTICS_GCS_PATH = os.getenv('BQ_ANALYTICS_GCS_PATH', '')

# Construct full GCS bucket path if path prefix is specified
gcs_bucket_name = None
if BQ_ANALYTICS_GCS_BUCKET:
    if BQ_ANALYTICS_GCS_PATH:
        # Note: The plugin expects just the bucket name, path is handled internally
        # For now, we just use the bucket name
        gcs_bucket_name = BQ_ANALYTICS_GCS_BUCKET
    else:
        gcs_bucket_name = BQ_ANALYTICS_GCS_BUCKET

# Plugin configuration
bq_config = BigQueryLoggerConfig(
    enabled=True,
    gcs_bucket_name=gcs_bucket_name,
    log_multi_modal_content=True,
    max_content_length=500 * 1024,  # 500 KB limit for inline text
    batch_size=1,  # Low latency (increase for high throughput)
    shutdown_timeout=10.0,
)

# Create the plugin instance
bq_analytics_plugin = BigQueryAgentAnalyticsPlugin(
    project_id=PROJECT_ID,
    dataset_id=BQ_ANALYTICS_DATASET,
    table_id=BQ_ANALYTICS_TABLE,
    config=bq_config,
    location=LOCATION,
)
