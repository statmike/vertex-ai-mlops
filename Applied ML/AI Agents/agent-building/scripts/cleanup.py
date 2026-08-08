"""Tear down everything scripts/setup.py provisioned.

    uv run python scripts/cleanup.py

Idempotent: missing resources are skipped. Names are reconstructed from the same
config + helpers setup.py used, so this removes exactly what was created:

  - Agent Runtime service-agent IAM bindings (catalog search, Model Armor,
    Example Store read)
  - Model Armor guardrail template {MODEL_ARMOR_TEMPLATE}
  - Example Store (matched by display name {EXAMPLE_STORE_DISPLAY_NAME})
  - RAG Engine corpus (matched by display name {RAG_CORPUS_DISPLAY_NAME})
  - Dataplex profile scans (one per view)
  - BigQuery dataset {BQ_DATASET} (views + object table, deleted with contents)
  - BigQuery AI connection {BQ_DATASET}_ai
  - GCS docs bucket (and its contents)
  - BigQuery analytics dataset {BQ_ANALYTICS_DATASET} (observability logs)

It does NOT disable APIs or touch the public theLook data (we only read it).
"""

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import (  # noqa: E402
    BQ_ANALYTICS_DATASET,
    BQ_DATASET,
    BQ_LOCATION,
    DATAPLEX_LOCATION,
    EXAMPLE_STORE_DISPLAY_NAME,
    EXAMPLE_STORE_LOCATION,
    EXAMPLE_STORE_NAME,
    GOOGLE_CLOUD_PROJECT,
    MODEL_ARMOR_LOCATION,
    MODEL_ARMOR_TEMPLATE,
    RAG_CORPUS_DISPLAY_NAME,
    RAG_CORPUS_NAME,
    RAG_LOCATION,
    THELOOK_TABLES,
)
from scripts.resources import (  # noqa: E402
    agent_runtime_service_agent,
    ai_connection_id,
    docs_bucket_name,
    model_armor_template_path,
    profile_scan_id,
)

# Kept in sync with setup.RUNTIME_SA_ROLES — the roles to revoke on teardown.
RUNTIME_SA_ROLES = [
    "roles/dataplex.catalogViewer",
    "roles/modelarmor.user",
    "roles/aiplatform.viewer",
]


def _run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True)


def revoke_runtime_iam() -> None:
    """Remove the IAM bindings setup.py granted the Agent Runtime service agent."""
    number = _run(
        ["gcloud", "projects", "describe", GOOGLE_CLOUD_PROJECT, "--format=value(projectNumber)"]
    ).stdout.strip()
    if not number:
        print("Agent Runtime IAM: could not resolve project number; skipping.")
        return
    sa = agent_runtime_service_agent(number)
    print("Revoking Agent Runtime IAM:")
    for role in RUNTIME_SA_ROLES:
        result = _run(
            [
                "gcloud", "projects", "remove-iam-policy-binding", GOOGLE_CLOUD_PROJECT,
                f"--member=serviceAccount:{sa}", f"--role={role}", "--quiet",
            ]
        )
        if result.returncode == 0:
            print(f"    Revoked: {role}")
        else:
            print(f"    Not removed (may not exist): {role}")


def delete_model_armor_template() -> None:
    """Delete the Model Armor guardrail template setup.py created."""
    from google.api_core.client_options import ClientOptions
    from google.api_core.exceptions import NotFound
    from google.cloud import modelarmor_v1 as ma

    client = ma.ModelArmorClient(
        transport="rest",
        client_options=ClientOptions(
            api_endpoint=f"modelarmor.{MODEL_ARMOR_LOCATION}.rep.googleapis.com"
        ),
    )
    name = model_armor_template_path(
        GOOGLE_CLOUD_PROJECT, MODEL_ARMOR_LOCATION, MODEL_ARMOR_TEMPLATE
    )
    print("Deleting Model Armor template:")
    try:
        client.delete_template(request=ma.DeleteTemplateRequest(name=name))
        print(f"    Deleted: {MODEL_ARMOR_TEMPLATE}")
    except NotFound:
        print(f"    Not found: {MODEL_ARMOR_TEMPLATE}")
    except Exception as e:  # noqa: BLE001
        print(f"    FAILED (non-fatal): {MODEL_ARMOR_TEMPLATE} - {e}")


def delete_example_store() -> None:
    """Delete the Example Store setup.py created.

    Matched the same way setup resolves it: by the explicit EXAMPLE_STORE_NAME
    resource name if set, else by the deterministic display name (Vertex assigns a
    numeric resource id, so there's nothing else stable to match on).
    """
    import vertexai
    from vertexai.preview import example_stores

    print("Deleting Example Store:")
    vertexai.init(project=GOOGLE_CLOUD_PROJECT, location=EXAMPLE_STORE_LOCATION)

    targets = []
    try:
        if EXAMPLE_STORE_NAME:
            targets = [example_stores.ExampleStore(EXAMPLE_STORE_NAME)]
        else:
            targets = [
                s
                for s in example_stores.ExampleStore.list()
                if (getattr(s, "display_name", None)
                    or getattr(getattr(s, "_gca_resource", None), "display_name", None))
                == EXAMPLE_STORE_DISPLAY_NAME
            ]
    except Exception as e:  # noqa: BLE001
        print(f"    FAILED (non-fatal) listing stores: {e}")
        return

    if not targets:
        print(f"    Not found: {EXAMPLE_STORE_NAME or EXAMPLE_STORE_DISPLAY_NAME}")
        return
    for store in targets:
        try:
            store.delete()
            print(f"    Deleted: {store.resource_name}")
        except Exception as e:  # noqa: BLE001
            print(f"    FAILED (non-fatal): {store.resource_name} - {e}")


def delete_rag_corpus() -> None:
    """Delete the RAG Engine corpus setup.py created (and its imported files).

    Matched the same way setup resolves it: by the explicit RAG_CORPUS_NAME
    resource name if set, else by the deterministic display name.
    """
    import vertexai
    from vertexai.preview import rag

    print("Deleting RAG corpus:")
    vertexai.init(project=GOOGLE_CLOUD_PROJECT, location=RAG_LOCATION)

    names = []
    try:
        if RAG_CORPUS_NAME:
            names = [RAG_CORPUS_NAME]
        else:
            names = [
                c.name
                for c in rag.list_corpora()
                if getattr(c, "display_name", None) == RAG_CORPUS_DISPLAY_NAME
            ]
    except Exception as e:  # noqa: BLE001
        print(f"    FAILED (non-fatal) listing corpora: {e}")
        return

    if not names:
        print(f"    Not found: {RAG_CORPUS_NAME or RAG_CORPUS_DISPLAY_NAME}")
        return
    for name in names:
        try:
            rag.delete_corpus(name=name)
            print(f"    Deleted: {name}")
        except Exception as e:  # noqa: BLE001
            print(f"    FAILED (non-fatal): {name} - {e}")


def delete_profile_scans() -> None:
    from google.api_core.exceptions import NotFound
    from google.cloud.dataplex_v1 import DataScanServiceClient, DeleteDataScanRequest

    client = DataScanServiceClient()
    parent = f"projects/{GOOGLE_CLOUD_PROJECT}/locations/{DATAPLEX_LOCATION}"
    print("Deleting profile scans:")
    for table in THELOOK_TABLES:
        scan_id = profile_scan_id(table)
        name = f"{parent}/dataScans/{scan_id}"
        try:
            client.delete_data_scan(request=DeleteDataScanRequest(name=name)).result()
            print(f"    Deleted: {scan_id}")
        except NotFound:
            print(f"    Not found: {scan_id}")
        except Exception as e:  # noqa: BLE001
            print(f"    FAILED (non-fatal): {scan_id} - {e}")


def delete_datasets() -> None:
    """Delete the working dataset and the analytics dataset (with contents)."""
    from google.cloud import bigquery

    client = bigquery.Client(project=GOOGLE_CLOUD_PROJECT)
    print("Deleting BigQuery datasets:")
    for dataset in (BQ_DATASET, BQ_ANALYTICS_DATASET):
        ref = f"{GOOGLE_CLOUD_PROJECT}.{dataset}"
        client.delete_dataset(ref, delete_contents=True, not_found_ok=True)
        print(f"    Deleted: {ref}")


def delete_ai_connection() -> None:
    conn_id = ai_connection_id()
    result = _run(
        [
            "bq", "rm", "--connection", "--force",
            "--project_id", GOOGLE_CLOUD_PROJECT,
            "--location", BQ_LOCATION.lower(), conn_id,
        ]
    )
    if result.returncode == 0:
        print(f"Deleted AI connection: {conn_id}")
    else:
        print(f"AI connection not removed (may not exist): {conn_id}")


def delete_docs_bucket() -> None:
    from google.cloud import storage

    client = storage.Client(project=GOOGLE_CLOUD_PROJECT)
    bucket_name = docs_bucket_name()
    bucket = client.bucket(bucket_name)
    if bucket.exists():
        bucket.delete(force=True)
        print(f"Deleted bucket: gs://{bucket_name}")
    else:
        print(f"Bucket not found: gs://{bucket_name}")


def main() -> None:
    if not GOOGLE_CLOUD_PROJECT:
        sys.exit("GOOGLE_CLOUD_PROJECT is not set.")

    print(f"Removing agent-building resources from {GOOGLE_CLOUD_PROJECT}\n")
    revoke_runtime_iam()
    print()
    delete_model_armor_template()
    print()
    delete_example_store()
    print()
    delete_rag_corpus()
    print()
    delete_profile_scans()
    print()
    delete_ai_connection()
    print()
    delete_docs_bucket()
    print()
    delete_datasets()
    print("\nCleanup complete.")


if __name__ == "__main__":
    main()
