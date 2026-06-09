![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2FMLOps%2FFeature+Store%2FBigtable&file=readme.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/MLOps/Feature%20Store/Bigtable/readme.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https://github.com/statmike/vertex-ai-mlops/blob/main/MLOps/Feature%2520Store/Bigtable/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https://github.com/statmike/vertex-ai-mlops/blob/main/MLOps/Feature%2520Store/Bigtable/readme.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https://github.com/statmike/vertex-ai-mlops/blob/main/MLOps/Feature%2520Store/Bigtable/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https://github.com/statmike/vertex-ai-mlops/blob/main/MLOps/Feature%2520Store/Bigtable/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
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
    <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/MLOps/Feature%20Store/Bigtable/readme.md"><img src="https://www.svgrepo.com/download/5445/download-button.svg" alt="Download icon" width="20px"></a> <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/MLOps/Feature%20Store/Bigtable/readme.md">Download File</a> <i>(right-click and "Save As")</i>
  </td>
</tr>
</table><br/><br/>

---
# Bigtable Feature Store

> You are here: `vertex-ai-mlops/MLOps/Feature Store/Bigtable/readme.md`

Cloud [Bigtable](https://cloud.google.com/bigtable/docs/overview) provides single-digit millisecond reads by row key, making it an ideal online serving layer for pre-computed ML features. This series builds a complete feature store on Bigtable, using BigQuery as the offline analytical engine — covering everything from first export to production operations.

> **Also in this series: [BigQuery Feature Store](../BigQuery/readme.md), [Spanner Feature Store](../Spanner/readme.md), [Valkey Feature Store](../Valkey/readme.md), and [Vertex AI Feature Store](../vertex/readme.md)**
>
> This Bigtable approach gives you **full control** over the online serving layer — direct writes, streaming ingestion, multi-region replication, custom serialization, and fine-grained tuning. For a **managed** alternative where Google handles the online store, sync, and feature registry, see [Vertex AI Feature Store](../vertex/readme.md). For **zero infrastructure** (serve straight from BigQuery at 20–200ms), see [BigQuery Feature Store](../BigQuery/readme.md). For **SQL + ACID transactions** at the serving layer, see [Spanner Feature Store](../Spanner/readme.md). For **sub-millisecond in-memory** serving with HNSW vector search, see [Valkey Feature Store](../Valkey/readme.md). All approaches use BigQuery as the offline store. See the [comparison table](../readme.md#choosing-an-approach) in the parent readme.

The data uses a compound entity key (`entity_group` + `entity_id`) with 130,000 entities and 200+ features spanning every BigQuery data type, designed to exercise every edge case of the BigQuery-to-Bigtable pipeline.

## Presentation

A 25-slide overview of this series — motivates the topic, walks through the architecture, and shows how all 15 notebooks fit together:

- [Bigtable Feature Store — Overview (PDF)](./Bigtable%20Feature%20Store%20-%20Overview.pdf)
- [Bigtable Feature Store — Overview (HTML)](./Bigtable%20Feature%20Store%20-%20Overview.html) — to view: click the link, then use the download button (↓) to save locally and open in your browser
- [Bigtable Feature Store — Overview (source)](./Bigtable%20Feature%20Store%20-%20Overview.md) — Marp markdown source

## Environment Setup

### Option 1: Local environment

From this directory (`MLOps/Feature Store/Bigtable/`):

**uv** (recommended)
```bash
uv sync
uv run python -m ipykernel install --user --name bigtable-feature-store --display-name "Bigtable Feature Store"
```

**pip**
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
python -m ipykernel install --user --name bigtable-feature-store --display-name "Bigtable Feature Store"
```

Then select the **Bigtable Feature Store** kernel in your notebook.

### Option 2: Standalone

Each notebook includes an environment setup cell that installs required packages into your current kernel.

## Teardown / Cleanup

The Bigtable instance bills continuously — **delete it when you're done.** Teardown is automated by `cleanup.py`, parameterized by a `cleanup.json` that the Environment notebook writes with this run's resource names (`cleanup.json` is gitignored).

From this directory (`MLOps/Feature Store/Bigtable/`):

```bash
# Dry run — show what would be deleted (default, safe)
uv run python cleanup.py

# Delete the Bigtable instance (clears the NB5 change stream first, then deletes clusters + tables)
uv run python cleanup.py --yes

# Also delete the BigQuery dataset (kept by default — it's cheap and reusable)
uv run python cleanup.py --yes --include-dataset

# Verify no continuous queries are still running (lists running BQ jobs; deletes nothing)
uv run python cleanup.py --check-jobs
```

`cleanup.py` defaults to a dry run and is idempotent (already-deleted resources are reported, not errored). The **Bigtable instance is the main cost**; the BigQuery dataset is kept by default. Pub/Sub topics/subscriptions from notebooks 3, 5, and 9 clean up after themselves. Run the Environment notebook at least once first so `cleanup.json` exists.

Several notebooks demonstrate **`EXPORT DATA` reservations** and **continuous queries** that are designed to be created and torn down within the notebook run — so the teardown script doesn't manage them. `--check-jobs` lists any BigQuery jobs still in the `RUNNING` state so you can confirm none leaked; if one did, stop it with `bq cancel <job_id>`.

## Key Concepts

- **[EXPORT DATA](https://cloud.google.com/bigquery/docs/export-to-bigtable)** — BigQuery's native mechanism for writing query results directly to Bigtable. This is the primary bridge between the offline analytical layer and the online serving layer.
- **[Column Family](https://cloud.google.com/bigtable/docs/schema-design#column-families)** — Physical storage unit in Bigtable; features within the same family are stored together on disk. Column family design affects read performance, garbage collection policy, and access control.
- **[Row Key](https://cloud.google.com/bigtable/docs/schema-design)** — The single index for Bigtable reads; row key design determines performance and data locality. Bigtable stores rows in lexicographic order, so key structure controls how data is distributed across nodes.
- **Self-Describing Schema** — A metadata row (`#schema`) that stores the column layout so clients can decode feature values without hardcoded schemas. Enables generic serving code that adapts to schema changes automatically.
- **[App Profile](https://cloud.google.com/bigtable/docs/app-profiles)** — Controls request routing to Bigtable clusters; separate profiles for serving (HIGH priority) vs export (LOW priority) prevent batch workloads from degrading online latency.
- **[Cell Versioning](https://cloud.google.com/bigtable/docs/garbage-collection)** — Each cell can store multiple timestamped values, enabling point-in-time feature retrieval. Combined with garbage collection policies, this provides automatic history management.
- **Serialization** — How BigQuery data types (arrays, structs, JSON, geography) are encoded into Bigtable's byte-oriented cells. The choice of serialization method affects storage size, read latency, and client-side complexity.

## Notebooks

### 0. [Bigtable Feature Store — Environment](./Bigtable%20Feature%20Store%20-%20Environment.ipynb)

Creates the BigQuery dataset (dense + sparse tables with 200+ features across all data types) and provisions the Bigtable instance. Run this first — all subsequent notebooks depend on the resources created here.

**What you'll learn:**
- Generate synthetic feature data covering every BigQuery data type (INT64, FLOAT64, STRING, ARRAY, STRUCT, JSON, GEOGRAPHY, etc.)
- Create dense (1 row per entity) and sparse (time-series) tables for different feature patterns
- Provision a [Bigtable instance](https://cloud.google.com/bigtable/docs/instances-clusters-nodes) with SSD storage and configure initial cluster sizing
- Set up [app profiles](https://cloud.google.com/bigtable/docs/app-profiles) for separating serving and batch traffic

### 1. [Bigtable Feature Store — Fundamentals](./Bigtable%20Feature%20Store%20-%20Fundamentals.ipynb)

End-to-end flow from BigQuery to Bigtable to serving. This is the "hello world" of the series — after this notebook you'll have features in Bigtable and a working read path.

**What you'll learn:**
- Use [`EXPORT DATA`](https://cloud.google.com/bigquery/docs/export-to-bigtable) to push BigQuery query results directly into Bigtable
- Store a self-describing schema row (`#schema`) so clients can decode without hardcoded column maps
- Read features by row key using the Python client library
- Measure and compare read latency: single-row lookups, multi-row reads, filtered reads
- Visualize how data distributes across entity groups

### 2. [Bigtable Feature Store — Serialization](./Bigtable%20Feature%20Store%20-%20Serialization.ipynb)

Five serialization methods compared head-to-head: native column mapping, JSON casting, concatenation with delimiters, Protocol Buffers, and a hybrid approach. Each method is benchmarked for storage size and read latency.

**What you'll learn:**
- Native mapping: one BigQuery column per Bigtable qualifier, with a metadata column family for type information
- JSON casting: store entire feature sets as JSON strings — quick to implement, expensive to parse
- Concatenation: `CONCAT` with delimiters for single-column reads, plus the delimiter trap for data integrity
- [Protocol Buffers](https://cloud.google.com/bigtable/docs/query-protobuf-data): compile BigQuery rows into binary blobs with embedded `FileDescriptorSet` for self-description
- Hybrid: native columns for high-frequency features, protobuf blob for the long tail
- Storage size comparison across all five methods
- Read latency breakdown: network transfer time vs client-side deserialization CPU time

### 3. [Bigtable Feature Store — Synchronization](./Bigtable%20Feature%20Store%20-%20Synchronization.ipynb)

Keeping Bigtable in sync with BigQuery — from one-time backfills to continuous streaming. Covers reservation management for `EXPORT DATA` and streaming pipeline patterns.

**What you'll learn:**
- One-time sync: manual `EXPORT DATA` for initial load and backfilling
- Scheduled sync: BigQuery scheduled queries and Data Transfer Service for periodic refreshes
- Continuous sync: [continuous queries](https://cloud.google.com/bigquery/docs/continuous-queries-introduction) with `APPENDS()` for near-real-time feature propagation, plus streaming pipeline patterns via Pub/Sub
- [BigQuery reservation](https://cloud.google.com/bigquery/docs/reservations-intro) management: dedicated slots for export jobs to avoid contention
- Post-export validation: row count comparison, sample verification, and schema consistency checks
- [Data Boost](https://cloud.google.com/bigtable/docs/data-boost-overview): serverless batch reads for training export and analytics without impacting serving
- [Continuous materialized views](https://cloud.google.com/bigtable/docs/continuous-materialized-views) (Preview): pre-computed aggregations within Bigtable using GoogleSQL, automatically updated as source data changes
- Measure propagation latency across all three sync patterns
- The freshness trade-off: cost vs latency for each synchronization strategy

### 4. [Bigtable Feature Store — History and Time Travel](./Bigtable%20Feature%20Store%20-%20History%20and%20Time%20Travel.ipynb)

Two strategies for storing feature history — key-based (`entity_id#timestamp`) vs cell versioning — and how to use each for point-in-time joins when building training datasets.

**What you'll learn:**
- Key-based history: embed timestamps in row keys for range scans over feature history
- [Cell versioning](https://cloud.google.com/bigtable/docs/garbage-collection): multiple timestamped values per cell with automatic garbage collection (max versions)
- Trade-offs: key-based enables range scans but requires manual GC; cell versioning is cleaner but limits query patterns
- Point-in-time joins: retrieve features as they existed at a specific timestamp using Bigtable filters
- Training data extraction: build label-aligned feature snapshots for ML training pipelines
- Garbage collection policies: configure per-column-family retention rules

### 5. [Bigtable Feature Store — Streaming and Direct Writes](./Bigtable%20Feature%20Store%20-%20Streaming%20and%20Direct%20Writes.ipynb)

Bypass BigQuery entirely for high-frequency feature updates — direct writes, batch mutations, atomic operations, and change streams for downstream consumers.

**What you'll learn:**
- Direct writes: update streaming features (e.g., clicks in the last 30 seconds) without round-tripping through BigQuery
- Batch mutations: group multiple writes into a single RPC for throughput
- Atomic read-modify-write and check-and-mutate operations for consistent feature updates
- [Change streams](https://cloud.google.com/bigtable/docs/change-streams-overview): capture mutations in real time for downstream consumers or BigQuery backfill
- Dual-write architectures: App to Pub/Sub to both Bigtable and BigQuery vs App to Bigtable with change stream to BigQuery
- Idempotency patterns: ensure retries don't create duplicate versions or incorrect feature states

### 6. [Bigtable Feature Store — Key Design and Organization](./Bigtable%20Feature%20Store%20-%20Key%20Design%20and%20Organization.ipynb)

Row key patterns, hotspot avoidance, prefix scans, column family strategy, and the Key Visualizer — everything that determines whether your feature store runs at single-digit milliseconds or falls over under load.

**What you'll learn:**
- Row key design patterns: compound keys, key namespacing (`USER#123` vs `PROD#456`), salted keys
- Hotspot avoidance: why sequential keys are dangerous and how to distribute load across nodes
- Prefix scans: design keys so related entities can be retrieved in a single range scan
- Column family strategy: group features by access pattern, update frequency, and garbage collection policy
- The "single table" philosophy: managing multiple feature groups in one table using column families
- Key Visualizer deep dive: identify hot rows, sequential key patterns, and uneven data distribution

### 7. [Bigtable Feature Store — Schema Evolution and Operations](./Bigtable%20Feature%20Store%20-%20Schema%20Evolution%20and%20Operations.ipynb)

Maintaining the feature store over time — versioned schemas, backfilling without downtime, monitoring, app profiles, cost optimization, and a production readiness checklist.

**What you'll learn:**
- Versioned schemas: what happens when a feature is dropped, renamed, or changes type
- Versioned schemas: use feature metadata columns to tell the serving app how to decode each payload version
- Feature registry: centralized metadata row (`#registry`) for feature discovery, ownership tracking, lineage, and freshness SLA compliance
- Backfilling: update historical features in Bigtable without interrupting live inference traffic
- Monitoring: Cloud Monitoring for disk utilization, CPU, and throughput; alerting on degradation
- App profiles in production: single-cluster routing for consistency vs multi-cluster routing for availability
- Cost optimization: node scaling based on throughput, SSD vs HDD (spoiler: SSD for feature stores), committed use discounts
- Security & IAM: least-privilege roles (`bigtable.reader`/`user`/`admin`), VPC Service Controls, CMEK
- [Authorized views](https://cloud.google.com/bigtable/docs/authorized-views-overview): row-level and column-family-level access control without data duplication
- Autoscaling & capacity planning: CPU targets, node estimation, production vs development instances
- Production checklist: replication, backup, access control, and operational runbook

### 8. [Bigtable Feature Store — Serving Integration](./Bigtable%20Feature%20Store%20-%20Serving%20Integration.ipynb)

The "so what" notebook — train a model on features from BigQuery, serve predictions from Bigtable, and measure end-to-end latency. Demonstrates five read methods, a FastAPI serving application, and schema evolution during live serving.

**What you'll learn:**
- Train a simple model on features queried from BigQuery
- Read features from Bigtable at inference time and measure the latency breakdown (read → decode → predict)
- Five read methods compared: [Python client](https://cloud.google.com/python/docs/reference/bigtable/latest), [`cbt` CLI](https://cloud.google.com/bigtable/docs/cbt-overview), [GoogleSQL](https://cloud.google.com/bigtable/docs/googlesql-overview), [BigQuery external tables](https://cloud.google.com/bigquery/docs/bigtable-options), and REST/gRPC
- Build a [FastAPI](https://fastapi.tiangolo.com/) serving endpoint: receive request → read features → predict → respond
- Connection pooling, [app profiles](https://cloud.google.com/bigtable/docs/app-profiles) for serving priority, feature freshness gating, and Cloud Run deployment patterns
- Training-serving skew detection: compare features from BigQuery (training) vs Bigtable (serving) to catch precision loss and staleness
- Schema evolution during live serving: backfill rows and switch schema versions with zero errors and no latency degradation
- End-to-end latency analysis under concurrent load

### 9. [Bigtable Feature Store — Dynamic Features](./Bigtable%20Feature%20Store%20-%20Dynamic%20Features.ipynb)

Real-time feature computation at serving time — what happens when a new event arrives and the model needs features that depend on both the event and pre-computed values in Bigtable.

**What you'll learn:**
- The staleness problem: why pre-computed features become wrong the moment a new event arrives
- Pattern 1 — [Read-Modify-Write](https://cloud.google.com/bigtable/docs/writes#read-modify-write): atomic counters and running sums updated on every event
- Pattern 2 — Read + Compute: read stored features, combine with new event data at serve time (zero infrastructure overhead)
- Pattern 3 — Streaming Aggregation: [Pub/Sub](https://cloud.google.com/pubsub/docs/overview) → subscriber → Bigtable for complex aggregations
- Latency comparison across all three patterns with visualizations
- Combining patterns in production: batch features + atomic counters + serve-time computation in a single Bigtable read

### 10. [Bigtable Feature Store — Vector Storage and KNN Search](./Bigtable%20Feature%20Store%20-%20Vector%20Storage%20and%20KNN%20Search.ipynb)

Store embedding vectors in Bigtable and query for nearest neighbors using GoogleSQL. Bigtable supports brute-force KNN — no index required, but query time scales linearly with table size.

**What you'll learn:**
- Vector encoding: raw binary float32 in a standalone column (`struct.pack` / `struct.unpack`)
- Why vectors must be standalone columns — `TO_VECTOR32()` requires raw bytes, not protobuf or JSON
- KNN search with `COSINE_DISTANCE()` and `EUCLIDEAN_DISTANCE()` via [GoogleSQL](https://cloud.google.com/bigtable/docs/googlesql-overview)
- Performance benchmarks: latency vs table size and vector dimensionality
- Combining vectors with scalar features in a single table and row
- When Bigtable KNN is sufficient vs when to use a dedicated vector database

### 11. [Bigtable Feature Store — Replication](./Bigtable%20Feature%20Store%20-%20Replication.ipynb)

Multi-cluster [replication](https://cloud.google.com/bigtable/docs/replication-overview) for high availability and disaster recovery. Creates a separate Production instance (Development instances cannot replicate), demonstrates replication behavior, and cleans up.

**What you'll learn:**
- Create a Production instance with two clusters in different zones
- App profiles for replication: multi-cluster routing (automatic failover) vs single-cluster routing (strong consistency)
- Measure replication lag between clusters
- Failover patterns: automatic vs manual
- Replication topology: single-zone, multi-zone, multi-region
- Cost implications of multi-cluster deployments

### 12. [Bigtable Feature Store — Emulator](./Bigtable%20Feature%20Store%20-%20Emulator.ipynb)

Set up and use the [Bigtable emulator](https://cloud.google.com/bigtable/docs/emulator) for local development and CI/CD testing — no GCP project or billing required.

**What you'll learn:**
- Start the emulator: `gcloud beta emulators bigtable start`
- What the emulator supports and doesn't (no GoogleSQL, no admin API, no replication, no persistence)
- Connect with the same Python client code used against production
- Testing patterns: pytest fixtures, GitHub Actions, Cloud Build
- Conditional test skipping for GoogleSQL-dependent features

### 13. [Bigtable Feature Store — Production Deployment](./Bigtable%20Feature%20Store%20-%20Production%20Deployment.ipynb)

Deploy a complete feature store with [Terraform](https://www.terraform.io/) and read features from Go, Java, and Node.js — the two enterprise fundamentals missing from a notebook-only Python workflow.

**What you'll learn:**
- Install Terraform and write a complete configuration: instance, table, column families, GC policies, app profiles
- The `init → plan → apply` workflow: see exactly what Terraform will create before it creates anything
- Manage infrastructure changes: add a column family via Terraform, review the diff, apply
- [Go client](https://pkg.go.dev/cloud.google.com/go/bigtable): gRPC-native, compiled, ideal for high-throughput serving
- [Java client](https://cloud.google.com/java/docs/reference/google-cloud-bigtable/latest/overview): enterprise-grade, Maven-based
- [Node.js client](https://cloud.google.com/nodejs/docs/reference/bigtable/latest): async/await, serverless-friendly
- `terraform destroy`: one command removes all infrastructure — no orphaned resources

### 14. [Bigtable Feature Store — Recommendation Engine](./Bigtable%20Feature%20Store%20-%20Recommendation%20Engine.ipynb)

The capstone notebook — a fully self-contained two-stage recommendation system that ties together patterns from across the entire series. Creates its own table, generates its own data, trains its own model, and cleans up everything at the end.

**What you'll learn:**
- Multi-entity table design: users, items, and metadata in a single table using [key namespacing](./Bigtable%20Feature%20Store%20-%20Key%20Design%20and%20Organization.ipynb) (`USER#`, `ITEM#`)
- 64-dimensional [vector embeddings](./Bigtable%20Feature%20Store%20-%20Vector%20Storage%20and%20KNN%20Search.ipynb) for candidate retrieval via brute-force KNN
- [Atomic counters](./Bigtable%20Feature%20Store%20-%20Dynamic%20Features.ipynb) for real-time interaction tracking (views, clicks, purchases)
- [Streaming event ingestion](./Bigtable%20Feature%20Store%20-%20Streaming%20and%20Direct%20Writes.ipynb) via Pub/Sub → Bigtable counter updates
- Two-stage recommendation: KNN retrieval (500 → 50 candidates) followed by RandomForest ranking (50 → top 10)
- [FastAPI serving endpoint](./Bigtable%20Feature%20Store%20-%20Serving%20Integration.ipynb) with concurrent load testing and latency breakdown
- Feature freshness experiment: how stale embeddings cause recommendation drift

## Notebook Comparison

| Notebook | Focus | Key Topics |
|----------|-------|------------|
| [Environment](./Bigtable%20Feature%20Store%20-%20Environment.ipynb) | Setup | BQ data generation, Bigtable instance, data type coverage |
| [Fundamentals](./Bigtable%20Feature%20Store%20-%20Fundamentals.ipynb) | End-to-end | EXPORT DATA, schema metadata, latency benchmark |
| [Serialization](./Bigtable%20Feature%20Store%20-%20Serialization.ipynb) | Encoding | Native, JSON, concat, protobuf, hybrid; storage and latency benchmarks |
| [Synchronization](./Bigtable%20Feature%20Store%20-%20Synchronization.ipynb) | Data freshness | One-time, scheduled, continuous sync; reservation management; Data Boost; continuous materialized views (Preview) |
| [History and Time Travel](./Bigtable%20Feature%20Store%20-%20History%20and%20Time%20Travel.ipynb) | Temporal features | Key-based vs cell versioning, point-in-time joins, TTL/feature freshness, training data |
| [Streaming and Direct Writes](./Bigtable%20Feature%20Store%20-%20Streaming%20and%20Direct%20Writes.ipynb) | Write path | Direct writes, batch mutations, change streams, dual-write |
| [Key Design and Organization](./Bigtable%20Feature%20Store%20-%20Key%20Design%20and%20Organization.ipynb) | Data modeling | Row key patterns, hotspot avoidance, column family strategy |
| [Schema Evolution and Operations](./Bigtable%20Feature%20Store%20-%20Schema%20Evolution%20and%20Operations.ipynb) | Production | Versioned schemas, feature registry, backfilling, monitoring, security/IAM, authorized views, autoscaling, cost optimization |
| [Serving Integration](./Bigtable%20Feature%20Store%20-%20Serving%20Integration.ipynb) | Application | Model training, feature serving, multi-language reads, FastAPI endpoint, training-serving skew, feature freshness, live schema evolution |
| [Dynamic Features](./Bigtable%20Feature%20Store%20-%20Dynamic%20Features.ipynb) | Real-time | Atomic counters, read+compute, streaming aggregation, pattern comparison |
| [Vector Storage and KNN Search](./Bigtable%20Feature%20Store%20-%20Vector%20Storage%20and%20KNN%20Search.ipynb) | Embeddings | Vector encoding, cosine/euclidean distance, brute-force KNN, performance benchmarks |
| [Replication](./Bigtable%20Feature%20Store%20-%20Replication.ipynb) | High availability | Multi-cluster setup, app profiles, replication lag, failover patterns |
| [Emulator](./Bigtable%20Feature%20Store%20-%20Emulator.ipynb) | Local dev | Emulator setup, testing patterns, CI/CD, limitations |
| [Production Deployment](./Bigtable%20Feature%20Store%20-%20Production%20Deployment.ipynb) | Enterprise | Terraform IaC, Go/Java/Node.js clients, infrastructure lifecycle |
| [Recommendation Engine](./Bigtable%20Feature%20Store%20-%20Recommendation%20Engine.ipynb) | Capstone | Multi-entity table, vector KNN, atomic counters, streaming, two-stage ranking, FastAPI, freshness |

## Topic Map

Some topics span multiple notebooks. Use this map to find all coverage of a topic:

| Topic | Notebooks |
|-------|-----------|
| Schema design & metadata | [NB1](./Bigtable%20Feature%20Store%20-%20Fundamentals.ipynb), [NB6](./Bigtable%20Feature%20Store%20-%20Key%20Design%20and%20Organization.ipynb), [NB7](./Bigtable%20Feature%20Store%20-%20Schema%20Evolution%20and%20Operations.ipynb) |
| Row key design | [NB0](./Bigtable%20Feature%20Store%20-%20Environment.ipynb), [NB1](./Bigtable%20Feature%20Store%20-%20Fundamentals.ipynb), [NB6](./Bigtable%20Feature%20Store%20-%20Key%20Design%20and%20Organization.ipynb) |
| Serialization & encoding | [NB1](./Bigtable%20Feature%20Store%20-%20Fundamentals.ipynb), [NB2](./Bigtable%20Feature%20Store%20-%20Serialization.ipynb), [NB8](./Bigtable%20Feature%20Store%20-%20Serving%20Integration.ipynb) |
| Data sync (BQ → Bigtable) | [NB1](./Bigtable%20Feature%20Store%20-%20Fundamentals.ipynb), [NB3](./Bigtable%20Feature%20Store%20-%20Synchronization.ipynb), [NB5](./Bigtable%20Feature%20Store%20-%20Streaming%20and%20Direct%20Writes.ipynb) |
| Schema evolution & versioning | [NB7](./Bigtable%20Feature%20Store%20-%20Schema%20Evolution%20and%20Operations.ipynb), [NB8](./Bigtable%20Feature%20Store%20-%20Serving%20Integration.ipynb) |
| GC policies & TTL | [NB4](./Bigtable%20Feature%20Store%20-%20History%20and%20Time%20Travel.ipynb), [NB7](./Bigtable%20Feature%20Store%20-%20Schema%20Evolution%20and%20Operations.ipynb) |
| Feature freshness | [NB4](./Bigtable%20Feature%20Store%20-%20History%20and%20Time%20Travel.ipynb), [NB8](./Bigtable%20Feature%20Store%20-%20Serving%20Integration.ipynb), [NB14](./Bigtable%20Feature%20Store%20-%20Recommendation%20Engine.ipynb) |
| App profiles & routing | [NB7](./Bigtable%20Feature%20Store%20-%20Schema%20Evolution%20and%20Operations.ipynb), [NB8](./Bigtable%20Feature%20Store%20-%20Serving%20Integration.ipynb), [NB11](./Bigtable%20Feature%20Store%20-%20Replication.ipynb) |
| Monitoring & alerting | [NB7](./Bigtable%20Feature%20Store%20-%20Schema%20Evolution%20and%20Operations.ipynb) |
| Security & IAM | [NB7](./Bigtable%20Feature%20Store%20-%20Schema%20Evolution%20and%20Operations.ipynb) |
| Autoscaling & capacity | [NB7](./Bigtable%20Feature%20Store%20-%20Schema%20Evolution%20and%20Operations.ipynb) |
| Cost optimization | [NB7](./Bigtable%20Feature%20Store%20-%20Schema%20Evolution%20and%20Operations.ipynb) |
| Latency benchmarking | [NB1](./Bigtable%20Feature%20Store%20-%20Fundamentals.ipynb), [NB2](./Bigtable%20Feature%20Store%20-%20Serialization.ipynb), [NB8](./Bigtable%20Feature%20Store%20-%20Serving%20Integration.ipynb), [NB9](./Bigtable%20Feature%20Store%20-%20Dynamic%20Features.ipynb) |
| Feature history (key-based vs cell versioning) | [NB4](./Bigtable%20Feature%20Store%20-%20History%20and%20Time%20Travel.ipynb), [NB6](./Bigtable%20Feature%20Store%20-%20Key%20Design%20and%20Organization.ipynb) |
| Point-in-time joins | [NB4](./Bigtable%20Feature%20Store%20-%20History%20and%20Time%20Travel.ipynb) |
| Real-time / streaming features | [NB5](./Bigtable%20Feature%20Store%20-%20Streaming%20and%20Direct%20Writes.ipynb), [NB9](./Bigtable%20Feature%20Store%20-%20Dynamic%20Features.ipynb), [NB14](./Bigtable%20Feature%20Store%20-%20Recommendation%20Engine.ipynb) |
| Model serving | [NB8](./Bigtable%20Feature%20Store%20-%20Serving%20Integration.ipynb), [NB9](./Bigtable%20Feature%20Store%20-%20Dynamic%20Features.ipynb), [NB14](./Bigtable%20Feature%20Store%20-%20Recommendation%20Engine.ipynb) |
| Training-serving skew | [NB8](./Bigtable%20Feature%20Store%20-%20Serving%20Integration.ipynb) |
| Data Boost (batch reads) | [NB3](./Bigtable%20Feature%20Store%20-%20Synchronization.ipynb) |
| Vector storage / KNN search | [NB10](./Bigtable%20Feature%20Store%20-%20Vector%20Storage%20and%20KNN%20Search.ipynb), [NB14](./Bigtable%20Feature%20Store%20-%20Recommendation%20Engine.ipynb) |
| Multi-cluster replication | [NB7](./Bigtable%20Feature%20Store%20-%20Schema%20Evolution%20and%20Operations.ipynb), [NB11](./Bigtable%20Feature%20Store%20-%20Replication.ipynb) |
| Emulator / local dev | [NB7](./Bigtable%20Feature%20Store%20-%20Schema%20Evolution%20and%20Operations.ipynb), [NB12](./Bigtable%20Feature%20Store%20-%20Emulator.ipynb) |
| Feature registry / catalog | [NB7](./Bigtable%20Feature%20Store%20-%20Schema%20Evolution%20and%20Operations.ipynb) |
| Continuous materialized views | [NB3](./Bigtable%20Feature%20Store%20-%20Synchronization.ipynb) |
| Authorized views | [NB7](./Bigtable%20Feature%20Store%20-%20Schema%20Evolution%20and%20Operations.ipynb) |
| Terraform / IaC | [NB7](./Bigtable%20Feature%20Store%20-%20Schema%20Evolution%20and%20Operations.ipynb), [NB13](./Bigtable%20Feature%20Store%20-%20Production%20Deployment.ipynb) |
| Multi-language clients (Go, Java, Node.js) | [NB8](./Bigtable%20Feature%20Store%20-%20Serving%20Integration.ipynb), [NB13](./Bigtable%20Feature%20Store%20-%20Production%20Deployment.ipynb) |
| Recommendation engine (capstone) | [NB14](./Bigtable%20Feature%20Store%20-%20Recommendation%20Engine.ipynb) |

## Prerequisites

- A GCP project with billing enabled
- APIs enabled: BigQuery, BigQuery Reservation, BigQuery Data Transfer, Bigtable, Bigtable Admin, Pub/Sub, Cloud Monitoring (all enabled by Notebook 0)
- Python >= 3.10 with the packages listed in [`pyproject.toml`](./pyproject.toml)
- Each notebook includes its own setup cells — no pre-configuration needed beyond a GCP project

## Documentation

### Bigtable

| Topic | Link |
|-------|------|
| Overview | [Cloud Bigtable overview](https://cloud.google.com/bigtable/docs/overview) |
| Instances, clusters, nodes | [Instance architecture](https://cloud.google.com/bigtable/docs/instances-clusters-nodes) |
| Schema design | [Best practices](https://cloud.google.com/bigtable/docs/schema-design) |
| Row key design for time series | [Time series schema](https://cloud.google.com/bigtable/docs/schema-design-time-series) |
| Column families | [Column family design](https://cloud.google.com/bigtable/docs/schema-design#column-families) |
| Reads | [Reading data](https://cloud.google.com/bigtable/docs/reads) |
| Writes | [Writing data](https://cloud.google.com/bigtable/docs/writes) |
| Filters | [Using filters](https://cloud.google.com/bigtable/docs/using-filters) |
| Garbage collection | [GC policies](https://cloud.google.com/bigtable/docs/garbage-collection) |
| App profiles | [Routing & isolation](https://cloud.google.com/bigtable/docs/app-profiles) |
| Replication | [Multi-cluster replication](https://cloud.google.com/bigtable/docs/replication-overview) |
| Change streams | [Stream mutations](https://cloud.google.com/bigtable/docs/change-streams-overview) |
| Monitoring | [Instance monitoring](https://cloud.google.com/bigtable/docs/monitoring-instance) |
| Key Visualizer | [Visualize access patterns](https://cloud.google.com/bigtable/docs/keyvis-overview) |
| GoogleSQL for Bigtable | [SQL queries on Bigtable](https://cloud.google.com/bigtable/docs/googlesql-overview) |
| Protobuf queries | [Query protobuf data](https://cloud.google.com/bigtable/docs/query-protobuf-data) |
| Client libraries | [All languages](https://cloud.google.com/bigtable/docs/reference/libraries) |
| Python client | [API reference](https://cloud.google.com/python/docs/reference/bigtable/latest) |
| `cbt` CLI | [Command-line tool](https://cloud.google.com/bigtable/docs/cbt-overview) |
| Pricing | [Pricing & CUDs](https://cloud.google.com/bigtable/pricing) |

### BigQuery (offline store)

| Topic | Link |
|-------|------|
| EXPORT DATA to Bigtable | [Export guide](https://cloud.google.com/bigquery/docs/export-to-bigtable) |
| Data type mappings (BQ → Bigtable) | [Type mapping reference](https://cloud.google.com/bigquery/docs/export-to-bigtable#data-type-mappings) |
| EXPORT DATA statement | [SQL reference](https://cloud.google.com/bigquery/docs/reference/standard-sql/other-statements#export_data_statement) |
| Reservations | [Reservation concepts](https://cloud.google.com/bigquery/docs/reservations-intro) |
| Editions | [Enterprise edition](https://cloud.google.com/bigquery/docs/editions-intro) |
| Continuous queries | [Real-time sync](https://cloud.google.com/bigquery/docs/continuous-queries-introduction) |
| Scheduled queries | [Periodic sync](https://cloud.google.com/bigquery/docs/scheduling-queries) |
| ML.FEATURES_AT_TIME | [Point-in-time features](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-feature-time) |
| ML.ENTITY_FEATURES_AT_TIME | [Entity-level PIT](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-entity-feature-time) |
| Data types | [Type reference](https://cloud.google.com/bigquery/docs/reference/standard-sql/data-types) |
| Time travel | [Historical queries](https://cloud.google.com/bigquery/docs/time-travel) |
