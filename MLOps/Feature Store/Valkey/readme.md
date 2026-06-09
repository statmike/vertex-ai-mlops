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

An ultra-low-latency in-memory feature store on [Memorystore for Redis](https://cloud.google.com/memorystore/docs/redis/redis-overview) (Valkey-compatible). Sub-millisecond reads, native HNSW vector search via `FT.SEARCH`, atomic operations for real-time counters, and TTL-based feature expiration — for workloads where microseconds matter: real-time trading, gaming, ad bidding.

> **Also in this series: [Bigtable Feature Store](../Bigtable/readme.md), [BigQuery Feature Store](../BigQuery/readme.md), and [Spanner Feature Store](../Spanner/readme.md)**
>
> This Valkey approach gives you the **fastest reads in the series** (<1ms) with native approximate nearest neighbor search. The trade-off: data must fit in memory (max 300GB), there's no native BigQuery export (sync via Pub/Sub bridge), and data is volatile unless persistence is configured. For sub-5ms disk-backed serving, see [Bigtable Feature Store](../Bigtable/readme.md). For SQL at the serving layer with ACID transactions, see [Spanner Feature Store](../Spanner/readme.md). For zero-infrastructure serving, see [BigQuery Feature Store](../BigQuery/readme.md). All approaches use BigQuery as the offline store. See the [comparison table](../readme.md#choosing-an-approach) in the parent readme.

The data uses a 130K-entity dataset in BigQuery dataset `valkey_feature_store` — 26 entity groups (A–Z) × 5,000 entities. Each feature store series has its own independent BigQuery dataset with the same schema. Features are stored as Redis hashes with key pattern `features:{entity_group}:{entity_id}`.

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

### Local Redis for Development

If you don't have a Memorystore instance, run Redis locally with Docker:

```bash
# Basic Redis 7.2
docker run -p 6379:6379 redis:7.2

# Redis Stack (includes RediSearch for FT.CREATE / FT.SEARCH vector search)
docker run -p 6379:6379 redis/redis-stack:latest
```

## Notebooks — Run in This Order

Run the Environment notebook first. Notebooks 1–5 build core concepts sequentially. Notebooks 6–8 build on those foundations.

| # | Notebook | Prerequisites | What It Covers |
|---|----------|---------------|----------------|
| **0** | [Environment](./Valkey%20Feature%20Store%20-%20Environment.ipynb) | None | BigQuery dataset (creates if needed), Memorystore for Redis instance (Standard HA, 5GB, Redis 7.2), TLS certificate setup, Pub/Sub topic and subscription for sync bridge, two-client pattern (decode + bytes), memory sizing |
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
- APIs enabled: Memorystore for Redis, BigQuery, Pub/Sub
- Python >= 3.10
- For vector search (NB7, NB8): Redis 7.2+ with RediSearch module (included in Memorystore and `redis-stack`)

## Documentation

| Topic | Link |
|-------|------|
| Memorystore for Redis overview | [Overview](https://cloud.google.com/memorystore/docs/redis/redis-overview) |
| Redis data types | [Hashes](https://redis.io/docs/data-types/hashes/) |
| Pipelining | [Pipelining](https://redis.io/docs/manual/pipelining/) |
| TTL and eviction | [Eviction](https://redis.io/docs/reference/eviction/) |
| Vector search (RediSearch) | [Search and query](https://redis.io/docs/interact/search-and-query/) |
| HNSW vector index | [Vector similarity](https://redis.io/docs/interact/search-and-query/search/vectors/) |
| redis-py Python client | [redis-py](https://redis-py.readthedocs.io/) |
| Memorystore pricing | [Pricing](https://cloud.google.com/memorystore/docs/redis/pricing) |
| Pub/Sub overview | [Overview](https://cloud.google.com/pubsub/docs/overview) |
| BigQuery continuous queries | [Continuous queries](https://cloud.google.com/bigquery/docs/continuous-queries-introduction) |
