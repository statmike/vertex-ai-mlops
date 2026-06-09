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

# Valkey Feature Store

### 9 notebooks — sub-millisecond in-memory serving

<br>

Memorystore for Valkey | HNSW vector search | atomic real-time features

<br>

<div class="small">

github.com/statmike/vertex-ai-mlops/MLOps/Feature Store/Valkey

</div>

---

## The Feature Store Problem

Features are computed in batch (BigQuery) but served in real time. The online store sits between them — and when **microseconds matter** (trading, gaming, ad bidding), it has to be in memory.

<div class="diagram" style="margin-top: 40px;">
<div class="box box-blue">
<strong>BigQuery</strong><br>
<span class="small">Offline store<br>Feature engineering<br>seconds–minutes</span>
</div>
<div class="arrow">&rarr;</div>
<div class="box box-orange">
<strong>Sync</strong><br>
<span class="small">Pub/Sub bridge<br>continuous / batch</span>
</div>
<div class="arrow">&rarr;</div>
<div class="box box-green">
<strong>Valkey</strong><br>
<span class="small">Online store<br>in-memory serving<br><strong>&lt;2 ms</strong></span>
</div>
</div>

<br>

This series builds a complete feature store on **Memorystore for Valkey** — using BigQuery as the offline engine and Valkey for ultra-low-latency online serving.

---

## Why Valkey? (Redis vs Valkey on Memorystore)

Google Cloud offers two managed in-memory stores. This series uses **Valkey** — the patterns work on either, since Valkey is Redis-protocol compatible.

| | Memorystore for Redis | **Memorystore for Valkey** |
|---|---|---|
| Engine | Redis, up to 7.2 | Valkey 7.2 / 8.0 / 9.0 |
| Governance | Redis Inc. (SSPL/RSAL) | **Open source, Linux Foundation (BSD)** |
| Architecture | Primary + replica | **Cluster-native** (+ Cluster-Disabled option) |
| Scale-out | Vertical | **Horizontal** (add shards) |
| Newer features | Capped at 7.2 | HEXPIRE, ongoing OSS development |

We run **Cluster Mode Disabled** — single endpoint, standard `redis.Redis` client, all multi-key ops work without slot constraints.

<div class="notebook-ref">Environment notebook</div>

---

## The Latency Spectrum

Where Valkey sits among the five Google Cloud feature store approaches:

<div class="diagram" style="margin-top: 30px;">
<div class="box box-red">
<strong>BigQuery</strong><br>
<span class="small">Storage Read API<br>20–200 ms</span>
</div>
<div class="arrow">&rarr;</div>
<div class="box box-orange">
<strong>Spanner</strong><br>
<span class="small">SQL + ACID<br>~5–10 ms</span>
</div>
<div class="arrow">&rarr;</div>
<div class="box box-blue">
<strong>Bigtable</strong><br>
<span class="small">Key-based<br>~3–5 ms</span>
</div>
<div class="arrow">&rarr;</div>
<div class="box box-green">
<strong>Valkey</strong><br>
<span class="small">In-memory<br><strong>&lt;2 ms</strong></span>
</div>
</div>

<br>

Valkey gives the **fastest reads in the series** plus native vector search. The trade-off: data lives in memory, sync is a custom Pub/Sub bridge, and it's a serving layer — BigQuery remains the durable source of truth.

---

## Architecture

<div class="diagram" style="margin-top: 20px;">
<div class="box box-blue">
<strong>BigQuery</strong><br>
<span class="small">Offline store<br>Continuous Query</span>
</div>
<div class="arrow">&rarr;</div>
<div class="box box-orange">
<strong>Pub/Sub</strong><br>
<span class="small">Sync bridge<br>+ subscriber</span>
</div>
<div class="arrow">&rarr;</div>
<div class="box box-green">
<strong>Valkey</strong><br>
<span class="small">Hashes<br>HNSW index</span>
</div>
<div class="arrow">&rarr;</div>
<div class="box box-grey">
<strong>Serving</strong><br>
<span class="small">FastAPI<br>Cloud Run</span>
</div>
</div>

Features are stored as **Redis hashes**, key `features:{entity_group}:{entity_id}`. Applications also write real-time signals directly (dual-write path).

| Concept | Valkey | Bigtable equivalent |
|---|---|---|
| Hash key | `features:A:000001` | Row key `A#000001` |
| Hash field | `feature_float_1` | Column qualifier |
| Read all | `HGETALL` | ReadRow |
| Atomic add | `HINCRBY` | ReadModifyWriteRow |

<div class="notebook-ref">Environment, Fundamentals</div>

---

## The Data

A **130K-entity dataset** shared across all feature store series — 26 entity groups (A–Z), 5,000 entities per group, 224 columns spanning every BigQuery data type.

| Resource | Size | Purpose |
|----------|------|---------|
| `dense_features` | 130,000 rows, 224 cols | Every BQ data type |
| `sparse_events` | 2,600,000 rows | Time-series events |
| `valkey_feature_store` | BigQuery dataset | Independent per-series dataset |

Loaded into Valkey via pipelined `HSET`: **130K entities in ~25s**, ~300 MB memory.

<div class="notebook-ref">Environment, Fundamentals</div>

---

## Fundamentals — Hashes &amp; Sub-ms Reads

<div class="columns" style="margin-top: 10px;">
<div class="col">

**Read patterns**
- `HGET` — single field
- `HMGET` — selected fields
- `HGETALL` — whole entity

**Measured (130K entities)**

| Operation | Latency |
|-----------|---------|
| Point read (HGETALL) | ~1.6 ms |
| HMGET (subset) | ~1.5 ms |

</div>
<div class="col">

**Pipelining** — batch N reads in one roundtrip

| Entities | Total | Per-entity |
|----------|-------|------------|
| 1 | 1.3 ms | 1.3 ms |
| 10 | 3.0 ms | 0.30 ms |
| 100 | 14.6 ms | 0.15 ms |
| 500 | 60 ms | 0.12 ms |

</div>
</div>

Pipelining amortizes the network roundtrip — the key to bulk feature reads.

<div class="notebook-ref">Fundamentals</div>

---

## Serialization — Five Encoding Methods

Encoding BigQuery's 19 data types into Redis strings/bytes. Five methods, each a real trade-off:

| Method | Storage | Single-field read | All-field read |
|--------|---------|-------------------|----------------|
| **Native hash fields** | Highest | **Fastest** (HGET) | Slowest (HGETALL) |
| JSON blob | Large | Slow (parse all) | Medium |
| Concatenation | **Smallest** | Slow (split all) | Medium |
| Protocol Buffers | Small | Slow (deserialize) | Medium |
| **Hybrid** (hot + cold blob) | High | **Fastest** for hot | **Fastest** overall |

The Redis-specific insight: **native fields let you `HGET` one feature** — blob methods force reading the whole entity to read anything.

<div class="notebook-ref">Serialization</div>

---

## Synchronization — Four Patterns

No native BigQuery export to Valkey — so we build a **Pub/Sub bridge** (the reusable pattern for any target).

<div class="diagram" style="margin: 16px 0;">
<div class="box box-blue"><span class="small">BigQuery<br>Continuous Query</span></div>
<div class="arrow">&rarr;</div>
<div class="box box-orange"><span class="small">Pub/Sub<br>topic</span></div>
<div class="arrow">&rarr;</div>
<div class="box box-purple"><span class="small">Subscriber<br>(Cloud Run)</span></div>
<div class="arrow">&rarr;</div>
<div class="box box-green"><span class="small">Valkey<br>HSET</span></div>
</div>

| Pattern | Freshness | Use case |
|---------|-----------|----------|
| One-time backfill | Manual | Initial load (~10K entities/s) |
| Scheduled sync | Minutes–hours | Periodic feature refresh |
| Continuous query | Seconds | Near-real-time propagation |
| Dual-write | &lt;1 ms | Real-time signals (app → Valkey) |

<div class="notebook-ref">Synchronization</div>

---

## TTL-on-Sync — Automatic Staleness Bounds

A pattern **unique to Valkey**: write features with an `EXPIRE`, so stale data self-evicts if the sync pipeline stalls.

<div class="diagram" style="margin: 24px 0;">
<div class="box box-green">
<strong>Fresh feature</strong><br>
<span class="small">HSET + EXPIRE 180s</span>
</div>
<div class="arrow">&rarr;</div>
<div class="box box-orange">
<strong>Sync stalls</strong><br>
<span class="small">no refresh</span>
</div>
<div class="arrow">&rarr;</div>
<div class="box box-red">
<strong>Auto-expires</strong><br>
<span class="small">key gone → fall back to BigQuery</span>
</div>
</div>

Set TTL = sync interval × safety factor. A missing key means "stale" — the serving layer falls back to BigQuery and re-populates. An automatic staleness guarantee the disk-based stores don't have.

<div class="notebook-ref">Synchronization, TTL and Memory Management</div>

---

## TTL, Eviction &amp; Memory

In-memory means a hard ceiling — eviction is a first-class concern (Bigtable/Spanner scale disk instead).

<div class="columns">
<div class="col">

**TTL patterns**
- Session features → 30 min
- Real-time signals → 5 min
- Daily aggregates → 24 hr
- Core features → permanent

**Eviction**: `volatile-lru` drops TTL keys first, keeps permanent features.

</div>
<div class="col">

**Operational notes**
- Active vs lazy expiration: expired keys hold memory until collected
- Persistence: RDB/AOF + HA replica (BigQuery is the source of truth)
- **HEXPIRE** (per-field TTL) exists in Valkey 8.0 but Memorystore blocks it

</div>
</div>

<div class="notebook-ref">TTL and Memory Management</div>

---

## Atomic Operations &amp; Real-Time Features

Valkey's atomic ops are the fastest in the series — `HINCRBY` &lt;1 ms.

<div class="columns" style="margin-top: 10px;">
<div class="col">

**Primitives**
- `HINCRBY` / `HINCRBYFLOAT` — counters
- `MULTI/EXEC` — multi-key atomic
- `WATCH` — optimistic locking
- `SETNX` — idempotent write-once
- **Lua (EVAL)** — read-check-write in one server call
- **Streams (XADD)** — event log in-store

</div>
<div class="col">

**Three dynamic-feature patterns**

| Pattern | Best for |
|---------|----------|
| Read-modify-write | running totals |
| Read + compute | cheap derived |
| Streaming aggregation | windowed aggs |

Combine batch features (synced) + real-time counters (direct) in one hash.

</div>
</div>

<div class="notebook-ref">Atomic Operations</div>

---

## Serving Integration

FastAPI + connection pool + the correctness checks every feature store needs.

<div class="columns" style="margin-top: 10px;">
<div class="col">

**Serving path**
- `HMGET` → decode → predict
- Connection pool (created once)
- Retry + timeout + graceful degradation
- Fallback to BigQuery on miss

**Measured**: ~6.5 ms read+predict; ~1000 RPS at 50 workers

</div>
<div class="col">

**Correctness**
- **Training-serving skew** check (0% mismatch)
- Read-method comparison (HMGET ≈ Lua ≈ pipeline &lt; HGETALL)
- Live schema evolution — add a feature with no downtime

</div>
</div>

<div class="notebook-ref">Serving Integration</div>

---

## Vector Search with HNSW

Valkey's signature ML feature: native approximate nearest neighbor via `FT.SEARCH`.

<div class="columns" style="margin-top: 10px;">
<div class="col">

**Index types**
- `FLAT` — exact brute-force
- `HNSW` — approximate, sub-5 ms

**Measured (130K vectors, 64-dim)**

| Index | Latency | Recall@10 |
|-------|---------|-----------|
| FLAT | ~7 ms | 100% |
| HNSW | ~2 ms | ~89% |

</div>
<div class="col">

**Hybrid filtered search**

`(@category:{electronics} @score:[50 +inf]) =>[KNN 10 @embedding $q]`

Metadata filter **+** vector rank in one query — Bigtable can't pre-filter.

Tune recall via `M`, `EF_CONSTRUCTION`, `EF_RUNTIME` (set at index creation on Memorystore).

</div>
</div>

<div class="notebook-ref">Vector Search</div>

---

## Vector Search — Across the Series

All four serving stores now have **native** vector search — they differ on index, pre-filtering, and latency.

| Approach | Index | Pre-filtering | Latency (130K) |
|----------|-------|---------------|----------------|
| **Valkey** | HNSW / FLAT | TAG + NUMERIC | **~2–5 ms** |
| Spanner | ScaNN ANN / exact | **Full SQL WHERE** | ~10–50 ms |
| BigQuery | IVF / TreeAH | SQL pushdown | ~100 ms–s |
| Bigtable | brute-force | row key only | ~100–300 ms |

**Valkey** for sub-ms real-time retrieval. **Spanner** when vector search is one step inside a richer SQL query (filter many columns + JOIN).

<div class="notebook-ref">Vector Search</div>

---

## Capstone — Real-Time Trading

A trading feature store exercising every Valkey capability where microseconds matter.

<div class="columns" style="margin-top: 8px;">
<div class="col">

- **Instrument features** — hashes, sub-ms reads
- **Market quotes** — 5-second TTL (stale prices are dangerous)
- **Atomic P&amp;L** — `HINCRBYFLOAT` per trade (~2 ms)
- **Top movers** — sorted sets (`ZADD`)

</div>
<div class="col">

- **Instrument matching** — HNSW by factor exposure (&lt;5 ms)
- **Two-stage recommendation** — HNSW retrieve → score (~5 ms total)
- Load tested under concurrency

</div>
</div>

<div class="notebook-ref">Production Deployment</div>

---

## Production Operations

<div class="columns" style="margin-top: 10px;">
<div class="col">

**Deploy** — Terraform (`google_memorystore_instance`), PSC service connection policy, Pub/Sub with dead-letter

**Monitor** — Cloud Monitoring: memory usage ratio, cache hit ratio, evictions, failover

**Secure** — TLS + AUTH, least-privilege IAM, private (PSC) networking

</div>
<div class="col">

**HA** — Standard tier: primary + replica, automatic failover, stable endpoint

**Connect** — Cluster Disabled → `redis.Redis`; Cluster Enabled → `RedisCluster`

**Readiness checklist** — sizing, eviction policy, sync, skew checks, alerts

</div>
</div>

<div class="notebook-ref">Production Deployment</div>

---

## When to Use Valkey

**Sub-millisecond reads required (gaming, trading, ad bidding)?** &rarr; **Valkey**
**Large-scale real-time vector retrieval (HNSW ANN)?** &rarr; **Valkey**
**Atomic real-time counters / ephemeral session state?** &rarr; **Valkey**
**Data fits in memory and BigQuery is the source of truth?** &rarr; **Valkey**

| Capability | Valkey | Bigtable | Spanner |
|---|---|---|---|
| Point-lookup latency | &lt;2 ms | ~3–5 ms | ~5–10 ms |
| Vector search | HNSW (native) | brute-force | ScaNN (native) |
| Atomic ops | &lt;1 ms (HINCRBY) | ~3 ms | txn ~5–15 ms |
| Storage | in-memory | disk (petabytes) | disk (auto-scale) |
| BQ sync | Pub/Sub bridge | EXPORT DATA | continuous query |

<div class="notebook-ref">Production Deployment: §14</div>

---

<!-- _class: title -->
<!-- _paginate: false -->

# Resources

<br>

**Repository**: github.com/statmike/vertex-ai-mlops/MLOps/Feature Store/Valkey

**Memorystore for Valkey**: cloud.google.com/memorystore/docs/valkey

**Vector search**: cloud.google.com/memorystore/docs/valkey/about-vector-search

**Valkey**: valkey.io

<br>
<br>

<div class="small">

9 notebooks &middot; Memorystore for Valkey &middot; HNSW vector search &middot; sub-millisecond serving

</div>
