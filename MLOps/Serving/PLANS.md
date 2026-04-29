# Serving — Expansion Plans

> Remaining notebooks to round out the Serving section. Each is self-contained and follows the established Serving series conventions (header, setup, Colab support, cleanup). Delete individual entries as notebooks are completed.

## Current State (21 notebooks complete)

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
├── Understanding Prediction IO With FastAPI.ipynb
├── PLANS.md, pyproject.toml, readme.md
```

---

## Remaining Notebooks

### 1–5. Triton Inference Server Series

**Placement:** `MLOps/Serving/Triton/` — new subfolder with its own `readme.md`

Triton is a distinct serving paradigm (model repository, versioning, ensembles) that warrants its own series. Five notebooks progress from fundamentals through production deployment on three platforms.

All notebooks use the same HuggingFace sentiment models for consistency with the rest of the Serving section.

#### 1. Triton Inference Server — Fundamentals

**Status:** Not Started

**File:** `Triton/Triton Inference Server - Fundamentals.ipynb`

**What it covers:**
- Model repository structure: `model_name/version/model.pt` convention
- `config.pbtxt`: input/output tensors, platform, instance groups, dynamic batching
- Launch Triton locally (Docker) with a single sentiment model
- Model versioning: add v2 alongside v1, version policies (latest, specific, all)
- Multi-model serving: multiple independent models in one server
- Triton client library: `tritonclient.http` and `tritonclient.grpc`
- Performance: dynamic batching, instance groups, model warmup

#### 2. Triton Inference Server — Pipelines and Ensembles

**Status:** Not Started

**File:** `Triton/Triton Inference Server - Pipelines and Ensembles.ipynb`

**What it covers:**
- **Ensemble models:** chain preprocessing → inference → postprocessing in `config.pbtxt`
- **Business Logic Scripting (BLS):** Python backend for programmatic model orchestration
- Compare: ensemble scheduling (declarative) vs BLS (imperative, flexible)
- Performance: ensemble avoids network round-trips between stages

#### 3. Triton on Vertex AI Endpoints

**Status:** Not Started

**File:** `Triton/Triton on Vertex AI Endpoints.ipynb`

**What it covers:**
- Package Triton as a custom serving container for Vertex AI
- Deploy with `rawPredict` (bypasses Vertex AI payload parsing)
- Multi-model on one endpoint via model name in request
- GPU deployment
- Compare: Triton on Vertex AI vs plain FastAPI on Vertex AI

#### 4. Triton on Cloud Run

**Status:** Not Started

**File:** `Triton/Triton on Cloud Run.ipynb`

**What it covers:**
- Deploy Triton container to Cloud Run with GPU (L4)
- Cold start: model loading + download time
- Min instances vs scale-to-zero tradeoff
- Concurrency settings for Triton's internal request handling
- Compare: Triton on Cloud Run vs Triton on GKE

#### 5. Triton on GKE

**Status:** Not Started

**File:** `Triton/Triton on GKE.ipynb`

**What it covers:**
- Deploy Triton to GKE with GPU node pools
- Model repository options: baked in, GCS FUSE, PVC
- HPA with Triton custom metrics (queue depth, inference latency)
- Production patterns: probes, graceful shutdown, rolling updates
- Compare all three Triton platforms (Vertex AI, Cloud Run, GKE)

---

### 6. LLM Serving With vLLM

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
├── Triton/                                                    ← NEW (5 notebooks)
│   ├── readme.md
│   ├── Triton Inference Server - Fundamentals.ipynb
│   ├── Triton Inference Server - Pipelines and Ensembles.ipynb
│   ├── Triton on Vertex AI Endpoints.ipynb
│   ├── Triton on Cloud Run.ipynb
│   └── Triton on GKE.ipynb
├── Understanding Prediction IO With FastAPI.ipynb
├── LLM Serving With vLLM.ipynb                                ← NEW
├── PLANS.md, pyproject.toml, readme.md
```

**Total remaining: 6** (5 Triton + 1 vLLM)

---

## Build Order

1. **Triton Fundamentals** — foundation for the Triton series
2. **Triton Pipelines and Ensembles** — builds on fundamentals
3. **Triton on Vertex AI Endpoints** — combines Triton + Vertex AI
4. **Triton on Cloud Run** — combines Triton + Cloud Run
5. **Triton on GKE** — combines Triton + GKE (benefits from Platforms/ notebooks)
6. **LLM Serving With vLLM** — most complex, GPU-heavy, benefits from all prior knowledge

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

---

## pyproject.toml Updates

New dependencies to add as notebooks are built:
- `tritonclient[all]` — Triton client library (Triton series)
- `vllm` — vLLM engine (LLM serving, GPU required)
