![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2FFramework+Workflows%2FPyTorch%2Fserving&file=readme.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/Framework%20Workflows/PyTorch/serving/readme.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Framework%2520Workflows/PyTorch/serving/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Framework%2520Workflows/PyTorch/serving/readme.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https://github.com/statmike/vertex-ai-mlops/blob/main/Framework%2520Workflows/PyTorch/serving/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Framework%2520Workflows/PyTorch/serving/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
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
</table><br/><br/>

---
# PyTorch Model Serving

This folder contains complete examples of deploying and serving PyTorch models for inference across different platforms and use cases.

## Overview

After training a PyTorch model (see [../pytorch-autoencoder.ipynb](../pytorch-autoencoder.ipynb)), you have three main approaches for serving predictions:

1. **[Vertex AI Endpoints](#1-vertex-ai-endpoints)** - Managed online prediction service
2. **[Dataflow Integration](#2-dataflow-integration)** - Batch and streaming inference pipelines
3. **[TorchServe Deployments](#3-torchserve-deployments)** - Portable serving from local to cloud

### Quick Comparison

| Approach | Best For | Management | Cost Model |
|----------|----------|------------|------------|
| **Vertex AI** | Real-time predictions | Fully managed | Hourly (always on) |
| **Dataflow** | Batch/streaming processing | Managed pipeline | Per-second (when running) |
| **TorchServe** | Custom/on-premise | Self-managed | Infrastructure only |

---

## 1. Vertex AI Endpoints

**What it is**: Fully managed service for deploying ML models to production endpoints with auto-scaling and monitoring.

**Best for**:
- Real-time online predictions
- Low-latency requirements (<100ms)
- Automatic scaling based on traffic
- Minimal infrastructure management

**Key Features**:
- ✅ Pre-built PyTorch containers with TorchServe
- ✅ Autoscaling (min/max replicas)
- ✅ Traffic splitting for A/B testing
- ✅ Built-in monitoring and logging
- ✅ GPU and CPU support
- ✅ Private endpoints available

**Cost**: Pay per hour for deployed compute resources (even when idle)

### Deployment Options

#### Pre-built Container
[vertex-ai-endpoint-prebuilt-container.ipynb](./vertex-ai-endpoint-prebuilt-container.ipynb)

- Quick deployment with Google's pre-built PyTorch container
- Uses TorchServe under the hood
- Returns full model output (13 metrics)
- Automatic GCS access permissions
- Minimal configuration required

#### Custom Container
[vertex-ai-endpoint-custom-container.ipynb](./vertex-ai-endpoint-custom-container.ipynb)

- Custom FastAPI wrapper for complete output control
- ~70% response size reduction (2 fields vs 13)
- Requires service account setup for GCS access
- Uses Vertex AI's default routing paths
- Full control over preprocessing/postprocessing

### Decision Guide: Pre-built vs Custom

**Use Pre-built Container when:**
- ✅ Quick deployment is priority
- ✅ Full model output needed (all 13 metrics)
- ✅ Standard TorchServe setup works
- ✅ Minimal configuration preferred

**Use Custom Container when:**
- ✅ Custom output formatting needed
- ✅ Want to reduce network traffic
- ✅ Need custom preprocessing/postprocessing logic
- ✅ Framework flexibility beyond TorchServe

**Key Differences:**
- **Permissions**: Pre-built gets automatic GCS access; custom needs service account setup
- **Routing**: Custom containers use Vertex AI's default `/v1/endpoints/{id}/deployedModels/{id}` paths
- **Complexity**: Custom requires Dockerfile, Cloud Build, and IAM configuration
- **Output Control**: Custom allows complete control over response format
- **Deployment Time**: Pre-built is faster; custom requires container build step

### Cost Considerations

With `n1-standard-4` machine (4 vCPU, 15 GB RAM):
- **Hourly**: ~$0.20/hour per replica
- **Daily**: ~$4.80/day (1 replica always on)
- **Monthly**: ~$144/month

**Best practices**:
- Delete endpoints when not in use
- Use minimum replicas based on traffic
- Consider batch predictions for large datasets

### Quick Start

1. Train model: [../pytorch-autoencoder.ipynb](../pytorch-autoencoder.ipynb)
2. Deploy to endpoint:
   - **Pre-built**: [vertex-ai-endpoint-prebuilt-container.ipynb](./vertex-ai-endpoint-prebuilt-container.ipynb)
   - **Custom**: [vertex-ai-endpoint-custom-container.ipynb](./vertex-ai-endpoint-custom-container.ipynb)
3. Make predictions via SDK or REST API
4. Clean up resources when done

---

## 2. Dataflow Integration

**What it is**: Apache Beam's ML inference API integrated with Google Cloud Dataflow for scalable batch and streaming inference.

**Best for**:
- Batch processing of large datasets
- Streaming inference from Pub/Sub
- ETL pipelines with embedded predictions
- Cost-effective for sporadic workloads

**Key Features**:
- ✅ Process BigQuery tables (bounded source)
- ✅ Process Pub/Sub streams (unbounded source)
- ✅ Automatic batching for efficiency
- ✅ Horizontal scaling with autoscaling
- ✅ Configurable worker machine types and scaling limits
- ✅ Pay only when pipeline runs
- ✅ Supports both local models and Vertex AI Endpoints
- ✅ Job monitoring via SDK
- ✅ Centralized cleanup for all resources

**Cost**: Pay per second of worker compute time (no cost when not running)

**Example**: Processing 1M transactions might cost $1-5 depending on worker configuration.

### Infrastructure Setup

[dataflow-setup.ipynb](./dataflow-setup.ipynb) - One-time setup that:
- Downloads .mar file from GCS
- Extracts .pt file from .mar archive
- Uploads .pt to GCS for RunInference workers
- Creates BigQuery tables for results (4 tables: batch/streaming × local/vertex)
- Creates Pub/Sub topics and subscriptions for streaming

### Resource Cleanup

[dataflow-cleanup.ipynb](./dataflow-cleanup.ipynb) - Centralized cleanup for all Dataflow resources:
- ✅ Stop running Dataflow jobs (streaming and batch)
- ✅ Clean BigQuery tables (truncate or delete)
- ✅ Delete Pub/Sub topics and subscriptions
- ✅ Delete GCS model files
- ✅ Granular control via configuration flags
- ✅ Safety checks and confirmation prompts
- ✅ Pattern-based job filtering

**Why centralized cleanup?**
- Streaming jobs run continuously until cancelled (avoiding ongoing costs)
- One location to manage all test resources
- Flexible cleanup during testing (e.g., truncate tables without deleting schema)
- Prevents resource accumulation across multiple test runs

### Workflow Matrix

Dataflow offers a 2×2 matrix of workflows combining data sources with inference approaches:

|  | **Batch (BigQuery)** | **Streaming (Pub/Sub)** |
|---|---|---|
| **Local Model** | [dataflow-batch-runinference.ipynb](./dataflow-batch-runinference.ipynb) | [dataflow-streaming-runinference.ipynb](./dataflow-streaming-runinference.ipynb) |
| **Vertex Endpoint** | [dataflow-batch-runinference-vertex.ipynb](./dataflow-batch-runinference-vertex.ipynb) | [dataflow-streaming-runinference-vertex.ipynb](./dataflow-streaming-runinference-vertex.ipynb) |

#### Local Model Inference
Loads .pt file directly in Dataflow workers (in-process):
- **Lower cost**: No endpoint overhead
- **Higher performance**: No network calls
- **Simpler setup**: No endpoint deployment needed
- **Worker requirements**: Need sufficient memory to load PyTorch model
- **Best for**: High-throughput batch jobs

**Notebooks:**
- [dataflow-batch-runinference.ipynb](./dataflow-batch-runinference.ipynb) - Batch processing with local model
- [dataflow-streaming-runinference.ipynb](./dataflow-streaming-runinference.ipynb) - Streaming with local model

#### Vertex Endpoint Inference
Calls deployed Vertex AI Endpoint via API:
- **Centralized model**: Same endpoint used by multiple pipelines
- **Model updates**: Update endpoint without redeploying pipeline
- **Resource separation**: Endpoint scales independently
- **Worker requirements**: Lower memory needs (only API client)
- **Best for**: Shared model across services

**Notebooks:**
- [dataflow-batch-runinference-vertex.ipynb](./dataflow-batch-runinference-vertex.ipynb) - Batch processing via endpoint
- [dataflow-streaming-runinference-vertex.ipynb](./dataflow-streaming-runinference-vertex.ipynb) - Streaming via endpoint

### Worker Configuration

All Dataflow notebooks include configurable worker resources:

**Machine Type**: `n1-standard-4` (4 vCPUs, 15 GB memory)
- Adjust based on model size and throughput needs
- Local model: Higher memory for model loading
- Vertex endpoint: Lower memory (API calls only)

**Autoscaling**:
- **Batch jobs**: MIN_WORKERS=2, MAX_WORKERS=10
  - Jobs complete automatically when data exhausted
  - Lower max to control costs for bounded datasets
- **Streaming jobs**: MIN_WORKERS=2, MAX_WORKERS=20
  - Jobs run continuously until cancelled
  - Higher max to handle traffic bursts

**GPU Support**: Optional for local model inference (not applicable for Vertex endpoints)

### Job Monitoring

All Dataflow notebooks include job monitoring:

**Batch Jobs**:
- Non-blocking pipeline execution
- Programmatic status polling (30-second intervals)
- Automatic completion detection
- Final status summary with elapsed time

**Streaming Jobs**:
- Link to Dataflow Console for real-time metrics
- Use centralized cleanup notebook to stop jobs

### Quick Start

1. Train model: [../pytorch-autoencoder.ipynb](../pytorch-autoencoder.ipynb)
2. Setup infrastructure: [dataflow-setup.ipynb](./dataflow-setup.ipynb)
3. Choose your workflow based on the matrix above

**For Vertex Endpoint workflows**, also deploy an endpoint first:
- [vertex-ai-endpoint-prebuilt-container.ipynb](./vertex-ai-endpoint-prebuilt-container.ipynb) OR
- [vertex-ai-endpoint-custom-container.ipynb](./vertex-ai-endpoint-custom-container.ipynb)

4. When done testing: [dataflow-cleanup.ipynb](./dataflow-cleanup.ipynb)

---

## 3. TorchServe Deployments

**What it is**: PyTorch's official model serving framework - portable solution that scales from local development to enterprise Kubernetes.

**Best for**:
- Local development and testing
- Custom deployment environments
- On-premise deployments
- Full control over infrastructure
- Multi-model serving needs

**Key Features**:
- ✅ Load .mar files directly
- ✅ REST and gRPC APIs
- ✅ Multi-model serving
- ✅ Model versioning
- ✅ Metrics and logging
- ✅ Portable across environments

**Cost**: Infrastructure costs only (you manage servers)

**Note**: Vertex AI Endpoints use TorchServe under the hood with pre-built containers.

### Deployment Paths

TorchServe offers a progressive deployment path from local development to production:

```
Local Development → Cloud Run (Serverless) → GCE (VMs) → GKE (Kubernetes)
```

### Getting Started

#### Local Development
[torchserve-local.ipynb](./torchserve-local.ipynb)

- Start TorchServe on your machine
- Load .mar file from training
- Make predictions via REST API
- Perfect for development and testing
- Zero cloud costs

**Use this for**:
- Local testing before cloud deployment
- Development and debugging
- Learning TorchServe basics
- Offline inference

#### Serverless Deployment
[torchserve-cloud-run.ipynb](./torchserve-cloud-run.ipynb)

- Containerize TorchServe application
- Deploy to Cloud Run (fully managed)
- Auto-scaling, pay-per-use model
- Scales to zero when idle
- Production-ready with minimal ops

**Use this for**:
- Production deployments with minimal ops
- Variable/unpredictable traffic
- Cost-effective serving
- Quick cloud deployment

### Scaling to Production

For advanced production scenarios, detailed guides are available:

#### Compute Engine Deployment
[torchserve-gce.md](./torchserve-gce.md) - Deploy TorchServe to GCE VMs

- Long-running dedicated servers
- Persistent serving workloads
- Predictable, constant traffic
- Full VM control

**When to use**:
- Consistent 24/7 traffic
- Need dedicated resources
- Specific VM configurations required
- Cost-effective for steady loads

#### Kubernetes Deployment
[torchserve-gke.md](./torchserve-gke.md) - Deploy TorchServe to GKE

- Multi-model orchestration
- Advanced scaling strategies
- High availability requirements
- Enterprise production needs

**When to use**:
- Multiple models to serve
- Complex deployment strategies
- Need rolling updates/canary deployments
- Enterprise-scale infrastructure

### Quick Start

1. Train model: [../pytorch-autoencoder.ipynb](../pytorch-autoencoder.ipynb)
2. Start locally: [torchserve-local.ipynb](./torchserve-local.ipynb)
3. Deploy serverless: [torchserve-cloud-run.ipynb](./torchserve-cloud-run.ipynb)
4. Scale up as needed: [torchserve-gce.md](./torchserve-gce.md) or [torchserve-gke.md](./torchserve-gke.md)

---

## Model Artifacts

All serving approaches use the **.mar (Model Archive)** format created during training:

```
pytorch_autoencoder.mar
├── final_model_traced.pt   # TorchScript traced model
├── handler.py              # Custom request/response handler
└── MANIFEST.json           # Model metadata
```

**Creating a .mar file:**
```bash
torch-model-archiver \
    --model-name pytorch_autoencoder \
    --version 1.0 \
    --serialized-file final_model_traced.pt \
    --handler handler.py \
    --export-path .
```

See [../pytorch-autoencoder.ipynb](../pytorch-autoencoder.ipynb) for complete example.

---

## Model Input/Output Format

### Input
```json
{
  "instances": [
    [92.35, -0.26, 0.13, ..., 15.47]  // 30 features
  ]
}
```

### Output (Pre-built Container / TorchServe)
```json
{
  "predictions": [{
    "denormalized_MAE": 26.99,
    "denormalized_RMSE": 141.12,
    "denormalized_MSE": 19914.84,
    "denormalized_MSLE": 0.41,
    "normalized_MAE": 0.72,
    "normalized_RMSE": 1.03,
    "normalized_MSE": 1.07,
    "normalized_MSLE": 0.12,
    "encoded": [0.17, 0.0, 0.19, 0.41],
    "normalized_reconstruction": [...],
    "normalized_reconstruction_errors": [...],
    "denormalized_reconstruction": [...],
    "denormalized_reconstruction_errors": [...]
  }]
}
```

### Output (Custom Container)
```json
{
  "anomaly_score": 26.99,
  "encoded": [0.17, 0.0, 0.19, 0.41]
}
```

**Key metrics**:
- `denormalized_MAE` / `anomaly_score`: Anomaly score (higher = more anomalous)
- `encoded`: Latent space representation (4D)
- `*_reconstruction`: Reconstructed input values
- `*_reconstruction_errors`: Per-feature reconstruction errors

---

## Resources

### Vertex AI
- [Vertex AI Prediction Overview](https://cloud.google.com/vertex-ai/docs/predictions/overview)
- [Pre-built PyTorch Containers](https://cloud.google.com/vertex-ai/docs/predictions/pre-built-containers#pytorch)
- [Vertex AI Pricing](https://cloud.google.com/vertex-ai/pricing)

### Dataflow
- [Dataflow ML Documentation](https://cloud.google.com/dataflow/docs/machine-learning)
- [Apache Beam RunInference](https://beam.apache.org/documentation/ml/about-ml/)
- [Dataflow Pricing](https://cloud.google.com/dataflow/pricing)

### TorchServe
- [TorchServe Documentation](https://pytorch.org/serve/)
- [Model Archiver](https://github.com/pytorch/serve/tree/master/model-archiver)
- [TorchServe Examples](https://github.com/pytorch/serve/tree/master/examples)

### PyTorch
- [PyTorch Documentation](https://pytorch.org/docs/stable/index.html)
- [TorchScript](https://pytorch.org/docs/stable/jit.html)
- [PyTorch Tutorials](https://pytorch.org/tutorials/)

---

## Navigation

- [← Back to PyTorch Folder](../readme.md)

### Vertex AI Endpoints
- [Pre-built Container →](./vertex-ai-endpoint-prebuilt-container.ipynb)
- [Custom Container →](./vertex-ai-endpoint-custom-container.ipynb)

### Dataflow Workflows
- [Setup Infrastructure →](./dataflow-setup.ipynb)
- Local Model Inference:
  - [Batch RunInference →](./dataflow-batch-runinference.ipynb)
  - [Streaming RunInference →](./dataflow-streaming-runinference.ipynb)
- Vertex Endpoint Inference:
  - [Batch RunInference →](./dataflow-batch-runinference-vertex.ipynb)
  - [Streaming RunInference →](./dataflow-streaming-runinference-vertex.ipynb)
- [Cleanup Resources →](./dataflow-cleanup.ipynb)

### TorchServe Deployments
- [Local Development →](./torchserve-local.ipynb)
- [Cloud Run Deployment →](./torchserve-cloud-run.ipynb)
- [GCE Deployment Guide →](./torchserve-gce.md)
- [GKE Deployment Guide →](./torchserve-gke.md)
