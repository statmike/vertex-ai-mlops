![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2FApplied+GenAI%2FEmbeddings%2Flegacy&file=readme.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%20GenAI/Embeddings/legacy/readme.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520GenAI/Embeddings/legacy/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520GenAI/Embeddings/legacy/readme.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520GenAI/Embeddings/legacy/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520GenAI/Embeddings/legacy/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
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
    <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/Applied%20GenAI/Embeddings/legacy/readme.md"><img src="https://www.svgrepo.com/download/5445/download-button.svg" alt="Download icon" width="20px"></a> <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/Applied%20GenAI/Embeddings/legacy/readme.md">Download File</a> <i>(right-click and "Save As")</i>
  </td>
</tr>
</table><br/><br/>

---
# Embeddings (Legacy)
> You are here: `vertex-ai-mlops/Applied GenAI/Embeddings/legacy/readme.md`

> **NOTE** - the notebooks in this folder were previously in the parent [Embeddings](../readme.md) folder and have been moved here to preserve them while newer content uses better techniques and current models. These notebooks are built on the deprecating `vertexai` SDK. They remain for reference, but for current work see the latest content in the [main Embeddings folder](../readme.md) — start with [Embeddings API](../Embeddings%20API.ipynb).

## Retired Notebooks

- [Vertex AI Text Embeddings API](./Vertex%20AI%20Text%20Embeddings%20API.ipynb) — text embeddings with the `vertexai` SDK (`TextEmbeddingModel`). Replaced by [Embeddings API](../Embeddings%20API.ipynb).
- [Vertex AI Multimodal Embeddings](./Vertex%20AI%20Multimodal%20Embeddings.ipynb) — text/image/video embeddings with `MultiModalEmbeddingModel` (`multimodalembedding@001`). Replaced by [Embeddings API](../Embeddings%20API.ipynb).
- [Vertex AI GenAI Embeddings](./Vertex%20AI%20GenAI%20Embeddings.ipynb) — embeddings for text and images with TensorBoard Projector visualization. See [Embeddings API](../Embeddings%20API.ipynb) for current embedding generation and [Bring Embeddings to Life With Visualization Techniques](../Bring%20Embeddings%20to%20Life%20With%20Visualization%20Techniques.ipynb) for visualization.
- [Vertex AI GenAI Embeddings - As Features For Hierarchical Classification](./Vertex%20AI%20GenAI%20Embeddings%20-%20As%20Features%20For%20Hierarchical%20Classification.ipynb) — a BigQuery ML + BigFrames workflow using the deprecated `PaLM2TextEmbeddingGenerator`. Replaced and modernized in [`data+ai/bq-ml/workflows/embeddings_classification/`](../../../data+ai/bq-ml/workflows/embeddings_classification/) (`AI.EMBED` + native SQL `BOOSTED_TREE_CLASSIFIER`).
