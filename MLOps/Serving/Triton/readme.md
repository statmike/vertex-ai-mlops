![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2FMLOps%2FServing%2FTriton&file=readme.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/MLOps/Serving/Triton/readme.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https://github.com/statmike/vertex-ai-mlops/blob/main/MLOps/Serving/Triton/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https://github.com/statmike/vertex-ai-mlops/blob/main/MLOps/Serving/Triton/readme.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https://github.com/statmike/vertex-ai-mlops/blob/main/MLOps/Serving/Triton/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https://github.com/statmike/vertex-ai-mlops/blob/main/MLOps/Serving/Triton/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
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
    <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/MLOps/Serving/Triton/readme.md"><img src="https://www.svgrepo.com/download/5445/download-button.svg" alt="Download icon" width="20px"></a> <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/MLOps/Serving/Triton/readme.md">Download File</a> <i>(right-click and "Save As")</i>
  </td>
</tr>
</table><br/><br/>

---
# Triton Inference Server

> You are here: `vertex-ai-mlops/MLOps/Serving/Triton/readme.md`

[NVIDIA Triton Inference Server](https://developer.nvidia.com/triton-inference-server) is an open-source serving platform designed for production ML inference. Unlike the custom FastAPI containers used in the rest of this Serving series, Triton provides a standardized model repository structure, built-in support for multiple ML frameworks, and production features like dynamic batching, model versioning, and ensemble pipelines — all without writing serving code.

These notebooks use the same HuggingFace sentiment models (DistilBERT v1, BERT v2) as the rest of the Serving section, so you can directly compare Triton's approach with the FastAPI-based patterns.

## Key Concepts

- **Model Repository** — A directory structure (`model_name/version/model_artifact`) that Triton scans at startup. Adding a model is as simple as placing files in the right directory.
- **config.pbtxt** — Per-model configuration defining inputs, outputs, backend, batching, instance groups, and version policy.
- **Multiple Backends** — Serve ONNX, TensorFlow, PyTorch, TensorRT, and Python models from the same server.
- **Dynamic Batching** — Triton accumulates individual requests into batches server-side, improving GPU utilization without client-side batching logic.
- **Ensemble Models** — Chain preprocessing, inference, and postprocessing into a single pipeline defined entirely in configuration.
- **KServe V2 Protocol** — Triton implements the [KServe V2 inference protocol](https://kserve.github.io/website/latest/modelserving/data_plane/v2_protocol/), a vendor-neutral REST/gRPC API for model serving.

## Notebooks

### 1. [Triton Inference Server — Fundamentals](./Triton%20Inference%20Server%20-%20Fundamentals.ipynb)

Build and run a Triton model repository locally with Docker. Covers both Python backend (wraps `transformers.pipeline`) and ONNX backend (exported via `torch.onnx.export()`).

**What you'll learn:**
- Model repository structure and `config.pbtxt` configuration
- Python backend: wrap any Python code as a Triton model
- ONNX export: convert HuggingFace models to ONNX format for high-performance inference
- HTTP and gRPC inference with `tritonclient`
- Model versioning and version policies
- Multi-model serving from a single server
- Dynamic batching and instance groups for throughput optimization

### 2. [Triton Inference Server — Pipelines and Ensembles](./Triton%20Inference%20Server%20-%20Pipelines%20and%20Ensembles.ipynb)

Chain tokenization, inference, and postprocessing into server-side pipelines — no client-side preprocessing needed.

**What you'll learn:**
- **Ensemble models (declarative):** Define a tokenizer → ONNX model → postprocessor pipeline in `config.pbtxt`
- **Business Logic Scripting (imperative):** Use Python backend with `pb_utils.InferenceRequest` for programmatic model orchestration and conditional routing
- When to use ensemble vs BLS: declarative DAGs vs imperative code
- Swapping inference backends without changing the pipeline
- Performance comparison: all-in-one Python vs ensemble vs BLS

### 3. [Triton on Vertex AI Endpoints](./Triton%20on%20Vertex%20AI%20Endpoints.ipynb)

Package Triton as a custom serving container and deploy to Vertex AI with `rawPredict`.

**What you'll learn:**
- Dockerfile based on the Triton container image
- Why `rawPredict` is required (Triton's V2 protocol differs from Vertex AI's `{"instances": [...]}`)
- Multi-model serving on a single endpoint via model name routing
- GPU deployment with L4 and optional TensorRT optimization
- Comparison: Triton on Vertex AI vs FastAPI on Vertex AI

### 4. [Triton on Cloud Run](./Triton%20on%20Cloud%20Run.ipynb)

Deploy Triton to Cloud Run with L4 GPU for serverless model serving.

**What you'll learn:**
- Cloud Run GPU deployment with `nvidia-l4` accelerator
- Cold start considerations: ~15 GB container + model loading
- Concurrency tuning: let Cloud Run feed Triton's internal dynamic batcher
- CPU-only deployment as a lower-cost alternative
- OIDC authentication for secure access

### 5. [Triton on GKE](./Triton%20on%20GKE.ipynb)

Deploy Triton to GKE Autopilot with full Kubernetes control over model serving infrastructure.

**What you'll learn:**
- Model repository strategies: baked-in container vs GCS FUSE volume mount
- GPU scheduling with L4 on GKE Autopilot
- HPA with Triton's Prometheus metrics (queue depth, inference latency)
- Production patterns: health probes, graceful shutdown, rolling updates
- Platform comparison: Vertex AI vs Cloud Run vs GKE for Triton

## Comparison

| Aspect | Fundamentals | Ensembles | Vertex AI | Cloud Run | GKE |
|--------|:---:|:---:|:---:|:---:|:---:|
| **Compute** | Local Docker | Local Docker | Vertex AI Endpoint | Cloud Run | GKE Autopilot |
| **GPU** | CPU-only | CPU-only | CPU + L4 exercise | L4 | L4 |
| **Backends** | Python + ONNX | Ensemble + BLS | ONNX | ONNX | ONNX |
| **Focus** | Core concepts | Pipelines | Managed deployment | Serverless | Full control |
| **Protocol** | HTTP + gRPC | HTTP | rawPredict (HTTP) | HTTP | HTTP |

## Container Image

All notebooks use `nvcr.io/nvidia/tritonserver:24.12-py3` — a recent stable release that includes Python backend, ONNX Runtime, and TensorRT support. The image works on both CPU and GPU. Note: the image is ~15 GB, so initial pulls and Cloud Build steps take several minutes.

## Files

Each notebook writes its source files to a per-notebook subdirectory:

```
Triton/
├── files/
│   ├── triton-fundamentals/      ← model_repository (Python backend, ONNX models, config.pbtxt)
│   ├── triton-ensembles/         ← model_repository (tokenizer, postprocessor, ensemble, BLS)
│   ├── triton-vertex-ai/         ← Dockerfile + model_repository for Cloud Build
│   ├── triton-cloud-run/         ← Dockerfile + model_repository for Cloud Build
│   └── triton-gke/               ← Dockerfile + model_repository for Cloud Build
```

## Related

- **[Triton with vLLM Backend](../vLLM/Triton%20with%20vLLM%20Backend.ipynb)** — Use vLLM as a Triton backend for LLM serving. Combines Triton's multi-model management with vLLM's LLM inference engine. Part of the [vLLM series](../vLLM/readme.md).

## Prerequisites

- A GCP project with billing enabled
- Docker installed locally (for Fundamentals and Ensembles notebooks)
- APIs enabled: Cloud Build, Artifact Registry, Vertex AI, Cloud Run, GKE (as needed)
- Python >= 3.10 with the packages listed in the parent [`pyproject.toml`](../pyproject.toml)
- Each notebook includes its own setup cells — no pre-configuration needed beyond a GCP project
