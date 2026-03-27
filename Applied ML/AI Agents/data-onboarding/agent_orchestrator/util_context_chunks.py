"""Context chunks management for semantic search over table documentation.

Manages the ``context_chunks`` table in the ``{BQ_CONTEXT_DATASET}`` dataset.
Each chunk is a searchable piece of table documentation with autonomous
embeddings via ``AI.EMBED``.

Pattern follows ``util_metadata.py``.
"""

import datetime
import logging
import time
import uuid

from .config import (
    BQ_CONNECTION_ID,
    BQ_CONTEXT_DATASET,
    BQ_DATASET_LOCATION,
    GOOGLE_CLOUD_PROJECT,
)

logger = logging.getLogger(__name__)

FULL_DATASET_ID = (
    f"{GOOGLE_CLOUD_PROJECT}.{BQ_CONTEXT_DATASET}" if GOOGLE_CLOUD_PROJECT else None
)

CONTEXT_CHUNKS_DDL = ""
if FULL_DATASET_ID:
    _conn_ref = f"{GOOGLE_CLOUD_PROJECT}.{BQ_DATASET_LOCATION}.{BQ_CONNECTION_ID}"
    CONTEXT_CHUNKS_DDL = f"""
CREATE TABLE IF NOT EXISTS `{FULL_DATASET_ID}.context_chunks`
(
  chunk_id STRING NOT NULL OPTIONS(description="Unique chunk identifier."),
  source_dataset STRING NOT NULL OPTIONS(description="Bronze dataset this chunk describes."),
  source_table STRING NOT NULL OPTIONS(description="Table this chunk describes."),
  chunk_type STRING NOT NULL OPTIONS(description="Type: column_description, table_documentation, table_summary, relationship, profile_stat."),
  chunk_text STRING NOT NULL OPTIONS(description="Searchable text content."),
  ml_embed_content STRUCT<result ARRAY<FLOAT64>, status STRING>
    GENERATED ALWAYS AS (
      AI.EMBED(chunk_text,
               connection_id => '{_conn_ref}',
               endpoint => 'text-embedding-005',
               task_type => 'RETRIEVAL_DOCUMENT')
    ) STORED OPTIONS (asynchronous = TRUE),
  created_at TIMESTAMP NOT NULL OPTIONS(description="When the chunk was created.")
)
CLUSTER BY source_dataset, chunk_type;
"""


def _ensure_connection() -> str | None:
    """Create the BQ Cloud Resource connection if it doesn't exist.

    Returns the connection's service account email, or None on failure.
    """
    try:
        from google.cloud import bigquery_connection_v1

        client = bigquery_connection_v1.ConnectionServiceClient()
        parent = f"projects/{GOOGLE_CLOUD_PROJECT}/locations/{BQ_DATASET_LOCATION}"
        conn_name = f"{parent}/connections/{BQ_CONNECTION_ID}"

        # Check if connection already exists
        try:
            conn = client.get_connection(name=conn_name)
            logger.info("Context: Connection '%s' exists.", BQ_CONNECTION_ID)
            return conn.cloud_resource.service_account_id
        except Exception:
            pass

        # Create connection
        connection = bigquery_connection_v1.Connection(
            cloud_resource=bigquery_connection_v1.CloudResourceProperties()
        )
        conn = client.create_connection(
            parent=parent,
            connection_id=BQ_CONNECTION_ID,
            connection=connection,
        )
        logger.info("Context: Connection '%s' created.", BQ_CONNECTION_ID)

        sa_email = conn.cloud_resource.service_account_id
        if sa_email:
            _grant_aiplatform_user(sa_email)
        return sa_email

    except Exception as e:
        logger.warning("Context: Connection setup failed: %s", e)
        return None


def _grant_aiplatform_user(sa_email: str) -> None:
    """Grant roles/aiplatform.user to the connection service account.

    Retries up to 3 times with a 90-second delay because newly created
    BQ connection service accounts can take 60-90 seconds to propagate.
    """
    from google.cloud import resourcemanager_v3
    from google.iam.v1 import policy_pb2

    client = resourcemanager_v3.ProjectsClient()
    resource = f"projects/{GOOGLE_CLOUD_PROJECT}"
    member = f"serviceAccount:{sa_email}"
    role = "roles/aiplatform.user"

    for attempt in range(3):
        try:
            policy = client.get_iam_policy(request={"resource": resource})

            # Check if binding already exists
            for binding in policy.bindings:
                if binding.role == role and member in binding.members:
                    logger.info("Context: IAM binding already exists for %s.", sa_email)
                    return

            # Add binding
            new_binding = policy_pb2.Binding(role=role, members=[member])
            policy.bindings.append(new_binding)
            client.set_iam_policy(request={"resource": resource, "policy": policy})
            logger.info("Context: Granted %s to %s.", role, sa_email)
            return
        except Exception as e:
            if "does not exist" in str(e) and attempt < 2:
                logger.info(
                    "Context: SA not yet propagated (attempt %d/3), "
                    "waiting 90s...", attempt + 1,
                )
                time.sleep(90)
            else:
                logger.warning(
                    "Context: IAM grant failed (%s). You may need to grant manually:\n"
                    "  gcloud projects add-iam-policy-binding %s "
                    "--member=serviceAccount:%s --role=roles/aiplatform.user",
                    e, GOOGLE_CLOUD_PROJECT, sa_email,
                )
                return


def ensure_context_dataset() -> None:
    """Create BQ connection, context dataset, and context_chunks table if not exists.

    Automatically creates the Cloud Resource connection needed for AI.EMBED
    autonomous embeddings and grants the service account ``roles/aiplatform.user``.
    """
    if not GOOGLE_CLOUD_PROJECT:
        logger.warning("ensure_context_dataset: GOOGLE_CLOUD_PROJECT not set, skipping.")
        return

    # Ensure connection exists (needed for AI.EMBED)
    _ensure_connection()

    from google.cloud import bigquery

    client = bigquery.Client(project=GOOGLE_CLOUD_PROJECT)

    # Create dataset
    try:
        client.get_dataset(FULL_DATASET_ID)
        logger.info("Context: Dataset '%s' exists.", FULL_DATASET_ID)
    except Exception as e:
        if "Not found" in str(e):
            logger.info("Context: Creating dataset '%s'...", FULL_DATASET_ID)
            dataset = bigquery.Dataset(FULL_DATASET_ID)
            dataset.location = BQ_DATASET_LOCATION
            dataset.description = (
                "Data Onboarding context chunks — semantic search over table documentation"
            )
            client.create_dataset(dataset, exists_ok=True)
            logger.info("Context: Dataset '%s' created.", FULL_DATASET_ID)
        else:
            raise

    # Create context_chunks table (connection_id is embedded in the AI.EMBED DDL)
    full_table = f"{FULL_DATASET_ID}.context_chunks"
    try:
        client.get_table(full_table)
        logger.info("Context: Table '%s' exists.", full_table)
    except Exception as e:
        if "Not found" in str(e):
            logger.info("Context: Creating table '%s'...", full_table)
            client.query(CONTEXT_CHUNKS_DDL).result()
            logger.info("Context: Table '%s' created.", full_table)
        else:
            raise


def chunk_table_documentation(
    dataset_name: str,
    table_name: str,
    documentation_md: str,
    column_details: list[dict],
    related_tables: dict | None = None,
    profile_stats: str | None = None,
) -> list[dict]:
    """Break table docs into searchable chunks.

    Args:
        dataset_name: Bronze dataset name.
        table_name: Table this documentation describes.
        documentation_md: Full markdown documentation string.
        column_details: List of column dicts with name, bq_type, description.
        related_tables: Optional relationship dict.
        profile_stats: Optional profile statistics text.

    Returns:
        List of chunk dicts ready for insertion.
    """
    now = datetime.datetime.now(datetime.UTC).isoformat()
    chunks = []

    # 1. Table documentation chunk
    doc_text = f"Table: {dataset_name}.{table_name}\n\n{documentation_md}"
    if len(doc_text) > 8000:
        doc_text = doc_text[:8000]
    chunks.append({
        "chunk_id": str(uuid.uuid4()),
        "source_dataset": dataset_name,
        "source_table": table_name,
        "chunk_type": "table_documentation",
        "chunk_text": doc_text,
        "created_at": now,
    })

    # 2. Table summary chunk — all columns in one searchable chunk
    if column_details:
        summary_lines = [
            f"Table summary: {dataset_name}.{table_name}",
            f"This table has {len(column_details)} columns:",
        ]
        for col in column_details:
            name = col.get("name", "")
            bq_type = col.get("bq_type", "STRING")
            desc = col.get("description", "")
            if desc:
                summary_lines.append(f"  - {name} ({bq_type}): {desc}")
            else:
                summary_lines.append(f"  - {name} ({bq_type})")
        summary_text = "\n".join(summary_lines)
        if len(summary_text) > 8000:
            summary_text = summary_text[:8000]
        chunks.append({
            "chunk_id": str(uuid.uuid4()),
            "source_dataset": dataset_name,
            "source_table": table_name,
            "chunk_type": "table_summary",
            "chunk_text": summary_text,
            "created_at": now,
        })

    # 3. Column description chunks — one per column
    for col in column_details:
        name = col.get("name", "")
        bq_type = col.get("bq_type", "STRING")
        desc = col.get("description", "")
        col_text = (
            f"Column: {dataset_name}.{table_name}.{name} ({bq_type})\n"
            f"Description: {desc}"
        )
        chunks.append({
            "chunk_id": str(uuid.uuid4()),
            "source_dataset": dataset_name,
            "source_table": table_name,
            "chunk_type": "column_description",
            "chunk_text": col_text,
            "created_at": now,
        })

    # 3. Relationship chunk
    if related_tables:
        rel_lines = [f"Relationships for {dataset_name}.{table_name}:"]
        for rel_type, rel_val in related_tables.items():
            if isinstance(rel_val, list):
                rel_lines.append(f"  {rel_type}: {', '.join(rel_val)}")
            else:
                rel_lines.append(f"  {rel_type}: {rel_val}")
        chunks.append({
            "chunk_id": str(uuid.uuid4()),
            "source_dataset": dataset_name,
            "source_table": table_name,
            "chunk_type": "relationship",
            "chunk_text": "\n".join(rel_lines),
            "created_at": now,
        })

    # 4. Profile stat chunk
    if profile_stats:
        chunks.append({
            "chunk_id": str(uuid.uuid4()),
            "source_dataset": dataset_name,
            "source_table": table_name,
            "chunk_type": "profile_stat",
            "chunk_text": f"Profile statistics for {dataset_name}.{table_name}:\n{profile_stats}",
            "created_at": now,
        })

    return chunks


def insert_context_chunks(chunks: list[dict]) -> int:
    """Insert chunks into the context_chunks table.

    Args:
        chunks: List of chunk dicts from ``chunk_table_documentation``.

    Returns:
        Number of chunks inserted, or 0 on failure.
    """
    if not GOOGLE_CLOUD_PROJECT:
        logger.warning("insert_context_chunks: GOOGLE_CLOUD_PROJECT not set, skipping.")
        return 0

    if not chunks:
        return 0

    try:
        from google.cloud import bigquery

        client = bigquery.Client(project=GOOGLE_CLOUD_PROJECT)
        table_id = f"{FULL_DATASET_ID}.context_chunks"

        errors = client.insert_rows_json(table_id, chunks)
        if errors:
            logger.warning("insert_context_chunks errors: %s", errors)
            return 0
        return len(chunks)

    except Exception as e:
        logger.warning("insert_context_chunks failed: %s", e)
        return 0
