![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2FMLOps%2FServing%2FSQL+Inference&file=readme.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/MLOps/Serving/SQL%20Inference/readme.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https://github.com/statmike/vertex-ai-mlops/blob/main/MLOps/Serving/SQL%2520Inference/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https://github.com/statmike/vertex-ai-mlops/blob/main/MLOps/Serving/SQL%2520Inference/readme.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https://github.com/statmike/vertex-ai-mlops/blob/main/MLOps/Serving/SQL%2520Inference/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https://github.com/statmike/vertex-ai-mlops/blob/main/MLOps/Serving/SQL%2520Inference/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
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
    <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/MLOps/Serving/SQL%20Inference/readme.md"><img src="https://www.svgrepo.com/download/5445/download-button.svg" alt="Download icon" width="20px"></a> <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/MLOps/Serving/SQL%20Inference/readme.md">Download File</a> <i>(right-click and "Save As")</i>
  </td>
</tr>
</table><br/><br/>

---
# SQL Inference — Predictions from SQL

> You are here: `vertex-ai-mlops/MLOps/Serving/SQL Inference/readme.md`

Run ML predictions directly from SQL — no Python serving code needed. Two patterns:

- **Remote models** — SQL calls a Vertex AI Endpoint. The model runs on Vertex AI, the database sends input and receives predictions. Any model, any size, any framework.
- **Model import** — The model is imported into the database engine itself. No endpoint needed, predictions run inside the query engine. Limited to supported formats and size constraints.

## Remote Models

Three GCP database services can call a Vertex AI Endpoint as a remote model via their native SQL interface. One endpoint deployment, three SQL surfaces.

### 1. [BQML Remote Model on Vertex AI Endpoint](./BQML%20Remote%20Model%20on%20Vertex%20AI%20Endpoint.ipynb)

BigQuery's remote model feature — call any Vertex AI Endpoint from SQL using `ML.PREDICT()`.

**What you'll learn:**
- Create a BigQuery Cloud Resource Connection and grant it endpoint access
- Register the endpoint as a BQML remote model (`CREATE MODEL ... REMOTE WITH CONNECTION`)
- Run predictions from SQL with `ML.PREDICT()` — no Python needed for inference
- Batch scoring patterns: full-table scoring, WHERE filters, JOINs

### 2. [AlloyDB AI Remote Model on Vertex AI Endpoint](./AlloyDB%20AI%20Remote%20Model%20on%20Vertex%20AI%20Endpoint.ipynb)

AlloyDB's `google_ml_integration` extension — row-level predictions inside OLTP transactions.

**What you'll learn:**
- Create an AlloyDB cluster with Private Services Access networking
- Enable the `google_ml_integration` extension and register the Vertex AI endpoint
- Call predictions with `google_ml.predict_row()` from SQL
- Row-level, low-latency predictions inside transactional workloads

### 3. [Spanner ML Remote Model on Vertex AI Endpoint](./Spanner%20ML%20Remote%20Model%20on%20Vertex%20AI%20Endpoint.ipynb)

Spanner ML — globally distributed ML predictions via `ML.PREDICT()`.

**What you'll learn:**
- Create a Spanner Enterprise instance and register a remote model
- Call predictions with `ML.PREDICT()` from Spanner's GoogleSQL dialect
- Globally distributed inference — Spanner's multi-region capability extends to ML calls
- Compare all three database ML surfaces

## Model Import

Import a model directly into BigQuery — predictions run inside the query engine with no external endpoint.

### 4. [BQML Import Model via ONNX](./BQML%20Import%20Model%20via%20ONNX.ipynb)

Import a PyTorch model (converted to ONNX) into BigQuery.

**What you'll learn:**
- Convert a PyTorch model to ONNX format
- Import the ONNX model into BigQuery (`CREATE MODEL ... OPTIONS(model_type='ONNX')`)
- Run predictions with `ML.PREDICT()` — model runs natively in BigQuery, no endpoint needed
- Compare: model import (runs inside BQ, < 250 MB limit) vs remote model (any size, calls endpoint)

### 5. [Serve TensorFlow SavedModel Format With BigQuery](./Serve%20TensorFlow%20SavedModel%20Format%20With%20BigQuery.ipynb)

Import a TensorFlow SavedModel into BigQuery — the serverless advantage of BigQuery applied to inference.

**What you'll learn:**
- Import a TensorFlow SavedModel into BigQuery using BQML
- Run predictions with `ML.PREDICT()` using the imported model
- Serverless, in-database inference with no endpoint needed

## Database ML Comparison

| Aspect | BigQuery (Remote) | BigQuery (Import) | AlloyDB | Spanner |
|--------|-------------------|-------------------|---------|---------|
| Pattern | Remote model | Model import | Remote model | Remote model |
| Endpoint needed? | Yes | No | Yes | Yes |
| SQL function | `ML.PREDICT()` | `ML.PREDICT()` | `google_ml.predict_row()` | `ML.PREDICT()` |
| Model size limit | Any | < 250 MB | Any | Any |
| Supported formats | Any (via endpoint) | ONNX, TF SavedModel | Any (via endpoint) | Any (via endpoint) |
| Best for | Batch scoring, analytics | Small models, no infra | Transactional scoring | Global transactional scoring |
| Latency profile | Seconds (query engine) | Seconds (query engine) | Milliseconds (row-level) | Milliseconds (global) |
| Cost driver | Bytes scanned | Bytes scanned | Instance size | Node count |

## Prerequisites

- A GCP project with billing enabled
- APIs enabled: Vertex AI, Cloud Build, Artifact Registry, plus database-specific APIs
- Python >= 3.10 with the packages listed in the parent [`pyproject.toml`](../pyproject.toml)
- Each notebook includes its own setup cells — no pre-configuration needed beyond a GCP project
