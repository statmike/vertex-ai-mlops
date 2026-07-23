![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2FMLOps%2FServing%2FPlatforms&file=readme.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/MLOps/Serving/Platforms/readme.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https://github.com/statmike/vertex-ai-mlops/blob/main/MLOps/Serving/Platforms/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https://github.com/statmike/vertex-ai-mlops/blob/main/MLOps/Serving/Platforms/readme.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https://github.com/statmike/vertex-ai-mlops/blob/main/MLOps/Serving/Platforms/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https://github.com/statmike/vertex-ai-mlops/blob/main/MLOps/Serving/Platforms/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
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
    <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/MLOps/Serving/Platforms/readme.md"><img src="https://www.svgrepo.com/download/5445/download-button.svg" alt="Download icon" width="20px"></a> <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/MLOps/Serving/Platforms/readme.md">Download File</a> <i>(right-click and "Save As")</i>
  </td>
</tr>
</table><br/><br/>

---
# Serving Platforms

> You are here: `vertex-ai-mlops/MLOps/Serving/Platforms/readme.md`

Beyond Vertex AI Endpoints, the same custom prediction container can be deployed to other GCP platforms. These notebooks demonstrate container portability — the same Docker image runs on Vertex AI, Cloud Run, GKE, and Cloud Functions without code changes, thanks to the `AIP_*` environment variable convention.

## Notebooks

### 1. [Serving Models on Cloud Run](./Serving%20Models%20on%20Cloud%20Run.ipynb)

Deploy the same FastAPI container to Cloud Run — same Docker image, same model, different platform.

**What you'll learn:**
- Container portability via explicit `AIP_*` environment variables
- Authentication deep dive: Cloud Run OIDC ID tokens vs Vertex AI access tokens
- Traffic splitting between revisions: v1 (DistilBERT) → v2 (BERT) → 50/50 split → full cutover
- Decision framework: when to choose Cloud Run vs Vertex AI Endpoints

### 2. [Serving Models on GKE](./Serving%20Models%20on%20GKE.ipynb)

Deploy the same container to GKE Autopilot with full Kubernetes control.

**What you'll learn:**
- GKE Autopilot cluster creation — no node management, pay-per-pod
- Kubernetes Deployment, Service, and Horizontal Pod Autoscaler (HPA)
- Workload Identity: bind Kubernetes SA to GCP SA for secure GCS access
- Traffic splitting between model versions via Service selector labels
- NLB source-IP affinity behavior and its impact on traffic distribution

### 3. [Serving Models With Cloud Functions](./Serving%20Models%20With%20Cloud%20Functions.ipynb)

The lightest serverless option — deploy a model as a Cloud Function with no container.

**What you'll learn:**
- Source deploy: model artifacts + function code, no Dockerfile needed
- Cold start: model loading on first invocation, warm instance reuse
- Min instances to eliminate cold starts for latency-sensitive use cases
- Decision framework: Cloud Functions vs Cloud Run vs Vertex AI Endpoints

### 4. [Vertex AI Pre-built Serving Containers](./Vertex%20AI%20Pre-built%20Serving%20Containers.ipynb)

Skip the container build entirely — use Vertex AI's pre-built serving containers.

**What you'll learn:**
- Upload a model to Model Registry with a pre-built container (TorchServe, TF Serving, etc.)
- No Dockerfile, no Cloud Build — simplest path to a Vertex AI Endpoint
- Export models to compatible formats (TorchScript, SavedModel, MAR)
- When to use pre-built vs custom containers

## Platform Comparison

| Aspect | Cloud Run | GKE Autopilot | Cloud Functions | Pre-built Container |
|--------|-----------|---------------|-----------------|-------------------|
| Deployment unit | Container | Container + K8s manifests | Source code | Model + pre-built container |
| Container build? | Yes | Yes | No | No |
| Scale-to-zero | Yes | Yes (with config) | Yes | No |
| GPU support | Yes (L4) | Yes (any GPU) | No | Yes (Vertex AI types) |
| Traffic splitting | Revision-based | Service selector | No | Vertex AI native |
| Autoscaling | Concurrency/CPU | HPA (CPU/custom) | Concurrent requests | Vertex AI native |
| Auth model | OIDC ID tokens | K8s RBAC + IAM | OIDC ID tokens | Vertex AI access tokens |
| Ops burden | Low | Medium | Lowest | Lowest |
| Best for | Production containers, scale-to-zero | Full K8s control, GPU scheduling | Small models, prototypes | Standard models, no custom logic |

## Files

Each notebook writes its source files to a per-platform subdirectory:

```
Platforms/
├── files/
│   ├── cloud-run/          ← Container source (Dockerfile, FastAPI app)
│   ├── gke-serving/        ← Container source (same pattern)
│   ├── cloud-functions/    ← Function source code
│   └── prebuilt-containers/ ← Model export scripts, MAR packaging
```

## Prerequisites

- A GCP project with billing enabled
- APIs enabled: Cloud Build, Artifact Registry, Cloud Run, GKE, Cloud Functions (as needed)
- Python >= 3.10 with the packages listed in the parent [`pyproject.toml`](../pyproject.toml)
- Each notebook includes its own setup cells — no pre-configuration needed beyond a GCP project

## Related: BQML mechanics in isolation

For the `EXPORT MODEL` mechanics feeding into this pre-built-container pattern — training a model in BigQuery ML, exporting it, and proving it loads/predicts entirely outside BigQuery before ever touching Vertex AI — see the sibling `bq-ml` project:
- [`data+ai/bq-ml/models/export/`](../../../data+ai/bq-ml/models/export/) — `EXPORT MODEL` to TensorFlow SavedModel and XGBoost Booster, `model_registry='VERTEX_AI'`, and the `bq extract --model` CLI equivalent.
- [`data+ai/bq-ml/models/remote/`](../../../data+ai/bq-ml/models/remote/) — takes an export from `models/export/` the rest of the way: upload with the pre-built TensorFlow container shown here, deploy to an Endpoint, then call it back from BigQuery with `REMOTE WITH CONNECTION`.
