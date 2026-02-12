![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2Fdata%2Bai&file=readme.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/data%2Bai/readme.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/readme.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
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
# Data + AI: Machine Learning with Google Cloud Data Sources

This guide provides an overview of machine learning options when working with data sources in Google Cloud. Whether you're building custom ML models or leveraging pre-trained solutions, Google Cloud offers a comprehensive ecosystem that brings your models directly to your data.

## Google Cloud Database Solutions

Google Cloud offers a comprehensive portfolio of fully managed database services designed to meet diverse application needs. From transactional workloads to analytical processing, each database service provides unique capabilities for storing and managing your data.

**[View the complete guide to Google Cloud Databases →](gcs-databases.md)**

The guide covers:
- **Google Cloud Storage (GCS)** - Object storage for unstructured data, blobs, and backups
- **BigQuery** - Serverless data warehouse for large-scale SQL analytics
- **Cloud SQL** - Managed relational databases (MySQL, PostgreSQL, SQL Server)
- **AlloyDB for PostgreSQL** - High-performance PostgreSQL with AI integration
- **Cloud Spanner** - Globally distributed, strongly consistent relational database
- **Cloud Bigtable** - NoSQL wide-column store for large-scale, low-latency applications
- **Firestore** - NoSQL document database for mobile and web applications
- **Memorystore** - In-memory data store for Redis and Memcached

Each database service offers native integration with Google Cloud's AI and ML ecosystem, enabling you to build intelligent applications that combine data storage, processing, and machine learning.

## Serving Custom ML Models

Google Cloud provides multiple pathways for serving custom machine learning models, allowing you to bring your models directly to your data regardless of where they're stored or how they were trained.

### Model Deployment Options

You can deploy custom ML models to Google Cloud through several approaches:

1. **Custom ML Training** - Train your models using your preferred framework and data sources
2. **Vertex AI** - Deploy models to managed endpoints with automatic scaling and monitoring
3. **Bring Your Own Model** - Import models trained elsewhere into Vertex AI Model Registry
4. **Database-Native ML** - Execute predictions directly within your database using SQL

### The Google Cloud Data & AI Ecosystem

<div align="center">

![Google Cloud Data & AI Ecosystem](resources/images/data+ai+ml.png)

*Bring your custom models directly to your data*

</div>

## PyTorch Model Training & Serving Examples

The following table provides a comprehensive guide to training custom PyTorch models and deploying them across various Google Cloud services. Each deployment option is tailored for specific use cases, from managed endpoints to database-native predictions.

### Complete Workflow Matrix

| Training | Deployment System | Method | Notebooks & Guides |
|----------|-------------------|--------|-------------------|
| **[PyTorch Autoencoder](../Framework%20Workflows/PyTorch/pytorch-autoencoder.ipynb)**<br><br>Custom PyTorch model for anomaly detection<br>• Data from BigQuery<br>• Custom preprocessing layers<br>• Multiple save formats (.pt, TorchScript, .mar) | **Vertex AI Endpoints**<br><br>Managed online prediction service | Pre-built Container<br>(TorchServe) | [Pre-built Container Deployment](../Framework%20Workflows/PyTorch/serving/vertex-ai-endpoint-prebuilt-container.ipynb)<br>• Quick deployment with TorchServe<br>• Returns full model output (13 metrics)<br>• Auto-scaling, built-in monitoring |
| | | Custom Container<br>(FastAPI) | [Custom Container Deployment](../Framework%20Workflows/PyTorch/serving/vertex-ai-endpoint-custom-container.ipynb)<br>• ~70% response size reduction<br>• Custom output formatting<br>• Complete control over API |
| | **BigQuery ML**<br><br>SQL-based inference in data warehouse | ONNX Import<br>(Native) | [ONNX Import to BigQuery](../Framework%20Workflows/PyTorch/serving/bigquery-bqml-import-model-onnx.ipynb)<br>• Model runs natively in BigQuery<br>• Lower latency, no endpoint costs<br>• Best for models < 250 MB |
| | | Remote Model<br>(Vertex AI) | [Remote Model from BigQuery](../Framework%20Workflows/PyTorch/serving/bigquery-bqml-remote-model-vertex.ipynb)<br>• Call Vertex AI endpoints from SQL<br>• No size limits<br>• Batch scoring with `ML.PREDICT()` |
| | **AlloyDB AI**<br><br>PostgreSQL-compatible transactional database | Vertex AI Endpoint<br>(SQL) | [AlloyDB with Vertex AI](../Framework%20Workflows/PyTorch/serving/alloydb-vertex-ai-endpoint.ipynb)<br>• OLTP + ML in one database<br>• `google_ml.predict_row()` function<br>• Sub-millisecond queries + predictions |
| | **Cloud Spanner**<br><br>Globally distributed relational database | Vertex AI Endpoint<br>(SQL) | [Spanner with Vertex AI](../Framework%20Workflows/PyTorch/serving/spanner-vertex-ai-endpoint.ipynb)<br>• Global scale with strong consistency<br>• `ML.PREDICT()` in GoogleSQL<br>• 99.999% SLA (multi-region) |
| | **Dataflow RunInference**<br><br>Batch and streaming processing | Local Model<br>(Batch) | [Setup](../Framework%20Workflows/PyTorch/serving/dataflow-setup.ipynb) • [Batch Processing](../Framework%20Workflows/PyTorch/serving/dataflow-batch-runinference.ipynb) • [Cleanup](../Framework%20Workflows/PyTorch/serving/dataflow-cleanup.ipynb)<br>• Process BigQuery tables<br>• In-process inference<br>• Cost-effective for large datasets |
| | | Local Model<br>(Streaming) | [Streaming Processing](../Framework%20Workflows/PyTorch/serving/dataflow-streaming-runinference.ipynb)<br>• Process Pub/Sub streams<br>• Explicit BatchElements + custom DoFn<br>• Auto-scaling workers |
| | | Local Model<br>(Streaming Keyed) | [Streaming with KeyedModelHandler](../Framework%20Workflows/PyTorch/serving/dataflow-streaming-runinference-keyed.ipynb)<br>• Beam-native RunInference + KeyedModelHandler<br>• 5 pipeline steps (vs 7 explicit)<br>• Model tracking via `PredictionResult.model_id` |
| | | Local Model<br>(Streaming Keyed +<br>Event-Mode) | [Streaming with Model Hot-Swap](../Framework%20Workflows/PyTorch/serving/dataflow-streaming-runinference-keyed-event-mode.ipynb)<br>• Runtime model hot-swap via Pub/Sub<br>• Vertex AI Model Registry integration<br>• Rollback by publishing previous version path |
| | | Vertex Endpoint<br>(Batch) | [Batch with Vertex API](../Framework%20Workflows/PyTorch/serving/dataflow-batch-runinference-vertex.ipynb)<br>• Call endpoint for BigQuery data<br>• Managed model updates<br>• Separation of compute and serving |
| | | Vertex Endpoint<br>(Streaming) | [Streaming with Vertex API](../Framework%20Workflows/PyTorch/serving/dataflow-streaming-runinference-vertex.ipynb)<br>• Call endpoint for Pub/Sub data<br>• Real-time with managed endpoints<br>• Version control and A/B testing |
| | **TorchServe**<br><br>Self-managed PyTorch model server | Local Testing | [Local TorchServe](../Framework%20Workflows/PyTorch/serving/torchserve-local.ipynb)<br>• Test before deployment<br>• Debug .mar files<br>• Validate handlers |
| | | Cloud Run<br>(Serverless) | [Cloud Run Deployment](../Framework%20Workflows/PyTorch/serving/torchserve-cloud-run.ipynb)<br>• Serverless auto-scaling<br>• Pay per request<br>• Zero infrastructure management |
| | | Compute Engine<br>(VMs) | [GCE Guide](../Framework%20Workflows/PyTorch/serving/torchserve-gce.md)<br>• Full VM control<br>• Custom configurations<br>• Persistent infrastructure |
| | | Kubernetes<br>(GKE) | [GKE Guide](../Framework%20Workflows/PyTorch/serving/torchserve-gke.md)<br>• Container orchestration<br>• Advanced scaling policies<br>• Multi-model deployment |

### Additional Resources

- **[Serving Overview](../Framework%20Workflows/PyTorch/serving/readme.md)** - Detailed comparison of all deployment options
- **[Advanced Topics](../Framework%20Workflows/PyTorch/serving/advanced-topics.md)** - Scaling, GPUs, and performance optimization
- **[PyTorch Framework Guide](../Framework%20Workflows/PyTorch/readme.md)** - Complete PyTorch workflow documentation


### TO BE ADDED

- Training Options: Vertex, BQML
- Solutions
- Generative AI - Hosted Models
- Generative AI - Private Models


