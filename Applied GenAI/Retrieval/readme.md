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
- Custom Endpoinnts on GCS and Vertex With Numpy