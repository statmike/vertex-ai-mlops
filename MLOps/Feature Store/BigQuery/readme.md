![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2FMLOps%2FFeature+Store%2FBigQuery&file=readme.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/MLOps/Feature%20Store/BigQuery/readme.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https://github.com/statmike/vertex-ai-mlops/blob/main/MLOps/Feature%2520Store/BigQuery/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https://github.com/statmike/vertex-ai-mlops/blob/main/MLOps/Feature%2520Store/BigQuery/readme.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https://github.com/statmike/vertex-ai-mlops/blob/main/MLOps/Feature%2520Store/BigQuery/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https://github.com/statmike/vertex-ai-mlops/blob/main/MLOps/Feature%2520Store/BigQuery/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
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
    <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/MLOps/Feature%20Store/BigQuery/readme.md"><img src="https://www.svgrepo.com/download/5445/download-button.svg" alt="Download icon" width="20px"></a> <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/MLOps/Feature%20Store/BigQuery/readme.md">Download File</a> <i>(right-click and "Save As")</i>
  </td>
</tr>
</table><br/><br/>

---
# BigQuery Feature Store

> You are here: `vertex-ai-mlops/MLOps/Feature Store/BigQuery/readme.md`

The [BigQuery Storage Read API](https://cloud.google.com/bigquery/docs/reference/storage) reads directly from BigQuery's storage layer — bypassing the query engine — streaming [Apache Arrow](https://arrow.apache.org/) record batches over parallel gRPC connections. Combined with session caching and table clustering, this creates a feature serving layer with 20–200ms latency, zero infrastructure, and capabilities that a key-value store can't match.

> **Also in this series: [Bigtable Feature Store](../Bigtable/readme.md) and [Vertex AI Feature Store](../vertex/readme.md)**
>
> This BigQuery approach eliminates the online store entirely — **no sync pipelines, no infrastructure to manage, no key design constraints**. For sub-10ms point lookups, see [Bigtable Feature Store](../Bigtable/readme.md). For a fully managed solution, see [Vertex AI Feature Store](../vertex/readme.md). All three approaches use BigQuery as the offline store. See the [comparison table](../readme.md#choosing-an-approach) in the parent readme.

The data uses a 130K-entity dataset (26 groups × 5,000 entities, 224 columns) stored in BigQuery dataset `bigquery_feature_store`.

## Environment Setup

### Option 1: Local environment

From this directory (`MLOps/Feature Store/BigQuery/`):

**uv** (recommended)
```bash
uv sync
uv run python -m ipykernel install --user --name bigquery-feature-store --display-name "BigQuery Feature Store"
```

**pip**
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
python -m ipykernel install --user --name bigquery-feature-store --display-name "BigQuery Feature Store"
```

Then select the **BigQuery Feature Store** kernel in your notebook.

### Option 2: Standalone

Each notebook includes an environment setup cell that installs required packages into your current kernel.

## Key Concepts

- **[BigQuery Storage Read API](https://cloud.google.com/bigquery/docs/reference/storage)** — Reads directly from BigQuery's Colossus storage layer via gRPC, bypassing the query engine. Returns data as Apache Arrow record batches for zero-copy deserialization.
- **[Apache Arrow](https://arrow.apache.org/)** — A columnar in-memory format designed for zero-copy reads. The on-wire format matches the in-memory format — no CPU cycles for deserialization.
- **Session Caching** — Pre-creating and caching `ReadSession` objects to skip the ~50–100ms session creation overhead on repeat reads. The `FeatureSessionPool` class provides this with TTL-based eviction in <50 lines of code.
- **[Table Clustering](https://cloud.google.com/bigquery/docs/clustered-tables)** — Physically sorts data by specified columns. When a `row_restriction` references clustered columns, BigQuery prunes at the storage block level — reading only blocks that contain matching rows.
- **Row Restriction** — A WHERE clause passed to the Storage Read API that filters rows at the storage level. Unlike Bigtable row key lookups, any column can be used in any combination.
- **Column Pruning** — Specifying `selected_fields` to read only the columns you need. Columnar storage makes this nearly free — unread columns are never touched.

## Notebooks

### [BigQuery Feature Store — Environment](./BigQuery%20Feature%20Store%20-%20Environment.ipynb)

Creates the BigQuery dataset and synthetic feature tables used by all notebooks in this series.

**What you'll learn:**
- Generate synthetic feature data covering every BigQuery data type (224 columns, 130K rows)
- Create clustered tables for Storage Read API performance
- Generate embedding vectors for similarity search demos

### [BigQuery Feature Store](./BigQuery%20Feature%20Store.ipynb)

The main notebook — builds the complete architecture, benchmarks everything, and demonstrates every advantage of using the Storage Read API for feature serving.

**What you'll learn:**
- Why the Storage Read API occupies a latency sweet spot between standard BQ queries (seconds) and Bigtable (<10ms)
- How table clustering and `row_restriction` enable storage-level block pruning for fast filtered reads
- Session caching with a reusable `FeatureSessionPool` that cuts repeat-read latency roughly in half
- Arrow zero-copy deserialization — from gRPC stream to numpy array with no intermediate copies
- A FastAPI serving endpoint with async integration, connection pooling, and concurrency scaling
- Multi-stream parallelism and bulk feature hydration where the Storage API dominates Bigtable at scale
- In-memory vector similarity search with numpy (SIMD-optimized, faster than server-side KNN for moderate scale)
- Honest three-way latency and cost comparisons: standard BQ query vs Storage API vs Bigtable
- A decision framework for choosing between BigQuery Storage API, Bigtable, and Vertex AI Feature Store

### Parts

| Part | Topic | Key Concepts |
|------|-------|-------------|
| 1. The Data | Verify tables | Confirm Environment notebook tables exist |
| 2. Baseline | Standard BQ queries | Why SQL queries are too slow for serving (~2–7s) |
| 3. Storage Read API | The core pattern | Single/batch reads, column pruning, flexible filtering, Arrow zero-copy |
| 4. Session Caching | Core optimization | `FeatureSessionPool`, TTL eviction, cold vs warm reads |
| 5. FastAPI Serving | Application | Endpoint, input validation, concurrent requests, async reads, concurrency scaling |
| 6. Bulk Hydration | Scale advantage | Segment reads, multi-stream scaling, scaling chart with BQ query baseline, training data extraction |
| 7. Vector Similarity | In-memory search | Embeddings → numpy → cosine similarity, top-K retrieval |
| 8. Advanced Patterns | Flexibility | Multi-table reads, dynamic columns, ad-hoc filtering, time travel |
| 9. Latency Comparison | Benchmarks | Storage API vs BQ query vs Bigtable — three-way visualization |
| 10. Cost Comparison | Economics | Infrastructure, read cost, sync pipeline, total cost of ownership |
| 11. When to Use Which | Decision framework | Decision tree, three-way comparison table |

### [BigQuery Feature Store — Cloud Run](./BigQuery%20Feature%20Store%20-%20Cloud%20Run.ipynb)

Deploy the FastAPI feature serving app to [Cloud Run](https://cloud.google.com/run/docs/overview/what-is-cloud-run) — from local notebook demo to managed, autoscaling service with IAM authentication and revision-based traffic splitting.

**What you'll learn:**

*Deployment & auth:*
- Containerize a Storage Read API serving app for Cloud Run (Dockerfile, Cloud Build, Artifact Registry)
- Cloud Run authentication: ID tokens vs access tokens

*Serving patterns:*
- Per-entity batch: N concurrent ReadSessions via `asyncio.gather()`
- Combined-restriction batch: 1 ReadSession for all entities via `IN (...)` clause
- When each pattern wins — entity count is the decision variable

*Performance at scale:*
- Cold start, warm request, and Cloud Run network overhead
- Concurrency scaling: throughput vs latency tradeoff
- Sustained load testing: throughput plateau and latency degradation under production-like traffic
- Spike bursts: autoscaling response and recovery latency

*Operations:*
- Traffic splitting between feature configurations (revision-based canary)
- Autoscaling tuning: `max_instance_request_concurrency`, instance count, CPU allocation

| Part | Topic | Key Concepts |
|------|-------|-------------|
| 1. Feature Serving App | Container packaging | FastAPI app, `FeatureSessionPool`, per-entity + combined batch endpoints, `%%writefile` |
| 2. Local Verification | Pre-build testing | Environment variables, uvicorn in-notebook |
| 3. Build Container | Cloud Build + AR | Artifact Registry, Cloud Build API, Docker image |
| 4. Deploy to Cloud Run | Service creation | `run_v2`, env var config, scale-to-zero |
| 5. Authentication | IAM + ID tokens | `roles/run.invoker`, access tokens vs ID tokens |
| 6. Single-Entity Benchmarks | Cold/warm latency | Cold start, warm p50/p95, local vs Cloud Run |
| 7. Entity Count Scaling | Batch throughput | Per-entity vs combined batch, 1–100 entities, visualization |
| 8. Concurrent Scaling | Autoscaling + load | 1–50 workers, throughput saturation, sustained load ramp (1000 req), spike bursts (200 simultaneous) |
| 9. Sync vs Async | Four patterns | Sequential, concurrent, per-entity batch, combined batch comparison |
| 10. Serving Summary | All patterns | Comprehensive benchmark table + visualization |
| 11. Traffic Splitting | Canary deployment | Revision-based split, feature column rollout |
| 12. Autoscaling Config | Production settings | `min_instance_count`, `max_instance_request_concurrency` |

## Prerequisites

- A GCP project with billing enabled
- APIs enabled: BigQuery, BigQuery Storage
- Python >= 3.10

## Documentation

| Topic | Link |
|-------|------|
| BigQuery Storage Read API | [Reference](https://cloud.google.com/bigquery/docs/reference/storage) |
| Storage Read API Python client | [API reference](https://cloud.google.com/python/docs/reference/bigquerystorage/latest) |
| Apache Arrow | [Overview](https://arrow.apache.org/) |
| PyArrow | [Documentation](https://arrow.apache.org/docs/python/) |
| Table clustering | [Clustered tables](https://cloud.google.com/bigquery/docs/clustered-tables) |
| BigQuery time travel | [Historical queries](https://cloud.google.com/bigquery/docs/time-travel) |
| BigQuery pricing | [Pricing](https://cloud.google.com/bigquery/pricing) |
| Storage Read API pricing | [Free tier (300 TiB/mo)](https://cloud.google.com/bigquery/pricing#storage-api) |
| Cloud Run | [Overview](https://cloud.google.com/run/docs/overview/what-is-cloud-run) |
| Cloud Build | [Overview](https://cloud.google.com/build/docs/overview) |
| Artifact Registry | [Overview](https://cloud.google.com/artifact-registry/docs/overview) |
