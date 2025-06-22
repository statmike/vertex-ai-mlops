![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2FApplied+ML%2FSolution+Prototypes&file=readme.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%20ML/Solution%20Prototypes/readme.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https%3A//github.com/statmike/vertex-ai-mlops/blob/main/Applied%20ML/Solution%20Prototypes/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https%3A//github.com/statmike/vertex-ai-mlops/blob/main/Applied%20ML/Solution%20Prototypes/readme.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https%3A//github.com/statmike/vertex-ai-mlops/blob/main/Applied%20ML/Solution%20Prototypes/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https%3A//github.com/statmike/vertex-ai-mlops/blob/main/Applied%20ML/Solution%20Prototypes/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
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
# Solution Prototypes
> You are here: `vertex-ai-mlops/Applied ML/Solution Prototypes/readme.md`

This folder contains solution prototypes that integrate multiple aspects of Applied ML. These solutions are more complex and use-case specific than the examples found in other folders within this section.

**Solutions**

- [Document Processing](./document-processing/readme.md)
  - **Challenge: Variable Document Formats**
    - Invoices are received from numerous vendors.
    - Each vendor uses a unique invoice format.
    - Subtle changes in a vendor's invoice format can occur, sometimes legitimately, sometimes as fraud.
  - **Solution Components:**
    - **Custom Document Extraction with Document AI:**
      - Develop a custom extractor to accurately extract key invoice information across various formats.
    - **Multimodal Embeddings:**
      - Generate multimodal embeddings for document images and extracted text.
      - Create a numerical representation of each document.
    - **Nearest Neighbor Search:**
      - Use embeddings to find the nearest neighbors of new documents.
      - Determine the similarity of a current document to previous documents from the same vendor.
    - **Conditional Generative AI Comparison:**
      - If a current document is dissimilar to previous documents from the same vendor, generate a comparison of the formatting for human review.
    - **Automated Processing:**
      - Automate document processing using BigQuery Object Tables.
    - **Agentic Workflow:**
      - Create an agentic workflow using the Google ADK including deployment to Vertex AI Agent Engine and example of application integration.
- [Time Series](./time-series/readme.md)
  - Users interact with agents built with ADK that select MCP tools and retrieve results from BigQuery and present interactive charts.

