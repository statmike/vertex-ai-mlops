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

A core part of MLOps, for going from model to MODELS, is feature management. A feature store provides an organized way to manage, serve, and share features across the ML lifecycle — from training to online serving.

This section covers feature store implementations using different serving backends:

## [Vertex AI Feature Store](./vertex/readme.md)

[Vertex AI Feature Store](https://cloud.google.com/vertex-ai/docs/featurestore/latest/overview) uses BigQuery as the offline store and provides managed online serving with two options: Cloud Bigtable online serving (highly scalable) and Optimized online serving (ultra-low latency).

Notebooks and workflows:
- [Feature Store](./vertex/Feature%20Store.ipynb) - Complete workflow for Vertex AI Feature Store
- [Feature Store - Embeddings](./vertex/Feature%20Store%20-%20Embeddings.ipynb) - Embedding features with vector matching and entity matching
- [Feature Focused Data Architecture](./vertex/Feature%20Focused%20Data%20Architecture.ipynb) - Data architecture patterns for feature management
- [Feature Store (Legacy)](./vertex/Feature%20Store%20%28Legacy%29.ipynb) - The pre-2023 legacy Vertex AI Feature Store
- [Feature Retrieval](./vertex/fs-feature-retrieval.ipynb) - Feature retrieval workflows
- [Data Sources](./vertex/feature-store-data-sources.ipynb) - Data source integration

## [Bigtable Feature Store](./Bigtable/MYPLANS.md)

Building a high-performance feature store directly on Cloud Bigtable for maximum control over the serving layer. Covers serialization strategies, sync patterns, time-travel, schema evolution, and production observability.
