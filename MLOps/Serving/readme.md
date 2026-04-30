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

This section focuses on turning trained machine learning models into production-ready services. 26 notebooks explore every major GCP serving pattern — online prediction, batch inference, SQL-based inference, multi-platform deployment, and Triton Inference Server — all using the same HuggingFace sentiment models for consistency.

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

## Online Prediction

Real-time, low-latency serving via Vertex AI Endpoints. See the **[Online Prediction](./Online/readme.md)** series for 7 notebooks covering every endpoint type, prediction method, autoscaling, and cost optimization:

| Notebook | Focus | Key Differentiator |
|----------|-------|-------------------|
| [Dedicated Public Endpoint](./Online/Vertex%20AI%20Dedicated%20Public%20Endpoint.ipynb) | Endpoint type | Recommended default: 10 MB, 1-hour timeout, gRPC, SSE |
| [Shared Public Endpoint](./Online/Vertex%20AI%20Shared%20Public%20Endpoint.ipynb) | Endpoint type | Simplest setup, tuned Gemini + AutoML explainability support |
| [Private Endpoint With PSC](./Online/Vertex%20AI%20Private%20Endpoint%20With%20PSC.ipynb) | Endpoint type | Private networking via PSC, GCE VM test client |
| [PSC Endpoint - Pipeline Model Swap](./Online/Vertex%20AI%20PSC%20Endpoint%20-%20Pipeline%20Model%20Swap.ipynb) | MLOps | KFP-automated rollout with health checks and rollback |
| [Prediction Methods](./Online/Vertex%20AI%20Endpoint%20-%20Prediction%20Methods.ipynb) | Reference | Every prediction method: SDK, REST, gRPC, streaming, multi-language |
| [Autoscaling](./Online/Vertex%20AI%20Endpoint%20-%20Autoscaling.ipynb) | Operations | Load testing, live metrics dashboard, runtime reconfiguration |
| [Model Cohosting](./Online/Vertex%20AI%20Endpoint%20-%20Model%20Cohosting.ipynb) | Cost optimization | DeploymentResourcePool, shared VMs, per-model endpoints |

All notebooks use the same HuggingFace sentiment models in a custom FastAPI container. See the [Online readme](./Online/readme.md) for full descriptions.

---

## Batch Inference

Processing large datasets through ML models in a single operation. See the **[Batch Inference](./Batch/readme.md)** series for 4 notebooks covering the same problem across different platforms:

| Notebook | Platform | Key Differentiator |
|----------|----------|-------------------|
| [Vertex AI Batch Prediction](./Batch/Vertex%20AI%20Batch%20Prediction.ipynb) | Vertex AI | Managed, container-based, `instanceConfig` column control |
| [Batch Inference With Dataflow](./Batch/Batch%20Inference%20With%20Dataflow.ipynb) | Dataflow | Beam pipelines, native pre/post processing, `KeyedModelHandler` |
| [Batch Inference With Dataproc](./Batch/Batch%20Inference%20With%20Dataproc.ipynb) | Dataproc Serverless | PySpark, Pandas UDF, runtime 2.2 pre-installed ML libs |
| [Orchestrating Batch Inference With Airflow](./Batch/Orchestrating%20Batch%20Inference%20With%20Airflow.ipynb) | Cloud Composer | Scheduling, data dependencies, Airflow → KFP and direct patterns |

Each notebook demonstrates multi-model inference, pre/post processing, and KFP orchestration. See the [Batch readme](./Batch/readme.md) for the full decision framework.

---

## SQL Inference

Run ML predictions directly from SQL — no Python serving code needed. See the **[SQL Inference](./SQL%20Inference/readme.md)** series for 5 notebooks covering two patterns: **remote models** (SQL calls a Vertex AI Endpoint) and **model import** (model runs inside the database engine):

| Notebook | Database | Pattern | Key Differentiator |
|----------|----------|---------|-------------------|
| [BQML Remote Model](./SQL%20Inference/BQML%20Remote%20Model%20on%20Vertex%20AI%20Endpoint.ipynb) | BigQuery | Remote model | OLAP batch scoring, `ML.PREDICT()` via Cloud Resource Connection |
| [AlloyDB AI Remote Model](./SQL%20Inference/AlloyDB%20AI%20Remote%20Model%20on%20Vertex%20AI%20Endpoint.ipynb) | AlloyDB | Remote model | OLTP row-level predictions, `google_ml.predict_row()` |
| [Spanner ML Remote Model](./SQL%20Inference/Spanner%20ML%20Remote%20Model%20on%20Vertex%20AI%20Endpoint.ipynb) | Spanner | Remote model | Globally distributed inference, `ML.PREDICT()` |
| [BQML Import via ONNX](./SQL%20Inference/BQML%20Import%20Model%20via%20ONNX.ipynb) | BigQuery | Model import | Model runs IN BigQuery, no endpoint needed, < 250 MB |
| [BQ TF SavedModel](./SQL%20Inference/Serve%20TensorFlow%20SavedModel%20Format%20With%20BigQuery.ipynb) | BigQuery | Model import | Import TensorFlow SavedModel for serverless SQL predictions |

See the [SQL Inference readme](./SQL%20Inference/readme.md) for the full database ML comparison table.

---

## Serving Platforms

The same custom prediction container deployed to different GCP platforms. See the **[Platforms](./Platforms/readme.md)** series for 4 notebooks demonstrating container portability:

| Notebook | Platform | Key Differentiator |
|----------|----------|-------------------|
| [Serving Models on Cloud Run](./Platforms/Serving%20Models%20on%20Cloud%20Run.ipynb) | Cloud Run | Scale-to-zero, OIDC auth, revision-based traffic splitting |
| [Serving Models on GKE](./Platforms/Serving%20Models%20on%20GKE.ipynb) | GKE Autopilot | Full Kubernetes control, HPA autoscaling, Workload Identity |
| [Serving Models With Cloud Functions](./Platforms/Serving%20Models%20With%20Cloud%20Functions.ipynb) | Cloud Functions | Lightest serverless option, no container needed, source deploy |
| [Vertex AI Pre-built Serving Containers](./Platforms/Vertex%20AI%20Pre-built%20Serving%20Containers.ipynb) | Vertex AI | No Dockerfile, no Cloud Build — pre-built TorchServe/TF Serving |

See the [Platforms readme](./Platforms/readme.md) for the full platform comparison table.

---

## Triton Inference Server

[NVIDIA Triton Inference Server](https://developer.nvidia.com/triton-inference-server) — a standardized serving platform with model repository, multi-backend support, dynamic batching, and ensemble pipelines. See the **[Triton](./Triton/readme.md)** series for 5 notebooks progressing from local Docker fundamentals to production deployment on three platforms:

| Notebook | Focus | Key Differentiator |
|----------|-------|-------------------|
| [Fundamentals](./Triton/Triton%20Inference%20Server%20-%20Fundamentals.ipynb) | Core concepts | Model repository, Python + ONNX backends, HTTP/gRPC clients, dynamic batching |
| [Pipelines and Ensembles](./Triton/Triton%20Inference%20Server%20-%20Pipelines%20and%20Ensembles.ipynb) | Server-side pipelines | Declarative ensembles, BLS imperative routing, model swap |
| [Triton on Vertex AI](./Triton/Triton%20on%20Vertex%20AI%20Endpoints.ipynb) | Managed deployment | rawPredict, multi-model routing, L4 GPU + TensorRT |
| [Triton on Cloud Run](./Triton/Triton%20on%20Cloud%20Run.ipynb) | Serverless | L4 GPU, OIDC auth, cold start analysis, concurrency tuning |
| [Triton on GKE](./Triton/Triton%20on%20GKE.ipynb) | Full control | GCS FUSE model repo, HPA with Triton metrics, production probes |

Notebooks 1-2 run CPU-only with local Docker (no GCP project needed). Notebooks 3-5 deploy to GCP with L4 GPU. See the [Triton readme](./Triton/readme.md) for full descriptions.

---

## Foundational Notebook

| Notebook | Focus |
|----------|-------|
| [Understanding Prediction IO With FastAPI](./Understanding%20Prediction%20IO%20With%20FastAPI.ipynb) | Build a custom prediction container, serve online and batch predictions across local, Vertex AI, and Cloud Run |

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
    - [RunInference Basics](../../data%2Bai/dataflow/examples/dataflow-runinference-basics.ipynb)
    - [Model Hot-Swap (Event Mode via Pub/Sub)](../../data%2Bai/dataflow/examples/dataflow-runinference-model-hotswap-event-mode.ipynb)
    - [Model Hot-Swap (Watch Mode via GCS polling)](../../data%2Bai/dataflow/examples/dataflow-runinference-model-hotswap-watch-mode.ipynb)
    - [GPU Inference Benchmark (Local GPU vs Vertex AI Endpoint)](../../data%2Bai/dataflow/gpu/benchmark/README.md)
    - [Python to Java Translation Guide](../../data%2Bai/dataflow/python-to-java.md)

---

## Serving on Dataproc

Spark-based ML inference on [Dataproc](https://cloud.google.com/dataproc), using PySpark Pandas UDFs for batch and streaming workloads. Dataproc Serverless Runtime 2.2 ships with torch and transformers pre-installed — no custom container or dependency installation needed.

Two approaches:
- **Model on Worker** — Load the model directly into Spark executors via Pandas UDF with module-level caching (highest throughput, no endpoint needed)
- **Call a Vertex AI Endpoint** — Workers call a deployed endpoint via `aiplatform.Endpoint.predict()` (centralized model management, no ML libs needed on workers)

**Examples in this repository:**
- `vertex-ai-mlops/data+ai/dataproc/` — Standalone Dataproc examples:
    - [Dataproc Serverless Fundamentals](../../data%2Bai/dataproc/examples/dataproc-serverless-fundamentals.ipynb)
    - [Spark Batch Inference](../../data%2Bai/dataproc/examples/dataproc-batch-inference.ipynb)
    - [Spark Structured Streaming for ML](../../data%2Bai/dataproc/examples/dataproc-structured-streaming.ipynb)
    - [Spark + Vertex AI Endpoint](../../data%2Bai/dataproc/examples/dataproc-vertex-ai-endpoint.ipynb)
- `vertex-ai-mlops/MLOps/Serving/Batch/` — Dataproc as a batch inference platform with KFP orchestration:
    - [Batch Inference With Dataproc](./Batch/Batch%20Inference%20With%20Dataproc.ipynb)

---

## Related Workflows

- `vertex-ai-mlops/Framework Workflows/CatBoost/`
    -  Customize prediction responses
        -  [CatBoost Custom Prediction With FastAPI](../../Framework%20Workflows/CatBoost/CatBoost%20Custom%20Prediction%20With%20FastAPI.ipynb)
            - Create multiple FastAPI apps in the same container. One that serves simple responses, another that gives details responses
            - Create a custom container and use it locally, on Vertex AI Endpoints, and Cloud Run to serve either response type
    - Simplify serving by integrating Vertex AI Feature Store API into your custom prediction - fetch features from Vertex AI Feature Store at serving time
        - [CatBoost Prediction With Vertex AI Feature Store](../../Framework%20Workflows/CatBoost/CatBoost%20Prediction%20With%20Vertex%20AI%20Feature%20Store.ipynb)
            - Custom serving container build with FastAPI
            - Incorporate feature retrieval from Vertex AI Feature Store

**Note:** While this section provides targeted examples, you'll find model serving techniques integrated into various other tutorials and guides throughout the repository.
