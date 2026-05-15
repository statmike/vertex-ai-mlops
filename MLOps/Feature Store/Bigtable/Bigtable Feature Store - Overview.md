---
marp: true
theme: default
paginate: true
style: |
  section {
    font-family: 'Segoe UI', Arial, sans-serif;
    padding-bottom: 80px;
  }
  section.title {
    text-align: center;
    justify-content: center;
  }
  section.title h1 {
    font-size: 2.2em;
  }
  .notebook-ref {
    position: absolute;
    bottom: 30px;
    left: 40px;
    right: 40px;
    background: #e8e8e8;
    color: #555;
    font-size: 13px;
    padding: 6px 16px;
    border-radius: 4px;
  }
  .diagram {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0;
  }
  .box {
    border: 2px solid #333;
    border-radius: 8px;
    padding: 12px 20px;
    text-align: center;
    font-size: 0.85em;
    background: #fff;
    min-width: 120px;
  }
  .box-blue {
    border-color: #4285F4;
    background: #e8f0fe;
  }
  .box-green {
    border-color: #34A853;
    background: #e6f4ea;
  }
  .box-orange {
    border-color: #F9AB00;
    background: #fef7e0;
  }
  .box-red {
    border-color: #EA4335;
    background: #fce8e6;
  }
  .box-purple {
    border-color: #9334E6;
    background: #f3e8fd;
  }
  .box-grey {
    border-color: #999;
    background: #f5f5f5;
  }
  .arrow {
    font-size: 1.5em;
    color: #555;
    margin: 0 8px;
  }
  .arrow-down {
    font-size: 1.5em;
    color: #555;
    text-align: center;
    margin: 4px 0;
  }
  .small {
    font-size: 0.75em;
    color: #666;
  }
  .columns {
    display: flex;
    gap: 30px;
  }
  .col {
    flex: 1;
  }
  table {
    font-size: 0.8em;
  }
  .four-col {
    display: flex !important;
    flex-direction: row !important;
    gap: 12px;
    font-size: 0.72em;
  }
  .four-col > div {
    flex: 1;
  }
---

<!-- _class: title -->
<!-- _paginate: false -->

# Bigtable Feature Store

### 15 notebooks from first export to production recommendation engine

<br>

BigQuery as the offline store | Bigtable for sub-10ms online serving

<br>

<div class="small">

github.com/statmike/vertex-ai-mlops/MLOps/Feature Store/Bigtable

</div>

---

## The Feature Store Problem

**Training** and **serving** have fundamentally different performance requirements.

<div class="diagram" style="margin-top: 40px;">
<div class="box box-blue">
<strong>Training</strong><br>
BigQuery<br>
<span class="small">Full table scans<br>Seconds to minutes</span>
</div>
<div style="text-align:center; margin: 0 30px;">
<div class="small" style="margin-bottom: 4px;">same features</div>
<div class="small" style="margin-bottom: 4px;">different latency</div>
</div>
<div class="box box-green">
<strong>Serving</strong><br>
Bigtable<br>
<span class="small">Single-row lookups<br>Single-digit ms</span>
</div>
</div>

<br>

A **feature store** bridges this gap: features are computed once in BigQuery, exported to Bigtable, and served at low latency for real-time inference.

---

## Why Bigtable?

<div class="columns">
<div class="col">

**Core properties**
- Sorted key-value store
- Single-digit ms reads by row key
- Column families for physical data grouping
- Cell versioning with automatic GC
- Scales to petabytes, billions of rows

</div>
<div class="col">

**For feature stores specifically**
- Direct write path (bypass BigQuery)
- Streaming ingestion via Pub/Sub
- Multi-cluster replication (HA + geo)
- App profiles for traffic isolation
- Native `EXPORT DATA` from BigQuery

</div>
</div>

<div class="notebook-ref">NB0: Environment</div>

---

## Series Overview

<div class="four-col">

<div>
<div class="box box-blue" style="margin-bottom: 8px; padding: 8px;">
<strong>Foundation</strong>
</div>
<div style="padding: 0 8px; line-height: 1.6;">
NB0 &middot; Environment<br>
NB1 &middot; Fundamentals<br>
NB2 &middot; Serialization<br>
NB3 &middot; Synchronization<br>
NB4 &middot; History & Time Travel
</div>
</div>

<div>
<div class="box box-green" style="margin-bottom: 8px; padding: 8px;">
<strong>Data Patterns</strong>
</div>
<div style="padding: 0 8px; line-height: 1.6;">
NB5 &middot; Streaming & Writes<br>
NB6 &middot; Key Design<br>
NB7 &middot; Schema & Ops<br>
NB9 &middot; Dynamic Features<br>
NB10 &middot; Vectors & KNN
</div>
</div>

<div>
<div class="box box-orange" style="margin-bottom: 8px; padding: 8px;">
<strong>Serving</strong>
</div>
<div style="padding: 0 8px; line-height: 1.6;">
NB8 &middot; Serving Integration<br>
NB11 &middot; Replication<br>
NB12 &middot; Emulator<br>
NB13 &middot; Production Deploy
</div>
</div>

<div>
<div class="box box-red" style="margin-bottom: 8px; padding: 8px;">
<strong>Capstone</strong>
</div>
<div style="padding: 0 8px; line-height: 1.6;">
NB14 &middot; Recommendation<br>
<span class="small">Ties all patterns together<br>into a complete system</span>
</div>
</div>

</div>

<div class="notebook-ref">All notebooks (NB0 &ndash; NB14)</div>

---

## Architecture

<div style="text-align: center; margin-top: 20px;">

<div class="diagram">
<div class="box box-blue" style="min-width: 160px;">
<strong>BigQuery</strong><br>
<span class="small">Offline store<br>Training data, analytics</span>
</div>
<div style="text-align: center; margin: 0 10px;">
<div style="font-size: 0.75em; color: #4285F4;">EXPORT DATA</div>
<div class="arrow">&rarr;</div>
</div>
<div class="box box-green" style="min-width: 160px;">
<strong>Bigtable</strong><br>
<span class="small">Online store<br>Sub-10ms feature reads</span>
</div>
<div style="text-align: center; margin: 0 10px;">
<div style="font-size: 0.75em; color: #34A853;">read</div>
<div class="arrow">&rarr;</div>
</div>
<div class="box box-orange" style="min-width: 160px;">
<strong>Serving App</strong><br>
<span class="small">FastAPI / Cloud Run<br>Read &rarr; Predict &rarr; Respond</span>
</div>
</div>

<div class="arrow-down">&uarr;</div>

<div class="diagram" style="margin-top: 0px;">
<div class="box box-purple" style="min-width: 160px;">
<strong>Applications</strong><br>
<span class="small">Direct writes, atomic ops<br>Pub/Sub streaming</span>
</div>
<div style="text-align: center; margin: 0 10px;">
<div style="font-size: 0.75em; color: #9334E6;">write</div>
<div class="arrow">&rarr;</div>
</div>
<div class="box box-green" style="min-width: 160px;">
<strong>Bigtable</strong><br>
<span class="small">Real-time features<br>Atomic counters</span>
</div>
</div>

</div>

<div class="notebook-ref">NB1: Fundamentals, NB3: Synchronization, NB5: Streaming & Direct Writes</div>

---

## First Export: BigQuery to Bigtable

<div class="diagram" style="margin: 30px 0;">
<div class="box box-blue">
<strong>BigQuery</strong><br>
<span class="small">SELECT features<br>FROM dataset</span>
</div>
<div style="text-align: center; margin: 0 12px;">
<div style="font-size: 0.75em; color: #4285F4;">EXPORT DATA<br>OPTIONS(bigtable_options)</div>
<div class="arrow">&rarr;</div>
</div>
<div class="box box-green">
<strong>Bigtable Table</strong><br>
<span class="small">Row key = entity_id<br>Column families = feature groups</span>
</div>
<div style="text-align: center; margin: 0 12px;">
<div style="font-size: 0.75em; color: #34A853;">read_row(key)</div>
<div class="arrow">&rarr;</div>
</div>
<div class="box box-grey">
<strong>Features</strong><br>
<span class="small">Decoded from bytes<br>Ready for inference</span>
</div>
</div>

**Self-describing schema**: A metadata row (`#schema`) stores column names, types, and layout so clients decode without hardcoded mappings.

**Data**: 130,000 entities with 200+ features across every BigQuery data type (INT64, FLOAT64, STRING, ARRAY, STRUCT, JSON, GEOGRAPHY).

<div class="notebook-ref">NB0: Environment, NB1: Fundamentals</div>

---

## Serialization Strategies

Five methods for encoding BigQuery data into Bigtable cells:

| Method | Approach | Storage | Decode Speed |
|--------|----------|---------|-------------|
| **Native** | One BQ column &rarr; one BT qualifier | Baseline | Fast |
| **JSON** | Entire row as JSON string | Larger | Slow (parse) |
| **Concat** | Delimiter-separated values | Compact | Medium |
| **Protobuf** | Binary blob with FileDescriptorSet | Smallest | Fast |
| **Hybrid** | Native for hot features, protobuf for long tail | Balanced | Fast (hot path) |

<br>

**Key tradeoff**: storage size vs. client-side decode CPU. Native is simplest; protobuf is most compact; hybrid optimizes for access patterns.

<div class="notebook-ref">NB2: Serialization</div>

---

## Keeping Data Fresh

<div style="text-align: center; margin: 30px 0;">
<div class="diagram">
<div class="box box-grey" style="min-width: 130px;">
<strong>One-time</strong><br>
<span class="small">Manual EXPORT<br>Backfills<br><strong>Hours</strong></span>
</div>
<div class="arrow">&rarr;</div>
<div class="box box-blue" style="min-width: 130px;">
<strong>Scheduled</strong><br>
<span class="small">Cron / DTS<br>Periodic refresh<br><strong>Minutes</strong></span>
</div>
<div class="arrow">&rarr;</div>
<div class="box box-green" style="min-width: 130px;">
<strong>Continuous</strong><br>
<span class="small">APPENDS()<br>Near-real-time<br><strong>Seconds</strong></span>
</div>
<div class="arrow">&rarr;</div>
<div class="box box-orange" style="min-width: 130px;">
<strong>Streaming</strong><br>
<span class="small">Pub/Sub pipeline<br>Direct writes<br><strong>Milliseconds</strong></span>
</div>
</div>
</div>

**Choose based on your freshness SLA and cost budget.** Most production systems combine patterns: scheduled sync for batch features, streaming for real-time signals.

Also covered: BigQuery reservations for export jobs, Data Boost for analytics reads, continuous materialized views.

<div class="notebook-ref">NB3: Synchronization</div>

---

## Feature History

Two strategies for storing historical feature values:

<div class="columns" style="margin-top: 20px;">
<div class="col">

**Key-based**
- Timestamp embedded in row key
- `entity_id#20240115T120000`
- Range scans over time windows
- Manual garbage collection
- Best for: time-series queries

</div>
<div class="col">

**Cell versioning**
- Multiple timestamped values per cell
- Automatic GC (max versions, max age)
- Cleaner API, fewer rows
- Limited query patterns
- Best for: recent history, rollback

</div>
</div>

Also: **point-in-time joins** for label-aligned training data extraction.

<div class="notebook-ref">NB4: History and Time Travel</div>

---

## Direct Writes and Streaming

Bypass BigQuery for high-frequency feature updates:

<div class="columns" style="margin-top: 20px;">
<div class="col">

**Write operations**
- Single-row writes
- Batch mutations (grouped RPCs)
- Atomic read-modify-write
- Check-and-mutate (conditional)

**Patterns**: idempotent writes, change streams, dual-write architectures

</div>
<div class="col">

<div style="text-align: center;">
<div class="diagram">
<div class="box box-purple" style="font-size: 0.8em;"><strong>App</strong></div>
<div class="arrow">&rarr;</div>
<div class="box box-orange" style="font-size: 0.8em;"><strong>Pub/Sub</strong></div>
<div class="arrow">&rarr;</div>
<div class="box box-green" style="font-size: 0.8em;"><strong>Bigtable</strong><br><span class="small">+ BigQuery</span></div>
</div>
</div>

</div>
</div>

<div class="notebook-ref">NB5: Streaming and Direct Writes</div>

---

## Key Design and Organization

Row key design determines performance, data locality, and query patterns.

<div class="columns" style="margin-top: 20px;">
<div class="col">

**Key patterns**
- Compound: `group#entity_id`
- Namespaced: `USER#123`, `ITEM#456`
- Salted: `hash_prefix#entity_id`

**Hotspot avoidance**: no sequential keys, no timestamp-first keys, distribute writes across nodes

</div>
<div class="col">

**Column family strategy**
- Group by access pattern
- Group by update frequency
- Group by GC policy
- Single-table design with multiple families

**Key Visualizer**: identify hot rows, spot sequential patterns, measure data distribution

</div>
</div>

<div class="notebook-ref">NB6: Key Design and Organization</div>

---

## Schema Evolution and Operations

Maintaining a feature store over time without downtime:

<div class="columns" style="margin-top: 20px;">
<div class="col">

**Schema management**
- Versioned schemas (add, drop, rename)
- Metadata columns for decode instructions
- Feature registry (`#registry` row)
- Backfill without interrupting serving

</div>
<div class="col">

**Production operations**
- Monitoring (CPU, disk, throughput)
- App profiles (serving vs. batch priority)
- Security, IAM, authorized views
- Autoscaling, cost optimization (SSD, CUDs)

</div>
</div>

<div class="notebook-ref">NB7: Schema Evolution and Operations</div>

---

## Vector Storage and KNN Search

Store embedding vectors alongside scalar features and query for nearest neighbors.

<div class="columns" style="margin-top: 20px;">
<div class="col">

**Storage**
- Raw binary float32 via `struct.pack()`
- Standalone column, co-located with scalar features
- Query with GoogleSQL `COSINE_DISTANCE()`

</div>
<div class="col">

**When to use Bigtable KNN**

| Scenario | Bigtable | Vector DB |
|----------|----------|-----------|
| < 100K vectors | Good | Overkill |
| Co-located with features | Great | Extra hop |
| Need ANN at scale | Linear scan | Built-in |
| Exact results required | Yes | Approximate |

</div>
</div>

<div class="notebook-ref">NB10: Vector Storage and KNN Search</div>

---

## Dynamic Features

What happens when a new event arrives and the model needs features that depend on it?

<div style="margin-top: 20px;">

| Pattern | How it works | Latency | Best for |
|---------|-------------|---------|----------|
| **Read-Modify-Write** | Atomic counter increment on each event | ~5ms | Counts, sums, running totals |
| **Read + Compute** | Read stored features, compute new ones at serve time | ~3ms + CPU | Ratios, time-since, combinations |
| **Streaming Aggregation** | Pub/Sub &rarr; subscriber &rarr; Bigtable | ~50ms | Complex aggregations, windowed stats |

</div>

<br>

**Combine all three in production** for a single Bigtable read.

<div class="notebook-ref">NB9: Dynamic Features</div>

---

## Serving Integration

Train on BigQuery features, serve from Bigtable, measure the gap.

<div class="diagram" style="margin: 20px 0;">
<div class="box box-orange" style="min-width: 130px;">
<strong>Request</strong><br>
<span class="small">entity_id</span>
</div>
<div class="arrow">&rarr;</div>
<div class="box box-green" style="min-width: 130px;">
<strong>Bigtable</strong><br>
<span class="small">Read features<br>~3ms</span>
</div>
<div class="arrow">&rarr;</div>
<div class="box box-grey" style="min-width: 130px;">
<strong>Decode</strong><br>
<span class="small">Deserialize<br>~1ms</span>
</div>
<div class="arrow">&rarr;</div>
<div class="box box-purple" style="min-width: 130px;">
<strong>Predict</strong><br>
<span class="small">Model inference<br>~1ms</span>
</div>
<div class="arrow">&rarr;</div>
<div class="box box-blue" style="min-width: 130px;">
<strong>Response</strong><br>
<span class="small">Total: ~5ms</span>
</div>
</div>

**Five read methods**: Python client, `cbt` CLI, GoogleSQL, BigQuery external tables, REST/gRPC

**FastAPI endpoint**: receive request &rarr; read features &rarr; predict &rarr; respond

**Training-serving skew**: compare BQ (training) vs Bigtable (serving) features to catch precision loss

<div class="notebook-ref">NB8: Serving Integration</div>

---

## Schema Evolution During Live Serving

Updating the schema without taking the serving endpoint offline:

<div style="text-align: center; margin: 30px 0;">
<div class="diagram">
<div class="box box-grey" style="min-width: 140px;">
<strong>Schema v1</strong><br>
<span class="small">Original features<br>Serving live traffic</span>
</div>
<div class="arrow">&rarr;</div>
<div class="box box-blue" style="min-width: 140px;">
<strong>Backfill v2</strong><br>
<span class="small">Write new schema rows<br>alongside existing ones</span>
</div>
<div class="arrow">&rarr;</div>
<div class="box box-green" style="min-width: 140px;">
<strong>Switch</strong><br>
<span class="small">Update schema metadata<br>Zero errors, zero downtime</span>
</div>
<div class="arrow">&rarr;</div>
<div class="box box-orange" style="min-width: 140px;">
<strong>Schema v2</strong><br>
<span class="small">New features live<br>No latency degradation</span>
</div>
</div>
</div>

Validated with concurrent load testing: schema version switches mid-flight with no errors and no latency spikes.

<div class="notebook-ref">NB8: Serving Integration</div>

---

## Replication and High Availability

<div class="columns" style="margin-top: 20px;">
<div class="col">

**Multi-cluster replication**

<div style="text-align: center; margin: 10px 0;">

<div class="diagram" style="gap: 20px;">
<div class="box box-green" style="min-width: 110px;">
<strong>Cluster A</strong><br>
<span class="small">us-central1-a</span>
</div>
<div style="text-align: center;">
<div class="small">replication</div>
<div>&harr;</div>
</div>
<div class="box box-green" style="min-width: 110px;">
<strong>Cluster B</strong><br>
<span class="small">us-central1-b</span>
</div>
</div>

</div>

**App profiles control routing:**
- Multi-cluster &rarr; automatic failover
- Single-cluster &rarr; strong consistency

</div>
<div class="col">

**Topology options**
- Single-zone (dev/test)
- Multi-zone (production HA)
- Multi-region (disaster recovery)

**Measured in this series**
- Replication lag between clusters
- Failover behavior
- Cost of additional clusters

</div>
</div>

<div class="notebook-ref">NB11: Replication</div>

---

## Local Development with the Emulator

<div class="columns" style="margin-top: 20px;">
<div class="col">

**What the emulator provides**
- `gcloud beta emulators bigtable start`
- Same Python client code
- No GCP project or billing needed
- Fast iteration for development

**Testing patterns**: pytest fixtures, GitHub Actions, Cloud Build, conditional test skipping

</div>
<div class="col">

**What it doesn't support**
- GoogleSQL queries
- Admin API (create instance)
- Replication
- Persistence across restarts
- App profiles

<br>

Design your tests to skip GoogleSQL-dependent features when running against the emulator.

</div>
</div>

<div class="notebook-ref">NB12: Emulator</div>

---

## Production Deployment with Terraform

Infrastructure as Code for the complete feature store:

<div style="text-align: center; margin: 30px 0;">
<div class="diagram">
<div class="box box-grey" style="min-width: 130px;">
<strong>terraform init</strong><br>
<span class="small">Download providers</span>
</div>
<div class="arrow">&rarr;</div>
<div class="box box-blue" style="min-width: 130px;">
<strong>terraform plan</strong><br>
<span class="small">Preview changes</span>
</div>
<div class="arrow">&rarr;</div>
<div class="box box-green" style="min-width: 130px;">
<strong>terraform apply</strong><br>
<span class="small">Create resources</span>
</div>
<div class="arrow">&rarr;</div>
<div class="box box-red" style="min-width: 130px;">
<strong>terraform destroy</strong><br>
<span class="small">Clean teardown</span>
</div>
</div>
</div>

**Managed resources**: instance, clusters, tables, column families, GC policies, app profiles

**Change management**: add a column family in `.tf`, review the diff in `plan`, apply with confidence

<div class="notebook-ref">NB13: Production Deployment</div>

---

## Multi-Language Clients

The same Bigtable feature store, accessed from different ecosystems:

| Language | Strengths | Use case |
|----------|-----------|----------|
| **Python** | Data science, ML frameworks, rapid prototyping | Training pipelines, notebooks, experimentation |
| **Go** | gRPC-native, compiled, high throughput | High-performance serving endpoints |
| **Java** | Enterprise-grade, Maven ecosystem | Enterprise applications, Android backends |
| **Node.js** | Async/await, lightweight | Serverless functions, web APIs |

All clients read the same rows, same column families, same byte encoding. The self-describing schema row works across languages.

<div class="notebook-ref">NB13: Production Deployment</div>

---

## Capstone: Recommendation Engine

A fully self-contained system that ties together patterns from across the entire series.

<div style="text-align: center; margin: 20px 0;">

<div class="diagram">
<div class="box box-green" style="min-width: 170px;">
<strong>Single Bigtable Table</strong><br>
<span class="small">USER# &middot; profiles, counters, embeddings<br>ITEM# &middot; catalog, embeddings<br>#schema &middot; metadata</span>
</div>
</div>

<div class="arrow-down">&darr; <span class="small">multi-entity key namespacing</span></div>

<div class="diagram">
<div class="box box-blue" style="min-width: 140px;">
<strong>Stage 1: Retrieve</strong><br>
<span class="small">KNN &middot; 500 &rarr; 50 candidates</span>
</div>
<div class="arrow">&rarr;</div>
<div class="box box-orange" style="min-width: 140px;">
<strong>Stage 2: Rank</strong><br>
<span class="small">RandomForest &middot; 50 &rarr; top 10</span>
</div>
<div class="arrow">&rarr;</div>
<div class="box box-purple" style="min-width: 140px;">
<strong>FastAPI</strong><br>
<span class="small">/recommend &middot; load tested</span>
</div>
</div>

</div>

<div class="notebook-ref">NB14: Recommendation Engine</div>

---

## Two-Stage Recommendation Pipeline

**Stage 1: Candidate Retrieval** — read user embedding (64-dim), scan ITEM# rows, cosine similarity, return top-50

**Stage 2: Ranking** — read user profile + item catalog, compute features, RandomForest scores each, return top-10

**Feature sources per prediction**

| Feature | Source | Update frequency |
|---------|--------|-----------------|
| User profile | Bigtable `profile` CF | Batch (daily) |
| User embedding | Bigtable `embeddings` CF | Batch (daily) |
| Interaction counts | Bigtable `counters` CF | Real-time (atomic) |
| Item catalog + embedding | Bigtable `catalog` + `embeddings` CF | Batch (weekly) |

<div class="notebook-ref">NB14: Recommendation Engine</div>

---

## Real-Time Signals and Feature Freshness

<div class="columns" style="margin-top: 20px;">
<div class="col">

**Atomic counters** track views, clicks, purchases. Big-endian INT64, no read-before-write races.

Updated via Pub/Sub streaming.

</div>
<div class="col">

**Key insight: combine batch + streaming**

| Features | Quality |
|----------|---------|
| Stale embedding only | Misses preference shifts |
| Fresh counters only | No semantic understanding |
| **Stale embedding + fresh counters** | **Best practical tradeoff** |
| Fresh everything | Ideal (expensive) |

Batch features (embeddings) provide semantic understanding. Real-time features (counters) provide recency. Together they outperform either alone.

</div>
</div>

<div class="notebook-ref">NB14: Recommendation Engine</div>

---

## Getting Started

Choose your entry point based on your experience level:

<div class="columns" style="margin-top: 30px;">
<div class="col">

<div class="box box-blue" style="margin-bottom: 12px;">
<strong>New to feature stores</strong><br>
<span class="small">Start from the beginning</span>
</div>

NB0 &rarr; NB1 &rarr; NB2

Environment setup, first export, serialization basics

</div>
<div class="col">

<div class="box box-green" style="margin-bottom: 12px;">
<strong>Know the basics</strong><br>
<span class="small">Jump to data patterns</span>
</div>

NB5 &rarr; NB6 &rarr; NB9 &rarr; NB8

Streaming writes, key design, dynamic features, serving

</div>
<div class="col">

<div class="box box-orange" style="margin-bottom: 12px;">
<strong>Production-ready</strong><br>
<span class="small">Operations and deployment</span>
</div>

NB7 &rarr; NB11 &rarr; NB13 &rarr; NB14

Schema ops, replication, Terraform, capstone

</div>
</div>

<div class="notebook-ref">All notebooks (NB0 &ndash; NB14)</div>

---

<!-- _class: title -->
<!-- _paginate: false -->

# Resources

<br>

**Repository**: github.com/statmike/vertex-ai-mlops/MLOps/Feature Store/Bigtable

**Bigtable docs**: cloud.google.com/bigtable/docs/overview

**EXPORT DATA**: cloud.google.com/bigquery/docs/export-to-bigtable

**Vertex AI Feature Store**: cloud.google.com/vertex-ai/docs/featurestore/latest/overview

<br>
<br>

<div class="small">

15 notebooks &middot; BigQuery offline store &middot; Bigtable online serving &middot; Sub-10ms reads

</div>
