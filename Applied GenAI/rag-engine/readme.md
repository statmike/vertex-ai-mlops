![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2FApplied+GenAI%2Frag-engine&file=readme.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%20GenAI/rag-engine/readme.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520GenAI/rag-engine/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520GenAI/rag-engine/readme.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520GenAI/rag-engine/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520GenAI/rag-engine/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
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
</table><br/><br/>

---
# Vertex AI RAG Engine

In RAG applications, the tasks for ingesting, chunking, embedding, indexing, retrieval, ranking, and generation all have great services and options within Vertex AI and Google Cloud. The [Vertex AI RAG Engine](https://cloud.google.com/vertex-ai/generative-ai/docs/rag-engine/rag-overview) is an SDK approach to automating these steps. The SDK makes opinionated choices for many of the services while surfacing important configuration parameters for the user. It also offers a direct entry point to the individual services in some cases for manually overriding the workflow when necessary.

Here we will show two paths with RAG Engine. A simple path using as many defaults as possible to illustrate the simplicity the service offers. Then, a more customized path where the vector database is independently set up and configured to augment the RAG engine with hybrid search enabled by [Vertex AI Vector Search](https://cloud.google.com/vertex-ai/docs/vector-search/overview).


RAG Engine Setup:
1. Create Corpus
2. Import Documents
3. Retrieval Points: 
   1. Matching Chunks
   2. Re-Ranked Matching Chunks
4. Generated Answers with a Tool to Retrieve

Workflows
- [Simple RAG Engine Workflow](./rag-engine-simple.py): This workflow demonstrates an end-to-end RAG implementation using the RAG Engine SDK with its default managed vector database. It covers creating a corpus, importing a PDF document from GCS, and then demonstrates multiple retrieval strategies: retrieval with basic vector search, retrieval with re-ranking, and using an LLM as a re-ranker. Finally, it shows how to use the RAG corpus and retrieval settings as a tool for a generative model to answer questions based on the document with a single call.
- [RAG Engine With a Custom Vector Search Backend](./rag-engine-vector-search.py): This workflow shows how to configure the RAG Engine to use a pre-existing Vertex AI Vector Search index as its vector database. It walks through creating a streaming Vector Search index and an endpoint, deploying the index, and then passing these resources to the RAG Engine during corpus creation. This allows for more control over the vector database while still leveraging the RAG Engine's orchestration for ingestion and retrieval.
- [Hybrid Search With Vector Search and Sparse Embeddings](./rag-engine-vector-search-hybrid.py): This workflow builds on the Vector Search backend setup to add hybrid search capabilities by combining dense embeddings with sparse embeddings. It demonstrates retrieving all chunks from the index, creating BM25-based sparse embeddings using custom text preprocessing (lemmatization, n-grams), and upserting sparse embeddings back to the index. The workflow then shows how to perform dense-only, sparse-only, and hybrid queries using Vertex AI Vector Search's HybridQuery with configurable alpha values for balancing semantic and keyword-based retrieval.

