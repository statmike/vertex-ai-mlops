![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2F08+-+R&file=readme.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/08%20-%20R/readme.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https://github.com/statmike/vertex-ai-mlops/blob/main/08%2520-%2520R/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https://github.com/statmike/vertex-ai-mlops/blob/main/08%2520-%2520R/readme.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https://github.com/statmike/vertex-ai-mlops/blob/main/08%2520-%2520R/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https://github.com/statmike/vertex-ai-mlops/blob/main/08%2520-%2520R/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
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
    <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/08%20-%20R/readme.md"><img src="https://www.svgrepo.com/download/5445/download-button.svg" alt="Download icon" width="20px"></a> <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/08%20-%20R/readme.md">Download File</a> <i>(right-click and "Save As")</i>
  </td>
</tr>
</table><br/><br/>

---
# 08 - R has moved ➡️ [Framework Workflows/R](../Framework%20Workflows/R/readme.md)

The R content that used to live here has been **rebuilt and consolidated** into a single, modern, R-first home:

## ➡️ [vertex-ai-mlops / Framework Workflows / R](../Framework%20Workflows/R/readme.md)

What changed:
- **One shared workflow across runtimes.** A single fraud-detection GLM is run in an interactive R notebook, as a Vertex AI Custom Training Job, on Dataproc Serverless (SparkR), and as a Vertex AI Pipeline — so you can compare runtimes directly.
- **Modern BigQuery → R data access.** Reads now use the BigQuery Storage Read API (Arrow) and BigQuery **Apache Iceberg** tables read directly with `arrow` — no CSV/GCS-FUSE export, no `duckdb` middle layer.
- **R model serving.** Package a trained model behind `plumber` in a custom container and deploy to a Vertex AI Endpoint or Cloud Run.
- **Custom R containers** (`rocker/r-ver`) instead of the deprecating prebuilt `r-cpu` images.

| Was here (08 - R) | Now in Framework Workflows/R |
|---|---|
| R - Working With BigQuery | [R - Reading BigQuery Iceberg Tables](../Framework%20Workflows/R/R%20-%20Reading%20BigQuery%20Iceberg%20Tables.ipynb) |
| R - Notebook Based Workflow | [R - Notebook Workflow](../Framework%20Workflows/R/R%20-%20Notebook%20Workflow.ipynb) |
| R - Vertex AI Custom Training Jobs | [R - Vertex AI Custom Training Job](../Framework%20Workflows/R/R%20-%20Vertex%20AI%20Custom%20Training%20Job.ipynb) |
| R - Dataproc Serverless Spark-R Jobs | [R - Dataproc Serverless Spark-R](../Framework%20Workflows/R/R%20-%20Dataproc%20Serverless%20Spark-R.ipynb) |
| R - Dataproc Cluster Spark-R Jobs | *retired* — use [Dataproc Serverless Spark-R](../Framework%20Workflows/R/R%20-%20Dataproc%20Serverless%20Spark-R.ipynb) |
| *(serving, previously stubbed)* | [R - Serving Predictions](../Framework%20Workflows/R/R%20-%20Serving%20Predictions.ipynb) |

> This folder is kept only as a redirect for existing links. New work lives in **[Framework Workflows/R](../Framework%20Workflows/R/readme.md)**.
