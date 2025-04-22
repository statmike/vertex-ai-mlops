![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2FApplied+ML%2FSolution+Prototypes&file=readme.md)
<!--- header table --->
<table align="left">     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%20ML/Solution%20Prototypes/readme.md">
      <img src="https://cloud.google.com/ml-engine/images/github-logo-32px.png" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</table><br/><br/><br/><br/>

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
      - Create an agentic workflow using the Google ADK.

