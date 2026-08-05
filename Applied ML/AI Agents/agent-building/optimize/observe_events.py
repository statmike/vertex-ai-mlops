"""Observability — summarize the agent event log written by the BQ plugin.

The concierge runs with the ADK BigQueryAgentAnalyticsPlugin (see
agent_concierge/bq_plugin.py), which logs every event to a partitioned BigQuery
table. This script reads that table and prints two rollups: events (and error
rate) by type, and activity by agent. It's the query-side companion to the plugin
and the offline complement to Cloud Trace.

    uv run python optimize/observe_events.py [--days N]

Needs GOOGLE_CLOUD_PROJECT set and at least one prior agent run to have logged
events. The SQL itself lives in optimize/harness/observability.py so it's tested.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from optimize.harness.observability import (  # noqa: E402
    agent_activity_sql,
    event_summary_sql,
)


def _full_table_id() -> str:
    from config import (
        BQ_ANALYTICS_DATASET,
        BQ_ANALYTICS_TABLE,
        GOOGLE_CLOUD_PROJECT,
    )

    if not GOOGLE_CLOUD_PROJECT:
        print("Error: GOOGLE_CLOUD_PROJECT not set.")
        raise SystemExit(1)
    return f"{GOOGLE_CLOUD_PROJECT}.{BQ_ANALYTICS_DATASET}.{BQ_ANALYTICS_TABLE}"


def _print_rows(title: str, rows) -> None:
    print(f"\n=== {title} ===")
    rows = list(rows)
    if not rows:
        print("  (no rows)")
        return
    headers = list(rows[0].keys())
    print("  " + "  ".join(headers))
    for row in rows:
        print("  " + "  ".join(str(row[h]) for h in headers))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--days", type=int, default=7, help="Look-back window (default 7).")
    args = parser.parse_args()

    from google.cloud import bigquery

    from config import BQ_LOCATION, GOOGLE_CLOUD_PROJECT

    table_id = _full_table_id()
    client = bigquery.Client(project=GOOGLE_CLOUD_PROJECT)

    print(f"Summarizing {table_id} over the last {args.days} day(s)...")
    try:
        events = client.query(event_summary_sql(table_id, args.days), location=BQ_LOCATION).result()
        activity = client.query(
            agent_activity_sql(table_id, args.days), location=BQ_LOCATION
        ).result()
    except Exception as e:  # noqa: BLE001
        print(f"\nQuery failed ({e}).")
        print("Has the agent run yet? The plugin creates the table on first use.")
        raise SystemExit(1) from e

    _print_rows("Events by type", events)
    _print_rows("Activity by agent", activity)
    print("\nFor traces/spans, open Cloud Trace in the Console (enable_tracing=True on deploy).")


if __name__ == "__main__":
    main()
