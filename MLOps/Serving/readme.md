![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2FMLOps%2FServing&file=readme.md)
<!--- header table --->
<table align="left">     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/MLOps/Serving/readme.md">
      <img src="https://cloud.google.com/ml-engine/images/github-logo-32px.png" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</table><br/><br/><br/><br/>

---
# Model Serving

> You are here: `vertex-ai-mlops/MLOps/Serving/readme.md`

This section focuses on turning trained machine learning models into production-ready services, a critical step in the MLOps lifecycle. We'll explore various techniques and tools for deploying models on Vertex AI and other GCP services, enabling you to efficiently serve predictions for your applications.

## Serving Methods

There are two primary approaches to model serving, each with its own set of considerations:

- **Online Prediction:**  Provides real-time, on-demand predictions with low latency. Ideal for applications requiring immediate responses, such as web applications, fraud detection systems, and interactive chatbots.
- **Batch Prediction:** Processes a collection of input data points in a single operation. Suitable for scenarios where immediate feedback isn't critical, like generating daily reports, analyzing customer behavior trends, or making recommendations.

## Tutorials and Examples

- **Workflows:**
    - [Understanding Prediction IO With FastAPI](./Understanding%20Prediction%20IO%20With%20FastAPI.ipynb)
        - Build A Custom Container with FastAPI that repeast the inputs as output predictions
        - Serve online predictions with the container: locally, on Vertex AI Prediction Endpoints, on Cloud Run
        - Serve batch predictions with Vertex AI Batch Prediction and multiple input types:
            - JSONL
            - CSV
            - BigQuery
            - File List
            - TFRecord Files
- **More examples in the repository:**
    -  Add links here - soon

**Note:** While this section provides targeted examples, you'll find model serving techniques integrated into various other tutorials and guides throughout the repository.