![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2FApplied+GenAI%2FRetrieval%2FVector+Search+2&file=readme.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%20GenAI/Retrieval/Vector%20Search%202/readme.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520GenAI/Retrieval/Vector%2520Search%25202/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520GenAI/Retrieval/Vector%2520Search%25202/readme.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520GenAI/Retrieval/Vector%2520Search%25202/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520GenAI/Retrieval/Vector%2520Search%25202/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
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
    <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/Applied%20GenAI/Retrieval/Vector%20Search%202/readme.md"><img src="https://www.svgrepo.com/download/5445/download-button.svg" alt="Download icon" width="20px"></a> <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/Applied%20GenAI/Retrieval/Vector%20Search%202/readme.md">Download File</a> <i>(right-click and "Save As")</i>
  </td>
</tr>
</table><br/><br/>

---
# Retrieval - Vertex AI Vector Search 2
> You are here: `vertex-ai-mlops/Applied GenAI/Retrieval/Vector Search 2/readme.md`

[Vertex AI Vector Search 2](https://docs.cloud.google.com/gemini-enterprise-agent-platform/build/vector-search-2/overview) is a fully managed, serverless vector database that unifies data and vector storage in a single **Collection**. It eliminates the operational complexity of provisioning instances, deploying indexes to endpoints, and managing separate embedding pipelines. Data is stored as **DataObjects** — JSON documents with structured fields and vector embeddings — and can be searched using vector similarity, semantic search (with auto-generated embeddings), full-text keyword search, or any combination via hybrid search with fusion ranking.

This is a significant evolution from [Vertex AI Vector Search (1.0)](../Retrieval%20-%20Vertex%20AI%20Vector%20Search.ipynb), which requires creating indexes from GCS-hosted vectors, deploying them to managed endpoints, and performing a separate lookup step to retrieve the text associated with matched IDs. Vector Search 2 stores everything together — vectors, text, and metadata — and returns complete results in a single call.

**Key Capabilities:**
- **Auto-Embedding**: Configure an embedding model (e.g., `text-embedding-005`, `gemini-embedding-001`) in the collection schema and VS2 generates embeddings automatically at import and query time — no client-side embedding pipeline needed.
- **Bring Your Own Embeddings (BYOE)**: Provide pre-computed embeddings alongside auto-embedded fields in the same collection.
- **Semantic Search**: Pass natural language text and VS2 auto-embeds the query to find similar results by meaning.
- **Full-Text Search**: Built-in keyword search with enhanced query mode supporting OR operators, phrase matching, and negation.
- **Hybrid Search**: Combine any mix of vector, semantic, and text searches in a single call with Reciprocal Rank Fusion (RRF) and optional VertexRanker semantic reranking.
- **MongoDB-Style Filters**: Expressive filter language (`$eq`, `$in`, `$gt`, `$and`, `$or`, etc.) for structured retrieval and pre-filtered search.
- **Serverless ANN Indexes**: Self-tuning approximate nearest neighbor indexes powered by Google's ScaNN algorithm — no partition configuration needed.

## Environment Setup

### Option 1: Local environment

From this directory (`Applied GenAI/Retrieval/Vector Search 2/`):

**uv** (recommended)
```bash
uv sync
uv run python -m ipykernel install --user --name retrieval-vertex-ai-vector-search-2 --display-name "Retrieval - Vertex AI Vector Search 2"
```

**pip**
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
python -m ipykernel install --user --name retrieval-vertex-ai-vector-search-2 --display-name "Retrieval - Vertex AI Vector Search 2"
```

Then select the **Retrieval - Vertex AI Vector Search 2** kernel in your notebook.

### Option 2: Standalone

Each notebook includes an environment setup cell that installs required packages into your current kernel.

## Workflows

- [Retrieval - Vertex AI Vector Search 2](Retrieval%20-%20Vertex%20AI%20Vector%20Search%202.ipynb)
    - End-to-end workflow: create a collection, load the same 9,040 embeddings used across all retrieval workflows, and demonstrate every search and query capability — vector search (BYOE), semantic search (auto-embedding), text search, filtered search, hybrid search with RRF, reranking with VertexRanker, data object management, and a simple RAG example. All searches use brute-force kNN (no index required).
- [Retrieval - Vertex AI Vector Search 2 — ANN Indexes](Retrieval%20-%20Vertex%20AI%20Vector%20Search%202%20-%20ANN%20Indexes.ipynb)
    - Companion to the main notebook: creates ANN indexes on the collection, demonstrates vector/semantic/filtered search against ANN indexes, and measures recall@K against brute-force kNN ground truth.
- [Retrieval - Vertex AI Vector Search 2 — RAG Engine](Retrieval%20-%20Vertex%20AI%20Vector%20Search%202%20-%20RAG%20Engine.ipynb)
    - Uses [RAG Engine](https://docs.cloud.google.com/gemini-enterprise-agent-platform/build/rag-engine/rag-overview) with Vector Search 2 as the managed backend: creates a RAG corpus, imports source PDFs (RAG Engine handles parsing, chunking, and embedding), retrieves contexts, and generates grounded answers with Gemini.

For more context on how this fits into the retrieval landscape, see the parent [Retrieval](../readme.md) series which compares all Google Cloud retrieval solutions side by side.

---
