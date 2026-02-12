![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2FFramework+Workflows%2FPyTorch&file=readme.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/Framework%20Workflows/PyTorch/readme.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Framework%2520Workflows/PyTorch/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Framework%2520Workflows/PyTorch/readme.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https://github.com/statmike/vertex-ai-mlops/blob/main/Framework%2520Workflows/PyTorch/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Framework%2520Workflows/PyTorch/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
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
# PyTorch
> You are here: `vertex-ai-mlops/Framework Workflows/PyTorch/readme.md`

[PyTorch](https://pytorch.org/) is an open-source machine learning framework that provides maximum flexibility and speed. PyTorch uses dynamic computation graphs (eager execution) and offers a Pythonic, intuitive API for building and training neural networks.

## Why PyTorch?

- **Pythonic & Intuitive**: Feels natural to Python developers with imperative programming style
- **Dynamic Computation Graphs**: Easier debugging and more flexibility for complex models
- **Research to Production**: Smooth transition with TorchScript and TorchServe
- **Strong Ecosystem**: Rich library ecosystem (torchvision, torchaudio, PyTorch Lightning, etc.)
- **Production Ready**: TorchServe for scalable model serving

## Workflows

### Training

#### [PyTorch Autoencoder Overview](./pytorch-autoencoder.ipynb)

A comprehensive workflow demonstrating pure PyTorch for building an autoencoder for anomaly detection. This notebook is designed as a **direct comparison** to the Keras JAX version.

**Key Features:**
- **Data Loading**: Load data from BigQuery with PyTorch DataLoaders
- **Custom Preprocessing Layers**: Embed normalization/denormalization in `nn.Module` layers
- **Autoencoder Architecture**: Exact same architecture as Keras version (30→16→8→4→8→16→30)
- **Explicit Training Loop**: Full control with early stopping and metric tracking
- **Encoder Extraction**: Standalone encoder model for embeddings
- **Comprehensive Post-Processing**: Match Keras output structure with detailed metrics
- **Multiple Save Formats**:
  - PyTorch native format (`.pt`)
  - TorchScript format for production
  - Model Archive (`.mar`) for TorchServe deployment
- **Custom Handler**: Minimal handler for TorchServe (preprocessing is in the model)

**What Makes This Different:**
- Preprocessing/postprocessing embedded inside custom `nn.Module` layers (just like Keras preprocessing layers)
- Explicit training loops provide full transparency and control
- .mar file format ready for TorchServe production deployment
- Direct architecture comparison with Keras JAX implementation

### Serving

#### [Model Serving Overview](./serving/readme.md)

Learn about different approaches for deploying and serving PyTorch models for inference.

**Deployment Options:**
- **Vertex AI Endpoints**: Fully managed online prediction service
  - [Pre-built Container](./serving/vertex-ai-endpoint-prebuilt-container.ipynb) - Quick deployment with TorchServe, returns full model output (13 metrics)
  - [Custom Container](./serving/vertex-ai-endpoint-custom-container.ipynb) - FastAPI wrapper with custom output formatting
    - ~70% response size reduction (2 fields vs 13)
    - Requires service account setup for GCS access
    - Uses Vertex AI's default routing paths
    - Complete control over response format
  - Real-time predictions with auto-scaling
  - SDK and REST API access
  - Built-in monitoring and logging
- **BigQuery ML**: SQL-based inference directly in BigQuery
  - [ONNX Import](./serving/bigquery-bqml-import-model-onnx.ipynb) - Convert PyTorch to ONNX and import to BigQuery ML
    - Model runs natively in BigQuery (no endpoints!)
    - Lower latency, no endpoint costs
    - Best for models < 250 MB
    - SQL-native predictions with `ML.PREDICT()`
  - [Remote Model](./serving/bigquery-bqml-remote-model-vertex.ipynb) - Call Vertex AI endpoints from BigQuery SQL
    - Reuse existing Vertex AI endpoints
    - SQL-based batch scoring
    - No size limits
    - Ideal for large models or existing deployments
  - Batch scoring, scheduled queries, continuous predictions
  - Perfect for data warehouse integration
- **AlloyDB AI**: SQL-based inference in PostgreSQL-compatible database
  - [AlloyDB with Vertex AI Endpoints](./serving/alloydb-vertex-ai-endpoint.ipynb) - Call endpoints from AlloyDB SQL
    - PostgreSQL-compatible transactional database with ML capabilities
    - SQL-native predictions with `google_ml.predict_row()`
    - Combine OLTP workloads with real-time ML inference
    - Sub-millisecond database queries + ML predictions
    - Ideal for operational databases needing predictions
- **Cloud Spanner**: SQL-based inference in globally distributed database
  - [Spanner with Vertex AI Endpoints](./serving/spanner-vertex-ai-endpoint.ipynb) - Call endpoints from Spanner SQL
    - Globally distributed, horizontally scalable relational database
    - SQL-native predictions with `ML.PREDICT()` (GoogleSQL dialect)
    - Combine OLTP workloads with ML inference at global scale
    - Strong consistency with 99.999% SLA (multi-region)
    - Ideal for globally distributed applications needing predictions
- **Dataflow RunInference**: Batch and streaming inference
  - [Setup](./serving/dataflow-setup.ipynb) - One-time infrastructure setup
  - [Cleanup](./serving/dataflow-cleanup.ipynb) - Remove Dataflow resources
  - Local Model Inference (in-process):
    - [Batch Processing](./serving/dataflow-batch-runinference.ipynb) - Process BigQuery tables
    - [Streaming Processing](./serving/dataflow-streaming-runinference.ipynb) - Process Pub/Sub streams
    - [Streaming with KeyedModelHandler](./serving/dataflow-streaming-runinference-keyed.ipynb) - Beam-native RunInference with metadata passthrough
    - [Streaming with Event-Mode Model Hot-Swap](./serving/dataflow-streaming-runinference-keyed-event-mode.ipynb) - Runtime model updates via Pub/Sub with Vertex AI Model Registry integration
  - Vertex Endpoint Inference (via API):
    - [Batch Processing](./serving/dataflow-batch-runinference-vertex.ipynb) - Call endpoint for BigQuery data
    - [Streaming Processing](./serving/dataflow-streaming-runinference-vertex.ipynb) - Call endpoint for Pub/Sub data
  - Cost-effective for large-scale batch and streaming jobs
- **TorchServe**: Self-managed model server
  - [Local Testing](./serving/torchserve-local.ipynb) - Test TorchServe locally before deployment
  - [Cloud Run Deployment](./serving/torchserve-cloud-run.ipynb) - Serverless TorchServe with auto-scaling
  - [Google Compute Engine Guide](./serving/torchserve-gce.md) - Deploy on VM instances
  - [Google Kubernetes Engine Guide](./serving/torchserve-gke.md) - Deploy on GKE clusters
  - Full control over infrastructure
  - Custom deployment environments
  - Production-grade model serving

See the [serving folder](./serving/) for detailed examples and comparisons.

- **[Advanced Topics: Scaling, GPUs, and Optimization](./serving/advanced-topics.md)** - Guidance on scale testing, performance tuning, and using GPUs.

## Framework Comparison

| Aspect | Keras (JAX/TF) | PyTorch |
|--------|----------------|---------|
| **API Style** | High-level, declarative | Mid-level, imperative |
| **Computation** | Static graph (TF) or functional (JAX) | Dynamic eager execution |
| **Training** | `.fit()` method | Explicit loops |
| **Debugging** | Can be challenging | Native Python debugging |
| **Serving** | TF SavedModel | .mar for TorchServe |
| **Preprocessing** | `keras.layers.Preprocessing` | Custom `nn.Module` |
| **Multi-backend** | ✅ (TF/JAX/PyTorch) | ❌ (PyTorch only) |

## Which Framework to Choose?

### Choose PyTorch if you want:
- Maximum flexibility and control
- Easier debugging during development
- Research-first workflows
- Native Python feel
- Complex dynamic architectures

### Choose Keras if you want:
- Rapid prototyping
- Multi-backend flexibility (run same code on TF, JAX, or PyTorch)
- High-level API simplicity
- Mature TensorFlow ecosystem integration (BigQuery ML, TF Serving, etc.)

## Environment Setup

This folder uses **Poetry** for dependency management. The `pyproject.toml` defines all required packages.

### Required Packages

Core packages for PyTorch workflows:
- `torch` - PyTorch deep learning framework
- `torchvision` - Vision utilities
- `torch-model-archiver` - Create .mar files for TorchServe
- `google-cloud-bigquery` - Data loading from BigQuery
- `pandas` - Data manipulation
- `matplotlib` - Visualization
- `numpy` - Numerical operations

### Installation

If running locally with Poetry:
```bash
# Install dependencies
poetry install

# Activate environment
poetry shell

# Register Jupyter kernel
poetry run task kernel

# Generate requirements files
poetry run task reqs_all
```

### Running Notebooks

**Option 1: Poetry Environment (Local)**
```bash
poetry shell
jupyter lab
```

**Option 2: Google Colab**
- Open the notebook link in any cell
- The setup cells will handle package installation automatically

**Option 3: Vertex AI Workbench**
- Deploy notebook to Workbench
- Packages installed via centralized setup

## Additional Resources

### PyTorch Documentation
- [PyTorch Tutorials](https://pytorch.org/tutorials/)
- [PyTorch Documentation](https://pytorch.org/docs/stable/index.html)
- [TorchServe Documentation](https://pytorch.org/serve/)

### Related Workflows
- [Keras with JAX Overview](../Keras/Keras%20With%20JAX%20Overview.ipynb) - Compare with this implementation
- [Keras with TensorFlow Overview](../Keras/Keras%20With%20TensorFlow%20Overview.ipynb) - Alternative backend

## Future Workflows

Planned additions:
- PyTorch Lightning integration
- Distributed training with PyTorch DDP
- Custom CUDA kernels for performance
- Quantization and mobile deployment
- Model monitoring and drift detection
