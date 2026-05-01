![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2Fdata%2Bai%2Falloydb&file=readme.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/data%2Bai/alloydb/readme.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/alloydb/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/alloydb/readme.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/alloydb/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/alloydb/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
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
    <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/data%2Bai/alloydb/readme.md"><img src="https://www.svgrepo.com/download/5445/download-button.svg" alt="Download icon" width="20px"></a> <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/data%2Bai/alloydb/readme.md">Download File</a> <i>(right-click and "Save As")</i>
  </td>
</tr>
</table><br/><br/>

---
# AlloyDB

ML inference with [AlloyDB AI](https://cloud.google.com/alloydb/docs/ai/overview) using `ML.PREDICT()` to call Vertex AI Endpoints for SQL-based predictions. AlloyDB registers a remote model that points to a Vertex AI Endpoint, then calls it directly from SQL queries.

## Notebooks

AlloyDB AI content lives in two locations in this repository:

### SQL Inference (MLOps/Serving)

- **[AlloyDB AI Remote Model on Vertex AI Endpoint](../../MLOps/Serving/SQL%20Inference/AlloyDB%20AI%20Remote%20Model%20on%20Vertex%20AI%20Endpoint.ipynb)** — Register a Vertex AI Endpoint as an AlloyDB remote model and run `ML.PREDICT()` for sentiment analysis directly from SQL.

### PyTorch Serving (Framework Workflows)

- **[AlloyDB to Vertex AI Endpoint](../../Framework%20Workflows/PyTorch/serving/alloydb-vertex-ai-endpoint.ipynb)** — End-to-end PyTorch workflow: train a model, deploy to a Vertex AI Endpoint, and call it from AlloyDB using `ML.PREDICT()`.

## The Pattern

AlloyDB follows the same "model on endpoint, call from data platform" pattern used across Google Cloud:

| Data Platform | How it calls the endpoint |
|---------------|--------------------------|
| **AlloyDB** (this section) | `ML.PREDICT()` SQL function with remote model |
| **Spanner** | `ML.PREDICT()` SQL function with remote model |
| **BigQuery** | `ML.PREDICT()` with remote model or Vertex AI connection |
| **Spark on Dataproc** | Pandas UDF with `endpoint.predict()` |

The model runs centrally on a Vertex AI Endpoint, and each data platform calls it over the network via a prediction API.

## Related

- **[Spanner](../spanner/)** — Same `ML.PREDICT()` pattern on Spanner
- **[Dataproc](../dataproc/)** — Calling Vertex AI Endpoints from Spark
- **[Model Serving Overview](../model-serving.md)** — Complete guide to training and deploying custom ML models across Google Cloud
- **[Google Cloud Databases](../gcp-databases.md)** — Overview of Google Cloud's managed database portfolio and AI/ML capabilities
