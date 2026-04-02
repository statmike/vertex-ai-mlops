![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2Fdata%2Bai%2Fdataflow%2Fexamples&file=README.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/data%2Bai/dataflow/examples/README.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/dataflow/examples/README.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/dataflow/examples/README.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/dataflow/examples/README.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/dataflow/examples/README.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
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
    <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/data%2Bai/dataflow/examples/README.md"><img src="https://www.svgrepo.com/download/5445/download-button.svg" alt="Download icon" width="20px"></a> <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/data%2Bai/dataflow/examples/README.md">Download File</a> <i>(right-click and "Save As")</i>
  </td>
</tr>
</table><br/><br/>

---
# Dataflow Examples

Example notebooks for Apache Beam and Google Cloud Dataflow.

## Notebooks

| Notebook | Description |
|----------|-------------|
| [dataflow-runinference-model-hotswap-event-mode.ipynb](dataflow-runinference-model-hotswap-event-mode.ipynb) | Streaming inference with event-mode model hot-swap via Pub/Sub |
| [dataflow-runinference-model-hotswap-watch-mode.ipynb](dataflow-runinference-model-hotswap-watch-mode.ipynb) | Streaming inference with watch-mode model hot-swap via GCS polling |

## Prerequisites

- A Google Cloud project with billing enabled
- [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) installed and authenticated
- A GCS bucket for Dataflow staging (defaults to `gs://{PROJECT_ID}`)
- APIs enabled: `dataflow.googleapis.com`, `pubsub.googleapis.com`, `storage.googleapis.com`
  ```bash
  gcloud services enable dataflow.googleapis.com pubsub.googleapis.com storage.googleapis.com
  ```

## Environment Setup

### Option 1: Local environment

Set up a local Python environment and register it as a Jupyter kernel. From this directory (`data+ai/dataflow/examples/`):

**Python version:** This project requires Python >= 3.10. Use whichever version manager you prefer:
- **pyenv**: `pyenv install 3.11 && pyenv local 3.11` — all tools below will use it automatically
- **uv**: downloads a compatible version automatically if one isn't found
- **system**: any system Python >= 3.10 works

**uv** (recommended)
```bash
uv sync
uv run python -m ipykernel install --user --name dataflow-examples --display-name "Dataflow Examples"
```

**pip**
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
python -m ipykernel install --user --name dataflow-examples --display-name "Dataflow Examples"
```

**poetry**
```bash
poetry install
poetry run python -m ipykernel install --user --name dataflow-examples --display-name "Dataflow Examples"
```

Then select the **Dataflow Examples** kernel in your notebook.

### Option 2: Standalone

Each notebook includes an environment setup cell that installs required packages into your current kernel using `uv` (if available) with `pip` fallback. No pre-configuration needed — just run the notebook.
