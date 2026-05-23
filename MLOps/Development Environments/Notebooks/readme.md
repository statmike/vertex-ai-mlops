![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2FMLOps%2FDevelopment+Environments%2FNotebooks&file=readme.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/MLOps/Development%20Environments/Notebooks/readme.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https://github.com/statmike/vertex-ai-mlops/blob/main/MLOps/Development%2520Environments/Notebooks/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https://github.com/statmike/vertex-ai-mlops/blob/main/MLOps/Development%2520Environments/Notebooks/readme.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https://github.com/statmike/vertex-ai-mlops/blob/main/MLOps/Development%2520Environments/Notebooks/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https://github.com/statmike/vertex-ai-mlops/blob/main/MLOps/Development%2520Environments/Notebooks/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
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
    <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/MLOps/Development%20Environments/Notebooks/readme.md"><img src="https://www.svgrepo.com/download/5445/download-button.svg" alt="Download icon" width="20px"></a> <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/MLOps/Development%20Environments/Notebooks/readme.md">Download File</a> <i>(right-click and "Save As")</i>
  </td>
</tr>
</table><br/><br/>

---
# Notebooks
> You are here: `vertex-ai-mlops/MLOps/Development Environments/Notebooks/readme.md`

Jupyter notebooks are a popular development interface for ML practitioners. While interactive use is common, programmatic management of notebooks enables automation, testing, and integration with MLOps workflows.

This section demonstrates how to manage notebooks as code — listing, downloading, modifying, and executing them via cloud APIs.

---
## Environment Setup

To work with the notebooks locally, set up a virtual environment with [uv](https://docs.astral.sh/uv/):

```bash
cd "MLOps/Development Environments/Notebooks"
uv sync --group dev
```

This installs the project dependencies and `ipykernel` (dev group). To register the environment as a Jupyter kernel:

```bash
uv run python -m ipykernel install --user --name dev-environments-notebooks --display-name "Python (dev-environments-notebooks)"
```

Then select the `Python (dev-environments-notebooks)` kernel when opening a notebook.

> **Running on Colab, Colab Enterprise, or Vertex AI Workbench?** Each notebook includes an install cell that handles packages automatically — no local setup needed.

---
## Notebooks

| Notebook | Description |
|---|---|
| [Colab Enterprise - Notebook Management](./Colab%20Enterprise%20-%20Notebook%20Management.ipynb) | Programmatic notebook management with Colab Enterprise — list and download notebooks via the Dataform API, modify notebook cells as JSON, execute notebooks via the Vertex AI NotebookExecutionJob API, and retrieve results from GCS. Covers authentication, runtime template discovery, execution polling, and cell-level timing analysis. |

---
## Documentation

Google Cloud offers several managed notebook environments:

| Environment | Description |
|---|---|
| [Colab Enterprise](https://cloud.google.com/colab/docs/introduction) | Google Cloud's managed notebook environment for teams with enterprise security, IAM integration, and managed runtimes |
| [Colab Enterprise in BigQuery](https://cloud.google.com/bigquery/docs/notebooks-introduction) | The same Colab Enterprise notebooks, accessed through BigQuery Studio — notebooks are BigQuery Studio code assets powered by Dataform and run on Colab Enterprise runtimes |
| [Colab](https://colab.research.google.com/) | Google's free, hosted Jupyter notebook environment — available to anyone with a Google account |
| [Vertex AI Workbench](https://cloud.google.com/vertex-ai/docs/workbench/introduction) | Managed JupyterLab instances on Google Cloud with deep integration into Vertex AI services |

---
