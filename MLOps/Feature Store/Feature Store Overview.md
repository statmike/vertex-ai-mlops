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
    min-width: 90px;
  }
  .box-blue { border-color: #4285F4; background: #e8f0fe; }
  .box-green { border-color: #34A853; background: #e6f4ea; }
  .box-orange { border-color: #F9AB00; background: #fef7e0; }
  .box-red { border-color: #EA4335; background: #fce8e6; }
  .box-purple { border-color: #9334E6; background: #f3e8fd; }
  .box-grey { border-color: #999; background: #f5f5f5; }
  .arrow { font-size: 1.5em; color: #555; margin: 0 6px; }
  .arrow-down { font-size: 1.5em; color: #555; text-align: center; margin: 4px 0; }
  .small { font-size: 0.75em; color: #666; }
  .columns { display: flex; gap: 24px; }
  .col { flex: 1; min-width: 0; }
  table { font-size: 0.74em; }
  section.compact table { font-size: 0.62em; }
  h2 { color: #1a73e8; }
---

<!-- _class: title -->
<!-- _paginate: false -->

# Feature Stores on Google Cloud

### 5 approaches — from zero infrastructure to sub-millisecond serving

<br>

BigQuery · Spanner · Bigtable · Valkey · Vertex AI Feature Store

<br>

<div class="small">

45 notebooks · one shared 130K-entity dataset · github.com/statmike/vertex-ai-mlops/MLOps/Feature Store

</div>

---

## The Feature Store Problem

Features are **computed in batch** (BigQuery — seconds to minutes) but **served in real time** (milliseconds or less, per prediction). An online store bridges the two, and the offline store stays the source of truth.

<div class="diagram" style="margin-top: 30px;">
<div class="box box-blue">
<strong>Offline store</strong><br>
<span class="small">BigQuery<br>full history<br>training, backfills<br>seconds–minutes</span>
</div>
<div class="arrow">&rarr;</div>
<div class="box box-orange">
<strong>Sync</strong><br>
<span class="small">EXPORT DATA /<br>continuous query /<br>Pub/Sub / managed</span>
</div>
<div class="arrow">&rarr;</div>
<div class="box box-green">
<strong>Online store</strong><br>
<span class="small">latest values<br>low-latency reads<br>real-time inference</span>
</div>
</div>

<br>

**The recurring questions:** how fresh must features be? how fast must reads be? do you need to filter, JOIN, or transact at serve time? how much infrastructure do you want to own? Each approach answers these differently.

---

## Five Approaches, One Offline Store

Every approach uses **BigQuery as the offline analytical engine**. They differ in the *online* path. Four are self-built on the **same 130K-entity dataset** (26 groups × 5,000, 224 columns) so they compare directly; the fifth is fully managed.

| Approach | Online store | Notebooks |
|---|---|---|
| **BigQuery** | none — serve from BigQuery storage | 3 |
| **Spanner** | Cloud Spanner (SQL database) | 12 |
| **Bigtable** | Cloud Bigtable (wide-column) | 15 |
| **Valkey** | Memorystore for Valkey (in-memory) | 9 |
| **Vertex AI FS** | managed (Bigtable-backed or Optimized) | 6 |

The first four trade latency for operational simplicity along a spectrum. Vertex AI sits apart — it *abstracts* the online store rather than exposing it.

---

## The Latency Spectrum

The central trade-off: **lower latency costs more infrastructure and more constraints.**

<div class="diagram" style="margin-top: 28px;">
<div class="box box-red">
<strong>BigQuery</strong><br>
<span class="small">Storage Read API<br><strong>20–200 ms</strong><br>zero infra</span>
</div>
<div class="arrow">&rarr;</div>
<div class="box box-green">
<strong>Spanner</strong><br>
<span class="small">SQL + ACID<br><strong>~5–10 ms</strong><br>provisioned PUs</span>
</div>
<div class="arrow">&rarr;</div>
<div class="box box-blue">
<strong>Bigtable</strong><br>
<span class="small">key-based<br><strong>~3–5 ms</strong><br>provisioned nodes</span>
</div>
<div class="arrow">&rarr;</div>
<div class="box box-orange">
<strong>Valkey</strong><br>
<span class="small">in-memory<br><strong>&lt;2 ms</strong><br>provisioned memory</span>
</div>
</div>

<br>

<div class="diagram">
<div class="box box-purple" style="min-width: 600px;">
<strong>Vertex AI Feature Store</strong> — managed serving (Bigtable-backed or Optimized), off the spectrum: Google runs the infra and the registry
</div>
</div>

<br>

<span class="small">Latency = measured single-entity point read on the shared dataset. Faster reads buy you less: data must fit in memory (Valkey), or you give up SQL/JOINs (Bigtable).</span>

---

## Shared Architecture

One offline store, four online paths, plus direct writes for real-time signals.

<div class="diagram" style="margin-top: 16px;">
<div class="box box-blue"><strong>BigQuery</strong><br><span class="small">offline store<br>(source of truth)</span></div>
<div class="arrow">&rarr;</div>
<div class="box box-grey"><span class="small"><strong>Sync</strong><br>EXPORT DATA<br>continuous query<br>Pub/Sub bridge<br>managed</span></div>
<div class="arrow">&rarr;</div>
<div class="box box-green"><span class="small"><strong>Online store</strong><br>Spanner / Bigtable /<br>Valkey / Vertex</span></div>
<div class="arrow">&rarr;</div>
<div class="box box-grey"><span class="small"><strong>Serving</strong><br>FastAPI /<br>Cloud Run</span></div>
</div>

<div class="diagram" style="margin-top: 10px;">
<div class="box box-orange" style="min-width: 560px;"><span class="small"><strong>Direct write path</strong> — apps write real-time signals straight to the online store (counters, state, quotes), bypassing BigQuery</span></div>
</div>

The shared dataset: `dense_features` (130,000 rows × 224 columns, every BQ type) + `sparse_events` (2.6M rows). BigQuery FS serves it in place; the others sync a copy. **BigQuery stays the durable record everywhere.**

---

## BigQuery Feature Store — Zero Infrastructure

Serve features **directly from BigQuery** — no online store, no sync, nothing to provision.

<div class="columns" style="margin-top: 10px;">
<div class="col">

**How** — [Storage Read API](https://cloud.google.com/bigquery/docs/reference/storage) reads Colossus directly over gRPC, streaming Apache Arrow (zero-copy). Session caching + clustering.

**Unique**
- Always fresh (no sync lag)
- Filter on **any column**, ad-hoc
- Time travel built in
- Dataplex governance for free

</div>
<div class="col">

**Measured**
- ~150–400 ms warm (2.7× via session pool)
- Arrow→numpy 235 µs (zero-copy)
- Bulk: wins vs Bigtable at 100+ entities

**Cost** — **$0 infra**, 300 TiB/mo free read tier

</div>
</div>

**Best for** — workloads where 20–200 ms is fine and you want the simplest path: bulk reads, flexible filtering, built-in governance, zero ops.

---

## Spanner Feature Store — SQL at the Serving Layer

Make the online store a **real SQL database** — the only approach with serving-time JOINs and multi-row ACID.

<div class="columns" style="margin-top: 10px;">
<div class="col">

**How** — composite PK `(entity_group, entity_id)`; `execute_sql` / `read()`; FastAPI + session pool. Enterprise edition for vector indexes.

**Unique**
- **Secondary indexes** — query any column
- **Serving-time JOINs** (1/2/3-table)
- **Multi-row / multi-table ACID**
- Native vector search **+ SQL WHERE** in one query
- Multi-region, 99.999% SLA

</div>
<div class="col">

**Measured (100 PU)**
- point read ~10 ms (strong), ~8 ms (stale)
- index: `rows_scanned` 1 vs 130,000
- concurrency: 10 writers, 0 lost updates
- SQL-filtered vector KNN ~45 ms

**Cost** — provisioned PUs (1000 = 1 node) + autoscaling; Enterprise for ANN

</div>
</div>

**Best for** — filter/JOIN on non-key columns at serve time, multi-row transactions, vector search inside a richer SQL query, or strong-consistency multi-region.

---

## Bigtable Feature Store — Key-Based, Full Control

Direct ownership of a sub-5 ms wide-column serving layer with atomic real-time writes.

<div class="columns" style="margin-top: 10px;">
<div class="col">

**How** — read by row key; `#schema` metadata row decodes bytes; column families + cell versioning. 5 serialization strategies.

**Unique**
- **Atomic** read-modify-write, check-and-mutate
- 4 sync tiers (one-time → streaming)
- Multi-cluster replication; app-profile priority isolation
- Cell-version history; multi-language clients
- Petabyte scale

</div>
<div class="col">

**Measured**
- end-to-end ~5 ms (read 3 + decode 1 + predict 1)
- atomic counter RMW ~5 ms
- streaming aggregation ~50 ms

**Cost** — provisioned nodes, ~$500+/mo (1-node min); bills continuously

</div>
</div>

**Best for** — sub-5 ms key lookups, atomic counters/state without round-tripping BigQuery, streaming ingestion, and HA replication you control.

---

## Valkey Feature Store — Sub-Millisecond In-Memory

The fastest reads in the set, with native HNSW vector search and atomic counters.

<div class="columns" style="margin-top: 10px;">
<div class="col">

**How** — [Memorystore for Valkey](https://cloud.google.com/memorystore/docs/valkey/valkey-overview), Cluster-Disabled; features as Redis hashes `features:{group}:{id}`; `HGET`/`HMGET`; ConnectionPool.

**Unique**
- **&lt;2 ms reads** (only in-memory store)
- **TTL-on-sync** — stale data self-evicts → fall back to BigQuery
- Atomic `HINCRBY` &lt;1 ms; Lua, Streams
- HNSW ANN via `FT.SEARCH`

</div>
<div class="col">

**Measured (130K)**
- point read ~1.6 ms; pipelined 0.12 ms/entity
- HNSW ~2 ms @ ~89% recall@10 vs FLAT ~7 ms @ 100%
- load 130K in ~25 s, ~300 MB

**Cost** — provisioned memory (hard ceiling); HA tier primary + replica

</div>
</div>

**Best for** — microsecond reads (trading, gaming, ad bidding), real-time counters / ephemeral state, large-scale HNSW retrieval; data fits in RAM.

---

## Vertex AI Feature Store — Fully Managed

Google runs the serving infra, the sync, and a formal feature registry.

<div class="columns" style="margin-top: 10px;">
<div class="col">

**How** — managed online store: **Bigtable-backed** (scalable) or **Optimized** (ultra-low latency). Serving unit is a **Feature View**; `OnlineStoreReader` helper for async reads.

**Unique**
- The only **fully managed** option
- **Feature registry**: Feature Groups → Features → Feature Views
- Point-in-time correctness: `ML.FEATURES_AT_TIME`, `ML.ENTITY_FEATURES_AT_TIME`

</div>
<div class="col">

**Vector search** — ANN or brute-force with filter columns + crowding, but **only on the Optimized online store** (not the Bigtable-backed backend).

**Note** — defines its own source-table shapes (entity rows or history tables); **not** built on the shared 130K dataset like the other four.

</div>
</div>

**Best for** — teams that want a managed feature store + registry out of the box, without building or operating the serving layer.

---

<!-- _class: compact -->

## Sync Patterns Compared

How features get from BigQuery to the online store. **Freshness costs complexity.**

| Approach | Mechanism | Freshness | Notes |
|---|---|---|---|
| **BigQuery** | none — served in place | always fresh | no pipeline at all |
| **Spanner** | `EXPORT DATA format=CLOUD_SPANNER`; `INSERT OR UPDATE` upsert | seconds (continuous) | continuous query needs Enterprise reservation; change streams for reverse sync |
| **Bigtable** | `EXPORT DATA` (CLOUD_BIGTABLE); 4 tiers | hours → ms | one-time / scheduled / continuous (`APPENDS()`) / streaming Pub/Sub |
| **Valkey** | **Pub/Sub bridge** (no native export) | seconds | continuous query → Pub/Sub → subscriber → `HSET`; dead-letter + idempotency |
| **Vertex AI** | managed sync | managed | Google handles it |

Spanner and Bigtable are **native `EXPORT DATA` targets**; Valkey builds the bridge itself; BigQuery needs no sync; Vertex hides it.

---

<!-- _class: compact -->

## Direct Write &amp; Transaction Patterns

For real-time signals written *outside* the batch pipeline (counters, quotes, state).

| Approach | Write primitives | Atomicity |
|---|---|---|
| **BigQuery** | Storage Write API (append/DML) | n/a — read-serving layer |
| **Spanner** | DML, `INSERT OR UPDATE`, partitioned DML | **multi-row / multi-table ACID** (serializable) |
| **Bigtable** | single-row write, batch mutations, read-modify-write, check-and-mutate | **single-row** atomic |
| **Valkey** | `HSET`, `HINCRBY`/`HINCRBYFLOAT`, MULTI/EXEC, WATCH, Lua | **single-key** atomic (&lt;1 ms) |
| **Vertex AI** | offline-first (write to BigQuery source) | n/a |

Only **Spanner** spans rows and tables atomically. **Bigtable** and **Valkey** give the fastest single-entity atomic updates. **BigQuery/Vertex** are write-through-the-offline-store.

---

<!-- _class: compact -->

## Vector Search Compared

All four self-built stores now have **native** vector search — they differ on index type, pre-filtering, and latency.

| Approach | Index | Functions | Pre-filtering | Latency (130K) |
|---|---|---|---|---|
| **BigQuery** | IVF / TreeAH (or numpy) | `VECTOR_SEARCH` / numpy | SQL pushdown | ~ms after bulk read |
| **Spanner** | **ScaNN ANN** + exact | `APPROX_COSINE_DISTANCE` | **full SQL `WHERE`** | ~10–50 ms (filter+KNN, one query) |
| **Bigtable** | brute-force | `COSINE_DISTANCE` | row key only | scales with table size |
| **Valkey** | **HNSW** / FLAT | `FT.SEARCH` KNN | TAG + NUMERIC | **~2 ms @ ~89% recall** |
| **Vertex AI** | ANN / brute-force (**Optimized store only**) | managed | filter cols + crowding | managed |

**Spanner** for vector search inside a SQL query; **Valkey** for fastest standalone ANN; **BigQuery** for offline scale.

---

<!-- _class: compact -->

## Latency &amp; Cost Comparison

Measured point-read latency and the cost model, side by side.

| | **BigQuery** | **Spanner** | **Bigtable** | **Valkey** | **Vertex AI** |
|---|---|---|---|---|---|
| Single-entity read | 20–200 ms | ~5–10 ms | ~3–5 ms | **&lt;2 ms** | single-digit ms / sub-ms |
| Bulk (100+ entities) | **strong** (Storage API) | SQL `IN` / JOIN | batched reads | pipelined 0.12 ms/ea | managed |
| Query by any column | yes (SQL) | yes (indexes) | no (key only) | tag/numeric | feature-view |
| Multi-row transactions | no | **ACID** | single-row | single-key | no |
| Infrastructure | **$0 serverless** | provisioned PUs | nodes (~$500+/mo) | provisioned memory | managed |
| Scales to | petabytes | petabytes | petabytes | RAM ceiling | managed |
| Availability | BQ SLA | 99.99% / **99.999%** | multi-cluster | HA tier | managed SLA |

Cost roughly tracks the latency spectrum: serverless (pay-per-read) → provisioned compute → provisioned memory.

---

## Decision Framework

<div class="columns" style="margin-top: 6px;">
<div class="col">

**Start with latency + query needs:**

- **20–200 ms OK, want simplest path?**
  &rarr; **BigQuery** (zero infra, any-column filter, governance)
- **Need SQL filters / JOINs / ACID at serve time?**
  &rarr; **Spanner**
- **Need sub-5 ms key lookups + atomic writes + full control?**
  &rarr; **Bigtable**

</div>
<div class="col">

<br>

- **Need &lt;2 ms reads or real-time counters?**
  &rarr; **Valkey** (if data fits in memory)
- **Want it all managed, with a feature registry?**
  &rarr; **Vertex AI Feature Store**

**Then check the deciders:** multi-region strong consistency → Spanner; vector search *inside* SQL → Spanner; fastest standalone ANN → Valkey; petabyte key-value → Bigtable.

</div>
</div>

It's rarely either/or — many systems pair **BigQuery offline + one online store**, or use different stores per workload (e.g. Bigtable for serving, Valkey for hot counters).

---

## When NOT to Use Each

A quick gut-check against the common failure modes.

| Approach | Reconsider if… |
|---|---|
| **BigQuery** | you need single-digit-ms reads, or atomic real-time writes |
| **Spanner** | you need sub-3 ms reads, or want zero provisioned infra |
| **Bigtable** | you need to filter/JOIN on non-key columns, or want serverless |
| **Valkey** | the working set won't fit in RAM, or you need durable-by-default storage |
| **Vertex AI** | you need direct control over serialization, schema, or the serving layer |

Every store keeps **BigQuery as the durable source of truth** — so you can change your mind, or run more than one, without losing data.

---

<!-- _class: title -->
<!-- _paginate: false -->

# Explore the Series

<br>

**[BigQuery](./BigQuery/readme.md)** (3) · **[Spanner](./Spanner/readme.md)** (12) · **[Bigtable](./Bigtable/readme.md)** (15) · **[Valkey](./Valkey/readme.md)** (9) · **[Vertex AI](./vertex/readme.md)** (6)

<br>

Each series: a per-approach overview deck + hands-on notebooks, all on BigQuery as the offline store.

<br>

<div class="small">

45 notebooks · github.com/statmike/vertex-ai-mlops/MLOps/Feature Store

</div>
