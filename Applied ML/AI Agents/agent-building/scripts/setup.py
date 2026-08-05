"""Provision everything the agents need — run once, before touching agent code.

    uv run python scripts/setup.py

Idempotent: safe to re-run; existing resources are left in place. This is the
"a real company already has data" boundary — ALL provisioning lives here, never
inside an agent package. Cleanup mirrors it in scripts/cleanup.py.

What it creates in your project (names come from config.py, all derived from
RESOURCE_PREFIX so cleanup can find them):

  1. APIs            — enables the services the agents call.
  2. BQ dataset      — {BQ_DATASET}, holds the views + object table below.
  3. Structured data — views over the public theLook tables, so they register as
                       entries in *your* Knowledge Catalog for the discovery agent.
  4. Profile scans   — Dataplex data-profile scans that enrich those entries.
  5. Unstructured    — a GCS bucket seeded with synthetic retail docs.
  6. AI connection   — a BigQuery Cloud Resource connection ({BQ_DATASET}_ai) the
                       AI.* functions use, with the needed IAM roles granted.
  7. Object table    — {BQ_OBJECT_TABLE} over the GCS docs, for the catalog agent.
  8. Runtime IAM     — grants the Agent Runtime service agent the catalog-search
                       role deployed agents need (the discovery agent), which
                       Runtime does not grant automatically.

Knowledge Catalog is the product formerly called Dataplex Universal Catalog
(renamed April 2026); the API/SDK namespace remains ``dataplex``.
"""

import subprocess
import sys
import time
from pathlib import Path

# Import the single source of truth for every resource name.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import (  # noqa: E402
    BQ_DATASET,
    BQ_LOCATION,
    BQ_OBJECT_TABLE,
    DATAPLEX_LOCATION,
    DOCS_PREFIX,
    GOOGLE_CLOUD_PROJECT,
    THELOOK_DATASET,
    THELOOK_PROJECT,
    THELOOK_TABLES,
)
from scripts.resources import (  # noqa: E402
    agent_runtime_service_agent,
    ai_connection_id,
    docs_bucket_name,
    profile_scan_id,
)

# APIs the agents and this script depend on.
REQUIRED_APIS = [
    "aiplatform.googleapis.com",
    "bigquery.googleapis.com",
    "bigqueryconnection.googleapis.com",
    "storage.googleapis.com",
    "dataplex.googleapis.com",
    "geminidataanalytics.googleapis.com",
    "cloudresourcemanager.googleapis.com",
]

# IAM roles the AI connection's service account needs to read GCS + call models.
CONNECTION_SA_ROLES = [
    "roles/aiplatform.user",
    "roles/storage.objectViewer",
]

# IAM roles the Agent Runtime service agent needs once agents are DEPLOYED. Agent
# Runtime grants most data roles automatically (BigQuery read/jobs, GCS, Gemini
# Data Analytics), but not catalog *search*: the discovery agent calls
# dataplex.projects.search, which lives in catalogViewer, not the auto-granted
# dataplex.viewer. Locally the agent borrows the developer's own permissions, so
# this gap only surfaces after deploy — we close it here so setup is complete.
RUNTIME_SA_ROLES = [
    "roles/dataplex.catalogViewer",
]

# Synthetic unstructured corpus: filename -> plain-text content. Deliberately
# tiny so the demo is fast and the AI.GENERATE pass over it is cheap.
RETAIL_DOCS: dict[str, str] = {
    "return_policy.txt": (
        "theLook Return Policy\n\n"
        "Items may be returned within 30 days of delivery for a full refund. "
        "Items must be unworn, unwashed, and have original tags attached. "
        "Final-sale and clearance items cannot be returned. "
        "Refunds are issued to the original payment method within 5-7 business "
        "days after we receive the return. Return shipping is free for members; "
        "non-members are charged a flat $5 return-shipping fee."
    ),
    "shipping_faq.txt": (
        "theLook Shipping FAQ\n\n"
        "Standard shipping (3-5 business days) is free on orders over $50. "
        "Express shipping (1-2 business days) is $12. We ship to all 50 US "
        "states. International shipping is not currently available. Orders placed "
        "before 12pm ET ship the same business day. You will receive a tracking "
        "link by email once your order ships."
    ),
    "sizing_guide.txt": (
        "theLook Sizing Guide\n\n"
        "Our apparel follows standard US sizing. If you are between sizes, we "
        "recommend sizing up for a relaxed fit. Denim is measured by waist in "
        "inches. Footwear uses US shoe sizes; our shoes run true to size. Detailed "
        "measurement charts for chest, waist, and inseam are on each product page."
    ),
    "care_guide.txt": (
        "theLook Product Care Guide\n\n"
        "Machine wash cold with like colors and tumble dry low unless the garment "
        "label says otherwise. Wash denim inside out to preserve color. Do not "
        "bleach. Leather goods should be kept dry and conditioned twice a year. "
        "Knitwear should be laid flat to dry to keep its shape."
    ),
    "warranty.txt": (
        "theLook Warranty\n\n"
        "All footwear and bags carry a one-year limited warranty against "
        "manufacturing defects. The warranty does not cover normal wear and tear "
        "or damage from misuse. To file a claim, contact support with your order "
        "number and photos of the defect. Approved claims are replaced free of "
        "charge or refunded if the item is out of stock."
    ),
    "membership.txt": (
        "theLook Membership Perks\n\n"
        "theLook+ membership is $39/year and includes free standard and return "
        "shipping on every order, early access to sales, and a birthday reward. "
        "Members earn 2 points per dollar; 100 points convert to a $5 store "
        "credit. Membership can be cancelled anytime for a prorated refund."
    ),
}


def _run(cmd: list[str]) -> subprocess.CompletedProcess:
    """Run a shell command, capturing output (never raises on non-zero)."""
    return subprocess.run(cmd, capture_output=True, text=True)


def enable_apis() -> None:
    """Enable every required API (idempotent; already-enabled is a no-op)."""
    print("Enabling APIs:")
    result = _run(
        ["gcloud", "services", "enable", *REQUIRED_APIS, "--project", GOOGLE_CLOUD_PROJECT]
    )
    if result.returncode == 0:
        print(f"    Enabled: {', '.join(a.split('.')[0] for a in REQUIRED_APIS)}")
    else:
        print(f"    WARNING: could not enable APIs ({result.stderr.strip()}).")


def create_dataset_and_views() -> None:
    """Create the working dataset and views over the public theLook tables.

    The views register catalog entries in *your* project (so the discovery agent
    can find them) and carry the source tables' column descriptions.
    """
    from google.cloud import bigquery

    client = bigquery.Client(project=GOOGLE_CLOUD_PROJECT)

    dataset_ref = f"{GOOGLE_CLOUD_PROJECT}.{BQ_DATASET}"
    dataset = bigquery.Dataset(dataset_ref)
    dataset.location = BQ_LOCATION
    dataset.description = "agent-building — theLook views + unstructured object table."
    client.create_dataset(dataset, exists_ok=True)
    print(f"Dataset: {dataset_ref}")

    print("Views over public theLook tables:")
    for table in THELOOK_TABLES:
        view_ref = f"{dataset_ref}.{table}"
        source = f"{THELOOK_PROJECT}.{THELOOK_DATASET}.{table}"
        expected_query = f"SELECT * FROM `{source}`"

        try:
            existing = client.get_table(view_ref)
        except Exception:
            existing = None

        try:
            if existing is not None and existing.view_query == expected_query:
                print(f"    View exists: {table}")
            else:
                if existing is not None:
                    client.delete_table(view_ref, not_found_ok=True)
                view = bigquery.Table(view_ref)
                view.view_query = expected_query
                client.create_table(view)
                print(f"    View: {table} -> {source}")
            # Copy schema (column descriptions) from source for richer catalog entries.
            try:
                src = client.get_table(source)
                created = client.get_table(view_ref)
                created.schema = src.schema
                client.update_table(created, ["schema"])
            except Exception:
                pass  # column descriptions are nice-to-have
        except Exception as e:  # noqa: BLE001
            print(f"    View {table}: FAILED - {e}")


def run_profile_scans() -> None:
    """Create + run a Dataplex data-profile scan per view (enriches the catalog)."""
    from google.api_core.exceptions import AlreadyExists, ResourceExhausted
    from google.cloud.dataplex_v1 import (
        CreateDataScanRequest,
        DataProfileSpec,
        DataScan,
        DataScanServiceClient,
        DataSource,
        RunDataScanRequest,
        Trigger,
    )

    client = DataScanServiceClient()
    parent = f"projects/{GOOGLE_CLOUD_PROJECT}/locations/{DATAPLEX_LOCATION}"

    print("Profile scans (Dataplex):")
    for i, table in enumerate(THELOOK_TABLES):
        scan_id = profile_scan_id(table)
        resource = (
            f"//bigquery.googleapis.com/projects/{GOOGLE_CLOUD_PROJECT}"
            f"/datasets/{BQ_DATASET}/tables/{table}"
        )
        if i > 0:
            time.sleep(3)  # stay under the Dataplex request-rate quota

        scan = DataScan(
            data=DataSource(resource=resource),
            data_profile_spec=DataProfileSpec(
                sampling_percent=10.0,
                catalog_publishing_enabled=True,
            ),
            execution_spec=DataScan.ExecutionSpec(
                trigger=Trigger(on_demand=Trigger.OnDemand()),
            ),
            description=f"Profile scan for {BQ_DATASET}.{table}",
        )
        # The Dataplex API caps requests at 30/min/region; creating a scan polls
        # a long-running op (several calls), so a run of six can trip the limit.
        # Retry on rate-limit with backoff so a single setup run creates them all.
        created = False
        for attempt in range(4):
            try:
                client.create_data_scan(
                    request=CreateDataScanRequest(
                        parent=parent, data_scan=scan, data_scan_id=scan_id
                    )
                ).result()
                print(f"    Scan created: {scan_id}")
                created = True
                break
            except AlreadyExists:
                print(f"    Scan exists:  {scan_id}")
                created = True
                break
            except ResourceExhausted:
                wait = 20 * (attempt + 1)  # 20s, 40s, 60s — quota is per-minute
                print(f"    Scan rate-limited: {scan_id} — retrying in {wait}s")
                time.sleep(wait)
            except Exception as e:  # noqa: BLE001 — enrichment is best-effort
                print(f"    Scan FAILED (non-fatal): {scan_id} - {e}")
                break
        if not created:
            print(f"    Scan FAILED (non-fatal): {scan_id} - still rate-limited; re-run setup.py")
            continue
        try:
            client.run_data_scan(
                request=RunDataScanRequest(name=f"{parent}/dataScans/{scan_id}")
            )
        except Exception as e:  # noqa: BLE001
            print(f"    Scan run failed: {scan_id} - {e}")


def seed_docs_bucket() -> None:
    """Create the GCS bucket and upload the synthetic retail docs (idempotent)."""
    from google.cloud import storage

    client = storage.Client(project=GOOGLE_CLOUD_PROJECT)
    bucket_name = docs_bucket_name()

    bucket = client.bucket(bucket_name)
    if not bucket.exists():
        bucket = client.create_bucket(bucket_name, location=BQ_LOCATION)
        print(f"Bucket: gs://{bucket_name}")
    else:
        print(f"Bucket exists: gs://{bucket_name}")

    print("Retail docs:")
    for filename, content in RETAIL_DOCS.items():
        blob = bucket.blob(f"{DOCS_PREFIX}/{filename}")
        blob.upload_from_string(content, content_type="text/plain")
        print(f"    Uploaded: {DOCS_PREFIX}/{filename}")


def create_ai_connection() -> None:
    """Create the BigQuery Cloud Resource connection and grant its SA roles."""
    import json

    conn_id = ai_connection_id()
    location = BQ_LOCATION.lower()

    # Create (idempotent — a duplicate create is a harmless no-op).
    _run(
        [
            "bq", "mk", "--connection", "--location", location,
            "--connection_type", "CLOUD_RESOURCE",
            "--project_id", GOOGLE_CLOUD_PROJECT, conn_id,
        ]
    )
    show = _run(
        [
            "bq", "show", "--connection", "--format=json",
            "--project_id", GOOGLE_CLOUD_PROJECT, "--location", location, conn_id,
        ]
    )
    if show.returncode != 0:
        print(f"AI connection FAILED: {show.stderr.strip()}")
        return
    sa = json.loads(show.stdout)["cloudResource"]["serviceAccountId"]
    print(f"AI connection: {conn_id} (SA {sa})")
    for role in CONNECTION_SA_ROLES:
        _run(
            [
                "gcloud", "projects", "add-iam-policy-binding", GOOGLE_CLOUD_PROJECT,
                f"--member=serviceAccount:{sa}", f"--role={role}", "--quiet",
            ]
        )
        print(f"    Granted: {role}")
    # IAM propagation lag before the object table can read via this SA.
    time.sleep(10)


def create_object_table() -> None:
    """Create the BigQuery object table over the seeded GCS docs."""
    from google.cloud import bigquery

    client = bigquery.Client(project=GOOGLE_CLOUD_PROJECT)
    table_ref = f"{GOOGLE_CLOUD_PROJECT}.{BQ_DATASET}.{BQ_OBJECT_TABLE}"
    connection = f"{GOOGLE_CLOUD_PROJECT}.{BQ_LOCATION.lower()}.{ai_connection_id()}"
    uris = f"gs://{docs_bucket_name()}/{DOCS_PREFIX}/*"

    ddl = f"""
    CREATE OR REPLACE EXTERNAL TABLE `{table_ref}`
    WITH CONNECTION `{connection}`
    OPTIONS (
      object_metadata = 'SIMPLE',
      uris = ['{uris}']
    )
    """
    try:
        client.query(ddl).result()
        count = list(client.query(f"SELECT COUNT(*) AS n FROM `{table_ref}`").result())[0]["n"]
        print(f"Object table: {BQ_OBJECT_TABLE} ({count} documents)")
    except Exception as e:  # noqa: BLE001
        print(f"Object table FAILED: {e}")


def _project_number() -> str | None:
    """Resolve the project *number* (Agent Runtime's SA is keyed to it)."""
    result = _run(
        [
            "gcloud", "projects", "describe", GOOGLE_CLOUD_PROJECT,
            "--format=value(projectNumber)",
        ]
    )
    number = result.stdout.strip()
    return number or None


def grant_runtime_iam() -> None:
    """Grant the Agent Runtime service agent the roles deployed agents need.

    Only matters once you deploy (deploy/deploy.py); harmless to run before. The
    service agent exists as soon as the aiplatform API is enabled.
    """
    print("Agent Runtime IAM:")
    number = _project_number()
    if not number:
        print("    WARNING: could not resolve project number; skipping Runtime IAM.")
        return
    sa = agent_runtime_service_agent(number)
    for role in RUNTIME_SA_ROLES:
        result = _run(
            [
                "gcloud", "projects", "add-iam-policy-binding", GOOGLE_CLOUD_PROJECT,
                f"--member=serviceAccount:{sa}", f"--role={role}", "--quiet",
            ]
        )
        if result.returncode == 0:
            print(f"    Granted: {role} -> {sa}")
        else:
            print(f"    WARNING: could not grant {role} ({result.stderr.strip()}).")


def main() -> None:
    if not GOOGLE_CLOUD_PROJECT:
        sys.exit("GOOGLE_CLOUD_PROJECT is not set — copy .env.example to .env first.")

    print(f"Provisioning agent-building resources in {GOOGLE_CLOUD_PROJECT}\n")
    enable_apis()
    print()
    create_dataset_and_views()
    print()
    run_profile_scans()
    print()
    seed_docs_bucket()
    print()
    create_ai_connection()
    print()
    create_object_table()
    print()
    grant_runtime_iam()
    print("\nSetup complete. Run the agents with:  uv run adk web .")


if __name__ == "__main__":
    main()
