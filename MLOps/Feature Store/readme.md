![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2FMLOps%2FFeature+Store&file=readme.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/MLOps/Feature%20Store/readme.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https://github.com/statmike/vertex-ai-mlops/blob/main/MLOps/Feature%2520Store/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https://github.com/statmike/vertex-ai-mlops/blob/main/MLOps/Feature%2520Store/readme.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https://github.com/statmike/vertex-ai-mlops/blob/main/MLOps/Feature%2520Store/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https://github.com/statmike/vertex-ai-mlops/blob/main/MLOps/Feature%2520Store/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
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
    <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/MLOps/Feature%20Store/readme.md"><img src="https://www.svgrepo.com/download/5445/download-button.svg" alt="Download icon" width="20px"></a> <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/MLOps/Feature%20Store/readme.md">Download File</a> <i>(right-click and "Save As")</i>
  </td>
</tr>
</table><br/><br/>

---
# Feature Management
> You are here: `vertex-ai-mlops/MLOps/Feature Store/readme.md`

A core part of MLOps, for going from model to MODELS, is feature management. A feature store provides an organized way to manage, serve, and share features across the ML lifecycle — from training to online serving. The offline store holds the full history of feature values (for training, backfills, and point-in-time joins), while the online store serves the latest feature values at low latency (for real-time inference).

This section covers **five approaches** to building a feature store on Google Cloud. All use **BigQuery as the offline analytical engine** but take different paths for online serving — spanning the full latency/cost spectrum from serverless reads straight out of BigQuery to sub-millisecond in-memory serving. Four of them (BigQuery, Spanner, Bigtable, Valkey) are self-built on the same 130K-entity dataset so you can compare them directly; the fifth (Vertex AI Feature Store) is Google's fully managed option.

## The Latency Spectrum

```
BigQuery Storage API  →  Spanner       →  Bigtable      →  Valkey
20–200 ms                ~5–10 ms          ~3–5 ms          <2 ms
serverless, no infra     SQL + ACID        key-based        in-memory
serve from offline       secondary idx     full control     volatile
```

Plus **Vertex AI Feature Store** — managed serving (Bigtable-backed or Optimized) with a built-in feature registry, sitting alongside the spectrum rather than on it.

## Choosing an Approach

Ordered along the latency spectrum (fastest reads on the right), with the managed option last:

| | **[BigQuery](./BigQuery/readme.md)** | **[Spanner](./Spanner/readme.md)** | **[Bigtable](./Bigtable/readme.md)** | **[Valkey](./Valkey/readme.md)** | **[Vertex AI FS](./vertex/readme.md)** |
|---|---|---|---|---|---|
| **Philosophy** | No online store — serve from BigQuery storage | SQL database at the serving layer | Self-managed wide-column store | Sub-ms in-memory store | Managed — Google runs the serving infra |
| **Online store** | None ([Storage Read API](https://cloud.google.com/bigquery/docs/reference/storage)) | [Cloud Spanner](https://cloud.google.com/spanner/docs/overview) | [Cloud Bigtable](https://cloud.google.com/bigtable/docs/overview) | [Memorystore for Valkey](https://cloud.google.com/memorystore/docs/valkey/valkey-overview) | [Bigtable-backed or Optimized](https://cloud.google.com/vertex-ai/docs/featurestore/latest/overview) |
| **Read latency** | 20–200 ms | ~5–10 ms | ~3–5 ms | **&lt;2 ms** | single-digit ms / sub-ms |
| **Query model** | SQL (full) | **SQL — filter any column, JOINs, ACID** | key / prefix only | key + `FT.SEARCH` | feature-view lookup |
| **Sync from BigQuery** | none (always fresh) | `EXPORT DATA` (CLOUD_SPANNER) + change streams | [`EXPORT DATA`](https://cloud.google.com/bigquery/docs/export-to-bigtable) (CLOUD_BIGTABLE) | Pub/Sub bridge | managed |
| **Write path** | through BigQuery | DML + ACID transactions | direct writes, atomic RMW | `HSET`/`HINCRBY`, atomic | through BigQuery |
| **Transactions** | n/a (read serving) | **multi-row / multi-table ACID** | single-row atomic | single-key atomic | n/a |
| **Vector search** | IVF / TreeAH (native SQL) | **ScaNN ANN + exact, SQL-filtered** | brute-force `COSINE_DISTANCE` | **HNSW (native ANN)** | aNN / brute-force (built in) |
| **Availability** | BigQuery SLA (serverless) | regional 99.99% / multi-region **99.999%** | multi-cluster replication | HA tier (primary + replica) | managed SLA |
| **Infrastructure** | none (serverless) | provisioned PUs (autoscaling) | provisioned nodes ($500+/mo) | provisioned memory | managed |
| **Best for** | Simplest path; 20–200 ms OK; bulk reads + governance | SQL filtering/JOINs + ACID at serve time; multi-region | Sub-5 ms key lookups, atomic writes, full control | Microsecond reads; real-time counters; HNSW retrieval | Managed infra + feature registry out of the box |

No single approach is universally better — they solve different problems:

- **BigQuery** eliminates the online store entirely — no sync, no infrastructure — for workloads where 20–200 ms is acceptable. Inherits BigQuery governance ([Dataplex](https://cloud.google.com/dataplex/docs/overview): discovery, lineage, column-level security).
- **Spanner** makes the serving layer a real SQL database: secondary-index lookups on any column, serving-time JOINs, multi-row/multi-table ACID transactions, native vector search you can combine with a SQL `WHERE`, and automatic multi-region with strong consistency (99.999%).
- **Bigtable** gives direct access to the serving layer for sub-5 ms key lookups, atomic real-time writes (counters, state) without round-tripping through BigQuery, custom Pub/Sub + Dataflow pipelines, and multi-region replication.
- **Valkey** is the fastest reads in the set (&lt;2 ms in-memory) with native HNSW vector search and atomic counters — for trading, gaming, ad bidding where microseconds matter. Data must fit in memory and BigQuery remains the durable source of truth.
- **Vertex AI Feature Store** minimizes operational overhead with a managed feature registry, automatic sync, and built-in vector search.

## Presentations

Each self-built series ships an overview slide deck (PDF):

- [BigQuery Feature Store — Overview](./BigQuery/BigQuery%20Feature%20Store%20-%20Overview.pdf)
- [Spanner Feature Store — Overview](./Spanner/Spanner%20Feature%20Store%20-%20Overview.pdf)
- [Bigtable Feature Store — Overview](./Bigtable/Bigtable%20Feature%20Store%20-%20Overview.pdf)
- [Valkey Feature Store — Overview](./Valkey/Valkey%20Feature%20Store%20-%20Overview.pdf)

## [Vertex AI Feature Store](./vertex/readme.md)

[Vertex AI Feature Store](https://cloud.google.com/vertex-ai/docs/featurestore/latest/overview) is Google Cloud's managed feature store service. It uses BigQuery as the offline store and provides managed online serving with two options: Cloud Bigtable online serving (highly scalable) and Optimized online serving (ultra-low latency). The built-in feature registry (Feature Groups, Features, Feature Views) tracks lineage and simplifies serving.

Notebooks and workflows:
- [Feature Store](./vertex/Feature%20Store.ipynb) - Complete workflow for Vertex AI Feature Store
- [Feature Store - Embeddings](./vertex/Feature%20Store%20-%20Embeddings.ipynb) - Embedding features with vector matching and entity matching
- [Feature Focused Data Architecture](./vertex/Feature%20Focused%20Data%20Architecture.ipynb) - Data architecture patterns for feature management
- [Feature Store (Legacy)](./vertex/Feature%20Store%20%28Legacy%29.ipynb) - The pre-2023 legacy Vertex AI Feature Store
- [Feature Retrieval](./vertex/fs-feature-retrieval.ipynb) - Feature retrieval workflows
- [Data Sources](./vertex/feature-store-data-sources.ipynb) - Data source integration

## [Bigtable Feature Store](./Bigtable/readme.md)

Building a feature store directly on [Cloud Bigtable](https://cloud.google.com/bigtable/docs/overview) for maximum control over the serving layer. Bigtable's direct write path means applications can update features in real time — without round-tripping through BigQuery — using single-row writes, batch mutations, or atomic read-modify-write operations. Features can also stream in from external sources via [Pub/Sub](https://cloud.google.com/pubsub/docs/overview) and [Dataflow](https://cloud.google.com/dataflow/docs/overview) pipelines. With [multi-cluster replication](https://cloud.google.com/bigtable/docs/replication-overview), the online store can span zones or regions for high availability and geo-local reads.

15 notebooks covering serialization strategies, sync patterns (one-time, scheduled, continuous, streaming), time-travel, direct writes, key design, schema evolution, serving integration, dynamic feature computation, production operations (Terraform, CI/CD, multi-language clients), vector embeddings with KNN search, multi-cluster replication, Bigtable emulator for local development, and a capstone recommendation engine — using BigQuery as the offline analytical engine and Bigtable for sub-10ms online serving.

## [BigQuery Feature Store](./BigQuery/readme.md)

Serving features directly from BigQuery via the [Storage Read API](https://cloud.google.com/bigquery/docs/reference/storage) — no online store, no sync pipelines, no infrastructure to manage. The Storage Read API bypasses the query engine entirely, reading directly from BigQuery's storage layer and streaming [Apache Arrow](https://arrow.apache.org/) record batches over parallel gRPC connections. Combined with session caching and table clustering, this creates a feature serving layer with 20–200ms latency. Because features stay in BigQuery, you inherit its governance layer — [Dataplex](https://cloud.google.com/dataplex/docs/overview) for discovery, column-level security, data lineage, and policy tags — without building anything yourself.

3 notebooks covering environment setup (dataset and synthetic table creation), standard BQ query baselines, Storage Read API core patterns, session caching with a reusable `FeatureSessionPool`, FastAPI serving with async integration and concurrency scaling, multi-stream parallelism, bulk feature hydration (where Storage API dominates Bigtable at 100+ entities), in-memory vector similarity with numpy, advanced patterns (multi-table reads, dynamic columns, ad-hoc filtering, time travel), honest three-way latency and cost comparisons (BQ query vs Storage API vs Bigtable), and Cloud Run deployment with per-entity and combined-restriction batch endpoints, entity count scaling, concurrency benchmarks, sustained load testing, spike burst testing, sync vs async pattern comparison, traffic splitting, and autoscaling configuration.

## [Spanner Feature Store](./Spanner/readme.md)

A SQL-powered online feature store on [Cloud Spanner](https://cloud.google.com/spanner/docs/overview). Spanner trades a few milliseconds versus key-value stores for **SQL at the serving layer** — secondary-index lookups on any column, serving-time JOINs across feature tables, and multi-row/multi-table ACID transactions — plus automatic multi-region with strong consistency and a 99.999% SLA. It's also a native [vector search](https://cloud.google.com/spanner/docs/find-k-nearest-neighbors) engine: exact KNN and ScaNN-based approximate search you can combine with a SQL `WHERE` clause in a single query.

12 notebooks covering environment setup (Enterprise-edition instance for vector search), fundamentals (composite primary keys, query plans via `PROFILE`/`rows_scanned`, mutations vs DML), synchronization (`EXPORT DATA` reverse-ETL, continuous queries, change streams → BigQuery), secondary indexes (covering/`STORING`, `NULL_FILTERED`, write amplification), interleaved tables (co-location, `ON DELETE CASCADE`), transactions (abort-retry concurrency, partitioned DML, the 80k-mutation limit, staleness modes), schema evolution (online DDL, generated columns, type-change recipe), serving integration (read-method comparison, session pools, FastAPI), native vector embeddings (exact KNN + ScaNN ANN with SQL pre-filtering), multi-region and HA, the Spanner emulator for local development/CI, and a capstone recommendation engine (SQL-filtered vector KNN + serving-time JOINs + atomic updates, Terraform, load test) — validated end-to-end on a live 100 PU Enterprise instance.

## [Valkey Feature Store](./Valkey/readme.md)

An ultra-low-latency in-memory feature store on [Memorystore for Valkey](https://cloud.google.com/memorystore/docs/valkey/valkey-overview) — the fastest reads in the set (&lt;2 ms) with native HNSW vector search, atomic operations for real-time counters, and TTL-based feature expiration. For workloads where microseconds matter: real-time trading, gaming, ad bidding. Since Valkey has no native BigQuery export, sync runs through a [Pub/Sub](https://cloud.google.com/pubsub/docs/overview) bridge; data lives in memory with BigQuery as the durable source of truth.

9 notebooks covering environment setup (Memorystore for Valkey, with a Redis-vs-Valkey comparison), fundamentals (hashes, sub-ms reads, pipelining), serialization (encoding BQ types, `struct.pack` for float32 embeddings), synchronization (BigQuery Continuous Query → Pub/Sub → subscriber, dead-letter handling), TTL and memory management (eviction policies, freshness gating), atomic operations (`HINCRBY`, MULTI/EXEC, WATCH, Lua, Streams), serving integration (connection pooling, FastAPI), vector search (`FT.CREATE`/`FT.SEARCH` with HNSW + FLAT indexes, recall tuning), and a production capstone (real-time trading: expiring quotes, HNSW instrument matching, atomic P&L) — using BigQuery as the offline engine and Valkey for sub-millisecond online serving.
