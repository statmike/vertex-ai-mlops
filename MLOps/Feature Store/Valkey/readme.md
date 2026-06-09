![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2FMLOps%2FFeature+Store%2FValkey&file=readme.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/MLOps/Feature%20Store/Valkey/readme.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https://github.com/statmike/vertex-ai-mlops/blob/main/MLOps/Feature%2520Store/Valkey/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https://github.com/statmike/vertex-ai-mlops/blob/main/MLOps/Feature%2520Store/Valkey/readme.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https://github.com/statmike/vertex-ai-mlops/blob/main/MLOps/Feature%2520Store/Valkey/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https://github.com/statmike/vertex-ai-mlops/blob/main/MLOps/Feature%2520Store/Valkey/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
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
    <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/MLOps/Feature%20Store/Valkey/readme.md"><img src="https://www.svgrepo.com/download/5445/download-button.svg" alt="Download icon" width="20px"></a> <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/MLOps/Feature%20Store/Valkey/readme.md">Download File</a> <i>(right-click and "Save As")</i>
  </td>
</tr>
</table><br/><br/>

---
# Valkey Feature Store

> You are here: `vertex-ai-mlops/MLOps/Feature Store/Valkey/readme.md`

An ultra-low-latency in-memory feature store on [Memorystore for Valkey](https://cloud.google.com/memorystore/docs/valkey/valkey-overview). Sub-millisecond reads, native HNSW vector search via `FT.SEARCH`, atomic operations for real-time counters, and TTL-based feature expiration — for workloads where microseconds matter: real-time trading, gaming, ad bidding.

> **Also in this series: [Bigtable Feature Store](../Bigtable/readme.md), [BigQuery Feature Store](../BigQuery/readme.md), [Spanner Feature Store](../Spanner/readme.md), and [Vertex AI Feature Store](../vertex/readme.md)**
>
> This Valkey approach gives you the **fastest reads in the series** (<1ms) with native approximate nearest neighbor search. The trade-off: data must fit in memory, there's no native BigQuery export (sync via Pub/Sub bridge), and data is volatile unless persistence is configured. For sub-5ms disk-backed serving, see [Bigtable Feature Store](../Bigtable/readme.md). For SQL at the serving layer with ACID transactions, see [Spanner Feature Store](../Spanner/readme.md). For zero-infrastructure serving, see [BigQuery Feature Store](../BigQuery/readme.md). For a fully managed solution, see [Vertex AI Feature Store](../vertex/readme.md). All approaches use BigQuery as the offline store. See the [comparison table](../readme.md#choosing-an-approach) in the parent readme.

The data uses a 130K-entity dataset in BigQuery dataset `valkey_feature_store` — 26 entity groups (A–Z) × 5,000 entities. Each feature store series has its own independent BigQuery dataset with the same schema. Features are stored as hashes with key pattern `features:{entity_group}:{entity_id}`.

## Memorystore for Redis vs Memorystore for Valkey

Google Cloud offers **two** managed in-memory stores. This series uses **Memorystore for Valkey**, but every pattern works on either — Valkey is Redis-protocol compatible, so the same `redis-py` client and commands apply.

| | **Memorystore for Redis** | **Memorystore for Valkey** *(this series)* |
|---|---|---|
| **Engine** | Redis, up to 7.2 | Valkey 7.2 / 8.0 / 9.0 |
| **Governance** | Redis Inc. (source-available SSPL/RSAL since 2024) | **Open source, Linux Foundation** (BSD) |
| **Architecture** | Single primary + optional replica | **Cluster-native** (shards × nodes); also a Cluster-Mode-Disabled option |
| **Scale-out** | Vertical (bigger instance, max 300 GB) | **Horizontal** — add shards to scale capacity and throughput |
| **Newer features** | Capped at 7.2 | Hash-field TTL (`HEXPIRE`, 8.0+), newer commands, ongoing OSS development |
| **Provisioning** | `gcloud redis` (VPC peering, host/port) | `gcloud memorystore` (Private Service Connect automation) |
| **Client** | `redis.Redis` | `redis.Redis` (Cluster Disabled) or `redis.cluster.RedisCluster` (Cluster Enabled) |

**Why this series chooses Valkey:**
1. **Open governance** — Valkey is the Linux Foundation fork created after Redis's 2024 license change: BSD-licensed, community-governed, no vendor lock-in.
2. **Horizontal scale** — cluster mode shards data across nodes, past a single machine's memory/throughput ceiling.
3. **Newer capabilities** — e.g. per-field hash TTL (`HEXPIRE`, Valkey 8.0+) that Memorystore for Redis (7.2) lacks.
4. **Drop-in compatibility** — Redis-protocol compatible, so migration is mostly a provisioning change.

**Setup used here — Cluster Mode Disabled:** a single-shard instance so the notebooks connect with the standard `redis.Redis` client and all multi-key operations (MULTI/EXEC, multi-key Lua, pipelining) work without hash-tag/slot constraints. Throughout the notebooks, **🔄 Redis vs Valkey** callouts mark every place the Valkey approach differs from Memorystore for Redis.

## Environment Setup

### Option 1: Local environment

From this directory (`MLOps/Feature Store/Valkey/`):

**uv** (recommended)
```bash
uv sync
uv run python -m ipykernel install --user --name valkey-feature-store --display-name "Valkey Feature Store"
```

**pip**
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
python -m ipykernel install --user --name valkey-feature-store --display-name "Valkey Feature Store"
```

Then select the **Valkey Feature Store** kernel in your notebook.

### Option 2: Standalone

Each notebook includes an environment setup cell that installs required packages into your current kernel.

### Local Valkey for Development

If you don't have a Memorystore instance, run Valkey locally with Docker:

```bash
# Valkey 8 (includes hash-field TTL / HEXPIRE)
docker run -p 6379:6379 valkey/valkey:8

# For vector search (FT.CREATE / FT.SEARCH), use an image with the search module,
# e.g. Redis Stack (Redis-protocol compatible with the notebook code):
docker run -p 6379:6379 redis/redis-stack:latest
```

> The notebooks auto-detect a missing Memorystore instance and fall back to printing a local-dev hint. To point at a local instance, set the host/port in the connection cell to `localhost:6379` (no TLS).

## Notebooks — Run in This Order

Run the Environment notebook first. Notebooks 1–5 build core concepts sequentially. Notebooks 6–8 build on those foundations.

| # | Notebook | Prerequisites | What It Covers |
|---|----------|---------------|----------------|
| **0** | [Environment](./Valkey%20Feature%20Store%20-%20Environment.ipynb) | None | Redis-vs-Valkey comparison, BigQuery dataset (creates if needed), PSC service connection policy, Memorystore for Valkey instance (Cluster Mode Disabled, Valkey 8.0, 1 shard + 1 replica), TLS certificate, Pub/Sub topic + subscription, two-client pattern (decode + bytes) |
| **1** | [Fundamentals](./Valkey%20Feature%20Store%20-%20Fundamentals.ipynb) | NB0 | Bulk load 130K entities from BigQuery via pipelined HSET, hash data structure (HSET/HGET/HMGET/HGETALL), key naming convention, sub-ms point read latency, pipelined batch reads, comparison to Bigtable and Spanner |
| **2** | [Serialization](./Valkey%20Feature%20Store%20-%20Serialization.ipynb) | NB0, NB1 | Encoding BQ types to Redis strings/bytes, struct.pack for float32 embeddings (required for FT.SEARCH), JSON for complex types, NULL handling via field absence, storage size comparison, read latency by encoding |
| **3** | [Synchronization](./Valkey%20Feature%20Store%20-%20Synchronization.ipynb) | NB0 | Full Pub/Sub bridge: BigQuery Continuous Query → Pub/Sub → subscriber → HSET, idempotency via timestamp checks, error handling with dead-letter topics, backpressure control, batch writes via pipelining, propagation latency measurement |
| **4** | [TTL and Memory Management](./Valkey%20Feature%20Store%20-%20TTL%20and%20Memory%20Management.ipynb) | NB0, NB1 | EXPIRE/TTL/PERSIST for per-key expiration, eviction policies (allkeys-lru, volatile-lru, allkeys-lfu), feature freshness gating, memory monitoring (INFO memory, fragmentation ratio), TTL patterns for session/daily/permanent features |
| **5** | [Atomic Operations](./Valkey%20Feature%20Store%20-%20Atomic%20Operations.ipynb) | NB0, NB1 | HINCRBY/HINCRBYFLOAT for real-time counters, pipelining (sequential vs pipelined throughput), MULTI/EXEC atomic transactions, WATCH optimistic locking, combining batch features + real-time counters |
| **6** | [Serving Integration](./Valkey%20Feature%20Store%20-%20Serving%20Integration.ipynb) | NB0, NB1 | Train model on BigQuery, serve from Valkey (read → decode → predict), FastAPI endpoint, ConnectionPool (max_connections=50), concurrent serving benchmark (1–50 workers), comparison to Bigtable/Spanner serving latency |
| **7** | [Vector Search](./Valkey%20Feature%20Store%20-%20Vector%20Search.ipynb) | NB0, NB1, NB2 | Store embeddings as packed float32 bytes, FT.CREATE FLAT (brute-force) and HNSW (ANN) indexes, FT.SEARCH KNN queries, COSINE/L2/IP distance metrics, HNSW tuning (M, EF_CONSTRUCTION, EF_RUNTIME), FLAT vs HNSW latency benchmark at 130K vectors |
| **8** | [Production Deployment](./Valkey%20Feature%20Store%20-%20Production%20Deployment.ipynb) | NB0, NB1 | Terraform (google_redis_instance + Pub/Sub with dead-letter), real-time trading capstone: instrument features, expiring quotes (5s TTL), HNSW instrument matching, atomic P&L tracking (HINCRBYFLOAT), sorted sets for top movers, two-stage recommendation pipeline, load test |

## Key Concepts

- **[Redis Hashes](https://redis.io/docs/data-types/hashes/)** — One hash per entity, fields for each feature. Key pattern: `features:{entity_group}:{entity_id}`. Analogous to Bigtable row + column qualifiers.
- **[Pipelining](https://redis.io/docs/manual/pipelining/)** — Batch multiple commands into a single network roundtrip. Turns 100 individual reads (~100ms sequential) into one batch (~3ms).
- **[EXPIRE / TTL](https://redis.io/commands/expire/)** — Per-key expiration. In feature stores, TTL is a design tool — session features expire in 30 minutes, daily features in 24 hours, permanent features never expire.
- **[Eviction Policies](https://redis.io/docs/reference/eviction/)** — When memory is full, `volatile-lru` evicts TTL keys first, preserving permanent features. Unlike Bigtable (which scales disk), Valkey has a hard memory ceiling.
- **[HINCRBY / HINCRBYFLOAT](https://redis.io/commands/hincrby/)** — Atomic field increment. <1ms for counter updates (click counts, P&L). Bigtable's equivalent (`ReadModifyWriteRow`) takes ~3ms.
- **[FT.CREATE / FT.SEARCH](https://redis.io/docs/interact/search-and-query/)** — Native vector search with FLAT (brute-force) and HNSW (approximate nearest neighbor) indexes. The only production-grade ANN in this feature store series.
- **Pub/Sub Sync Bridge** — BigQuery Continuous Query → Pub/Sub → subscriber → HSET. The general-purpose pattern for syncing BigQuery to any target without native export (applies beyond Valkey).
- **Two-Client Pattern** — `decode_responses=True` for strings, `decode_responses=False` for raw bytes (embeddings). Required because `FT.SEARCH` vectors must be packed float32 bytes.

## Prerequisites

- A GCP project with billing enabled
- APIs enabled: Memorystore (`memorystore.googleapis.com`), Network Connectivity (`networkconnectivity.googleapis.com`), BigQuery, Pub/Sub
- A PSC service connection policy for the `gcp-memorystore` service class (NB0 creates it)
- Python >= 3.10
- For vector search (NB7, NB8): vector search is built into Memorystore for Valkey (instances created after 2024-09-13); locally, use a search-enabled image such as `redis-stack`
- For hash-field TTL (NB4 §8): Valkey 8.0+ (Memorystore for Valkey default)

## Documentation

| Topic | Link |
|-------|------|
| Memorystore for Valkey overview | [Overview](https://cloud.google.com/memorystore/docs/valkey/valkey-overview) |
| Memorystore for Valkey networking (PSC) | [Networking](https://cloud.google.com/memorystore/docs/valkey/networking) |
| Memorystore for Valkey vector search | [Vector search](https://cloud.google.com/memorystore/docs/valkey/about-vector-search) |
| Valkey commands | [Valkey docs](https://valkey.io/commands/) |
| Pipelining | [Pipelining](https://redis.io/docs/manual/pipelining/) |
| TTL and eviction | [Eviction](https://redis.io/docs/reference/eviction/) |
| redis-py Python client | [redis-py](https://redis-py.readthedocs.io/) |
| Memorystore for Valkey pricing | [Pricing](https://cloud.google.com/memorystore/docs/valkey/pricing) |
| Pub/Sub overview | [Overview](https://cloud.google.com/pubsub/docs/overview) |
| BigQuery continuous queries | [Continuous queries](https://cloud.google.com/bigquery/docs/continuous-queries-introduction) |
