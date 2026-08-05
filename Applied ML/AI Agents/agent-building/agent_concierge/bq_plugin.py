"""BigQuery Agent Analytics plugin — the Observability pillar, in code.

The ADK BigQueryAgentAnalyticsPlugin logs every agent event (LLM calls, tool
invocations, transfers) to a BigQuery table you can then query and dashboard.
This is the agent's *own operational telemetry*, distinct from the retail data —
so unlike domain provisioning (which lives in scripts/), the plugin get-or-creates
its own tiny events table on import. It is fully None-guarded: with no
GOOGLE_CLOUD_PROJECT set, the plugin is None and the agent runs without logging.

Reference: https://google.github.io/adk-docs/observability/bigquery-agent-analytics/
"""

import logging

from config import (
    BQ_ANALYTICS_DATASET,
    BQ_ANALYTICS_TABLE,
    BQ_LOCATION,
    GOOGLE_CLOUD_PROJECT,
)

logger = logging.getLogger(__name__)

_FULL_TABLE_ID = (
    f"{GOOGLE_CLOUD_PROJECT}.{BQ_ANALYTICS_DATASET}.{BQ_ANALYTICS_TABLE}"
    if GOOGLE_CLOUD_PROJECT
    else None
)

_CREATE_TABLE_DDL = (
    f"""
CREATE TABLE IF NOT EXISTS `{_FULL_TABLE_ID}`
(
  timestamp TIMESTAMP NOT NULL OPTIONS(description="UTC time the event was logged."),
  event_type STRING OPTIONS(description="Event type (e.g. 'LLM_REQUEST', 'TOOL_COMPLETED')."),
  agent STRING OPTIONS(description="Name of the ADK agent/author for the event."),
  session_id STRING OPTIONS(description="Groups events within one conversation/session."),
  invocation_id STRING OPTIONS(description="Identifies one agent turn within a session."),
  user_id STRING OPTIONS(description="User associated with the session."),
  trace_id STRING OPTIONS(description="OpenTelemetry trace ID."),
  span_id STRING OPTIONS(description="OpenTelemetry span ID."),
  parent_span_id STRING OPTIONS(description="OpenTelemetry parent span ID."),
  content JSON OPTIONS(description="Event payload as JSON."),
  attributes JSON OPTIONS(description="Arbitrary key-value metadata."),
  latency_ms JSON OPTIONS(description="Latency measurements."),
  status STRING OPTIONS(description="Outcome, typically 'OK' or 'ERROR'."),
  error_message STRING OPTIONS(description="Populated on error."),
  is_truncated BOOLEAN OPTIONS(description="Whether content was truncated.")
)
PARTITION BY DATE(timestamp)
CLUSTER BY event_type, agent, user_id;
"""
    if _FULL_TABLE_ID
    else ""
)


def _ensure_setup() -> None:
    """Get-or-create the analytics dataset and table (best effort)."""
    if not GOOGLE_CLOUD_PROJECT:
        logger.warning("BQ Analytics: GOOGLE_CLOUD_PROJECT not set — skipping auto-setup.")
        return
    try:
        from google.cloud import bigquery

        client = bigquery.Client(project=GOOGLE_CLOUD_PROJECT)
        dataset_ref = f"{GOOGLE_CLOUD_PROJECT}.{BQ_ANALYTICS_DATASET}"
        try:
            client.get_dataset(dataset_ref)
        except Exception:
            dataset = bigquery.Dataset(dataset_ref)
            dataset.location = BQ_LOCATION
            dataset.description = "agent-building — ADK agent event logs (observability)"
            client.create_dataset(dataset, exists_ok=True)
        try:
            client.get_table(_FULL_TABLE_ID)
        except Exception:
            client.query(_CREATE_TABLE_DDL).result()
    except Exception as e:  # noqa: BLE001 — never block agent startup on telemetry
        logger.warning(f"BQ Analytics: auto-setup failed ({e}); plugin may still work.")


_ensure_setup()

# None when unconfigured, so App(plugins=[p for p in [plugin] if p]) stays empty.
bq_analytics_plugin = None
if GOOGLE_CLOUD_PROJECT:
    from google.adk.plugins.bigquery_agent_analytics_plugin import (
        BigQueryAgentAnalyticsPlugin,
        BigQueryLoggerConfig,
    )

    bq_analytics_plugin = BigQueryAgentAnalyticsPlugin(
        project_id=GOOGLE_CLOUD_PROJECT,
        dataset_id=BQ_ANALYTICS_DATASET,
        table_id=BQ_ANALYTICS_TABLE,
        config=BigQueryLoggerConfig(
            enabled=True,
            log_multi_modal_content=False,
            batch_size=20,
            shutdown_timeout=30.0,
        ),
        location=BQ_LOCATION,
    )
else:
    logger.info("BQ Analytics: GOOGLE_CLOUD_PROJECT not set — plugin disabled.")
