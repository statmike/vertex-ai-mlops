---
marp: true
theme: default
paginate: true
style: |
  section {
    font-family: 'Segoe UI', Arial, sans-serif;
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
    top: 20px;
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
    padding: 10px 16px;
    text-align: center;
    font-size: 0.82em;
    background: #fff;
    min-width: 100px;
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
    margin: 0 6px;
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
    gap: 24px;
  }
  .col {
    flex: 1;
    min-width: 0;
  }
  table {
    font-size: 0.75em;
  }
---

<!-- _class: title -->
<!-- _paginate: false -->

# BigQuery Feature Store

### 3 notebooks — no online store, no sync, no infrastructure

<br>

BigQuery Storage Read API | 20–200ms serving | Apache Arrow zero-copy

<br>

<div class="small">

github.com/statmike/vertex-ai-mlops/MLOps/Feature Store/BigQuery

</div>

---

## The Latency Sweet Spot

Standard BigQuery queries go through the full query engine — job scheduling, slot allocation, table scanning. The [Storage Read API](https://cloud.google.com/bigquery/docs/reference/storage) bypasses all of it, reading directly from BigQuery's Colossus storage layer via gRPC.

<div class="diagram" style="margin-top: 40px;">
<div class="box box-red">
<strong>Standard BQ Query</strong><br>
<span class="small">Full query engine<br>~2,000 ms<br>$6.25/TB scanned</span>
</div>
<div class="arrow">&rarr;</div>
<div class="box box-blue">
<strong>Storage Read API</strong><br>
<span class="small">Direct storage reads<br>~150–400 ms<br>300 TiB/mo free</span>
</div>
<div class="arrow">&rarr;</div>
<div class="box box-green">
<strong>Bigtable</strong><br>
<span class="small">Point lookups<br>~3–5 ms<br>Provisioned nodes</span>
</div>
</div>

<br>

This approach lives in the sweet spot — fast enough for many serving workloads, flexible enough to replace complex pipelines, and cheap enough to run continuously.

<div class="notebook-ref">Main notebook, Environment notebook</div>

---

## Architecture

<div class="diagram" style="margin-top: 20px;">
<div class="box box-blue">
<strong>BigQuery</strong><br>
<span class="small">Colossus storage<br>Clustered tables</span>
</div>
<div class="arrow">&rarr;</div>
<div class="box box-orange">
<strong>gRPC Stream</strong><br>
<span class="small">Arrow record batches<br>Parallel streams</span>
</div>
<div class="arrow">&rarr;</div>
<div class="box box-green">
<strong>Application</strong><br>
<span class="small">Arrow &rarr; numpy / dict<br>FastAPI response</span>
</div>
</div>

No online store, no sync pipeline, no provisioned infrastructure. BigQuery is both the offline store and the serving layer.

| | Standard BQ Query | Storage Read API |
|---|---|---|
| Parse | SQL parse & plan | (skipped) |
| Allocate | Slot allocation | (skipped) |
| Read | Distributed scan | Direct storage read |
| Transfer | HTTP + deserialization | gRPC + Arrow zero-copy |
| **Latency** | **~2,000 ms** | **~150–400 ms** |

<div class="notebook-ref">Main notebook: Part 3</div>

---

## The Data

A **130K-entity dataset** used across all three notebooks — 26 entity groups (A–Z), 5,000 entities per group, 224 columns spanning every BigQuery data type.

| Table | Rows | Cols | Purpose |
|-------|------|------|---------|
| `dense_features` | 130,000 | 224 | Every BQ data type (FLOAT, STRING, STRUCT, JSON, ...) |
| `sparse_events` | 2,600,000 | 10 | Time-series events (20 per entity) |
| `dense_features_clustered` | 130,000 | 224 | **Primary table** — clustered by group + ID |
| `entity_embeddings` | 130,000 | 3 | 64-dim vectors for similarity search |

**Why clustering matters:** `CLUSTER BY entity_group, entity_id` physically sorts data so `row_restriction` filters prune at the storage block level.

<div class="notebook-ref">Environment notebook, Main notebook: Part 1</div>

---

## Core Pattern — Row Restriction + Column Pruning

<div class="columns" style="margin-top: 10px;">
<div class="col" style="flex: 1.3;">

**Row restriction** — any WHERE clause

| Filter | Rows | Latency |
|--------|------|---------|
| `group = 'A' AND id = '000001'` | 1 | ~350 ms |
| `feature_float_1 > 50.0` | 2,477 | ~400 ms |
| `group IN ('A','B','C') AND float_1 > 50` | 3,794 | ~406 ms |
| `id BETWEEN '002000' AND '003000'` | 1,000 | ~396 ms |


</div>
<div class="col">

**Column pruning** — read only what you need

| Columns | Latency | Data |
|---------|---------|------|
| 5 | ~630 ms | 270 KB |
| 50 | ~524 ms | 2 MB |
| 224 (all) | ~1,242 ms | 10 MB |


</div>
</div>

<div class="notebook-ref">Main notebook: Part 3</div>

---

## Session Caching

Session creation is the dominant latency cost — ~60% of total read time. The `FeatureSessionPool` eliminates it for repeat reads.

<div class="diagram" style="margin: 30px 0;">
<div class="box box-red">
<strong>Cold Read</strong><br>
<span class="small">Create session + read stream<br><strong>~400 ms</strong></span>
</div>
<div style="text-align: center; margin: 0 20px;">
<div style="font-size: 0.75em; color: #34A853;">add caching</div>
<div class="arrow">&rarr;</div>
</div>
<div class="box box-green">
<strong>Warm Read</strong><br>
<span class="small">Skip session creation<br><strong>~150 ms</strong></span>
</div>
<div style="text-align: center; margin: 0 20px;">
<div style="font-size: 1.2em; color: #34A853;"><strong>2.7&times;</strong></div>
</div>
</div>

**`FeatureSessionPool`** — 48 lines of Python, no external dependencies.

- TTL-based eviction (default 5 minutes)
- `warm()` method for pre-creating sessions at startup
- Reuses the gRPC channel and connection pool across requests
- Copy into any project — just a Python dict with TTL

<div class="notebook-ref">Main notebook: Part 4</div>

---

## Arrow Zero-Copy

Arrow's on-wire format matches its in-memory format — the bytes that arrive over gRPC are the bytes your code works with.

<div class="diagram" style="margin: 20px 0;">
<div class="box box-blue">
<strong>gRPC Stream</strong><br>
<span class="small">Arrow IPC format<br>Binary over wire</span>
</div>
<div class="arrow">&rarr;</div>
<div class="box box-orange">
<strong>Arrow Table</strong><br>
<span class="small">Columnar in-memory<br>Same bytes</span>
</div>
<div class="arrow">&rarr;</div>
<div class="box box-green">
<strong>numpy array</strong><br>
<span class="small">Pointer cast<br>No data copy</span>
</div>
</div>

Conversion benchmarks (5,000 rows):

| Target | Time | Notes |
|--------|------|-------|
| Arrow &rarr; **numpy** | **235 &micro;s** | Zero-copy for float columns |
| Arrow &rarr; pandas | 3,065 &micro;s | Memory copy |
| Arrow &rarr; Python dict | 20,384 &micro;s | Python object allocation |

<div class="notebook-ref">Main notebook: Part 3</div>

---

## Serving Application

FastAPI + `asyncio.to_thread()` + `FeatureSessionPool` — non-blocking reads with warm gRPC channels.

<div class="columns" style="margin-top: 10px;">
<div class="col">

**Endpoints**
- `GET /features/{group}/{id}` — single entity
- `POST /features/batch` — N sessions via `asyncio.gather`
- `POST /features/batch/combined` — 1 session, `IN (...)` clause

</div>
<div class="col">

**Performance (10 entities)**

| Pattern | Total | Per-entity |
|---------|-------|------------|
| Sequential (10&times; GET) | 1,538 ms | 154 ms |
| Concurrent (gather) | 448 ms | 45 ms |
| Combined batch | 396 ms | 40 ms |

Concurrent (20 in-flight): p50 359 ms, p95 587 ms

</div>
</div>

<div class="notebook-ref">Main notebook: Part 5, Cloud Run notebook</div>

---

## Batch Patterns — Per-Entity vs Combined

<div class="columns" style="margin-top: 10px;">
<div class="col">

**Per-entity batch**
N ReadSessions via `asyncio.gather()`
- 1 roundtrip, N server-side sessions
- Latency scales with entity count

**Combined-restriction batch**
1 ReadSession with `IN (...)` clause
- 1 roundtrip, 1 server-side session
- Near-constant latency

Combined wins at &gt;10 entities.

</div>
<div class="col">

| Entities | Per-Entity | Combined | Speedup |
|----------|-----------|----------|---------|
| 1 | ~453 ms | ~453 ms | 1.0&times; |
| 10 | ~800 ms | ~520 ms | 1.5&times; |
| 25 | ~1,400 ms | ~540 ms | 2.6&times; |
| 50 | ~1,900 ms | ~510 ms | 3.7&times; |
| 100 | ~2,289 ms | ~486 ms | **4.7&times;** |

</div>
</div>

<div class="notebook-ref">Cloud Run notebook: Parts 7, 9</div>

---

## Cloud Run Deployment

<div class="diagram" style="margin: 20px 0;">
<div class="box box-grey">
<strong>FastAPI App</strong><br>
<span class="small">Dockerfile</span>
</div>
<div class="arrow">&rarr;</div>
<div class="box box-blue">
<strong>Cloud Build</strong><br>
<span class="small">Artifact Registry</span>
</div>
<div class="arrow">&rarr;</div>
<div class="box box-green">
<strong>Cloud Run</strong><br>
<span class="small">Autoscaling</span>
</div>
<div class="arrow">&rarr;</div>
<div class="box box-orange">
<strong>ID Token Auth</strong><br>
<span class="small">roles/run.invoker</span>
</div>
</div>

<div class="columns">
<div class="col">

**Performance**

| Metric | Value |
|--------|-------|
| Cold start | ~229 ms |
| Warm p50 | ~453 ms |
| Throughput plateau | ~30–40 req/s |
| Spike bursts (200 sim.) | Zero errors |

</div>
<div class="col">

**Production configuration**

| Setting | Value |
|---------|-------|
| `min_instance_count` | 1 |
| `max_instance_count` | 10 |
| `max_instance_request_concurrency` | 20 |
| CPU / Memory | 2 vCPU / 2 GiB |

</div>
</div>

Traffic splitting for canary deployments — revision-based rollout of new feature columns.

<div class="notebook-ref">Cloud Run notebook: Parts 2&ndash;8, 12</div>

---

## Three-Way Comparison

| Operation | BQ Query | Storage API | Bigtable (ref) |
|-----------|----------|-------------|----------------|
| 1 entity (5 features) | ~2,000 ms | ~350 ms | ~3–5 ms |
| 100 entities | ~1,500 ms | ~460 ms | ~50–100 ms |
| 1,000 entities | ~1,600 ms | ~420 ms | ~200–500 ms |
| 5,000 entities | ~1,500 ms | ~360 ms | ~500–2,000 ms |
| Filtered segment | ~1,600 ms | ~410 ms | N/A |

| Component | BQ Storage API | Bigtable |
|-----------|---------------|----------|
| Infrastructure | **$0** (serverless) | ~$500+/mo (1 node min) |
| Read cost | 300 TiB/mo free | Included in node cost |
| Sync pipeline | **None** | EXPORT DATA / Dataflow |


<div class="notebook-ref">Main notebook: Parts 9, 10</div>

---

## When to Use Which

**Sub-ms atomic writes (counters, real-time state)?** &rarr; **Bigtable**
**Single-digit-ms point lookups?** &rarr; **Bigtable**
**20–200ms OK? Want simplicity + governance?** &rarr; **BQ Storage API**
**Managed feature registry?** &rarr; **Vertex AI Feature Store**

| Capability | BQ Storage API | Bigtable | Vertex AI FS |
|---|---|---|---|
| Point-lookup latency | 20–200 ms | <10 ms | Managed |
| Bulk reads (1K+) | Excellent | Many RPCs | Managed |
| Filtering | Predicate pushdown | Row key only | Feature Views |
| Streaming writes | Storage Write API | Atomic point writes | Offline-first |
| Governance | Built-in (Dataplex) | You build it | Managed |
| Infrastructure | None | Provisioned | Managed |

<div class="notebook-ref">Main notebook: Part 11</div>

---

<!-- _class: title -->
<!-- _paginate: false -->

# Resources

<br>

**Repository**: github.com/statmike/vertex-ai-mlops/MLOps/Feature Store/BigQuery

**Storage Read API**: cloud.google.com/bigquery/docs/reference/storage

**Apache Arrow**: arrow.apache.org

**Clustered tables**: cloud.google.com/bigquery/docs/clustered-tables

**Cloud Run**: cloud.google.com/run/docs/overview/what-is-cloud-run

<br>
<br>

<div class="small">

3 notebooks &middot; BigQuery Storage Read API &middot; Apache Arrow zero-copy &middot; 20&ndash;200ms serving

</div>
