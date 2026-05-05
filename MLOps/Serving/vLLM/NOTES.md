# vLLM Notebook Testing — Session Notes

> Working notes for picking up notebook testing across sessions. Delete this file when all 6 notebooks pass Restart & Run All.

## Current Status

**All 6 notebooks are built, committed, and pushed.** Ready for testing but blocked on GPU/CUDA driver compatibility.

### What's Done

- [x] All 6 notebooks created and committed
- [x] `vLLM/readme.md` — full readme with GPU Requirement section, HuggingFace Authentication section, platform comparison table, notebook descriptions
- [x] `PLANS.md` — updated with vLLM test order checklist
- [x] `Serving/readme.md` — updated with vLLM section, notebook count 26 → 32
- [x] `Serving/pyproject.toml` — added `vllm`, `openai`, `huggingface_hub`, `Pillow`, `pydantic`, `ipywidgets`
- [x] `Triton/readme.md` — added cross-link to Triton with vLLM Backend notebook
- [x] GPU check cell in all 3 local notebooks (Fundamentals, Multimodal, Triton+vLLM) — fails fast with clear platform guidance
- [x] HF auth in all 6 notebooks — Secret Manager first (`HF_SECRET_NAME` param), falls back to `login()` widget
- [x] `HF_SECRET_NAME` defined in cell 3 (alongside `PROJECT_ID`) before auth cell — no ordering issues
- [x] Cloud notebooks (Vertex AI, Cloud Run, GKE) also set `os.environ['HF_TOKEN']` for container deployments

### What's NOT Done

- [ ] Test all 6 notebooks via Restart & Run All (blocked on CUDA driver)

## CUDA Driver Issue

The Cloud Workstation's NVIDIA driver (535.288.01) supports CUDA 12.2 max. Current vLLM (0.20.1) ships with PyTorch compiled for CUDA 13.0. `torch.cuda.is_available()` returns `False` due to this mismatch.

**Cannot fix from inside the workstation** — the driver is at the host/VM level.

**Resolution options:**
1. Update the Cloud Workstation configuration to use a newer base image with driver 550+ or 570+
2. Use Colab (free T4, current drivers)
3. Use Vertex AI Workbench (T4/L4, current drivers)
4. Use Colab Enterprise (runs in your GCP project)

**Downgrading vLLM/PyTorch won't work** — older vLLM versions don't support Python 3.13.

## Test Order

From `PLANS.md` — local notebooks first (fast iteration, no cloud cost), then cloud:

1. `vLLM - Fundamentals.ipynb` — local GPU, vLLM + Gemma 4 E2B, OpenAI API, LoRA, structured output, tool calling, speculative decoding
2. `vLLM Multimodal Serving.ipynb` — local GPU, Gemma 4 E4B, image+text via OpenAI vision API
3. `vLLM on Vertex AI Endpoints.ipynb` — pre-built container, rawPredict, Gemma 4 26B-A4B MoE on L4
4. `vLLM on Cloud Run.ipynb` — Dockerfile build, OIDC auth, scale-to-zero, single L4
5. `vLLM on GKE.ipynb` — Autopilot cluster, K8s manifests, LoadBalancer, HPA, Inference Gateway
6. `Triton with vLLM Backend.ipynb` — local Docker, Triton + vLLM backend, multi-model serving

## HuggingFace Authentication

All notebooks use this pattern:

```python
# Cell 3 (inputs, before auth):
PROJECT_ID = 'statmike-mlops-349915'
HF_SECRET_NAME = 'hugging-face-notebooks-read'  # optional — Secret Manager secret name

# Cell 8 or 9 (auth):
import os
try:
    from google.cloud import secretmanager
    client = secretmanager.SecretManagerServiceClient()
    name = f'projects/{PROJECT_ID}/secrets/{HF_SECRET_NAME}/versions/latest'
    token = client.access_secret_version(name=name).payload.data.decode('UTF-8')
    os.environ['HF_TOKEN'] = token
except Exception:
    from huggingface_hub import login
    login()
```

- Secret Manager method was tested and works (`hugging-face-notebooks-read` secret exists in `statmike-mlops-349915`)
- The `login()` widget was tested and works — shows ipywidgets form, caches token to `~/.cache/huggingface/token`
- HF token needs **Read access to contents of all public gated repos you can access** permission (fine-grained token type)
- User created a token named "notebooks" with this permission

## GPU Requirements by Notebook

| Notebook | Model | VRAM Needed | T4 (16 GB) | L4 (24 GB) |
|----------|-------|-------------|------------|------------|
| Fundamentals | gemma-4-E2B-it (2B) | ~4 GB | Yes | Yes |
| Multimodal | gemma-4-E4B-it (4B) | ~8 GB | Yes | Yes |
| Triton+vLLM | gemma-4-E2B-it (2B) | ~4 GB | Yes | Yes |
| Vertex AI | gemma-4-26B-A4B-it (MoE) | ~16 GB INT4 | N/A (cloud) | Yes (cloud) |
| Cloud Run | gemma-4-26B-A4B-it (MoE) | ~16 GB INT4 | N/A (cloud) | Yes (cloud) |
| GKE | gemma-4-26B-A4B-it (MoE) | ~16 GB INT4 | N/A (cloud) | Yes (cloud) |

## Notebook Cell Structure

All notebooks follow this order:
1. Header (pixel tracker + buttons)
2. Intro markdown
3. Colab Setup (`PROJECT_ID`, `HF_SECRET_NAME`)
4. Colab auth try/except
5. Environment (install helper)
6. HF Auth markdown
7. HF Auth code (Secret Manager → login() fallback)
8. Setup (inputs, packages, parameters)
9. GPU check (local notebooks only, right before server start)
10. Main content sections
11. Cleanup

## Key Commits

```
72c1d324 feat(serving): add GPU checks, Secret Manager auth, and HF login widget to vLLM notebooks
4b6ac18c docs(serving): add vLLM test order to PLANS.md
76975114 feat(serving): add vLLM LLM serving series with 6 Gemma 4 notebooks
```
