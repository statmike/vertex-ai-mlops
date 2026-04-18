![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2FMLOps%2FServing&file=readme.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/MLOps/Serving/readme.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https://github.com/statmike/vertex-ai-mlops/blob/main/MLOps/Serving/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https://github.com/statmike/vertex-ai-mlops/blob/main/MLOps/Serving/readme.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https://github.com/statmike/vertex-ai-mlops/blob/main/MLOps/Serving/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https://github.com/statmike/vertex-ai-mlops/blob/main/MLOps/Serving/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Connect With Author On: </b> 
    <a href="https://www.linkedin.com/in/statmike"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a>
    <a href="https://www.github.com/statmike"><img src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub Logo" width="20px"></a> 
    <a href="https://www.youtube.com/@statmike-channel"><img src="https://upload.wikimedia.org/wikipedia/commons/f/fd/YouTube_full-color_icon_%282024%29.svg" alt="YouTube Logo" width="20px"></a>
    <a href="https://bsky.app/profile/statmike.bsky.social"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://x.com/statmike"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/MLOps/Serving/readme.md"><img src="https://www.svgrepo.com/download/5445/download-button.svg" alt="Download icon" width="20px"></a> <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/MLOps/Serving/readme.md">Download File</a> <i>(right-click and "Save As")</i>
  </td>
</tr>
</table><br/><br/>

---
# Model Serving

> You are here: `vertex-ai-mlops/MLOps/Serving/readme.md`

This section focuses on turning trained machine learning models into production-ready services, a critical step in the MLOps lifecycle. We'll explore various techniques and tools for deploying models on Vertex AI and other GCP services, enabling you to efficiently serve predictions for your applications.

## Environment Setup

### Option 1: Local environment

Set up a local Python environment and register it as a Jupyter kernel. From this directory (`MLOps/Serving/`):

**Python version:** This project requires Python >= 3.10. Use whichever version manager you prefer:
- **pyenv**: `pyenv install 3.11 && pyenv local 3.11` — all tools below will use it automatically
- **uv**: downloads a compatible version automatically if one isn't found
- **system**: any system Python >= 3.10 works

**uv** (recommended)
```bash
uv sync
uv run python -m ipykernel install --user --name mlops-serving --display-name "MLOps Serving"
```

**pip**
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
python -m ipykernel install --user --name mlops-serving --display-name "MLOps Serving"
```

**poetry**
```bash
poetry install
poetry run python -m ipykernel install --user --name mlops-serving --display-name "MLOps Serving"
```

Then select the **MLOps Serving** kernel in your notebook.

### Option 2: Standalone

Each notebook includes an environment setup cell that installs required packages into your current kernel using `uv` (if available) with `pip` fallback. No pre-configuration needed — just run the notebook.

---

## Serving Methods

There are two primary approaches to model serving, each with its own set of considerations:

- **Online Prediction:**  Provides real-time, on-demand predictions with low latency. Ideal for applications requiring immediate responses, such as web applications, fraud detection systems, and interactive chatbots.
- **Batch Prediction:** Processes a collection of input data points in a single operation. Suitable for scenarios where immediate feedback isn't critical, like generating daily reports, analyzing customer behavior trends, or making recommendations.

---

## Vertex AI Endpoint Types

When deploying models for online prediction on Vertex AI, you choose an [endpoint type](https://cloud.google.com/vertex-ai/docs/predictions/choose-endpoint-type) that determines networking, resource isolation, and capabilities. There are four endpoint types organized along two axes: **network access** (public vs private) and **resource isolation** (dedicated vs shared networking plane).

### The Four Endpoint Types

**Dedicated Public Endpoint (recommended)** — Accessible over the public internet using a dedicated networking plane. This is the recommended default for most workloads. Provides production isolation, larger payloads (10 MB), configurable timeouts (up to 1 hour), unlimited QPM, gRPC support, and server-sent events (SSE) streaming.

**Shared Public Endpoint** — Accessible over the public internet using a shared networking plane. Simpler to set up but has significant limitations: 1.5 MB payload limit, 60-second timeout, 30K QPM quota, HTTP only (no gRPC), and no streaming. This is the only endpoint type that supports tuned Gemini model deployment and AutoML models with explainability.

**Dedicated Private Endpoint using PSC (recommended)** — Private access through a [Private Service Connect](https://cloud.google.com/vpc/docs/private-service-connect) forwarding rule. Recommended for production enterprise applications. Same capabilities as dedicated public (10 MB, 1 hour timeout, unlimited QPM, gRPC, SSE) but traffic stays on private networks. Supports transitive connectivity and multiple VPCs.

**Private Endpoint (VPC Peering)** — Private access via [VPC Network Peering](https://cloud.google.com/vpc/docs/vpc-peering) with the Vertex AI service project. The most limited type: no traffic splitting, no request/response logging, no streaming, HTTP only, and 60-second timeout. Does support VPC Service Controls.

### Comparison Table

| Feature | Dedicated Public | Shared Public | Dedicated Private (PSC) | Private (VPC Peering) |
|---------|:---:|:---:|:---:|:---:|
| **Networking** | Public, dedicated plane | Public, shared plane | Private via PSC | Private via VPC Peering |
| **Payload size limit** | 10 MB | 1.5 MB | 10 MB | 10 MB |
| **Inference timeout** | Up to 1 hour | 60 seconds | Up to 1 hour | 60 seconds |
| **QPM quota** | Unlimited | 30,000 | Unlimited | Unlimited |
| **Protocol** | HTTP or gRPC | HTTP only | HTTP or gRPC | HTTP only |
| **Streaming (SSE)** | Yes | No | Yes | No |
| **Traffic splitting** | Yes | Yes | Yes | **No** |
| **Request/response logging** | Yes | Yes | Yes | **No** |
| **Access logging** | Yes | Yes | Yes | **No** |
| **VPC Service Controls** | **No** | Yes | Yes | Yes |
| **Encryption in transit** | TLS (CA-signed) | TLS (CA-signed) | TLS (self-signed, optional) | None |
| **Tuned Gemini deployment** | No | **Yes** | No | No |
| **AutoML + explainability** | No | **Yes** | No | No |

### Creating Each Endpoint Type

#### Dedicated Public Endpoint (recommended)

```python
from google.cloud import aiplatform

aiplatform.init(project = PROJECT_ID, location = REGION)

# Create a dedicated public endpoint
endpoint = aiplatform.Endpoint.create(
    display_name = "my-dedicated-public-endpoint",
    dedicated_endpoint_enabled = True,
)

# Deploy a model
endpoint.deploy(
    model = model,
    deployed_model_display_name = "model-v1",
    machine_type = "n1-standard-4",
    min_replica_count = 1,
    max_replica_count = 5,
)
```

#### Shared Public Endpoint

```python
# Create a shared public endpoint (the default when dedicated_endpoint_enabled is not set)
endpoint = aiplatform.Endpoint.create(
    display_name = "my-shared-public-endpoint",
)

# Deploy a model — traffic_percentage controls traffic splitting across deployed models
endpoint.deploy(
    model = model,
    deployed_model_display_name = "model-v1",
    machine_type = "n1-standard-4",
    min_replica_count = 1,
    max_replica_count = 3,
    traffic_percentage = 100,
)
```

#### Dedicated Private Endpoint using PSC (recommended for private access)

```python
# Step 1: Create endpoint with PSC enabled
endpoint = aiplatform.Endpoint.create(
    display_name = "my-psc-endpoint",
    dedicated_endpoint_enabled = True,
    enable_private_service_connect = True,
    project_allowlist = [PROJECT_ID],  # projects allowed to connect
)

# Step 2: Deploy model
endpoint.deploy(
    model = model,
    deployed_model_display_name = "model-v1",
    machine_type = "n1-standard-4",
    min_replica_count = 1,
    max_replica_count = 3,
)

# Step 3: Create a PSC forwarding rule in your VPC (via gcloud or Terraform)
# pointing to the service attachment from endpoint.private_service_connect_config
```

#### Private Endpoint (VPC Peering)

```python
# Requires VPC peering with servicenetworking.googleapis.com already established
endpoint = aiplatform.Endpoint.create(
    display_name = "my-vpc-peering-endpoint",
    network = f"projects/{PROJECT_NUMBER}/global/networks/{VPC_NETWORK}",
)

endpoint.deploy(
    model = model,
    deployed_model_display_name = "model-v1",
    machine_type = "n1-standard-4",
    min_replica_count = 1,
    max_replica_count = 3,
)
```

### Choosing an Endpoint Type

```
Is private network access required?
│
├── No (public internet is fine)
│   │
│   ├── Need tuned Gemini or AutoML + explainability?
│   │   ├── Yes ──► Shared Public Endpoint
│   │   └── No  ──► Dedicated Public Endpoint (recommended)
│   │
│   └── Need VPC Service Controls on a public endpoint?
│       └── Yes ──► Shared Public Endpoint
│
└── Yes (traffic must stay private)
    │
    ├── Need traffic splitting, logging, gRPC, or streaming?
    │   └── Yes ──► Dedicated Private Endpoint (PSC) (recommended)
    │
    └── Already have VPC peering and only need basic HTTP?
        └── Yes ──► Private Endpoint (VPC Peering)
```

> **Note:** The VPC Peering private endpoint is the most restricted type — no traffic splitting, no logging, no streaming, and 60-second timeouts. For new private deployments, prefer PSC.

> For full details, see the [Choose an endpoint type](https://cloud.google.com/vertex-ai/docs/predictions/choose-endpoint-type) documentation.

---

## Serving on Dataflow Streaming Pipelines

Beyond Vertex AI Endpoints and Batch Prediction, you can embed model inference directly into [Dataflow](https://cloud.google.com/dataflow) streaming pipelines using Apache Beam's [RunInference API](https://beam.apache.org/documentation/ml/about-ml/). This is ideal for continuous, event-driven predictions — processing messages from Pub/Sub, applying a model, and writing results to BigQuery or another sink, all in a single pipeline.

Two approaches:
- **Local Model on Workers** — Load the model directly into Dataflow workers for in-process inference (lower latency, no endpoint needed)
- **Call a Vertex AI Endpoint** — Workers call a deployed endpoint via API (centralized model management, independent scaling)

**Examples in this repository:**
- `vertex-ai-mlops/Framework Workflows/PyTorch/serving/` — Complete Dataflow serving workflows including batch and streaming with both local models and Vertex AI Endpoints, keyed inference, model hot-swap, and scale testing:
    - [Streaming RunInference (local model)](../../Framework%20Workflows/PyTorch/serving/dataflow-streaming-runinference.ipynb)
    - [Streaming RunInference (Vertex AI Endpoint)](../../Framework%20Workflows/PyTorch/serving/dataflow-streaming-runinference-vertex.ipynb)
    - [Streaming with Keyed Model Handler](../../Framework%20Workflows/PyTorch/serving/dataflow-streaming-runinference-keyed.ipynb)
    - [Streaming with Runtime Model Hot-Swap (Event Mode)](../../Framework%20Workflows/PyTorch/serving/dataflow-streaming-runinference-keyed-event-mode.ipynb)
    - [Scale Testing: Streaming with Local Model](../../Framework%20Workflows/PyTorch/serving/scale-tests-dataflow-streaming-runinference.ipynb)
    - [Scale Testing: Streaming with Vertex AI Endpoint](../../Framework%20Workflows/PyTorch/serving/scale-tests-dataflow-streaming-vertex.ipynb)
    - See the full [PyTorch Serving readme](../../Framework%20Workflows/PyTorch/serving/readme.md) for all workflows
- `vertex-ai-mlops/data+ai/dataflow/` — Standalone Dataflow examples and advanced topics:
    - [Model Hot-Swap (Event Mode via Pub/Sub)](../../data%2Bai/dataflow/examples/dataflow-runinference-model-hotswap-event-mode.ipynb)
    - [Model Hot-Swap (Watch Mode via GCS polling)](../../data%2Bai/dataflow/examples/dataflow-runinference-model-hotswap-watch-mode.ipynb)
    - [GPU Inference Benchmark (Local GPU vs Vertex AI Endpoint)](../../data%2Bai/dataflow/gpu/benchmark/README.md)
    - [Python to Java Translation Guide](../../data%2Bai/dataflow/python-to-java.md)

---

## Tutorials and Examples

**Workflows:**
- Building a custom prediction container that works for online and batch predition across local, Vertex AI Endpoints, Vertex AI Batch Predictions, and Cloud Run
    - [Understanding Prediction IO With FastAPI](./Understanding%20Prediction%20IO%20With%20FastAPI.ipynb)
        - Build A Custom Container with FastAPI that repeara the inputs as output predictions
        - Serve **online predictions** with the container: locally, on Vertex AI Prediction Endpoints, on Cloud Run
        - Serve **batch predictions** with Vertex AI Batch Prediction and multiple input types:
            - JSONL
            - CSV
            - BigQuery
            - File List
            - TFRecord Files
- Deploy a model to a dedicated public endpoint with production isolation, traffic splitting, and lifecycle management
    - [Vertex AI Dedicated Public Endpoint](./Vertex%20AI%20Dedicated%20Public%20Endpoint.ipynb)
        - Build a custom FastAPI container for HuggingFace sentiment models with Cloud Build
        - Create a dedicated public endpoint (`dedicated_endpoint_enabled=True`) and deploy two model versions
        - Shift traffic between models, validate predictions, and undeploy cleanly
        - Demonstrates the recommended default endpoint type: 10 MB payloads, up to 1-hour timeout, unlimited QPM, gRPC and SSE streaming support
- Deploy a model to a shared public endpoint — the simplest setup with trade-offs on payload size and timeout
    - [Vertex AI Shared Public Endpoint](./Vertex%20AI%20Shared%20Public%20Endpoint.ipynb)
        - Build a custom FastAPI container for HuggingFace sentiment models with Cloud Build
        - Create a shared public endpoint (the default, no special flags) and deploy two model versions
        - Shift traffic between models, validate predictions, and undeploy cleanly
        - Highlights limitations: 1.5 MB payload, 60-second timeout, 30K QPM, HTTP only — but the only type supporting tuned Gemini deployment and AutoML with explainability
- Deploy models to a PSC private endpoint, swap models with traffic splitting, and prove the private IP stays stable through lifecycle changes
    - [Vertex AI Private Endpoint With PSC](./Vertex%20AI%20Private%20Endpoint%20With%20PSC.ipynb)
        - Build a custom FastAPI container for HuggingFace sentiment models with Cloud Build
        - Create a PSC-enabled private endpoint and deploy the first model (the service attachment only exists after deploy — no serving infrastructure is provisioned until then)
        - Set up PSC networking: reserve an internal IP and create a forwarding rule pointing to the service attachment
        - Shift traffic between models and undeploy while verifying the private IP and connection remain uninterrupted
        - Self-contained demo with a GCE VM test client for sending requests to the private IP
- Automate model rollout on a PSC private endpoint using Vertex AI Pipelines
    - [Vertex AI PSC Endpoint - Pipeline Model Swap](./Vertex%20AI%20PSC%20Endpoint%20-%20Pipeline%20Model%20Swap.ipynb)
        - Set up PSC infrastructure (endpoint, networking, VM) and deploy an initial model manually
        - Define a Kubeflow Pipeline with components for: verify endpoint, deploy at 0% traffic, shift traffic, verify deployment health, undeploy old models, and notify
        - KFP artifacts (`dsl.Artifact` for endpoint, `dsl.Model` for model) flow between components and create lineage in Vertex AI ML Metadata — including model registry version tracking
        - Pipeline validates deployment via the management API; PSC forwarding rules are not transitive through VPC peering, so prediction testing is done independently from the GCE VM
        - Uses `dsl.ExitHandler` for notification, `dsl.If`/`dsl.Else` for conditional undeploy vs automatic rollback on verification failure
        - Independently verify predictions through the PSC private IP from the GCE VM after the pipeline completes
- Every way to request predictions from a Vertex AI Endpoint — comprehensive multi-language reference
    - [Vertex AI Endpoint - Prediction Methods](./Vertex%20AI%20Endpoint%20-%20Prediction%20Methods.ipynb)
        - Deploy a single model to a dedicated public endpoint and demonstrate every prediction method
        - Python SDK high-level: `predict()`, `raw_predict()`, `predict_async()`, `stream_raw_predict()`
        - Python SDK low-level (gapic): `PredictionServiceClient` and `PredictionServiceAsyncClient` for sync/async predict and raw_predict
        - Dedicated endpoint direct URL: route requests through the unique DNS (`dedicated_endpoint_dns`)
        - REST API in Python (`requests`, `httpx` async), `curl`, plus reference examples in Node.js, Java, and Go
        - gcloud CLI: `gcloud ai endpoints predict` and `gcloud ai endpoints raw-predict`
        - gRPC transport: inspect and use the gRPC channel underlying the gapic client
        - Streaming (SSE): `stream_raw_predict` and `:streamRawPredict` REST endpoint
        - Sync vs async concurrency benchmarks with `asyncio.Semaphore`
        - Error handling with exponential backoff retries
        - Endpoint type compatibility chart: which methods work with which endpoint types
        - Cross-references to PSC notebooks for private endpoint prediction examples
- Understand and observe autoscaling behavior through load testing and live metric visualization
    - [Vertex AI Endpoint - Autoscaling](./Vertex%20AI%20Endpoint%20-%20Autoscaling.ipynb)
        - Deploy with configurable autoscaling: `min_replica_count=1`, `max_replica_count=5`, CPU target 60%
        - Explore Cloud Monitoring metrics: discover available metrics, build a reusable query helper with sparse metric handling (raw query + pandas resample + ffill)
        - Experiment 1 — CPU-triggered scaling: generate sustained load, watch scale-up, observe the 5-minute stabilization window and scale-down timing
        - Experiment 2 — Request-count scaling: switch to traffic-based scaling with `mutateDeployedModel` REST API (no redeploy), compare behavior with CPU-based
        - Experiment 3 — Threshold tuning: lower CPU target from 60% to 30%, show earlier trigger with moderate load
        - 4-panel matplotlib dashboard: replicas (actual vs target), CPU utilization with threshold line, predictions/sec, P95 latency — all on shared time axes with event markers
        - Configuration reference: all autoscaling parameters, `mutateDeployedModel` vs redeploy, cost implications, gotchas (reserved vCPU, single-threaded servers, GPU+CPU interaction, scale-to-zero)
- Deploy the same custom prediction container to Cloud Run and compare with Vertex AI Endpoints
    - [Serving Models on Cloud Run](./Serving%20Models%20on%20Cloud%20Run.ipynb)
        - Deploy the same FastAPI container to Cloud Run — same Docker image, same model, different platform. Container portability via explicit `AIP_*` environment variables.
        - Authentication deep dive: Cloud Run uses OIDC **ID tokens** (not the access tokens used with Vertex AI). Demonstrates the common mistake, the correct pattern with `google.oauth2.id_token.fetch_id_token()`, granting `roles/run.invoker`, and public access with `allUsers`.
        - Traffic splitting between revisions: deploy DistilBERT (v1), update to BERT (v2), split traffic 50/50, verify both models serving via different label formats, shift 100% to v2
        - Configuration reference: autoscaling comparison (scale-to-zero, concurrency-based vs CPU-based), GPU on Cloud Run (L4, constraints), decision framework for when to choose Cloud Run vs Vertex AI
- Private Endpoint (VPC Peering) — not demonstrated in a notebook
    - Uses [VPC Network Peering](https://cloud.google.com/vpc/docs/vpc-peering) with the Vertex AI service project for private network access. This is the most restricted endpoint type: no traffic splitting, no request/response logging, no streaming, HTTP only, and a 60-second timeout. Requires establishing VPC peering with `servicenetworking.googleapis.com` before creating the endpoint. For new private deployments, **prefer the PSC approach** — it supports traffic splitting, logging, gRPC, streaming, larger payloads, longer timeouts, and works across multiple VPCs without the limitations of peering. See the [Choose an endpoint type](https://cloud.google.com/vertex-ai/docs/predictions/choose-endpoint-type) documentation for full details.
- Import TensorFlow SavedModel format model directly into BigQuery and get serverless predictions with SQL
    - [Serve TensorFlow SavedModel Format With BigQuery](./Serve%20TensorFlow%20SavedModel%20Format%20With%20BigQuery.ipynb) 

**Related Workflows:**
- `vertex-ai-mlops/Framework Workflows/Catboost/`
    -  Customize prediction responses
        -  [CatBoost Custom Prediction With FastAPI](../../Framework%20Workflows/CatBoost/CatBoost%20Custom%20Prediction%20With%20FastAPI.ipynb)
            - Create multiple FastAPI apps in the same container. One that serves simple responses, another that gives details responses
            - Create a custom container and use it locally, on Vertex AI Endpoints, and Cloud Run to serve either response type
    - Simplify serving by integrating Vertex AI Feature Store API into your custom prediction - fetch features from Vertex AI Feature Store at serving time
        - [CatBoost Prediction With Vertex AI Feature Store](../../Framework%20Workflows/CatBoost/CatBoost%20Prediction%20With%20Vertex%20AI%20Feature%20Store.ipynb)
            - Custom serving container build with FastAPI
            - Incorporate feature retrieval from Vertex AI Feature Store

**Note:** While this section provides targeted examples, you'll find model serving techniques integrated into various other tutorials and guides throughout the repository.