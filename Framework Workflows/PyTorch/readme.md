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

### [PyTorch Autoencoder Overview](./pytorch-autoencoder.ipynb)

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
- ONNX export for cross-framework compatibility
- Distributed training with PyTorch DDP
- Custom CUDA kernels for performance
- Quantization and mobile deployment
