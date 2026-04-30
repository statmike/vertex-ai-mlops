# Serving — Expansion Plans

> Remaining notebooks to round out the Serving section. Each is self-contained and follows the established Serving series conventions (header, setup, Colab support, cleanup). Delete individual entries as notebooks are completed.

## Current State (26 notebooks complete)

```
MLOps/Serving/
├── Online/                          (7 notebooks)
│   ├── Vertex AI Dedicated Public Endpoint.ipynb
│   ├── Vertex AI Shared Public Endpoint.ipynb
│   ├── Vertex AI Private Endpoint With PSC.ipynb
│   ├── Vertex AI PSC Endpoint - Pipeline Model Swap.ipynb
│   ├── Vertex AI Endpoint - Prediction Methods.ipynb
│   ├── Vertex AI Endpoint - Autoscaling.ipynb
│   └── Vertex AI Endpoint - Model Cohosting.ipynb
├── Batch/                           (4 notebooks)
│   ├── Vertex AI Batch Prediction.ipynb
│   ├── Batch Inference With Dataflow.ipynb
│   ├── Batch Inference With Dataproc.ipynb
│   └── Orchestrating Batch Inference With Airflow.ipynb
├── SQL Inference/                   (5 notebooks)
│   ├── BQML Remote Model on Vertex AI Endpoint.ipynb
│   ├── AlloyDB AI Remote Model on Vertex AI Endpoint.ipynb
│   ├── Spanner ML Remote Model on Vertex AI Endpoint.ipynb
│   ├── BQML Import Model via ONNX.ipynb
│   └── Serve TensorFlow SavedModel Format With BigQuery.ipynb
├── Platforms/                       (4 notebooks)
│   ├── Serving Models on Cloud Run.ipynb
│   ├── Serving Models on GKE.ipynb
│   ├── Serving Models With Cloud Functions.ipynb
│   └── Vertex AI Pre-built Serving Containers.ipynb
├── Triton/                          (5 notebooks)
│   ├── Triton Inference Server - Fundamentals.ipynb
│   ├── Triton Inference Server - Pipelines and Ensembles.ipynb
│   ├── Triton on Vertex AI Endpoints.ipynb
│   ├── Triton on Cloud Run.ipynb
│   └── Triton on GKE.ipynb
├── Understanding Prediction IO With FastAPI.ipynb
├── PLANS.md, pyproject.toml, readme.md
```

---

## Run and Revise

Notebooks that need a full test run (execute all cells, fix issues, verify outputs). Mark each as done after a clean run.

### Triton Series (5 notebooks — code-reviewed, not yet run)

- [ ] `Triton/Triton Inference Server - Fundamentals.ipynb` — CPU-only local Docker, Python + ONNX backends, HTTP/gRPC clients, dynamic batching
- [ ] `Triton/Triton Inference Server - Pipelines and Ensembles.ipynb` — CPU-only local Docker, ensembles, BLS, model swap
- [ ] `Triton/Triton on Vertex AI Endpoints.ipynb` — GCP deploy, rawPredict, multi-model, GPU exercise
- [ ] `Triton/Triton on Cloud Run.ipynb` — Cloud Run with L4 GPU, OIDC auth, concurrency
- [ ] `Triton/Triton on GKE.ipynb` — GKE Autopilot with L4 GPU, GCS FUSE, HPA, production probes

### Dataproc Series (4 notebooks — newly created, not yet run)

- [ ] `data+ai/dataproc/examples/dataproc-serverless-fundamentals.ipynb` — Runtimes, BQ connector, SDK submission, Spark properties, job lifecycle
- [ ] `data+ai/dataproc/examples/dataproc-batch-inference.ipynb` — Pandas UDF vs mapPartitions, multi-model, performance tuning
- [ ] `data+ai/dataproc/examples/dataproc-structured-streaming.ipynb` — Provisioned cluster, GCS file stream, foreachBatch, Pandas UDF
- [ ] `data+ai/dataproc/examples/dataproc-vertex-ai-endpoint.ipynb` — Deploy endpoint, call from Spark, model-on-worker vs model-on-endpoint

### Dataflow Basics (1 notebook — newly created, not yet run)

- [ ] `data+ai/dataflow/examples/dataflow-runinference-basics.ipynb` — ModelHandler, KeyedModelHandler, simple Pub/Sub streaming pipeline

**Run order:** Triton 1-2 first (CPU-only, fast iteration), then Triton 3-5 (GCP deploys), then Dataproc 1-4, then Dataflow basics.

---

## Remaining Notebooks

### 1. LLM Serving With vLLM

**Status:** Not Started

**File:** `LLM Serving With vLLM.ipynb` (root level)

**What it covers:**
- Deploy an open LLM (Gemma 2B or 7B) with vLLM on Vertex AI Endpoints
- OpenAI-compatible API via `rawPredict`
- Key vLLM concepts: continuous batching, PagedAttention, speculative decoding, streaming
- Benchmarking: tokens/sec, time-to-first-token, concurrent throughput
- Compare: vLLM vs Model Garden vs Gemini API

---

## Proposed Tree After Completion

```
MLOps/Serving/
├── Online/                                                    (7 notebooks)
├── Batch/                                                     (4 notebooks)
├── SQL Inference/                                             (5 notebooks)
├── Platforms/                                                 (4 notebooks)
├── Triton/                                                    (5 notebooks)
├── Understanding Prediction IO With FastAPI.ipynb
├── LLM Serving With vLLM.ipynb                                ← NEW
├── PLANS.md, pyproject.toml, readme.md
```

**Total remaining: 1** (vLLM)

---

## Build Order

1. **LLM Serving With vLLM** — GPU-heavy, benefits from all prior Serving knowledge

---

## Completed Notebooks (for reference)

| # | Notebook | Location | Completed |
|---|----------|----------|-----------|
| 1 | BQML Remote Model on Vertex AI Endpoint | SQL Inference/ | Yes |
| 2 | AlloyDB AI Remote Model on Vertex AI Endpoint | SQL Inference/ | Yes |
| 3 | Spanner ML Remote Model on Vertex AI Endpoint | SQL Inference/ | Yes |
| 4 | Serving Models on GKE | Platforms/ | Yes |
| 5 | Vertex AI Endpoint - Model Cohosting | Online/ | Yes |
| 6 | Vertex AI Pre-built Serving Containers | Platforms/ | Yes |
| 7 | Serving Models With Cloud Functions | Platforms/ | Yes |
| 8 | BQML Import Model via ONNX | SQL Inference/ | Yes |
| 9 | Triton Inference Server — Fundamentals | Triton/ | Yes |
| 10 | Triton Inference Server — Pipelines and Ensembles | Triton/ | Yes |
| 11 | Triton on Vertex AI Endpoints | Triton/ | Yes |
| 12 | Triton on Cloud Run | Triton/ | Yes |
| 13 | Triton on GKE | Triton/ | Yes |

---

## pyproject.toml Updates

New dependencies to add as notebooks are built:
- ~~`tritonclient[all]` — Triton client library (Triton series)~~ ✓ Added
- `vllm` — vLLM engine (LLM serving, GPU required)
