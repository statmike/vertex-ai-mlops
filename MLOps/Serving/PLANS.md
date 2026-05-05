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

### Triton Series (5 notebooks — all complete)

- [x] `Triton/Triton Inference Server - Fundamentals.ipynb` — CPU-only local Docker, Python + ONNX backends, HTTP/gRPC clients, dynamic batching
- [x] `Triton/Triton Inference Server - Pipelines and Ensembles.ipynb` — CPU-only local Docker, linear/fan-out ensembles, routing/cascade BLS, model swap
- [x] `Triton/Triton on Vertex AI Endpoints.ipynb` — L4 GPU, full ensemble pipeline, rawPredict, multi-model routing
- [x] `Triton/Triton on Cloud Run.ipynb` — CPU ONNX-direct, OIDC auth, concurrency, GPU exercise
- [x] `Triton/Triton on GKE.ipynb` — CPU ONNX-direct, GKE Autopilot, HPA, Prometheus metrics, GPU exercise

### Dataproc Series (4 notebooks — all complete)

- [x] `data+ai/dataproc/examples/dataproc-serverless-fundamentals.ipynb` — Runtimes, BQ connector, SDK submission, Spark properties, job lifecycle
- [x] `data+ai/dataproc/examples/dataproc-batch-inference.ipynb` — Pandas UDF vs mapPartitions, multi-model, performance tuning
- [x] `data+ai/dataproc/examples/dataproc-structured-streaming.ipynb` — Provisioned cluster, GCS file stream, foreachBatch, Pandas UDF
- [x] `data+ai/dataproc/examples/dataproc-vertex-ai-endpoint.ipynb` — Deploy endpoint, call from Spark, model-on-worker vs model-on-endpoint

### Dataflow Basics (1 notebook — complete)

- [x] `data+ai/dataflow/examples/dataflow-runinference-basics.ipynb` — ModelHandler, KeyedModelHandler, simple Pub/Sub streaming pipeline

### vLLM Series (6 notebooks — testing)

Test order: local notebooks first (fast iteration, no cloud cost), then cloud in order of complexity.

- [ ] `vLLM/vLLM - Fundamentals.ipynb` — local GPU, vLLM + Gemma 4 E2B, OpenAI API, LoRA, structured output, tool calling, speculative decoding
- [ ] `vLLM/vLLM Multimodal Serving.ipynb` — local GPU, Gemma 4 E4B, image+text via OpenAI vision API
- [ ] `vLLM/vLLM on Vertex AI Endpoints.ipynb` — pre-built container, rawPredict, Gemma 4 26B-A4B MoE on L4
- [ ] `vLLM/vLLM on Cloud Run.ipynb` — Dockerfile build, OIDC auth, scale-to-zero, single L4
- [ ] `vLLM/vLLM on GKE.ipynb` — Autopilot cluster, K8s manifests, LoadBalancer, HPA, Inference Gateway
- [ ] `vLLM/Triton with vLLM Backend.ipynb` — local Docker, Triton + vLLM backend, multi-model serving

**Remaining:** 6 vLLM notebooks to test.

---

## Remaining Notebooks

### 1. vLLM — LLM Serving (6 notebooks)

**Status:** Built, testing in progress

**Folder:** `vLLM/` (new subfolder, same structure as `Triton/`)

**What it covers:**
- vLLM serving engine for Gemma 4 models: PagedAttention, continuous batching, OpenAI-compatible API
- Advanced features: LoRA adapters, structured output, tool calling, speculative decoding
- Deploy to Vertex AI (pre-built container), Cloud Run (scale-to-zero), GKE (HPA, Inference Gateway)
- Multimodal inference: image + text with Gemma 4's native vision capabilities
- Triton + vLLM backend: bridge the Triton and vLLM series

**Notebooks:**
1. `vLLM - Fundamentals.ipynb` — Core concepts + advanced features (LoRA, structured output, tool calling, speculative decoding), local GPU, Gemma 4 E2B
2. `vLLM on Vertex AI Endpoints.ipynb` — Pre-built container, rawPredict/streamRawPredict, Gemma 4 26B-A4B MoE
3. `vLLM on Cloud Run.ipynb` — Single L4, scale-to-zero, SSE streaming, OIDC auth
4. `vLLM on GKE.ipynb` — Autopilot, HPA with vLLM metrics, Inference Gateway
5. `vLLM Multimodal Serving.ipynb` — Image+text inference with Gemma 4 E4B
6. `Triton with vLLM Backend.ipynb` — vLLM as Triton backend, bridges both series

**Test order** (local first for fast iteration, then cloud in order of complexity):
- [ ] `vLLM - Fundamentals.ipynb` — local GPU, validates vLLM + Gemma 4 basics; if this breaks, nothing else works
- [ ] `vLLM Multimodal Serving.ipynb` — local GPU, validates multimodal support before cloud deploys
- [ ] `vLLM on Vertex AI Endpoints.ipynb` — simplest cloud deploy (pre-built container, no Dockerfile)
- [ ] `vLLM on Cloud Run.ipynb` — adds Dockerfile build, OIDC auth, scale-to-zero
- [ ] `vLLM on GKE.ipynb` — most complex (cluster, K8s manifests, LoadBalancer routing)
- [ ] `Triton with vLLM Backend.ipynb` — last, depends on both Triton and vLLM understanding; local Docker

---

## Proposed Tree After Completion

```
MLOps/Serving/
├── Online/                                                    (7 notebooks)
├── Batch/                                                     (4 notebooks)
├── SQL Inference/                                             (5 notebooks)
├── Platforms/                                                 (4 notebooks)
├── Triton/                                                    (5 notebooks)
├── vLLM/                                                      (6 notebooks) ← NEW
│   ├── vLLM - Fundamentals.ipynb
│   ├── vLLM on Vertex AI Endpoints.ipynb
│   ├── vLLM on Cloud Run.ipynb
│   ├── vLLM on GKE.ipynb
│   ├── vLLM Multimodal Serving.ipynb
│   └── Triton with vLLM Backend.ipynb
├── Understanding Prediction IO With FastAPI.ipynb
├── PLANS.md, pyproject.toml, readme.md
```

**Total remaining: 6** (vLLM series)

---

## Build Order

1. **vLLM Scaffold** — `vLLM/readme.md`, `.gitignore`, update PLANS.md/pyproject.toml/Serving readme
2. **vLLM - Fundamentals** — Foundation, teaches all vLLM concepts locally
3. **vLLM on Vertex AI Endpoints** — Simplest deployment (pre-built container)
4. **vLLM on Cloud Run** — Adds OIDC, scale-to-zero
5. **vLLM on GKE** — Most complex (K8s, HPA, Inference Gateway)
6. **vLLM Multimodal Serving** — Independent, any GPU
7. **Triton with vLLM Backend** — Bridges series, must be last

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
- `openai` — OpenAI SDK for vLLM's compatible API
- `huggingface_hub` — HuggingFace model access (Gemma 4 is gated)
- `Pillow` — Image handling for multimodal inference
- `pydantic` — Structured output schema definitions
