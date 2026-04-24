---
# Online Prediction

> You are here: `vertex-ai-mlops/MLOps/Serving/Online/readme.md`

This series covers deploying models for real-time, low-latency prediction on Vertex AI Endpoints. While the [parent Serving section](../readme.md) provides conceptual overviews and the endpoint type comparison table, these notebooks walk through each endpoint type end-to-end — from container build through deployment, traffic management, and cleanup.

All notebooks use the same two pre-trained HuggingFace sentiment models served via a custom FastAPI container built with Cloud Build. The different label formats (`POSITIVE`/`NEGATIVE` vs `LABEL_0`/`LABEL_1`) confirm which model is serving — the same teaching device used across the [Batch Inference](../Batch/readme.md) series.

## Notebooks

### 1. [Vertex AI Dedicated Public Endpoint](./Vertex%20AI%20Dedicated%20Public%20Endpoint.ipynb)

The recommended default. Public internet access with a dedicated networking plane — production isolation, 10 MB payloads, up to 1-hour timeout, unlimited QPM, gRPC and SSE streaming.

**What you'll learn:**
- Build a custom FastAPI container for HuggingFace sentiment models with Cloud Build
- Create a dedicated public endpoint (`dedicated_endpoint_enabled=True`) and deploy two model versions
- Shift traffic between models, validate predictions, and undeploy cleanly

### 2. [Vertex AI Shared Public Endpoint](./Vertex%20AI%20Shared%20Public%20Endpoint.ipynb)

The simplest setup, with trade-offs. Shared networking plane means lower limits: 1.5 MB payload, 60-second timeout, 30K QPM, HTTP only. The only endpoint type supporting tuned Gemini deployment and AutoML with explainability.

**What you'll learn:**
- Same container build and deployment pattern as Dedicated Public
- Understand shared endpoint limitations through direct comparison
- Traffic splitting between model versions on a shared endpoint

### 3. [Vertex AI Private Endpoint With PSC](./Vertex%20AI%20Private%20Endpoint%20With%20PSC.ipynb)

The recommended private access path. Traffic stays on private networks via [Private Service Connect](https://cloud.google.com/vpc/docs/private-service-connect) — same capabilities as dedicated public but with private networking.

**What you'll learn:**
- Create a PSC-enabled private endpoint and deploy the first model
- Set up PSC networking: reserve an internal IP, create a forwarding rule pointing to the service attachment
- Swap models and verify the private IP and connection remain uninterrupted
- Self-contained demo with a GCE VM test client for sending requests to the private IP

### 4. [Vertex AI PSC Endpoint - Pipeline Model Swap](./Vertex%20AI%20PSC%20Endpoint%20-%20Pipeline%20Model%20Swap.ipynb)

Automate model rollout on a PSC endpoint using Vertex AI Pipelines. Builds on the manual PSC workflow from Notebook 3.

**What you'll learn:**
- Kubeflow Pipeline with components for: verify endpoint, deploy at 0% traffic, shift traffic, verify health, undeploy old models, and notify
- KFP artifacts (`dsl.Artifact`, `dsl.Model`) for lineage and model registry version tracking
- `dsl.ExitHandler` for notification, `dsl.If`/`dsl.Else` for conditional rollback on verification failure
- Independent prediction testing through the PSC private IP from a GCE VM

### 5. [Vertex AI Endpoint - Prediction Methods](./Vertex%20AI%20Endpoint%20-%20Prediction%20Methods.ipynb)

Comprehensive multi-language reference for every way to request predictions from a Vertex AI Endpoint.

**What you'll learn:**
- Python SDK: `predict()`, `raw_predict()`, `predict_async()`, `stream_raw_predict()`
- Python gapic: `PredictionServiceClient` and `PredictionServiceAsyncClient`
- Dedicated endpoint direct URL via `dedicated_endpoint_dns`
- REST API in Python (`requests`, `httpx` async), `curl`, Node.js, Java, and Go
- gRPC transport, streaming (SSE), sync vs async benchmarks
- Endpoint type compatibility chart: which methods work with which endpoint types

### 6. [Vertex AI Endpoint - Autoscaling](./Vertex%20AI%20Endpoint%20-%20Autoscaling.ipynb)

Understand and observe autoscaling behavior through load testing and live metric visualization.

**What you'll learn:**
- Deploy with configurable autoscaling: min/max replicas, CPU target
- Cloud Monitoring metrics: discover metrics, build a reusable query helper with sparse metric handling
- Three experiments: CPU-triggered scaling, request-count scaling, threshold tuning
- 4-panel matplotlib dashboard: replicas, CPU utilization, predictions/sec, P95 latency
- Reconfigure autoscaling at runtime with `mutateDeployedModel` (no redeploy)
- Configuration reference: all parameters, cost implications, gotchas

## Endpoint Type Comparison

See the [parent readme](../readme.md#vertex-ai-endpoint-types) for the full comparison table and decision tree covering all four endpoint types (Dedicated Public, Shared Public, Dedicated Private via PSC, Private via VPC Peering).

## Files

Each notebook writes its container source to a per-endpoint subdirectory:

```
Online/
├── files/
│   ├── dedicated-public-endpoint/    ← Container source
│   ├── shared-public-endpoint/
│   ├── psc-private-endpoint/
│   ├── psc-pipeline-model-swap/      ← Container source + compiled KFP pipeline
│   ├── prediction-methods/
│   └── autoscaling/
```

## Prerequisites

- A GCP project with billing enabled
- APIs enabled: Vertex AI, Cloud Build, Artifact Registry, Compute Engine (for PSC notebooks)
- Python >= 3.10 with the packages listed in the parent [`pyproject.toml`](../pyproject.toml)
- Each notebook includes its own setup cells — no pre-configuration needed beyond a GCP project
