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

**Workflows:** Implement retrieval with different storage and indexing solutions:

- [Retrieval - Local With Numpy](Retrieval%20-%20Local%20With%20Numpy.ipynb)
- [Retrieval - BigQuery Vector Indexing And Search](Retrieval%20-%20BigQuery%20Vector%20Indexing%20And%20Search.ipynb)
- [Retrieval - Vertex AI Feature Store](Retrieval%20-%20Vertex%20AI%20Feature%20Store.ipynb)
- [Retrieval - Vertex AI Vector Search](Retrieval%20-%20Vertex%20AI%20Vector%20Search.ipynb)
- In Progress - Working - Needs Writeup: [Retrieval - Spanner](Retrieval%20-%20Spanner.ipynb)
- In Progress - Working - Needs Writeup: [Retrieval - Firestore](Retrieval%20-%20Firestore.ipynb)
- In Progress - Setup Only: [Retrieval - AlloyDB For PostgreSQL](Retrieval%20-%20AlloyDB%20For%20PostgreSQL.ipynb)
- In Progress - Working - Needs Writeup: [Retrieval - Memorystore](Retrieval%20-%20Memorystore.ipynb)
- In Progress - Working - Needs Writeup: [Retrieval - Bigtable](Retrieval%20-%20Bigtable.ipynb)
- Upcoming: Retrieval - CloudSQL

**More To Come**

- Local With Scaan
- Vertex AI LlamaIndex
- Custom Endpoints on Cloud Run and Vertex With Numpy
- Integrations with Langchain For Vertex AI
- Integrations with Langchain OSS

## Important Notes About Setting Up An Index Solution

When working with embeddings—vectors of numbers represented as lists of floating points—there are key considerations for choosing and configuring a vector database solution.  Here are some crucial aspects to keep in mind:

- **Storage**
    - **Filterable attributes:**  Include values that can be used to filter search results (e.g., date, category, source).
    - **Crowding attributes:**  Use these to limit the number of similar matches returned (e.g., author, publication).
    - **Inline data:** Store the text chunk associated with each embedding directly to avoid an extra retrieval step.
    - **Metadata:**  Include relevant metadata like file name, location in the file, page number, etc.
    - **Normalization:** Consider automatic calculation and storage of normalized embeddings for efficient comparisons.

- **Indexing**
    - **Brute-force search:**  Offer a configuration for exhaustive search across all embeddings, useful for benchmarking and establishing ground truth retrieval.
    - **Approximate Nearest Neighbor (ANN) search:** Provide methods for efficient approximate search, such as:
        - **Inverted File (IVF) index:**  Clustering embeddings using algorithms like k-means.
        - **Tree-based methods:**  Hierarchical approaches like TreeAH.
        - **Quantization techniques:**  Compressing embeddings using methods like ScaNN ([link to ScaNN research blog](https://research.google/blog/announcing-scann-efficient-vector-similarity-search/)).
    - **Index parameters:** Allow configuration of cluster size (IVF) or leaf node size (TreeAH) to tune performance.
    - **Distance metrics:**  Support various distance metrics for similarity calculations (e.g., dot product, Euclidean, Manhattan, cosine).

- **Retrieval**
    - **Brute-force override:**  Enable an option to override ANN search and perform a brute-force search for ground truth retrieval.
    - **Control over retrieved neighbors:** Allow users to specify the number of neighbors to retrieve.
    - **Distance metric override:** Allow users to override the default distance metric at query time.
    - **Filtering and crowding:**  Enable the use of filterable and crowding attributes to refine the list of retrieved neighbors.
    - **Rich result sets:**  Return more than just match IDs; include the content, metadata, and similarity scores.
