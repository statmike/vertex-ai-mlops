"""SQL for summarizing the agent event log — pure string building, testable.

The BigQuery Agent Analytics plugin (agent_concierge/bq_plugin.py) logs every
event to a partitioned table. These builders turn a fully-qualified table id into
the queries observe_events.py runs, so the SQL is unit-tested without a warehouse.
"""

from __future__ import annotations


def _validate_table_id(table_id: str) -> str:
    """Guard the table id (it's interpolated into SQL, so no injection surface).

    Accepts ``project.dataset.table`` with the characters BigQuery allows in those
    names. Raises ValueError otherwise — a bad id fails loudly, never runs.
    """
    parts = table_id.split(".")
    if len(parts) != 3 or not all(parts):
        raise ValueError(f"Expected 'project.dataset.table', got {table_id!r}")
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_")
    if not all(set(p) <= allowed for p in parts):
        raise ValueError(f"Illegal character in table id {table_id!r}")
    return table_id


def event_summary_sql(table_id: str, days: int = 7) -> str:
    """Per-event-type counts and error rate over the last ``days`` days."""
    _validate_table_id(table_id)
    days = int(days)
    return f"""
SELECT
  event_type,
  COUNT(*) AS events,
  COUNTIF(status = 'ERROR') AS errors,
  ROUND(SAFE_DIVIDE(COUNTIF(status = 'ERROR'), COUNT(*)) * 100, 1) AS error_pct
FROM `{table_id}`
WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days} DAY)
GROUP BY event_type
ORDER BY events DESC
""".strip()


def agent_activity_sql(table_id: str, days: int = 7) -> str:
    """Per-agent event and session counts — shows routing/usage distribution."""
    _validate_table_id(table_id)
    days = int(days)
    return f"""
SELECT
  agent,
  COUNT(*) AS events,
  COUNT(DISTINCT session_id) AS sessions,
  COUNT(DISTINCT user_id) AS users
FROM `{table_id}`
WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days} DAY)
  AND agent IS NOT NULL
GROUP BY agent
ORDER BY events DESC
""".strip()
