# PyTorch Model Serving

This folder contains examples of deploying and serving PyTorch models for inference.

## Overview

After training a PyTorch model (see [../pytorch-autoencoder.ipynb](../pytorch-autoencoder.ipynb)), you have several options for serving predictions:

1. **Vertex AI Endpoints** - Managed online prediction service (this folder)
2. **Dataflow RunInference** - Batch and streaming inference pipelines (coming soon)
3. **TorchServe** - Self-managed model server (local or cloud)

## Serving Approaches

### 1. Vertex AI Endpoints (Recommended for Online Predictions)

**What it is**: Fully managed service for deploying ML models to production endpoints.

**Best for**:
- Real-time online predictions
- Low-latency requirements (<100ms)
- Automatic scaling based on traffic
- No infrastructure management

**Key Features**:
- ✅ Pre-built PyTorch containers with TorchServe
- ✅ Autoscaling (min/max replicas)
- ✅ Traffic splitting for A/B testing
- ✅ Built-in monitoring and logging
- ✅ GPU and CPU support
- ✅ Private endpoints available

**Cost**: Pay per hour for deployed compute resources (even when idle)

**Examples**:
- [vertex-ai-endpoint-prebuilt-container.ipynb](./vertex-ai-endpoint-prebuilt-container.ipynb) - Deploy with Google's pre-built PyTorch container
- [vertex-ai-endpoint-custom-container.ipynb](./vertex-ai-endpoint-custom-container.ipynb) - Deploy with custom FastAPI container for output control

#### Pre-built vs Custom Container Decision Guide

**Use Pre-built Container when:**
- ✅ Quick deployment is priority
- ✅ Full model output needed (all 13 metrics)
- ✅ Standard TorchServe setup works
- ✅ Minimal configuration preferred

**Use Custom Container when:**
- ✅ Custom output formatting needed (e.g., only anomaly scores)
- ✅ Want to reduce network traffic (~70% size reduction)
- ✅ Need custom preprocessing/postprocessing logic
- ✅ Framework flexibility beyond TorchServe

**Key Differences:**
- **Permissions**: Pre-built gets automatic GCS access; custom needs service account setup
- **Routing**: Custom containers use Vertex AI's default `/v1/endpoints/{id}/deployedModels/{id}` paths (not configurable via environment variables)
- **Complexity**: Custom requires Dockerfile, Cloud Build, and IAM configuration
- **Output Control**: Custom allows complete control over response format
- **Deployment Time**: Pre-built is faster; custom requires container build step

---

### 2. Dataflow RunInference

**What it is**: Apache Beam's ML inference API integrated with Google Cloud Dataflow.

**Best for**:
- Batch processing of large datasets
- Streaming inference from Pub/Sub
- ETL pipelines with embedded predictions
- Cost-effective for sporadic workloads

**Key Features**:
- ✅ Process BigQuery tables (bounded source)
- ✅ Process Pub/Sub streams (unbounded source)
- ✅ Automatic batching for efficiency
- ✅ Horizontal scaling
- ✅ Pay only when pipeline runs

**Cost**: Pay per second of worker compute time (no cost when not running)

**Examples**:
- [dataflow-setup.ipynb](./dataflow-setup.ipynb) - One-time infrastructure setup
- [dataflow-batch-runinference.ipynb](./dataflow-batch-runinference.ipynb) - Batch inference on BigQuery data
- [dataflow-streaming-runinference.ipynb](./dataflow-streaming-runinference.ipynb) - Real-time streaming inference from Pub/Sub
- [dataflow-vertex-endpoint.ipynb](./dataflow-vertex-endpoint.ipynb) - Call Vertex Endpoint from Dataflow

---

### 3. TorchServe (Self-Managed)

**What it is**: PyTorch's official model serving framework.

**Best for**:
- Custom deployment environments
- On-premise deployments
- Full control over infrastructure
- Development and testing

**Key Features**:
- ✅ Load .mar files directly
- ✅ REST and gRPC APIs
- ✅ Multi-model serving
- ✅ Model versioning
- ✅ Metrics and logging

**Cost**: Infrastructure costs only (you manage servers)

**Note**: Vertex AI Endpoints use TorchServe under the hood with pre-built containers.

---

## Comparison

| Feature | Vertex AI Endpoint | Dataflow RunInference | TorchServe |
|---------|-------------------|----------------------|------------|
| **Managed** | Fully managed | Managed pipeline | Self-managed |
| **Use Case** | Online predictions | Batch/streaming | Custom deployments |
| **Latency** | Low (<100ms) | Higher (batch optimized) | Configurable |
| **Scaling** | Auto (vertical) | Auto (horizontal) | Manual |
| **Cost Model** | Hourly (always on) | Per-second (when running) | Infrastructure only |
| **Setup Complexity** | Low | Medium | High |
| **Infrastructure** | None | None | You manage |

---

## PyTorch Model Artifacts

All serving approaches use the **.mar (Model Archive)** format created during training:

```
pytorch_autoencoder.mar
├── final_model_traced.pt   # TorchScript traced model
├── handler.py              # Custom request/response handler
└── MANIFEST.json           # Model metadata
```

**Creating a .mar file:**
```python
torch-model-archiver \
    --model-name pytorch_autoencoder \
    --version 1.0 \
    --serialized-file final_model_traced.pt \
    --handler handler.py \
    --export-path .
```

See [../pytorch-autoencoder.ipynb](../pytorch-autoencoder.ipynb) for complete example.

---

## Quick Start

### Deploy to Vertex AI Endpoint

1. Train model: [../pytorch-autoencoder.ipynb](../pytorch-autoencoder.ipynb)
2. Deploy to endpoint:
   - **Pre-built container**: [vertex-ai-endpoint-prebuilt-container.ipynb](./vertex-ai-endpoint-prebuilt-container.ipynb) - Quick deployment with TorchServe
   - **Custom container**: [vertex-ai-endpoint-custom-container.ipynb](./vertex-ai-endpoint-custom-container.ipynb) - Custom output format with FastAPI
3. Make predictions via SDK or REST API
4. Clean up resources when done

### Use with Dataflow

1. Train model: [../pytorch-autoencoder.ipynb](../pytorch-autoencoder.ipynb)
2. Setup infrastructure: [dataflow-setup.ipynb](./dataflow-setup.ipynb) - One-time setup
3. Choose your workflow:
   - **Batch processing**: [dataflow-batch-runinference.ipynb](./dataflow-batch-runinference.ipynb)
   - **Streaming**: [dataflow-streaming-runinference.ipynb](./dataflow-streaming-runinference.ipynb)
   - **Endpoint calls**: [dataflow-vertex-endpoint.ipynb](./dataflow-vertex-endpoint.ipynb)

---

## Cost Considerations

### Vertex AI Endpoint Costs

With `n1-standard-4` machine (4 vCPU, 15 GB RAM):
- **Hourly**: ~$0.20/hour per replica
- **Daily**: ~$4.80/day (1 replica always on)
- **Monthly**: ~$144/month

**Best practices**:
- Delete endpoints when not in use
- Use minimum replicas based on traffic
- Consider batch predictions for large datasets

### Dataflow Costs

Charged per second of worker time:
- **Batch jobs**: Pay only during execution
- **Streaming jobs**: Pay while pipeline runs
- **No cost** when pipelines are not running

**Example**: Processing 1M transactions might cost $1-5 depending on worker configuration.

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

### Output
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

**Key metrics**:
- `denormalized_MAE`: Anomaly score (higher = more anomalous)
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
- Deploy to Vertex AI Endpoint:
  - [Pre-built Container →](./vertex-ai-endpoint-prebuilt-container.ipynb)
  - [Custom Container →](./vertex-ai-endpoint-custom-container.ipynb)
- Dataflow Workflows:
  - [Setup Infrastructure →](./dataflow-setup.ipynb)
  - [Batch RunInference →](./dataflow-batch-runinference.ipynb)
  - [Streaming RunInference →](./dataflow-streaming-runinference.ipynb)
  - [Endpoint Calls →](./dataflow-vertex-endpoint.ipynb)
