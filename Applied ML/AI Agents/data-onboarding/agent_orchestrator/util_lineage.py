"""Dataplex Data Lineage API utilities for publishing end-to-end lineage.

Creates Process → Run → LineageEvent entries that trace data from its
original URL through GCS staging and into BigQuery tables.  Events use
three FQN prefixes:
  - ``custom:`` for external URLs (web pages, download links)
  - ``gcs:`` for Cloud Storage objects
  - ``bigquery:`` for BigQuery tables

We publish four custom events per file:
  1. starting URL  →  file download URL
  2. file URL      →  GCS staging object
  3. GCS object    →  external BQ table
  4. external BQ table → bronze (materialized) BQ table

This gives one continuous chain: URL → file URL → GCS → ext_table → table.
"""

import logging

from .config import BQ_DATASET_LOCATION, GOOGLE_CLOUD_PROJECT

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# FQN builders
# ---------------------------------------------------------------------------

def build_fqn_bigquery(project: str, dataset: str, table: str) -> str:
    """Fully qualified name for a BigQuery table."""
    return f"bigquery:{project}.{dataset}.{table}"


def build_fqn_bigquery_full(table_id: str) -> str:
    """Fully qualified name from an already-qualified ``project.dataset.table`` id."""
    return f"bigquery:{table_id}"


def build_fqn_gcs(gcs_uri: str) -> str:
    """Fully qualified name for a GCS object.

    Accepts either ``gs://bucket/path`` or bare ``bucket/path`` forms.
    """
    if gcs_uri.startswith("gs://"):
        return f"gcs:{gcs_uri}"
    return f"gcs:gs://{gcs_uri}"


def build_fqn_url(url: str) -> str:
    """Fully qualified name for an external URL."""
    return f"custom:{url}"


# ---------------------------------------------------------------------------
# Lineage API helpers
# ---------------------------------------------------------------------------

def _lineage_location() -> str:
    """Map ``BQ_DATASET_LOCATION`` to the Data Lineage API location string.

    Multi-region values (``US``, ``EU``) are lowercased.  Regional values
    (e.g. ``us-central1``) are passed through as-is.
    """
    return BQ_DATASET_LOCATION.lower()


def _create_event(client, run_name: str, source_fqns: list[str], target_fqn: str) -> str:
    """Create a single LineageEvent linking *source_fqns* → *target_fqn*.

    Returns the created event resource name.
    """
    from google.cloud.datacatalog_lineage_v1 import (
        CreateLineageEventRequest,
        EntityReference,
        EventLink,
        LineageEvent,
    )
    from google.protobuf.timestamp_pb2 import Timestamp

    now = Timestamp()
    now.GetCurrentTime()

    links = [
        EventLink(
            source=EntityReference(fully_qualified_name=src),
            target=EntityReference(fully_qualified_name=target_fqn),
        )
        for src in source_fqns
    ]

    event = LineageEvent(links=links, start_time=now, end_time=now)
    request = CreateLineageEventRequest(parent=run_name, lineage_event=event)
    created = client.create_lineage_event(request=request)
    return created.name


def publish_lineage(
    source_id: str,
    starting_url: str,
    file_lineage: list[dict],
) -> dict:
    """Publish end-to-end lineage to the Dataplex Data Lineage API.

    Creates one **Process** (``data-onboarding``), one **Run** per
    invocation, and up to four **LineageEvents** per file:

    1. ``custom:<starting_url>`` → ``custom:<file_url>``
    2. ``custom:<file_url>``     → ``gcs:<gcs_uri>``
    3. ``gcs:<gcs_uri>``         → ``bigquery:<ext_table>``
    4. ``bigquery:<ext_table>``  → ``bigquery:<bronze_table>``

    Args:
        source_id: Unique identifier for this onboarding run.
        starting_url: The original URL provided by the user.
        file_lineage: List of dicts, each with keys:
            - file_url: Direct download URL of the file.
            - gcs_uri: GCS URI (``gs://bucket/path``).
            - external_table: Fully-qualified external table id
              (``project.dataset.table``).
            - bronze_table: Fully-qualified bronze table id
              (``project.dataset.table``).

    Returns:
        Dict with ``process``, ``run``, and ``events_created`` count,
        or ``error`` on failure.
    """
    if not GOOGLE_CLOUD_PROJECT:
        logger.warning("publish_lineage: GOOGLE_CLOUD_PROJECT not set, skipping.")
        return {"events_created": 0, "error": "GOOGLE_CLOUD_PROJECT not set"}

    try:
        from google.cloud.datacatalog_lineage_v1 import (
            CreateProcessRequest,
            CreateRunRequest,
            LineageClient,
            Process,
            Run,
        )
        from google.protobuf.struct_pb2 import Value
        from google.protobuf.timestamp_pb2 import Timestamp

        client = LineageClient()
        location = _lineage_location()
        parent = f"projects/{GOOGLE_CLOUD_PROJECT}/locations/{location}"

        # --- Process (reusable template) ---
        process = Process(
            display_name="Data Onboarding Pipeline",
            attributes={
                "system": Value(string_value="data-onboarding-agent"),
            },
        )
        created_process = client.create_process(
            request=CreateProcessRequest(parent=parent, process=process)
        )
        logger.info(f"Lineage process: {created_process.name}")

        # --- Run (single execution) ---
        now = Timestamp()
        now.GetCurrentTime()

        run = Run(
            display_name=f"Onboarding: {source_id}",
            start_time=now,
            end_time=now,
            state=Run.State.COMPLETED,
            attributes={
                "source_id": Value(string_value=source_id),
                "starting_url": Value(string_value=starting_url),
            },
        )
        created_run = client.create_run(
            request=CreateRunRequest(parent=created_process.name, run=run)
        )
        logger.info(f"Lineage run: {created_run.name}")

        # --- LineageEvents ---
        events_created = 0

        for entry in file_lineage:
            file_url = entry.get("file_url", "")
            gcs_uri = entry.get("gcs_uri", "")

            # Event 1: starting URL → file download URL
            if file_url and starting_url and starting_url != file_url:
                _create_event(
                    client,
                    created_run.name,
                    [build_fqn_url(starting_url)],
                    build_fqn_url(file_url),
                )
                events_created += 1

            # Event 2: file download URL → GCS staging object
            if file_url and gcs_uri:
                _create_event(
                    client,
                    created_run.name,
                    [build_fqn_url(file_url)],
                    build_fqn_gcs(gcs_uri),
                )
                events_created += 1

            # Event 3: GCS staging object → external BQ table
            ext_table = entry.get("external_table", "")
            if gcs_uri and ext_table:
                _create_event(
                    client,
                    created_run.name,
                    [build_fqn_gcs(gcs_uri)],
                    build_fqn_bigquery_full(ext_table),
                )
                events_created += 1

            # Event 4: external BQ table → bronze (materialized) BQ table
            bronze_table = entry.get("bronze_table", "")
            if ext_table and bronze_table:
                _create_event(
                    client,
                    created_run.name,
                    [build_fqn_bigquery_full(ext_table)],
                    build_fqn_bigquery_full(bronze_table),
                )
                events_created += 1

        logger.info(f"Lineage events created: {events_created}")

        return {
            "process": created_process.name,
            "run": created_run.name,
            "events_created": events_created,
        }

    except Exception as e:
        logger.warning(f"publish_lineage failed: {e}")
        return {"events_created": 0, "error": str(e)}
