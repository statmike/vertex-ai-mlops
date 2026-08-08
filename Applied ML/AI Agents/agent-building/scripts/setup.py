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
  8. Runtime IAM     — grants the Agent Runtime service agent the roles deployed
                       agents need but Runtime does not grant automatically:
                       catalog search (discovery), Model Armor (the guard), and
                       Example Store read (the analytics few-shot tool).
  9. Model Armor     — a guardrail template ({MODEL_ARMOR_TEMPLATE}) the concierge
                       screens prompts/responses against, plus the modelarmor.user
                       role on the Agent Runtime service agent so deployed agents
                       can call it.
 10. Example Store   — a managed few-shot store ({EXAMPLE_STORE_DISPLAY_NAME})
                       seeded with curated analytics Q&A; the analytics agent
                       retrieves the most similar examples per question (dynamic
                       few-shot). Vertex assigns it a numeric id, so it's matched
                       by display name — the resource name is printed on create.
 11. RAG corpus      — a RAG Engine corpus ({RAG_CORPUS_DISPLAY_NAME}) over the
                       same GCS retail docs, backed by the managed vector database;
                       the catalog agent retrieves from it (managed alternative to
                       its object-table tool). Also matched by display name.

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
    EXAMPLE_STORE_DISPLAY_NAME,
    EXAMPLE_STORE_EMBEDDING_MODEL,
    EXAMPLE_STORE_LOCATION,
    GOOGLE_CLOUD_PROJECT,
    MODEL_ARMOR_LOCATION,
    MODEL_ARMOR_TEMPLATE,
    RAG_CORPUS_DISPLAY_NAME,
    RAG_EMBEDDING_MODEL,
    RAG_LOCATION,
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
    "modelarmor.googleapis.com",
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
#
# One more deploy-time grant is NOT here on purpose: the concierge's cross-agent
# A2A call to discovery needs aiplatform.reasoningEngines.query, which the stock
# reasoningEngineServiceAgent role lacks. That one is *resource*-scoped (bound to
# the discovery engine only, least privilege) so it can't be granted until the
# engine exists — deploy/deploy.py applies it right after deploying discovery, and
# it's torn down automatically when the engine is deleted.
RUNTIME_SA_ROLES = [
    "roles/dataplex.catalogViewer",
    # The concierge's Model Armor guard calls sanitizeUserPrompt/sanitizeModelResponse
    # on every turn; that permission lives in modelarmor.user. Locally the developer's
    # own creds cover it, so (like catalogViewer) this gap only surfaces once deployed.
    "roles/modelarmor.user",
    # The analytics agent's ExampleTool searches the Example Store each turn
    # (aiplatform.exampleStores.readExample/get/list). The default Runtime service
    # agent role grants none of those; aiplatform.viewer is the least-privilege
    # predefined role that covers exactly the read set (not create/update/delete).
    "roles/aiplatform.viewer",
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


# Curated few-shot examples for the analytics agent's Example Store: each pairs a
# representative question with an ideal, well-formatted answer. The store serves
# the most semantically-similar ones per incoming question, so these shape tone
# and formatting (currency, thousands separators, concise phrasing) dynamically.
ANALYTICS_EXAMPLES: list[tuple[str, str]] = [
    (
        "How many orders were placed in total?",
        "theLook has 124,931 orders in total.",
    ),
    (
        "What were the top 5 product categories by revenue?",
        "The top 5 categories by revenue are:\n"
        "1. Outerwear & Coats — $1.42M\n"
        "2. Jeans — $1.19M\n"
        "3. Sweaters — $0.98M\n"
        "4. Suits & Sport Coats — $0.87M\n"
        "5. Swim — $0.74M",
    ),
    (
        "How many distinct customers have placed at least one order?",
        "80,044 distinct customers have placed at least one order.",
    ),
    (
        "What is the average order value?",
        "The average order value is $85.46 across all completed orders.",
    ),
    (
        "Which distribution center has shipped the most items?",
        "Chicago IL has shipped the most items — 34,127 — followed by "
        "Houston TX (28,905) and Los Angeles CA (26,540).",
    ),
]


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


def create_model_armor_template() -> None:
    """Create the Model Armor guardrail template the concierge screens against.

    Idempotent: an existing template of the same name is left as-is. The template
    is regional and served from a per-region REST endpoint
    (modelarmor.<location>.rep.googleapis.com), so the client is pinned there.

    Filters enabled: prompt-injection / jailbreak detection, malicious-URI
    detection, and responsible-AI harms (hate, harassment, sexual, dangerous) at a
    medium confidence threshold — a sensible default a real deployment would tune.
    """
    from google.api_core.client_options import ClientOptions
    from google.api_core.exceptions import AlreadyExists
    from google.cloud import modelarmor_v1 as ma

    print("Model Armor template:")
    parent = f"projects/{GOOGLE_CLOUD_PROJECT}/locations/{MODEL_ARMOR_LOCATION}"
    client = ma.ModelArmorClient(
        transport="rest",
        client_options=ClientOptions(
            api_endpoint=f"modelarmor.{MODEL_ARMOR_LOCATION}.rep.googleapis.com"
        ),
    )

    medium = ma.DetectionConfidenceLevel.MEDIUM_AND_ABOVE
    template = ma.Template(
        filter_config=ma.FilterConfig(
            pi_and_jailbreak_filter_settings=ma.PiAndJailbreakFilterSettings(
                filter_enforcement=ma.PiAndJailbreakFilterSettings.PiAndJailbreakFilterEnforcement.ENABLED,
                confidence_level=medium,
            ),
            malicious_uri_filter_settings=ma.MaliciousUriFilterSettings(
                filter_enforcement=ma.MaliciousUriFilterSettings.MaliciousUriFilterEnforcement.ENABLED,
            ),
            rai_settings=ma.RaiFilterSettings(
                rai_filters=[
                    ma.RaiFilterSettings.RaiFilter(filter_type=t, confidence_level=medium)
                    for t in (
                        ma.RaiFilterType.HATE_SPEECH,
                        ma.RaiFilterType.HARASSMENT,
                        ma.RaiFilterType.SEXUALLY_EXPLICIT,
                        ma.RaiFilterType.DANGEROUS,
                    )
                ]
            ),
        )
    )
    try:
        client.create_template(
            request=ma.CreateTemplateRequest(
                parent=parent, template_id=MODEL_ARMOR_TEMPLATE, template=template
            )
        )
        print(f"    Created: {MODEL_ARMOR_TEMPLATE} (in {MODEL_ARMOR_LOCATION})")
    except AlreadyExists:
        print(f"    Exists:  {MODEL_ARMOR_TEMPLATE}")
    except Exception as e:  # noqa: BLE001 — guard is optional; don't fail setup
        print(f"    FAILED (non-fatal): {MODEL_ARMOR_TEMPLATE} - {e}")


def _example_store_display_name(store) -> str | None:
    """Read a store's display name across SDK shapes (attr or backing resource)."""
    name = getattr(store, "display_name", None)
    if name:
        return name
    gca = getattr(store, "_gca_resource", None)
    return getattr(gca, "display_name", None)


def create_example_store() -> None:
    """Create the Example Store and seed it with curated analytics few-shot Q&A.

    Idempotent: keyed on the deterministic display name, since Vertex assigns the
    store a numeric resource id at creation (a custom id is ignored). If a store
    with EXAMPLE_STORE_DISPLAY_NAME already exists it's reused; otherwise one is
    created (a slow LRO — several minutes is normal). Either way the store's
    examples are cleared and re-seeded (upsert_examples always *appends* new
    example ids, so a plain re-run would duplicate — we remove first to converge
    on exactly the seed set), and the resolved resource name is printed so it can
    be pinned via EXAMPLE_STORE_NAME to skip the lookup.

    The analytics agent's ExampleTool searches this store on every turn and injects
    the most similar examples, so the seed set shapes answer tone and formatting.
    """
    import vertexai
    from vertexai.preview import example_stores

    print("Example Store:")
    vertexai.init(project=GOOGLE_CLOUD_PROJECT, location=EXAMPLE_STORE_LOCATION)

    # Reuse an existing store with this display name; otherwise create one (slow LRO).
    store = None
    try:
        for existing in example_stores.ExampleStore.list():
            if _example_store_display_name(existing) == EXAMPLE_STORE_DISPLAY_NAME:
                store = existing
                print(f"    Exists:  {EXAMPLE_STORE_DISPLAY_NAME}")
                break
    except Exception as e:  # noqa: BLE001 — list is best-effort; fall through to create
        print(f"    (could not list existing stores: {e})")

    if store is None:
        try:
            store = example_stores.ExampleStore.create(
                example_store_config=example_stores.ExampleStoreConfig(
                    vertex_embedding_model=EXAMPLE_STORE_EMBEDDING_MODEL,
                ),
                display_name=EXAMPLE_STORE_DISPLAY_NAME,
                description="agent-building — curated analytics few-shot examples.",
            )
            print(f"    Created: {EXAMPLE_STORE_DISPLAY_NAME} (in {EXAMPLE_STORE_LOCATION})")
        except Exception as e:  # noqa: BLE001 — store is optional; don't fail setup
            print(f"    FAILED (non-fatal): {EXAMPLE_STORE_DISPLAY_NAME} - {e}")
            return

    # Clear any existing examples first so re-runs converge on exactly the seed
    # set. upsert_examples always appends (fresh example ids), so without this a
    # re-run would silently duplicate every example.
    try:
        fetched = store.fetch_examples()
        existing_examples = (
            fetched.get("examples", []) if isinstance(fetched, dict) else (fetched or [])
        )
        existing_ids = [
            eid
            for e in existing_examples
            if (eid := (e.get("example_id") if isinstance(e, dict) else None))
        ]
        if existing_ids:
            store.remove_examples(example_ids=existing_ids)
            print(f"    Cleared: {len(existing_ids)} prior example(s)")
    except Exception as e:  # noqa: BLE001 — clearing is best-effort
        print(f"    (could not clear prior examples: {e})")

    # Seed the curated examples. Each is a search-key -> (question, ideal answer)
    # pair the tool retrieves by semantic similarity. The Example Store types are
    # TypedDicts keyed on vertexai.generative_models.Content.
    from vertexai.generative_models import Content, Part

    examples: list[example_stores.Example] = [
        example_stores.Example(
            stored_contents_example=example_stores.StoredContentsExample(
                search_key=question,
                contents_example=example_stores.ContentsExample(
                    contents=[
                        Content(role="user", parts=[Part.from_text(question)]),
                    ],
                    expected_contents=[
                        example_stores.ExpectedContent(
                            content=Content(
                                role="model", parts=[Part.from_text(answer)]
                            ),
                        ),
                    ],
                ),
            )
        )
        for question, answer in ANALYTICS_EXAMPLES
    ]
    try:
        store.upsert_examples(examples=examples)
        print(f"    Seeded:  {len(examples)} analytics examples")
    except Exception as e:  # noqa: BLE001
        print(f"    Seed FAILED (non-fatal): {e}")
    # The agent resolves this by display name, but printing the resource name lets
    # you pin EXAMPLE_STORE_NAME to skip that lookup (e.g. in a deploy env).
    print(f"    Resource: {store.resource_name}")


def create_rag_corpus() -> None:
    """Create a RAG Engine corpus over the retail docs and import them.

    Idempotent, keyed on the deterministic display name (like the Example Store,
    Vertex assigns a numeric resource id). If a corpus with RAG_CORPUS_DISPLAY_NAME
    exists it's reused; otherwise one is created backed by the managed vector
    database (RagManagedVertexVectorSearch — this is the Vector Search storage; the
    older RagManagedDb backend is rejected in serverless mode) with the configured
    embedding model. Then the same GCS retail docs the object table exposes are
    imported (chunked + embedded); re-importing the same URIs is a no-op upsert.

    Uses the ``agentplatform`` client (the successor to ``vertexai.preview.rag``,
    which is deprecated and whose backend_config embedding path is broken in this
    SDK build). The catalog agent still *resolves* the corpus via the older SDK's
    list_corpora — the resource is the same either way.

    The catalog agent retrieves from this corpus via ADK's VertexAiRagRetrieval —
    a managed alternative to its object-table + AI.GENERATE tool over the same docs.
    """
    import agentplatform
    from agentplatform._genai.types import common
    from google.genai import types as gtypes

    print("RAG corpus:")
    client = agentplatform.Client(project=GOOGLE_CLOUD_PROJECT, location=RAG_LOCATION)

    # Reuse an existing corpus with this display name; otherwise create one.
    corpus = None
    try:
        for existing in client.rag.list_corpora().rag_corpora or []:
            if existing.display_name == RAG_CORPUS_DISPLAY_NAME:
                corpus = existing
                print(f"    Exists:  {RAG_CORPUS_DISPLAY_NAME}")
                break
    except Exception as e:  # noqa: BLE001 — list is best-effort; fall through to create
        print(f"    (could not list existing corpora: {e})")

    if corpus is None:
        # Embedding endpoint must be fully qualified with the region, or corpus
        # creation fails resolving the prediction endpoint.
        embed_endpoint = (
            f"projects/{GOOGLE_CLOUD_PROJECT}/locations/{RAG_LOCATION}"
            f"/publishers/google/models/{RAG_EMBEDDING_MODEL}"
        )
        try:
            corpus = client.rag.create_corpus(
                rag_corpus=common.RagCorpus(
                    display_name=RAG_CORPUS_DISPLAY_NAME,
                    description="agent-building — theLook retail docs (managed RAG).",
                    vector_db_config=common.RagVectorDbConfig(
                        rag_managed_vertex_vector_search=(
                            common.RagVectorDbConfigRagManagedVertexVectorSearch()
                        ),
                        rag_embedding_model_config=common.RagEmbeddingModelConfig(
                            vertex_prediction_endpoint=(
                                common.RagEmbeddingModelConfigVertexPredictionEndpoint(
                                    endpoint=embed_endpoint,
                                )
                            ),
                        ),
                    ),
                ),
            )
            print(f"    Created: {RAG_CORPUS_DISPLAY_NAME} (in {RAG_LOCATION})")
        except Exception as e:  # noqa: BLE001 — corpus is optional; don't fail setup
            print(f"    FAILED (non-fatal): {RAG_CORPUS_DISPLAY_NAME} - {e}")
            return

    # Import the same GCS docs the object table exposes. Re-importing identical
    # URIs upserts (no duplicates), so this is safe to re-run.
    uris = f"gs://{docs_bucket_name()}/{DOCS_PREFIX}/"
    try:
        resp = client.rag.import_files(
            name=corpus.name,
            import_config=common.ImportRagFilesConfig(
                gcs_source=gtypes.GcsSource(uris=[uris]),
                rag_file_chunking_config=common.RagFileChunkingConfig(
                    chunk_size=512, chunk_overlap=100
                ),
            ),
        )
        print(f"    Imported: {uris} ({resp.imported_rag_files_count} files)")
    except Exception as e:  # noqa: BLE001
        print(f"    Import FAILED (non-fatal): {e}")
    # Printed so it can be pinned via RAG_CORPUS_NAME to skip the runtime lookup.
    print(f"    Resource: {corpus.name}")


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
    create_model_armor_template()
    print()
    create_example_store()
    print()
    create_rag_corpus()
    print()
    grant_runtime_iam()
    print("\nSetup complete. Run the agents with:  uv run adk web .")


if __name__ == "__main__":
    main()
