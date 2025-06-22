![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2FMLOps%2FServing&file=readme.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/MLOps/Serving/readme.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https%3A//github.com/statmike/vertex-ai-mlops/blob/main/MLOps%2FServing/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https%3A//github.com/statmike/vertex-ai-mlops/blob/main/MLOps%2FServing/readme.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https%3A//github.com/statmike/vertex-ai-mlops/blob/main/MLOps%2FServing/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https%3A//github.com/statmike/vertex-ai-mlops/blob/main/MLOps%2FServing/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
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
# Model Serving

> You are here: `vertex-ai-mlops/MLOps/Serving/readme.md`

This section focuses on turning trained machine learning models into production-ready services, a critical step in the MLOps lifecycle. We'll explore various techniques and tools for deploying models on Vertex AI and other GCP services, enabling you to efficiently serve predictions for your applications.

## Serving Methods

There are two primary approaches to model serving, each with its own set of considerations:

- **Online Prediction:**  Provides real-time, on-demand predictions with low latency. Ideal for applications requiring immediate responses, such as web applications, fraud detection systems, and interactive chatbots.
- **Batch Prediction:** Processes a collection of input data points in a single operation. Suitable for scenarios where immediate feedback isn't critical, like generating daily reports, analyzing customer behavior trends, or making recommendations.

## Tutorials and Examples

**Workflows:**
- Building a custom prediction container that works for online and batch predition across local, Vertex AI Endpoints, Vertex AI Batch Predictions, and Cloud Run
    - [Understanding Prediction IO With FastAPI](./Understanding%20Prediction%20IO%20With%20FastAPI.ipynb)
        - Build A Custom Container with FastAPI that repeara the inputs as output predictions
        - Serve **online predictions** with the container: locally, on Vertex AI Prediction Endpoints, on Cloud Run
        - Serve **batch predictions** with Vertex AI Batch Prediction and multiple input types:
            - JSONL
            - CSV
            - BigQuery
            - File List
            - TFRecord Files
- Import TensorFlow SavedModel format model directly into BigQuery and get serverless predictions with SQL
    - [Serve TensorFlow SavedModel Format With BigQuery](./Serve%20TensorFlow%20SavedModel%20Format%20With%20BigQuery.ipynb) 

**Related Workflows:**
- `vertex-ai-mlops/Framework Workflows/Catboost/`
    -  Customize prediction responses
        -  [CatBoost Custom Prediction With FastAPI](../../Framework%20Workflows/CatBoost/CatBoost%20Custom%20Prediction%20With%20FastAPI.ipynb)
            - Create multiple FastAPI apps in the same container. One that serves simple responses, another that gives details responses
            - Create a custom container and use it locally, on Vertex AI Endpoints, and Cloud Run to serve either response type
    - Simplify serving by integrating Vertex AI Feature Store API into your custom prediction - fetch features from Vertex AI Feature Store at serving time
        - [CatBoost Prediction With Vertex AI Feature Store](../../Framework%20Workflows/CatBoost/CatBoost%20Prediction%20With%20Vertex%20AI%20Feature%20Store.ipynb)
            - Custom serving container build with FastAPI
            - Incorporate feature retrieval from Vertex AI Feature Store

**Planning**
- BigQuery Import ONNX model files
- BigQuery Import XGBoost model files
- BigQuery Remote Connection To Vertex AI Endpoints
- Vertex AI Endpoints - Cohosting, Ensembling, and Multi-framwork serving With NVIDIA Triton Server
- Vertex AI Endpoints with Pre-built containers
- Vertex AI Cohosting With Deployment Pools
- Model deployment patterns with Vertex AI Endpoints: replace, rollout
- Model serving scaling examples
- Model serving APIs for Vertex AI Endpoints
- Vertex AI Endpoint Types

**Note:** While this section provides targeted examples, you'll find model serving techniques integrated into various other tutorials and guides throughout the repository.