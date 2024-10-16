![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2FApplied+GenAI%2FRetrieval&file=readme.md)
<!--- header table --->
<table align="left">     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%20GenAI/Retrieval/readme.md">
      <img src="https://cloud.google.com/ml-engine/images/github-logo-32px.png" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</table><br/><br/><br/><br/>

---
# Retrieval
> You are here: `vertex-ai-mlops/Applied GenAI/Retrieval/readme.md`

<p align="center"><center>
    <img src="../resources/images/created/applied-genai/overview-build-index.png" width="75%">
</center></p>

Once [embeddings](../Embeddings/readme.md) are generated for the pieces of content ([chunks](../Chunking/readme.md)), it is helpful to create a **retrieval** system that can be queried for similar matching chunks. This could be a brute-force solution or an index-based system that surfaces neighbors for query embeddings. Some solutions can store embedding vectors along with the text/image as well as other metadata. Other systems are designed to return the matching entity IDs, and a second step is needed to retrieve the text/image related to those entities. This section will review implementing a retrieval system with various Google Cloud offerings that span the set of features introduced here and can be used individually or together to fit your application workflow(s).

This retrieval process is what is usually referred to as retrieval augmented generation, or RAG, but is actually just the retrieval portion. Read more about the full process in the parent series of this content: [Applied GenAI](../readme.md), which includes a common next step of [ranking/re-ranking](../Ranking/readme.md) of the matched content.

**Workflows:**

- [Retrieval - Local With Numpy](Retrieval%20-%20Local%20With%20Numpy.ipynb)
- [Retrieval - BigQuery Vector Indexing And Search](Retrieval%20-%20BigQuery%20Vector%20Indexing%20And%20Search.ipynb)
- [Retrieval - Vertex AI Feature Store](Retrieval%20-%20Vertex%20AI%20Feature%20Store.ipynb)

**More To Come**

- Local With Scaan
- Vertex AI Vector Search
- Alloy DB
- Spanner
- LlamaIndex
- Custom Endpoints on GCS and Vertex With Numpy


---

**Notes To Incorporate On Future Revision**

---
Important Notes About Setting Up An Index

Working with embeddings, a vectors of numbers, a list of floating points... the nature of vector database solutions.  These are considerations to be taken regardless of the solution being used.  Here Vertex AI Feature Store, which has many configurable options to aide in this.

- **Storage**
    - filter attributes: values that can be used to limit a search
    - crowding attributes: limit the number of matches with these attributes
    - additional columns inline, like the text chunk an embedding represents to prevent the additional step of retrieving data for matches
- **Indexing**
    - a brute force configuration to force search across all embeddings, good for benchmarkinng and ground truth retrieval
    - a method of segmenting embeddings, primarily:
        - inverted file index (IVF), or k-means clustering of embeddings
        - TreeAH, or [ScaNN](https://research.google/blog/announcing-scann-efficient-vector-similarity-search/), for compressing embeddings
    - setting to configure the size of a cluster (IVF) or leaf nodes (TreeAH)
    - distance type to set how matches are computed: dot product, euclidean, manhatten, cosine
- **Retrieval**
    - a brute force override to retrieve ground truth across the full index
    - ability to control the number of neighbors retrieved at query time
    - option to set distance calcuation type at query time
    - usage of filtering and crowding attributes to tailor neighbors list