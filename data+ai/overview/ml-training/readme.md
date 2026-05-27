![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2Fdata%2Bai%2Foverview%2Fml-training&file=readme.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/data%2Bai/overview/ml-training/readme.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/overview/ml-training/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/overview/ml-training/readme.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/overview/ml-training/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/overview/ml-training/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
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
    <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/data%2Bai/overview/ml-training/readme.md"><img src="https://www.svgrepo.com/download/5445/download-button.svg" alt="Download icon" width="20px"></a> <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/data%2Bai/overview/ml-training/readme.md">Download File</a> <i>(right-click and "Save As")</i>
  </td>
</tr>
</table><br/><br/>

---
# ML Training & Batch Inference Overview

A series of standalone notebooks demonstrating ML training and batch inference across Google Cloud services. Each notebook uses the same BigQuery dataset (`bigquery-public-data.ml_datasets.ulb_fraud_detection`), making approaches directly comparable — but each stands on its own, so start wherever fits your use case.

---
## Environment Setup

To work with the notebooks locally, set up a virtual environment with [uv](https://docs.astral.sh/uv/):

```bash
cd "data+ai/overview/ml-training"
uv sync --group dev
```

This installs the project dependencies and `ipykernel` (dev group). To register the environment as a Jupyter kernel:

```bash
uv run python -m ipykernel install --user --name ml-training-overview --display-name "Python (ml-training-overview)"
```

Then select the `Python (ml-training-overview)` kernel when opening a notebook.

> **Running on Colab, Colab Enterprise, or Vertex AI Workbench?** Each notebook includes an install cell that handles packages automatically — no local setup needed.

---
## Notebooks

| Notebook | Service | Topics |
|---|---|---|
| `bigframes-local.ipynb` | BigFrames + XGBoost | Local training with a pandas-like API over BigQuery data, evaluation metrics (classification report, confusion matrix, ROC-AUC) |
| `bqml.ipynb` | BigQuery ML | In-database `BOOSTED_TREE_CLASSIFIER` with Vizier hyperparameter tuning, `ML.EVALUATE`, batch predictions, feature importance — all via SQL |
| `dataproc-serverless.ipynb` | Dataproc Serverless | Interactive Spark sessions via API, PySpark MLlib (logistic regression, XGBoost with barrier mode), batch job submission, custom container images, SparkR workloads |
| `vertex-training.ipynb` | Vertex AI Training | `CustomJob` with pre-built containers (Python XGBoost, R GLM, C++ conceptual), standalone Vizier hyperparameter optimization decoupled from compute |
| `colab-enterprise.ipynb` | Colab Enterprise | Programmatic notebook execution via `NotebookExecutionJob` API, runtime template discovery, GCS result retrieval |
| `model-registry.ipynb` | Vertex AI Model Registry | Listing registered models, BQML export-and-register via GCS, direct BQML registration with `model_registry='vertex_ai'`, custom model upload, model versioning with `parent_model`, version alias management with `ALTER MODEL` |
| `kfp-orchestration.ipynb` | Vertex AI Pipelines (KFP) | Lightweight Python components with per-component `packages_to_install`, `@dsl.container_component` for non-Python code (R), single-component pipelines, 5 parallel training branches (scikit-learn, BQML, Dataproc, Vertex Training, R GLM), sequential dependencies, conditional execution with `dsl.If`, pipeline compilation, metrics retrieval |

## Shared Dataset

All notebooks work with the same BigQuery table to keep comparisons fair. Dataset details and setup are self-contained in each notebook.
