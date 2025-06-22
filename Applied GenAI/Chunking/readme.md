![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2FApplied+GenAI%2FChunking&file=readme.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%20GenAI/Chunking/readme.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https%3A//github.com/statmike/vertex-ai-mlops/blob/main/Applied%20GenAI/Chunking/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https%3A//github.com/statmike/vertex-ai-mlops/blob/main/Applied%20GenAI/Chunking/readme.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https%3A//github.com/statmike/vertex-ai-mlops/blob/main/Applied%20GenAI/Chunking/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https%3A//github.com/statmike/vertex-ai-mlops/blob/main/Applied%20GenAI/Chunking/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
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
# Content Processing and Annotation - Chunking
> You are here: `vertex-ai-mlops/Applied GenAI/Chunking/readme.md`

<p align="center"><center>
    <img src="../resources/images/created/applied-genai/overview-build-chunk.png" width="75%">
</center></p>

In retrieval augement generation (RAG) workflows, the goal is to retrieve context chunks related to a query. While whole documents are possible with long-context LLMs like Gemini (see examples in [Long Context Retrieval With The Vertex AI Gemini API](../Generate/Long%20Context%20Retrieval%20With%20The%20Vertex%20AI%20Gemini%20API.ipynb) and [Vertex AI Gemini API](../Generate/Vertex%20AI%20Gemini%20API.ipynb)), it is often more efficient to retrieve the most relevant context via a retrieval system. These systems can be simple or complex, but at their core is the choice of methods for breaking down content into logical parts—chunks. The following workflows examine methods to help with automating the creation of chunks from documents.

## Document AI Layout Parser
Document AI on Google Cloud offers parsers that process input documents into output JSON with extracted information.  The [Layout Parser](https://cloud.google.com/document-ai/docs/layout-parse-chunk) is specifically designed for creating chunks of desired sizes while also maintaining location information from a documents hierarchy: title > chapter > section > ... headings.  The following workflow shows multiple ways to process documents of different lengths and types and how to process the responses into information ready for creating embeddings.  This workflow creates the information (chunks) used by the [embeddings workflows](../Embeddings/readme.md) and [retrieval (RAG) workflows](../Retrieval/readme.md) within this [series](../readme.md):
- [Process Documents - Document AI Layout Parser](./Process%20Documents%20-%20Document%20AI%20Layout%20Parser.ipynb)

Building on the overview of the Document AI Layout Parser, the following workflow processes multiple large documents (over 1000 pages):
- [Large Document Processing - Document AI Layout Parser](./Large%20Document%20Processing%20-%20Document%20AI%20Layout%20Parser.ipynb)

## Using PyMuPDF For Extraction

[PyMuPDF](https://pymupdf.readthedocs.io/en/latest/) (based on the underlying MuPDF library) is a lightweight yet powerful Python library for accessing and manipulating various document formats, most notably PDF. It is known for its speed, efficiency, and comprehensive feature set, making it an excellent choice for extracting raw content from PDFs before chunking for RAG applications.

**Key Capabilities Utilized:**

* **Text Extraction:** Efficiently extracts plain text content page by page or from the entire document. It can also provide more detailed text information, including bounding boxes, which can be useful for layout-aware chunking strategies.
* **Metadata Access:** Allows retrieval of standard PDF metadata (e.g., title, author, creation date) which can be valuable context to associate with chunks.
* **Image Extraction:** Can identify and extract embedded images from PDFs, useful if your RAG pipeline needs to handle or reference visual content separately.
* **Page Handling:** Provides easy access to individual pages, page counts, and basic manipulation capabilities.

**Workflow Demonstration:**

The following notebook demonstrates a typical workflow using PyMuPDF to open PDF documents, iterate through pages, and extract text content suitable for subsequent chunking operations:

- [Process Documents - PyMuPDF](./Process%20Documents%20-%20PyMuPDF.ipynb)