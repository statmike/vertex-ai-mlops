![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2FMLOps%2FServing%2FBatch&file=readme.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/MLOps/Serving/Batch/readme.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https://github.com/statmike/vertex-ai-mlops/blob/main/MLOps/Serving/Batch/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https://github.com/statmike/vertex-ai-mlops/blob/main/MLOps/Serving/Batch/readme.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https://github.com/statmike/vertex-ai-mlops/blob/main/MLOps/Serving/Batch/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https://github.com/statmike/vertex-ai-mlops/blob/main/MLOps/Serving/Batch/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
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
    <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/MLOps/Serving/Batch/readme.md"><img src="https://www.svgrepo.com/download/5445/download-button.svg" alt="Download icon" width="20px"></a> <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/MLOps/Serving/Batch/readme.md">Download File</a> <i>(right-click and "Save As")</i>
  </td>
</tr>
</table><br/><br/>

---
# Batch Inference

> You are here: `vertex-ai-mlops/MLOps/Serving/Batch/readme.md`

This series explores batch inference — processing large collections of data through ML models in a single operation. While the [parent Serving section](../readme.md) covers online prediction (real-time, low-latency), batch inference is the production workhorse for scenarios where immediate responses aren't required: generating daily predictions, scoring customer segments, running model comparisons, or processing backlog data.

The series presents **the same problem solved four ways**: sentiment analysis using HuggingFace models (DistilBERT and BERT) deployed across different GCP platforms. Each notebook is self-contained — pick the platform that fits your team and infrastructure.

## Models

All notebooks use the same two pre-trained HuggingFace models, downloaded directly (no training step):

| Model | HuggingFace ID | Labels | Purpose |
|-------|---------------|--------|---------|
| DistilBERT | `distilbert-base-uncased-finetuned-sst-2-english` | POSITIVE / NEGATIVE | Primary model (v1) |
| BERT | `textattack/bert-base-uncased-SST-2` | LABEL_0 / LABEL_1 | Second model (v2) for multi-model demos |

The different label formats make it easy to verify which model produced each prediction — the same teaching device used in the [online serving notebooks](../readme.md).

## Common Themes

Every notebook in this series demonstrates:

- **Pre/post processing** — Production batch jobs rarely do raw inference alone. Each notebook shows how to prepare data before prediction and transform results afterward, using the patterns native to each platform.
- **Multi-model inference** — Run multiple models on the same data in a single workflow. Enables model comparison, A/B analysis, and ensemble patterns.
- **KFP orchestration via Vertex AI Pipelines** — After showing the direct approach, each notebook builds a Kubeflow Pipeline that orchestrates the same workflow. This is the production pattern for scheduled, repeatable batch inference.
- **BigQuery integration** — Read input from and write predictions to BigQuery, the most common data warehouse for GCP-based ML workloads.

## Notebooks

### 1. [Vertex AI Batch Prediction](./Vertex%20AI%20Batch%20Prediction.ipynb)

The managed, container-based path. Same FastAPI container from the online serving notebooks, uploaded to Vertex AI Model Registry, then used for batch prediction.

**What you'll learn:**
- Batch prediction from both GCS (JSONL) and BigQuery inputs
- Column control with `instanceConfig`: `includedFields`, `excludedFields`, and `keyField` for pass-through row IDs
- Worker tuning: `startingReplicaCount` and `batchSize` — how to size them for your model
- Multi-model: run both DistilBERT and BERT batch jobs, compare outputs
- KFP pipeline with `ModelBatchPredictOp`: pre-process (BQ query) → batch predict → post-process (BQ query)

**Best for:** Teams already using Vertex AI for online serving who want managed batch prediction with minimal infrastructure work.

### 2. [Batch Inference With Dataflow](./Batch%20Inference%20With%20Dataflow.ipynb)

The Apache Beam path. Models load directly into Dataflow workers — no container needed. Pre/post processing are first-class pipeline stages that scale independently.

**What you'll learn:**
- `RunInference` with `PytorchModelHandlerTensor` — load models from GCS, run on workers
- Pre/post processing as Beam `DoFn` stages, plus the `with_preprocess_fn()`/`with_postprocess_fn()` alternative
- Dynamic batching with `BatchElements` — Beam auto-tunes batch size based on throughput
- Multi-model with `KeyedModelHandler` — route inputs to different models by key in a single pipeline
- KFP pipeline with `DataflowPythonJobOp`: parameterized Dataflow job launched from Vertex AI Pipelines

**Best for:** Teams with Apache Beam expertise, complex processing pipelines, or workloads that benefit from Dataflow's autoscaling and exactly-once semantics.

### 3. [Batch Inference With Dataproc](./Batch%20Inference%20With%20Dataproc.ipynb)

The Spark path. For teams in the PySpark ecosystem, or when data lives in formats Spark handles well. Uses Dataproc Serverless — no cluster management.

**What you'll learn:**
- PySpark inference with `mapPartitions` — load model once per partition, avoid per-row serialization overhead
- Dataproc ML Library: `PyTorchModelHandler` and `VertexAIModelHandler` as alternatives to custom UDFs
- Pre/post processing with Spark transformations: `filter()`, `withColumn()`, window functions
- Multi-model: partition-based routing (single pass) and sequential approaches
- KFP pipeline with `DataprocPySparkBatchOp`: parameterized Serverless Spark job from Vertex AI Pipelines

**Best for:** Teams already using PySpark for data processing who want to add ML inference without leaving the Spark ecosystem.

### 4. [Orchestrating Batch Inference With Airflow](./Orchestrating%20Batch%20Inference%20With%20Airflow.ipynb)

The scheduling and coordination layer. Airflow (Cloud Composer) handles *when* to run batch inference and *what happens around it* — data dependencies, cross-system coordination, alerting, and backfill.

**What you'll learn:**
- **Airflow → KFP pattern:** Airflow schedules and monitors, KFP runs the ML pipeline. Best separation of concerns.
- **Airflow direct pattern:** Airflow calls Vertex AI Batch Prediction, Dataflow, or Dataproc directly — skip KFP when the pipeline is simple.
- Deferrable operators: release Airflow workers during long-running batch jobs
- Production patterns: data dependency sensors, multi-model DAGs with task groups, retry/alerting, backfill
- Operators: `RunPipelineJobOperator`, `CreateBatchPredictionJobOperator`, `DataflowStartPythonJobOperator`, `DataprocCreateBatchOperator`

**Best for:** Teams with existing Airflow/Composer infrastructure who need to integrate ML batch inference into broader data pipelines.

## Choosing a Platform

| Need | Vertex AI Batch | Dataflow | Dataproc | Airflow |
|------|:-:|:-:|:-:|:-:|
| **Role** | Inference engine | Inference engine | Inference engine | Orchestrator |
| **Pre/post processing** | KFP pipeline steps | Native Beam stages | Spark transformations | Delegates to engines |
| **Multi-model** | Separate jobs | KeyedModelHandler | Partition-based | Parallel task groups |
| **Model loading** | Container-based | ModelHandler (direct) | UDF / ML Library | N/A (calls engines) |
| **Autoscaling** | No (fixed workers) | Yes (within bounds) | Dynamic allocation | N/A |
| **Scale-to-zero** | N/A (job-based) | N/A (job-based) | N/A (Serverless) | N/A |
| **Data ecosystem** | GCS, BigQuery | GCS, BQ, Pub/Sub, Kafka | GCS, BQ, Hive, Delta | Any (via operators) |
| **GPU support** | Via container | Runner v2 | RAPIDS, Spark GPU | Via engines |
| **Managed service** | Fully managed | Fully managed | Serverless option | Cloud Composer |
| **Scheduling** | Manual / KFP | Manual / KFP | Manual / KFP | Native (cron, sensors) |
| **Backfill** | Manual | Manual | Manual | Native |
| **Team fit** | ML engineers | Data engineers (Beam) | Data engineers (Spark) | Platform/data engineers |

```
What does your batch inference need?
│
├── Just need managed batch prediction, minimal code?
│   └── Vertex AI Batch Prediction (Notebook 1)
│
├── Complex processing pipeline with pre/post steps?
│   │
│   ├── Team knows Apache Beam?
│   │   └── Dataflow (Notebook 2)
│   │
│   └── Team knows PySpark?
│       └── Dataproc (Notebook 3)
│
├── Need scheduling, data dependencies, or cross-system coordination?
│   └── Add Airflow (Notebook 4) on top of any of the above
│
└── Already have Airflow and want the simplest integration?
    └── Airflow direct to Vertex AI Batch (Notebook 4, Pattern 2)
```

## Files

Each notebook writes its source files (container code, Beam pipelines, PySpark scripts, Airflow DAGs) to a per-service subdirectory:

```
Batch/
├── files/
│   ├── vertex-batch/    ← Container source, KFP pipeline definitions
│   ├── dataflow/        ← Beam pipeline scripts, requirements
│   ├── dataproc/        ← PySpark scripts, dependencies
│   └── airflow/         ← DAG files
```

## Prerequisites

- A GCP project with billing enabled
- APIs enabled: Vertex AI, Cloud Build, Artifact Registry, Cloud Storage, BigQuery, Dataflow, Dataproc, Composer (for Notebook 4)
- Python >= 3.10 with the packages listed in the parent [`pyproject.toml`](../pyproject.toml)
- Each notebook includes its own setup cells — no pre-configuration needed beyond a GCP project
