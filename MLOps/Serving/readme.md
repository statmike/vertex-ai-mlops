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
    - [Online Serving With NVIDIA Triton Server](./Online%20Serving%20With%20NVIDIA%20Triton%20Server.ipynb)
- **More examples in the repository:**
    -  Add links here - soon

**Note:** While this section provides targeted examples, you'll find model serving techniques integrated into various other tutorials and guides throughout the repository.