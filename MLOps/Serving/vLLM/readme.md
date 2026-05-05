![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2FMLOps%2FServing%2FvLLM&file=readme.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/MLOps/Serving/vLLM/readme.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https://github.com/statmike/vertex-ai-mlops/blob/main/MLOps/Serving/vLLM/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https://github.com/statmike/vertex-ai-mlops/blob/main/MLOps/Serving/vLLM/readme.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https://github.com/statmike/vertex-ai-mlops/blob/main/MLOps/Serving/vLLM/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https://github.com/statmike/vertex-ai-mlops/blob/main/MLOps/Serving/vLLM/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
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
    <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/MLOps/Serving/vLLM/readme.md"><img src="https://www.svgrepo.com/download/5445/download-button.svg" alt="Download icon" width="20px"></a> <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/MLOps/Serving/vLLM/readme.md">Download File</a> <i>(right-click and "Save As")</i>
  </td>
</tr>
</table><br/><br/>

---
# vLLM — LLM Serving

> You are here: `vertex-ai-mlops/MLOps/Serving/vLLM/readme.md`

[vLLM](https://docs.vllm.ai/) is a high-throughput, memory-efficient serving engine purpose-built for large language models. Unlike the custom FastAPI containers and NVIDIA Triton used in the rest of this Serving series for traditional ML/DL models, vLLM is designed specifically for autoregressive text generation — the core operation behind chatbots, code assistants, and agentic workflows. It provides an OpenAI-compatible API out of the box, so any application built for OpenAI can point at a vLLM endpoint with zero code changes.

These notebooks use [Gemma 4](https://ai.google.dev/gemma/docs/core) models from Google DeepMind — a family of open models available under the Apache 2.0 license. Gemma 4 models are natively multimodal (text, image, video, audio) and range from 2B to 31B parameters, making them ideal for demonstrating vLLM across different GPU configurations.

## Key Concepts

- **PagedAttention** — Memory-efficient KV cache management inspired by OS virtual memory paging. Eliminates memory waste from pre-allocated, fixed-size buffers by storing attention keys/values in non-contiguous memory pages.
- **Continuous Batching** — Dynamically adds and removes requests from running batches as they complete, rather than waiting for an entire batch to finish (static batching). Dramatically improves GPU utilization and throughput.
- **OpenAI-Compatible API** — vLLM exposes `/v1/chat/completions`, `/v1/completions`, and `/v1/models` endpoints that are drop-in replacements for the OpenAI API. Use the standard `openai` Python SDK.
- **KV Cache** — Cached key-value attention states from previously processed tokens. The KV cache size determines how many concurrent requests and how much context a server can handle — it's the primary memory constraint after model weights.
- **Quantization** — Reduce model memory footprint with INT4/INT8/FP8 precision (GPTQ, AWQ, bitsandbytes). A 26B parameter model that needs ~52 GB at BF16 fits in ~16 GB at INT4.
- **LoRA Adapters** — Serve multiple fine-tuned model variants from a single set of base weights. vLLM loads LoRA adapters dynamically, sharing the base model's memory across all adapters.
- **Structured Output** — Constrained generation that guarantees valid JSON, JSON Schema compliance, or regex-matched output. Uses guided decoding to restrict token sampling at each step.
- **Speculative Decoding** — Accelerate generation by using a small, fast draft model to propose tokens that the larger target model then verifies in parallel. Can provide 2-3x speedup with no quality loss.

## Gemma 4 Models

All Gemma 4 models are [available on Hugging Face](https://huggingface.co/collections/google/gemma-4-release-680f5e77305ea7f903056ff8) under the Apache 2.0 license. The `-it` suffix denotes instruction-tuned variants.

| Model | Type | Total Params | Active Params | Context | L4 (24 GB) | A100 (80 GB) |
|-------|------|:---:|:---:|:---:|:---:|:---:|
| `gemma-4-E2B-it` | Dense | 2B | 2B | 128K | BF16 fits (~4 GB) | BF16 fits |
| `gemma-4-E4B-it` | Dense | 4B | 4B | 128K | BF16 fits (~8 GB) | BF16 fits |
| `gemma-4-26B-A4B-it` | MoE (128 experts, top-8) | 26B | 3.8B | 256K | INT4 fits (~16 GB) | BF16 fits |
| `gemma-4-31B-it` | Dense | 31B | 31B | 256K | Does not fit | INT4 fits (~18 GB) |

The **26B-A4B MoE** is the production sweet spot — it uses Mixture of Experts to activate only 3.8B parameters per token (out of 26B total), delivering near-31B quality at a fraction of the compute. At INT4 quantization it fits on a single L4 GPU with room for KV cache.

## Notebooks

### 1. [vLLM — Fundamentals](./vLLM%20-%20Fundamentals.ipynb)

Comprehensive introduction to vLLM as a serving engine — core concepts and all advanced features in a single notebook. After this, the remaining notebooks are purely about deploying what you've learned.

**What you'll learn:**
- Start a vLLM server and interact via the OpenAI-compatible API
- Streaming responses and measuring time-to-first-token
- Sampling parameters: temperature, top_p, top_k, max_tokens
- Continuous batching in action: concurrent request throughput
- LoRA adapter hot-swap: serve multiple fine-tuned models from one base
- Structured output: JSON mode, JSON schema enforcement, guided decoding
- Tool calling: function calling with vLLM's tool-use support
- Speculative decoding: draft + target model acceleration
- Benchmarking: tokens/sec, TTFT, throughput under concurrency

### 2. [vLLM on Vertex AI Endpoints](./vLLM%20on%20Vertex%20AI%20Endpoints.ipynb)

Deploy vLLM to Vertex AI using Google's pre-built optimized container — the simplest path to production LLM serving on GCP. No Dockerfile needed.

**What you'll learn:**
- Google's pre-built vLLM container: optimized fork with parallel model downloading and LoRA support
- Upload and deploy Gemma 4 26B-A4B to a Vertex AI Endpoint with L4 GPU
- `rawPredict` and `streamRawPredict`: why they're required for OpenAI-format requests
- Configure the OpenAI SDK to point at your Vertex AI endpoint
- Comparison: pre-built container vs custom Dockerfile vs Model Garden one-click

### 3. [vLLM on Cloud Run](./vLLM%20on%20Cloud%20Run.ipynb)

Deploy vLLM to Cloud Run with L4 GPU for serverless LLM serving that scales to zero when idle.

**What you'll learn:**
- Cloud Run GPU deployment with `nvidia-l4` accelerator
- Cold start analysis: vLLM + model loading time, strategies to minimize
- OIDC authentication for secure access
- SSE streaming: native Cloud Run streaming support
- Scale-to-zero: cost implications and warm-up strategies
- Concurrency tuning: Cloud Run `max_instance_request_concurrency` vs vLLM `--max-num-seqs`

### 4. [vLLM on GKE](./vLLM%20on%20GKE.ipynb)

Deploy vLLM to GKE Autopilot with full Kubernetes control — the most capable platform for LLM serving.

**What you'll learn:**
- Kubernetes Deployment with GPU resource requests and HuggingFace token secrets
- HPA with vLLM's Prometheus metrics: `vllm:num_requests_running`, `vllm:gpu_cache_usage_perc`
- GKE Inference Gateway: intelligent request routing for LLM workloads
- Multi-GPU with `--tensor-parallel-size` for larger models
- vLLM Prometheus metrics dashboard: key metrics to monitor in production
- Platform comparison: Vertex AI vs Cloud Run vs GKE for vLLM

### 5. [vLLM Multimodal Serving](./vLLM%20Multimodal%20Serving.ipynb)

Serve Gemma 4's native multimodal capabilities — image + text inference with vLLM. Demonstrates vision use cases that text-only notebooks can't cover.

**What you'll learn:**
- Gemma 4 multimodal capabilities: which models support which modalities
- Image + text inference via the OpenAI vision API
- Use cases: image captioning, visual Q&A, document understanding, chart reading
- Structured output from images: extract JSON from visual content
- Performance considerations: image resolution, token count per image, VRAM impact

### 6. [Triton with vLLM Backend](./Triton%20with%20vLLM%20Backend.ipynb)

Bridge the Triton and vLLM series — use vLLM as a Triton backend to get Triton's multi-model management and KServe V2 protocol with vLLM's LLM inference engine underneath.

**What you'll learn:**
- When to use Triton + vLLM vs standalone vLLM: decision framework
- Triton's vLLM backend: how it wraps vLLM's AsyncEngine
- Model repository setup: `config.pbtxt` for the vLLM backend
- Multi-model serving: traditional ONNX model + LLM from the same Triton instance
- Inference via both `tritonclient` (KServe V2) and OpenAI SDK

## Notebook Comparison

| Aspect | Fundamentals | Vertex AI | Cloud Run | GKE | Multimodal | Triton+vLLM |
|--------|:---:|:---:|:---:|:---:|:---:|:---:|
| **Compute** | Local/Colab GPU | Vertex AI Endpoint | Cloud Run | GKE Autopilot | Local/Colab GPU | Local/Colab GPU |
| **GPU** | T4/L4 | L4 | L4 | L4 | T4/L4 | T4/L4 |
| **Model** | E2B (2B) | 26B-A4B MoE | 26B-A4B MoE | 26B-A4B MoE | E4B (4B) | E2B (2B) |
| **Focus** | Core + advanced | Managed deployment | Serverless | Full control | Vision inference | Triton integration |
| **API** | OpenAI SDK | rawPredict | OpenAI SDK | OpenAI SDK | OpenAI SDK | Triton HTTP |

## Platform Comparison

When choosing where to deploy vLLM on Google Cloud:

| | **Vertex AI** | **Cloud Run** | **GKE** |
|---|---|---|---|
| **Status** | GA | GA (GPU since Jun 2025) | GA |
| **GPU options** | L4, A100, H100, TPU | L4 (single GPU, 24 GB) | L4, A100, H100, multi-GPU |
| **Google support** | Pre-built optimized vLLM container | Official Gemma tutorials | Helm charts, Inference Gateway |
| **Key feature** | `rawPredict` with OpenAI API | Scale-to-zero, SSE streaming | HPA with vLLM metrics |
| **Multi-GPU** | Yes | No | Yes, including multi-node |
| **Best for** | Managed endpoint, existing Vertex AI workflow | Cost-sensitive, bursty traffic | Full control, high throughput |

**Vertex AI** is the easiest path — Google maintains an optimized vLLM fork with parallel model downloading, LoRA support, and Vertex AI format handling.

**Cloud Run** is the simplest for single-model serving with scale-to-zero, but limited to one L4 GPU (24 GB VRAM).

**GKE** has the deepest support — full monitoring dashboards, HPA with vLLM-specific metrics, and Inference Gateway for intelligent request routing across model replicas.

## Container Images

**Google's pre-built vLLM container** (used in the Vertex AI notebook) is a customized vLLM fork optimized for Google Cloud. It includes parallel model downloading from GCS, LoRA adapter support, and Vertex AI format handling. Find the latest image URI in the [Vertex AI Model Garden documentation](https://cloud.google.com/vertex-ai/docs/open-models/use-vllm).

**Official vLLM container** (`vllm/vllm-openai`) from Docker Hub works on Cloud Run and GKE. For GKE, you can also use the NVIDIA GPU Operator-compatible images.

**Custom containers** — build your own when you need additional Python packages, custom model loading logic, or specific vLLM version pinning.

## Files

Each notebook writes its source files to a per-notebook subdirectory:

```
vLLM/
├── files/
│   ├── vllm-fundamentals/       ← scripts for local server management
│   ├── vllm-vertex-ai/          ← Dockerfile for custom container option
│   ├── vllm-cloud-run/          ← Dockerfile + deploy config
│   ├── vllm-gke/                ← Kubernetes manifests (Deployment, Service, HPA)
│   ├── vllm-multimodal/         ← test images + scripts
│   └── vllm-triton/             ← Triton config.pbtxt + Dockerfile
```

## Prerequisites

- A GCP project with billing enabled
- GPU access (T4 for local notebooks, L4 for deployment notebooks)
- A [Hugging Face account](https://huggingface.co/join) with an access token — Gemma 4 models require accepting the [license agreement](https://huggingface.co/google/gemma-4-E2B-it)
- APIs enabled: Vertex AI, Cloud Run, GKE, Cloud Build, Artifact Registry (as needed per notebook)
- Python >= 3.10 with the packages listed in the parent [`pyproject.toml`](../pyproject.toml)
- Each notebook includes its own setup cells — no pre-configuration needed beyond a GCP project and HuggingFace token
