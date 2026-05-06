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

This section covers two approaches to building a feature store on Google Cloud — both use BigQuery as the offline analytical engine but take fundamentally different paths for online serving:

## Choosing an Approach

| | **[Vertex AI Feature Store](./vertex/readme.md)** | **[Bigtable Feature Store](./Bigtable/readme.md)** |
|---|---|---|
| **Philosophy** | Managed — Google handles the online serving infrastructure | Self-managed — you own every layer of the serving stack |
| **Online store** | [Bigtable-backed](https://cloud.google.com/vertex-ai/docs/featurestore/latest/overview) (scalable) or Optimized (ultra-low latency) | [Cloud Bigtable](https://cloud.google.com/bigtable/docs/overview) directly — full control over instances, clusters, and tuning |
| **Offline store** | BigQuery (managed by Feature Store) | BigQuery (managed by you) |
| **Sync** | Managed sync from BigQuery to online store | You choose: [`EXPORT DATA`](https://cloud.google.com/bigquery/docs/export-to-bigtable), [scheduled queries](https://cloud.google.com/bigquery/docs/scheduling-queries), [continuous queries](https://cloud.google.com/bigquery/docs/continuous-queries-introduction), or streaming via [Pub/Sub](https://cloud.google.com/pubsub/docs/overview) + [Dataflow](https://cloud.google.com/dataflow/docs/overview) |
| **Write path** | Through BigQuery (offline-first) | Direct writes, batch mutations, atomic operations — bypass BigQuery entirely for real-time features |
| **Read latency** | Single-digit ms (Bigtable) or sub-ms (Optimized) | Single-digit ms with full tuning control ([app profiles](https://cloud.google.com/bigtable/docs/app-profiles), priority routing, connection pooling) |
| **Availability** | Managed SLA | [Multi-cluster replication](https://cloud.google.com/bigtable/docs/replication-overview) across zones or regions — you configure the topology |
| **Feature registry** | Built-in (Feature Groups, Feature Views) | Self-describing schema rows + versioning (you build it) |
| **Embeddings** | Vector search with aNN/brute-force matching built in | Store embeddings as features; bring your own vector search |
| **Best for** | Teams that want managed infrastructure and a feature registry out of the box | Teams that need maximum control, streaming writes, multi-region serving, or custom serialization |

Neither approach is universally better — they solve different problems. Vertex AI Feature Store minimizes operational overhead with a managed feature registry, automatic sync, and built-in vector search. Bigtable Feature Store gives you direct access to the serving layer for use cases that need streaming writes from applications (without round-tripping through BigQuery), custom data pipelines from Pub/Sub and Dataflow, multi-region replication, fine-grained read/write priority isolation, and full control over serialization and schema evolution.

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

10 notebooks covering serialization strategies, sync patterns (one-time, scheduled, continuous, streaming), time-travel, direct writes, key design, schema evolution, serving integration, dynamic feature computation, and production operations — using BigQuery as the offline analytical engine and Bigtable for sub-10ms online serving.
