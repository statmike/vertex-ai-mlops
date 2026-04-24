# Serving — Expansion Plans

> New notebooks to round out the Serving section. Each is self-contained and follows the established Serving series conventions (header, setup, Colab support, cleanup). Delete individual entries as notebooks are completed.

## Current State

```
MLOps/Serving/
├── Online/                          (6 notebooks — Vertex AI endpoint types, methods, autoscaling)
├── Batch/                           (4 notebooks — Vertex AI Batch, Dataflow, Dataproc, Airflow)
├── Understanding Prediction IO With FastAPI.ipynb
├── Serving Models on Cloud Run.ipynb
├── Serve TensorFlow SavedModel Format With BigQuery.ipynb
├── pyproject.toml, readme.md
```

---

## New Notebooks

### 1–3. Remote Models Series

**Placement:** `MLOps/Serving/Remote Models/` — new subfolder with its own `readme.md`

All three GCP database services can call a Vertex AI Endpoint as a remote model via their native SQL interface. One endpoint deployment, three SQL surfaces. Each notebook deploys the same HuggingFace sentiment model to a Vertex AI Endpoint, then demonstrates calling it from SQL — no Python needed for inference.

The shared pattern: deploy model → create connection → register remote model → `ML.PREDICT()` / `google_ml.predict()` from SQL.

#### 1. BQML Remote Model on Vertex AI Endpoint

**Status:** Not Started

**File:** `Remote Models/BQML Remote Model on Vertex AI Endpoint.ipynb`

**What it covers:**
- Deploy the sentiment model to a Vertex AI Endpoint (reuse the FastAPI container pattern from Online/)
- Create a BigQuery Cloud Resource Connection (`CREATE CONNECTION`)
- Register the endpoint as a BQML remote model (`CREATE MODEL ... REMOTE WITH CONNECTION`)
- Run predictions from SQL with `ML.PREDICT()` — no Python needed for inference
- Compare: model import (ONNX/TF, runs inside BQ, <250 MB limit) vs remote model (any framework, any size, calls endpoint)
- Batch scoring patterns: `ML.PREDICT()` over a full table, with WHERE filters, with JOINs
- Cost considerations: endpoint stays running vs BigQuery on-demand compute

**Existing context:** `03 - BigQuery ML/BQML Remote Model on Vertex AI Endpoint.ipynb` and `Framework Workflows/PyTorch/serving/bigquery-bqml-remote-model-vertex.ipynb` — use as reference but build fresh with Serving series conventions and the same sentiment model.

#### 2. AlloyDB AI Remote Model on Vertex AI Endpoint

**Status:** Not Started

**File:** `Remote Models/AlloyDB AI Remote Model on Vertex AI Endpoint.ipynb`

**What it covers:**
- Deploy the sentiment model to a Vertex AI Endpoint (or reuse from notebook 1)
- Create an AlloyDB cluster + primary instance (Autopilot recommended for demo)
- Enable the `google_ml_integration` database extension
- Create a connection to the Vertex AI endpoint
- Call predictions with `google_ml.predict()` from SQL
- Real-time, row-level predictions inside transactional workloads (e.g., scoring at INSERT time via trigger)
- Compare with BQML: AlloyDB is OLTP (row-level, low-latency) vs BigQuery is OLAP (batch analytics)
- Cleanup: delete AlloyDB cluster (important — AlloyDB charges continuously)

#### 3. Spanner ML Remote Model on Vertex AI Endpoint

**Status:** Not Started

**File:** `Remote Models/Spanner ML Remote Model on Vertex AI Endpoint.ipynb`

**What it covers:**
- Deploy the sentiment model to a Vertex AI Endpoint (or reuse from notebook 1)
- Create a Spanner instance + database
- Register the Vertex AI endpoint as a Spanner ML model (`CREATE MODEL ... REMOTE`)
- Call predictions with `ML.PREDICT()` from Spanner SQL
- Globally distributed ML predictions — Spanner's multi-region capability extends to ML calls
- Use case: global applications needing consistent, low-latency predictions alongside strongly consistent reads
- Compare all three database ML surfaces:

| Aspect | BigQuery | AlloyDB | Spanner |
|--------|----------|---------|---------|
| Database type | OLAP (analytics) | OLTP (PostgreSQL) | OLTP (globally distributed) |
| SQL function | `ML.PREDICT()` | `google_ml.predict()` | `ML.PREDICT()` |
| Best for | Batch scoring, analytics | Transactional scoring | Global transactional scoring |
| Latency profile | Seconds (query engine) | Milliseconds (row-level) | Milliseconds (global) |
| Scale model | On-demand compute | Always-on instance | Always-on instance |
| Cost driver | Bytes scanned | Instance size | Node count |

- Cleanup: delete Spanner instance (important — Spanner charges continuously)

---

### 4. Serving Models on GKE

**Status:** Not Started

**File:** `Serving Models on GKE.ipynb` (root level, parallel to Cloud Run notebook)

**Placement:** `MLOps/Serving/` — sits alongside `Serving Models on Cloud Run.ipynb`. Same container, different platform.

**What it covers:**
- Deploy the same FastAPI sentiment container to GKE Autopilot
- GKE cluster creation (Autopilot — no node pool management)
- Kubernetes manifests: Deployment, Service, HPA (horizontal pod autoscaler)
- Traffic splitting between model versions via Gateway API or multiple Deployments with weighted routing
- Authentication: workload identity, IAP, or direct service access
- Comparison table: GKE vs Cloud Run vs Vertex AI Endpoints (control, cost, scaling, ops burden)
- When to choose GKE: custom networking, GPU scheduling, multi-model pods, compliance requirements, team already on Kubernetes

**Existing context:** `Framework Workflows/PyTorch/serving/torchserve-gke.md` — markdown guide covering TorchServe on GKE. Use as architecture reference.

---

### 5. Vertex AI Endpoint — Model Cohosting

**Status:** Not Started

**File:** `Online/Vertex AI Endpoint - Model Cohosting.ipynb`

**Placement:** `MLOps/Serving/Online/` — cohosting is a Vertex AI Endpoint deployment strategy, fits naturally with the existing endpoint series.

**What it covers:**
- Deploy multiple models to a shared VM pool using `DeploymentResourcePool`
- Create a resource pool with specified machine type and replica count
- Deploy both sentiment models (DistilBERT + BERT) to the same pool
- Show resource utilization: models share GPU/CPU memory, efficient for low-traffic models
- Traffic management: each model gets its own endpoint, but shares backend VMs
- Compare: cohosting (shared VMs, cost savings, lower isolation) vs separate deployments (dedicated VMs, full isolation, higher cost)
- Scaling behavior: pool scales based on aggregate load across all cohosted models
- Limitations and when NOT to cohost (noisy neighbors, different SLAs, GPU memory contention)

---

### 6–10. Triton Inference Server Series

**Placement:** `MLOps/Serving/Triton/` — new subfolder with its own `readme.md`

Triton is a distinct serving paradigm (model repository, versioning, ensembles) that warrants its own series, similar to Online/ and Batch/. Five notebooks progress from fundamentals through production deployment on three platforms.

All notebooks use the same HuggingFace sentiment models for consistency with the rest of the Serving section, plus a simple preprocessing model to demonstrate ensembles.

#### 6. Triton Inference Server — Fundamentals

**Status:** Not Started

**File:** `Triton/Triton Inference Server - Fundamentals.ipynb`

**What it covers:**
- Model repository structure: `model_name/version/model.pt` convention
- `config.pbtxt`: input/output tensors, platform, instance groups, dynamic batching
- Launch Triton locally (Docker) with a single sentiment model
- Model versioning: add v2 (BERT) alongside v1 (DistilBERT), version policies (latest, specific, all)
- Multi-model serving: multiple independent models in one server, each with its own config
- Health checks, model readiness, server readiness
- Triton client library: `tritonclient.http` and `tritonclient.grpc`
- Performance: dynamic batching configuration, instance groups (CPU/GPU), model warmup

#### 7. Triton Inference Server — Pipelines and Ensembles

**Status:** Not Started

**File:** `Triton/Triton Inference Server - Pipelines and Ensembles.ipynb`

**What it covers:**
- **Ensemble models:** chain preprocessing → inference → postprocessing in `config.pbtxt`
  - Tokenizer model (Python backend) → Sentiment model (PyTorch backend) → Label mapper (Python backend)
  - Single client request triggers the full chain server-side
- **Business Logic Scripting (BLS):** Python backend models that orchestrate other models programmatically
  - Conditional routing: send input to different models based on text length or language
  - Fan-out: run both DistilBERT and BERT, return ensemble/comparison result
- Compare: ensemble scheduling (declarative, simpler) vs BLS (imperative, flexible)
- Performance implications: ensemble avoids network round-trips between stages

#### 8. Triton on Vertex AI Endpoints

**Status:** Not Started

**File:** `Triton/Triton on Vertex AI Endpoints.ipynb`

**What it covers:**
- Package Triton as a custom serving container for Vertex AI
- Container: `nvcr.io/nvidia/tritonserver` base + model repository baked in or loaded from GCS at startup
- Vertex AI integration: map Triton's HTTP API to `/predict` and `/health` routes (or use `rawPredict`)
- Deploy to Dedicated Public Endpoint with `rawPredict` (bypasses Vertex AI payload parsing, sends directly to Triton)
- Multi-model on one endpoint: all models in the Triton repo are accessible via the model name in the request
- GPU deployment: machine type with GPU, Triton auto-uses available GPUs
- Compare: Triton on Vertex AI (managed scaling + Triton features) vs plain FastAPI on Vertex AI (simpler, no Triton overhead)

#### 9. Triton on Cloud Run

**Status:** Not Started

**File:** `Triton/Triton on Cloud Run.ipynb`

**What it covers:**
- Deploy Triton container to Cloud Run (GPU support via Cloud Run GPU, L4)
- Container startup: download model repo from GCS at startup (Cloud Run has no persistent storage)
- Cold start considerations: Triton model loading time + model download time
- Min instances to avoid cold starts for latency-sensitive workloads
- Scale-to-zero cost savings vs startup latency tradeoff
- Concurrency settings: Triton handles concurrent requests internally, set Cloud Run concurrency accordingly
- Compare: Triton on Cloud Run (scale-to-zero, simpler ops) vs Triton on GKE (persistent, more control)

#### 10. Triton on GKE

**Status:** Not Started

**File:** `Triton/Triton on GKE.ipynb`

**What it covers:**
- Deploy Triton to GKE with GPU node pools
- Kubernetes manifests: Deployment with GPU resource requests, Service, Ingress
- Model repository options: baked into container, GCS FUSE sidecar, or PVC
- HPA: scale based on Triton metrics (queue depth, inference latency) via custom metrics adapter
- Multi-node Triton: independent replicas behind a Service (Triton is stateless per replica)
- Node auto-provisioning for GPU: GKE dynamically adds GPU nodes as Triton pods scale
- Production patterns: liveness/readiness probes using Triton health endpoints, graceful shutdown, rolling updates
- Compare all three Triton platforms:

| Aspect | Vertex AI | Cloud Run | GKE |
|--------|-----------|-----------|-----|
| Ops burden | Lowest | Low | Highest |
| GPU support | Yes (Vertex machine types) | Yes (L4 only) | Yes (any GPU) |
| Scale-to-zero | No | Yes | Yes (with Keda/custom) |
| Autoscaling metric | CPU/GPU utilization | Concurrency/CPU | Custom (queue depth) |
| Persistent model storage | GCS load at startup | GCS load at startup | PVC / GCS FUSE |
| Cost model | Per-replica-hour | Per-request + min instances | Per-node-hour |
| Best for | Managed ML platform teams | Event-driven / bursty traffic | Full control / multi-GPU |

---

### 11. Vertex AI Pre-built Serving Containers

**Status:** Not Started

**File:** `Vertex AI Pre-built Serving Containers.ipynb` (root level)

**Placement:** `MLOps/Serving/` — every existing notebook uses custom FastAPI containers. This shows the simpler path when you don't need custom serving logic.

**What it covers:**
- Upload a model to Model Registry with a pre-built container (no Dockerfile, no Cloud Build)
- Pre-built containers for: TensorFlow Serving, scikit-learn, XGBoost, PyTorch (TorchServe)
- Export the sentiment model to TorchScript or ONNX format for pre-built container compatibility
- Deploy to an endpoint — the container handles `/predict` and `/health` automatically
- Compare: pre-built (zero container work, opinionated I/O format) vs custom (full control, any framework, any I/O)
- When to use pre-built: standard model format, no custom pre/post processing needed, fastest path to deployment
- When to use custom: non-standard I/O, multiple models in one container, custom business logic, framework not supported

---

### 12. Serving Models With Cloud Functions

**Status:** Not Started

**File:** `Serving Models With Cloud Functions.ipynb` (root level)

**Placement:** `MLOps/Serving/` — completes the serverless spectrum: Cloud Functions (lightest) → Cloud Run (containers) → Vertex AI (managed ML)

**What it covers:**
- Deploy a lightweight sentiment model as a Cloud Function (2nd gen, Cloud Run–backed)
- Package model artifacts: bundle small model into the function deployment, or load from GCS at cold start
- Function code: load model on first invocation (global scope), serve predictions on subsequent calls
- Cold start analysis: model loading time on first request, warm invocation latency
- Min instances to eliminate cold starts for latency-sensitive use cases
- Concurrency: Cloud Functions 2nd gen supports concurrent requests per instance
- Size constraints: deployment package limit (source + dependencies), memory limit, timeout
- Compare the full serverless spectrum:

| Aspect | Cloud Functions | Cloud Run | Vertex AI Endpoint |
|--------|----------------|-----------|-------------------|
| Deployment unit | Function | Container | Container + Model Registry |
| Smallest model? | Best (no container overhead) | Good | Overhead for small models |
| Scale-to-zero | Yes | Yes | No |
| Max model size | ~few hundred MB (memory-bound) | Multi-GB | Multi-GB |
| GPU | No | Yes (L4) | Yes (many types) |
| Traffic splitting | No | Yes | Yes |
| Best for | Small models, prototypes, webhooks | Production containers | Production ML with monitoring |

---

### 13. LLM Serving With vLLM

**Status:** Not Started

**File:** `LLM Serving With vLLM.ipynb` (root level)

**Placement:** `MLOps/Serving/` — LLM serving is fundamentally different from classical ML serving (KV-cache, continuous batching, tensor parallelism). Warrants its own notebook rather than fitting into an existing series.

**What it covers:**
- Deploy an open LLM (Gemma 2B or 7B) with vLLM on Vertex AI Endpoints
- vLLM container: `vllm/vllm-openai` base image with model downloaded from GCS or HuggingFace at startup
- GPU deployment: A100 or L4, tensor parallelism across multiple GPUs for larger models
- OpenAI-compatible API: vLLM serves `/v1/completions` and `/v1/chat/completions` — standard interface
- Vertex AI integration: deploy vLLM container, use `rawPredict` to hit the OpenAI-compatible API
- Key vLLM concepts:
  - Continuous batching (vs static batching in classical serving)
  - PagedAttention / KV-cache management
  - Speculative decoding for faster generation
  - Streaming token generation via SSE
- Benchmarking: tokens/sec, time-to-first-token, concurrent request throughput
- Compare: vLLM (open models, full control, cost-efficient) vs Vertex AI Model Garden (one-click, managed) vs Gemini API (proprietary, highest capability)

---

## Proposed Tree After Completion

```
MLOps/Serving/
├── Online/                                                    (7 notebooks)
│   ├── Vertex AI Dedicated Public Endpoint.ipynb
│   ├── Vertex AI Shared Public Endpoint.ipynb
│   ├── Vertex AI Private Endpoint With PSC.ipynb
│   ├── Vertex AI PSC Endpoint - Pipeline Model Swap.ipynb
│   ├── Vertex AI Endpoint - Prediction Methods.ipynb
│   ├── Vertex AI Endpoint - Autoscaling.ipynb
│   └── Vertex AI Endpoint - Model Cohosting.ipynb             ← NEW
├── Batch/                                                     (4 notebooks)
│   ├── Vertex AI Batch Prediction.ipynb
│   ├── Batch Inference With Dataflow.ipynb
│   ├── Batch Inference With Dataproc.ipynb
│   └── Orchestrating Batch Inference With Airflow.ipynb
├── Remote Models/                                             ← NEW subfolder
│   ├── readme.md
│   ├── BQML Remote Model on Vertex AI Endpoint.ipynb           ← NEW
│   ├── AlloyDB AI Remote Model on Vertex AI Endpoint.ipynb     ← NEW
│   └── Spanner ML Remote Model on Vertex AI Endpoint.ipynb     ← NEW
├── Triton/                                                    ← NEW subfolder
│   ├── readme.md
│   ├── Triton Inference Server - Fundamentals.ipynb            ← NEW
│   ├── Triton Inference Server - Pipelines and Ensembles.ipynb ← NEW
│   ├── Triton on Vertex AI Endpoints.ipynb                     ← NEW
│   ├── Triton on Cloud Run.ipynb                               ← NEW
│   └── Triton on GKE.ipynb                                     ← NEW
├── Understanding Prediction IO With FastAPI.ipynb
├── Serving Models on Cloud Run.ipynb
├── Serving Models on GKE.ipynb                                 ← NEW
├── Serve TensorFlow SavedModel Format With BigQuery.ipynb
├── Vertex AI Pre-built Serving Containers.ipynb                ← NEW
├── Serving Models With Cloud Functions.ipynb                   ← NEW
├── LLM Serving With vLLM.ipynb                                 ← NEW
├── PLANS.md
├── pyproject.toml
└── readme.md
```

**Total new notebooks: 13** (3 Remote Models, 1 GKE, 1 Cohosting, 5 Triton, 1 Pre-built Containers, 1 Cloud Functions, 1 vLLM)

---

## Build Order

Suggested order based on dependencies and complexity:

1. **BQML Remote Model** — shortest notebook, reuses existing endpoint deployment, mostly SQL
2. **AlloyDB AI Remote Model** — same pattern as BQML, different database
3. **Spanner ML Remote Model** — completes the remote models series
4. **Model Cohosting** — short, self-contained, fills an obvious gap in Online/
5. **Pre-built Serving Containers** — short, no container build, good contrast to existing notebooks
6. **Cloud Functions** — lightweight, fast to build, completes the serverless spectrum
7. **Serving Models on GKE** — parallel to existing Cloud Run notebook, same container
8. **Triton Fundamentals** — foundation for the Triton series
9. **Triton Pipelines and Ensembles** — builds on fundamentals
10. **Triton on Vertex AI Endpoints** — combines Triton + Vertex AI knowledge
11. **Triton on Cloud Run** — combines Triton + Cloud Run knowledge
12. **Triton on GKE** — combines Triton + GKE knowledge (benefits from notebook 7)
13. **LLM Serving With vLLM** — most complex, GPU-heavy, benefits from all prior serving knowledge

---

## Shared Conventions

All new notebooks follow the established Serving series patterns:

- **Header:** GitHub/Colab/CE/Workbench links (same table format)
- **Setup:** Colab detection, installs with `uv`/`pip` fallback, API enablement, project params
- **Models:** Same DistilBERT + BERT sentiment models from GCS
- **EXPERIMENT variable:** Unique per notebook for resource naming
- **Cleanup:** Delete all created resources, empty end cell
- **Markdown-heavy:** Explanation cells between code cells, comparison tables, decision frameworks
- **Files:** Source files written with `%%writefile` to `files/{experiment}/`

## pyproject.toml Updates

New dependencies to add as notebooks are built:
- `tritonclient[all]` — Triton client library (Triton series)
- `google-cloud-container` — GKE cluster management (GKE notebooks)
- `kubernetes` — Kubernetes Python client (GKE notebooks)
- `google-cloud-alloydb` — AlloyDB admin client (Remote Models)
- `google-cloud-spanner` — Spanner client (Remote Models)
- `google-cloud-functions` — Cloud Functions admin client
- `vllm` — vLLM engine (LLM serving, GPU required)
