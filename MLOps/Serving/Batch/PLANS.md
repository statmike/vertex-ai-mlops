# Batch Inference Notebook Series — Plans

> Track the status of each notebook in the batch inference series. Delete this file when all notebooks are complete.

## Series Overview

Four self-contained notebooks covering batch inference on GCP. All use the same two HuggingFace sentiment models (DistilBERT + BERT), demonstrate pre/post processing, multi-model patterns, and KFP orchestration. Each notebook is independent — no cross-notebook dependencies.

---

## Notebook 1: Vertex AI Batch Prediction

**Status:** Not Started

**File:** `Vertex AI Batch Prediction.ipynb`

The managed, container-based path. Same FastAPI container from the online serving notebooks, uploaded to Model Registry, used for batch prediction.

### Structure

**Setup (~15 cells)**
- Header with GitHub/Colab/CE/Workbench links (same pattern as all Serving notebooks)
- `EXPERIMENT = 'vertex-batch'`
- Colab setup, installs, API enablement
- Project, params, imports, clients
- Download DistilBERT + BERT to GCS (idempotent, same as Dedicated Public Endpoint notebook)
- Build same FastAPI container with Cloud Build, push to AR (idempotent)
- Upload both models to Vertex AI Model Registry

**Batch Prediction from GCS — JSONL (~10 cells)**
- Prepare JSONL input file in GCS with multiple sentences
- Include extra columns beyond what the model needs (to demonstrate column filtering)
- Configure batch prediction job:
  - `instanceConfig.keyField` — pass-through row ID (appears in output, NOT sent to model)
  - `instanceConfig.includedFields` — whitelist only the text column
  - Show `excludedFields` as the alternative (mutually exclusive with `includedFields`)
- Worker config:
  - `startingReplicaCount` — explicit worker count (no autoscaling in batch mode)
  - `manualBatchTuningParameters.batchSize` — instances per HTTP request to container (default 64)
  - Explain sizing: model memory per instance x batch size must fit in worker memory
- Submit job via `aiplatform.Model.batch_predict()`
- Monitor job progress (state polling)
- Read and display results from GCS output

**Batch Prediction from BigQuery (~8 cells)**
- Create BQ table with input data (multiple columns: id, text, category, timestamp)
- Run batch prediction with BQ input → BQ output
- Show `instanceConfig` filtering columns from BQ schema
- Query results directly in BQ — demonstrate how `keyField` enables joining predictions back to source table
- Markdown: when to use GCS vs BQ paths (GCS for files already in storage, BQ when data lives in warehouse and results need to join back)

**Multi-Model Batch Prediction (~8 cells)**
- Run batch prediction with DistilBERT model
- Run batch prediction with BERT model (same input data)
- Compare outputs side by side:
  - DistilBERT returns `POSITIVE`/`NEGATIVE` labels
  - BERT returns `LABEL_0`/`LABEL_1` labels
  - Same teaching point as online serving notebooks — different labels confirm which model produced each prediction
- Markdown: use cases for multi-model batch (model comparison, A/B analysis, ensemble voting)

**Pre/Post Processing with KFP Pipeline (~12 cells)**
- The production story: batch prediction rarely stands alone
- Build a KFP pipeline with three stages:
  1. **Pre-process component:** BQ query to filter/transform raw data → staging table
     - Filter by date range (parameterized)
     - Clean text (remove special characters, normalize whitespace)
     - Add row IDs for downstream joining
  2. **Batch predict component:** `ModelBatchPredictOp` on the staged data
     - Pass `instanceConfig`, worker count, batch size as pipeline params
  3. **Post-process component:** BQ query to transform predictions
     - Map numeric labels to human-readable names
     - Compute confidence buckets (high/medium/low)
     - Join predictions back to source table with metadata
- Compile and submit pipeline to Vertex AI Pipelines
- Inspect pipeline run: component status, artifacts at each stage, lineage
- Show parameterization: swap model URI, change date filter, adjust worker count — all pipeline params

**Tuning & Monitoring Reference (~4 cells, markdown-heavy)**
- Batch size tuning guide:
  - Default is 64 — this means 64 instances per HTTP request to the container
  - Too large: OOM in container, failed requests, job retries
  - Too small: underutilized workers, slower throughput
  - Rule of thumb: start with default, reduce if seeing OOM errors, increase if container CPU/memory are underutilized
- Worker count:
  - `startingReplicaCount` is the actual count — no autoscaling in batch mode
  - More workers = faster but more cost. Linear scaling for embarrassingly parallel workloads.
  - Consider: input data size / (batch_size x predictions_per_second_per_worker) = approximate job duration
- Monitoring: job state polling, Cloud Logging for container logs
- Cost: worker-hours x machine type pricing

**Cleanup (~4 cells)**
- Delete batch prediction jobs (or let them auto-clean)
- Undeploy and delete models from Model Registry
- Optional: delete GCS artifacts (commented out)
- Empty end cell

### Key Files
- `files/vertex-batch/` — Container source (same FastAPI app), KFP pipeline definition

### Dependencies
- `google-cloud-aiplatform`, `google-cloud-storage`, `google-cloud-bigquery`, `kfp`, `google-cloud-pipeline-components` (all already in pyproject.toml)

---

## Notebook 2: Batch Inference With Dataflow

**Status:** Not Started

**File:** `Batch Inference With Dataflow.ipynb`

The Apache Beam path. Models load directly into Dataflow workers via `RunInference` — no container build needed. Pre/post processing are native Beam pipeline stages that scale independently.

### Structure

**Setup (~12 cells)**
- Header with GitHub/Colab/CE/Workbench links
- `EXPERIMENT = 'dataflow-batch'`
- Colab setup, installs (`apache-beam[gcp]` added to pyproject.toml)
- Project, params, imports, clients
- Download DistilBERT + BERT to GCS (idempotent)
- No container build — Dataflow uses `ModelHandler` to load models directly from GCS
- Create BQ dataset and input table with sample sentences

**Direct RunInference Pipeline (~15 cells)**
- Build an Apache Beam pipeline step by step, explaining each stage:
  1. **Read:** `ReadFromBigQuery` — pull text data from BQ table
  2. **Pre-process:** Custom `DoFn` for tokenization
     - Load HuggingFace tokenizer
     - Convert text → token IDs, attention masks
     - Output `torch.Tensor` ready for model input
  3. **Batch:** `BatchElements` with `min_batch_size`/`max_batch_size`
     - Beam auto-tunes batch size based on throughput
     - Explain: dynamic batching adapts to model latency, unlike fixed batch sizes
  4. **Infer:** `RunInference` with `PytorchModelHandlerTensor`
     - Configure: model class, model URI (GCS path), device ('cpu')
     - Model loads once per worker, reused across elements
  5. **Post-process:** Custom `DoFn` to extract predictions
     - Apply softmax to logits
     - Map label indices to human-readable names
     - Extract confidence scores
  6. **Write:** `WriteToBigQuery` — results to BQ output table
- Run locally with `DirectRunner` on a small sample (5-10 sentences) to verify pipeline logic
- Run on Dataflow with `DataflowRunner`:
  - Configure `num_workers`, `max_num_workers`, `machine_type`
  - Set `temp_location` and `staging_location` in GCS
  - Monitor job in Dataflow console link
- Read and display results from BQ output table

**Pre/Post Processing Deep Dive (~8 cells)**
- Show alternative: `with_preprocess_fn()` and `with_postprocess_fn()` on `RunInference`
  - Simpler API — functions attached directly to the inference step
  - Tradeoff: co-located with inference (no independent scaling) vs separate DoFns (scale independently)
- Production pre-process patterns:
  - Input validation (reject malformed inputs, log errors)
  - Text normalization (lowercase, strip HTML, handle unicode)
  - Feature engineering (combine fields, compute derived features)
- Production post-process patterns:
  - Confidence thresholding (flag low-confidence predictions for human review)
  - Result enrichment (add metadata: model version, timestamp, input hash)
  - Error handling (graceful degradation for failed predictions)
- Compare: separate DoFns (more flexible, independent scaling, better for complex logic) vs built-in functions (simpler, co-located, better for lightweight transforms)

**Multi-Model with KeyedModelHandler (~10 cells)**
- `KeyedModelHandler` — route inputs to different models based on a key
- Prepare input data with a key column (e.g., `model_version`: "distilbert" or "bert")
- Configure two model handlers:
  - `PytorchModelHandlerTensor` for DistilBERT with key "distilbert"
  - `PytorchModelHandlerTensor` for BERT with key "bert"
- Wrap in `KeyedModelHandler` — single pipeline processes both
- Results tagged with which model served them (key preserved in output)
- Verify: DistilBERT predictions show POSITIVE/NEGATIVE, BERT shows LABEL_0/LABEL_1
- Use cases: A/B testing in batch, model comparison on same data, ensemble inference

**KFP Orchestration (~10 cells)**
- Write Beam pipeline as a standalone Python file with `%%writefile` to `files/dataflow/`
  - Parameterized: model path, input/output tables, worker count via argparse
  - Same pipeline logic as the direct section above
- Upload pipeline file to GCS
- Build KFP pipeline using `DataflowPythonJobOp`:
  - Pass Dataflow params: project, region, temp location, worker count
  - Pass model path, input/output tables as pipeline params
  - Configure requirements file for worker dependencies
- Compile and submit pipeline to Vertex AI Pipelines
- Compare with running Dataflow directly: KFP adds scheduling, lineage tracking, retry, and parameter management

**Configuration Reference (~6 cells, markdown-heavy)**
- Autoscaling:
  - `num_workers` (initial count) vs `max_num_workers` (ceiling)
  - Dataflow autoscales between them based on backlog
  - Unlike Vertex AI Batch (fixed workers), Dataflow adapts
- Batching:
  - `BatchElements` dynamic batching: Beam measures element processing time and adjusts batch size
  - `min_batch_size`, `max_batch_size` — bounds for the auto-tuner
  - Relationship to model throughput: larger batches amortize model loading overhead
- GPU support:
  - Runner v2 with custom container that includes GPU drivers
  - `accelerator` pipeline option for GPU type and count
  - Not demoed (small models don't need it) — reference to `data+ai/dataflow/gpu/` for GPU examples
- Comparison table: Dataflow vs Vertex AI Batch Prediction

| Aspect | Vertex AI Batch | Dataflow RunInference |
|--------|:-:|:-:|
| Pre/post processing | Separate pipeline steps | Native pipeline stages |
| Multi-model | Separate jobs | Single pipeline (KeyedModelHandler) |
| Model loading | Container-based | Direct (ModelHandler) |
| Autoscaling | No (fixed workers) | Yes (within bounds) |
| Custom logic | Limited to container | Full Beam SDK |
| Managed service | Fully managed | Fully managed |
| Best for | Simple predict jobs | Complex processing pipelines |

**Cleanup (~4 cells)**
- Cancel Dataflow job if still running
- Delete BQ dataset/tables
- Delete GCS artifacts
- Empty end cell

### Key Files
- `files/dataflow/pipeline.py` — Standalone Beam pipeline (for KFP)
- `files/dataflow/requirements.txt` — Worker dependencies

### Dependencies
- Existing: `google-cloud-aiplatform`, `google-cloud-storage`, `google-cloud-bigquery`, `kfp`, `google-cloud-pipeline-components`, `torch`, `transformers`
- New: `apache-beam[gcp]` (add to pyproject.toml)

---

## Notebook 3: Batch Inference With Dataproc

**Status:** Not Started

**File:** `Batch Inference With Dataproc.ipynb`

The Spark path. PySpark for data processing, model inference via UDFs or Dataproc ML Library. Uses Dataproc Serverless — no cluster to manage.

### Structure

**Setup (~12 cells)**
- Header with GitHub/Colab/CE/Workbench links
- `EXPERIMENT = 'dataproc-batch'`
- Colab setup, installs
- Project, params, imports, clients
- Download DistilBERT + BERT to GCS (idempotent)
- No container build — models load directly in Spark executors
- Create BQ dataset and input table with sample sentences

**Direct PySpark Batch Job (~15 cells)**
- Write a PySpark script with `%%writefile` to `files/dataproc/`:
  1. **Read:** `spark.read.format('bigquery')` — pull from BQ into DataFrame
  2. **Pre-process:** Spark UDF for tokenization
     - Broadcast tokenizer artifacts to executors (avoid per-task serialization)
     - Convert text → token IDs, attention masks
  3. **Infer:** `mapPartitions` pattern
     - Load model once per partition (NOT per row — this is the critical performance pattern)
     - Run inference on all rows in the partition
     - Explain: `mapPartitions` amortizes model loading across rows; a naive UDF would reload the model for every row
  4. **Post-process:** Spark UDF for label mapping, confidence extraction
     - Map label indices to names
     - Extract confidence scores
     - Add metadata columns (model version, timestamp)
  5. **Write:** `df.write.format('bigquery')` — results back to BQ
- Submit as Dataproc Serverless batch job using `dataproc_v1.BatchControllerClient`:
  - Configure runtime version, Python version
  - Set executor count, memory, cores
  - Pass model path and BQ tables as script args
- Monitor job progress (poll operation)
- Read and display results from BQ output table

**Dataproc ML Library (~8 cells)**
- Alternative to custom UDFs — higher-level API
- `PyTorchModelHandler`:
  - Load model from GCS
  - `predict(df, model_handler)` — handles batching and model loading automatically
  - Less control but simpler code
- `VertexAIModelHandler`:
  - Call a deployed Vertex AI endpoint from Spark
  - Hybrid approach: Spark for data processing, Vertex AI for inference
  - When to use: model too large for executor memory, or model already deployed for online serving
- Compare: custom UDF with `mapPartitions` (full control, best performance) vs ML Library (simpler, opinionated) vs VertexAI handler (model already deployed, centralized serving)

**Pre/Post Processing Patterns (~6 cells)**
- Spark's strength: SQL-like transformations at scale
- Pre-process examples:
  - `df.filter()` — filter rows by date range, category, quality score
  - `df.withColumn()` — text cleaning, normalization
  - Window functions — compute features from surrounding rows (e.g., rolling averages)
  - `df.join()` — enrich with reference data (lookup tables, feature store)
- Post-process examples:
  - Join predictions back to source data
  - Aggregate predictions (e.g., average sentiment per customer)
  - Write to multiple outputs: BQ for analytics, GCS for archival
- Show the full DataFrame transformation chain: raw → clean → tokenized → predicted → enriched → output

**Multi-Model (~8 cells)**
- Two approaches:
  1. **Partition-based routing (single pass):**
     - Add model key column to DataFrame
     - `repartition` by model key
     - `mapPartitions` loads the appropriate model based on the key in each partition
     - More efficient (single pass over data) but more complex code
  2. **Sequential (two passes):**
     - Two separate `mapPartitions` calls, each with a different model
     - Union or join results
     - Simpler code, easier to debug, but two passes over data
- Compare approaches: partition-based is better for large datasets (single I/O pass), sequential is simpler and fine for moderate sizes
- Verify: DistilBERT predictions show POSITIVE/NEGATIVE, BERT shows LABEL_0/LABEL_1

**KFP Orchestration (~10 cells)**
- PySpark script already written to `files/dataproc/` from the direct section
- Upload script to GCS
- Build KFP pipeline using `DataprocPySparkBatchOp`:
  - Pass Dataproc Serverless params: project, region, runtime version
  - Pass model path, input/output tables, executor count as pipeline params
  - Configure Spark properties (`spark.executor.memory`, `spark.executor.cores`)
- Optional: multi-step pipeline with one component per model (fan-out pattern)
  - Two `DataprocPySparkBatchOp` components running in parallel
  - A final component that joins/compares results
- Compile and submit pipeline to Vertex AI Pipelines
- Compare with running Dataproc directly: KFP adds scheduling, parameter management, and the ability to compose with other ML steps

**Configuration Reference (~6 cells, markdown-heavy)**
- Dataproc Serverless vs Dataproc on Compute Engine:
  - Serverless: no cluster, auto-provisioned, pay per job — use for batch inference
  - On Compute Engine: persistent cluster, more control — use when you need custom images or long-running interactive work
- Executor sizing:
  - `spark.executor.memory` — must hold model + batch of data. Sentiment models need ~1-2 GB; large models need more.
  - `spark.executor.cores` — controls parallelism within each executor
  - Number of executors — horizontal scaling. More executors = more parallel partitions.
- Spark properties that matter for ML:
  - `spark.sql.execution.arrow.pyspark.enabled=true` — Arrow for faster pandas UDF serialization
  - `spark.dynamicAllocation.enabled` — Spark's autoscaling (Serverless manages this)
- GPU on Dataproc:
  - Supported via RAPIDS accelerator
  - More complex than Dataflow GPU — requires RAPIDS-compatible operations
  - Not demoed — reference only
- Three-way comparison table:

| Aspect | Vertex AI Batch | Dataflow | Dataproc |
|--------|:-:|:-:|:-:|
| Processing model | Container per worker | Beam pipeline | Spark DataFrame |
| Pre/post processing | KFP pipeline steps | Beam DoFns | Spark UDFs |
| Multi-model | Separate jobs | KeyedModelHandler | Partition-based |
| Autoscaling | No | Yes | Dynamic allocation |
| Data ecosystem | GCS, BQ | GCS, BQ, Pub/Sub, Kafka | GCS, BQ, Hive, Delta |
| Team fit | ML engineers | Data engineers (Beam) | Data engineers (Spark) |
| GPU support | Via container | Runner v2 | RAPIDS |
| Serverless | Yes | Yes | Yes |

**Cleanup (~4 cells)**
- Cancel Dataproc batch job if still running
- Delete BQ dataset/tables
- Delete GCS artifacts
- Empty end cell

### Key Files
- `files/dataproc/inference.py` — PySpark inference script
- `files/dataproc/requirements.txt` — Dependencies for Dataproc workers

### Dependencies
- Existing: `google-cloud-aiplatform`, `google-cloud-storage`, `google-cloud-bigquery`, `kfp`, `google-cloud-pipeline-components`, `torch`, `transformers`
- New: `google-cloud-dataproc`, `pyspark` (add to pyproject.toml)

---

## Notebook 4: Orchestrating Batch Inference With Airflow

**Status:** Not Started

**File:** `Orchestrating Batch Inference With Airflow.ipynb`

The scheduling and coordination layer. Cloud Composer (managed Airflow) handles when to run batch inference and what happens around it — data dependencies, cross-system coordination, alerting, and backfill. Self-contained — includes its own simplified pipeline definitions rather than depending on Notebooks 1-3.

### Structure

**Setup (~10 cells)**
- Header with GitHub/Colab/CE/Workbench links
- `EXPERIMENT = 'airflow-batch'`
- Colab setup, installs
- Project, params, imports, clients
- Cloud Composer environment: check for existing or create one
  - Composer 2 (managed Airflow 2.x)
  - Note: Composer environment creation takes ~20 minutes — show how to check for and reuse existing environments
- `apache-airflow-providers-google` comes pre-installed in Composer — pin version for reference

**Why Airflow for ML Workflows (~4 cells, markdown-heavy)**
- Where Airflow fits: scheduling, data dependencies, monitoring, alerting, cross-system coordination
- Where KFP fits: ML-specific logic, experiment tracking, artifact lineage, model registry integration
- The handoff: Airflow decides *when* to run, KFP decides *how* to run
- Production reality: ML batch inference is one step in a larger data pipeline. Airflow is the existing scheduler. Adding ML as "just another DAG" is simpler than standing up a separate scheduler.
- Markdown flow: Data Landing (scheduled/event) → Data Validation (Airflow) → ML Inference (Vertex AI / Dataflow / Dataproc) → Result Validation (Airflow) → Downstream Systems (Airflow)

**Pattern 1: Airflow → KFP Pipeline (~15 cells)**
- The cleanest separation: Airflow schedules, KFP runs ML
- Write DAG with `%%writefile` to `files/airflow/`:
  1. `BigQueryCheckOperator` — sensor that waits for today's data to land in BQ (e.g., check row count for today's partition)
  2. `RunPipelineJobOperator` — trigger a KFP batch prediction pipeline
     - Pass execution date, model version, worker count as pipeline params (Airflow templating: `{{ ds }}`)
     - `deferrable=True` — release Airflow worker while KFP pipeline runs (critical for cost — batch pipelines can run for hours)
  3. `BigQueryInsertJobOperator` — post-prediction SQL to update reporting/aggregation table
  4. Notification task on success or failure (email, Slack, or Cloud Monitoring)
- Include a minimal KFP pipeline definition inline (simplified version of Notebook 1's pipeline) so the notebook is self-contained
- Upload KFP pipeline template to GCS/AR
- Upload DAG to Composer's GCS bucket
- Trigger DAG manually, observe execution in Airflow UI (link)
- Inspect: Airflow logs show orchestration timing, KFP console shows ML pipeline details

**Pattern 2: Airflow Direct to Vertex AI Batch Prediction (~10 cells)**
- Skip KFP — call Vertex AI directly from Airflow
- Write DAG with `%%writefile` to `files/airflow/`:
  1. `BigQueryCheckOperator` — wait for data
  2. `CreateBatchPredictionJobOperator` — submit batch prediction job
     - Configure `instanceConfig`, worker count, batch size (same params as Notebook 1)
     - `deferrable=True` — don't hold a worker while the batch job runs
  3. `BigQueryInsertJobOperator` — post-process results in BQ
- When to use over Pattern 1: simpler pipeline, no need for KFP artifact tracking, team standardized on Airflow for everything

**Pattern 3: Airflow Direct to Dataflow (~10 cells)**
- Airflow launches a Dataflow RunInference job
- Write DAG with `%%writefile` to `files/airflow/`:
  1. `BigQueryCheckOperator` — wait for data
  2. `DataflowStartPythonJobOperator` — launch Beam pipeline
     - Pass model path, input/output tables, worker config
     - `deferrable=True`
     - Include simplified Beam pipeline file inline (self-contained)
  3. Post-processing task
- Upload Beam pipeline file to GCS
- Upload DAG to Composer

**Pattern 4: Airflow Direct to Dataproc (~8 cells)**
- Airflow launches a Dataproc Serverless batch job
- Write DAG with `%%writefile` to `files/airflow/`:
  1. `BigQueryCheckOperator` — wait for data
  2. `DataprocCreateBatchOperator` — submit PySpark job
     - `deferrable=True`
     - Include simplified PySpark script inline (self-contained)
  3. Post-processing task
- Upload PySpark script to GCS
- Upload DAG to Composer

**Production Patterns (~8 cells, markdown-heavy)**
- **Multi-model DAG:**
  - Task groups: run DistilBERT and BERT inference in parallel
  - Downstream aggregation task that compares or merges results
  - Show `TaskGroup` syntax for visual organization in Airflow UI
- **Retry and alerting:**
  - `retries`, `retry_delay` — batch jobs fail sometimes (quota, transient errors)
  - `on_failure_callback` — send alert on failure (Cloud Monitoring, Slack, email)
  - `sla` — flag missed deadlines (e.g., predictions should be ready by 6 AM)
- **Backfill:**
  - One of Airflow's killer features for batch ML
  - Missed a day? `airflow dags backfill --start-date 2026-04-15 --end-date 2026-04-17`
  - The DAG runs for each missing date — no custom scripting needed
  - KFP doesn't have a native equivalent — this is a major Airflow advantage
- **Idempotency:**
  - DAGs should be idempotent: running the same date twice produces the same result
  - Pattern: write to date-partitioned BQ tables, overwrite partition on re-run
  - Avoid append-only patterns that duplicate data on retry
- **Decision framework:**

| Need | Airflow → KFP | Airflow Direct |
|------|:-:|:-:|
| ML artifact lineage | Yes (KFP tracks) | No |
| Team already has KFP | Yes (leverage it) | Unnecessary layer |
| Complex ML pipeline | Yes (KFP handles) | Gets messy in a DAG |
| Simple batch predict | Overkill | Clean and simple |
| Cross-system deps | Both (Airflow handles) | Both (Airflow handles) |
| Backfill | Both | Both |
| Monitoring | Airflow + KFP UIs | Airflow UI only |

**Series Comparison (~4 cells, markdown-heavy)**

| Orchestration | Scheduling | ML Logic | Best For |
|:---:|:---:|:---:|:---:|
| KFP only (Notebooks 1-3) | Manual / cron trigger | KFP pipeline | ML-first teams |
| Airflow → KFP (this notebook) | Airflow DAG | KFP pipeline | Enterprise with existing Airflow |
| Airflow direct (this notebook) | Airflow DAG | Airflow operators | Simple pipelines, Airflow-native teams |

**Cleanup (~4 cells)**
- Delete DAGs from Composer's GCS bucket
- Delete BQ artifacts
- Note: don't delete Composer environment (expensive to recreate, ~20 min, user likely shares it across projects)
- Empty end cell

### Key Files
- `files/airflow/dag_kfp.py` — DAG for Airflow → KFP pattern
- `files/airflow/dag_vertex_batch.py` — DAG for direct Vertex AI Batch Prediction
- `files/airflow/dag_dataflow.py` — DAG for direct Dataflow
- `files/airflow/dag_dataproc.py` — DAG for direct Dataproc
- `files/airflow/pipeline.py` — Simplified Beam pipeline (self-contained)
- `files/airflow/inference.py` — Simplified PySpark script (self-contained)

### Dependencies
- Existing: `google-cloud-aiplatform`, `google-cloud-storage`, `google-cloud-bigquery`, `kfp`, `google-cloud-pipeline-components`
- New: `apache-airflow-providers-google` (reference only — pre-installed in Composer, not needed locally unless testing DAGs outside Composer)

---

## Shared Conventions

All notebooks follow the established Serving series patterns:

- **Header:** GitHub/Colab/CE/Workbench links (same table format)
- **Setup:** Colab detection, installs with `uv`/`pip` fallback, API enablement, project params
- **Models:** Same DistilBERT + BERT from GCS, idempotent download
- **EXPERIMENT variable:** Unique per notebook for resource naming
- **Cleanup:** Delete all created resources, empty end cell
- **Markdown-heavy:** Explanation cells between code cells, comparison tables, decision frameworks
- **Files:** Source files written with `%%writefile` to `files/{service}/`

## pyproject.toml Updates

New dependencies to add when building the notebooks:
- `apache-beam[gcp]` — for Notebook 2 (Dataflow)
- `google-cloud-dataproc` — for Notebook 3 (Dataproc)
- `pyspark` — for Notebook 3 (Dataproc), local testing only

## Build Order

All four notebooks are independent, but the natural build order is:
1. **Vertex AI Batch Prediction** — most native to the repo's Vertex AI focus, established container pattern
2. **Batch Inference With Dataflow** — builds on the RunInference patterns already in the repo (Framework Workflows/PyTorch/serving/)
3. **Batch Inference With Dataproc** — least prior art in the repo, most exploration needed
4. **Orchestrating Batch Inference With Airflow** — benefits from having all three inference patterns established, includes simplified versions of each
