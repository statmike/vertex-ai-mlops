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
| | | Local Model<br>(Streaming) | [Streaming Processing](../Framework%20Workflows/PyTorch/serving/dataflow-streaming-runinference.ipynb)<br>• Process Pub/Sub streams<br>• Real-time inference pipeline<br>• Auto-scaling workers |
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


